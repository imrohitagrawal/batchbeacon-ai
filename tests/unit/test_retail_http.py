"""Real ASGI/service/SDK-fake queue flow, including durable refresh admission."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event

import pytest
from fastapi.testclient import TestClient
from google.api_core import exceptions
from pydantic import ValidationError

from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied
from batchbeacon.incident_api import IncidentHTTPPolicy, create_incident_test_app
from batchbeacon.retail_api import mount_retail_api
from batchbeacon.retail_projection import QueueFilter
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from tests.unit.test_firestore_store import owned, saved
from tests.unit.test_guest_boundary import ORIGIN
from tests.unit.test_retail_store import cold
from tests.unit.test_retail_store import enabled as enabled  # noqa: F401
from tests.unit.test_retail_store import env as env  # noqa: F401
from tests.unit.test_retail_store import (
    no_network_or_credentials as no_network_or_credentials,  # noqa: F401
)
from tests.unit.test_retail_store import setup as setup  # noqa: F401


@pytest.fixture
def http(enabled):
    stores, _, guest, evidence, actions, _ = enabled
    refresh = RetailRefresh(stores.retail, RefreshPolicy())
    app = create_incident_test_app(guest, evidence, actions, IncidentHTTPPolicy())
    mount_retail_api(app, refresh, IncidentHTTPPolicy())
    return TestClient(app, base_url=ORIGIN), refresh


def authorize(http, enabled):
    token, session, incident = owned(enabled)
    http[0].cookies.set(enabled[2].policy.cookie_name, token)
    return token, session, incident


def test_http_owned_queue_public_shape_and_separate_admission_writes(http, enabled):
    token, session, incident = authorize(http, enabled)
    stores, server, *_ = enabled
    server.calls.clear()
    response = http[0].get("/api/retail/queue", headers={"Idempotency-Key": "view"})
    assert response.status_code == 200
    body = response.json()
    assert [r["incident_id"] for r in body["snapshot"]["rows"]] == [incident.id]
    assert body["shop_label"] == "Synthetic demo shop"
    assert body["new_verification"]["state"] == "UNKNOWN"
    for private in (token, session.capability_hash, session.scope.session_id,
                    session.scope.shop_id, "effective_policy_hash", "read_policy_hash",
                    "context_binding_hash", "project_id", "budget", "lease_id"):
        assert private not in response.text
    assert response.headers["cache-control"] == "no-store, private"
    assert response.headers["referrer-policy"] == "no-referrer"
    writes = [w.update.name for method, r, _ in server.calls if method == "commit"
              for w in r.writes]
    assert writes == [stores.name("refresh", session.capability_hash)] * 2
    assert saved(enabled, "refresh", session.capability_hash).count == 1
    assert saved(enabled, "refresh", session.capability_hash).lease_id is None


@pytest.mark.parametrize("suffix,headers,content,status", [
    ("?shop_id=foreign", {}, None, 422),
    ("?filter=ALL&filter=ALL", {}, None, 422),
    ("?filter=wrong", {}, None, 422),
    ("", {}, b"{}", 422),
    ("", {"Idempotency-Key": ""}, None, 422),
    ("", {"Cookie": "batchbeacon_guest=wrong"}, None, 401),
])
def test_http_rejects_untrusted_inputs(http, enabled, suffix, headers, content, status):
    authorize(http, enabled)
    response = http[0].request("GET", "/api/retail/queue" + suffix,
        headers={"Idempotency-Key": "view", **headers}, content=content)
    assert response.status_code == status


def test_duplicate_cookie_and_fresh_session_cannot_read_other_queue(http, enabled):
    token, _, incident = authorize(http, enabled)
    name = enabled[2].policy.cookie_name
    response = http[0].get("/api/retail/queue", headers={
        "Cookie": f"{name}={token}; {name}={token}", "Idempotency-Key": "dup"})
    assert response.status_code == 401
    other, _ = enabled[2].issue()
    http[0].cookies.set(name, other)
    response = http[0].get("/api/retail/queue", headers={"Idempotency-Key": "own"})
    assert response.status_code == 200 and incident.id not in response.text
    assert response.json()["snapshot"]["rows"] == []


def test_rate_count_and_lease_persist_across_clients(enabled, env):
    token, session, _ = owned(enabled)
    policy = RefreshPolicy(max_session_refreshes=2)
    first = RetailRefresh(enabled[0].retail, policy)
    second = RetailRefresh(cold(enabled, env)[0].retail, policy)
    first.read(token, "one", selected_filter=QueueFilter.ALL)
    with pytest.raises(GuestDenied, match="refresh_rate_limited"):
        second.read(token, "two", selected_filter=QueueFilter.ALL)
    enabled[5][0] += timedelta(seconds=policy.minimum_interval_seconds)
    second.read(token, "two", selected_filter=QueueFilter.ALL)
    enabled[5][0] += timedelta(seconds=policy.minimum_interval_seconds)
    with pytest.raises(GuestDenied, match="refresh_allowance_exhausted"):
        first.read(token, "three", selected_filter=QueueFilter.ALL)
    assert saved(enabled, "refresh", session.capability_hash).count == 2


def test_cross_client_overlap_does_not_start_a_second_queue_read(enabled, env):
    token, _, _ = owned(enabled)
    first = RetailRefresh(enabled[0].retail, RefreshPolicy())
    second = RetailRefresh(cold(enabled, env)[0].retail, RefreshPolicy())
    lease = first.claim(token, "one")
    with pytest.raises(GuestDenied, match="refresh_in_progress"):
        second.read(token, "two", selected_filter=QueueFilter.ALL)
    first.release(token, lease)
    with pytest.raises(GuestDenied, match="refresh_request_already_admitted"):
        second.read(token, "one", selected_filter=QueueFilter.ALL)


def test_unknown_admission_ack_never_reads_queue_or_refunds_count(http, enabled):
    _, session, _ = authorize(http, enabled)
    stores, server, *_ = enabled
    server.calls.clear()
    def lost(request):
        if request.writes:
            raise exceptions.DeadlineExceeded("unknown claim")
    server.after_commit = lost
    response = http[0].get("/api/retail/queue", headers={"Idempotency-Key": "lost"})
    assert response.status_code == 503
    reads = [name for m, r, _ in server.calls if m == "batch_get_documents" for name in r.documents]
    assert not any("/sdk_tests/retail-" in name for name in reads)
    assert saved(enabled, "refresh", session.capability_hash).count == 1
    assert saved(enabled, "refresh", session.capability_hash).lease_id is not None


def test_expired_lease_stops_before_first_queue_rpc(enabled):
    token, _, _ = owned(enabled)
    stores, server, *_ = enabled
    server.calls.clear()
    with pytest.raises(GuestDenied):
        stores.retail.read(token, not_after=enabled[5][0])
    assert server.calls == []


def test_worker_holds_lease_until_read_finishes(http, enabled, monkeypatch):
    token, _, _ = authorize(http, enabled)
    started, finish = Event(), Event()
    original = http[1].retail.read
    def slow(*args, **kwargs):
        started.set()
        assert finish.wait(3)
        return original(*args, **kwargs)
    monkeypatch.setattr(http[1].retail, "read", slow)
    with ThreadPoolExecutor(max_workers=2) as pool:
        future = pool.submit(http[1].read, token, "first", selected_filter=QueueFilter.ALL)
        assert started.wait(3)
        try:
            with pytest.raises(GuestDenied, match="refresh_in_progress"):
                http[1].read(token, "second", selected_filter=QueueFilter.ALL)
        finally:
            finish.set()
        assert future.result().snapshot.rows


@pytest.mark.parametrize("change", [
    {"minimum_interval_seconds": 0}, {"lease_seconds": float("nan")},
    {"max_session_refreshes": True}, {"max_session_refreshes": 0},
])
def test_invalid_refresh_policy_fails_closed(change):
    with pytest.raises(ValidationError):
        RefreshPolicy(**change)


def test_lease_must_cover_operation_and_fit_session(enabled):
    with pytest.raises(ValueError):
        RetailRefresh(enabled[0].retail, replace(RefreshPolicy(), lease_seconds=1.0))

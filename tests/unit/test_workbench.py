"""Connected workbench HTTP checks; fake RPC/model explicitly retained."""

import pytest
from fastapi.testclient import TestClient
from google.api_core import exceptions

from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.guest_service import csrf_for
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.workbench import create_workbench_test_app
from tests.unit.test_retail_store import connected as connected  # noqa: F401
from tests.unit.test_retail_store import env as env  # noqa: F401
from tests.unit.test_retail_store import (
    no_network_or_credentials as no_network_or_credentials,  # noqa: F401
)
from tests.unit.test_retail_store import setup as setup  # noqa: F401
from tests.unit.test_reviewed_extraction import acquire


@pytest.fixture
def workbench(connected):
    c = connected
    app = create_workbench_test_app(
        c[0], c[8], RetailRefresh(c[3][0].retail, RefreshPolicy()), ExtractionHTTPPolicy()
    )
    client = TestClient(app, base_url=c[3][2].policy.origin)
    client.cookies.set(c[3][2].policy.cookie_name, c[2])
    headers = {
        "Origin": c[3][2].policy.origin,
        "X-CSRF-Token": csrf_for(c[2]),
        "Idempotency-Key": "workbench",
    }
    return client, c, headers


def test_assets_configuration_and_capture_recovery(workbench):
    client, c, _ = workbench
    root = client.get("/")
    assert root.status_code == 200 and "Opening BatchBeacon AI" in root.text
    assert "Loading extraction mode" in root.text
    assert "Server result · awaiting configuration" in root.text
    assert "frame-ancestors 'none'" in root.headers["content-security-policy"]
    config = client.get("/api/workbench/config").json()
    assert config["mode"] == "LOCAL_INTEGRATION_SIMULATED_EXTRACTION"
    assert len(config["samples"]) == 3 and config["server_time"]
    assert client.get("/samples/sfa-a.png").status_code == 200
    assert client.get("/samples/not-allowed.png").status_code == 404
    assert client.get("/design/prototype.js").status_code == 404
    batches = client.get(f"/api/incidents/{c[1].incident_id}/captures").json()["batches"]
    assert batches[0]["ready"] and len(batches[0]["captures"]) == 1
    assert "request_key" not in str(batches)
    assert not c[4]


def test_correction_reverification_is_bounded_and_does_not_call_model(workbench):
    client, c, headers = workbench
    acquire(c)
    path = f"/api/incidents/{c[1].incident_id}"
    before = client.get(path + "/evidence").json()
    original = next(
        f["observation"] for f in before["observation"]["fields"] if f["field"] == "LOT"
    )
    corrected = client.post(
        path + "/corrections",
        headers=headers,
        json={
            "expected_revision": 1,
            "field": "LOT",
            "replacement": original | {"value": "000Different"},
        },
    )
    assert corrected.status_code == 200 and not corrected.json()["current"]
    response = client.post(path + "/verifications", headers=headers | {"Idempotency-Key": "verify"})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["current"] and not result["hold_eligible"]
    assert result["observation"]["revision"] == 2 and len(result["result_history"]) == 2
    assert len(c[4]) == 2


def test_new_routes_deny_foreign_and_expired_sessions(workbench):
    client, c, headers = workbench
    path = f"/api/incidents/{c[1].incident_id}"
    foreign, _ = c[3][2].issue()
    client.cookies.set(c[3][2].policy.cookie_name, foreign)
    assert client.get(path + "/captures").status_code == 404
    assert client.post(path + "/verifications", headers=headers).status_code == 403
    client.cookies.set(c[3][2].policy.cookie_name, c[2])
    c[3][5][0] = c[6].scope.expires_at
    assert client.get(path + "/captures").status_code == 401
    assert client.post(path + "/verifications", headers=headers).status_code == 401


def test_verification_retry_reuses_existing_result_and_slot(workbench):
    client, c, headers = workbench
    acquire(c)
    path = f"/api/incidents/{c[1].incident_id}/verifications"
    first = client.post(path, headers=headers)
    assert first.status_code == 200, first.text
    second = client.post(path, headers=headers)
    assert second.status_code == 200, second.text
    assert len(second.json()["result_history"]) == len(first.json()["result_history"])


def test_verification_unknown_outcome_is_reported(workbench):
    client, c, headers = workbench
    acquire(c)
    store, server, *_ = c[3]

    def lost(request):
        if any(
            w.update.name == store.name("evidence", c[6].capability_hash, c[1].incident_id)
            for w in request.writes
        ):
            raise exceptions.DeadlineExceeded("unknown verification commit acknowledgement")

    server.after_commit = lost
    response = client.post(f"/api/incidents/{c[1].incident_id}/verifications", headers=headers)
    assert response.status_code == 503
    assert response.json().get("outcome") == "unknown", response.text


def test_old_reserved_key_does_not_publish_changed_observation(workbench):
    client, c, headers = workbench
    acquire(c)
    path = f"/api/incidents/{c[1].incident_id}"
    operation = headers["Idempotency-Key"]
    binding = c[7].verification_binding(c[2], c[1].incident_id, request_key=operation)
    c[0].shared.reserve_verification(c[6].capability_hash, c[1].incident_id, operation, binding)
    before = client.get(path + "/evidence").json()
    lot = next(f["observation"] for f in before["observation"]["fields"] if f["field"] == "LOT")
    changed = client.post(
        path + "/corrections",
        headers=headers | {"Idempotency-Key": "correction"},
        json={
            "expected_revision": 1,
            "field": "LOT",
            "replacement": lot | {"value": "000Corrected"},
        },
    )
    assert changed.status_code == 200
    result = client.post(path + "/verifications", headers=headers)
    assert result.status_code == 409, result.text
    after = client.get(path + "/evidence").json()
    assert not after["current"] and not after["hold_eligible"] and len(after["result_history"]) == 1


def test_committed_old_key_replay_cannot_restore_stale_result(workbench):
    client, c, headers = workbench
    acquire(c)
    path = f"/api/incidents/{c[1].incident_id}"
    first = client.post(path + "/verifications", headers=headers)
    assert first.status_code == 200
    lot = next(
        f["observation"] for f in first.json()["observation"]["fields"] if f["field"] == "LOT"
    )
    changed = client.post(
        path + "/corrections",
        headers=headers | {"Idempotency-Key": "correction"},
        json={
            "expected_revision": 1,
            "field": "LOT",
            "replacement": lot | {"value": "000Corrected"},
        },
    )
    assert changed.status_code == 200
    second = client.post(path + "/verifications", headers=headers)
    assert second.status_code == 200, second.text
    assert not second.json()["current"] and not second.json()["hold_eligible"]
    assert len(second.json()["result_history"]) == 2


def test_capture_reconciliation_is_exact_owned_read_only(workbench):
    client, c, _ = workbench
    service = c[3][2]
    incident = service.incident(c[2], c[1].incident_id)
    key = incident.batches[0].request_key
    path = f'/api/incidents/{incident.id}/capture-reconciliation'
    before = service.resolve(c[2])
    response = client.get(path, headers={'Idempotency-Key': key})
    assert response.status_code == 200
    assert response.json()['found'] and response.json()['batch']['ready']
    assert response.json()['batch']['captures'][0]['id'] == incident.batches[0].captures[0].id
    assert client.get(path, headers={'Idempotency-Key': 'absent'}).json() == {
        'found': False, 'batch': None}
    assert service.resolve(c[2]) == before and not c[4]
    assert client.get(path).status_code == 422
    assert client.get(path, headers={'Idempotency-Key': 'bad key'}).status_code == 422
    assert client.get(path, headers=[('Idempotency-Key', key),
                                     ('Idempotency-Key', key)]).status_code == 422
    foreign, _ = service.issue()
    client.cookies.set(service.policy.cookie_name, foreign)
    assert client.get(path, headers={'Idempotency-Key': key}).status_code == 404
    client.cookies.set(service.policy.cookie_name, c[2])
    c[3][5][0] = c[6].scope.expires_at
    assert client.get(path, headers={'Idempotency-Key': key}).status_code == 401


@pytest.mark.parametrize('committed', [False, True])
def test_capture_storage_failure_is_unknown_and_reconcilable(workbench, monkeypatch, committed):
    from pathlib import Path

    from batchbeacon.guest_service import GuestDenied

    client, c, headers = workbench
    service = c[3][2]
    original = service.retain

    def lost(*args, **kwargs):
        if committed:
            original(*args, **kwargs)
        raise GuestDenied(503, 'evidence_temporarily_unavailable')

    monkeypatch.setattr(service, 'retain', lost)
    headers = headers | {'Idempotency-Key': 'lost-capture-ack'}
    prefix = f'/api/incidents/{c[1].incident_id}'
    response = client.post(prefix + '/captures', headers=headers, files=[
        ('images', ('synthetic.png',
                    Path('fixtures/synthetic/sfa-a.png').read_bytes(), 'image/png'))])
    assert response.status_code == 503 and response.json()['outcome'] == 'unknown'
    readback = client.get(prefix + '/capture-reconciliation', headers=headers).json()
    assert readback['found'] is committed
    assert (readback['batch']['ready'] if committed else readback['batch'] is None)

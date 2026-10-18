"""HTTP01–14 local wire checks over preseeded, explicitly fake owned stores.

These do not prove atomic new-guest provisioning or real Firestore/model behavior.
"""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from starlette.requests import Request

from batchbeacon.action_service import ActionService
from batchbeacon.app import app as preparation_app
from batchbeacon.evidence_service import EvidenceService, replace
from batchbeacon.guest_service import csrf_for
from batchbeacon.incident_api import (
    CorrectionCommand,
    IncidentHTTPPolicy,
    _command,
    create_incident_test_app,
)
from tests.unit.domain_fixtures import known
from tests.unit.test_action_service import HOLD, REVIEW, fail_source  # noqa: F401
from tests.unit.test_action_service import actions as actions
from tests.unit.test_evidence_service import correct, publish
from tests.unit.test_evidence_service import rig as rig  # noqa: F401


@pytest.fixture
def api(actions):
    service, store, rig = actions
    policy = IncidentHTTPPolicy()
    app = create_incident_test_app(rig[0].guest, rig[0], service, policy)
    client = TestClient(app, base_url=rig[0].guest.policy.origin)
    client.cookies.set(rig[0].guest.policy.cookie_name, rig[2])
    headers = {"Origin": rig[0].guest.policy.origin, "X-CSRF-Token": csrf_for(rig[2]),
               "Idempotency-Key": "wire"}
    return client, headers, f"/api/incidents/{rig[4].id}", actions, policy


def correction(api, **updates):
    ref = api[3][2][5].captures[0]
    return {"expected_revision": 1, "field": "LOT",
            "replacement": known("000éB", evidence=ref).model_dump(mode="json")} | updates


def confirmation(api, kind=HOLD):
    response = api[0].get(api[2] + "/actions/prepare", params={"action_type": kind.value})
    assert response.status_code == 200, response.text
    assert response.json()["confirmation_required"]
    return {"target": response.json()["target"], "explicit_confirmation": True}


def action_state(api):
    _, store, rig = api[3]
    return store.state(rig[3].capability_hash, rig[4].id)


def protected_reads(api):
    path = api[2]
    return [path + "/evidence", path + "/actions",
            path + "/actions/prepare?action_type=SIMULATED_HOLD",
            path + "/actions/reconcile?result_revision=1&action_type=SIMULATED_HOLD",
            path + "/actions/" + "f" * 32]


def test_factory_scope_health_and_injection(api):
    client, _, _, actions, policy = api
    service, store, rig = actions
    assert client.get("/healthz").json() == {
        "mode": "adapter_test", "product": "not_ready", "paid_admission": "closed"}
    assert client.app.state.incident_http_policy_hash == policy.digest()
    assert not any(route.path.startswith("/api/incidents") for route in preparation_app.routes)
    with pytest.raises(ValueError):
        create_incident_test_app(rig[0].guest, None, service, policy)
    fresh_evidence = EvidenceService(rig[0].guest, rig[1], rig[0].policy)
    with pytest.raises(ValueError):
        create_incident_test_app(rig[0].guest, fresh_evidence, service, policy)
    assert store.states and action_state(api).actions == ()
    for suffix in ("/extractions", "/results", "/sources", "/budget", "/operator"):
        assert client.post(api[2] + suffix, json={}).status_code == 404


def test_preseeded_evidence_correction_and_historical_provenance(api):
    client, headers, path, actions, _ = api
    usage = actions[2][1].usage.copy()
    first = client.get(path + "/evidence").json()
    assert first["current"] and first["hold_eligible"]
    assert first["extraction_history"][0]["provenance"] == "fake"
    assert "redacted_output_json" not in first["extraction_history"][0]
    assert actions[2][2] not in json.dumps(first)
    changed = client.post(path + "/corrections", headers=headers, json=correction(api))
    assert changed.status_code == 200 and changed.json() == {
        "observation_revision": 2, "latest_observation_revision": 2, "current": False,
        "hold_eligible": False, "reverification_required": True}
    current = client.get(path + "/evidence").json()
    assert not current["current"] and not current["hold_eligible"]
    assert current["observation"]["corrections"][0]["previous"]["value"] == "232511"
    assert current["observation"]["fields"][0]["observation"]["raw"] == "000éB"
    original = client.get(path + "/evidence?revision=1").json()
    assert original["observation"]["fields"][0]["observation"]["value"] == "232511"
    assert not original["current"]
    assert actions[2][1].usage == usage
    assert client.post(path + "/corrections", headers=headers,
                       json=correction(api)).json() == changed.json()
    assert client.post(path + "/corrections", headers=headers,
                       json=correction(api, field="PACK")).status_code == 409


@pytest.mark.parametrize("bearer", ["missing", "malformed", "header_only", "expired"])
def test_all_protected_routes_require_current_cookie(api, bearer):
    client, headers, path, actions, _ = api
    command = confirmation(api)
    token = actions[2][2]
    client.cookies.clear()
    if bearer == "malformed":
        client.cookies.set(actions[2][0].guest.policy.cookie_name, "bad")
    if bearer == "header_only":
        client.headers["Authorization"] = "Bearer " + token
    if bearer == "expired":
        client.cookies.set(actions[2][0].guest.policy.cookie_name, token)
        actions[2][6][0] += timedelta(hours=8)
    for url in protected_reads(api):
        response = client.get(url)
        assert response.status_code == 401 and token not in response.text
    for suffix, body in (("/corrections", correction(api)), ("/actions", command)):
        assert client.post(path + suffix, headers=headers, json=body).status_code == 401
    assert not action_state(api).actions


def test_foreign_and_unknown_incident_denials_precede_body_parsing(api):
    client, headers, path, actions, _ = api
    command = confirmation(api)
    created = client.post(path + "/actions", headers=headers, json=command)
    owner_action = created.json()["action"]["id"]
    guest = actions[2][0].guest
    foreign_token, _ = guest.issue()
    foreign_incident = guest.create_incident(foreign_token, "foreign")
    other = path.replace(actions[2][4].id, foreign_incident.id)
    unknown_path = path.replace(actions[2][4].id, "f" * 32)
    for suffix in ("/evidence", "/actions", "/actions/" + owner_action,
                   "/actions/reconcile?result_revision=1&action_type=SIMULATED_HOLD",
                   "/actions/prepare?action_type=SIMULATED_HOLD"):
        foreign = client.get(other + suffix)
        unknown = client.get(unknown_path + suffix)
        assert (foreign.status_code, foreign.json()) == (unknown.status_code, unknown.json())
        assert foreign.status_code == 404
    for prefix in (other, unknown_path):
        for suffix in ("/corrections", "/actions"):
            response = client.post(prefix + suffix, headers=headers,
                                   content=b"x" * (api[4].max_json_bytes + 1))
            assert response.status_code == 404
    # A real action ID under a different, owned incident also cannot cross scope.
    owned = guest.create_incident(actions[2][2], "owned-second")
    assert client.get(f"/api/incidents/{owned.id}/actions/{owner_action}").status_code == 503


@pytest.mark.parametrize("origin", [None, "null", "https://evil.example",
                                     "https://batchbeacon.example.evil"])
def test_mutations_reject_wrong_origin_without_change(api, origin):
    client, headers, path, _, _ = api
    command = confirmation(api)
    headers = headers.copy()
    if origin is None:
        del headers["Origin"]
    else:
        headers["Origin"] = origin
    for suffix, body in (("/corrections", correction(api)), ("/actions", command)):
        assert client.post(path + suffix, headers=headers, json=body).status_code == 403
    assert not action_state(api).actions
    assert client.get(path + "/evidence").json()["latest_observation_revision"] == 1


@pytest.mark.parametrize("csrf", [None, "", "f" * 64])
def test_mutations_require_csrf_even_on_identical_retry(api, csrf):
    client, headers, path, _, _ = api
    command = confirmation(api)
    assert client.post(path + "/actions", headers=headers, json=command).status_code == 200
    headers = headers.copy()
    if csrf is None:
        del headers["X-CSRF-Token"]
    else:
        headers["X-CSRF-Token"] = csrf
    assert client.post(path + "/actions", headers=headers, json=command).status_code == 403
    assert len(action_state(api).actions) == 1


@pytest.mark.parametrize("raw", [b"{broken", b"[]", b"null", b"", b'{"field":"LOT","field":"PACK"}',
                                 b'{"expected_revision":NaN}', b'{"x":{"a":1,"a":2}}'])
def test_invalid_json_and_duplicate_keys_are_safe_errors(api, raw):
    response = api[0].post(api[2] + "/corrections",
        headers=api[1] | {"Content-Type": "application/json"}, content=raw)
    assert response.status_code == 422 and response.json() == {"error": "invalid_command"}
    assert api[0].get(api[2] + "/evidence").json()["latest_observation_revision"] == 1


@pytest.mark.parametrize("suffix", ["/corrections", "/actions"])
def test_deep_json_is_a_private_safe_error_without_mutation(api, suffix):
    client = TestClient(api[0].app, base_url=api[0].base_url, raise_server_exceptions=False)
    client.cookies.update(api[0].cookies)
    raw = b'{"x":' + b"[" * 10000 + b"0" + b"]" * 10000 + b"}"
    assert len(raw) < api[4].max_json_bytes
    response = client.post(api[2] + suffix,
        headers=api[1] | {"Content-Type": "application/json"}, content=raw)
    assert response.status_code == 422
    assert response.json() == {"error": "invalid_command"}
    assert response.headers["Cache-Control"] == "no-store, private"
    assert client.get(api[2] + "/evidence").json()["latest_observation_revision"] == 1
    assert not action_state(api).actions


@pytest.mark.parametrize("override", [{"Content-Type": "text/plain"},
    {"Content-Type": "application/json; charset=utf-16"}, {"Content-Encoding": "gzip"}])
def test_unsupported_media_or_encoding_rejected(api, override):
    headers = api[1] | {"Content-Type": "application/json"} | override
    response = api[0].post(api[2] + "/corrections", headers=headers,
                           content=json.dumps(correction(api)).encode())
    assert response.status_code == 415


@pytest.mark.parametrize("revision", [True, 1.0, "1", 0, -1])
def test_wire_revision_is_strict(api, revision):
    response = api[0].post(api[2] + "/corrections", headers=api[1],
                           json=correction(api, expected_revision=revision))
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["actor_session", "previous", "verdict", "reviewed", "role"])
def test_wire_correction_cannot_supply_authority(api, field):
    response = api[0].post(api[2] + "/corrections", headers=api[1],
                           json=correction(api, **{field: "private-test-input"}))
    assert response.status_code == 422 and "private-test-input" not in response.text


@pytest.mark.parametrize("value", [False, None, 1, 1.0, "true", {}, []])
def test_wire_confirmation_requires_literal_boolean_true(api, value):
    command = confirmation(api) | {"explicit_confirmation": value}
    response = api[0].post(api[2] + "/actions", headers=api[1], json=command)
    assert response.status_code == 422 and not action_state(api).actions


@pytest.mark.parametrize("key", [None, "", "bad key", "x" * 81])
def test_mutations_require_bounded_key(api, key):
    headers = api[1].copy()
    if key is None:
        del headers["Idempotency-Key"]
    else:
        headers["Idempotency-Key"] = key
    for suffix, command in (("/corrections", correction(api)), ("/actions", confirmation(api))):
        response = api[0].post(api[2] + suffix, headers=headers, json=command)
        assert response.status_code == 422 and response.json()["error"] == "request_key_required"


def test_concurrent_wire_confirmations_and_per_key_conflict(api):
    client, headers, path, actions, _ = api
    command = confirmation(api)
    def submit(index):
        c = TestClient(client.app, base_url=client.base_url)
        c.cookies.set(actions[2][0].guest.policy.cookie_name, actions[2][2])
        return c.post(path + "/actions", headers=headers | {"Idempotency-Key": f"k{index}"},
                      json=command)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(submit, range(3)))
    assert all(r.status_code == 200 for r in results)
    assert len({r.json()["action"]["id"] for r in results}) == 1
    assert len(action_state(api).events) == 1
    changed = command | {"target": command["target"] | {"result_hash": "b" * 64}}
    for i in range(3):
        assert client.post(path + "/actions", headers=headers | {"Idempotency-Key": f"k{i}"},
                           json=changed).status_code == 409


def test_correction_source_change_and_review_action_routes(api):
    client, headers, path, actions, _ = api
    old = confirmation(api)
    correct(actions[2])
    assert client.post(path + "/actions", headers=headers, json=old).status_code == 409
    fail_source(actions)
    publish(actions[2], key="failure")
    assert client.get(path + "/actions/prepare?action_type=SIMULATED_HOLD").status_code == 409
    command = confirmation(api, REVIEW)
    created = client.post(path + "/actions", headers=headers, json=command)
    assert created.status_code == 200
    data = created.json()
    assert data["action"]["simulation"] is True and "SOURCE_UNAVAILABLE" in data["event"]["reason"]
    assert client.get(path + "/actions/" + data["action"]["id"]).json() == data
    reconciled = client.get(path + "/actions/reconcile", params={
        "result_revision": 2, "action_type": REVIEW.value}).json()
    assert reconciled == {"found": True, "record": data}


def test_source_change_after_commit_returns_historical_not_renewed_approval(api):
    client, headers, path, actions, _ = api
    command = confirmation(api)
    actions[1].after_commit = lambda: fail_source(actions)
    response = client.post(path + "/actions", headers=headers, json=command)
    assert response.status_code == 200
    assert not response.json()["current"] and response.json()["requires_renewed_review"]
    assert client.post(path + "/actions", headers=headers, json=command).json() == response.json()
    assert len(action_state(api).events) == 1


def test_expiry_after_commit_denies_without_erasing_action(api):
    command = confirmation(api)
    api[3][1].after_commit = lambda: api[3][2][6].__setitem__(0, api[3][2][3].scope.expires_at)
    response = api[0].post(api[2] + "/actions", headers=api[1], json=command)
    assert response.status_code == 401 and len(action_state(api).actions) == 1


@pytest.mark.parametrize("committed", [False, True])
def test_uncertain_write_and_owned_reconciliation(api, committed):
    client, headers, path, actions, _ = api
    command = confirmation(api)
    actions[1].fail_after, actions[1].fail_before = committed, not committed
    response = client.post(path + "/actions", headers=headers, json=command)
    assert response.status_code == 503 and response.json()["outcome"] == "unknown"
    query = "/actions/reconcile?result_revision=1&action_type=SIMULATED_HOLD"
    failed = client.get(path + query)
    assert failed.status_code == 503 and "found" not in failed.json()
    actions[1].fail_before = actions[1].fail_after = False
    reconciled = client.get(path + query)
    assert reconciled.status_code == 200 and reconciled.json()["found"] is committed
    assert client.post(path + "/actions", headers=headers, json=command).status_code == 200
    assert len(action_state(api).events) == 1


def test_queries_bodies_private_headers_and_no_cors(api):
    client, _, path, _, _ = api
    urls = [path + "/evidence?revision=true", path + "/evidence?revision=1&revision=1",
        path + "/evidence?actor=me", path + "/actions?role=manager",
        path + "/actions/prepare?action_type=SELL", path + "/actions/reconcile",
        path + "/actions/not-an-id"]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 422
        assert response.headers["Cache-Control"] == "no-store, private"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert "access-control-allow-origin" not in response.headers
    for url in protected_reads(api)[:-1]:
        assert client.request("GET", url, content=b"unexpected").status_code == 422
    assert client.post(path + "/corrections?role=manager", headers=api[1],
                       json=correction(api)).status_code == 422


def test_effective_utf8_byte_limit_with_missing_or_false_length(api):
    client, headers, path, actions, _ = api
    raw = json.dumps(correction(api), ensure_ascii=False, separators=(",", ":")).encode()
    policy = IncidentHTTPPolicy(max_json_bytes=len(raw))
    app = create_incident_test_app(actions[2][0].guest, actions[2][0], actions[0], policy)
    bounded = TestClient(app, base_url=client.base_url)
    bounded.cookies.set(actions[2][0].guest.policy.cookie_name, actions[2][2])
    for length in (None, "0", "1"):
        sent = headers | {"Content-Type": "application/json"}
        if length is not None:
            sent["Content-Length"] = length
        over = bounded.post(path + "/corrections", headers=sent, content=iter((raw, b" ")))
        assert over.status_code == 413
    response = bounded.post(path + "/corrections",
        headers=headers | {"Content-Type": "application/json"}, content=raw)
    assert response.status_code == 200


def test_slow_json_wire_times_out_before_mutation(api):
    client, headers, path, actions, _ = api
    policy = IncidentHTTPPolicy(read_deadline_seconds=0.01)
    app = create_incident_test_app(actions[2][0].guest, actions[2][0], actions[0], policy)
    async def run():
        async def body():
            yield b'{"field":'
            await asyncio.sleep(0.05)
            yield b'"LOT"}'
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url=client.base_url) as c:
            response = await c.post(path + "/corrections", headers=headers | {
                "Content-Type": "application/json",
                "Cookie": f"{actions[2][0].guest.policy.cookie_name}={actions[2][2]}"},
                content=body())
            return response
    response = asyncio.run(run())
    assert response.status_code == 408
    assert client.get(path + "/evidence").json()["latest_observation_revision"] == 1


def test_cancelled_body_is_not_swallowed():
    async def receive():
        raise asyncio.CancelledError()
    request = Request({"type": "http", "method": "POST", "path": "/", "headers": [
        (b"content-type", b"application/json")]}, receive)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(_command(request, CorrectionCommand, IncidentHTTPPolicy()))


def test_cold_services_preserve_owned_http_history(api):
    client, headers, path, actions, policy = api
    command = confirmation(api)
    saved = client.post(path + "/actions", headers=headers, json=command).json()
    rig = actions[2]
    evidence = EvidenceService(rig[0].guest, rig[1], rig[0].policy)
    action = ActionService(evidence, actions[1], actions[0].policy)
    cold = TestClient(create_incident_test_app(rig[0].guest, evidence, action, policy),
                      base_url=client.base_url)
    cold.cookies.set(rig[0].guest.policy.cookie_name, rig[2])
    assert cold.get(path + "/actions/" + saved["action"]["id"]).json() == saved


def test_limits_are_typed_and_no_empty_state_is_invented(api):
    for override in ({"max_json_bytes": True}, {"max_json_bytes": 0},
                     {"read_deadline_seconds": float("nan")}, {"read_deadline_seconds": -1},
                     {"max_json_bytes": "1024"}):
        with pytest.raises(ValidationError):
            IncidentHTTPPolicy(**override)
    rig = api[3][2]
    with pytest.raises(ValueError):
        create_incident_test_app(rig[0].guest, rig[0], api[3][0],
            IncidentHTTPPolicy(read_deadline_seconds=float(rig[0].guest.policy.retail.session_seconds)))
    # Existing guest creation remains usable, but missing unified provisioning is
    # an explicit dependency failure rather than silently manufactured evidence.
    new = api[0].post("/api/incidents", headers=api[1] | {"Idempotency-Key": "new"})
    assert new.status_code == 200
    iid = new.json()["incident_id"]
    response = api[0].get(f"/api/incidents/{iid}/evidence")
    assert response.status_code == 503 and response.json()["error"] == "evidence_state_unavailable"
    assert (rig[3].capability_hash, iid) not in rig[1].states


def test_existing_body_free_routes_reject_stray_input(api):
    rig = api[3][2]
    capture_id = rig[5].captures[0].artifact_id
    for path in ("/api/incidents", api[2] + "/captures/" + capture_id):
        assert api[0].get(path + "?role=manager").status_code == 422
        assert api[0].request("GET", path, content=b"unexpected").status_code == 422
        assert api[0].get(path).status_code == 200


def test_scoped_negative_cannot_prepare_or_confirm_either_action(api):
    from tests.unit.domain_fixtures import observation
    old = confirmation(api)
    rig = api[3][2]
    correct(rig)
    state = rig[1].state(rig[3].capability_hash, rig[4].id)
    saved = state.observations[-1]
    identity = replace(saved.observation.identity,
                       resolved_name=saved.observation.identity.name.value,
                       resolution_review_hash=observation().identity.resolution_review_hash)
    saved = replace(saved, observation=replace(saved.observation, identity=identity))
    rig[1].states[(rig[3].capability_hash, rig[4].id)] = replace(state,
        observations=(*state.observations[:-1], saved)).model_dump_json()
    publish(rig, key="negative-wire")
    data = api[0].get(api[2] + "/evidence").json()
    assert data["current"] and data["result"]["verdict"] == "NOT_LISTED_IN_CHECKED_NOTICES"
    for kind in (HOLD, REVIEW):
        assert api[0].get(api[2] + "/actions/prepare", params={
            "action_type": kind.value}).status_code == 409
    assert api[0].post(api[2] + "/actions", headers=api[1], json=old).status_code == 409
    assert not action_state(api).actions


def test_old_correction_retry_reports_fresh_currentness_without_reactivation(api):
    rig = api[3][2]
    command = correction(api, replacement=known("232511", evidence=rig[5].captures[0]).model_dump(
        mode="json"))
    first = api[0].post(api[2] + "/corrections", headers=api[1], json=command)
    assert first.status_code == 200
    publish(rig, key="verified-correction")
    replay = api[0].post(api[2] + "/corrections", headers=api[1], json=command)
    assert replay.status_code == 200
    assert replay.json()["reverification_required"] is False
    assert replay.json()["current"] is True
    correct(rig, key="later-edit", expected=2)
    older = api[0].post(api[2] + "/corrections", headers=api[1], json=command).json()
    assert older["observation_revision"] == 2 and older["latest_observation_revision"] == 3
    assert older["current"] is False and older["reverification_required"] is True

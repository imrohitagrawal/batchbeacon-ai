"""P01–18 offline installed-SDK checks, separate from emulator/cloud evidence."""

import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import google.auth
import pytest
from fastapi.testclient import TestClient
from google.api_core import exceptions
from google.cloud.firestore_v1.types import BatchGetDocumentsResponse, Value
from pydantic import ValidationError

from batchbeacon.action_service import ActionConfirmation, ActionPolicy, ActionService
from batchbeacon.contracts import ActionType, VerifierPolicy
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidencePolicy,
    EvidenceService,
    ExtractedIdentity,
    ExtractedValues,
    ExtractionEnvelope,
    replace,
)
from batchbeacon.firestore_store import FirestorePolicy, FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService
from batchbeacon.incident_api import IncidentHTTPPolicy, create_incident_test_app
from batchbeacon.shared_admission import Address, Change, SharedAdmission, SharedDenied
from batchbeacon.uploads import sanitize_images
from tests.unit.domain_fixtures import NOW, context, known, notice, observation
from tests.unit.durable_fixtures import record_wire, run_binding, wire_response
from tests.unit.firestore_rpc_fake import Server, client
from tests.unit.test_guest_boundary import ORIGIN, MemoryObjects, picture
from tests.unit.test_shared_admission import env as env


@pytest.fixture(autouse=True)
def no_network_or_credentials(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("offline test attempted network or credential discovery")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(google.auth, "default", forbidden)


@pytest.fixture
def setup():
    policy = FirestorePolicy(project_id="synthetic-project", database_id="(default)",
        namespace="sdk_tests", environment_id="sfa_first", mode="offline_test",
        api_endpoint="127.0.0.1:8088")
    now, server = [NOW], Server()
    gp, ep, ap = GuestPolicy(origin=ORIGIN), EvidencePolicy(), ActionPolicy()
    stores = FirestoreStores(client(server), policy, gp, ep, ap, clock=lambda: now[0])
    guest = GuestService(gp, stores.guests, MemoryObjects(), clock=lambda: now[0])
    evidence = EvidenceService(guest, stores.evidence, ep)
    actions = ActionService(evidence, stores.actions, ap)
    environment = EvidenceEnvironment(context=context(), notices=(notice(),),
                                       verifier_policy=VerifierPolicy())
    server.seed(stores._encode(stores.name("environment"), "environment", environment))
    return stores, server, guest, evidence, actions, now


def owned(setup):
    token, session = setup[2].issue()
    return token, session, setup[2].create_incident(token, "first")


def saved(setup, kind, key=None, incident=None):
    stores, server, *_ = setup
    name = stores.name(kind, key, incident)
    return stores._decode(server.docs[name], kind) if name in server.docs else None


def extract(setup, token, incident):
    _, _, guest, evidence, _, _ = setup
    capture = guest.retain(token, incident.id, "upload",
        sanitize_images((picture(),), guest.policy.uploads)).captures[0].evidence()
    obs = observation()
    envelope = ExtractionEnvelope(provenance="fake", redacted_output_json='{"fake":true}',
        validation="VALID", values=ExtractedValues(identity=ExtractedIdentity(
            name=known(obs.identity.name.value, evidence=capture),
            pack=known("250 g", evidence=capture)), fields=tuple(replace(f,
                observation=known(f.observation.value, f.observation.value_type, evidence=capture))
                for f in obs.fields)), model_id="test-fake", prompt_version="test-1",
        configuration_hash="a" * 64, sources=(notice().dependency,), captures=(capture,),
        started_at=NOW, completed_at=NOW)
    evidence.record_extraction(token, incident.id, "extract", 0, envelope)
    return envelope


def shared(setup, env):
    # Test grant only; this does NOT initialize a budget in the adapter.
    return SharedAdmission(env[0].policy, env[0].grant, setup[0].shared,
                            clock=lambda: setup[5][0])


def publish(setup, env, token, session, incident):
    evidence = setup[3]
    binding = evidence.verification_binding(token, incident.id)
    shared(setup, env).reserve_verification(session.capability_hash,
        incident.id, "verify", binding)
    evidence.publish_verification(token, incident.id, "verify", binding)


def test_fresh_guest_http_provisions_children_without_manual_seed(setup):
    stores, server, guest, evidence, actions, _ = setup
    http = TestClient(create_incident_test_app(guest, evidence, actions, IncidentHTTPPolicy()),
                      base_url=ORIGIN)
    issued = http.post("/api/guest", headers={"Origin": ORIGIN})
    assert issued.status_code == 200
    headers = {"Origin": ORIGIN, "X-CSRF-Token": issued.json()["csrf_token"],
               "Idempotency-Key": "new"}
    created = http.post("/api/incidents", headers=headers)
    assert created.status_code == 200
    iid = created.json()["incident_id"]
    result = http.get(f"/api/incidents/{iid}/evidence")
    assert result.status_code == 200 and result.json()["observation"] is None
    assert not result.json()["current"]
    assert http.get(f"/api/incidents/{iid}/actions").json() == {"actions": []}
    assert http.post("/api/incidents", headers=headers).json() == created.json()
    assert stores.name("budget") not in server.docs and len(server.docs) == 5
    versions = server.versions.copy()
    http.get(f"/api/incidents/{iid}/evidence")
    assert versions == server.versions


def test_services_history_and_cold_reconstruction(setup, env):
    stores, server, guest, evidence, actions, _ = setup
    token, session, incident = owned(setup)
    original = extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    assert evidence.read_evidence(token, incident.id).hold_eligible
    target = actions.prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    record = actions.confirm(token, incident.id, "hold",
        ActionConfirmation(target=target, explicit_confirmation=True))
    usage = saved(setup, "usage", session.capability_hash)
    evidence.correct(token, incident.id, "correction", 1, "LOT",
                     known("000aB", evidence=original.captures[0]))
    cold = FirestoreStores(client(server), stores.policy, guest.policy, evidence.policy,
                            actions.policy, clock=lambda: setup[5][0])
    cold_guest = GuestService(guest.policy, cold.guests, guest.objects, clock=lambda: setup[5][0])
    cold_evidence = EvidenceService(cold_guest, cold.evidence, evidence.policy)
    cold_actions = ActionService(cold_evidence, cold.actions, actions.policy)
    view = cold_evidence.read_evidence(token, incident.id)
    assert view.observation.fields[0].observation.value == "000aB" and not view.current
    assert view.state.observations[0].observation.fields[0].observation.value == "232511"
    assert cold_actions.get_action(token, incident.id, record.action.id).requires_renewed_review
    assert saved(setup, "usage", session.capability_hash) == usage
    assert stores.name("budget") not in server.docs


def test_two_clients_concurrently_create_one_incident(setup):
    stores, server, guest, evidence, actions, _ = setup
    token, session = guest.issue()
    second = FirestoreStores(client(server), stores.policy, guest.policy, evidence.policy,
                             actions.policy, clock=lambda: setup[5][0])
    other = GuestService(guest.policy, second.guests, guest.objects, clock=lambda: setup[5][0])
    barrier = Barrier(2)
    def before(request):
        if len(request.writes) == 4 and server.aborts == 0:
            barrier.wait(timeout=2)
    server.before_commit = before
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(g.create_incident, token, "same") for g in (guest, other)]
        results = [f.result() for f in futures]
    assert results[0] == results[1] and server.aborts == 1
    assert len(saved(setup, "usage", session.capability_hash).incidents) == 1
    assert len(server.docs) == 5


@pytest.mark.parametrize("kind", ["usage", "evidence", "actions", "environment"])
def test_missing_records_never_initialize_or_reset(setup, kind):
    stores, server, _, evidence, actions, _ = setup
    token, session, incident = owned(setup)
    name = stores.name(kind, session.capability_hash if kind != "environment" else None,
                       incident.id if kind in {"evidence", "actions"} else None)
    del server.docs[name]
    with pytest.raises(GuestDenied) as exc:
        (actions.list_actions if kind == "actions" else evidence.read_evidence)(token, incident.id)
    assert exc.value.status == 503 and name not in server.docs


@pytest.mark.parametrize("transform", [lambda r: r[:-1], lambda r: [*r, r[0]],
    lambda r: [BatchGetDocumentsResponse(missing="unexpected"), *r],
    lambda r: [BatchGetDocumentsResponse(), *r]])
def test_incomplete_duplicate_foreign_or_empty_responses_fail(setup, transform):
    _, server, guest, _, _, _ = setup
    token, _, _ = owned(setup)
    assert guest.resolve(token)  # fake already returns reversed response order
    server.read_transform = transform
    with pytest.raises(GuestDenied) as exc:
        guest.resolve(token)
    assert exc.value.status == 503


def test_lost_ack_reconciles_same_incident_without_reset(setup):
    stores, server, guest, *_ = setup
    token, session = guest.issue()
    def lost(request):
        if len(request.writes) == 4:
            raise exceptions.DeadlineExceeded("injected lost acknowledgement")
    server.after_commit, server.rollback_fails = lost, True
    with pytest.raises(GuestDenied):
        guest.create_incident(token, "unknown")
    assert len(saved(setup, "usage", session.capability_hash).incidents) == 1
    server.after_commit = lambda request: None
    result = guest.create_incident(token, "unknown")
    assert len(guest.resolve(token).incidents) == 1
    assert saved(setup, "usage", session.capability_hash).incidents[0].incident_id == result.id
    assert stores.name("budget") not in server.docs


def test_exclusive_creation_and_outage_never_return_empty_success(setup):
    stores, server, guest, *_ = setup
    token, session, _ = owned(setup)
    before = server.versions.copy()
    with pytest.raises(OSError):
        stores.guests.create(replace(session, incidents=()))
    assert before == server.versions
    server.fail = "batch_get_documents"
    with pytest.raises(GuestDenied) as exc:
        guest.resolve(token)
    assert exc.value.status == 503
    server.fail = None
    assert stores.guests.get("f" * 64) is None


@pytest.mark.parametrize("override", [
    {"operation_seconds": float("nan")}, {"rpc_seconds": 0}, {"max_transaction_attempts": True},
    {"namespace": "../escape"}, {"database_id": "bad/name"}, {"project_id": "bad/project"},
    {"mode": "production"}, {"api_endpoint": "evil.example:8088"},
    {"api_endpoint": "127.0.0.1:65536"}, {"max_document_bytes": 1048577},
    {"max_request_bytes": 10485761}, {"cleanup_seconds": 6.0},
])
def test_config_rejects_invalid_values(setup, override):
    with pytest.raises(ValidationError):
        replace(setup[0].policy, **override)


def test_effective_config_reaches_rpc_and_writer_receipt(setup):
    stores, server, guest, evidence, actions, _ = setup
    policy = replace(stores.policy, database_id="other-db", namespace="other_space",
                     rpc_seconds=2.5, operation_seconds=7.0, cleanup_seconds=0.5)
    changed = FirestoreStores(client(server), policy, guest.policy, evidence.policy,
                              actions.policy, clock=lambda: setup[5][0])
    service = GuestService(guest.policy, changed.guests, guest.objects, clock=lambda: setup[5][0])
    _, session = service.issue()
    recent = server.calls[-3:]
    assert all(request.database == policy.database for _, request, _ in recent)
    assert all(0 < o["timeout"] <= 2.5 and o["retry"] is None for _, _, o in recent)
    document = server.docs[changed.name("guest", session.capability_hash)]
    assert document.fields["writer_config_hash"].string_value == policy.digest()
    payload = json.loads(document.fields["payload"].string_value)
    assert payload["policy_hash"] == guest.policy.digest()
    assert changed.name("budget") not in server.docs


@pytest.mark.parametrize("mutation", [
    lambda d: d.fields.__setitem__("schema", Value(integer_value=2)),
    lambda d: d.fields.__setitem__("payload", Value(string_value="{bad")),
    lambda d: d.fields.__setitem__("writer_config_hash", Value(string_value="wrong")),
    lambda d: d.fields.__setitem__("kind", Value(string_value="actions")),
    lambda d: d.fields.__setitem__("extra", Value(string_value="unrecognized")),
])
def test_corrupt_envelopes_deny_without_repair(setup, mutation):
    stores, server, guest, *_ = setup
    token, session, _ = owned(setup)
    mutation(server.docs[stores.name("guest", session.capability_hash)])
    before = server.versions.copy()
    with pytest.raises(GuestDenied) as exc:
        guest.resolve(token)
    assert exc.value.status == 503 and before == server.versions


def test_pure_verification_no_budget_and_commit_required_circuit(setup, env):
    stores, server, *_ = setup
    token, session, incident = owned(setup)
    service = shared(setup, env)
    service.reserve_verification(session.capability_hash, incident.id, "pure", "c" * 64)
    assert stores.name("budget") not in server.docs
    with pytest.raises(SharedDenied):
        service.begin_run(session.capability_hash, incident.id, "paid",
                          run_binding(setup[2], token, incident.id))
    # Explicit test budget inside the recording server only.
    stores.shared.create_budget(env[1].state())
    with pytest.raises(OSError):
        stores.shared.create_budget(env[1].state())
    result = stores.shared.transact(Address(), lambda snap: Change(
        replace(snap.budget, circuit="open_bound"), denial="test circuit"))
    assert result.denial == "test circuit" and saved(setup, "budget").circuit == "open_bound"


def test_source_change_is_in_action_conflict_set(setup, env):
    stores, server, _, evidence, actions, _ = setup
    token, session, incident = owned(setup)
    extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    command = ActionConfirmation(target=actions.prepare(token, incident.id,
        ActionType.SIMULATED_HOLD), explicit_confirmation=True)
    def change_source(request):
        if request.writes and request.writes[0].update.name == stores.name(
                "actions", session.capability_hash, incident.id) and server.aborts == 0:
            old = saved(setup, "environment")
            source = old.context.current_sources[0]
            updated = replace(old, context=replace(old.context,
                current_sources=(replace(source, epoch=source.epoch + 1),)))
            server.seed(stores._encode(stores.name("environment"), "environment", updated))
    server.before_commit = change_source
    with pytest.raises(GuestDenied) as exc:
        actions.confirm(token, incident.id, "racing", command)
    assert exc.value.status == 409 and server.aborts == 1
    assert not saved(setup, "actions", session.capability_hash, incident.id).actions
    assert not evidence.read_evidence(token, incident.id).current


def test_not_after_reaches_commit_and_cleanup_has_own_bound(setup):
    stores, server, *_ = setup
    _, session, _ = owned(setup)
    before = server.versions.copy()
    with pytest.raises(OSError):
        stores.shared.transact(Address(session.capability_hash), lambda snap: Change(
            snap.budget, snap.usage, not_after=NOW - timedelta(seconds=1)))
    assert server.versions == before
    name, _, options = server.calls[-1]
    assert name == "rollback" and 0 < options["timeout"] <= stores.policy.cleanup_seconds


def test_small_document_limit_prevents_commit(setup):
    stores, server, guest, evidence, actions, _ = setup
    small = FirestoreStores(client(server), replace(stores.policy, max_document_bytes=200),
        guest.policy, evidence.policy, actions.policy, clock=lambda: setup[5][0])
    service = GuestService(guest.policy, small.guests, guest.objects, clock=lambda: setup[5][0])
    before = server.versions.copy()
    with pytest.raises(GuestDenied):
        service.issue()
    assert server.versions == before
    assert not any(name == "commit" for name, _, _ in server.calls)


def test_bounded_conflict_retries_and_ambiguous_begin_do_not_write(setup):
    stores, server, guest, *_ = setup
    def conflict(request):
        raise exceptions.Aborted("injected definite conflict")
    server.before_commit = conflict
    with pytest.raises(GuestDenied):
        guest.issue()
    assert sum(n == "commit" for n, _, _ in server.calls) == stores.policy.max_transaction_attempts
    assert len(server.docs) == 1
    server.calls.clear()
    server.fail = "begin_transaction"
    with pytest.raises(GuestDenied):
        guest.issue()
    assert [n for n, _, _ in server.calls] == ["begin_transaction"]


@pytest.mark.parametrize("limits, expected_rpc", [
    ({"max_documents": 1}, "begin_transaction"),
    ({"max_document_bytes": 100, "max_request_bytes": 180, "max_read_bytes": 500},
     "begin_transaction"),
    ({"max_document_bytes": 100, "max_request_bytes": 2000, "max_read_bytes": 101},
     "batch_get_documents"),
])
def test_document_count_request_and_stream_limits_reach_consumer(setup, limits, expected_rpc):
    stores, server, guest, evidence, actions, _ = setup
    bounded = FirestoreStores(client(server), replace(stores.policy, **limits),
        guest.policy, evidence.policy, actions.policy, clock=lambda: setup[5][0])
    with pytest.raises(OSError):
        bounded.guests.get("a" * 64)
    names = [n for n, _, _ in server.calls]
    assert expected_rpc in names and "commit" not in names
    assert len(server.docs) == 1


def test_operation_expiry_after_ack_keeps_records_without_retry_or_rollback(setup):
    stores, server, guest, *_ = setup
    ticks = [0.0]
    stores.monotonic = lambda: ticks[0]
    def late(request):
        ticks[0] = stores.policy.operation_seconds + 1
    server.after_commit = late
    with pytest.raises(GuestDenied):
        guest.issue()
    assert len(server.docs) == 3
    names = [n for n, _, _ in server.calls]
    assert names.count("commit") == 1 and "rollback" not in names


def test_expired_stream_and_callback_denial_preserve_original_outcome(setup):
    stores, server, guest, *_ = setup
    token, session, _ = owned(setup)
    ticks = [0.0]
    stores.monotonic = lambda: ticks[0]
    def delayed(responses):
        yield responses[0]
        ticks[0] += stores.policy.operation_seconds + 1
        yield from responses[1:]
    server.read_transform, server.rollback_fails = delayed, True
    versions = server.versions.copy()
    with pytest.raises(GuestDenied):
        guest.resolve(token)
    assert versions == server.versions
    server.read_transform = lambda responses: responses
    def deny(stored):
        raise GuestDenied(409, "original_denial")
    with pytest.raises(GuestDenied) as exc:
        stores.guests.transact(session.capability_hash, deny)
    assert exc.value.code == "original_denial"


def test_shared_claim_lost_ack_retains_intent_and_one_usage_reconciliation(setup, env):
    stores, server, *_ = setup
    token, session, incident = owned(setup)
    service = shared(setup, env)
    stores.shared.create_budget(env[1].state())
    run = service.begin_run(session.capability_hash, incident.id, "run",
                            run_binding(setup[2], token, incident.id))
    attempt = service.reserve(session.capability_hash, run.id, "b" * 32, "c" * 64,
                              operation_key="extract")
    def lost_claim(request):
        if any(w.update.name == stores.name("attempt", attempt.id) for w in request.writes):
            raise exceptions.DeadlineExceeded("injected lost claim acknowledgement")
    server.after_commit, server.rollback_fails = lost_claim, True
    with pytest.raises(OSError):
        service.claim_dispatch(session.capability_hash, run.id, attempt.id,
                               attempt.request_hash, attempt.model_configuration_hash)
    assert saved(setup, "attempt", attempt.id).dispatch_claimed
    balance = saved(setup, "budget").balance(attempt.pool)
    assert balance.reserved_nanos == attempt.reserved_nanos
    server.after_commit = lambda request: None
    with pytest.raises(SharedDenied):
        service.claim_dispatch(session.capability_hash, run.id, attempt.id,
                               attempt.request_hash, attempt.model_configuration_hash)
    record_wire(service, attempt, wire_response(100, 10))
    service.reconcile(attempt.id)
    budget = saved(setup, "budget")
    service.reconcile(attempt.id)
    assert saved(setup, "budget") == budget

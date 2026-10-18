"""Durable attempt tests through the installed generated SDK with recording RPCs."""

import json
import traceback
from datetime import timedelta

import pytest
from google.api_core import exceptions
from google.cloud.firestore_v1.types import Value

from batchbeacon.attempt_evidence import response_evidence
from batchbeacon.evidence_service import replace
from batchbeacon.firestore_store import FirestoreStores
from batchbeacon.shared_admission import SharedAdmission, SharedDenied
from tests.unit.durable_fixtures import record_wire, run_binding, wire_response
from tests.unit.firestore_rpc_fake import client
from tests.unit.test_firestore_store import (
    no_network_or_credentials as no_network_or_credentials,
)
from tests.unit.test_firestore_store import owned, saved, shared
from tests.unit.test_firestore_store import setup as setup
from tests.unit.test_shared_admission import env as env


def started(setup, env):
    stores, _, guest, *_ = setup
    token, session, incident = owned(setup)
    service = shared(setup, env)
    stores.shared.create_budget(env[1].state())
    run = service.begin_run(session.capability_hash, incident.id, "run",
                            run_binding(guest, token, incident.id))
    attempt = service.reserve(session.capability_hash, run.id, "b" * 32, "c" * 64,
                              operation_key="extract")
    service.claim_dispatch(session.capability_hash, run.id, attempt.id, attempt.request_hash,
                           attempt.model_configuration_hash)
    return service, session, run, attempt


def cold(setup, service):
    old, server, guest, evidence, actions, now = setup
    stores = FirestoreStores(client(server), old.policy, guest.policy, evidence.policy,
                             actions.policy, clock=lambda: now[0])
    return SharedAdmission(service.policy, service.grant, stores.shared, clock=lambda: now[0])


@pytest.mark.parametrize("phase", ["response", "reconcile"])
def test_lost_ack_cold_recovery_preserves_once_only_money_and_raw(setup, env, phase):
    stores, server, *_ = setup
    service, session, run, attempt = started(setup, env)
    if phase == "reconcile":
        record_wire(service, attempt)
    def lost(request):
        if any(w.update.name == stores.name("attempt", attempt.id) for w in request.writes):
            raise exceptions.DeadlineExceeded("test lost durable evidence ack")
    server.after_commit = lost
    with pytest.raises(OSError):
        record_wire(service, attempt) if phase == "response" else service.reconcile(attempt.id)
    server.after_commit = lambda _: None
    reopened = cold(setup, service)
    assert reopened.inspect_run(session.capability_hash, run.id).attempt_ids == (attempt.id,)
    retained = reopened.inspect_attempt(session.capability_hash, run.id, attempt.id)
    assert retained.response.complete
    before = saved(setup, "budget")
    record_wire(reopened, attempt) if phase == "response" else reopened.reconcile(attempt.id)
    assert saved(setup, "budget") == before
    with pytest.raises(SharedDenied, match="claim"):
        reopened.claim_dispatch(session.capability_hash, run.id, attempt.id,
                                attempt.request_hash, attempt.model_configuration_hash)
    assert len(saved(setup, "evidence", session.capability_hash, run.incident_id).extractions) == 0


def test_conflicting_response_transaction_retry_preserves_first_commit(setup, env):
    stores, server, *_ = setup
    service, _, _, attempt = started(setup, env)
    other = cold(setup, service)
    fired = []
    def conflict(request):
        if not fired and any(w.update.name == stores.name("attempt", attempt.id)
                             for w in request.writes):
            fired.append(True)
            server.before_commit = lambda _: None
            record_wire(other, attempt, b'original first response')
    server.before_commit = conflict
    before = saved(setup, "budget")
    with pytest.raises(SharedDenied, match="conflict"):
        record_wire(service, attempt, b'losing response')
    assert server.aborts == 1
    assert saved(setup, "attempt", attempt.id).response.original() == b'original first response'
    assert saved(setup, "budget") == before


def document_size(document):
    # Document storage-size contract includes resource name/envelope, not just raw bytes.
    return len(document.name.encode()) + 48 + sum(len(k.encode()) + 1 + (
        len(v.string_value.encode()) + 1 if k != "schema" else 8)
        for k, v in document.fields.items())


@pytest.mark.parametrize("offset", [0, -1])
def test_actual_base64_document_exact_limit_and_one_byte_over(setup, env, offset):
    stores, server, *_ = setup
    service, _, _, attempt = started(setup, env)
    raw = b'not parsed ' * 5000
    candidate = saved(setup, "attempt", attempt.id).model_copy(update={"response":
        response_evidence(raw, status_code=200, complete=True, observed_bytes=len(raw),
                          limits=attempt.evidence_limits)})
    doc = stores._encode(stores.name("attempt", attempt.id), "attempt", candidate)
    size = document_size(doc)
    assert size > 4 * len(raw) // 3  # Includes base64 and the actual enclosing metadata.
    stores.policy = replace(stores.policy, max_document_bytes=size + offset)
    before = server.versions.copy()
    if offset:
        with pytest.raises(OSError):
            record_wire(service, attempt, raw)
        assert server.versions == before
        assert saved(setup, "attempt", attempt.id).response is None
    else:
        record_wire(service, attempt, raw)
        assert saved(setup, "attempt", attempt.id).response.original() == raw


@pytest.mark.parametrize("offset", [0, -1])
def test_actual_generated_commit_exact_limit_and_one_byte_over(setup, env, offset):
    stores, server, *_ = setup
    service, _, _, attempt = started(setup, env)
    raw = b'bounded response ' * 4000
    call = stores._call
    inspected = []
    def bounded(method, request, *args):
        if method == "commit" and request.writes:
            size = len(type(request).serialize(request))
            doc_size = max(document_size(w.update) for w in request.writes)
            assert doc_size < size + offset
            stores.policy = replace(stores.policy, max_document_bytes=doc_size,
                                     max_request_bytes=size + offset)
            inspected.append(size)
        return call(method, request, *args)
    stores._call = bounded
    before = server.versions.copy()
    if offset:
        with pytest.raises(OSError):
            record_wire(service, attempt, raw)
        assert server.versions == before
    else:
        record_wire(service, attempt, raw)
    assert len(inspected) == 1


def test_late_internal_evidence_uses_existing_attempt_without_guest_access(setup, env):
    service, session, run, attempt = started(setup, env)
    setup[5][0] += timedelta(days=10)
    reopened = cold(setup, service)
    record_wire(reopened, attempt)
    reopened.reconcile(attempt.id)
    assert saved(setup, "attempt", attempt.id).actual_nanos == attempt.price.cost_nanos(100, 50)
    with pytest.raises(SharedDenied, match="guest"):
        reopened.inspect_attempt(session.capability_hash, run.id, attempt.id)


@pytest.mark.parametrize("field,value", [("body_base64", "private bad base64"),
                                         ("retained_sha256", "f" * 64)])
def test_corrupt_retained_response_is_generic_and_never_refunds(setup, env, field, value):
    stores, server, *_ = setup
    service, _, _, attempt = started(setup, env)
    record_wire(service, attempt)
    name = stores.name("attempt", attempt.id)
    payload = json.loads(server.docs[name].fields["payload"].string_value)
    payload["response"][field] = value
    server.docs[name].fields["payload"] = Value(string_value=json.dumps(payload))
    before = server.versions.copy()
    with pytest.raises(OSError, match="persistent evidence unavailable") as exc:
        service.reconcile(attempt.id)
    assert exc.value.__context__ is None
    assert value not in "".join(traceback.format_exception(exc.value))
    assert server.versions == before


def test_overbound_circuit_survives_actual_firestore_record_size_failure(setup, env):
    stores, _, *_ = setup
    service, session, run, attempt = started(setup, env)
    # Enough original body to make this document larger than guest/usage/budget.
    record_wire(service, attempt, wire_response(12001, 1, retained_context="x" * 5000))
    original = saved(setup, "attempt", attempt.id)
    size = document_size(stores._encode(stores.name("attempt", attempt.id), "attempt", original))
    stores.policy = replace(stores.policy, max_document_bytes=size)
    before = saved(setup, "budget").balance(attempt.pool)
    with pytest.raises(OSError):
        service.reconcile(attempt.id)
    assert saved(setup, "budget").circuit == "open_bound"
    assert saved(setup, "budget").balance(attempt.pool) == before
    assert saved(setup, "attempt", attempt.id) == original
    with pytest.raises(SharedDenied, match="circuit"):
        service.reserve(session.capability_hash, run.id, "d" * 32, "e" * 64,
                        operation_key="another")

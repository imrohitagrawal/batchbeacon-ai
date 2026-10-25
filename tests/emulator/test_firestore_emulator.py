"""Explicit loopback Firestore integration; not deployed IAM/Storage/model proof.

Run only with BATCHBEACON_EMULATOR_CONFIG pointing to a private, provenance-
admitted server configuration. This module never starts a server or uses ADC.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import google.auth
import grpc
import pytest
from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud.firestore_v1.services.firestore import FirestoreClient
from google.cloud.firestore_v1.services.firestore.transports.grpc import FirestoreGrpcTransport

from batchbeacon.action_service import ActionConfirmation, ActionPolicy, ActionService
from batchbeacon.contracts import ActionType, VerifierPolicy
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidencePolicy,
    EvidenceService,
    replace,
)
from batchbeacon.firestore_store import FirestorePolicy, FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestPolicy, GuestService
from batchbeacon.shared_admission import SharedAdmission
from tests.unit.domain_fixtures import NOW, context, known, notice
from tests.unit.test_firestore_store import extract
from tests.unit.test_guest_boundary import ORIGIN, MemoryObjects
from tests.unit.test_shared_admission import env as env

pytestmark = pytest.mark.skipif(not os.environ.get("BATCHBEACON_EMULATOR_CONFIG"),
                                reason="explicit admitted loopback emulator required")


def seed(stores, record):
    name = stores.name("environment")
    def change(tx):
        old = tx.read({name: "environment"})[name]
        tx.write(name, "environment", record, create=old is None)
    stores.run(change)


def open_instance(policy, now, objects):
    channel = grpc.insecure_channel(policy.api_endpoint)
    transport = FirestoreGrpcTransport(channel=channel, credentials=AnonymousCredentials(),
                                        host=policy.api_endpoint)
    client = FirestoreClient(transport=transport,
        client_options=ClientOptions(api_endpoint=policy.api_endpoint))
    gp, ep, ap = GuestPolicy(origin=ORIGIN), EvidencePolicy(), ActionPolicy()
    stores = FirestoreStores(client, policy, gp, ep, ap, clock=lambda: now[0])
    guest = GuestService(gp, stores.guests, objects, clock=lambda: now[0])
    evidence = EvidenceService(guest, stores.evidence, ep)
    actions = ActionService(evidence, stores.actions, ap)
    return (stores, None, guest, evidence, actions, now), channel


@pytest.fixture
def runtime(monkeypatch):
    def no_credentials(*args, **kwargs):
        raise AssertionError("emulator must never discover credentials")
    monkeypatch.setattr(google.auth, "default", no_credentials)
    config = json.loads(Path(os.environ["BATCHBEACON_EMULATOR_CONFIG"]).read_text())
    assert config["host"] == "127.0.0.1" and config["project_id"].startswith("demo-")
    endpoint = f'127.0.0.1:{config["rpc_port"]}'
    policy = FirestorePolicy(project_id=config["project_id"], database_id=config["database_id"],
        namespace="integration_" + uuid4().hex, environment_id="first_slice",
        mode="emulator", api_endpoint=endpoint, rpc_seconds=config["rpc_seconds"],
        operation_seconds=config["operation_seconds"], cleanup_seconds=config["cleanup_seconds"],
        max_transaction_attempts=config["transaction_attempts"])
    now, objects = [NOW], MemoryObjects()
    channels, instances = [], []
    for _ in range(2):
        instance, channel = open_instance(policy, now, objects)
        channels.append(channel)
        instances.append(instance)
    seed(instances[0][0], EvidenceEnvironment(context=context(), notices=(notice(),),
                                              verifier_policy=VerifierPolicy()))
    yield instances
    for channel in channels:
        channel.close()


def prepared(runtime, env):
    first = runtime[0]
    stores, _, guest, evidence, actions, _ = first
    token, session = guest.issue()
    incident = guest.create_incident(token, "first")
    envelope = extract(first, token, incident)
    policy = replace(env[0].policy, project_id=stores.policy.project_id)
    grant = replace(env[0].grant, project_id=policy.project_id, policy_hash=policy.digest())
    admission = SharedAdmission(policy, grant, stores.shared, clock=lambda: first[5][0])
    binding = evidence.verification_binding(token, incident.id)
    admission.reserve_verification(session.capability_hash, incident.id, "verify", binding)
    evidence.publish_verification(token, incident.id, "verify", binding)
    target = actions.prepare(token, incident.id, ActionType.SIMULATED_HOLD)
    return token, session, incident, envelope, ActionConfirmation(
        target=target, explicit_confirmation=True)


def test_fresh_guest_atomic_creation_and_independent_client_restart(runtime):
    first, second = runtime
    token, session = first[2].issue()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(r[2].create_incident, token, "same") for r in runtime]
        incidents = [f.result() for f in futures]
    assert incidents[0] == incidents[1]
    iid = incidents[0].id
    assert len(second[2].resolve(token).incidents) == 1
    assert second[3].read_evidence(token, iid).observation is None
    assert second[4].list_actions(token, iid) == ()
    stores = second[0]
    budget = stores.run(lambda tx: tx.read({stores.name("budget"): "budget"}))
    assert budget[stores.name("budget")] is None
    cold, channel = open_instance(stores.policy, first[5], first[2].objects)
    try:
        assert cold[2].resolve(token).incidents[0].id == iid
        assert cold[3].read_evidence(token, iid).state.incident_id == iid
    finally:
        channel.close()


def test_lost_ack_after_actual_commit_reconciles_on_other_client(runtime):
    first, second = runtime
    token, session = first[2].issue()
    call = first[0]._call
    def lost(method, request, *args):
        result = call(method, request, *args)
        if method == "commit" and len(request.writes) == 4:
            raise exceptions.DeadlineExceeded("injected response loss after real emulator commit")
        return result
    first[0]._call = lost
    with pytest.raises(GuestDenied):
        first[2].create_incident(token, "lost")
    retained = second[2].resolve(token)
    assert len(retained.incidents) == 1
    reconciled = second[2].create_incident(token, "lost")
    assert reconciled == retained.incidents[0]
    assert second[3].read_evidence(token, reconciled.id).observation is None


def test_concurrent_confirmation_then_correction_preserves_history(runtime, env):
    token, session, incident, envelope, command = prepared(runtime, env)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(r[4].confirm, token, incident.id, f"confirm-{i}", command)
                   for i, r in enumerate(runtime)]
        views = [f.result() for f in futures]
    assert views[0].action.id == views[1].action.id
    assert len(runtime[1][4].list_actions(token, incident.id)) == 1
    runtime[0][3].correct(token, incident.id, "lot-edit", 1, "LOT",
                         known("000aB", evidence=envelope.captures[0]))
    reread = runtime[1][3].read_evidence(token, incident.id)
    assert not reread.current
    assert reread.state.observations[0].observation.fields[0].observation.value == "232511"
    assert reread.observation.fields[0].observation.value == "000aB"
    assert runtime[1][4].get_action(token, incident.id, views[0].action.id).requires_renewed_review


def test_source_update_racing_confirmation_never_renews_old_result(runtime, env):
    token, session, incident, _, command = prepared(runtime, env)
    source = notice().dependency
    changed = EvidenceEnvironment(context=replace(context(),
        current_sources=(replace(source, epoch=source.epoch + 1),)),
        notices=(notice(),), verifier_policy=VerifierPolicy())
    def confirm():
        try:
            return runtime[0][4].confirm(token, incident.id, "race", command)
        except GuestDenied as exc:
            assert exc.status in {409, 503}  # bounded contention may require renewed review
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        action = pool.submit(confirm)
        update = pool.submit(seed, runtime[1][0], changed)
        update.result()
        result = action.result()
    assert not runtime[1][3].read_evidence(token, incident.id).current
    if result:
        history = runtime[1][4].get_action(token, incident.id, result.action.id)
        assert history.requires_renewed_review
    with pytest.raises(GuestDenied):
        runtime[1][4].prepare(token, incident.id, ActionType.SIMULATED_HOLD)


def test_nonbillable_settlement_is_atomic_across_independent_clients(runtime, env):
    from batchbeacon.shared_admission import Attempt, Pool, SharedDenied
    from tests.unit.test_nonbillable_reconciliation import failed, policy
    first = runtime[0]
    token, session = first[2].issue()
    incident = first[2].create_incident(token, 'nonbillable')
    sp = replace(env[0].policy, project_id=first[0].policy.project_id)
    grant = replace(env[0].grant, project_id=sp.project_id, policy_hash=sp.digest())
    services = [SharedAdmission(sp, grant, r[0].shared, clock=lambda: first[5][0])
                for r in runtime]
    services[0].initialize(env[7])
    services[0].activate_phase(env[1].state().phase)
    local = (services[0], first[0].shared, first[2], token, session.capability_hash,
             incident.id, first[5], env[7])
    rule = policy(local)
    for service in services:
        service.nonbillable_policy = rule
    attempt, run = failed(local)
    def read(kind, identifier=None):
        stores = runtime[1][0]
        name = stores.name(kind, identifier) if identifier else stores.name(kind)
        return stores.run(lambda tx: tx.read({name: kind}))[name]
    before = read('budget')
    def new_run():
        return services[1].admit_run(session.capability_hash, incident.id,
                                     'after-settlement', run.binding)
    assert services[1].reconciliation_required(session.capability_hash)
    with pytest.raises(SharedDenied, match='requires operator review'):
        new_run()
    def racing_admission():
        try:
            result = new_run()
        except SharedDenied:
            return None
        # Settlement is monotonic: a new run can only commit after that receipt.
        assert read('attempt', attempt.id).actual_nanos == 0
        return result
    with ThreadPoolExecutor(max_workers=3) as pool:
        settlement = [pool.submit(service.reconcile, attempt.id) for service in services]
        admission = pool.submit(racing_admission)
        for future in settlement:
            future.result()
        admission.result()
    after, retained = read('budget'), read('attempt', attempt.id)
    assert isinstance(retained, Attempt) and retained.nonbillable_receipt
    assert retained.actual_nanos == 0 and retained.complete_usage is None
    assert after.balance(Pool.PUBLIC).reserved_nanos == 0
    assert after.balance(Pool.PUBLIC).incurred_nanos == before.balance(Pool.PUBLIC).incurred_nanos
    assert after.balance(Pool.PUBLIC).lifetime_attempts == 1
    assert after.phase == before.phase and after.grant_hash == before.grant_hash
    assert services[1].inspect_run(session.capability_hash, run.id).calls == 1
    assert not services[1].reconciliation_required(session.capability_hash)
    assert new_run().run.request_key == 'after-settlement'
    services[1].nonbillable_policy = None
    services[1].reconcile(attempt.id)
    assert read('budget') == after and read('attempt', attempt.id) == retained


def test_predecessor_settlement_across_independent_clients_preserves_authority(runtime, env):
    from batchbeacon.shared_admission import Address, Change, SharedDenied
    from tests.unit.durable_fixtures import record_wire, run_binding, wire_response
    from tests.unit.test_predecessor_liabilities import manifest

    first, second = runtime
    token, session = first[2].issue()
    incident = first[2].create_incident(token, 'predecessor')
    sp = replace(env[0].policy, project_id=first[0].policy.project_id)
    grant = replace(env[0].grant, project_id=sp.project_id, policy_hash=sp.digest())
    old = SharedAdmission(sp, grant, first[0].shared, clock=lambda: first[5][0])
    old.initialize(env[7])
    old.activate_phase(env[1].state().phase)
    run = old.begin_run(session.capability_hash, incident.id, 'original',
                        run_binding(first[2], token, incident.id))
    a = old.reserve(session.capability_hash, run.id, 'b' * 32, 'c' * 64,
                    operation_key='extract')
    a = old.claim_dispatch(session.capability_hash, run.id, a.id,
                            a.request_hash, a.model_configuration_hash)
    old.finish_run(session.capability_hash, run.id, failed=True)
    sp2 = replace(sp, run_seconds=50, model_configuration_hash='2' * 64)
    grant2 = replace(grant, policy_hash=sp2.digest())
    m = replace(manifest(old, sp2, grant2, a), namespace=first[0].policy.namespace,
                environment_id=first[0].policy.environment_id)
    def migrate(tx):
        name = first[0].name('budget')
        budget = tx.read({name: 'budget'})[name]
        assert budget.grant_hash == grant.digest()
        tx.write(name, 'budget', replace(budget, grant_hash=grant2.digest(),
                                         policy_hash=sp2.digest()))
        return budget
    before = first[0].run(migrate)
    services = []
    for instance in runtime:
        s = instance[0]
        store = FirestoreStores(s.client, s.policy, s.guest_policy, s.evidence_policy,
            s.action_policy, clock=s.clock, predecessor_liabilities=m)
        services.append(SharedAdmission(sp2, grant2, store.shared, clock=s.clock,
                                        predecessor_liabilities=m))
    def read(kind, identifier=None):
        name = second[0].name(kind, identifier) if identifier else second[0].name(kind)
        return second[0].run(lambda tx: tx.read({name: kind}))[name]
    for service in services:
        with pytest.raises(SharedDenied, match='complete usage unavailable'):
            service.reconcile(a.id)
        with pytest.raises(OSError):
            service.store.transact(Address(attempt_id=a.id), lambda s: Change(s.budget))
    with pytest.raises((ValueError, OSError)):
        old.claim_dispatch(session.capability_hash, run.id, a.id,
                            a.request_hash, a.model_configuration_hash)
    assert read('budget').balances == before.balances
    record_wire(services[0], a, wire_response(100, 10))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda service: service.reconcile(a.id), services))
    after, retained = read('budget'), read('attempt', a.id)
    assert retained.actual_nanos == a.price.cost_nanos(100, 10)
    assert retained.grant_hash == grant.digest() and retained.policy_hash == sp.digest()
    assert after.balance(a.pool).incurred_nanos == (
        before.balance(a.pool).incurred_nanos + retained.actual_nanos)
    assert after.balance(a.pool).reserved_nanos == 0
    assert after.balance(a.pool).lifetime_attempts == 1
    assert after.phase == before.phase and after.circuit == before.circuit
    assert after.grant_hash == grant2.digest() and after.policy_hash == sp2.digest()
    services[1].reconcile(a.id)
    assert read('budget') == after and read('attempt', a.id) == retained


def test_permanent_admission_epoch_rejects_old_client_preserving_counters(runtime):
    from datetime import timedelta

    from batchbeacon.guest_admission import GuestAdmissionPolicy, GuestAdmissionState

    old, new = runtime
    before = GuestAdmissionPolicy(max_issued_sessions=None, max_sessions_per_window=30,
        window_seconds=60, not_before=NOW, expires_at=NOW + timedelta(days=1))
    after = before.model_copy(update={"version": "guest-admission-2"})
    old[0].guest_admission = before
    new[0].guest_admission = after
    original = GuestAdmissionState(policy_hash=before.digest(), issued_sessions=27,
        window_started_at=NOW, window_issued=3)
    name = old[0].name("guest_admission")
    def initialize(tx):
        assert tx.read({name: "guest_admission"})[name] is None
        tx.write(name, "guest_admission", original, create=True)
    old[0].run(initialize)
    migrated = original.model_copy(update={"policy_hash": after.digest()})

    def migrate(tx):
        assert tx.read({name: "guest_admission"})[name] == original
        tx.write(name, "guest_admission", migrated, create=False)
    new[0].run(migrate)
    with pytest.raises(GuestDenied, match="demo_guest_capacity_unavailable"):
        old[2].issue()
    assert new[0].run(lambda tx: tx.read({name: "guest_admission"})[name]) == migrated
    new[2].issue()
    recorded = new[0].run(lambda tx: tx.read({name: "guest_admission"})[name])
    assert recorded == migrated.model_copy(update={"issued_sessions": 28, "window_issued": 4})
    with pytest.raises(GuestDenied, match="demo_guest_capacity_unavailable"):
        old[2].issue()
    assert new[0].run(lambda tx: tx.read({name: "guest_admission"})[name]) == recorded


def test_cached_usage_settlement_is_atomic_and_keeps_failed_run(runtime, env):
    from batchbeacon.shared_admission import Pool
    from tests.unit.durable_fixtures import record_wire, run_binding, wire_response

    first = runtime[0]
    token, session = first[2].issue()
    incident = first[2].create_incident(token, 'cache-accounting')
    policy = replace(env[0].policy, project_id=first[0].policy.project_id)
    grant = replace(env[0].grant, project_id=policy.project_id, policy_hash=policy.digest())
    services = [SharedAdmission(policy, grant, r[0].shared, clock=lambda: first[5][0])
                for r in runtime]
    services[0].initialize(env[7])
    services[0].activate_phase(env[1].state().phase)
    run = services[0].begin_run(session.capability_hash, incident.id, 'cached',
                                run_binding(first[2], token, incident.id))
    attempt = services[0].reserve(session.capability_hash, run.id, 'b' * 32, 'c' * 64,
                                  operation_key='extract')
    services[0].claim_dispatch(session.capability_hash, run.id, attempt.id,
                               attempt.request_hash, attempt.model_configuration_hash)
    services[0].finish_run(session.capability_hash, run.id, failed=True)
    body = json.loads(wire_response(100, 10, 5))
    body['usageMetadata']['cachedContentTokenCount'] = 90
    record_wire(services[0], attempt, json.dumps(body).encode())

    def read(kind, identifier=None):
        stores = runtime[1][0]
        name = stores.name(kind, identifier) if identifier else stores.name(kind)
        return stores.run(lambda tx: tx.read({name: kind}))[name]

    before = read('budget')
    failed_run = services[1].inspect_run(session.capability_hash, run.id)
    assert services[1].reconciliation_required(session.capability_hash)
    assert read('budget') == before  # Status GET never settles retained cache evidence.
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda service: service.reconcile(attempt.id), services))
    after, receipt = read('budget'), read('attempt', attempt.id)
    cost = attempt.price.cost_nanos(100, 15)
    assert receipt.actual_nanos == cost and receipt.complete_usage.input_tokens == 100
    assert receipt.usage_hash == receipt.complete_usage.digest()
    assert after.balance(Pool.PUBLIC).reserved_nanos == 0
    assert after.balance(Pool.PUBLIC).incurred_nanos == (
        before.balance(Pool.PUBLIC).incurred_nanos + cost)
    assert after.balance(Pool.PUBLIC).lifetime_attempts == 1
    assert services[1].inspect_run(session.capability_hash, run.id) == failed_run
    assert failed_run.terminal == 'failed' and failed_run.completion_hash is None
    services[0].reconcile(attempt.id)
    assert read('budget') == after and read('attempt', attempt.id) == receipt

"""Run/completion integration using the actual SDK with an explicit RPC fake."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from google.cloud.firestore_v1.types import Document

from batchbeacon.action_service import ActionConfirmation, ActionService
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import EvidenceService, replace
from batchbeacon.firestore_store import FirestoreStores
from batchbeacon.guest_service import GuestDenied, GuestService
from batchbeacon.shared_admission import SharedDenied
from tests.unit.domain_fixtures import known, notice
from tests.unit.durable_fixtures import run_binding
from tests.unit.firestore_rpc_fake import client
from tests.unit.test_firestore_store import extract, owned, publish, saved, shared
from tests.unit.test_firestore_store import setup as setup  # noqa: F401
from tests.unit.test_shared_admission import env as env  # noqa: F401


@pytest.fixture
def acquisition(setup, env):
    stores, server, guest, evidence, actions, now = setup
    server.clock = lambda: now[0]
    token, session, incident = owned(setup)
    envelope = extract(setup, token, incident)
    publish(setup, env, token, session, incident)
    admission = shared(setup, env)
    server.seed(stores._encode(stores.name('budget'), 'budget', env[1].state()))
    binding = run_binding(guest, token, incident.id)
    binding = replace(binding, expected_observation_revision=1,
        manifest=replace(binding.manifest, source=envelope.sources[0],
                         notice_digest=notice().digest(),
                         prompt_version=envelope.prompt_version))
    return setup, admission, token, session, incident, envelope, binding


def start(a, key='acquire', **kwargs):
    _, service, _, session, incident, _, binding = a
    return service.admit_run(session.capability_hash, incident.id, key, binding, **kwargs)


def stage(a, run):
    setup, shared_service, token, session, incident, envelope, _ = a
    evidence = setup[3]
    evidence.record_extraction(token, incident.id, 'run-extract', 1,
                               envelope, run_id=run.id)
    binding = evidence.verification_binding(token, incident.id, run_id=run.id)
    shared_service.reserve_verification(session.capability_hash, incident.id, 'run-verify', binding)
    evidence.publish_verification(token, incident.id, 'run-verify', binding, run_id=run.id)


def complete(a, run):
    setup, _, token, _, incident, _, _ = a
    return setup[3].complete_acquisition(token, incident.id, run.id, 'run-extract', 'run-verify')


def view(a):
    return a[0][3].read_evidence(a[2], a[4].id)


def test_fresh_disposition_concurrent_replay_has_one_executor(acquisition):
    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(lambda _: start(acquisition), range(2)))
    assert sum(r.fresh for r in results) == 1
    assert results[0].run.id == results[1].run.id
    assert not start(acquisition).fresh
    assert not view(acquisition).current


def test_lost_admission_ack_reconstructs_without_fresh_execution(acquisition):
    a = acquisition
    server = a[0][1]
    def lost(request):
        if any(w.update.name.endswith('usage-' + a[3].capability_hash) for w in request.writes):
            raise OSError('injected lost admission acknowledgment')
    server.after_commit = lost
    with pytest.raises(OSError):
        start(a)
    server.after_commit = lambda _: None
    assert not start(a).fresh
    assert not view(a).current


def test_earlier_absolute_deadline_is_preserved_on_replay(acquisition):
    now = acquisition[0][5][0]
    run = start(acquisition, not_after=now + timedelta(seconds=2)).run
    assert run.deadline == now + timedelta(seconds=2)
    acquisition[0][5][0] += timedelta(seconds=3)
    repeated = start(acquisition, not_after=now + timedelta(days=1))
    assert not repeated.fresh and repeated.run.deadline == run.deadline


@pytest.mark.parametrize('elapsed', [0, 1])
def test_expired_preparation_cannot_acquire(acquisition, elapsed):
    now = acquisition[0][5][0]
    with pytest.raises(SharedDenied):
        start(acquisition, not_after=now - timedelta(seconds=elapsed))


@pytest.mark.parametrize('terminal', [None, 'failed', 'timed_out', 'completed'])
def test_new_acquisition_never_revives_old_result_without_completion(acquisition, terminal):
    a = acquisition
    actions = a[0][4]
    target = actions.prepare(a[2], a[4].id, ActionType.SIMULATED_HOLD)
    run = start(a).run
    if terminal is not None:
        stores, server = a[0][:2]
        usage = saved(a[0], 'usage', a[3].capability_hash)
        usage = replace(usage, runs=(replace(run, terminal=terminal),))
        server.seed(stores._encode(stores.name('usage', a[3].capability_hash), 'usage', usage))
    assert not view(a).current and not view(a).hold_eligible
    with pytest.raises(GuestDenied):
        a[0][3].verification_binding(a[2], a[4].id)
    with pytest.raises(GuestDenied):
        a[0][3].correct(a[2], a[4].id, 'edit', 1, 'LOT',
                       known('232511', evidence=a[5].captures[0]))
    with pytest.raises(GuestDenied):
        actions.confirm(a[2], a[4].id, 'hold',
                        ActionConfirmation(target=target, explicit_confirmation=True))


def test_candidate_is_ineligible_until_immutable_timely_completion(acquisition):
    a = acquisition
    run = start(a).run
    stage(a, run)
    assert view(a).result is not None and not view(a).current
    with pytest.raises(GuestDenied):
        a[0][4].prepare(a[2], a[4].id, ActionType.SIMULATED_HOLD)
    assert complete(a, run).hold_eligible
    stores, server = a[0][:2]
    name = stores.name('completion', run.id)
    original = Document(server.docs[name])
    a[0][5][0] += timedelta(seconds=31)
    assert complete(a, run).current  # Reconcile original on-time proof, no new publication.
    assert Document(server.docs[name]) == original
    a[0][3].correct(a[2], a[4].id, 'edit', 2, 'LOT',
                   known('232511', evidence=a[5].captures[0]))
    assert not view(a).current
    binding = a[0][3].verification_binding(a[2], a[4].id)
    a[1].reserve_verification(a[3].capability_hash, a[4].id, 'reverify', binding)
    a[0][3].publish_verification(a[2], a[4].id, 'reverify', binding)
    assert view(a).current
    assert Document(server.docs[name]) == original


@pytest.mark.parametrize('delta,eligible', [(-1, True), (0, False), (1, False)])
def test_server_creation_time_controls_eligibility_even_when_client_clock_is_earlier(
        acquisition, delta, eligible):
    a = acquisition
    run = start(a).run
    stage(a, run)
    a[0][1].clock = lambda: run.deadline + timedelta(microseconds=delta)
    assert complete(a, run).current == eligible
    assert view(a).hold_eligible == eligible
    if not eligible:
        with pytest.raises(GuestDenied):
            a[0][4].prepare(a[2], a[4].id, ActionType.SIMULATED_HOLD)
        with pytest.raises(GuestDenied):
            a[0][3].verification_binding(a[2], a[4].id)


def test_late_ack_throws_but_cold_read_resolves_ontime_commit(acquisition):
    a = acquisition
    run = start(a).run
    stage(a, run)
    stores, server, guest, evidence, actions, now = a[0]
    name = stores.name('completion', run.id)
    def delay(request):
        if any(w.update.name == name for w in request.writes):
            now[0] = run.deadline
    server.after_commit = delay
    with pytest.raises(GuestDenied):
        complete(a, run)
    server.after_commit = lambda _: None
    cold = FirestoreStores(client(server), stores.policy, guest.policy, evidence.policy,
                           actions.policy, clock=lambda: now[0])
    cold_guest = GuestService(guest.policy, cold.guests, guest.objects, clock=lambda: now[0])
    cold_evidence = EvidenceService(cold_guest, cold.evidence, evidence.policy)
    assert cold_evidence.read_evidence(a[2], a[4].id).hold_eligible
    cold_actions = ActionService(cold_evidence, cold.actions, actions.policy)
    assert cold_actions.prepare(a[2], a[4].id, ActionType.SIMULATED_HOLD)


@pytest.mark.parametrize('damage', ['missing_created', 'missing_updated', 'changed_updated',
    'changed_hash', 'wrong_run', 'wrong_deadline', 'wrong_result', 'missing'])
def test_bad_completion_proof_is_never_current(acquisition, damage):
    a = acquisition
    run = start(a).run
    stage(a, run)
    complete(a, run)
    stores, server = a[0][:2]
    name = stores.name('completion', run.id)
    document = Document(server.docs[name])
    if damage == 'missing':
        del server.docs[name]
    elif damage.startswith('missing_'):
        Document.pb(document).ClearField('create_time' if damage == 'missing_created'
                                         else 'update_time')
        server.docs[name] = document
    elif damage == 'changed_updated':
        document.update_time = run.started_at + timedelta(seconds=1)
        server.docs[name] = document
    else:
        record = saved(a[0], 'completion', run.id)
        changes = {'changed_hash': {'binding_hash': 'b'*64},
            'wrong_run': {'run_id': 'b'*32},
            'wrong_deadline': {'deadline': run.deadline + timedelta(1)},
            'wrong_result': {'result_hash': 'b'*64}}[damage]
        document.fields['payload'].string_value = replace(record, **changes).model_dump_json()
        server.docs[name] = document
    try:
        assert not view(a).current
    except GuestDenied:
        pass
    with pytest.raises(GuestDenied):
        a[0][4].prepare(a[2], a[4].id, ActionType.SIMULATED_HOLD)


@pytest.mark.parametrize('mutation', ['configuration_hash', 'prompt_version', 'sources',
                                     'started_at', 'completed_at'])
def test_publication_must_bind_running_acquisition(acquisition, mutation):
    a = acquisition
    run = start(a).run
    value = {'configuration_hash': 'c'*64, 'prompt_version': 'changed', 'sources': (),
             'started_at': run.started_at-timedelta(seconds=1),
             'completed_at': run.deadline}[mutation]
    envelope = replace(a[5], **{mutation: value})
    if mutation == 'completed_at':
        a[0][5][0] = run.deadline
    with pytest.raises(GuestDenied):
        a[0][3].record_extraction(a[2], a[4].id, 'run-extract', 1, envelope, run_id=run.id)
    assert len(view(a).state.extractions) == 1


def test_unbound_live_and_bypass_after_run_are_denied(acquisition):
    a = acquisition
    with pytest.raises(GuestDenied):
        a[0][3].record_extraction(a[2], a[4].id, 'live', 1,
                                  replace(a[5], provenance='live'))
    start(a)
    with pytest.raises(GuestDenied):
        a[0][3].record_extraction(a[2], a[4].id, 'fake-bypass', 1, a[5])


def test_initial_completion_response_rechecks_after_retained_input_read(acquisition):
    a = acquisition
    run = start(a).run
    stage(a, run)
    objects = a[0][2].objects
    original_get = objects.get
    def delayed_get(*args, **kwargs):
        value = original_get(*args, **kwargs)
        a[0][5][0] = run.deadline
        return value
    objects.get = delayed_get
    with pytest.raises(GuestDenied, match='acquisition_deadline_elapsed'):
        complete(a, run)
    objects.get = original_get
    assert view(a).current  # Subsequent status resolves the on-time committed proof.


def test_missing_established_completion_cannot_be_recreated(acquisition):
    a = acquisition
    run = start(a).run
    stage(a, run)
    assert complete(a, run).current
    stores, server = a[0][:2]
    name = stores.name('completion', run.id)
    del server.docs[name]
    a[0][5][0] += timedelta(seconds=1)
    assert not view(a).current
    with pytest.raises(GuestDenied):
        complete(a, run)
    assert name not in server.docs

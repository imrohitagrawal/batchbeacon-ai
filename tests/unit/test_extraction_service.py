"""Owned coordinator through installed ADK/Firestore SDK and explicit transport fakes."""

import asyncio
import copy
import json
from importlib.metadata import version

import httpx
import pytest

from batchbeacon.action_service import ActionConfirmation
from batchbeacon.contracts import ActionType
from batchbeacon.evidence_service import EvidenceEnvironment, replace
from batchbeacon.extraction_service import AcquisitionCommand, ExtractionService, SourceBundle
from batchbeacon.model_runtime import ExtractionConfig
from batchbeacon.shared_admission import SharedAdmission
from batchbeacon.uploads import sanitize_images
from tests.unit.domain_fixtures import context
from tests.unit.durable_fixtures import wire_response
from tests.unit.test_extraction_proposal import rig
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import owned, saved
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_guest_boundary import picture
from tests.unit.test_probe_runner import credentials
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def coordinator(setup, env, request):
    stores, server, guest, evidence, actions, now = setup
    server.clock = lambda: now[0]
    config = ExtractionConfig(mode='offline_test', project_id='synthetic-project',
        model_id='gemini-3.8-flash', model_location='global', api_version='v1beta1',
        adk_version=version('google-adk'), genai_version=version('google-genai'),
        **getattr(request, 'param', {}))
    p = replace(env[0].policy, model_configuration_hash=config.digest(),
                run_seconds=config.run_seconds)
    grant = replace(env[0].grant, policy_hash=p.digest())
    shared = SharedAdmission(p, grant, stores.shared, clock=lambda: now[0])
    shared.initialize(env[7])
    shared.activate_phase(env[1].state().phase)
    token, session, incident = owned(setup)
    batch = guest.retain(token, incident.id, 'upload',
        sanitize_images((picture(), picture()), guest.policy.uploads))
    proposal, source, notice, _ = rig()
    old_environment = saved(setup, 'environment')
    environment = EvidenceEnvironment(context=replace(context(),
        current_sources=(notice.dependency,)), notices=(notice,),
        verifier_policy=old_environment.verifier_policy)
    server.seed(stores._encode(stores.name('environment'), 'environment', environment))
    calls, output = [], [proposal]
    async def fake(request):
        calls.append(request)
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        raw = output[0] if isinstance(output[0], bytes) else wire_response(candidates=[{
            'content': {'role': 'model', 'parts': [{'text': json.dumps(output[0])}]},
            'finishReason': 'STOP', 'index': 0}])
        return httpx.Response(200, content=raw)
    service = ExtractionService(evidence, shared, config, {'first': SourceBundle(notice, source)},
        transport_factory=lambda: httpx.MockTransport(fake), credentials_factory=credentials)
    command = AcquisitionCommand(incident_id=incident.id, request_key='first-extraction',
        source_selection='first', capture_ids=tuple(c.id for c in batch.captures),
        expected_observation_revision=0)
    return service, command, token, setup, calls, output, session


def acquire(c, command=None):
    return asyncio.run(c[0].acquire(c[2], command or c[1]))


def test_owned_success_publishes_once_completes_and_action_survives_refresh(coordinator):
    c = coordinator
    status = acquire(c)
    assert status.state == 'COMPLETE' and status.current
    assert (status.extraction_revision, status.observation_revision,
            status.result_revision) == (1, 1, 1)
    assert len(c[4]) == 2
    assert acquire(c) == status and len(c[4]) == 2
    assert c[0].status_for_key(c[2], c[1].incident_id, c[1].request_key) == status
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert view.hold_eligible
    assert view.state.extractions[0].envelope.provenance == 'fake'
    summary = view.state.extractions[0].envelope.redacted_output_json
    assert c[0].sources['first'].original.decode() not in summary
    assert c[5][0]['label']['name']['value'] not in summary
    actions = c[3][4]
    target = actions.prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)
    action = actions.confirm(c[2], c[1].incident_id, 'hold',
                            ActionConfirmation(target=target, explicit_confirmation=True))
    assert action
    assert c[0].status(c[2], status.run_id).current


def test_source_disagreement_retains_diagnostic_without_values_or_completion(coordinator):
    c = coordinator
    c[5][0] = copy.deepcopy(c[5][0])
    c[5][0]['source']['products'].pop()
    status = acquire(c)
    assert status.state == 'FAILED' and status.diagnostics == ('SOURCE_DISAGREEMENT',)
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert len(view.state.extractions) == 1
    assert not view.state.observations and not view.state.results
    assert view.state.extractions[0].envelope.values is None
    run = c[0].shared.inspect_run(c[6].capability_hash, status.run_id)
    assert run.terminal == 'failed' and run.completion_hash is None
    assert acquire(c).state == 'FAILED' and len(c[4]) == 2


def test_typed_missing_date_remains_review_required_without_fabrication(coordinator):
    from tests.unit.test_extraction_proposal import unknown
    c = coordinator
    c[5][0]['label']['best_before'] = unknown()
    status = acquire(c)
    assert status.state == 'REVIEW_REQUIRED' and status.current
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert not view.hold_eligible and view.result.outstanding_fields
    date = next(f.observation for f in view.observation.fields if f.field == 'BEST_BEFORE')
    assert date.state == 'UNKNOWN' and date.value is None


@pytest.mark.parametrize('failure', ['proposal', 'provider_json', 'transport'])
def test_failure_has_bounded_owned_status_and_no_invented_observation(coordinator, failure):
    c = coordinator
    if failure == 'proposal':
        c[5][0]['unexpected_private_key'] = 'private-output-marker'
    elif failure == 'provider_json':
        c[5][0] = b'{"broken":"private-output-marker"'
    else:
        def fail(request):
            raise OSError('private-output-marker')
        c[0].transport_factory = lambda: httpx.MockTransport(fail)
    status = acquire(c)
    assert status.state == 'FAILED' and not status.current
    assert 'private-output-marker' not in status.model_dump_json()
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert not view.state.observations and not view.state.results
    assert len(view.state.extractions) == (1 if failure == 'proposal' else 0)


def test_transport_unknown_blocks_new_generation_until_original_usage_settles(coordinator):
    from batchbeacon.guest_service import GuestDenied
    from tests.unit.durable_fixtures import record_wire
    c = coordinator
    requests = []
    async def provider(request):
        requests.append(request)
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        raise httpx.ReadTimeout('unknown original response', request=request)
    c[0].transport_factory = lambda: httpx.MockTransport(provider)
    first = acquire(c)
    assert first.state == 'FAILED' and first.reconciliation_required
    run = c[0].shared.inspect_run(c[6].capability_hash, first.run_id)
    attempt = saved(c[3], 'attempt', run.attempt_ids[0])
    assert attempt.dispatch_claimed and attempt.response is None and attempt.actual_nanos is None
    before = saved(c[3], 'budget'), saved(c[3], 'usage', c[6].capability_hash)
    assert acquire(c) == first
    with pytest.raises(GuestDenied):
        acquire(c, replace(c[1], request_key='different-key'))
    assert len(requests) == 2  # countTokens plus original generation only.
    assert (saved(c[3], 'budget'), saved(c[3], 'usage', c[6].capability_hash)) == before
    # An offline retained-original receipt settles liability, never invents a result.
    record_wire(c[0].shared, attempt)
    c[0].shared.reconcile(attempt.id)
    after = c[0].status(c[2], first.run_id)
    assert after.state == 'FAILED' and not after.reconciliation_required and not after.current
    admitted = c[0].shared.admit_run(c[6].capability_hash, run.incident_id,
                                    'after-settlement', run.binding)
    assert admitted.fresh and len(requests) == 2


def test_settled_invalid_proposal_can_be_explicitly_retried(coordinator):
    c = coordinator
    c[5][0]['unexpected_field'] = 'invalid'
    first = acquire(c)
    assert first.state == 'FAILED' and not first.reconciliation_required
    second = acquire(c, replace(c[1], request_key='explicit-retry'))
    assert second.run_id != first.run_id and not second.reconciliation_required
    assert len(c[4]) == 4


@pytest.mark.parametrize('change', ['source', 'capture', 'duplicates', 'revision'])
def test_invalid_selection_denied_before_any_model_call(coordinator, change):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    updates = {'source': {'source_selection': 'unknown'}, 'capture': {'capture_ids': ('b'*32,)},
        'duplicates': {'capture_ids': (c[1].capture_ids[0], c[1].capture_ids[0])},
        'revision': {'expected_observation_revision': 1}}[change]
    with pytest.raises(GuestDenied):
        acquire(c, replace(c[1], **updates))
    assert not c[4]
    assert not saved(c[3], 'usage', c[6].capability_hash).runs


@pytest.mark.parametrize('mutation', ['missing', 'changed'])
def test_original_retained_bytes_required_before_admission(coordinator, mutation):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    objects = c[3][2].objects
    key = next(iter(objects.data))
    if mutation == 'missing':
        del objects.data[key]
    else:
        objects.data[key] = b'changed'
    with pytest.raises(GuestDenied):
        acquire(c)
    assert not c[4] and not saved(c[3], 'usage', c[6].capability_hash).runs


def test_missing_human_review_denied_before_admission(coordinator):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    bundle = c[0].sources['first']
    notice = replace(bundle.notice, review=None)
    c[0].sources = {'first': SourceBundle(notice, bundle.original)}
    stores, server = c[3][:2]
    environment = replace(saved(c[3], 'environment'), notices=(notice,))
    server.seed(stores._encode(stores.name('environment'), 'environment', environment))
    with pytest.raises(GuestDenied, match='source_review_required'):
        acquire(c)
    assert not c[4] and not saved(c[3], 'usage', c[6].capability_hash).runs


@pytest.mark.parametrize('field',
                         ['source_selection', 'capture_ids', 'expected_observation_revision'])
def test_reused_request_key_cannot_change_command(coordinator, field):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    acquire(c)
    value = {'source_selection': 'different', 'capture_ids': tuple(reversed(c[1].capture_ids)),
             'expected_observation_revision': 1}[field]
    with pytest.raises(GuestDenied, match='acquisition_request_conflict'):
        acquire(c, replace(c[1], **{field: value}))
    assert len(c[4]) == 2


def test_replay_and_status_do_not_rebuild_source_or_restart_model(coordinator):
    c = coordinator
    status = acquire(c)
    c[0].sources = {}
    def forbidden():
        raise AssertionError('status must not construct model transport')
    c[0].transport_factory = forbidden
    assert acquire(c) == status
    assert c[0].status_for_key(c[2], c[1].incident_id, c[1].request_key) == status
    assert len(c[4]) == 2


def test_failed_new_acquisition_invalidates_old_result_without_fake_negative(coordinator):
    c = coordinator
    old = acquire(c)
    c[5][0] = b'{'
    newer = acquire(c, replace(c[1], request_key='second', expected_observation_revision=1))
    assert newer.state == 'FAILED' and not newer.current
    assert c[0].status(c[2], old.run_id).state == 'SUPERSEDED'
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert not view.current and len(view.state.observations) == 1 and len(view.state.results) == 1


@pytest.mark.parametrize('mutation', ['epoch', 'review'])
def test_source_change_during_generation_denies_publication(coordinator, mutation):
    c = coordinator
    stores, server = c[3][:2]
    original = c[0].evidence.record_extraction
    def changed(*args, **kwargs):
        env = saved(c[3], 'environment')
        if mutation == 'epoch':
            context = replace(env.context, current_sources=(replace(
                env.notices[0].dependency, epoch=2),))
            env = replace(env, context=context)
        else:
            env = replace(env, notices=(replace(env.notices[0], review=None),))
        server.seed(stores._encode(stores.name('environment'), 'environment', env))
        return original(*args, **kwargs)
    c[0].evidence.record_extraction = changed
    status = acquire(c)
    assert status.state == 'FAILED' and not status.current
    assert not c[3][3].read_evidence(c[2], c[1].incident_id).state.observations
    assert len(c[4]) == 2


def test_lost_admission_ack_status_recovers_identity_without_dispatch(coordinator):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    server = c[3][1]
    def lost(request):
        if any('usage-' in w.update.name for w in request.writes):
            raise OSError('private-lost-admission')
    server.after_commit = lost
    with pytest.raises((OSError, GuestDenied)):
        acquire(c)
    server.after_commit = lambda _: None
    status = c[0].status_for_key(c[2], c[1].incident_id, c[1].request_key)
    assert status.state == 'INCOMPLETE' and not status.current
    assert acquire(c) == status and not c[4]


@pytest.mark.parametrize('phase', ['extraction', 'verification', 'completion'])
def test_lost_publication_ack_recovers_status_without_model(coordinator, phase):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    method = {'extraction': 'record_extraction', 'verification': 'publish_verification',
              'completion': 'complete_acquisition'}[phase]
    original = getattr(c[0].evidence, method)
    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError('private-lost-publication')
    setattr(c[0].evidence, method, lost)
    with pytest.raises(GuestDenied, match='acquisition_outcome_unknown') as error:
        acquire(c)
    assert error.value.__context__ is None
    status = c[0].status_for_key(c[2], c[1].incident_id, c[1].request_key)
    assert status.current == (phase == 'completion')
    assert acquire(c) == status and len(c[4]) == 2
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert len(view.state.extractions) == 1


def test_preparation_is_inside_original_absolute_deadline(coordinator, monkeypatch):
    from datetime import timedelta

    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    original = c[3][2].image
    def slow(*args, **kwargs):
        data = original(*args, **kwargs)
        c[3][5][0] += timedelta(seconds=16)
        return data
    monkeypatch.setattr(c[3][2], 'image', slow)
    with pytest.raises(GuestDenied, match='acquisition_deadline_elapsed'):
        acquire(c)
    assert not c[4] and not saved(c[3], 'usage', c[6].capability_hash).runs


def test_status_and_commands_require_current_ownership(coordinator):
    from batchbeacon.guest_service import GuestDenied
    from batchbeacon.shared_admission import SharedDenied
    c = coordinator
    status = acquire(c)
    foreign, _ = c[3][2].issue()
    with pytest.raises((GuestDenied, SharedDenied)):
        c[0].status(foreign, status.run_id)
    with pytest.raises((GuestDenied, SharedDenied)):
        asyncio.run(c[0].acquire(foreign, c[1]))
    c[3][5][0] = c[6].scope.expires_at
    with pytest.raises((GuestDenied, SharedDenied)):
        c[0].status(c[2], status.run_id)
    assert len(c[4]) == 2


@pytest.mark.parametrize('field', ['provenance', 'configuration_hash', 'source_bytes', 'reviewed'])
def test_public_command_cannot_assert_authority(coordinator, field):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        AcquisitionCommand.model_validate(coordinator[1].model_dump() | {field: 'untrusted'})


@pytest.mark.parametrize('method', ['acquire', 'status', 'status_for_key'])
def test_storage_errors_at_owned_entry_points_are_sanitized(coordinator, monkeypatch, method):
    import traceback

    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    status = acquire(c)
    def fail(*args, **kwargs):
        raise OSError('private-storage-exception-marker')
    monkeypatch.setattr(c[0].shared.store, 'transact', fail)
    with pytest.raises(GuestDenied) as error:
        if method == 'acquire':
            acquire(c)
        elif method == 'status':
            c[0].status(c[2], status.run_id)
        else:
            c[0].status_for_key(c[2], c[1].incident_id, c[1].request_key)
    assert error.value.status == 503
    assert error.value.__context__ is None and error.value.__cause__ is None
    formatted = ''.join(traceback.format_exception(error.value))
    assert 'private-storage-exception-marker' not in formatted


@pytest.mark.parametrize('setup_seconds,expected_counts', [(0, 1), (5, 1), (31, 0)])
def test_preparation_monotonic_time_is_not_restarted_at_model_setup(
    coordinator, monkeypatch, setup_seconds, expected_counts
):
    from batchbeacon import extraction_service
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    original = extraction_service.prepare_input
    async def scenario():
        loop = asyncio.get_running_loop()
        virtual_now = [loop.time()]
        def slow(*args, **kwargs):
            value = original(*args, **kwargs)
            virtual_now[0] += 20 + setup_seconds
            return value
        async def fake(request):
            c[4].append(request)
            if str(request.url).endswith(':countTokens'):
                virtual_now[0] += 11
                # Exercise the actual asyncio timeout callback with host setup
                # time held constant; UTC stays fixed to isolate monotonic time.
                await asyncio.sleep(0)
                await asyncio.sleep(0)
                return httpx.Response(200, json={'totalTokens': 100})
            return httpx.Response(200, content=wire_response(candidates=[{
                'content': {'parts': [{'text': json.dumps(c[5][0])}]}, 'finishReason': 'STOP'}]))
        with monkeypatch.context() as patch:
            patch.setattr(loop, 'time', lambda: virtual_now[0])
            patch.setattr(extraction_service, 'prepare_input', slow)
            c[0].transport_factory = lambda: httpx.MockTransport(fake)
            with pytest.raises(GuestDenied, match='acquisition_deadline_elapsed'):
                await c[0].acquire(c[2], c[1])
    asyncio.run(scenario())
    assert len(c[4]) == expected_counts
    assert all(str(request.url).endswith(':countTokens') for request in c[4])


@pytest.mark.parametrize('phase', ['record_extraction', 'publish_verification', 'status'])
def test_no_fresh_success_after_late_blocking_phase(coordinator, monkeypatch, phase):
    from datetime import timedelta

    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    instance = c[0] if phase == 'status' else c[0].evidence
    original = getattr(instance, phase)
    def slow(*args, **kwargs):
        value = original(*args, **kwargs)
        c[3][5][0] += timedelta(seconds=31)
        return value
    monkeypatch.setattr(instance, phase, slow)
    with pytest.raises(GuestDenied, match='acquisition_deadline_elapsed'):
        acquire(c)
    assert len(c[4]) == 2


def test_simultaneous_duplicate_commands_have_one_executor(coordinator):
    c = coordinator
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        original_factory = c[0].transport_factory
        original = original_factory()
        async def waiting(request):
            if str(request.url).endswith(':countTokens'):
                entered.set()
                await release.wait()
            return await original.handle_async_request(request)
        c[0].transport_factory = lambda: httpx.MockTransport(waiting)
        first = asyncio.create_task(c[0].acquire(c[2], c[1]))
        await asyncio.wait_for(entered.wait(), 5)
        second = await c[0].acquire(c[2], c[1])
        assert second.state == 'INCOMPLETE'
        release.set()
        return await first
    result = asyncio.run(scenario())
    assert result.current and len(c[4]) == 2
    assert len(saved(c[3], 'usage', c[6].capability_hash).runs) == 1


@pytest.mark.parametrize('identity', ['second_affected', 'third_identity'])
def test_product_identity_controls_result_even_with_same_lot(coordinator, identity):
    from tests.unit.test_extraction_proposal import known
    c = coordinator
    name = (c[5][0]['source']['products'][1]['name'] if identity == 'second_affected'
            else 'Meadow Vale Brie')
    c[5][0]['label']['name'] = known(name)
    status = acquire(c)
    assert status.current
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert view.hold_eligible == (identity == 'second_affected')
    assert view.result.verdict == ('MATCHED_HOLD_FOR_REVIEW' if identity == 'second_affected'
                                   else 'REVIEW_REQUIRED')
    # A raw unfamiliar name is not a reviewed identity exclusion. The runtime
    # must not fabricate the identity-review proof required for a scoped negative.


def test_fourth_acquisition_denied_without_resetting_history_or_counts(coordinator):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    for index in range(3):
        status = acquire(c, replace(c[1], request_key=f'run_{index}',
                                    expected_observation_revision=index))
        assert status.current
    with pytest.raises(GuestDenied, match='acquisition_not_admitted'):
        acquire(c, replace(c[1], request_key='fourth', expected_observation_revision=3))
    assert len(c[4]) == 6
    state = saved(c[3], 'usage', c[6].capability_hash)
    assert len(state.runs) == 3 and state.incidents[0].acquisitions == 3
    assert len(c[3][3].read_evidence(c[2], c[1].incident_id).state.extractions) == 3


@pytest.mark.parametrize('mutation', ['review', 'available', 'complete', 'agreement', 'predicate'])
def test_source_support_change_invalidates_status_and_action_without_epoch_change(
    coordinator, mutation
):
    from batchbeacon.guest_service import GuestDenied
    c = coordinator
    status = acquire(c)
    stores, server = c[3][:2]
    env = saved(c[3], 'environment')
    source = env.notices[0]
    if mutation == 'predicate':
        product = source.products[0]
        predicates = tuple(replace(p, values=('DIFFERENT',)) if p.field == 'LOT' else p
                           for p in product.predicates)
        source = replace(source, products=(replace(product, predicates=predicates),
                                          *source.products[1:]))
    else:
        field, value = {'review': ('review', None), 'available': ('source_available', False),
            'complete': ('interpretation_complete', False),
            'agreement': ('source_proposal_agrees', False)}[mutation]
        source = replace(source, **{field: value})
    environment = replace(env, notices=(source,))
    server.seed(stores._encode(stores.name('environment'), 'environment', environment))
    assert c[0].status(c[2], status.run_id).state == 'STALE'
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert not view.current and not view.hold_eligible
    with pytest.raises(GuestDenied, match='current_result_required'):
        c[3][4].prepare(c[2], c[1].incident_id, ActionType.SIMULATED_HOLD)
    assert len(c[4]) == 2


def test_terminal_failure_keeps_reason_after_original_run_deadline(coordinator):
    from datetime import timedelta

    c = coordinator
    c[5][0]["source"]["products"].pop()
    before = acquire(c)
    assert before.state == "FAILED" and before.diagnostics == ("SOURCE_DISAGREEMENT",)
    run = c[0].shared.inspect_run(c[6].capability_hash, before.run_id)
    c[3][5][0] = run.deadline + timedelta(seconds=1)
    assert c[0].status(c[2], before.run_id) == before
    assert len(c[4]) == 2


@pytest.mark.parametrize('failure,diagnostic', [
    ('allowance', 'ALLOWANCE_UNAVAILABLE'), ('provider', 'PROVIDER_UNAVAILABLE')])
def test_failed_run_reason_survives_owned_reopen_without_redispatch(coordinator, monkeypatch,
                                                                  failure, diagnostic):
    from batchbeacon.shared_admission import SharedDenied
    c = coordinator
    if failure == 'allowance':
        def unavailable(*args, **kwargs):
            raise SharedDenied('insufficient uncommitted model allowance')
        monkeypatch.setattr(c[0].shared, 'reserve', unavailable)
    else:
        async def provider(request):
            c[4].append(request)
            if str(request.url).endswith(':countTokens'):
                return httpx.Response(200, json={'totalTokens': 100})
            return httpx.Response(504, json={'error': {'code': 504,
                'status': 'DEADLINE_EXCEEDED', 'message': 'private-provider-marker'}})
        c[0].transport_factory = lambda: httpx.MockTransport(provider)
    status = acquire(c)
    assert status.state == 'FAILED' and status.diagnostics == (diagnostic,)
    assert not status.current and status.result_revision is None
    calls = len(c[4])
    assert calls == (1 if failure == 'allowance' else 2)
    run = c[0].shared.inspect_run(c[6].capability_hash, status.run_id)
    assert run.failure_reason == diagnostic and run.calls == (failure == 'provider')
    for _ in range(2):
        assert c[0].status(c[2], status.run_id) == status
        assert acquire(c) == status
    assert len(c[4]) == calls
    view = c[3][3].read_evidence(c[2], c[1].incident_id)
    assert not view.hold_eligible and not view.state.results
    assert 'private-provider-marker' not in status.model_dump_json()
    c[0].shared.finish_run(c[6].capability_hash, run.id, failed=True,
                          failure_reason='CHECK_FAILED')
    assert c[0].status(c[2], status.run_id) == status


@pytest.mark.parametrize('reason', ['paid ledger unavailable or circuit open',
                                    'operator phase changed'])
def test_local_dispatch_denial_is_not_misreported_as_provider_failure(coordinator,
                                                                    monkeypatch, reason):
    from batchbeacon.shared_admission import SharedDenied
    c = coordinator
    def denied(*args, **kwargs):
        raise SharedDenied(reason)
    monkeypatch.setattr(c[0].shared, 'reserve', denied)
    status = acquire(c)
    assert status.state == 'FAILED' and status.diagnostics == ('CHECK_FAILED',)
    assert len(c[4]) == 1 and c[4][0].url.path.endswith(':countTokens')
    assert reason not in status.model_dump_json()
    assert c[0].status(c[2], status.run_id) == status
    assert c[0].shared.inspect_run(c[6].capability_hash, status.run_id).calls == 0

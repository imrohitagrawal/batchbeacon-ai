"""Private lineage from actual controlled coordinator/learning consumers."""

import asyncio
import json

import pytest
from pydantic import ValidationError

from batchbeacon import acquisition_timing
from batchbeacon import provenance_events as events
from batchbeacon.evidence_service import replace
from batchbeacon.runtime import RuntimeConfig
from tests.unit.test_extraction_service import (  # noqa: F401
    coordinator as coordinator,
)
from tests.unit.test_extraction_service import (
    env as env,
)
from tests.unit.test_extraction_service import (
    no_network_or_credentials as no_network_or_credentials,
)
from tests.unit.test_extraction_service import (
    setup as setup,
)
from tests.unit.test_learning_service import learning as learning  # noqa: F401
from tests.unit.test_runtime import runtime as runtime  # noqa: F401


def binding(**overrides):
    return events.context(events.ProvenancePolicy(**overrides), 'a' * 64, 'synthetic-revision')


def test_actual_success_lineage_and_reconciliation_preserve_calls(coordinator, monkeypatch):
    c = coordinator
    c[0].provenance = binding()
    logged = []
    monkeypatch.setattr(events._logger, 'info', lambda raw: logged.append(json.loads(raw)))

    async def check():
        trace = acquisition_timing.AcquisitionTiming('b' * 64, provenance=c[0].provenance)
        with acquisition_timing.observe(trace):
            result = await c[0].acquire(c[2], c[1])
        trace.finish(result.state)
        return result

    result = asyncio.run(check())
    first = logged[-1]
    assert result.state == 'COMPLETE' and len(c[4]) == 2
    assert first['generation'] == 'RESULT_RETURNED' and first['validation'] == 'VALID'
    assert first['extraction_persistence'] == first['verifier_publication'] == 'ACKNOWLEDGED'
    assert first['verifier_receipt_hash'] and first['verifier_policy_hash'] and first['result_hash']
    assert first['runtime_hash'] == 'a' * 64
    assert first['model_configuration_hash'] == c[0].config.digest() != first['runtime_hash']
    dependency = c[0].sources['first'].notice.dependency
    assert first['sources'][0]['capture_hash'] == dependency.content_hash
    assert first['prompt_hash'] == events.identifier_hash(c[0].config.instruction)
    assert first['guidance_state'] == 'NOT_OBSERVED'
    assert first['source_currentness'] == 'NOT_ASSESSED'
    calls = len(c[3][1].calls)
    asyncio.run(check())
    assert logged[-1]['reconciliation_only']
    assert logged[-1]['generation'] == 'RESULT_NOT_RETURNED'
    assert logged[-1]['verifier_publication'] == 'NOT_ACKNOWLEDGED'
    assert len(c[4]) == 2
    # Status reconciliation performs existing reads; never starts another provider request.
    assert len(c[3][1].calls) > calls
    text = json.dumps(first)
    for private in (c[2], c[1].incident_id, c[1].request_key, c[0].config.instruction):
        assert private not in text


@pytest.mark.parametrize('failure', ['invalid', 'unavailable', 'lost_verifier_ack'])
def test_actual_failure_stages_not_promoted_to_success(coordinator, monkeypatch, failure):
    c = coordinator
    c[0].provenance = binding()
    if failure == 'invalid':
        import copy
        c[5][0] = copy.deepcopy(c[5][0])
        c[5][0]['source']['products'].pop()
    elif failure == 'unavailable':
        c[0].transport_factory = lambda: (_ for _ in ()).throw(OSError('synthetic'))
    else:
        original = c[0].evidence.publish_verification

        def lost(*args, **kwargs):
            original(*args, **kwargs)
            raise OSError('lost_after_commit')

        monkeypatch.setattr(c[0].evidence, 'publish_verification', lost)
    logged = []
    monkeypatch.setattr(events._logger, 'info', lambda raw: logged.append(json.loads(raw)))

    async def check():
        trace = acquisition_timing.AcquisitionTiming('b' * 64, provenance=c[0].provenance)
        try:
            with acquisition_timing.observe(trace):
                result = await c[0].acquire(c[2], c[1])
            outcome = result.state
        except Exception:
            outcome = 'unknown'
        trace.finish(outcome)

    asyncio.run(check())
    record = logged[-1]
    assert record['verifier_publication'] == 'NOT_ACKNOWLEDGED'
    if failure == 'invalid':
        assert record['generation'] == 'RESULT_RETURNED' and record['validation'] == 'INVALID'
    if failure == 'unavailable':
        assert record['generation'] == 'RESULT_NOT_RETURNED' and not c[4]
    assert record['outcome'] != 'COMPLETE'


def test_sink_failure_does_not_change_acquisition(coordinator, monkeypatch):
    c = coordinator
    c[0].provenance = binding()
    monkeypatch.setattr(events._logger, 'info', lambda raw: (_ for _ in ()).throw(OSError()))

    async def check():
        trace = acquisition_timing.AcquisitionTiming('b' * 64, provenance=c[0].provenance)
        with acquisition_timing.observe(trace):
            result = await c[0].acquire(c[2], c[1])
        trace.finish(result.state)
        return result

    assert asyncio.run(check()).state == 'COMPLETE' and len(c[4]) == 2


def test_guidance_actual_post_ack_receipt_and_repeat(learning, monkeypatch):
    c, service = learning
    server = c[3][1]
    before = len(server.calls)
    service.guidance(c[2], c[1].incident_id, 'baseline-guidance')
    baseline_methods = [x[0] for x in server.calls[before:]]
    service.provenance = binding()
    logged = []
    monkeypatch.setattr(events._logger, 'info', lambda raw: logged.append(json.loads(raw)))
    before = len(server.calls)
    request = service.guidance(c[2], c[1].incident_id, 'lineage-guidance')
    assert [x[0] for x in server.calls[before:]] == baseline_methods
    event = logged[-1]
    assert event['event'] == 'guidance_lineage_v1'
    assert event['guidance_policy_hash'] == request.binding.policy.content_hash
    assert event['guidance_activation_revision'] == request.binding.activation_revision
    assert event['guidance_receipt_hash'] == request.digest()
    assert event['sources'] and event['observation_hash'] and event['result_hash']
    assert service.guidance(c[2], c[1].incident_id, 'lineage-guidance') == request
    assert logged[-1]['guidance_receipt_hash'] == event['guidance_receipt_hash']
    original = service._operate

    def lost(*args):
        original(*args)
        raise OSError('lost_ack')

    monkeypatch.setattr(service, '_operate', lost)
    count = len(logged)
    with pytest.raises(OSError):
        service.guidance(c[2], c[1].incident_id, 'lineage-guidance')
    assert len(logged) == count


@pytest.mark.parametrize('field', ['max_sources', 'max_event_bytes'])
@pytest.mark.parametrize('value', [0, -1, True, '1', float('inf')])
def test_policy_invalid(field, value):
    with pytest.raises(ValidationError):
        events.ProvenancePolicy(**{field: value})


def test_limits_and_missing_revision_reach_sink(monkeypatch):
    logged = []
    monkeypatch.setattr(events._logger, 'info', logged.append)
    b = events.context(events.ProvenancePolicy(max_event_bytes=1), 'a' * 64)
    assert events.emit(b, events.initial(b)) is None and not logged
    b = events.context(events.ProvenancePolicy(), 'a' * 64)
    assert events.emit(b, events.initial(b)).deployment_evidence == 'UNKNOWN'
    with pytest.raises(ValidationError):
        events.context(b.policy, b.runtime_hash, 'private/path@example')


def test_context_isolation_refusal_and_disconnect(monkeypatch):
    logged = []
    monkeypatch.setattr(events._logger, 'info', lambda raw: logged.append(json.loads(raw)))

    async def operation(digest, outcome):
        b = events.context(events.ProvenancePolicy(), digest * 64)
        trace = acquisition_timing.AcquisitionTiming('b' * 64, provenance=b)
        with acquisition_timing.observe(trace):
            acquisition_timing.lineage(b, request_hash=digest * 64)
            await asyncio.sleep(0)
        trace.finish(outcome)
        assert trace.finish('COMPLETE') is None

    async def run():
        await asyncio.gather(operation('a', 'refused'), operation('c', 'disconnected'))

    asyncio.run(run())
    assert {(x['runtime_hash'], x['request_hash'], x['outcome']) for x in logged} == {
        ('a' * 64, 'a' * 64, 'refused'), ('c' * 64, 'c' * 64, 'disconnected')}
    assert acquisition_timing._current.get() is None


def test_inherited_runtime_digests_unchanged_without_policy(runtime):
    # Existing checked-in local fixture has the same absent optional field behavior.
    config, _, _ = runtime
    assert 'provenance' not in config.model_dump()
    raw = json.loads(config.model_dump_json())
    assert RuntimeConfig.model_validate_json(json.dumps(raw)).digest() == config.digest()
    assert replace(config, provenance=events.ProvenancePolicy()).digest() != config.digest()


def test_invalid_revision_refused_before_credentials(runtime, monkeypatch):
    from pathlib import Path

    import google.auth

    from batchbeacon.runtime import build_app
    config, _, _ = runtime
    config = replace(config, provenance=events.ProvenancePolicy())
    monkeypatch.setenv('DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA', 'true')
    monkeypatch.delenv('FIRESTORE_EMULATOR_HOST', raising=False)
    monkeypatch.delenv('STORAGE_EMULATOR_HOST', raising=False)
    monkeypatch.setattr(google.auth, 'default', lambda **kw: pytest.fail('ADC must not run'))
    with pytest.raises(ValidationError):
        build_app(config, Path('.'), deployment_revision='private/not-a-revision')


def test_source_cap_and_fact_validation_fail_closed(coordinator, monkeypatch):
    logged = []
    monkeypatch.setattr(events._logger, 'info', logged.append)
    dep = coordinator[0].sources['first'].notice.dependency
    b = binding(max_sources=1)
    record = events.Lineage.model_validate(events.initial(b).model_dump() | {
        'sources': events.sources((dep, replace(dep, version='other-version')))})
    assert events.emit(b, record) is None and not logged
    for changes in ({'validation': 'VALID'}, {'verifier_publication': 'ACKNOWLEDGED'},
                    {'guidance_state': 'ACKNOWLEDGED'}, {'deployment_evidence': 'UNKNOWN'}):
        with pytest.raises(ValidationError):
            events.Lineage.model_validate(events.initial(b).model_dump() | changes)

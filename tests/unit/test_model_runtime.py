"""Actual installed ADK through offline HTTP and shared durable admission fakes."""

import asyncio
import json
from importlib.metadata import version

import httpx
import pytest

from batchbeacon.evidence_service import replace
from batchbeacon.extraction_input import prepare_input
from batchbeacon.extraction_records import RunBinding
from batchbeacon.model_runtime import ExtractionConfig, execute_model
from batchbeacon.shared_admission import SharedAdmission
from batchbeacon.uploads import sanitize_images
from tests.unit.durable_fixtures import wire_response
from tests.unit.test_extraction_adk_compatibility import no_external_io as no_external_io  # noqa
from tests.unit.test_extraction_input import inputs
from tests.unit.test_guest_boundary import picture
from tests.unit.test_probe_runner import credentials
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def runtime(env, request):
    old, store, guests, token, key, iid, clock, openings = env
    config = ExtractionConfig(mode='offline_test', project_id='synthetic-project',
        model_id='gemini-3.8-flash', model_location='global', api_version='v1beta1',
        adk_version=version('google-adk'), genai_version=version('google-genai'),
        **getattr(request, 'param', {}))
    policy = replace(old.policy, model_configuration_hash=config.digest(),
                     run_seconds=config.run_seconds)
    grant = replace(old.grant, policy_hash=policy.digest())
    phase = store.state().phase
    store.budget = None
    shared = SharedAdmission(policy, grant, store, clock=lambda: clock[0])
    shared.initialize(openings)
    shared.activate_phase(phase)
    batch = guests.retain(token, iid, 'upload',
                          sanitize_images((picture(),), guests.policy.uploads))
    proposal, args = inputs()
    args.update(captures=tuple((c, guests.image(token, iid, c.id)) for c in batch.captures),
                instruction=config.instruction, prompt_version=config.prompt_version,
                policy=config.preparation)
    prepared = prepare_input(**args)
    binding = RunBinding(manifest=prepared.manifest, expected_observation_revision=0,
        application_configuration_hash=config.digest(), logical_operation='extract')
    run = shared.admit_run(key, iid, 'run', binding).run
    return config, shared, key, run, prepared, proposal, clock, store


def response(proposal):
    return wire_response(candidates=[{'content': {'role': 'model',
        'parts': [{'text': json.dumps(proposal)}]}, 'finishReason': 'STOP', 'index': 0}])


def exercise(runtime, *, handler=None):
    config, shared, key, run, prepared, proposal, _, _ = runtime
    calls = []
    async def fake(request):
        calls.append(request)
        if handler:
            return await handler(request)
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        return httpx.Response(200, content=response(proposal))
    result = asyncio.run(execute_model(config, shared, key, run, prepared,
        transport=httpx.MockTransport(fake), credentials=credentials()))
    return result, calls


def test_actual_adk_exact_count_generation_and_durable_response(runtime):
    result, calls = exercise(runtime)
    assert len(calls) == 2
    assert str(calls[0].url).endswith(':countTokens')
    counted, generated = [json.loads(r.content) for r in calls]
    assert counted == {k: v for k, v in generated.items() if k != 'labels'}
    config, shared, key, run, prepared, proposal, _, store = runtime
    assert result.candidate == json.dumps(proposal).encode()
    attempt = shared.inspect_attempt(key, run.id, result.attempt_id)
    assert attempt.response.original() == response(proposal)
    assert attempt.usage_hash and attempt.dispatch_claimed and attempt.actual_nanos
    assert prepared.manifest.schema_hash == config.schema_hash
    assert len(store.attempts) == 1


def reject(runtime, *, count=None, raw=None, status=200, handler=None, match=None):
    from batchbeacon.model_runtime import ModelFailure
    calls = []
    async def fake(request):
        calls.append(request)
        if handler:
            return await handler(request)
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100} if count is None else count)
        return httpx.Response(status, content=raw if raw is not None else response(runtime[5]))
    with pytest.raises(ModelFailure, match=match) as caught:
        exercise(runtime, handler=fake)
    assert caught.value.__context__ is None
    return calls


@pytest.mark.parametrize('total', [0, -1, True, 12001, 1.5, '100', None])
def test_invalid_or_excessive_count_never_reserves_or_generates(runtime, total):
    calls = reject(runtime, count={'totalTokens': total})
    assert len(calls) == 1 and not runtime[7].attempts


def test_cached_count_rejected(runtime):
    assert len(reject(runtime, count={'totalTokens': 100, 'cachedContentTokenCount': 1})) == 1
    assert not runtime[7].attempts


@pytest.mark.parametrize('status', [400, 429, 500, 503])
def test_provider_error_persists_original_and_never_retries(runtime, status):
    raw = b'{"error":{"message":"private-provider-canary"}}'
    calls = reject(runtime, status=status, raw=raw, match='provider_status_rejected')
    assert len(calls) == 2
    from batchbeacon.shared_admission import Attempt
    attempt = Attempt.model_validate_json(next(iter(runtime[7].attempts.values())))
    assert attempt.response.original() == raw and attempt.response.status_code == status
    assert attempt.response.complete and attempt.usage_hash is None
    assert runtime[7].state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


@pytest.mark.parametrize('raw', [b'{', b'{"x":1,"x":2}', b'{"x":NaN}',
                                b'{"candidates":"private-shape-canary"}', b'\xff'])
def test_malformed_body_is_durable_and_sanitized_before_sdk(runtime, raw):
    calls = reject(runtime, raw=raw)
    assert len(calls) == 2
    from batchbeacon.shared_admission import Attempt
    attempt = Attempt.model_validate_json(next(iter(runtime[7].attempts.values())))
    assert attempt.response.original() == raw and attempt.usage_hash is None


@pytest.mark.parametrize('change', ['continuation', 'max_tokens', 'multiple', 'no_parts',
                                     'function_call', 'empty', 'thought'])
def test_no_incomplete_or_nontext_candidate_is_publishable(runtime, change):
    body = json.loads(response(runtime[5]))
    candidate = body['candidates'][0]
    if change == 'continuation':
        candidate['continuationToken'] = 'private-continuation'
    elif change == 'max_tokens':
        candidate['finishReason'] = 'MAX_TOKENS'
    elif change == 'multiple':
        body['candidates'].append(candidate.copy())
    elif change == 'no_parts':
        candidate['content']['parts'] = []
    elif change == 'function_call':
        candidate['content']['parts'] = [{'functionCall': {'name': 'unreviewed', 'args': {}}}]
    elif change == 'empty':
        body['candidates'] = []
    else:
        candidate['content']['parts'][0]['thought'] = True
    calls = reject(runtime, raw=json.dumps(body).encode())
    assert len(calls) == 2
    from batchbeacon.shared_admission import Attempt
    attempt = Attempt.model_validate_json(next(iter(runtime[7].attempts.values())))
    assert attempt.usage_hash and attempt.actual_nanos  # Usage is independent of valid output.


@pytest.mark.parametrize('phase', ['count', 'reserve', 'claim', 'response'])
def test_absolute_deadline_rechecked_after_each_blocking_phase(runtime, phase, monkeypatch):
    config, shared, key, run, prepared, proposal, clock, store = runtime
    if phase in ('reserve', 'claim'):
        method = 'reserve' if phase == 'reserve' else 'claim_dispatch'
        original = getattr(shared, method)
        def slow(*args, **kwargs):
            result = original(*args, **kwargs)
            clock[0] = run.deadline
            return result
        monkeypatch.setattr(shared, method, slow)
    async def fake(request):
        is_count = str(request.url).endswith(':countTokens')
        if (phase == 'count' and is_count) or (phase == 'response' and not is_count):
            clock[0] = run.deadline
        return httpx.Response(200, json={'totalTokens': 100}) if is_count else httpx.Response(
            200, content=response(proposal))
    calls = reject(runtime, handler=fake)
    assert len(calls) == (2 if phase == 'response' else 1)
    if phase == 'response':
        from batchbeacon.shared_admission import Attempt
        attempt = Attempt.model_validate_json(next(iter(store.attempts.values())))
        assert attempt.response.complete and attempt.usage_hash


@pytest.mark.parametrize('method', ['reserve', 'claim_dispatch'])
def test_lost_ack_never_dispatches_or_replaces_attempt(runtime, method, monkeypatch):
    shared, store = runtime[1], runtime[7]
    original = getattr(shared, method)
    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError('private-lost-ack-canary')
    monkeypatch.setattr(shared, method, lost)
    assert len(reject(runtime)) == 1
    assert len(store.attempts) == 1
    from batchbeacon.shared_admission import Attempt
    attempt = Attempt.model_validate_json(next(iter(store.attempts.values())))
    assert attempt.dispatch_claimed == (method == 'claim_dispatch')
    assert store.state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


def test_reexecuting_run_cannot_make_second_generation(runtime):
    exercise(runtime)
    assert len(reject(runtime)) == 1  # Defensive count may occur; claim cannot be reused.
    assert len(runtime[7].attempts) == 1


@pytest.mark.parametrize('field,value', [('max_input_tokens', 90),
    ('instruction', 'Changed prompt'), ('max_count_response_bytes', 1024),
    ('max_request_bytes', 1024), ('request_timeout_seconds', 10.0)])
def test_configuration_change_denied_without_matching_shared_admission(runtime, field, value):
    changed = (replace(runtime[0], **{field: value}), *runtime[1:])
    assert reject(changed, match='configuration_mismatch') == []


def test_invalid_configuration_rejected_and_schema_bound(runtime):
    from pydantic import ValidationError
    for changes in ({'request_timeout_seconds': 31}, {'run_seconds': True},
                    {'max_count_response_bytes': 0}, {'schema_hash': 'b'*64},
                    {'request_timeout_seconds': float('nan')}):
        with pytest.raises(ValidationError):
            replace(runtime[0], **changes)


def test_debug_logs_do_not_include_model_content_and_restore_other_context(runtime, caplog):
    import logging
    caplog.set_level(logging.DEBUG)
    exercise(runtime)
    text = caplog.text
    assert runtime[4].source_bytes.decode() not in text
    assert runtime[0].instruction not in text and json.dumps(runtime[5]) not in text
    logger = logging.getLogger('google_adk.google.adk.models.google_llm')
    logger.warning('unrelated-sdk-message')
    logging.getLogger('batchbeacon.test').warning('application-message')
    assert 'unrelated-sdk-message' in caplog.text and 'application-message' in caplog.text


def test_unsafe_environment_telemetry_override_denied_before_client(runtime, monkeypatch):
    monkeypatch.setenv('ADK_TELEMETRY_IGNORE_RUN_CONFIG', 'true')
    monkeypatch.setenv('ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS', 'true')
    assert reject(runtime, match='content_telemetry_forbidden') == []


@pytest.mark.parametrize('mutation', ['source', 'image', 'system', 'schema', 'settings',
                                     'endpoint', 'method', 'extra'])
def test_changed_final_wire_denied_before_count_or_generation(runtime, monkeypatch, mutation):
    original_send = httpx.AsyncClient.send
    async def mutate(client, request, **kwargs):
        body = json.loads(request.content)
        if mutation == 'source':
            body['contents'][0]['parts'][0]['text'] += 'changed'
        elif mutation == 'image':
            body['contents'][0]['parts'][1]['inlineData']['data'] = 'YQ=='
        elif mutation == 'system':
            body['systemInstruction']['parts'][0]['text'] += 'changed'
        elif mutation == 'schema':
            body['generationConfig']['responseJsonSchema'] = {}
        elif mutation == 'settings':
            body['generationConfig']['maxOutputTokens'] += 1
        elif mutation == 'extra':
            body['cachedContent'] = 'unreviewed'
        changed = httpx.Request('GET' if mutation == 'method' else request.method,
            str(request.url) + '/changed' if mutation == 'endpoint' else request.url,
            headers=request.headers, extensions=request.extensions, json=body)
        return await original_send(client, changed, **kwargs)
    monkeypatch.setattr(httpx.AsyncClient, 'send', mutate)
    assert reject(runtime) == []
    assert not runtime[7].attempts


class Stream(httpx.AsyncByteStream):
    def __init__(self, chunks, error=None, signal=None):
        self.chunks, self.error, self.signal, self.closed = chunks, error, signal, False

    async def __aiter__(self):
        for chunk in self.chunks:
            yield chunk
        if self.signal:
            self.signal.set()
            await asyncio.Event().wait()
        if self.error:
            raise self.error

    async def aclose(self):
        self.closed = True


@pytest.mark.parametrize('failure', ['oversized', 'read_error'])
def test_bounded_incomplete_original_prefix_retains_liability(runtime, failure):
    from batchbeacon.shared_admission import Attempt
    limit = runtime[0].evidence_limits.max_response_bytes
    chunks = [b'{"private-prefix":']
    if failure == 'oversized':
        chunks.append(b'x' * limit)
    stream = Stream(chunks,
                    OSError('private-transport-canary') if failure == 'read_error' else None)
    async def fake(request):
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        return httpx.Response(200, stream=stream)
    assert len(reject(runtime, handler=fake)) == 2
    attempt = Attempt.model_validate_json(next(iter(runtime[7].attempts.values())))
    assert attempt.response.original() == b''.join(chunks)[:limit]
    assert not attempt.response.complete and attempt.usage_hash is None and stream.closed
    assert runtime[7].state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


def test_cancellation_retains_prefix_and_closes_owned_clients(runtime):
    from batchbeacon.shared_admission import Attempt
    config, shared, key, run, prepared, _, _, store = runtime
    async def scenario():
        started = asyncio.Event()
        stream = Stream([b'private-prefix'], signal=started)
        async def fake(request):
            if str(request.url).endswith(':countTokens'):
                return httpx.Response(200, json={'totalTokens': 100})
            return httpx.Response(200, stream=stream)
        transport = httpx.MockTransport(fake)
        task = asyncio.create_task(execute_model(config, shared, key, run, prepared,
                                   transport=transport, credentials=credentials()))
        await asyncio.wait_for(started.wait(), 5)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert stream.closed
    asyncio.run(scenario())
    attempt = Attempt.model_validate_json(next(iter(store.attempts.values())))
    assert attempt.response.original() == b'private-prefix'
    assert not attempt.response.complete and attempt.usage_hash is None
    assert store.state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


def test_constructor_failure_closes_preconstructed_http_clients(runtime, monkeypatch):
    from batchbeacon import model_runtime
    clients = []
    def fail(**kwargs):
        options = kwargs['http_options']
        clients.extend([options.httpx_client, options.httpx_async_client])
        raise RuntimeError('private-constructor-canary')
    monkeypatch.setattr(model_runtime.genai, 'Client', fail)
    assert reject(runtime) == []
    assert len(clients) == 2 and all(c.is_closed for c in clients)


def test_slow_constructor_cannot_count_or_dispatch(runtime, monkeypatch):
    from batchbeacon import model_runtime
    original = model_runtime.genai.Client
    clients = []
    def slow(**kwargs):
        client = original(**kwargs)
        clients.extend([kwargs['http_options'].httpx_client,
                        kwargs['http_options'].httpx_async_client])
        runtime[6][0] = runtime[3].deadline
        return client
    monkeypatch.setattr(model_runtime.genai, 'Client', slow)
    assert reject(runtime) == []
    assert all(c.is_closed for c in clients)


def test_response_persistence_failure_prevents_output_and_refund(runtime, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError('private-storage-canary')
    monkeypatch.setattr(runtime[1], 'record_response', fail)
    assert len(reject(runtime)) == 2
    from batchbeacon.shared_admission import Attempt
    attempt = Attempt.model_validate_json(next(iter(runtime[7].attempts.values())))
    assert attempt.response is None and attempt.usage_hash is None
    assert runtime[7].state().balance(attempt.pool).reserved_nanos == attempt.reserved_nanos


def test_oversized_usage_opens_circuit_without_output(runtime):
    raw = wire_response(input_tokens=12001,
                        candidates=json.loads(response(runtime[5]))['candidates'])
    assert len(reject(runtime, raw=raw)) == 2
    assert runtime[7].state().circuit == 'open_bound'


@pytest.mark.parametrize('runtime', [{'max_output_tokens': 128, 'request_timeout_seconds': 4.0,
    'thinking_level': 'MEDIUM', 'instruction': 'Explicit synthetic override instruction.'}],
    indirect=True)
def test_valid_overrides_reach_final_wire_and_receipt(runtime):
    result, calls = exercise(runtime)
    body = json.loads(calls[1].content)
    assert body['generationConfig']['maxOutputTokens'] == 128
    assert body['generationConfig']['thinkingConfig'] == {'thinking_level': 'MEDIUM'}
    assert runtime[0].instruction in body['systemInstruction']['parts'][0]['text']
    assert 0 < calls[1].extensions['timeout']['read'] <= 4.0
    attempt = runtime[1].inspect_attempt(runtime[2], runtime[3].id, result.attempt_id)
    assert attempt.model_configuration_hash == runtime[0].digest()


@pytest.mark.parametrize('runtime', [{'max_count_response_bytes': 16}], indirect=True)
def test_count_response_limit_effective_before_reservation(runtime):
    assert len(reject(runtime)) == 1
    assert not runtime[7].attempts


@pytest.mark.parametrize('runtime', [{'max_input_tokens': 99}], indirect=True)
def test_configured_input_token_limit_effective(runtime):
    assert len(reject(runtime)) == 1
    assert not runtime[7].attempts


def test_transport_stream_is_sealed_from_the_exact_counted_bytes(runtime, monkeypatch):
    original_send = httpx.AsyncClient.send
    async def mutate(client, request, **kwargs):
        body = json.loads(request.content)
        body['contents'][0]['parts'][0]['text'] = 'unapproved stream replacement'
        wrong = json.dumps(body).encode()
        request.stream = httpx.ByteStream(wrong)
        request.headers['content-length'] = str(len(wrong))
        return await original_send(client, request, **kwargs)
    monkeypatch.setattr(httpx.AsyncClient, 'send', mutate)
    calls = []
    class ConsumingTransport(httpx.MockTransport):
        async def handle_async_request(self, request):
            actual = b''.join([chunk async for chunk in request.stream])
            assert len(actual) == int(request.headers['content-length'])
            calls.append(json.loads(actual))
            if str(request.url).endswith(':countTokens'):
                return httpx.Response(200, json={'totalTokens': 100})
            return httpx.Response(200, content=response(runtime[5]))
    result = asyncio.run(execute_model(*runtime[:5],
        transport=ConsumingTransport(lambda _: None), credentials=credentials()))
    assert result.candidate
    assert calls[0]['contents'] == calls[1]['contents']
    assert calls[1]['contents'][0]['parts'][0]['text'].encode() == runtime[4].source_bytes


def test_lazy_http_transport_logs_redacted_in_fresh_process():
    import os
    import subprocess
    import sys
    from pathlib import Path
    code = '''
import asyncio, logging, io, socket
import google.auth
import httpx
from batchbeacon.model_runtime import private_model_operation

def forbidden(*a, **k): raise AssertionError('no external IO')
socket.socket.connect = forbidden
google.auth.default = forbidden
sink = io.StringIO()
handler = logging.StreamHandler(sink)
logging.getLogger().addHandler(handler)
logging.getLogger().setLevel(logging.DEBUG)
assert 'httpcore.http11' not in logging.Logger.manager.loggerDict
async def check():
    with private_model_operation():
        transport = httpx.AsyncHTTPTransport(retries=0)
        from httpcore._trace import Trace
        with Trace('receive_response_headers', logging.getLogger('httpcore.http11'),
                   None, kwargs={'headers': [('x-private', 'lazy-header-canary')]}):
            pass
        await transport.aclose()
asyncio.run(check())
assert 'lazy-header-canary' not in sink.getvalue()
logging.getLogger('httpcore.http11').warning('outside-context-message')
assert 'outside-context-message' in sink.getvalue()
'''
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[2] / 'src')))
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('operation', ['generateContent', 'countTokens'])
@pytest.mark.parametrize('field', ['schema_boolean', 'setting_integer'])
def test_final_semantic_equality_is_json_type_sensitive(runtime, monkeypatch, operation, field):
    original_send = httpx.AsyncClient.send
    async def mutate(client, request, **kwargs):
        if str(request.url).endswith(':' + operation):
            body = json.loads(request.content)
            if field == 'schema_boolean':
                body['generationConfig']['responseJsonSchema']['additionalProperties'] = 0
            else:
                body['generationConfig']['maxOutputTokens'] = float(
                    body['generationConfig']['maxOutputTokens'])
            request = httpx.Request(request.method, request.url, headers=request.headers,
                                    extensions=request.extensions, json=body)
        return await original_send(client, request, **kwargs)
    monkeypatch.setattr(httpx.AsyncClient, 'send', mutate)
    assert reject(runtime) == []
    assert not runtime[7].attempts


@pytest.mark.parametrize('deadline', [float('nan'), float('inf'), True, '1'])
def test_invalid_carried_monotonic_deadline_denied_before_io(runtime, deadline):
    from batchbeacon.model_runtime import ModelFailure
    calls = []
    with pytest.raises(ModelFailure, match='invalid_execution_deadline'):
        asyncio.run(execute_model(*runtime[:5],
            transport=httpx.MockTransport(lambda r: calls.append(r)), credentials=credentials(),
            monotonic_deadline=deadline))
    assert not calls and not runtime[7].attempts

"""Injected HTTP journey using installed ADK and generated Firestore SDK/fake RPC."""

import asyncio
from contextlib import suppress
from threading import Event

import httpx
import pytest
from fastapi.testclient import TestClient

from batchbeacon.extraction_api import ExtractionHTTPPolicy, create_extraction_test_app
from batchbeacon.guest_service import GuestDenied, csrf_for
from tests.unit.test_extraction_service import coordinator as coordinator  # noqa
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def api(coordinator):
    c = coordinator
    policy = ExtractionHTTPPolicy()
    app = create_extraction_test_app(c[0], c[3][4], policy)
    headers = {'Origin': c[3][2].policy.origin, 'X-CSRF-Token': csrf_for(c[2]),
               'Idempotency-Key': c[1].request_key}
    body = c[1].model_dump(mode='json', exclude={'incident_id', 'request_key'})
    path = f'/api/incidents/{c[1].incident_id}/acquisitions'
    with TestClient(app) as client:
        client.cookies.set(c[3][2].policy.cookie_name, c[2])
        yield client, headers, body, path, c, app


def start(api, **updates):
    client, headers, body, path = api[:4]
    return client.post(path, headers=headers, json=body | updates)


def test_http_extraction_evidence_explicit_action_and_recovery(api):
    client, headers, _, path, c, _ = api
    response = start(api)
    assert response.status_code == 200, response.text
    status = response.json()
    assert status['state'] == 'COMPLETE' and status['current']
    assert start(api).json() == status and len(c[4]) == 2
    assert client.get(path + '/' + status['run_id']).json() == status
    recovered = client.get(path + '/reconcile', headers={'Idempotency-Key': c[1].request_key})
    assert recovered.json() == status
    incident = path.removesuffix('/acquisitions')
    evidence = client.get(incident + '/evidence').json()
    assert evidence['hold_eligible'] and evidence['current']
    prepared = client.get(incident + '/actions/prepare',
                          params={'action_type': 'SIMULATED_HOLD'}).json()
    action = client.post(incident + '/actions', headers=headers | {'Idempotency-Key': 'hold'},
        json={'target': prepared['target'], 'explicit_confirmation': True})
    assert action.status_code == 200
    assert len(client.get(incident + '/actions').json()['actions']) == 1
    assert client.get(path + '/' + status['run_id']).json()['current']
    assert len(c[4]) == 2
    assert response.headers['cache-control'] == 'no-store, private'
    assert response.headers['referrer-policy'] == 'no-referrer'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert 'access-control-allow-origin' not in response.headers
    assert set(status) == {'run_id', 'incident_id', 'state', 'current', 'reconciliation_required',
                           'extraction_revision',
                          'observation_revision', 'result_revision', 'diagnostics'}


@pytest.mark.parametrize('field', [
    'incident_id', 'request_key', 'session_id', 'shop_id', 'reviewed',
    'configuration_hash', 'source_bytes', 'expected_verdict', 'provenance', 'resolved_name'])
def test_extra_authority_fields_rejected_before_model(api, field):
    assert start(api, **{field: 'untrusted'}).status_code == 422
    assert not api[4][4]


@pytest.mark.parametrize('change', [
    'missing_origin', 'foreign_origin', 'missing_csrf', 'wrong_csrf',
                                   'missing_key', 'invalid_key'])
def test_mutation_guards_precede_dispatch_including_replay(api, change):
    client, headers, body, path, c, _ = api
    assert start(api).status_code == 200
    modified = dict(headers)
    if change == 'missing_origin':
        modified.pop('Origin')
    elif change == 'foreign_origin':
        modified['Origin'] = 'https://untrusted.invalid'
    elif change == 'missing_csrf':
        modified.pop('X-CSRF-Token')
    elif change == 'wrong_csrf':
        modified['X-CSRF-Token'] = 'f' * 64
    elif change == 'missing_key':
        modified.pop('Idempotency-Key')
    else:
        modified['Idempotency-Key'] = 'bad/key'
    assert client.post(path, headers=modified, json=body).status_code in (403, 422)
    assert len(c[4]) == 2


@pytest.mark.parametrize('condition', ['missing_cookie', 'foreign_cookie', 'expired'])
def test_ownership_denies_mutation_status_and_key_lookup(api, condition):
    client, headers, body, path, c, _ = api
    status = start(api).json()
    if condition == 'missing_cookie':
        client.cookies.clear()
        client.headers['Authorization'] = 'Bearer ' + c[2]
    elif condition == 'foreign_cookie':
        foreign, _ = c[3][2].issue()
        client.cookies.set(c[3][2].policy.cookie_name, foreign)
        headers = headers | {'X-CSRF-Token': csrf_for(foreign)}
    else:
        c[3][5][0] = c[6].scope.expires_at
    responses = [client.post(path, headers=headers, json=body),
        client.get(path + '/' + status['run_id']),
        client.get(path + '/reconcile', headers={'Idempotency-Key': c[1].request_key})]
    assert all(r.status_code in (401, 404) for r in responses)
    assert len(c[4]) == 2
    assert all('run_id' not in r.json() for r in responses)


def test_owned_but_different_incident_cannot_return_run_status(api):
    client, headers, _, _, _, _ = api
    status = start(api).json()
    other = client.post('/api/incidents', headers=headers | {'Idempotency-Key': 'second'}).json()
    path = '/api/incidents/' + other['incident_id'] + '/acquisitions/' + status['run_id']
    response = client.get(path)
    assert response.status_code == 404 and 'run_id' not in response.json()


@pytest.mark.parametrize('raw', [b'{"source_selection":"first","source_selection":"first"}',
    b'[]', b'{"capture_ids":NaN}', b'{', b'"private-body-marker"'])
def test_ambiguous_or_malformed_json_has_constant_errors(api, raw):
    response = api[0].post(api[3], headers=api[1] | {'Content-Type': 'application/json'},
                           content=raw)
    assert response.status_code == 422
    assert 'private-body-marker' not in response.text and not api[4][4]


@pytest.mark.parametrize('kind', [
    'post_query', 'get_query', 'get_body', 'key_duplicate', 'key_missing'])
def test_unexpected_query_or_body_rejected(api, kind):
    client, headers, body, path, c, _ = api
    status = start(api).json()
    if kind == 'post_query':
        response = client.post(path + '?actor=manager', headers=headers, json=body)
    elif kind == 'get_query':
        response = client.get(path + '/' + status['run_id'] + '?reviewed=true')
    elif kind == 'get_body':
        response = client.request('GET', path + '/' + status['run_id'], content=b'body')
    elif kind == 'key_duplicate':
        response = client.get(path + '/reconcile?request_key=a&request_key=b')
    else:
        response = client.get(path + '/reconcile')
    assert response.status_code == 422 and len(c[4]) == 2


def test_unknown_completion_ack_reconciles_original_key_without_dispatch(api, monkeypatch):
    c = api[4]
    original = c[0].evidence.complete_acquisition
    def lost(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError('private-completion-marker')
    monkeypatch.setattr(c[0].evidence, 'complete_acquisition', lost)
    response = start(api)
    assert response.status_code == 503
    assert response.json()['outcome'] == 'unknown'
    assert response.json()['recovery'] == 'original_request_key'
    assert 'private-completion-marker' not in response.text
    status = api[0].get(api[3] + '/reconcile',
                       headers={'Idempotency-Key': c[1].request_key}).json()
    assert status['current'] and start(api).json() == status and len(c[4]) == 2


def test_status_never_constructs_model_and_error_payload_stays_private(api, monkeypatch):
    c = api[4]
    status = start(api).json()
    def forbidden(*args, **kwargs):
        raise OSError('private-transport-marker')
    c[0].transport_factory = forbidden
    assert api[0].get(api[3] + '/' + status['run_id']).json() == status
    monkeypatch.setattr(c[0].shared.store, 'transact', forbidden)
    response = api[0].get(api[3] + '/' + status['run_id'])
    assert response.status_code == 503 and 'private-transport-marker' not in response.text


def test_worker_preserves_event_loop_capacity_and_slot_through_cancellation(api):
    c, app = api[4:]
    entered, release, done = Event(), Event(), Event()
    original_acquire = c[0].acquire
    async def tracked(*args, **kwargs):
        try:
            return await original_acquire(*args, **kwargs)
        finally:
            done.set()
    c[0].acquire = tracked
    original = c[0].transport_factory()
    async def blocked(request):
        if str(request.url).endswith(':countTokens'):
            entered.set()
            assert release.wait(10), 'test must release owned worker'
        return await original.handle_async_request(request)
    c[0].transport_factory = lambda: httpx.MockTransport(blocked)
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=c[3][2].policy.origin,
            cookies={c[3][2].policy.cookie_name: c[2]}) as client:
            first = asyncio.create_task(client.post(api[3], headers=api[1], json=api[2]))
            try:
                assert await asyncio.to_thread(entered.wait, 5)
                assert (await asyncio.wait_for(client.get('/healthz'), 5)).status_code == 200
                first.cancel()
                await asyncio.sleep(0)
                second = await client.post(api[3], headers=api[1] | {'Idempotency-Key': 'second'},
                                           json=api[2])
                assert second.status_code == 429
                release.set()
                with suppress(asyncio.CancelledError):
                    await first
            finally:
                release.set()
                with suppress(asyncio.CancelledError):
                    await first
                assert await asyncio.to_thread(done.wait, 5)
            recovered = await client.get(api[3] + '/reconcile',
                headers={'Idempotency-Key': c[1].request_key})
            assert recovered.json()['current']
    asyncio.run(scenario())


@pytest.mark.parametrize('value', [0, -1, True, 1.5, '2'])
def test_invalid_execution_capacity_rejected(value):
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ExtractionHTTPPolicy(max_concurrent_acquisitions=value)


def test_configured_body_limit_consumed_and_no_default_route(api):
    from batchbeacon.app import app
    policy = ExtractionHTTPPolicy(max_json_bytes=8, max_concurrent_acquisitions=2)
    c = api[4]
    local = create_extraction_test_app(c[0], c[3][4], policy)
    assert local.state.extraction_http_policy_hash == policy.digest()
    with TestClient(local) as client:
        client.cookies.set(c[3][2].policy.cookie_name, c[2])
        assert client.post(api[3], headers=api[1], json=api[2]).status_code == 413
    assert not c[4]
    assert not any('acquisitions' in route.path for route in app.routes)


def test_missing_graph_is_not_a_runtime_fallback(api):
    with pytest.raises(ValueError):
        create_extraction_test_app(None, api[4][3][4], ExtractionHTTPPolicy())
    with pytest.raises(ValueError):
        create_extraction_test_app(api[4][0], None, ExtractionHTTPPolicy())


def test_expiry_during_command_read_denies_before_model(api, monkeypatch):
    from batchbeacon import extraction_api
    original = extraction_api._command
    async def expires(*args, **kwargs):
        body = await original(*args, **kwargs)
        api[4][3][5][0] = api[4][6].scope.expires_at
        return body
    monkeypatch.setattr(extraction_api, '_command', expires)
    response = start(api)
    assert response.status_code in (401, 409) and not api[4][4]


def test_ownership_storage_error_sanitized(api, monkeypatch):
    def fail(*args, **kwargs):
        raise GuestDenied(503, 'guest_storage_unavailable')
    monkeypatch.setattr(api[4][3][2], 'resolve', fail)
    assert start(api).json() == {'error': 'guest_storage_unavailable', 'outcome': 'unknown',
                                'recovery': 'original_request_key'}


@pytest.mark.parametrize('field,value', [
    ('expected_observation_revision', True), ('expected_observation_revision', 0.0),
    ('expected_observation_revision', '0'), ('expected_observation_revision', -1),
    ('source_selection', 'https://untrusted.invalid'), ('capture_ids', []),
    ('capture_ids', ['a' * 32] * 3)])
def test_strict_start_types_prevent_dispatch(api, field, value):
    assert start(api, **{field: value}).status_code == 422 and not api[4][4]


@pytest.mark.parametrize('header', ['Idempotency-Key', 'Origin', 'X-CSRF-Token', 'Cookie'])
def test_duplicate_authority_headers_rejected(api, header):
    c = api[4]
    headers = list(api[1].items())
    if header == 'Cookie':
        value = c[3][2].policy.cookie_name + '=' + c[2]
        headers.extend([('Cookie', value), ('Cookie', value)])
    else:
        headers.append((header, api[1][header]))
    response = api[0].post(api[3], headers=headers, json=api[2])
    assert response.status_code in (401, 403, 422) and not c[4]


def test_duplicate_capability_in_one_cookie_header_rejected(api):
    c = api[4]
    value = c[3][2].policy.cookie_name + '=' + c[2]
    response = api[0].post(api[3], headers=api[1] | {'Cookie': value + '; ' + value}, json=api[2])
    assert response.status_code == 401 and not c[4]


@pytest.mark.parametrize('header,value', [('Content-Type', 'text/plain'),
    ('Content-Type', 'application/json; charset=utf-16'), ('Content-Encoding', 'gzip')])
def test_unsupported_wire_encoding_rejected(api, header, value):
    response = api[0].post(api[3], headers=api[1] | {header: value}, json=api[2])
    assert response.status_code == 415 and not api[4][4]


def test_worker_capacity_override_reaches_consumer(api, monkeypatch):
    from batchbeacon.extraction_service import AcquisitionStatus
    c = api[4]
    release = Event()
    entered = [Event(), Event()]
    def fake_result(command):
        return AcquisitionStatus(run_id='a' * 32, incident_id=command.incident_id,
                                 state='INCOMPLETE', current=False)
    async def blocked(token, command):
        index = int(command.request_key.removeprefix('parallel'))
        entered[index].set()
        assert release.wait(10)
        return fake_result(command)
    monkeypatch.setattr(c[0], 'acquire', blocked)
    app = create_extraction_test_app(c[0], c[3][4],
                                    ExtractionHTTPPolicy(max_concurrent_acquisitions=2))
    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
            base_url=c[3][2].policy.origin,
            cookies={c[3][2].policy.cookie_name: c[2]}) as client:
            pending = [asyncio.create_task(client.post(api[3],
                headers=api[1] | {'Idempotency-Key': f'parallel{i}'}, json=api[2]))
                       for i in range(2)]
            try:
                assert await asyncio.to_thread(entered[0].wait, 5)
                assert await asyncio.to_thread(entered[1].wait, 5)
                third = await client.post(api[3], headers=api[1], json=api[2])
                assert third.status_code == 429
            finally:
                release.set()
                responses = await asyncio.gather(*pending)
            assert all(r.status_code == 200 for r in responses)
    asyncio.run(scenario())


def test_post_deadline_returns_unknown_without_claiming_rollback(api, monkeypatch):
    async def late(*args, **kwargs):
        raise GuestDenied(409, 'acquisition_deadline_elapsed')
    monkeypatch.setattr(api[4][0], 'acquire', late)
    response = start(api)
    assert response.status_code == 409
    assert response.json()['outcome'] == 'unknown'
    assert response.json()['recovery'] == 'original_request_key'


@pytest.mark.parametrize('whitespace', [' ', '\t'])
def test_duplicate_cookie_key_whitespace_matches_actual_parser(api, whitespace):
    c = api[4]
    foreign, _ = c[3][2].issue()
    name = c[3][2].policy.cookie_name
    cookie = f'{name}={foreign}; {name}{whitespace}={c[2]}'
    response = api[0].post(api[3], headers=api[1] | {'Cookie': cookie}, json=api[2])
    assert response.status_code == 401 and not c[4]


@pytest.mark.parametrize('method', ['post', 'status', 'key'])
def test_expiry_at_worker_ack_denies_status_serialization(api, monkeypatch, method):
    from batchbeacon import extraction_api
    c = api[4]
    status = start(api).json()
    original = extraction_api.run_in_threadpool
    async def delayed(function, *args, **kwargs):
        result = await original(function, *args, **kwargs)
        if function.__name__ in {'execute', 'status', 'status_for_key'}:
            c[3][5][0] = c[6].scope.expires_at
        return result
    monkeypatch.setattr(extraction_api, 'run_in_threadpool', delayed)
    if method == 'post':
        response = start(api)
    elif method == 'status':
        response = api[0].get(api[3] + '/' + status['run_id'])
    else:
        response = api[0].get(api[3] + '/reconcile', headers=api[1])
    assert response.status_code == 401 and 'run_id' not in response.json()
    assert len(c[4]) == 2

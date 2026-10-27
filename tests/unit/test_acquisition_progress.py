"""Streaming transport preserves the existing acquisition and ownership lifecycle."""
# ruff: noqa: F811

import asyncio
import json
from datetime import timedelta
from threading import Event
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient

from batchbeacon.extraction_api import (
    PROGRESS_MEDIA_TYPE,
    PROGRESS_PROTOCOL,
    ExtractionHTTPPolicy,
    create_extraction_test_app,
)
from batchbeacon.extraction_service import AcquisitionStatus
from batchbeacon.guest_service import GuestDenied
from tests.unit.test_extraction_api import api  # noqa: F401
from tests.unit.test_extraction_service import coordinator  # noqa: F401
from tests.unit.test_firestore_store import no_network_or_credentials, setup  # noqa: F401
from tests.unit.test_shared_admission import env  # noqa: F401


def application(fixture, **changes):
    c = fixture[4]
    policy = ExtractionHTTPPolicy(progress_response_enabled=True,
        progress_interval_seconds=.01, **changes)
    return create_extraction_test_app(c[0], c[3][4], policy)


def call(fixture, app, **header_changes):
    c = fixture[4]
    with TestClient(app) as client:
        client.cookies.set(c[3][2].policy.cookie_name, c[2])
        return client.post(fixture[3], json=fixture[2], headers=fixture[1] | {
            'X-BatchBeacon-Progress': PROGRESS_PROTOCOL} | header_changes)


def test_streamed_actual_acquisition_replays_without_another_model_call(api):
    app = application(api)
    first = call(api, app)
    assert first.status_code == 200 and first.content.startswith(b'\n')
    assert first.headers['content-type'] == PROGRESS_MEDIA_TYPE
    assert first.headers['cache-control'] == 'no-store, private, no-transform'
    assert first.headers['x-accel-buffering'] == 'no'
    envelope = first.json()
    assert envelope['protocol'] == PROGRESS_PROTOCOL and envelope['status'] == 200
    assert envelope['body']['state'] == 'COMPLETE'
    assert call(api, app).json() == envelope and len(api[4][4]) == 2


@pytest.mark.parametrize('status,code,unknown', [
    (429, 'acquisition_capacity_unavailable', False),
    (503, 'provider_unavailable', True), (409, 'acquisition_deadline_elapsed', True)])
def test_errors_after_headers_are_explicit_not_success(api, monkeypatch, status, code, unknown):
    async def fail(*args):
        raise GuestDenied(status, code)
    monkeypatch.setattr(api[4][0], 'acquire', fail)
    result = call(api, application(api)).json()
    assert result['status'] == status and result['body']['error'] == code
    assert (result['body'].get('outcome') == 'unknown') is unknown
    assert not api[4][4]


def test_expiry_after_worker_completion_prevents_final_evidence(api, monkeypatch):
    c = api[4]
    async def late(*args):
        c[3][5][0] = c[6].scope.expires_at + timedelta(seconds=1)
        return AcquisitionStatus(run_id='a'*32, incident_id=c[1].incident_id,
                                 state='COMPLETE', current=True)
    monkeypatch.setattr(c[0], 'acquire', late)
    result = call(api, application(api)).json()
    assert result['status'] == 401 and 'run_id' not in result['body']


@pytest.mark.parametrize('change', ['version', 'duplicate', 'csrf', 'body'])
def test_stream_preflight_fails_before_worker(api, change):
    headers = list((api[1] | {'X-BatchBeacon-Progress': PROGRESS_PROTOCOL}).items())
    body = api[2]
    if change == 'version':
        headers = [(k, 'unknown' if k == 'X-BatchBeacon-Progress' else v) for k, v in headers]
    elif change == 'duplicate':
        headers.append(('X-BatchBeacon-Progress', PROGRESS_PROTOCOL))
    elif change == 'csrf':
        headers = [(k, v) for k, v in headers if k != 'X-CSRF-Token']
    else:
        body = body | {'authority': 'untrusted'}
    c = api[4]
    with TestClient(application(api)) as client:
        client.cookies.set(c[3][2].policy.cookie_name, c[2])
        response = client.post(api[3], json=body, headers=headers)
    assert response.status_code in (403, 406, 422) and not c[4]
    assert response.headers['content-type'].startswith('application/json')


@pytest.mark.parametrize('values', [
    {'progress_interval_seconds': 0}, {'progress_interval_seconds': float('inf')},
    {'progress_timeout_seconds': float('nan')}, {'progress_timeout_seconds': -1},
    {'progress_interval_seconds': '1'}, {'progress_response_enabled': 'true'},
    {'progress_interval_seconds': 15., 'progress_timeout_seconds': 15.}])
def test_invalid_progress_policy_fails_closed(values):
    with pytest.raises(ValueError):
        ExtractionHTTPPolicy(**values)


def test_progress_policy_defaults_digest_and_consumer_window(api):
    policy = ExtractionHTTPPolicy()
    assert not policy.progress_response_enabled and policy.progress_interval_seconds == 15.
    assert policy.progress_timeout_seconds == 230.
    assert application(api).state.extraction_http_policy_hash != policy.digest()
    with pytest.raises(ValueError, match='cover_model_run'):
        application(api, progress_timeout_seconds=float(api[4][0].config.run_seconds))


def test_default_disabled_keeps_ordinary_response_compatible(api):
    response = call(api, api[5])
    assert response.headers['content-type'] == 'application/json'
    assert response.json()['state'] == 'COMPLETE' and len(api[4][4]) == 2


def test_response_deadline_is_unknown_and_joins_actual_settlement(api, monkeypatch):
    import batchbeacon.extraction_api as adapter
    values = iter([0., 1000.])
    monkeypatch.setattr(adapter, 'monotonic', lambda: next(values, 1000.))
    result = call(api, application(api)).json()
    assert result['status'] == 503 and result['body']['outcome'] == 'unknown'
    assert result['body']['recovery'] == 'original_request_key'
    # The stream's deadline is not evidence of cancellation or a refund. Join
    # actual ADK/mock settlement, then recover the original run without a retry.
    assert len(api[4][4]) == 2
    status = api[4][0].status_for_key(api[4][2], api[4][1].incident_id,
                                    api[4][1].request_key)
    assert status.state == 'COMPLETE'


@pytest.mark.parametrize('spec', ['2.0', '2.4'])
@pytest.mark.parametrize('disconnect', [False, True])
def test_raw_asgi_heartbeat_and_disconnect_keep_worker_owned(api, monkeypatch, spec, disconnect):
    c = api[4]
    released, completed = Event(), Event()
    calls = []
    async def slow(token, command):
        calls.append(command.request_key)
        assert released.wait(5)
        completed.set()
        return AcquisitionStatus(run_id='a'*32, incident_id=command.incident_id,
                                 state='INCOMPLETE', current=False)
    monkeypatch.setattr(c[0], 'acquire', slow)
    app = application(api)

    async def scenario():
        body_sent = False
        disconnect_event = asyncio.Event()
        first_body = asyncio.Event()
        messages = []
        headers = api[1] | {'X-BatchBeacon-Progress': PROGRESS_PROTOCOL,
            'Cookie': c[3][2].policy.cookie_name+'='+c[2], 'Content-Type': 'application/json'}
        origin = urlsplit(c[3][2].policy.origin)
        scope = {'type': 'http', 'asgi': {'version': '3.0', 'spec_version': spec},
            'method': 'POST', 'scheme': origin.scheme, 'http_version': '1.1',
            'path': api[3], 'raw_path': api[3].encode(), 'query_string': b'',
            'root_path': '', 'server': (origin.hostname, origin.port or 80),
            'client': ('127.0.0.1', 1234),
            'headers': [(k.lower().encode(), v.encode()) for k, v in headers.items()]}
        async def receive():
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {'type': 'http.request', 'body': json.dumps(api[2]).encode()}
            await disconnect_event.wait()
            return {'type': 'http.disconnect'}
        async def send(message):
            messages.append(message)
            if message['type'] == 'http.response.body' and message.get('body'):
                if not first_body.is_set():
                    assert not completed.is_set() and message['body'].strip() == b''
                    first_body.set()
                elif disconnect and spec == '2.4':
                    raise OSError('controlled disconnect')
        running = asyncio.create_task(app(scope, receive, send))
        await asyncio.wait_for(first_body.wait(), 2)
        await asyncio.sleep(.02)
        if disconnect and spec == '2.0':
            disconnect_event.set()
        await asyncio.sleep(.03)
        assert not running.done() and not completed.is_set()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
            base_url=c[3][2].policy.origin,
            cookies={c[3][2].policy.cookie_name: c[2]}) as client:
            refused = await client.post(api[3], headers=api[1], json=api[2])
            assert refused.status_code == 429
        released.set()
        try:
            await asyncio.wait_for(running, 2)
        except (OSError, ExceptionGroup):
            assert disconnect
        assert completed.is_set() and calls == [c[1].request_key]
        if not disconnect:
            payload = b''.join(m.get('body', b'') for m in messages)
            assert json.loads(payload)['body']['state'] == 'INCOMPLETE'
            assert len([m for m in messages if m.get('body') == b'\n']) >= 2
    try:
        asyncio.run(scenario())
    finally:
        released.set()


def test_v2_stages_are_bounded_ordered_and_terminal_is_unique(api):
    from batchbeacon.extraction_api import STAGE_MEDIA_TYPE, STAGE_PROTOCOL
    response = call(api, application(api), **{'X-BatchBeacon-Progress': STAGE_PROTOCOL})
    assert response.headers['content-type'] == STAGE_MEDIA_TYPE
    frames = [json.loads(line) for line in response.content.splitlines() if line.strip()]
    assert [f['sequence'] for f in frames] == list(range(len(frames)))
    assert [f['stage'] for f in frames[:-1]] == ['preparing', 'model', 'saving']
    assert frames[-1]['type'] == 'terminal' and frames[-1]['status'] == 200
    assert frames[-1]['body']['state'] == 'COMPLETE'
    assert len(response.content) < 65536
    # Reconciliation/replay carries no new provider dispatch.
    replay = call(api, application(api), **{'X-BatchBeacon-Progress': STAGE_PROTOCOL})
    assert replay.status_code == 200
    assert len(api[4][4]) == 2


def test_v2_failure_never_claims_model_dispatch(api, monkeypatch):
    from batchbeacon.extraction_api import STAGE_PROTOCOL
    async def fail(*args):
        raise GuestDenied(429, 'acquisition_capacity_unavailable')
    monkeypatch.setattr(api[4][0], 'acquire', fail)
    response = call(api, application(api), **{'X-BatchBeacon-Progress': STAGE_PROTOCOL})
    frames = [json.loads(line) for line in response.content.splitlines() if line.strip()]
    assert all(f.get('stage') != 'model' for f in frames)
    assert frames[-1]['status'] == 429 and not api[4][4]


def test_timing_spans_are_nonoverlapping_private_and_failures_retained(monkeypatch):
    import batchbeacon.acquisition_timing as module
    from batchbeacon.acquisition_timing import AcquisitionTiming, observe, stage
    async def check():
        clock = iter([0., 1., 3., 6., 10.])
        monkeypatch.setattr(module, 'monotonic', lambda: next(clock))
        trace = AcquisitionTiming('a' * 64)
        with observe(trace):
            stage('ownership')
            stage('preparation')
            stage('provider')
        logged = []
        monkeypatch.setattr(module._logger, 'info', logged.append)
        result = trace.finish('unknown')
        assert result['seconds'] == 10
        assert [s['seconds'] for s in result['spans']] == [2., 3., 4.]
        assert trace.progress() == ('preparing', 'model')
        assert trace.finish('COMPLETE') is None
        assert json.loads(logged[-1])['outcome'] == 'unknown'
    asyncio.run(check())


def test_timing_sink_survives_exact_uvicorn_logging_config():
    import os
    import subprocess
    import sys

    code = """
import asyncio, logging.config
import uvicorn.config
logging.config.dictConfig(uvicorn.config.LOGGING_CONFIG)
from batchbeacon.acquisition_timing import AcquisitionTiming
async def main():
    trace = AcquisitionTiming('a'*64)
    trace.begin('ownership')
    trace.finish('refused')
asyncio.run(main())
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True,
                            text=True, timeout=10, env=os.environ | {'PYTHONPATH': 'src'})
    assert result.returncode == 0
    record = json.loads(result.stderr.strip())
    assert record['event'] == 'acquisition_timing_v1' and record['outcome'] == 'refused'


def test_plain_response_expiry_is_refused_in_timing_not_complete(api, monkeypatch):
    from batchbeacon.acquisition_timing import AcquisitionTiming
    records = []
    finish = AcquisitionTiming.finish
    def capture(self, outcome):
        result = finish(self, outcome)
        records.append(result)
        return result
    monkeypatch.setattr(AcquisitionTiming, 'finish', capture)
    c = api[4]
    async def late(*args):
        c[3][5][0] = c[6].scope.expires_at + timedelta(seconds=1)
        return AcquisitionStatus(run_id='a'*32, incident_id=c[1].incident_id,
                                 state='COMPLETE', current=True)
    monkeypatch.setattr(c[0], 'acquire', late)
    result = call(api, api[5])
    assert result.status_code == 401
    assert records[-1]['outcome'] == 'refused'

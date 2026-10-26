"""Explicit offline acquisition HTTP integration; default application stays unmounted."""

import asyncio
import json
from contextlib import suppress
from threading import BoundedSemaphore
from time import monotonic
from typing import Annotated

import anyio
from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import Field, TypeAdapter, ValidationError, model_validator
from starlette.concurrency import run_in_threadpool

from batchbeacon.action_service import ActionService
from batchbeacon.contracts import Record
from batchbeacon.extraction_service import AcquisitionCommand, ExtractionService, owned_boundary
from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey
from batchbeacon.incident_api import (
    IncidentHTTPPolicy,
    _command,
    _no_body,
    _queries,
    create_incident_test_app,
)


class ExtractionHTTPPolicy(IncidentHTTPPolicy):
    max_concurrent_acquisitions: Annotated[int, Field(gt=0)] = 1
    progress_response_enabled: bool = False
    progress_interval_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 15.0
    progress_timeout_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 230.0

    @model_validator(mode='after')
    def progress_window(self):
        if self.progress_interval_seconds >= self.progress_timeout_seconds:
            raise ValueError('progress_interval_must_fit_response_window')
        return self


PROGRESS_PROTOCOL = 'acquisition-progress-v1'
PROGRESS_MEDIA_TYPE = 'application/vnd.batchbeacon.acquisition+json'


class _OwnedProgressResponse(StreamingResponse):
    """A disconnect must not detach the acquisition from its request lifecycle."""

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            # ASGI 2.4 send failures do not necessarily close the iterator.
            with anyio.CancelScope(shield=True):
                await self.body_iterator.aclose()


class AcquisitionStart(Record):
    source_selection: Annotated[str, Field(pattern=r'^[a-z][a-z0-9_-]{0,63}$')]
    capture_ids: tuple[OpaqueId, ...] = Field(min_length=1, max_length=2)
    expected_observation_revision: Annotated[int, Field(ge=0)]


def create_extraction_test_app(
    extraction: ExtractionService, actions: ActionService, policy: ExtractionHTTPPolicy,
):
    if extraction is None or policy is None or extraction.config.mode != 'offline_test':
        raise ValueError('explicit_offline_extraction_graph_required')
    return _create_extraction_app(extraction, actions, policy)


def create_extraction_app(
    extraction: ExtractionService, actions: ActionService, policy: ExtractionHTTPPolicy,
):
    """Explicit real-provider graph; admission and provisioning remain operator-owned."""
    if extraction is None or policy is None or extraction.config.mode != 'vertex':
        raise ValueError('explicit_vertex_extraction_graph_required')
    extraction.config.validate_consumer(extraction.shared)
    app = _create_extraction_app(extraction, actions, policy)
    app.state.health_view = {"mode": "explicit_real_provider", "product": "not_ready",
                             "paid_admission": "operator_bound"}
    return app


def _create_extraction_app(extraction, actions, policy):
    if policy.progress_response_enabled \
            and policy.progress_timeout_seconds <= extraction.config.run_seconds:
        raise ValueError('progress_window_must_cover_model_run')
    evidence = extraction.evidence
    guest = evidence.guest
    app = create_incident_test_app(guest, evidence, actions, policy)
    app.title = 'BatchBeacon extraction adapter test'
    app.state.extraction_http_policy_hash = policy.digest()
    capacity = BoundedSemaphore(policy.max_concurrent_acquisitions)
    prior_denied = app.exception_handlers[GuestDenied]

    @app.exception_handler(GuestDenied)
    async def denied(request, error):
        if request.method == 'POST' and request.url.path.endswith('/acquisitions') \
                and (error.status >= 500 or error.code == 'acquisition_deadline_elapsed'):
            return JSONResponse({'error': error.code, 'outcome': 'unknown',
                                 'recovery': 'original_request_key'}, status_code=error.status)
        return await prior_denied(request, error)

    @owned_boundary
    def owned(request, incident_id, *, mutation=False):
        cookies = request.headers.getlist('cookie')
        occurrences = sum(part.partition('=')[0].strip() == guest.policy.cookie_name
                          for header in cookies for part in header.split(';'))
        if len(cookies) > 1 or occurrences > 1:
            raise GuestDenied(401, 'guest_unavailable')
        token = request.cookies.get(guest.policy.cookie_name)
        session = guest.resolve(token)
        if mutation:
            if any(len(request.headers.getlist(name)) != 1
                   for name in ('origin', 'x-csrf-token')):
                raise GuestDenied(403, 'mutation_guard_required')
            guest.guard(request.headers.get('origin'), token, request.headers.get('x-csrf-token'))
        try:
            TypeAdapter(OpaqueId).validate_python(incident_id)
        except ValidationError:
            raise GuestDenied(422, 'invalid_incident_id') from None
        guest.incident(token, incident_id)
        return token, session

    def response(result, token, session):
        # The worker's last access check can precede its acknowledgement to ASGI.
        # Scope expiry is immutable; recheck it at the actual response boundary.
        guest._live(session, guest._key(token))
        return result.model_dump(mode='json')

    def identifier(value, schema, code):
        try:
            return TypeAdapter(schema).validate_python(value)
        except ValidationError:
            raise GuestDenied(422, code) from None

    def request_key(request):
        values = request.headers.getlist('idempotency-key')
        if len(values) != 1:
            raise GuestDenied(422, 'request_key_required')
        return identifier(values[0], RequestKey, 'request_key_required')

    def execute(token, command):
        # The worker owns its slot through actual completion, including when the
        # HTTP client disappears. Cancellation cannot terminate a Python thread.
        if not capacity.acquire(blocking=False):
            raise GuestDenied(429, 'acquisition_capacity_unavailable')
        try:
            return asyncio.run(extraction.acquire(token, command))
        finally:
            capacity.release()

    @app.get('/api/incidents/{incident_id}/capabilities')
    async def capabilities(incident_id: str, request: Request):
        token, session = await run_in_threadpool(owned, request, incident_id)
        _queries(request, set())
        await _no_body(request, policy)
        result = await run_in_threadpool(extraction.capabilities, token, incident_id)
        return response(result, token, session)

    @app.post('/api/incidents/{incident_id}/acquisitions')
    async def acquire(incident_id: str, request: Request):
        token, session = await run_in_threadpool(owned, request, incident_id, mutation=True)
        key = request_key(request)
        _queries(request, set())
        body = await _command(request, AcquisitionStart, policy)
        command = AcquisitionCommand(incident_id=incident_id, request_key=key, **body.model_dump())
        progress = request.headers.getlist('x-batchbeacon-progress')
        if progress and progress != [PROGRESS_PROTOCOL]:
            raise GuestDenied(406, 'unsupported_acquisition_progress')
        if progress and policy.progress_response_enabled:
            async def stream():
                # This is the same finite worker as the ordinary response. The
                # iterator and response both join it, even after a disconnect.
                worker = asyncio.create_task(run_in_threadpool(execute, token, command))
                deadline = monotonic() + policy.progress_timeout_seconds
                try:
                    yield b'\n'
                    while not worker.done():
                        remaining = deadline - monotonic()
                        if remaining <= 0:
                            break
                        done, _ = await asyncio.wait(
                            {worker}, timeout=min(policy.progress_interval_seconds, remaining))
                        if not done and monotonic() < deadline:
                            yield b'\n'
                    try:
                        if not worker.done() or monotonic() >= deadline:
                            raise GuestDenied(503, 'acquisition_response_deadline_elapsed')
                        # Recheck immutable ownership expiry at final publication.
                        payload = response(worker.result(), token, session)
                        status = 200
                    except GuestDenied as error:
                        rejected = await denied(request, error)
                        payload, status = json.loads(rejected.body), rejected.status_code
                    except Exception:
                        payload = {'error': 'acquisition_response_unavailable',
                                   'outcome': 'unknown', 'recovery': 'original_request_key'}
                        status = 503
                    yield json.dumps({'protocol': PROGRESS_PROTOCOL, 'status': status,
                                      'body': payload}, separators=(',', ':')).encode()
                finally:
                    # A stopped stream does not cancel a model call, release its
                    # capacity early, or imply a refund. The bounded worker owns
                    # accounting through actual completion, as on the JSON path.
                    with anyio.CancelScope(shield=True), suppress(Exception):
                        await asyncio.shield(worker)

            return _OwnedProgressResponse(stream(), media_type=PROGRESS_MEDIA_TYPE,
                headers={'Cache-Control': 'private, no-store, no-transform',
                         'X-Accel-Buffering': 'no'})
        result = await run_in_threadpool(execute, token, command)
        return response(result, token, session)

    # Literal key-recovery path precedes opaque run IDs.
    @app.get('/api/incidents/{incident_id}/acquisitions/reconcile')
    async def reconcile(incident_id: str, request: Request):
        token, session = await run_in_threadpool(owned, request, incident_id)
        _queries(request, set())
        key = request_key(request)
        await _no_body(request, policy)
        result = await run_in_threadpool(extraction.status_for_key, token, incident_id, key)
        return response(result, token, session)

    @app.get('/api/incidents/{incident_id}/acquisitions/{run_id}')
    async def status(incident_id: str, run_id: str, request: Request):
        token, session = await run_in_threadpool(owned, request, incident_id)
        identifier(run_id, OpaqueId, 'invalid_run_id')
        _queries(request, set())
        await _no_body(request, policy)
        result = await run_in_threadpool(extraction.status, token, run_id)
        if result.incident_id != incident_id:
            raise GuestDenied(404, 'acquisition_unavailable')
        return response(result, token, session)

    return app

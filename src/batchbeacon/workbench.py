"""Connected local workbench. Explicit offline graph; no production fallback."""

from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from batchbeacon.extraction_api import (
    ExtractionHTTPPolicy,
    create_extraction_app,
    create_extraction_test_app,
)
from batchbeacon.extraction_service import owned_boundary
from batchbeacon.guest_service import GuestDenied
from batchbeacon.incident_api import _no_body
from batchbeacon.retail_api import mount_retail_api

ROOT = Path(__file__).resolve().parents[2]


def create_workbench_test_app(extraction, actions, refresh, policy: ExtractionHTTPPolicy,
                              *, learning=None):
    """Compose existing owned adapters. This factory cannot activate a paid provider."""
    return _create_workbench(extraction, actions, refresh, policy, real=False, learning=learning)


def create_workbench_app(extraction, actions, refresh, policy: ExtractionHTTPPolicy,
                         *, learning=None):
    """Compose an explicitly admitted graph; never initialize or replenish its budget."""
    return _create_workbench(extraction, actions, refresh, policy, real=True, learning=learning)


def _create_workbench(extraction, actions, refresh, policy, *, real, learning):
    guest, evidence = extraction.evidence.guest, extraction.evidence
    if refresh.guest is not guest or refresh.retail.projector.actions is not actions:
        raise ValueError('one consistent workbench graph required')
    factory = create_extraction_app if real else create_extraction_test_app
    app = factory(extraction, actions, policy)
    mount_retail_api(app, refresh, policy)
    if learning is not None:
        from batchbeacon.learning_api import mount_learning_api
        if learning.guest is not guest or learning.evidence is not evidence:
            raise ValueError('learning requires the same owned workbench graph')
        mount_learning_api(app, learning, policy)
    app.title = 'BatchBeacon AI' if real else 'BatchBeacon AI — connected local integration'
    prior_denied = app.exception_handlers[GuestDenied]

    @app.exception_handler(GuestDenied)
    async def denied(request, error):
        if request.method == 'POST' and request.url.path.endswith('/verifications') \
                and error.status >= 500:
            from fastapi.responses import JSONResponse
            return JSONResponse({'error': error.code, 'outcome': 'unknown',
                                 'recovery': 'original_request_key'}, status_code=error.status)
        response = await prior_denied(request, error)
        if error.status == 401:
            response.delete_cookie(guest.policy.cookie_name, path='/',
                                   secure=guest.policy.mode == 'deployment', httponly=True,
                                   samesite='strict')
        return response
    ui = Path(__file__).parent / 'ui'

    @app.middleware('http')
    async def security_headers(request, call_next):
        response = await call_next(request)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob:; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; "
            "form-action 'self'")
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response

    @app.get('/', include_in_schema=False)
    def index():
        return FileResponse(ui / 'index.html')

    @app.get('/design/{name}', include_in_schema=False)
    def design(name: str):
        if name not in {'style.css', 'mark.svg'}:
            raise GuestDenied(404, 'asset_unavailable')
        return FileResponse(ROOT / 'prototypes/refined' / name)

    @app.get('/api/workbench/config')
    def configuration():
        from batchbeacon.guidance_policies import POLICIES
        identities = evidence.identities.catalog.identities if evidence.identities else ()
        return {
            'mode': 'REAL_VERTEX_EXTRACTION' if real else 'LOCAL_INTEGRATION_SIMULATED_EXTRACTION',
            'server_time': guest._now().isoformat(),
            'storage': 'Explicitly configured application stores' if real else
                'Explicitly injected test adapters; not cloud persistence',
            'sources': [{'selection': key, 'notice': bundle.notice.model_dump(mode='json',
                exclude={'review'})} for key, bundle in extraction.sources.items()],
            'samples': [{'id': row.fixture_id, 'name': row.name, 'synthetic': True}
                        for row in identities],
            'max_images': guest.policy.uploads.max_images,
            'max_image_bytes': guest.policy.uploads.max_image_bytes,
            'refresh_interval_seconds': refresh.policy.minimum_interval_seconds,
            'guidance': 'OWNED_LIFECYCLE_CONNECTED' if learning else
                'OWNED_LIFECYCLE_NOT_CONNECTED',
            'guidance_policies': {key: value.model_dump(mode='json')
                                  for key, value in POLICIES.items()} if learning else {},
        }

    @app.get('/samples/{sample_id}.png', include_in_schema=False)
    def sample(sample_id: str):
        identities = evidence.identities.catalog.identities if evidence.identities else ()
        allowed = {row.fixture_id: row.approved_image_sha256 for row in identities}
        if sample_id not in allowed:
            raise GuestDenied(404, 'sample_unavailable')
        from hashlib import sha256

        from fastapi.responses import Response
        raw = (ROOT / 'fixtures/synthetic' / (sample_id + '.png')).read_bytes()
        if sha256(raw).hexdigest() != allowed[sample_id]:
            raise GuestDenied(503, 'sample_unavailable')
        return Response(raw, media_type='image/png')

    def owned(request, incident_id, mutation=False):
        token = request.cookies.get(guest.policy.cookie_name)
        session = guest.resolve(token)
        if mutation:
            guest.guard(request.headers.get('origin'), token, request.headers.get('x-csrf-token'))
        incident = guest.incident(token, incident_id)
        return token, session, incident

    @app.get('/api/incidents/{incident_id}/captures')
    async def captures(incident_id: str, request: Request):
        token, session, incident = await run_in_threadpool(owned, request, incident_id)
        await _no_body(request, policy)
        if request.query_params:
            raise GuestDenied(422, 'unexpected_input')
        guest._live(session, guest._key(token))
        return {'batches': [{'captures': [c.model_dump(mode='json') for c in b.captures],
                             'ready': b.ready} for b in incident.batches]}

    @owned_boundary
    def reverify(request, incident_id):
        from pydantic import TypeAdapter, ValidationError

        from batchbeacon.guest_service import RequestKey
        token, session, _ = owned(request, incident_id, True)
        keys = request.headers.getlist('idempotency-key')
        if len(keys) != 1:
            raise GuestDenied(422, 'request_key_required')
        try:
            key = TypeAdapter(RequestKey).validate_python(keys[0])
        except ValidationError:
            raise GuestDenied(422, "request_key_required") from None
        binding = evidence.verification_binding(token, incident_id, request_key=key)
        extraction.shared.reserve_verification(session.capability_hash, incident_id, key, binding)
        evidence.publish_verification(token, incident_id, key, binding)
        from batchbeacon.incident_api import _evidence_view
        view = evidence.read_evidence(token, incident_id)
        guest._live(session, guest._key(token))
        return _evidence_view(view)

    @app.post('/api/incidents/{incident_id}/verifications')
    async def verify(incident_id: str, request: Request):
        await _no_body(request, policy)
        if request.query_params:
            raise GuestDenied(422, 'unexpected_input')
        return await run_in_threadpool(reverify, request, incident_id)

    app.mount('/assets', StaticFiles(directory=ui), name='workbench-assets')
    return app

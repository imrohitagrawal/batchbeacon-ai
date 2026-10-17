"""Injectable T09 HTTP boundary; NOT mounted by the preparation application.

Cloud adapters, shared request/budget controls and real-service tests are pending.
Constructing this test surface never enables any model or stock-action endpoint.
"""

import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser, parse_options_header

from batchbeacon.guest_service import GuestDenied, GuestService, csrf_for
from batchbeacon.uploads import InvalidUpload, sanitize_images


class _ImageParser(MultiPartParser):
    def __init__(self, request, policy):
        async def bounded_stream():
            total = 0
            async for chunk in request.stream():
                total += len(chunk)
                if total > policy.max_request_bytes:
                    raise GuestDenied(413, "upload_allowance_exceeded")
                yield chunk

        super().__init__(
            request.headers,
            bounded_stream(),
            max_files=policy.max_images,
            max_fields=0,
            max_part_size=policy.multipart_overhead_bytes,
        )
        self.policy, self.part_bytes, self.ended = policy, 0, False
        self.spool_max_size = policy.spool_bytes

    def on_part_begin(self):
        self.part_bytes = 0
        super().on_part_begin()

    def on_part_data(self, data, start, end):
        self.part_bytes += end - start
        if self.part_bytes > self.policy.max_image_bytes:
            raise GuestDenied(413, "upload_allowance_exceeded")
        super().on_part_data(data, start, end)

    def on_end(self):
        self.ended = True


async def _images(request, policy):
    content_type, _ = parse_options_header(request.headers.get("content-type", ""))
    if content_type != b"multipart/form-data":
        raise GuestDenied(415, "synthetic_image_files_required")
    parser = _ImageParser(request, policy)
    try:
        async with asyncio.timeout(policy.read_deadline_seconds):
            form = await parser.parse()
            try:
                items = form.multi_items()
                if (
                    not parser.ended
                    or not items
                    or any(
                        name != "images" or not isinstance(value, UploadFile)
                        for name, value in items
                    )
                ):
                    raise GuestDenied(422, "invalid_image_upload")
                raw = tuple([await value.read(policy.max_image_bytes + 1) for _, value in items])
            finally:
                await form.close()
    except MultiPartException as exc:
        raise GuestDenied(422, "invalid_image_upload") from exc
    except TimeoutError as exc:
        raise GuestDenied(408, "upload_timed_out") from exc
    finally:
        # Incomplete parts never enter FormData; close the entire parser file registry.
        # This installed Starlette internal is pinned and covered by a leak regression.
        for temporary_file in parser._files_to_close_on_error:
            temporary_file.close()
    try:
        return await run_in_threadpool(sanitize_images, raw, policy)
    except InvalidUpload as exc:
        raise GuestDenied(422, "invalid_image_upload") from exc


def create_guest_test_app(service: GuestService) -> FastAPI:
    """Explicit adapter-test factory, no persistence fallback or service discovery."""
    app = FastAPI(
        title="BatchBeacon guest adapter test", docs_url=None, redoc_url=None, openapi_url=None
    )
    policy = service.policy

    @app.middleware("http")
    async def private_headers(request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, private"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(GuestDenied)
    async def denied(request, exc):
        return JSONResponse({"error": exc.code}, status_code=exc.status)

    def capability(request):
        token = request.cookies.get(policy.cookie_name)
        service.resolve(token)
        return token

    def mutation(request):
        token = capability(request)
        service.guard(request.headers.get("origin"), token, request.headers.get("x-csrf-token"))
        return token

    def operation(request):
        # Strict, body-free command key; no client actor/shop/pool/source claims accepted.
        from pydantic import TypeAdapter, ValidationError

        from batchbeacon.guest_service import RequestKey

        try:
            return TypeAdapter(RequestKey).validate_python(request.headers.get("idempotency-key"))
        except ValidationError as exc:
            raise GuestDenied(422, "request_key_required") from exc

    async def no_body(request):
        try:
            async with asyncio.timeout(policy.uploads.read_deadline_seconds):
                async for chunk in request.stream():
                    if chunk:
                        raise GuestDenied(422, "unexpected_input")
        except TimeoutError as exc:
            raise GuestDenied(408, "request_timed_out") from exc
        if request.query_params:
            raise GuestDenied(422, "unexpected_input")

    @app.get("/healthz")
    def health():
        return {"mode": "adapter_test", "product": "not_ready", "paid_admission": "closed"}

    @app.post("/api/guest")
    async def guest(request: Request):
        service.guard(request.headers.get("origin"))
        await no_body(request)
        token = request.cookies.get(policy.cookie_name)
        if token:
            session = service.resolve(token)
        else:
            token, session = service.issue()
        # CSRF is intentionally JS-readable, while the bearer capability is only a cookie.
        response = JSONResponse(
            {
                "csrf_token": csrf_for(token),
                "expires_at": session.scope.expires_at.isoformat(),
                "demo_manager": session.demo_manager,
            }
        )
        remaining = max(0, int((session.scope.expires_at - service.clock()).total_seconds()))
        response.set_cookie(
            policy.cookie_name,
            token,
            max_age=remaining,
            httponly=True,
            secure=policy.mode == "deployment",
            samesite="strict",
            path="/",
        )
        return response

    @app.post("/api/incidents")
    async def new_incident(request: Request):
        token, key = mutation(request), operation(request)
        await no_body(request)
        incident = await run_in_threadpool(service.create_incident, token, key)
        return {"incident_id": incident.id}

    @app.get("/api/incidents")
    def list_incidents(request: Request):
        session = service.resolve(capability(request))
        return {"incident_ids": [i.id for i in session.incidents]}

    @app.post("/api/incidents/{incident_id}/captures")
    async def upload(incident_id: str, request: Request):
        token, key = mutation(request), operation(request)
        service.incident(token, incident_id)  # Reject foreign IDs before parsing bytes.
        if request.query_params:
            raise GuestDenied(422, "unexpected_input")
        images = await _images(request, policy.uploads)
        result = await run_in_threadpool(service.retain, token, incident_id, key, images)
        return {"captures": [c.model_dump() for c in result.captures], "ready": result.ready}

    @app.get("/api/incidents/{incident_id}/captures/{capture_id}")
    def image(incident_id: str, capture_id: str, request: Request):
        data = service.image(capability(request), incident_id, capture_id)
        return Response(data, media_type="image/png")

    return app

"""Owned historical selection only. Trusted global refresh has no HTTP route."""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import TypeAdapter, ValidationError
from starlette.concurrency import run_in_threadpool

from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey
from batchbeacon.incident_api import _command, _no_body, _queries
from batchbeacon.source_service import SourceCommand, StartSourceReview


def mount_source_api(app, service, policy):
    guest = service.guest
    prior = app.exception_handlers[GuestDenied]

    @app.exception_handler(GuestDenied)
    async def denied(request, error):
        if (
            request.method == "POST"
            and error.status >= 500
            and (request.url.path == "/api/source-reviews" or request.url.path.endswith("/source"))
        ):
            return JSONResponse(
                {"error": error.code, "outcome": "unknown", "recovery": "original_request_key"},
                status_code=error.status,
            )
        return await prior(request, error)

    def owned(request, incident=None, mutation=False, keyed=False):
        cookies = request.headers.getlist("cookie")
        if (
            len(cookies) != 1
            or sum(
                part.partition("=")[0].strip() == guest.policy.cookie_name
                for header in cookies
                for part in header.split(";")
            )
            != 1
        ):
            raise GuestDenied(401, "guest_expired_or_invalid")
        token = request.cookies.get(guest.policy.cookie_name)
        session = guest.resolve(token)
        if incident is not None:
            try:
                TypeAdapter(OpaqueId).validate_python(incident)
            except ValidationError:
                raise GuestDenied(422, "invalid_incident_id") from None
            guest.incident(token, incident)  # Ownership precedes every body parse.
        if mutation:
            if any(len(request.headers.getlist(n)) != 1 for n in ("origin", "x-csrf-token")):
                raise GuestDenied(403, "mutation_guard_required")
            guest.guard(request.headers.get("origin"), token, request.headers.get("x-csrf-token"))
        key = None
        if mutation or keyed:
            values = request.headers.getlist("idempotency-key")
            try:
                if len(values) != 1:
                    raise ValueError()
                key = TypeAdapter(RequestKey).validate_python(values[0])
            except (ValueError, ValidationError):
                raise GuestDenied(422, "request_key_required") from None
        return token, session, key

    def response(value, token, session):
        guest._live(session, guest._key(token))
        return value

    @app.get("/api/source-reviews/context")
    async def context(request: Request):
        token, session, _ = await run_in_threadpool(owned, request)
        _queries(request, set())
        await _no_body(request, policy)
        value = await run_in_threadpool(service.context, token)
        return response(value, token, session)

    @app.get("/api/source-reviews/reconcile")
    async def reconcile_start(request: Request):
        token, session, key = await run_in_threadpool(owned, request, keyed=True)
        _queries(request, set())
        await _no_body(request, policy)
        value = await run_in_threadpool(service.reconcile_start, token, key)
        return response(value, token, session)

    @app.post("/api/source-reviews")
    async def start(request: Request):
        token, session, key = await run_in_threadpool(owned, request, mutation=True)
        _queries(request, set())
        command = await _command(request, StartSourceReview, policy)
        value = await run_in_threadpool(service.start, token, key, command)
        return response(value, token, session)

    @app.get("/api/incidents/{incident_id}/source")
    async def source(incident_id: str, request: Request):
        token, session, _ = await run_in_threadpool(owned, request, incident_id)
        _queries(request, set())
        await _no_body(request, policy)
        value = await run_in_threadpool(service.read, token, incident_id)
        return response(value, token, session)

    @app.get("/api/incidents/{incident_id}/source/reconcile")
    async def reconcile(incident_id: str, request: Request):
        token, session, key = await run_in_threadpool(owned, request, incident_id, keyed=True)
        _queries(request, set())
        await _no_body(request, policy)
        value = await run_in_threadpool(service.read, token, incident_id, key)
        return response(value, token, session)

    @app.post("/api/incidents/{incident_id}/source")
    async def select(incident_id: str, request: Request):
        token, session, key = await run_in_threadpool(owned, request, incident_id, mutation=True)
        _queries(request, set())
        command = await _command(request, SourceCommand, policy)
        value = await run_in_threadpool(service.select, token, incident_id, key, command)
        return response(value, token, session)

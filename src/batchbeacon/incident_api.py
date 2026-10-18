"""Injected LOCAL/PARTIAL incident HTTP surface; never mounted by the default app.

Services must eventually share a real atomic adapter. No extraction/result/source
write, model call, operator endpoint or persistence fallback is exposed here.
"""

import asyncio
import json
import re
from typing import Annotated, Literal

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Field, TypeAdapter, ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.formparsers import parse_options_header

from batchbeacon.action_service import ActionConfirmation, ActionService
from batchbeacon.contracts import ActionType, ObservedValue, Record
from batchbeacon.evidence_service import EvidenceService
from batchbeacon.guest_api import create_guest_test_app
from batchbeacon.guest_service import GuestDenied, GuestService, OpaqueId, RequestKey


class IncidentHTTPPolicy(Record):
    max_json_bytes: Annotated[int, Field(gt=0)] = 32768
    read_deadline_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 5.0


class CorrectionCommand(Record):
    expected_revision: Annotated[int, Field(ge=1)]
    field: Literal["PRODUCT_NAME", "PACK", "PRODUCT_CODE", "GTIN", "LOT", "BEST_BEFORE", "USE_BY"]
    replacement: ObservedValue


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("ambiguous duplicate key")
        result[key] = value
    return result


def _constant(value):
    raise ValueError("non-JSON constant")


async def _command(request, schema, policy):
    content_type, options = parse_options_header(request.headers.get("content-type", ""))
    if content_type != b"application/json" \
            or options.get(b"charset", b"utf-8").lower() not in {b"utf-8", b"utf8"} \
            or request.headers.get("content-encoding", "identity").lower() != "identity":
        raise GuestDenied(415, "json_command_required")
    chunks, count = [], 0
    try:
        async with asyncio.timeout(policy.read_deadline_seconds):
            async for chunk in request.stream():
                count += len(chunk)
                if count > policy.max_json_bytes:
                    raise GuestDenied(413, "command_too_large")
                chunks.append(chunk)
        raw = b"".join(chunks)
        parsed = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        if not isinstance(parsed, dict):
            raise ValueError("command must be an object")
        return schema.model_validate_json(raw)
    except TimeoutError as exc:
        raise GuestDenied(408, "request_timed_out") from exc
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise GuestDenied(422, "invalid_command") from exc


def _queries(request, allowed):
    items = request.query_params.multi_items()
    if len({key for key, _ in items}) != len(items) or any(key not in allowed for key, _ in items):
        raise GuestDenied(422, "unexpected_input")
    return dict(items)


async def _no_body(request, policy):
    try:
        async with asyncio.timeout(policy.read_deadline_seconds):
            async for chunk in request.stream():
                if chunk:
                    raise GuestDenied(422, "unexpected_input")
    except TimeoutError as exc:
        raise GuestDenied(408, "request_timed_out") from exc


def _revision(value):
    if not value or not re.fullmatch(r"[1-9][0-9]*", value):
        raise GuestDenied(422, "invalid_revision")
    try:
        return int(value)
    except ValueError as exc:
        raise GuestDenied(422, "invalid_revision") from exc


def _action_type(value):
    try:
        return ActionType(value)
    except (TypeError, ValueError) as exc:
        raise GuestDenied(422, "invalid_action_type") from exc


def _action_view(view):
    return {
        "action": view.action.model_dump(mode="json", exclude={"session_id", "actor_session",
                                                              "request_key", "payload_hash"}),
        "event": view.event.model_dump(mode="json", exclude={"session_id"}),
        "current": view.current,
        "requires_renewed_review": view.requires_renewed_review,
    }


def _evidence_view(view):
    state = view.state
    # Raw values, corrections and selected original revisions are reviewable.
    # Provider response bodies/configuration stay in the internal evidence store;
    # this retail surface does not expose diagnostic traces or bearer identities.
    return {
        "observation": view.observation.model_dump(mode="json", exclude={"session_id"})
        if view.observation else None,
        "result": view.result.model_dump(mode="json", exclude={"session_id"})
        if view.result else None,
        "current": view.current,
        "hold_eligible": view.hold_eligible,
        "latest_observation_revision": len(state.observations),
        "active_result_revision": state.active_result,
        "observation_history": [
            {"revision": saved.observation.revision,
             "extraction_revision": saved.extraction_revision,
             "correction_count": len(saved.observation.corrections)}
            for saved in state.observations
        ],
        "extraction_history": [
            {"revision": saved.revision, "recorded_at": saved.recorded_at.isoformat(),
             **saved.envelope.model_dump(mode="json", exclude={"values", "redacted_output_json",
                                                                "configuration_hash"})}
            for saved in state.extractions
        ],
        "result_history": [
            r.model_dump(mode="json", exclude={"session_id"}) for r in state.results],
    }


def create_incident_test_app(
    guest: GuestService, evidence: EvidenceService, actions: ActionService,
    policy: IncidentHTTPPolicy,
):
    """Explicit adapter-test factory. Atomic new-record provisioning is required
    from the injected adapters; this factory never manufactures missing history.
    """
    if guest is None or evidence is None or actions is None or policy is None \
            or evidence.guest is not guest or actions.evidence is not evidence \
            or actions.guest is not guest:
        raise ValueError("one consistent explicitly injected service graph is required")
    if policy.read_deadline_seconds >= guest.policy.retail.session_seconds:
        raise ValueError("command read deadline must fit guest access")
    app = create_guest_test_app(guest)
    app.title = "BatchBeacon incident adapter test"
    app.state.incident_http_policy_hash = policy.digest()

    @app.exception_handler(GuestDenied)
    async def denied(request, exc):
        body = {"error": exc.code}
        if exc.status == 503 and request.method == "POST" \
                and request.url.path.endswith(("/actions", "/corrections")):
            body["outcome"] = "unknown"
        return JSONResponse(body, status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse({"error": "invalid_request"}, status_code=422)

    def owned(request, incident_id, *, mutation=False):
        token = request.cookies.get(guest.policy.cookie_name)
        guest.resolve(token)  # Bearer comes only from the configured HttpOnly cookie.
        if mutation:
            guest.guard(request.headers.get("origin"), token, request.headers.get("x-csrf-token"))
        try:
            TypeAdapter(OpaqueId).validate_python(incident_id)
        except ValidationError as exc:
            raise GuestDenied(422, "invalid_incident_id") from exc
        guest.incident(token, incident_id)  # Always precedes command-body parsing.
        return token

    def operation(request):
        try:
            return TypeAdapter(RequestKey).validate_python(request.headers.get("idempotency-key"))
        except ValidationError as exc:
            raise GuestDenied(422, "request_key_required") from exc

    @app.get("/api/incidents/{incident_id}/evidence")
    async def read_evidence(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id)
        query = _queries(request, {"revision"})
        revision = _revision(query["revision"]) if "revision" in query else None
        await _no_body(request, policy)
        view = await run_in_threadpool(evidence.read_evidence, token, incident_id, revision)
        return _evidence_view(view)

    @app.post("/api/incidents/{incident_id}/corrections")
    async def correct(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id, mutation=True)
        key = operation(request)
        _queries(request, set())
        command = await _command(request, CorrectionCommand, policy)
        receipt = await run_in_threadpool(evidence.correct, token, incident_id, key,
                                          command.expected_revision, command.field,
                                          command.replacement)
        view = await run_in_threadpool(evidence.read_evidence, token, incident_id)
        return {"observation_revision": receipt.revision,
                "latest_observation_revision": len(view.state.observations),
                "current": view.current, "hold_eligible": view.hold_eligible,
                "reverification_required": not view.current}

    # Literal paths precede action IDs so they cannot be interpreted as guessed IDs.
    @app.get("/api/incidents/{incident_id}/actions/prepare")
    async def prepare(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id)
        kind = _action_type(_queries(request, {"action_type"}).get("action_type"))
        await _no_body(request, policy)
        target = await run_in_threadpool(actions.prepare, token, incident_id, kind)
        return {"target": target.model_dump(mode="json"), "confirmation_required": True}

    @app.post("/api/incidents/{incident_id}/actions")
    async def confirm(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id, mutation=True)
        key = operation(request)
        _queries(request, set())
        command = await _command(request, ActionConfirmation, policy)
        view = await run_in_threadpool(actions.confirm, token, incident_id, key, command)
        return _action_view(view)

    @app.get("/api/incidents/{incident_id}/actions")
    async def history(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id)
        _queries(request, set())
        await _no_body(request, policy)
        views = await run_in_threadpool(actions.list_actions, token, incident_id)
        return {"actions": [_action_view(v) for v in views]}

    @app.get("/api/incidents/{incident_id}/actions/reconcile")
    async def reconcile(incident_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id)
        query = _queries(request, {"result_revision", "action_type"})
        revision = _revision(query.get("result_revision"))
        kind = _action_type(query.get("action_type"))
        await _no_body(request, policy)
        view = await run_in_threadpool(actions.reconcile, token, incident_id, revision, kind)
        return {"found": view is not None, "record": _action_view(view) if view else None}

    @app.get("/api/incidents/{incident_id}/actions/{action_id}")
    async def action(incident_id: str, action_id: str, request: Request):
        token = await run_in_threadpool(owned, request, incident_id)
        _queries(request, set())
        await _no_body(request, policy)
        try:
            TypeAdapter(OpaqueId).validate_python(action_id)
        except ValidationError as exc:
            raise GuestDenied(422, "invalid_action_id") from exc
        view = await run_in_threadpool(actions.get_action, token, incident_id, action_id)
        return _action_view(view)

    return app

"""Owned guidance HTTP surface; clients cannot submit evaluation results or policies."""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field, TypeAdapter, ValidationError
from starlette.concurrency import run_in_threadpool

from batchbeacon.contracts import Record
from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey
from batchbeacon.incident_api import _command, _no_body, _queries
from batchbeacon.learning_service import ActivationConfirmation, RollbackConfirmation
from batchbeacon.retail_contracts import FeedbackDetail


class FeedbackCommand(Record):
    detail: FeedbackDetail
    request_id: OpaqueId | None = None


class CandidateCommand(Record):
    feedback_ids: tuple[OpaqueId, ...] = Field(min_length=1, max_length=5)


def public_record(record):
    return record.model_dump(
        mode="json",
        exclude={
            "scope",
            "effective_policy_hash",
            "actor_session",
            "lease",
            "initiating_key",
            "request_key",
            "payload_hash",
            "configuration_hash",
            "evaluator_hash",
            "capacity",
            "usage_hash",
            "evidence_hash",
        },
    )


def mount_learning_api(app, service, policy):
    guest = service.guest
    prior = app.exception_handlers[GuestDenied]

    @app.exception_handler(GuestDenied)
    async def denied(request, error):
        if (
            request.method == "POST"
            and (
                "/learning/" in request.url.path
                or request.url.path.endswith(("/guidance", "/feedback"))
            )
            and error.status >= 500
        ):
            return JSONResponse(
                {"error": error.code, "outcome": "unknown", "recovery": "original_request_key"},
                status_code=error.status,
            )
        return await prior(request, error)

    def identifier(value):
        try:
            return TypeAdapter(OpaqueId).validate_python(value)
        except ValidationError:
            raise GuestDenied(422, "invalid_learning_id") from None

    def owned(request, mutation=False):
        cookies = request.headers.getlist("cookie")
        occurrences = sum(
            part.partition("=")[0].strip() == guest.policy.cookie_name
            for header in cookies
            for part in header.split(";")
        )
        if len(cookies) != 1 or occurrences != 1:
            raise GuestDenied(401, "guest_expired_or_invalid")
        token = request.cookies.get(guest.policy.cookie_name)
        session = guest.resolve(token)
        key = None
        if mutation:
            if any(
                len(request.headers.getlist(name)) != 1
                for name in ("origin", "x-csrf-token", "idempotency-key")
            ):
                raise GuestDenied(403, "mutation_guard_required")
            guest.guard(request.headers.get("origin"), token, request.headers.get("x-csrf-token"))
            try:
                key = TypeAdapter(RequestKey).validate_python(request.headers["idempotency-key"])
            except ValidationError:
                raise GuestDenied(422, "request_key_required") from None
        return token, session, key

    def response(record, token, session):
        guest._live(session, guest._key(token))
        return public_record(record)

    def snapshot(state, context):
        return {
            "context": context,
            "active": state.active.model_dump(mode="json"),
            "observed_at": guest._now().isoformat(),
            "requests": [public_record(x) for x in state.requests],
            "feedback": [public_record(x) for x in state.feedback],
            "candidates": [public_record(x) for x in state.candidates],
            "evaluations": [public_record(x) for x in state.evaluations],
            "transitions": [public_record(x) for x in state.transitions],
            "limits": {
                "feedback": guest.policy.retail.max_feedback,
                "candidates": guest.policy.retail.max_candidates,
                "evaluations": guest.policy.retail.max_evaluations,
                "forward_activations": guest.policy.retail.max_forward_activations,
            },
        }

    def selection(request, token, default=None):
        query = _queries(request, {"incident"})
        incident = identifier(query["incident"]) if "incident" in query else default
        if default is not None and incident != default:
            raise GuestDenied(422, "invalid_learning_context")
        if incident is not None:
            guest.incident(token, incident)
        return incident

    def mutation_response(record, token, session, incident):
        result = response(record, token, session)
        state, context = service.presentation(token, incident)
        result["learning_state"] = snapshot(state, context)
        guest._live(session, guest._key(token))
        return result

    @app.get("/api/learning")
    async def read(request: Request):
        _queries(request, {"incident"})
        await _no_body(request, policy)
        token, session, _ = await run_in_threadpool(owned, request)
        try:
            if len(request.headers.getlist("idempotency-key")) != 1:
                raise ValueError("one refresh key required")
            key = TypeAdapter(RequestKey).validate_python(request.headers["idempotency-key"])
        except (ValueError, ValidationError):
            raise GuestDenied(422, "request_key_required") from None
        incident = await run_in_threadpool(selection, request, token)
        state, context = await run_in_threadpool(
            service.refresh, token, key, incident=incident, with_context=True
        )
        guest._live(session, guest._key(token))
        return snapshot(state, context)

    @app.post("/api/incidents/{incident_id}/guidance")
    async def guidance(incident_id: str, request: Request):
        identifier(incident_id)
        _queries(request, {"incident"})
        await _no_body(request, policy)
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, incident_id)
        result = await run_in_threadpool(service.guidance, token, incident_id, key)
        return await run_in_threadpool(mutation_response, result, token, session, incident)

    @app.post("/api/incidents/{incident_id}/feedback")
    async def feedback(incident_id: str, request: Request):
        identifier(incident_id)
        _queries(request, {"incident"})
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, incident_id)
        command = await _command(request, FeedbackCommand, policy)
        result = await run_in_threadpool(
            service.feedback, token, incident_id, key, command.detail, command.request_id
        )
        return await run_in_threadpool(mutation_response, result, token, session, incident)

    @app.post("/api/learning/candidates")
    async def candidate(request: Request):
        _queries(request, {"incident"})
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, None)
        command = await _command(request, CandidateCommand, policy)
        result = await run_in_threadpool(service.candidate, token, key, command.feedback_ids)
        return await run_in_threadpool(mutation_response, result, token, session, incident)

    @app.post("/api/learning/candidates/{candidate_id}/evaluations")
    async def evaluate(candidate_id: str, request: Request):
        identifier(candidate_id)
        _queries(request, {"incident"})
        await _no_body(request, policy)
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, None)
        result = await run_in_threadpool(service.evaluate, token, key, candidate_id)
        return await run_in_threadpool(mutation_response, result, token, session, incident)

    @app.get("/api/learning/activation/prepare")
    async def prepare_activation(request: Request):
        query = _queries(request, {"evaluation"})
        evaluation = identifier(query.get("evaluation"))
        await _no_body(request, policy)
        token, session, _ = await run_in_threadpool(owned, request)
        result = await run_in_threadpool(service.prepare_activation, token, evaluation)
        return response(result, token, session)

    @app.post("/api/learning/activation")
    async def activate(request: Request):
        _queries(request, {"incident"})
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, None)
        command = await _command(request, ActivationConfirmation, policy)
        result = await run_in_threadpool(service.activate, token, key, command)
        return await run_in_threadpool(mutation_response, result, token, session, incident)

    @app.get("/api/learning/rollback/prepare")
    async def prepare_rollback(request: Request):
        _queries(request, set())
        await _no_body(request, policy)
        token, session, _ = await run_in_threadpool(owned, request)
        result = await run_in_threadpool(service.prepare_rollback, token)
        return response(result, token, session)

    @app.post("/api/learning/rollback")
    async def rollback(request: Request):
        _queries(request, {"incident"})
        token, session, key = await run_in_threadpool(owned, request, True)
        incident = await run_in_threadpool(selection, request, token, None)
        command = await _command(request, RollbackConfirmation, policy)
        result = await run_in_threadpool(service.rollback, token, key, command)
        return await run_in_threadpool(mutation_response, result, token, session, incident)

"""Owned manual retail refresh over explicitly injected server persistence."""

from fastapi import Request
from pydantic import TypeAdapter, ValidationError
from starlette.concurrency import run_in_threadpool

from batchbeacon.guest_service import GuestDenied, RequestKey
from batchbeacon.incident_api import IncidentHTTPPolicy, _no_body, _queries
from batchbeacon.retail_projection import QueueFilter
from batchbeacon.retail_refresh import RetailRefresh


def mount_retail_api(app, refresh: RetailRefresh, policy: IncidentHTTPPolicy):
    if refresh is None or policy is None:
        raise ValueError("explicit refresh admission and HTTP policy required")
    guest = refresh.guest
    app.state.retail_refresh_policy_hash = refresh.policy.digest()

    @app.get("/api/retail/queue")
    async def queue(request: Request):
        cookies = request.headers.getlist("cookie")
        occurrences = sum(part.partition("=")[0].strip() == guest.policy.cookie_name
                          for header in cookies for part in header.split(";"))
        if len(cookies) != 1 or occurrences != 1:
            raise GuestDenied(401, "guest_expired_or_invalid")
        token = request.cookies.get(guest.policy.cookie_name)
        # Parse the opaque capability locally; authoritative ownership/expiry is
        # checked inside the admission transaction, without another store resolve.
        guest._key(token)
        query = _queries(request, {"filter"})
        keys = request.headers.getlist("idempotency-key")
        try:
            selected = QueueFilter(query.get("filter", QueueFilter.ALL))
            if len(keys) != 1:
                raise ValueError("one request key required")
            operation = TypeAdapter(RequestKey).validate_python(keys[0])
        except (ValueError, ValidationError):
            raise GuestDenied(422, "invalid_refresh_request") from None
        await _no_body(request, policy)
        result = await run_in_threadpool(refresh.read, token, operation, selected_filter=selected)
        # Admission/release may take time after the queue read. Scope is immutable.
        payload = result.model_dump(mode="json", exclude={
            "snapshot": {"scope": True, "effective_policy_hash": True},
            "read_policy_hash": True, "context_binding_hash": True})
        payload["shop_label"] = "Synthetic demo shop"
        if guest._now() >= result.snapshot.scope.expires_at:
            raise GuestDenied(401, "guest_expired_or_invalid")
        return payload

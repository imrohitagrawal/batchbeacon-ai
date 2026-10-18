"""Persistent manual refresh admission, separate from the read-only queue.

Claim and release each transact guest/usage/admission (three document reads).
Only admission metadata changes; domain counters and model budgets are untouched.
"""

from datetime import timedelta
from typing import Annotated, Self
from uuid import uuid4

from pydantic import AwareDatetime, Field, TypeAdapter, model_validator

from batchbeacon.contracts import Digest, Record
from batchbeacon.evidence_service import replace
from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey


class RefreshPolicy(Record):
    minimum_interval_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 2.0
    lease_seconds: Annotated[float, Field(gt=0, allow_inf_nan=False)] = 20.0
    max_session_refreshes: Annotated[int, Field(gt=0)] = 40


class RefreshState(Record):
    session_id: OpaqueId
    policy_hash: Digest
    expires_at: AwareDatetime
    count: Annotated[int, Field(ge=1)]
    last_request_key: RequestKey
    next_allowed_at: AwareDatetime
    lease_id: OpaqueId | None
    lease_until: AwareDatetime | None

    @model_validator(mode="after")
    def lease_pair(self) -> Self:
        if (self.lease_id is None) != (self.lease_until is None):
            raise ValueError("refresh lease requires identity and deadline")
        if self.lease_until is not None and self.lease_until > self.expires_at:
            raise ValueError("refresh lease cannot extend session")
        return self


class RetailRefresh:
    def __init__(self, retail, policy: RefreshPolicy):
        if retail is None or policy is None or retail.store.retail is not retail:
            raise ValueError("explicit enrolled retail store required")
        if not retail.store.policy.operation_seconds <= policy.lease_seconds < \
                retail.projector.guest.policy.retail.session_seconds:
            raise ValueError("refresh lease must cover operation and fit session")
        self.retail, self.policy = retail, policy
        self.store, self.guest = retail.store, retail.projector.guest

    def _snapshot(self, tx, key):
        s = self.store
        guest, _ = s._guest(tx, key)
        self.guest._live(guest, key)
        tx.limit_to(guest.scope.expires_at)
        name = s.name("refresh", key)
        state = tx.read({name: "refresh"})[name]
        if state is not None and (state.session_id != guest.scope.session_id
                or state.policy_hash != self.policy.digest()
                or state.expires_at != guest.scope.expires_at
                or state.count > self.policy.max_session_refreshes):
            raise GuestDenied(503, "refresh_admission_unavailable")
        return guest, name, state

    def claim(self, capability, request_key):
        request_key = TypeAdapter(RequestKey).validate_python(request_key)
        key, lease_id = self.guest._key(capability), uuid4().hex

        def claim(tx):
            guest, name, state = self._snapshot(tx, key)
            now = self.guest._now()
            if state is not None:
                if state.last_request_key == request_key:
                    raise GuestDenied(409, "refresh_request_already_admitted")
                if state.lease_until is not None and now < state.lease_until:
                    raise GuestDenied(429, "refresh_in_progress")
                if now < state.next_allowed_at:
                    raise GuestDenied(429, "refresh_rate_limited")
                if state.count >= self.policy.max_session_refreshes:
                    raise GuestDenied(429, "refresh_allowance_exhausted")
            result = RefreshState(session_id=guest.scope.session_id,
                policy_hash=self.policy.digest(), expires_at=guest.scope.expires_at,
                count=state.count + 1 if state else 1, last_request_key=request_key,
                next_allowed_at=now + timedelta(seconds=self.policy.minimum_interval_seconds),
                lease_id=lease_id, lease_until=min(guest.scope.expires_at,
                    now + timedelta(seconds=self.policy.lease_seconds)))
            tx.write(name, "refresh", result, create=state is None)
            return result

        lease = self.guest._storage(self.store.run, claim)
        if self.guest._now() >= lease.lease_until:
            raise GuestDenied(429, "refresh_lease_elapsed")
        return lease

    def release(self, capability, lease):
        key = self.guest._key(capability)

        def release(tx):
            _, name, state = self._snapshot(tx, key)
            if state is None or state.lease_id != lease.lease_id \
                    or state.last_request_key != lease.last_request_key:
                raise GuestDenied(409, "refresh_lease_changed")
            tx.write(name, "refresh", replace(state, lease_id=None, lease_until=None))
        self.guest._storage(self.store.run, release)

    def read(self, capability, request_key, *, selected_filter):
        # This complete synchronous operation stays in its worker even if the
        # HTTP requester disconnects. A slot is never released by task cancellation.
        lease = self.claim(capability, request_key)
        try:
            return self.retail.read(capability, selected_filter=selected_filter,
                                    not_after=lease.lease_until)
        finally:
            self.release(capability, lease)

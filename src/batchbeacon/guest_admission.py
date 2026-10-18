"""Rate-limited guest provisioning; independent of paid model allowances."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, model_validator

from batchbeacon.contracts import Digest, Record
from batchbeacon.guest_service import GuestDenied


class GuestAdmissionPolicy(Record):
    version: Literal["guest-admission-1"] = "guest-admission-1"
    # Required explicit choice: null removes only the lifetime issuance ceiling.
    # Omitting the setting must never silently enable uncapped admission.
    max_issued_sessions: Annotated[int, Field(gt=0)] | None
    max_sessions_per_window: Annotated[int, Field(gt=0)]
    window_seconds: Annotated[int, Field(gt=0)]
    not_before: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def coherent(self):
        if any(t.tzinfo is None or t.utcoffset() is None
               for t in (self.not_before, self.expires_at)):
            raise ValueError("guest admission requires aware timestamps")
        if (self.expires_at <= self.not_before
                or (self.max_issued_sessions is not None
                    and self.max_sessions_per_window > self.max_issued_sessions)
                or self.window_seconds > (self.expires_at - self.not_before).total_seconds()):
            raise ValueError("guest admission bounds disagree")
        return self


class GuestAdmissionState(Record):
    policy_hash: Digest
    issued_sessions: Annotated[int, Field(ge=0)]
    window_started_at: datetime
    window_issued: Annotated[int, Field(ge=0)]

    @model_validator(mode="after")
    def coherent(self):
        if self.window_started_at.tzinfo is None or self.window_started_at.utcoffset() is None:
            raise ValueError("guest admission requires an aware window")
        if self.window_issued > self.issued_sessions:
            raise ValueError("window exceeds lifetime issuance")
        return self


def reserve_guest(policy: GuestAdmissionPolicy, state: GuestAdmissionState | None,
                  now: datetime) -> GuestAdmissionState:
    if (state is None or state.policy_hash != policy.digest()
            or not policy.not_before <= state.window_started_at <= now < policy.expires_at
            or (policy.max_issued_sessions is not None
                and state.issued_sessions >= policy.max_issued_sessions)
            or state.window_issued > policy.max_sessions_per_window):
        raise GuestDenied(429, "demo_guest_capacity_unavailable")
    elapsed = (now - state.window_started_at).total_seconds()
    window_start = now if elapsed >= policy.window_seconds else state.window_started_at
    window_issued = 0 if elapsed >= policy.window_seconds else state.window_issued
    if window_issued >= policy.max_sessions_per_window:
        raise GuestDenied(429, "guest_creation_rate_limited")
    return GuestAdmissionState(policy_hash=state.policy_hash,
        issued_sessions=state.issued_sessions + 1, window_started_at=window_start,
        window_issued=window_issued + 1)

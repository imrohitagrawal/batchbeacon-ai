"""Nonsecret T08 model-probe policy. Configuration never grants cloud authority."""

from datetime import date, datetime
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from google.adk.agents.run_config import RunConfig
from google.genai import types
from pydantic import AwareDatetime, Field, model_validator

from batchbeacon.contracts import Digest, Nonempty, Record

Positive = Annotated[int, Field(gt=0)]
SingleAttempt = Annotated[int, Field(ge=1, le=1)]
# SQLite INTEGER is signed 64-bit. Monetary values are integer nanorupees.
Money = Annotated[int, Field(ge=0, le=2**63 - 1)]
PositiveMoney = Annotated[int, Field(gt=0, le=2**63 - 1)]
ProjectId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")]


class ModelPrice(Record):
    currency: Literal["INR"]
    input_nanos_per_million: PositiveMoney
    output_nanos_per_million: PositiveMoney
    evidence_sha256: Digest
    observed_at: AwareDatetime
    valid_until: AwareDatetime

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.valid_until <= self.observed_at:
            raise ValueError("price validity must follow observation")
        return self

    def cost_nanos(self, input_tokens: int, output_tokens: int) -> int:
        if any(type(v) is not int or v < 0 for v in (input_tokens, output_tokens)):
            raise ValueError("usage requires nonnegative integer token counts")
        numerator = (input_tokens * self.input_nanos_per_million
                     + output_tokens * self.output_nanos_per_million)
        return (numerator + 999_999) // 1_000_000


class ModelProbePolicy(Record):
    """Exactly one paid attempt per reservation; retries require new admission.

    The single-attempt/single-call restriction is this operator adapter's protocol,
    not a general application limit. T10's multi-call workflow needs admission at
    every call. Other limits are validated effective operation configuration.
    """

    version: Nonempty = "operator-probe-v1"
    project_id: ProjectId
    model_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9.-]+$")]
    model_location: Nonempty
    api_version: Nonempty
    thinking_level: Literal["LOW", "MEDIUM", "HIGH"]
    price: ModelPrice
    request_timeout_ms: Positive = 30_000
    run_deadline_ms: Positive = 30_000
    max_input_tokens: Positive = 12_000
    max_output_tokens: Positive = 4_096
    billable_output_token_bound: Positive
    billing_bound_evidence_sha256: Digest
    candidate_count: SingleAttempt = 1
    sdk_attempts: SingleAttempt = 1
    max_llm_calls: SingleAttempt = 1
    automatic_continuation: bool = False
    reserve_nanos: PositiveMoney
    max_daily_attempts: Positive = 1
    max_total_attempts: Positive = 22
    calendar_timezone: Nonempty = "Asia/Kolkata"
    ledger_lock_timeout_ms: Positive = 5_000

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.automatic_continuation:
            raise ValueError("a continuation requires separate paid admission")
        if self.request_timeout_ms > self.run_deadline_ms:
            raise ValueError("HTTP timeout must fit inside the outer run deadline")
        if self.billable_output_token_bound < self.max_output_tokens:
            raise ValueError("billable bound must cover response and reasoning")
        if self.reserve_nanos < self.price.cost_nanos(
            self.max_input_tokens, self.billable_output_token_bound
        ):
            raise ValueError("reservation is below the gross token cost bound")
        if self.max_daily_attempts > self.max_total_attempts:
            raise ValueError("daily attempts cannot exceed total attempts")
        try:
            ZoneInfo(self.calendar_timezone)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError("unknown budget calendar timezone") from error
        return self

    def http_options(self) -> types.HttpOptions:
        return types.HttpOptions(
            api_version=self.api_version,
            timeout=self.request_timeout_ms,
            retry_options=types.HttpRetryOptions(attempts=self.sdk_attempts),
        )

    def client_options(self) -> dict:
        return {
            "vertexai": True, "project": self.project_id, "location": self.model_location,
            "http_options": self.http_options(),
        }

    def run_config(self) -> RunConfig:
        return RunConfig(max_llm_calls=self.max_llm_calls, http_options=self.http_options())

    def generation_config(self) -> types.GenerateContentConfig:
        return types.GenerateContentConfig(
            http_options=self.http_options(),
            candidate_count=self.candidate_count,
            max_output_tokens=self.max_output_tokens,
            thinking_config=types.ThinkingConfig(thinking_level=self.thinking_level),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            automatic_continuation=self.automatic_continuation,
            response_modalities=[types.Modality.TEXT],
        )


class ProbeGrant(Record):
    """Operator-reviewed allocation, supplied separately from runtime settings.

    Evidence hashes identify real external review; constructing this record cannot
    substantiate its evidence. No public API accepts grants or creates ledgers.
    """

    project_id: ProjectId
    policy_sha256: Digest
    pool: Literal["model_probes"]
    currency: Literal["INR"]
    allocation_nanos: PositiveMoney
    not_before: AwareDatetime
    expires_at: AwareDatetime
    authority_evidence_sha256: Digest
    global_capacity_evidence_sha256: Digest

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.expires_at <= self.not_before:
            raise ValueError("grant expiry must follow its start")
        return self


class PriorAttemptDay(Record):
    day: date
    attempts: Positive


class OpeningLiabilities(Record):
    """Upper bounds for spend/unknown outcomes before this ledger's first entry."""

    incurred_nanos: Money | None
    outstanding_nanos: Money | None
    evidence_sha256: Digest | None
    prior_attempt_days: tuple[PriorAttemptDay, ...] | None

    @model_validator(mode="after")
    def unique_days(self) -> Self:
        if self.prior_attempt_days is not None:
            days = [entry.day for entry in self.prior_attempt_days]
            if len(days) != len(set(days)):
                raise ValueError("prior attempt days must be unique")
        return self

    def substantiated_total(self) -> int:
        if (self.incurred_nanos is None or self.outstanding_nanos is None
                or self.evidence_sha256 is None or self.prior_attempt_days is None):
            raise ValueError("unknown prior liabilities cannot initialize paid admission")
        return self.incurred_nanos + self.outstanding_nanos


def validate_admission(policy: ModelProbePolicy, grant: ProbeGrant, now: datetime) -> None:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("admission clock must include a timezone")
    if policy.digest() != grant.policy_sha256 or policy.project_id != grant.project_id:
        raise ValueError("effective policy does not match the reviewed allocation")
    if not grant.not_before <= now < grant.expires_at:
        raise ValueError("paid allocation is not active")
    if not policy.price.observed_at <= now < policy.price.valid_until:
        raise ValueError("verified price is not current")

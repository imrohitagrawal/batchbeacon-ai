"""Private immutable HTTP evidence and strict usage derivation; no network I/O."""

import base64
import json
from hashlib import sha256
from typing import Annotated, Self

from pydantic import AwareDatetime, Field, model_validator

from batchbeacon.contracts import Digest, Record

Positive = Annotated[int, Field(gt=0)]
Count = Annotated[int, Field(ge=0)]


class AttemptEvidenceLimits(Record):
    max_response_bytes: Positive = 262144
    max_attempt_record_bytes: Positive = 524288
    max_run_binding_bytes: Positive = 16384
    max_json_depth: Positive = 32

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if 4 * ((self.max_response_bytes + 2) // 3) >= self.max_attempt_record_bytes:
            raise ValueError("encoded response must fit the attempt record limit")
        return self


class ResponseEvidence(Record):
    status_code: Annotated[int, Field(ge=100, le=599)]
    complete: bool
    retained_bytes: Count
    observed_bytes: Count
    retained_sha256: Digest
    body_base64: str = Field(repr=False)

    @model_validator(mode="after")
    def coherent(self) -> Self:
        raw = base64.b64decode(self.body_base64, validate=True)
        if base64.b64encode(raw).decode() != self.body_base64 \
                or len(raw) != self.retained_bytes \
                or sha256(raw).hexdigest() != self.retained_sha256 \
                or self.observed_bytes < self.retained_bytes \
                or (self.complete and self.observed_bytes != self.retained_bytes):
            raise ValueError("response evidence inconsistent")
        return self

    def original(self) -> bytes:
        return base64.b64decode(self.body_base64, validate=True)


class CompleteUsage(Record):
    request_hash: Digest
    response_hash: Digest
    input_tokens: Count
    candidate_tokens: Count
    thought_tokens: Count
    total_tokens: Count
    metadata_json: str = Field(repr=False)

    @property
    def output_and_thought_tokens(self):
        return self.candidate_tokens + self.thought_tokens


def response_evidence(raw: bytes, *, status_code: int, complete: bool,
                      observed_bytes: int, limits: AttemptEvidenceLimits) -> ResponseEvidence:
    """Retain a labelled prefix on overflow; observed bytes are not a total length."""
    try:
        if type(raw) is not bytes or type(complete) is not bool \
                or type(observed_bytes) is not int or observed_bytes < len(raw) \
                or (complete and observed_bytes != len(raw)):
            raise ValueError("invalid response observation")
        retained = raw[:limits.max_response_bytes]
        return ResponseEvidence(status_code=status_code,
            complete=complete and len(retained) == len(raw), retained_bytes=len(retained),
            observed_bytes=observed_bytes, retained_sha256=sha256(retained).hexdigest(),
            body_base64=base64.b64encode(retained).decode())
    except (ValueError, TypeError):
        pass
    raise ValueError("response evidence invalid")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _depth(value, remaining):
    if remaining < 0:
        raise ValueError("JSON nesting exceeds policy")
    if isinstance(value, dict):
        for child in value.values():
            _depth(child, remaining - 1)
    elif isinstance(value, list):
        for child in value:
            _depth(child, remaining - 1)


def derive_usage(response: ResponseEvidence, request_hash: str,
                 limits: AttemptEvidenceLimits) -> CompleteUsage:
    """Only complete 2xx evidence can reduce a reservation. Failure stays unknown."""
    try:
        if not response.complete or not 200 <= response.status_code < 300:
            raise ValueError("response incomplete or not successful")
        body = json.loads(response.original().decode("utf-8"), object_pairs_hook=_unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        _depth(body, limits.max_json_depth)
        usage = body["usageMetadata"]
        required = ("promptTokenCount", "candidatesTokenCount", "thoughtsTokenCount",
                    "totalTokenCount")
        optional_counts = ("cachedContentTokenCount", "toolUsePromptTokenCount")
        details = {"promptTokensDetails": "promptTokenCount",
                   "candidatesTokensDetails": "candidatesTokenCount",
                   "cacheTokensDetails": "cachedContentTokenCount",
                   "toolUsePromptTokensDetails": "toolUsePromptTokenCount"}
        if type(usage) is not dict or set(usage) - set(required + optional_counts) \
                - set(details) - {"trafficType"}:
            raise ValueError("unknown usage fields")
        # Vertex uses implicit-presence proto3 int32 for thoughts_token_count.
        # Its zero default may be omitted. An unexplained total never infers
        # nonzero thoughts or reduces an unknown reservation.
        counts = [usage.get(k, 0) if k == "thoughtsTokenCount" else usage[k]
                  for k in required]
        if any(type(n) is not int or n < 0 for n in counts) or counts[3] != sum(counts[:3]):
            raise ValueError("incomplete usage")
        for name in optional_counts:
            if name in usage and (type(usage[name]) is not int or usage[name] != 0):
                raise ValueError("unsupported billing mode")
        for detail, total in details.items():
            if detail not in usage:
                continue
            rows = usage[detail]
            if type(rows) is not list or any(type(row) is not dict
                    or set(row) != {"modality", "tokenCount"}
                    or row["modality"] not in {"TEXT", "IMAGE"}
                    or type(row["tokenCount"]) is not int or row["tokenCount"] < 0
                    for row in rows) or len({row["modality"] for row in rows}) != len(rows) \
                    or sum(row["tokenCount"] for row in rows) != usage.get(total, 0):
                raise ValueError("usage detail mismatch")
        if "trafficType" in usage and usage["trafficType"] != "ON_DEMAND":
            raise ValueError("unsupported traffic type")
        return CompleteUsage(request_hash=request_hash, response_hash=response.retained_sha256,
            input_tokens=counts[0], candidate_tokens=counts[1], thought_tokens=counts[2],
            total_tokens=counts[3], metadata_json=json.dumps(usage, sort_keys=True,
                                                           separators=(",", ":")))
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError, OverflowError):
        pass
    raise ValueError("complete usage unavailable")


def candidate_text(parts) -> str:
    """Return visible text only; retain opaque signature solely in original bytes."""
    if type(parts) is not list or not parts:
        raise ValueError("unexpected response parts")
    for part in parts:
        if type(part) is not dict or set(part) - {"text", "thoughtSignature"} \
                or type(part.get("text")) is not str:
            raise ValueError("unexpected response parts")
        if "thoughtSignature" in part:
            signature = part["thoughtSignature"]
            if type(signature) is not str or not signature:
                raise ValueError("invalid thought signature")
            decoded = base64.b64decode(signature, validate=True)
            if base64.b64encode(decoded).decode() != signature:
                raise ValueError("invalid thought signature")
    return "".join(part["text"] for part in parts)


class NonbillablePolicy(Record):
    """Operator-reviewed provider rule; never inferred from an absent response."""

    model_id: str = Field(min_length=1, max_length=100)
    model_configuration_hash: Digest
    endpoint: str = Field(
        pattern=r"^https://[a-z0-9.-]+/v[0-9]+(?:beta[0-9]+)?/projects/[a-z0-9-]+/locations/[a-z0-9-]+/publishers/google/models/[a-z0-9.-]+:generateContent$"
    )
    source_url: str = Field(
        pattern=r"^https://cloud\.google\.com/gemini-enterprise-agent-platform/generative-ai/pricing$"
    )
    source_sha256: Digest
    applicability_evidence_sha256: Digest
    effective_from: AwareDatetime
    observed_at: AwareDatetime
    valid_until: AwareDatetime
    statuses: tuple[Annotated[int, Field(ge=400, le=599)], ...] = Field(min_length=1)

    @model_validator(mode="after")
    def coherent(self):
        if (
            not self.effective_from <= self.observed_at < self.valid_until
            or len(set(self.statuses)) != len(self.statuses)
            or not self.endpoint.endswith("/" + self.model_id + ":generateContent")
        ):
            raise ValueError("nonbillable policy inconsistent")
        return self


class NonbillableReceipt(Record):
    """Zero model charge under a reviewed error rule, not fabricated token usage."""

    attempt_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    request_hash: Digest
    response_hash: Digest
    policy: NonbillablePolicy
    settled_at: AwareDatetime

    def validate_response(self, response, *, attempt_id, request_hash, model_hash, reserved_at):
        if (
            self.attempt_id != attempt_id
            or self.request_hash != request_hash
            or self.response_hash != response.retained_sha256
            or self.policy.model_configuration_hash != model_hash
            or not self.policy.effective_from <= reserved_at <= self.settled_at
            or not self.policy.observed_at <= self.settled_at < self.policy.valid_until
            or not response.complete
            or response.status_code not in self.policy.statuses
        ):
            raise ValueError("nonbillable receipt binding invalid")
        body = json.loads(
            response.original().decode("utf-8"),
            object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()),
        )
        # A retained provider error must not also contain a successful candidate/usage.
        if (
            type(body) is not dict
            or set(body) != {"error"}
            or type(body["error"]) is not dict
            or type(body["error"].get("code")) is not int
            or body["error"]["code"] != response.status_code
            or not isinstance(body["error"].get("status"), str)
        ):
            raise ValueError("nonbillable provider error invalid")

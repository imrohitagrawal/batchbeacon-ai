"""Retail/learning records and policy validation, not HTTP or database authority.

T09/T34/T35 must obtain server scope and authoritative evidence transactionally.
No record here is a capability, signed evaluation receipt or source approval.
"""

import json
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import Field, computed_field, model_validator

from batchbeacon.contracts import (
    ActionType,
    Digest,
    Nonempty,
    Record,
    Revision,
    SourceDependency,
    SourceMode,
    Verdict,
)
from batchbeacon.guidance_policies import (
    POLICIES,
    GuidanceField,
    GuidancePolicyId,
    GuidanceText,
    wording_for,
)

Positive = Annotated[int, Field(gt=0)]
Count = Annotated[int, Field(ge=0)]
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")]


def _aware(*times: datetime) -> None:
    if any(stamp.tzinfo is None or stamp.utcoffset() is None for stamp in times):
        raise ValueError("timestamps require an explicit timezone")


def _unique(values: tuple) -> None:
    if len(values) != len(set(values)):
        raise ValueError("duplicate references are not allowed")


class RetailPolicy(Record):
    """Nonsecret effective configuration; changes are not an authorization grant."""

    version: Identifier = "retail-policy-1"
    session_seconds: Positive = 8 * 60 * 60
    max_incidents: Positive = 20
    max_summary_rows: Positive = 20
    max_feedback: Positive = 40
    max_candidates: Positive = 2
    max_support_refs: Positive = 5
    max_evaluations: Positive = 4
    max_active_evaluations: Positive = 1
    evaluation_deadline_seconds: Positive = 30
    max_forward_activations: Positive = 2
    max_transitions: Positive = 4
    record_bytes: Positive = 8 * 1024
    evaluation_bytes: Positive = 16 * 1024
    max_instruction_chars: Positive = 240
    automatic_refresh: bool = False
    minimum_poll_seconds: Positive = 30
    poll_seconds: Positive = 30

    @model_validator(mode="after")
    def coherent_bounds(self) -> Self:
        if self.max_summary_rows > self.max_incidents:
            raise ValueError("summary rows cannot exceed the incident limit")
        if self.max_active_evaluations > self.max_evaluations:
            raise ValueError("active evaluation limit exceeds lifetime allowance")
        if self.max_transitions < 2 * self.max_forward_activations:
            raise ValueError("reserve a rollback transition for each activation")
        if self.poll_seconds < self.minimum_poll_seconds:
            raise ValueError("poll interval is below its effective floor")
        if self.evaluation_deadline_seconds >= self.session_seconds:
            raise ValueError("evaluation deadline must fit within session lifetime")
        return self


class ShopScope(Record):
    session_id: Identifier
    shop_id: Identifier
    issued_at: datetime
    expires_at: datetime

    @model_validator(mode="after")
    def valid_scope(self) -> Self:
        _aware(self.issued_at, self.expires_at)
        if self.expires_at <= self.issued_at:
            raise ValueError("scope expiry must follow issuance")
        return self


class ScopedRecord(Record):
    scope: ShopScope
    created_at: datetime
    effective_policy_hash: Digest

    @computed_field
    @property
    def expires_at(self) -> datetime:
        return self.scope.expires_at

    @model_validator(mode="after")
    def scope_time(self) -> Self:
        _aware(self.created_at)
        if not self.scope.issued_at <= self.created_at < self.scope.expires_at:
            raise ValueError("record creation must be inside its scope lifetime")
        return self

    def storage_json(self) -> str:
        """Round-trippable stored inputs; computed response fields are rederived."""
        return self.model_dump_json(exclude_computed_fields=True)


class VersionRef(Record):
    id: Identifier
    revision: Revision
    content_hash: Digest


class EvidenceBasis(Record):
    incident_id: Identifier
    sources: tuple[SourceDependency, ...]
    observation: VersionRef
    result: VersionRef
    recapture: VersionRef | None = None
    context_state_hash: Digest

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        _unique(tuple(source.family for source in self.sources))
        return self


class QueueCategory(StrEnum):
    RENEWED_REVIEW = "NEEDS_RENEWED_REVIEW"
    ACTION_RECORDED = "SIMULATED_ACTION_RECORDED"
    IN_PROGRESS = "IN_PROGRESS"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    NOT_LISTED = "NOT_LISTED_IN_CHECKED_NOTICES"


class IncidentSummary(Record):
    incident_id: Identifier
    product_name: Nonempty
    jurisdiction: Nonempty
    source_mode: SourceMode
    checked_sources: tuple[SourceDependency, ...]
    observation_revision: Revision
    result: VersionRef | None
    verdict: Verdict | None
    current: bool
    currentness_hash: Digest
    reasons: tuple[Identifier, ...]
    outstanding_fields: tuple[GuidanceField, ...]
    category: QueueCategory
    latest_action: VersionRef | None = None
    action_type: ActionType | None = None
    uncertainty_unresolved: bool = False
    last_material_update: datetime

    @model_validator(mode="after")
    def coherent_summary(self) -> Self:
        _aware(self.last_material_update)
        if (self.result is None) != (self.verdict is None):
            raise ValueError("result reference and verdict must appear together")
        if (self.latest_action is None) != (self.action_type is None):
            raise ValueError("action reference requires its actual type")
        if self.category == QueueCategory.ACTION_RECORDED:
            if not self.current or self.result is None or self.latest_action is None:
                raise ValueError("recorded action category requires a current result and action")
            review = self.action_type == ActionType.SIMULATED_REVIEW_REQUEST
            if self.uncertainty_unresolved != review:
                raise ValueError("a review request leaves uncertainty unresolved")
            expected = Verdict.REVIEW_REQUIRED if review else Verdict.MATCHED_HOLD_FOR_REVIEW
            if self.verdict != expected:
                raise ValueError("action type and current verdict disagree")
        if self.category == QueueCategory.NOT_LISTED and (
            not self.current
            or self.verdict != Verdict.NOT_LISTED_IN_CHECKED_NOTICES
            or not self.checked_sources
            or self.outstanding_fields
            or self.reasons
            or self.uncertainty_unresolved
        ):
            raise ValueError("negative category needs a complete current scoped result")
        if self.category == QueueCategory.RENEWED_REVIEW and self.current:
            raise ValueError("current results are not renewed-review results")
        return self


class SnapshotStatus(StrEnum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class RetailSnapshot(ScopedRecord):
    id: Identifier
    generated_at: datetime
    currentness_basis_hash: Digest
    current_sources: tuple[SourceDependency, ...]
    status: SnapshotStatus
    rows: tuple[IncidentSummary, ...] | None
    count_scope: Literal["BOUNDED_SHOP"] = "BOUNDED_SHOP"

    @model_validator(mode="after")
    def coherent_snapshot(self) -> Self:
        _aware(self.generated_at)
        if not self.scope.issued_at <= self.generated_at <= self.created_at:
            raise ValueError("snapshot observation must precede creation inside the session")
        if (self.status == SnapshotStatus.UNAVAILABLE) != (self.rows is None):
            raise ValueError("unavailable has unknown rows/counts, never fabricated zero")
        _unique(tuple(row.incident_id for row in self.rows or ()))
        _unique(tuple(source.family for source in self.current_sources))
        if any(row.last_material_update > self.generated_at for row in self.rows or ()):
            raise ValueError("rows cannot postdate their snapshot")
        return self

    @computed_field
    @property
    def category_counts(self) -> dict[QueueCategory, int] | None:
        if self.rows is None:
            return None
        return {
            category: sum(row.category == category for row in self.rows)
            for category in QueueCategory
        }


class FeedbackCategory(StrEnum):
    GUIDANCE_UNCLEAR = "GUIDANCE_UNCLEAR"
    EXTRACTION_DISPUTED = "EXTRACTION_DISPUTED"
    SOURCE_SCOPE_DISPUTED = "SOURCE_SCOPE_DISPUTED"


class FeedbackDetail(StrEnum):
    LOT_CODE_UNCLEAR = "LOT_CODE_UNCLEAR"
    DATE_PANEL_UNCLEAR = "DATE_PANEL_UNCLEAR"
    IDENTITY_PANEL_UNCLEAR = "IDENTITY_PANEL_UNCLEAR"
    EXTRACTED_VALUE_DISPUTED = "EXTRACTED_VALUE_DISPUTED"
    SOURCE_SCOPE_DISPUTED = "SOURCE_SCOPE_DISPUTED"


class FeedbackDisposition(StrEnum):
    RECORDED = "RECORDED"
    TRIAGED = "TRIAGED"
    CANDIDATE_READY = "CANDIDATE_READY"
    NO_SAFE_CANDIDATE = "NO_SAFE_CANDIDATE"
    HUMAN_INVESTIGATION = "HUMAN_INVESTIGATION"
    STALE_BASIS = "STALE_BASIS"


class DispositionEvent(Record):
    disposition: FeedbackDisposition
    recorded_at: datetime


class FeedbackRecord(ScopedRecord):
    id: Identifier
    actor_session: Identifier
    basis: EvidenceBasis
    category: FeedbackCategory
    detail: FeedbackDetail
    history: tuple[DispositionEvent, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def structured_feedback(self) -> Self:
        if self.actor_session != self.scope.session_id:
            raise ValueError("feedback actor must belong to its server scope")
        category = {
            FeedbackDetail.EXTRACTED_VALUE_DISPUTED: FeedbackCategory.EXTRACTION_DISPUTED,
            FeedbackDetail.SOURCE_SCOPE_DISPUTED: FeedbackCategory.SOURCE_SCOPE_DISPUTED,
        }.get(self.detail, FeedbackCategory.GUIDANCE_UNCLEAR)
        if category != self.category:
            raise ValueError("feedback category/detail mismatch")
        if self.history[0].disposition != FeedbackDisposition.RECORDED:
            raise ValueError("feedback history starts with the original recorded disposition")
        previous = self.created_at
        for event in self.history:
            _aware(event.recorded_at)
            if not previous <= event.recorded_at < self.expires_at:
                raise ValueError("disposition history must be chronological and unexpired")
            previous = event.recorded_at
        return self


class PolicyRef(Record):
    id: GuidancePolicyId
    content_hash: Digest

    @model_validator(mode="after")
    def allowlisted(self) -> Self:
        if self.content_hash != POLICIES[self.id].digest():
            raise ValueError("policy identity/hash must match fixed allowlisted content")
        return self


def policy_ref(policy_id: GuidancePolicyId) -> PolicyRef:
    return PolicyRef(id=policy_id, content_hash=POLICIES[policy_id].digest())


class GuidanceBinding(Record):
    policy: PolicyRef
    activation_revision: Revision


class FeedbackSupport(Record):
    feedback: VersionRef
    basis: EvidenceBasis


class CandidateDiagnosis(StrEnum):
    REQUIRED_LOT_GUIDANCE = "REQUIRED_LOT_GUIDANCE"
    REQUIRED_DATE_GUIDANCE = "REQUIRED_DATE_GUIDANCE"


class ImprovementCandidate(ScopedRecord):
    id: Identifier
    family: Literal["required-panel-presentation-1"] = "required-panel-presentation-1"
    rule: VersionRef
    diagnosis: CandidateDiagnosis
    supports: tuple[FeedbackSupport, ...] = Field(min_length=1)
    base: GuidanceBinding
    proposed: PolicyRef
    # Subsequent evaluation/activation state is derived from immutable reports/events.
    status: Literal["CANDIDATE_READY"] = "CANDIDATE_READY"

    @model_validator(mode="after")
    def coherent_candidate(self) -> Self:
        _unique(tuple(item.feedback.id for item in self.supports))
        if any(item.basis.recapture is None for item in self.supports):
            raise ValueError("guidance candidate support requires its recapture reference")
        if self.base.policy == self.proposed:
            raise ValueError("candidate must propose different allowlisted content")
        return self


class LearningCase(StrEnum):
    L01 = "L01"
    L02 = "L02"
    L03 = "L03"
    L04 = "L04"
    L05 = "L05"
    L06 = "L06"


class LearningInvariant(StrEnum):
    SOURCE_TRUTH = "SOURCE_TRUTH"
    OBSERVATIONS = "OBSERVATIONS"
    REQUIRED_FIELDS = "REQUIRED_FIELDS"
    VERDICT_AND_REASONS = "VERDICT_AND_REASONS"
    ACTION_ELIGIBILITY = "ACTION_ELIGIBILITY"
    CURRENTNESS = "CURRENTNESS"
    LIFETIME_COUNTERS = "LIFETIME_COUNTERS"


class InvariantResult(Record):
    invariant: LearningInvariant
    baseline_hash: Digest
    candidate_hash: Digest


class LearningOutput(Record):
    policy: PolicyRef
    instructions: tuple[GuidanceText, ...]
    guidance_check_passed: bool


class PairedCaseResult(Record):
    case: LearningCase
    baseline: LearningOutput
    candidate: LearningOutput
    invariants: tuple[InvariantResult, ...]

    @model_validator(mode="after")
    def declared_invariants(self) -> Self:
        names = tuple(item.invariant for item in self.invariants)
        _unique(names)
        if set(names) != set(LearningInvariant):
            raise ValueError("each paired output requires all declared critical invariants")
        return self

    @property
    def passed(self) -> bool:
        return (
            self.baseline.guidance_check_passed
            and self.candidate.guidance_check_passed
            and all(item.baseline_hash == item.candidate_hash for item in self.invariants)
        )


class EvaluationStatus(StrEnum):
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class EvaluationFailure(StrEnum):
    CASE_FAILED = "CASE_FAILED"
    WORKER_INTERRUPTED = "WORKER_INTERRUPTED"
    DEADLINE_EXCEEDED = "DEADLINE_EXCEEDED"
    STALE_BASIS = "STALE_BASIS"


class CandidateEvaluation(ScopedRecord):
    id: Identifier
    attempt_number: Revision
    initiating_key: Identifier
    payload_hash: Digest
    lease_id: Identifier
    deadline_at: datetime
    candidate: VersionRef
    base: GuidanceBinding
    proposed: PolicyRef
    evidence_basis_hashes: tuple[Digest, ...] = Field(min_length=1)
    suite: VersionRef
    inputs: VersionRef
    evaluator: VersionRef
    outputs: tuple[PairedCaseResult, ...] = ()
    status: EvaluationStatus
    finished_at: datetime | None = None
    failures: tuple[EvaluationFailure, ...] = ()

    @model_validator(mode="after")
    def execution_shape(self) -> Self:
        _aware(self.deadline_at)
        if not self.created_at < self.deadline_at <= self.expires_at:
            raise ValueError("evaluation lease must end inside its session")
        _unique(tuple(output.case for output in self.outputs))
        _unique(self.evidence_basis_hashes)
        if self.status == EvaluationStatus.RUNNING:
            if self.finished_at is not None or self.failures:
                raise ValueError("running attempt cannot have terminal time/failure")
        else:
            if self.finished_at is None:
                raise ValueError("terminal attempt needs completion time")
            _aware(self.finished_at)
            if not self.created_at <= self.finished_at <= self.expires_at:
                raise ValueError("completion must fall inside the record lifetime")
        for output in self.outputs:
            if (
                output.baseline.policy != self.base.policy
                or output.candidate.policy != self.proposed
            ):
                raise ValueError("case outputs must bind the evaluated policies")
        if self.status == EvaluationStatus.PASSED and (
            set(output.case for output in self.outputs) != set(LearningCase)
            or not all(output.passed for output in self.outputs)
            or self.failures
            or self.finished_at >= self.deadline_at
        ):
            raise ValueError("PASS requires all six paired cases before deadline, without failures")
        if self.status == EvaluationStatus.FAILED and not self.failures:
            raise ValueError("failed attempt retains failure evidence")
        if self.status == EvaluationStatus.EXPIRED and (
            self.finished_at < self.deadline_at
            or EvaluationFailure.DEADLINE_EXCEEDED not in self.failures
        ):
            raise ValueError("expiry retains deadline failure and terminal time")
        return self


class GuidancePolicyState(ScopedRecord):
    active: GuidanceBinding
    last_transition: VersionRef | None = None

    @model_validator(mode="after")
    def baseline_or_transition(self) -> Self:
        if (self.active.activation_revision == 1) != (self.last_transition is None):
            raise ValueError("only initial state has no transition reference")
        if self.last_transition is None and self.active.policy.id != GuidancePolicyId.V1:
            raise ValueError("initial state must use the declared baseline")
        return self


class TransitionType(StrEnum):
    ACTIVATE = "ACTIVATE"
    ROLLBACK = "ROLLBACK"


class GuidanceTransition(ScopedRecord):
    id: Identifier
    kind: TransitionType
    previous: GuidanceBinding
    next: GuidanceBinding
    candidate: VersionRef | None = None
    evaluation: VersionRef | None = None
    rollback_of: VersionRef | None = None
    actor_session: Identifier
    confirmed_at: datetime
    explicit_confirmation: bool
    request_key: Identifier
    payload_hash: Digest

    @model_validator(mode="after")
    def monotonic_transition(self) -> Self:
        _aware(self.confirmed_at)
        if self.explicit_confirmation is not True:
            raise ValueError("explicit confirmation must be true")
        if self.actor_session != self.scope.session_id:
            raise ValueError("actor must belong to the transition scope")
        if not self.scope.issued_at <= self.confirmed_at <= self.created_at:
            raise ValueError("explicit confirmation must precede transition creation")
        if self.next.activation_revision != self.previous.activation_revision + 1:
            raise ValueError("activation and rollback both increment revision")
        if self.next.policy == self.previous.policy:
            raise ValueError("transition must change policy content")
        if self.kind == TransitionType.ACTIVATE:
            if self.candidate is None or self.evaluation is None or self.rollback_of is not None:
                raise ValueError("activation binds candidate/evaluation, not rollback reference")
        elif self.rollback_of is None or self.candidate is not None or self.evaluation is not None:
            raise ValueError("rollback binds the prior activation, not a new candidate")
        return self

    @computed_field
    @property
    def logical_identity(self) -> str:
        payload = {
            "scope": self.scope.model_dump(mode="json"),
            "kind": self.kind,
            "candidate": self.candidate.model_dump() if self.candidate else None,
            "evaluation": self.evaluation.model_dump() if self.evaluation else None,
            "rollback_of": self.rollback_of.model_dump() if self.rollback_of else None,
            "expected_revision": self.previous.activation_revision,
            "target": self.next.policy.model_dump(mode="json"),
        }
        return sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def validate_record(
    record: ScopedRecord, *, policy: RetailPolicy, server_scope: ShopScope, now: datetime
) -> None:
    """Shared effective-policy boundary. server_scope must come from T09, not JSON."""
    _aware(now)
    if record.scope != server_scope or not server_scope.issued_at <= now < server_scope.expires_at:
        raise ValueError("foreign or expired scope")
    if record.created_at > now or record.effective_policy_hash != policy.digest():
        raise ValueError("record time or effective policy binding mismatch")
    if (server_scope.expires_at - server_scope.issued_at).total_seconds() > policy.session_seconds:
        raise ValueError("session exceeds the effective lifetime")
    if isinstance(record, RetailSnapshot) and len(record.rows or ()) > policy.max_summary_rows:
        raise ValueError("snapshot exceeds the bounded summary limit")
    if isinstance(record, ImprovementCandidate) and len(record.supports) > policy.max_support_refs:
        raise ValueError("candidate exceeds the support-reference limit")
    if isinstance(record, CandidateEvaluation):
        if record.finished_at is not None and record.finished_at > now:
            raise ValueError("evaluation completion cannot be in the future")
        if record.attempt_number > policy.max_evaluations:
            raise ValueError("evaluation exceeds lifetime attempt allowance")
        if (
            record.deadline_at - record.created_at
        ).total_seconds() > policy.evaluation_deadline_seconds:
            raise ValueError("lease exceeds effective evaluation deadline")
    if isinstance(record, FeedbackRecord) and any(
        event.recorded_at > now for event in record.history
    ):
        raise ValueError("feedback disposition cannot be in the future")
    if isinstance(record, GuidanceTransition):
        if record.next.activation_revision > policy.max_transitions + 1:
            raise ValueError("transition exceeds lifetime transition allowance")
    byte_limit = (
        policy.evaluation_bytes
        if isinstance(record, CandidateEvaluation)
        else (
            policy.record_bytes
            if isinstance(record, (FeedbackRecord, ImprovementCandidate, GuidanceTransition))
            else None
        )
    )
    # Conservative wire-size bound includes computed response fields. Stored
    # inputs are smaller, but must still pass this same bound before persistence.
    if byte_limit is not None and len(record.model_dump_json().encode("utf-8")) > byte_limit:
        raise ValueError("serialized record exceeds the effective byte limit")


def render_guidance(
    policy: RetailPolicy, binding: GuidanceBinding, required: tuple[GuidanceField, ...]
) -> tuple[GuidanceText, ...]:
    return wording_for(
        binding.policy.id, required, max_instruction_chars=policy.max_instruction_chars
    )


class RetailUsage(Record):
    incidents: Count = 0
    feedback: Count = 0
    candidates: Count = 0
    evaluations: Count = 0
    active_evaluations: Count = 0
    forward_activations: Count = 0
    rollbacks: Count = 0

    @model_validator(mode="after")
    def coherent_usage(self) -> Self:
        if self.active_evaluations > self.evaluations or self.rollbacks > self.forward_activations:
            raise ValueError("usage cannot release unreserved work")
        return self


class RetailOperation(StrEnum):
    CREATE_INCIDENT = "CREATE_INCIDENT"
    RECORD_FEEDBACK = "RECORD_FEEDBACK"
    CREATE_CANDIDATE = "CREATE_CANDIDATE"
    START_EVALUATION = "START_EVALUATION"
    ACTIVATE = "ACTIVATE"
    ROLLBACK = "ROLLBACK"


def validate_usage(usage: RetailUsage, policy: RetailPolicy) -> None:
    pairs = (
        (usage.incidents, policy.max_incidents),
        (usage.feedback, policy.max_feedback),
        (usage.candidates, policy.max_candidates),
        (usage.evaluations, policy.max_evaluations),
        (usage.active_evaluations, policy.max_active_evaluations),
        (usage.forward_activations, policy.max_forward_activations),
        (usage.forward_activations + usage.rollbacks, policy.max_transitions),
    )
    if any(current > limit for current, limit in pairs):
        raise ValueError("effective lifetime or active allowance exhausted")


def admit_new_operation(
    usage: RetailUsage, operation: RetailOperation, policy: RetailPolicy
) -> RetailUsage:
    """Pure reservation proposal, to be committed atomically after deduplication.

    This does not authenticate, write, evaluate, activate or reserve cloud spend.
    T35 checks current transition/lease ownership before invoking it.
    """
    validate_usage(usage, policy)
    values = usage.model_dump()
    field = {
        RetailOperation.CREATE_INCIDENT: "incidents",
        RetailOperation.RECORD_FEEDBACK: "feedback",
        RetailOperation.CREATE_CANDIDATE: "candidates",
        RetailOperation.START_EVALUATION: "evaluations",
        RetailOperation.ACTIVATE: "forward_activations",
        RetailOperation.ROLLBACK: "rollbacks",
    }[operation]
    values[field] += 1
    if operation == RetailOperation.START_EVALUATION:
        values["active_evaluations"] += 1
    result = RetailUsage(**values)
    validate_usage(result, policy)
    return result

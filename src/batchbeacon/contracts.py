"""Immutable domain records. Trusted source review is never a model output schema."""

from datetime import date, datetime
from enum import StrEnum
from hashlib import sha256
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Nonempty = Annotated[str, Field(min_length=1)]
Digest = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Revision = Annotated[int, Field(ge=1)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    def digest(self) -> str:
        return sha256(self.model_dump_json().encode()).hexdigest()


class EvidenceKind(StrEnum):
    SOURCE = "SOURCE"
    CAPTURE = "CAPTURE"


class EvidenceRef(Record):
    kind: EvidenceKind
    artifact_id: Nonempty
    sha256: Digest
    locator: Nonempty


class ValueState(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"


class ValueType(StrEnum):
    TEXT = "TEXT"
    DATE = "DATE"


class ObservedValue(Record):
    raw: str
    state: ValueState
    value_type: ValueType = ValueType.TEXT
    value: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()

    @model_validator(mode="after")
    def supported_value(self) -> Self:
        if self.state == ValueState.KNOWN:
            if not self.value or not self.evidence:
                raise ValueError("known values require nonempty value and evidence")
            if self.value_type == ValueType.DATE:
                parsed = date.fromisoformat(self.value)
                if parsed.isoformat() != self.value:
                    raise ValueError("normalized dates require YYYY-MM-DD")
        elif self.value is not None:
            raise ValueError("unknown/ambiguous values cannot assert a normalized value")
        return self


class IdentifierKind(StrEnum):
    PRODUCT_CODE = "PRODUCT_CODE"
    GTIN = "GTIN"
    LOT = "LOT"


class ObservedIdentifier(Record):
    kind: IdentifierKind
    observation: ObservedValue


class TrustedIdentifier(Record):
    kind: IdentifierKind
    value: Nonempty
    evidence: tuple[EvidenceRef, ...] = Field(min_length=1)


class ProductIdentity(Record):
    name: ObservedValue
    pack: ObservedValue
    identifiers: tuple[ObservedIdentifier, ...] = ()
    # Set only by a server-side reviewed identity/alias resolver, never a model/client.
    resolved_name: Nonempty | None = None
    resolution_review_hash: Digest | None = None

    @model_validator(mode="after")
    def reviewed_resolution(self) -> Self:
        if (self.resolved_name is None) != (self.resolution_review_hash is None):
            raise ValueError("identity resolution requires its review hash")
        return self


class IdentityRule(Record):
    canonical_name: Nonempty
    reviewed_aliases: tuple[Nonempty, ...] = ()
    pack: Nonempty | None = None
    pack_material: bool = True
    identifiers: tuple[TrustedIdentifier, ...] = ()
    evidence: tuple[EvidenceRef, ...] = Field(min_length=1)
    normalization: Literal["name-casefold-whitespace-v1"] = "name-casefold-whitespace-v1"

    @model_validator(mode="after")
    def material_pack_present(self) -> Self:
        if self.pack_material and self.pack is None:
            raise ValueError("material pack identity requires a reviewed pack")
        if any(code.kind == IdentifierKind.LOT for code in self.identifiers):
            raise ValueError("LOT cannot establish product identity")
        return self


class PredicateField(StrEnum):
    LOT = "LOT"
    BEST_BEFORE = "BEST_BEFORE"
    USE_BY = "USE_BY"


class Operator(StrEnum):
    EXACT = "EXACT"
    SET = "SET"
    RANGE = "RANGE"
    ALL = "ALL"
    NOT_SPECIFIED = "NOT_SPECIFIED"
    UNKNOWN = "UNKNOWN"


class DateRange(Record):
    lower: date
    upper: date
    lower_inclusive: bool = True
    upper_inclusive: bool = True

    @model_validator(mode="after")
    def valid_range(self) -> Self:
        if self.lower > self.upper or (
            self.lower == self.upper and not (self.lower_inclusive and self.upper_inclusive)
        ):
            raise ValueError("empty or reversed date range")
        return self


class PredicateRule(Record):
    field: PredicateField
    operator: Operator
    value_type: ValueType
    values: tuple[Nonempty, ...] = ()
    date_range: DateRange | None = None
    applies: bool = True
    applicability_reason: str | None = None
    evidence: tuple[EvidenceRef, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def operator_shape(self) -> Self:
        if self.operator == Operator.EXACT and len(self.values) != 1:
            raise ValueError("EXACT requires one value")
        if self.operator == Operator.SET and not self.values:
            raise ValueError("SET requires values")
        if self.operator not in (Operator.EXACT, Operator.SET) and self.values:
            raise ValueError("values are only valid for EXACT and SET")
        if self.operator == Operator.RANGE:
            if self.value_type != ValueType.DATE or self.date_range is None:
                raise ValueError("only explicitly typed date ranges are supported")
        elif self.date_range is not None:
            raise ValueError("range bounds require RANGE")
        expected = ValueType.TEXT if self.field == PredicateField.LOT else ValueType.DATE
        if self.value_type != expected:
            raise ValueError("predicate field/value type mismatch")
        if self.value_type == ValueType.DATE:
            for value in self.values:
                if date.fromisoformat(value).isoformat() != value:
                    raise ValueError("source dates require YYYY-MM-DD")
        if not self.applies and not self.applicability_reason:
            raise ValueError("not-applicable requires a reviewed reason")
        return self


class AffectedProductRule(Record):
    id: Nonempty
    identity: IdentityRule
    predicates: tuple[PredicateRule, ...]

    @model_validator(mode="after")
    def unique_fields(self) -> Self:
        fields = [rule.field for rule in self.predicates]
        if len(fields) != len(set(fields)):
            raise ValueError("one reviewed predicate per field")
        return self


class HumanReview(Record):
    revision: Revision
    reviewer: Nonempty
    reviewed_at: datetime
    record_hash: Digest
    rights_basis: Nonempty

    @model_validator(mode="after")
    def aware_review(self) -> Self:
        if self.reviewed_at.tzinfo is None:
            raise ValueError("review time requires timezone")
        return self


class SourceDependency(Record):
    family: Nonempty
    version: Nonempty
    content_hash: Digest
    epoch: Revision
    review_revision: Revision


class AuthorityNotice(Record):
    dependency: SourceDependency
    authority: Nonempty
    original_url: Nonempty
    final_url: Nonempty
    published_at: date
    retrieved_at: datetime
    jurisdictions: tuple[Nonempty, ...] = Field(min_length=1)
    review: HumanReview | None
    interpretation_complete: bool
    source_available: bool
    source_proposal_agrees: bool
    products: tuple[AffectedProductRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def bound_source_support(self) -> Self:
        if self.retrieved_at.tzinfo is None:
            raise ValueError("retrieval time requires timezone")
        if self.review and self.review.revision != self.dependency.review_revision:
            raise ValueError("review revision must match dependency")
        ids = [product.id for product in self.products]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate product rules")
        for product in self.products:
            refs = list(product.identity.evidence)
            refs.extend(ref for code in product.identity.identifiers for ref in code.evidence)
            refs.extend(ref for predicate in product.predicates for ref in predicate.evidence)
            if any(
                ref.kind != EvidenceKind.SOURCE
                or ref.artifact_id != self.dependency.version
                or ref.sha256 != self.dependency.content_hash for ref in refs
            ):
                raise ValueError("rule support must belong to this exact notice version")
        return self


class ObservedPredicate(Record):
    field: PredicateField
    observation: ObservedValue


class Correction(Record):
    field: Nonempty
    previous: ObservedValue
    replacement: ObservedValue
    actor_session: Nonempty
    recorded_at: datetime


class SourceAgreement(Record):
    """Server translation receipt, scoped to one immutable acquisition input."""
    source: SourceDependency
    notice_digest: Digest
    proposal_hash: Digest
    schema_hash: Digest
    translation_policy_hash: Digest
    run_id: Annotated[str, Field(pattern=r"^[a-f0-9]{32}$")]
    binding_hash: Digest


class ProductObservation(Record):
    session_id: Nonempty
    incident_id: Nonempty
    revision: Revision
    captures: tuple[EvidenceRef, ...] = Field(min_length=1)
    identity: ProductIdentity
    fields: tuple[ObservedPredicate, ...]
    corrections: tuple[Correction, ...] = ()
    model_id: Nonempty
    prompt_version: Nonempty
    source_agreement: SourceAgreement | None = None

    @model_validator(mode="after")
    def bound_capture_support(self) -> Self:
        fields = [item.field for item in self.fields]
        if len(fields) != len(set(fields)):
            raise ValueError("duplicate observed fields")
        if any(ref.kind != EvidenceKind.CAPTURE for ref in self.captures):
            raise ValueError("observation captures must be capture references")
        allowed = {(ref.artifact_id, ref.sha256) for ref in self.captures}
        values = [self.identity.name, self.identity.pack]
        values.extend(code.observation for code in self.identity.identifiers)
        values.extend(item.observation for item in self.fields)
        values.extend(value for correction in self.corrections
                      for value in (correction.previous, correction.replacement))
        for value in values:
            if any(ref.kind != EvidenceKind.CAPTURE or (ref.artifact_id, ref.sha256)
                   not in allowed for ref in value.evidence):
                raise ValueError("observed field support must belong to a retained capture")
        current_values = {item.field.value: item.observation for item in self.fields}
        current_values.update(PRODUCT_NAME=self.identity.name, PACK=self.identity.pack)
        for code in self.identity.identifiers:
            key = code.kind.value
            if key in current_values and current_values[key] != code.observation:
                current_values[key] = None  # Conflicting input needs resolution first.
            else:
                current_values[key] = code.observation
        latest = {}
        for correction in self.corrections:
            if correction.actor_session != self.session_id or correction.recorded_at.tzinfo is None:
                raise ValueError("correction owner/time mismatch")
            if correction.field not in current_values:
                raise ValueError("correction must name an observed field")
            prior = latest.get(correction.field)
            if prior and (prior.replacement != correction.previous
                          or correction.recorded_at < prior.recorded_at):
                raise ValueError("correction history must be a chronological value chain")
            latest[correction.field] = correction
        if any(current_values[field] != correction.replacement
               for field, correction in latest.items()):
            raise ValueError("final correction must equal the current observed value")
        return self


class SourceMode(StrEnum):
    HISTORICAL_DEMO = "HISTORICAL_DEMO"
    LIVE = "LIVE"


class LiveStatus(StrEnum):
    NEVER_REQUESTED = "NEVER_REQUESTED"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class VerificationContext(Record):
    jurisdiction: Nonempty
    mode: SourceMode
    historical_selected_at: datetime | None = None
    live_status: LiveStatus = LiveStatus.NEVER_REQUESTED
    live_validated_at: datetime | None = None
    current_sources: tuple[SourceDependency, ...]
    result_revision: Revision
    computed_at: datetime

    @model_validator(mode="after")
    def aware_times(self) -> Self:
        for stamp in (self.historical_selected_at, self.live_validated_at, self.computed_at):
            if stamp is not None and stamp.tzinfo is None:
                raise ValueError("context times require timezone")
        if len({dep.family for dep in self.current_sources}) != len(self.current_sources):
            raise ValueError("one current dependency per source family")
        return self


class VerifierPolicy(Record):
    version: Nonempty = "verifier-policy-1"
    live_freshness_seconds: Annotated[int, Field(gt=0)] = 86400


class Comparison(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ComparisonRow(Record):
    field: Nonempty
    outcome: Comparison
    reason: Nonempty
    observed: str | None
    source_values: tuple[str, ...] = ()
    matched_member: str | None = None
    source_evidence: tuple[EvidenceRef, ...]
    observation_evidence: tuple[EvidenceRef, ...] = ()
    source_operator: Operator | None = None
    source_date_range: DateRange | None = None
    source_applies: bool | None = None

    @model_validator(mode="after")
    def range_restriction(self) -> Self:
        if (self.source_operator == Operator.RANGE) != (self.source_date_range is not None):
            raise ValueError("RANGE evidence rows must retain their typed bounds")
        return self


class CandidateComparison(Record):
    source: SourceDependency
    product_id: Nonempty
    eligible_jurisdiction: bool
    identity: ComparisonRow
    predicates: tuple[ComparisonRow, ...]
    outcome: Comparison


class Verdict(StrEnum):
    MATCHED_HOLD_FOR_REVIEW = "MATCHED_HOLD_FOR_REVIEW"
    NOT_LISTED_IN_CHECKED_NOTICES = "NOT_LISTED_IN_CHECKED_NOTICES"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class VerificationResult(Record):
    schema_version: Literal[1] = 1
    session_id: Nonempty
    incident_id: Nonempty
    revision: Revision
    observation_revision: Revision
    checked_sources: tuple[SourceDependency, ...]
    jurisdiction: Nonempty
    mode: SourceMode
    verdict: Verdict
    reasons: tuple[Nonempty, ...]
    candidates: tuple[CandidateComparison, ...]
    outstanding_fields: tuple[Nonempty, ...]
    hold_eligible: bool
    verifier_version: Nonempty
    policy_hash: Digest
    context_state_hash: Digest
    computed_at: datetime
    cache_provenance: Literal["computed"] = "computed"

    @model_validator(mode="after")
    def coherent_result(self) -> Self:
        if self.computed_at.tzinfo is None:
            raise ValueError("result time requires timezone")
        matched = self.verdict == Verdict.MATCHED_HOLD_FOR_REVIEW
        if self.hold_eligible != matched:
            raise ValueError("hold eligibility must agree with the computed verdict")
        if any(candidate.source not in self.checked_sources for candidate in self.candidates):
            raise ValueError("candidate evidence must belong to a checked source")
        eligible = [candidate for candidate in self.candidates if candidate.eligible_jurisdiction]
        if self.verdict != Verdict.REVIEW_REQUIRED:
            if not self.checked_sources or not eligible or self.outstanding_fields or self.reasons:
                raise ValueError("decidable result requires complete checked evidence")
            if matched and not any(c.outcome == Comparison.MATCH for c in eligible):
                raise ValueError("matched result requires an eligible matched candidate")
            if not matched and not all(c.outcome == Comparison.MISMATCH for c in eligible):
                raise ValueError("scoped negative requires all eligible candidates excluded")
        return self


class ActionType(StrEnum):
    SIMULATED_HOLD = "SIMULATED_HOLD"
    SIMULATED_REVIEW_REQUEST = "SIMULATED_REVIEW_REQUEST"


class ActionRecord(Record):
    id: Nonempty
    session_id: Nonempty
    incident_id: Nonempty
    result_revision: Revision
    observation_revision: Revision
    sources: tuple[SourceDependency, ...]
    action_type: ActionType
    actor_session: Nonempty
    confirmed_at: datetime
    request_key: Nonempty
    payload_hash: Digest
    simulation: Literal[True] = True
    prior_action_id: str | None = None

    @model_validator(mode="after")
    def coherent_action(self) -> Self:
        if self.actor_session != self.session_id or self.confirmed_at.tzinfo is None:
            raise ValueError("action owner/time mismatch")
        if self.action_type == ActionType.SIMULATED_HOLD and not self.sources:
            raise ValueError("a simulated hold must retain its source dependencies")
        if len({source.family for source in self.sources}) != len(self.sources):
            raise ValueError("action requires one dependency per source family")
        return self


class IncidentEvent(Record):
    id: Nonempty
    session_id: Nonempty
    incident_id: Nonempty
    sequence: Revision
    event_type: Nonempty
    result_revision: Revision | None
    observation_revision: Revision
    source_mode: SourceMode
    recorded_at: datetime
    reason: Nonempty

    @model_validator(mode="after")
    def aware_event(self) -> Self:
        if self.recorded_at.tzinfo is None:
            raise ValueError("event time requires timezone")
        return self

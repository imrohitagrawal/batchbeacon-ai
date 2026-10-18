"""Identity-first, source-scoped comparison over trusted immutable records."""

import json
from datetime import date
from hashlib import sha256

from batchbeacon.contracts import (
    AuthorityNotice,
    CandidateComparison,
    Comparison,
    ComparisonRow,
    IdentityRule,
    LiveStatus,
    ObservedValue,
    Operator,
    PredicateRule,
    ProductIdentity,
    ProductObservation,
    SourceDependency,
    SourceMode,
    ValueState,
    Verdict,
    VerificationContext,
    VerificationResult,
    VerifierPolicy,
)

VERIFIER_VERSION = "verifier-1"


def _name(value: str) -> str:
    """Reviewed name normalization only; never applied to codes or lots."""
    return " ".join(value.casefold().split())


def compare_identity(rule: IdentityRule, observed: ProductIdentity) -> ComparisonRow:
    refs = observed.name.evidence + observed.pack.evidence
    source_refs = rule.evidence + tuple(ref for code in rule.identifiers for ref in code.evidence)
    expected = {_name(rule.canonical_name), *(_name(alias) for alias in rule.reviewed_aliases)}
    name_known = observed.name.state == ValueState.KNOWN
    resolved = observed.resolved_name if name_known else None
    name_matches = name_known and _name(resolved or observed.name.value) in expected
    name_excluded = name_known and resolved is not None and _name(resolved) not in expected
    expected_by_kind = {}
    for code in rule.identifiers:
        expected_by_kind.setdefault(code.kind, set()).add(code.value)
    typed_comparisons = []
    for code in observed.identifiers:
        expected_values = expected_by_kind.get(code.kind)
        if expected_values and code.observation.state == ValueState.KNOWN:
            typed_comparisons.append(code.observation.value in expected_values)
            refs += code.observation.evidence
    code_matches = any(typed_comparisons)
    code_excluded = any(not match for match in typed_comparisons)
    pack_known = observed.pack.state == ValueState.KNOWN
    pack_excluded = rule.pack_material and pack_known and observed.pack.value != rule.pack
    if (code_matches and code_excluded) or (name_matches and code_excluded) \
            or (name_excluded and code_matches):
        outcome, reason = Comparison.UNKNOWN, "IDENTITY_CONFLICT"
    elif rule.pack_material and not pack_known:
        outcome, reason = Comparison.UNKNOWN, "IDENTITY_UNCERTAIN"
    elif pack_excluded and (name_matches or code_matches or name_excluded):
        outcome, reason = Comparison.MISMATCH, "MATERIAL_PACK_EXCLUDED"
    elif name_matches or code_matches:
        outcome, reason = Comparison.MATCH, "REVIEWED_IDENTITY_MATCH"
    elif name_excluded or code_excluded:
        outcome, reason = Comparison.MISMATCH, "REVIEWED_IDENTITY_EXCLUDED"
    else:
        outcome, reason = Comparison.UNKNOWN, "IDENTITY_UNCERTAIN"
    return ComparisonRow(
        field="IDENTITY", outcome=outcome, reason=reason, observed=observed.name.value,
        source_values=(rule.canonical_name,), source_evidence=source_refs,
        observation_evidence=refs,
    )


def compare_predicate(rule: PredicateRule, observed: ObservedValue | None) -> ComparisonRow:
    value = observed.value if observed else None
    refs = observed.evidence if observed else ()
    member = None
    if not rule.applies:
        outcome, reason = Comparison.NOT_APPLICABLE, rule.applicability_reason
    elif rule.operator in (Operator.ALL, Operator.NOT_SPECIFIED):
        outcome, reason = Comparison.NOT_APPLICABLE, f"REVIEWED_{rule.operator.value}"
    elif rule.operator == Operator.UNKNOWN:
        outcome, reason = Comparison.UNKNOWN, "SOURCE_PREDICATE_UNKNOWN"
    elif observed is None or observed.state != ValueState.KNOWN:
        outcome = Comparison.UNKNOWN
        reason = "DATE_AMBIGUOUS" if observed and observed.state == ValueState.AMBIGUOUS \
            else "PREDICATE_UNKNOWN"
    elif observed.value_type != rule.value_type:
        outcome, reason = Comparison.UNKNOWN, "VALUE_TYPE_MISMATCH"
    elif rule.operator in (Operator.EXACT, Operator.SET):
        matches = value in rule.values
        outcome = Comparison.MATCH if matches else Comparison.MISMATCH
        reason = "SUPPORTED_VALUE_MATCH" if matches else "SUPPORTED_VALUE_EXCLUDED"
        member = value if matches else None
    elif rule.operator == Operator.RANGE:
        bounds = rule.date_range
        # Contract validation admits only nonempty typed date ranges and ISO dates.
        point = date.fromisoformat(value)
        lower = point >= bounds.lower if bounds.lower_inclusive else point > bounds.lower
        upper = point <= bounds.upper if bounds.upper_inclusive else point < bounds.upper
        outcome = Comparison.MATCH if lower and upper else Comparison.MISMATCH
        reason = "SUPPORTED_RANGE_MATCH" if lower and upper else "SUPPORTED_RANGE_EXCLUDED"
    else:
        outcome, reason = Comparison.UNKNOWN, "UNSUPPORTED_OPERATOR"
    return ComparisonRow(
        field=rule.field.value, outcome=outcome, reason=reason, observed=value,
        source_values=rule.values, matched_member=member, source_evidence=rule.evidence,
        observation_evidence=refs, source_operator=rule.operator,
        source_date_range=rule.date_range, source_applies=rule.applies,
    )


def _dependencies_current(
    checked: tuple[SourceDependency, ...], current: tuple[SourceDependency, ...],
) -> bool:
    mapping = {dependency.family: dependency for dependency in current}
    return len(mapping) == len(current) and all(
        mapping.get(dependency.family) == dependency for dependency in checked
    )


def _context_blockers(context: VerificationContext, policy: VerifierPolicy) -> list[str]:
    if context.live_status in (LiveStatus.FAILED, LiveStatus.EXPIRED):
        return ["SOURCE_UNAVAILABLE" if context.live_status == LiveStatus.FAILED
                else "FRESHNESS_EXPIRED"]
    if context.mode == SourceMode.LIVE:
        if context.live_status != LiveStatus.VALIDATED or context.live_validated_at is None:
            return ["SOURCE_UNAVAILABLE"]
        age = (context.computed_at - context.live_validated_at).total_seconds()
        if age < 0 or age >= policy.live_freshness_seconds:
            return ["FRESHNESS_EXPIRED"]
    elif context.historical_selected_at is None \
            or context.historical_selected_at > context.computed_at:
        return ["HISTORICAL_SELECTION_REQUIRED"]
    return []


def is_current(
    result: VerificationResult, *, observation_revision: int,
    context: VerificationContext, policy: VerifierPolicy,
) -> bool:
    """Check the bound state, not hold eligibility; run even when quota is exhausted."""
    return (
        result.observation_revision == observation_revision
        and result.revision == context.result_revision
        and result.mode == context.mode
        and result.jurisdiction == context.jurisdiction
        and result.computed_at <= context.computed_at
        and result.policy_hash == policy.digest()
        and result.context_state_hash == _context_state_hash(context, policy)
    )


def _context_state_hash(context: VerificationContext, policy: VerifierPolicy) -> str:
    """Bind source/failure state while allowing time to advance within that state.

    A fresh failure-bound review can be current without being eligible for a hold.
    Crossing the freshness boundary changes the effective blockers and invalidates
    the old result. A source/state change still requires a new result revision.
    This hash is lineage evidence, not a substitute for session authorization.
    """
    state = context.model_dump(mode="json", exclude={"computed_at"})
    state["current_sources"] = sorted(state["current_sources"], key=lambda item: item["family"])
    state["effective_blockers"] = _context_blockers(context, policy)
    return sha256(json.dumps(state, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def is_current_evidence(
    result: VerificationResult, observation: ProductObservation,
    notices: tuple[AuthorityNotice, ...], context: VerificationContext,
    policy: VerifierPolicy,
) -> bool:
    """Check actual source support as well as the adapter's dependency registry.

    A missed epoch update must not leave changed or withdrawn source facts current.
    Re-verification remains possible; only the computation timestamp may advance.
    This is a pure comparison and never publishes a new verification revision.
    """
    if not is_current(result, observation_revision=observation.revision,
                      context=context, policy=policy):
        return False
    expected = verify(observation, notices, context, policy)
    return result.model_dump(exclude={"computed_at"}) == expected.model_dump(
        exclude={"computed_at"})


def verify(
    observation: ProductObservation, notices: tuple[AuthorityNotice, ...],
    context: VerificationContext, policy: VerifierPolicy,
) -> VerificationResult:
    checked = tuple(notice.dependency for notice in notices)
    blockers: list[str] = []
    if not notices:
        blockers.append("NO_CHECKED_COVERAGE")
    if len({dependency.family for dependency in checked}) != len(checked):
        blockers.append("CONFLICTING_SOURCE_VERSIONS")
    if not _dependencies_current(checked, context.current_sources):
        blockers.append("SOURCE_VERSION_CHANGED")
    for source in notices:
        if source.review is None:
            blockers.append("SOURCE_UNREVIEWED")
        if not source.interpretation_complete:
            blockers.append("SOURCE_INCOMPLETE")
        if not source.source_available:
            blockers.append("SOURCE_UNAVAILABLE")
        if not source.source_proposal_agrees:
            blockers.append("SOURCE_EXTRACTION_DISAGREEMENT")
    blockers.extend(_context_blockers(context, policy))

    values = {item.field: item.observation for item in observation.fields}
    candidates = []
    missing = set()
    for source in notices:
        for product in source.products:
            identity = compare_identity(product.identity, observation.identity)
            if identity.outcome != Comparison.MATCH:
                rows = tuple(ComparisonRow(
                    field=rule.field.value, outcome=Comparison.NOT_APPLICABLE,
                    reason="IDENTITY_FIRST", observed=None, source_values=rule.values,
                    source_evidence=rule.evidence, source_operator=rule.operator,
                    source_date_range=rule.date_range, source_applies=rule.applies,
                ) for rule in product.predicates)
                outcome = identity.outcome
                if outcome == Comparison.UNKNOWN:
                    missing.add("IDENTITY")
            else:
                rows = tuple(compare_predicate(rule, values.get(rule.field))
                             for rule in product.predicates)
                if any(row.outcome == Comparison.UNKNOWN for row in rows):
                    outcome = Comparison.UNKNOWN
                    missing.update(row.field for row in rows if row.outcome == Comparison.UNKNOWN)
                elif any(row.outcome == Comparison.MISMATCH for row in rows):
                    outcome = Comparison.MISMATCH
                else:
                    outcome = Comparison.MATCH
            candidates.append(CandidateComparison(
                source=source.dependency, product_id=product.id,
                eligible_jurisdiction=context.jurisdiction in source.jurisdictions,
                identity=identity, predicates=rows, outcome=outcome,
            ))
    eligible = [candidate for candidate in candidates if candidate.eligible_jurisdiction]
    foreign_positive = any(candidate.outcome == Comparison.MATCH
                           and not candidate.eligible_jurisdiction for candidate in candidates)
    if not eligible or foreign_positive:
        blockers.append("OUT_OF_SCOPE")
    if blockers:
        verdict = Verdict.REVIEW_REQUIRED
    elif any(candidate.outcome == Comparison.MATCH for candidate in eligible):
        verdict = Verdict.MATCHED_HOLD_FOR_REVIEW
        missing.clear()
    elif eligible and all(candidate.outcome == Comparison.MISMATCH for candidate in eligible):
        verdict = Verdict.NOT_LISTED_IN_CHECKED_NOTICES
        missing.clear()
    else:
        verdict = Verdict.REVIEW_REQUIRED
        blockers.append("IDENTITY_UNCERTAIN" if "IDENTITY" in missing else "PREDICATE_UNKNOWN")
    # Recover identity before requesting more lot/date evidence. Global source failures
    # require source review, not an unnecessary image acquisition.
    if "IDENTITY" in missing:
        missing = {"IDENTITY"}
    if any(reason.startswith(("SOURCE_", "FRESHNESS_", "NO_CHECKED", "OUT_OF_SCOPE",
                              "HISTORICAL_", "CONFLICTING_")) for reason in blockers):
        missing.clear()
    return VerificationResult(
        session_id=observation.session_id, incident_id=observation.incident_id,
        revision=context.result_revision, observation_revision=observation.revision,
        checked_sources=checked, jurisdiction=context.jurisdiction, mode=context.mode,
        verdict=verdict, reasons=tuple(dict.fromkeys(blockers)), candidates=tuple(candidates),
        outstanding_fields=tuple(sorted(missing)),
        hold_eligible=verdict == Verdict.MATCHED_HOLD_FOR_REVIEW,
        verifier_version=VERIFIER_VERSION, policy_hash=policy.digest(),
        context_state_hash=_context_state_hash(context, policy),
        computed_at=context.computed_at,
    )

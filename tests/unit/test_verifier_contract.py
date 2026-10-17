"""Pre-implementation truth tables from the independent acceptance checkpoint."""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import (
    Comparison,
    DateRange,
    IdentifierKind,
    LiveStatus,
    ObservedIdentifier,
    Operator,
    PredicateField,
    PredicateRule,
    TrustedIdentifier,
    ValueType,
    Verdict,
    VerifierPolicy,
)
from batchbeacon.domain.verifier import compare_identity, compare_predicate, is_current, verify
from tests.unit.domain_fixtures import (
    context,
    known,
    notice,
    observation,
    revise,
    source_ref,
    unknown,
)


@pytest.mark.parametrize("name", [
    "Camembert Superieur Au Lait Cru", "Bertrand Pere & Fils Camembert au lait cru",
])
def test_both_reviewed_sfa_products_match(name):
    result = verify(observation(name), (notice(),), context(), VerifierPolicy())
    assert result.verdict == Verdict.MATCHED_HOLD_FOR_REVIEW
    assert result.hold_eligible
    assert not result.outstanding_fields


def test_same_lot_third_identity_does_not_match():
    result = verify(observation("Meadow Vale Brie"), (notice(),), context(), VerifierPolicy())
    assert result.verdict == Verdict.NOT_LISTED_IN_CHECKED_NOTICES
    assert not result.hold_eligible
    assert all(candidate.identity.outcome == Comparison.MISMATCH for candidate in result.candidates)


def test_missing_identity_never_established_by_lot():
    obs = observation()
    obs = revise(obs, identity=revise(obs.identity, name=unknown()))
    result = verify(obs, (notice(),), context(), VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED
    assert result.outstanding_fields == ("IDENTITY",)


def test_unreviewed_alias_never_becomes_identity_exclusion():
    result = verify(observation("regional shorthand Camembert"), (notice(),), context(),
                    VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED
    assert not result.hold_eligible


def test_typed_product_code_is_not_gtin_or_lot():
    rule = notice().products[0].identity
    rule = revise(rule, identifiers=(TrustedIdentifier(kind=IdentifierKind.PRODUCT_CODE,
                  value="001A", evidence=(source_ref(),)),))
    obs = revise(observation().identity, name=unknown(), resolved_name=None,
                 resolution_review_hash=None, identifiers=(ObservedIdentifier(
        kind=IdentifierKind.GTIN, observation=known("001A")),))
    assert compare_identity(rule, obs).outcome == Comparison.UNKNOWN
    obs = revise(obs, identifiers=(ObservedIdentifier(kind=IdentifierKind.PRODUCT_CODE,
                                                    observation=known("001A")),))
    assert compare_identity(rule, obs).outcome == Comparison.MATCH


@pytest.mark.parametrize(("source_value", "seen", "expected"), [
    ("001A", "001A", Comparison.MATCH), ("001A", "1A", Comparison.MISMATCH),
    ("001A", "001a", Comparison.MISMATCH), ("001A", "001A ", Comparison.MISMATCH),
])
def test_exact_lot_preserves_case_whitespace_and_leading_zero(source_value, seen, expected):
    rule = revise(notice().products[0].predicates[0], values=(source_value,))
    assert compare_predicate(rule, known(seen)).outcome == expected


def test_set_records_the_actual_matching_member():
    rule = revise(notice().products[0].predicates[0], operator=Operator.SET,
                  values=("A001", "B002"))
    result = compare_predicate(rule, known("B002"))
    assert result.outcome == Comparison.MATCH
    assert result.matched_member == "B002"


@pytest.mark.parametrize(("value", "inclusive", "expected"), [
    ("2026-10-09", True, Comparison.MISMATCH), ("2026-10-10", True, Comparison.MATCH),
    ("2026-10-10", False, Comparison.MISMATCH), ("2026-10-15", False, Comparison.MATCH),
    ("2026-10-20", True, Comparison.MATCH), ("2026-10-20", False, Comparison.MISMATCH),
    ("2026-10-21", True, Comparison.MISMATCH),
])
def test_reviewed_typed_date_range_boundaries(value, inclusive, expected):
    rule = PredicateRule(field=PredicateField.BEST_BEFORE, operator=Operator.RANGE,
                         value_type=ValueType.DATE, evidence=(source_ref(),),
                         date_range=DateRange(lower=date(2026, 10, 10), upper=date(2026, 10, 20),
                                              lower_inclusive=inclusive, upper_inclusive=inclusive))
    assert compare_predicate(rule, known(value, ValueType.DATE)).outcome == expected
    assert compare_predicate(rule, unknown(True, ValueType.DATE)).outcome == Comparison.UNKNOWN


@pytest.mark.parametrize("operator", [Operator.ALL, Operator.NOT_SPECIFIED])
def test_reviewed_unrestricted_fields_do_not_require_capture(operator):
    rule = revise(notice().products[0].predicates[0], operator=operator, values=())
    result = compare_predicate(rule, None)
    assert result.outcome == Comparison.NOT_APPLICABLE
    assert result.reason and result.observed is None


def test_unknown_source_rule_is_never_a_wildcard_or_exclusion():
    rule = revise(notice().products[0].predicates[0], operator=Operator.UNKNOWN, values=())
    assert compare_predicate(rule, known("232511")).outcome == Comparison.UNKNOWN


def test_not_applicable_needs_a_reviewed_reason():
    rule = notice().products[0].predicates[0]
    with pytest.raises(ValidationError):
        revise(rule, applies=False)
    inapplicable = revise(rule, applies=False, applicability_reason="no lot scope")
    result = compare_predicate(inapplicable, None)
    assert result.outcome == Comparison.NOT_APPLICABLE and result.reason == "no lot scope"


def test_unknown_relevant_candidate_blocks_negative_not_supported_positive():
    src = notice()
    uncertain = revise(src.products[0], id="same-identity-unknown", predicates=(
        revise(src.products[0].predicates[0], field=PredicateField.USE_BY,
               value_type=ValueType.DATE, values=("2026-10-17",)),))
    src = revise(src, products=(src.products[0], uncertain))
    result = verify(observation(lot="wrong"), (src,), context(src), VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED
    positive = verify(observation(), (src,), context(src), VerifierPolicy())
    assert positive.verdict == Verdict.MATCHED_HOLD_FOR_REVIEW


@pytest.mark.parametrize("changes", [
    {"review": None}, {"interpretation_complete": False}, {"source_available": False},
    {"source_proposal_agrees": False},
])
def test_global_source_failures_are_review_only(changes):
    src = revise(notice(), **changes)
    result = verify(observation(), (src,), context(src), VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED and not result.hold_eligible


def test_no_coverage_and_foreign_positive_never_clear():
    uncovered = verify(observation(), (), revise(context(), current_sources=()), VerifierPolicy())
    assert uncovered.verdict == Verdict.REVIEW_REQUIRED
    result = verify(observation(), (notice(),), revise(context(), jurisdiction="GB-SCT"),
                    VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED and "OUT_OF_SCOPE" in result.reasons


@pytest.mark.parametrize("name", ["Camembert Superieur Au Lait Cru", "Meadow Vale Brie"])
def test_source_change_invalidates_positive_and_negative_even_historical(name):
    result = verify(observation(name), (notice(),), context(), VerifierPolicy())
    changed = (revise(notice().dependency, epoch=2),)
    assert not is_current(result, observation_revision=1,
                          context=revise(context(), current_sources=changed),
                          policy=VerifierPolicy())
    assert not is_current(result, observation_revision=2,
                          context=context(), policy=VerifierPolicy())
    stale = verify(observation(name), (notice(),), revise(context(), current_sources=changed),
                   VerifierPolicy())
    assert stale.verdict == Verdict.REVIEW_REQUIRED


@pytest.mark.parametrize("status", [LiveStatus.FAILED, LiveStatus.EXPIRED])
def test_relabelling_failed_live_source_historical_does_not_restore_hold(status):
    result = verify(observation(), (notice(),), revise(context(), live_status=status),
                    VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED and not result.hold_eligible


def test_policy_override_reaches_live_freshness_and_is_bound_to_result():
    from batchbeacon.contracts import SourceMode
    ctx = revise(context(), mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED,
                 live_validated_at=context().computed_at - timedelta(seconds=20))
    default = verify(observation(), (notice(),), ctx, VerifierPolicy())
    tight = verify(observation(), (notice(),), ctx, VerifierPolicy(live_freshness_seconds=10))
    assert default.hold_eligible and not tight.hold_eligible
    assert default.policy_hash != tight.policy_hash


@pytest.mark.parametrize("value", [0, -1, True, "10", 1.5, float("inf")])
def test_invalid_policy_refused(value):
    with pytest.raises(ValidationError):
        VerifierPolicy(live_freshness_seconds=value)

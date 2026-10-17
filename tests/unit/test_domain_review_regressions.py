"""Independent-review reproductions; these are abstract unit inputs, not model gold."""

import json
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import (
    ActionRecord,
    ActionType,
    Comparison,
    Correction,
    DateRange,
    IdentifierKind,
    LiveStatus,
    ObservedIdentifier,
    Operator,
    SourceMode,
    TrustedIdentifier,
    ValueType,
    Verdict,
    VerifierPolicy,
)
from batchbeacon.domain.verifier import compare_identity, compare_predicate, is_current, verify
from tests.unit.domain_fixtures import (
    NOW,
    context,
    known,
    notice,
    observation,
    revise,
    source_ref,
)


def identity_rule(codes):
    return revise(notice().products[0].identity, identifiers=tuple(
        TrustedIdentifier(kind=kind, value=value, evidence=(source_ref(),))
        for kind, value in codes))


@pytest.mark.parametrize('second_kind', [IdentifierKind.PRODUCT_CODE, IdentifierKind.GTIN])
def test_conflicting_known_identifiers_cannot_hide_behind_one_match(second_kind):
    rule = identity_rule([(IdentifierKind.PRODUCT_CODE, '001A'), (second_kind, '001A')])
    obs = revise(observation().identity, identifiers=(
        ObservedIdentifier(kind=IdentifierKind.PRODUCT_CODE, observation=known('001A')),
        ObservedIdentifier(kind=second_kind, observation=known('OTHER')),
    ))
    assert compare_identity(rule, obs).outcome == Comparison.UNKNOWN
    src = revise(notice(), products=(revise(notice().products[0], identity=rule),))
    result = verify(revise(observation(), identity=obs), (src,), context(src), VerifierPolicy())
    assert result.verdict == Verdict.REVIEW_REQUIRED and not result.hold_eligible


def test_reviewed_code_alternatives_do_not_conflict():
    rule = identity_rule([(IdentifierKind.PRODUCT_CODE, '001A'),
                          (IdentifierKind.PRODUCT_CODE, '002B')])
    obs = revise(observation().identity, identifiers=(
        ObservedIdentifier(kind=IdentifierKind.PRODUCT_CODE, observation=known('002B')),))
    assert compare_identity(rule, obs).outcome == Comparison.MATCH


@pytest.mark.parametrize('failure', ['expired', 'failed', 'policy_changed', 'future_result'])
def test_read_currentness_checks_live_state_and_bound_policy_without_reverification(failure):
    policy = VerifierPolicy(live_freshness_seconds=10)
    initial = revise(context(), mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED,
                     live_validated_at=NOW)
    result = verify(observation(), (notice(),), initial, policy)
    assert is_current(result, observation_revision=1, context=initial, policy=policy)
    later = revise(initial, computed_at=NOW + timedelta(seconds=11))
    if failure == 'failed':
        later = revise(initial, live_status=LiveStatus.FAILED)
    elif failure == 'policy_changed':
        later = initial
        policy = VerifierPolicy(live_freshness_seconds=20)
    elif failure == 'future_result':
        later = revise(initial, computed_at=NOW - timedelta(seconds=1))
    assert not is_current(result, observation_revision=1, context=later, policy=policy)


def test_historical_currentness_does_not_inherit_live_time_to_live():
    policy = VerifierPolicy(live_freshness_seconds=10)
    result = verify(observation(), (notice(),), context(), policy)
    later = revise(context(), computed_at=NOW + timedelta(days=2))
    assert is_current(result, observation_revision=1, context=later, policy=policy)
    assert not is_current(result, observation_revision=1,
                          context=revise(later, live_status=LiveStatus.FAILED), policy=policy)


@pytest.mark.parametrize('state', [LiveStatus.FAILED, LiveStatus.EXPIRED])
def test_new_failure_bound_review_result_is_current_but_cannot_hold(state):
    policy = VerifierPolicy()
    initial = revise(context(), mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED,
                     live_validated_at=NOW)
    old = verify(observation(), (notice(),), initial, policy)
    failed = revise(initial, live_status=state, result_revision=2)
    result = verify(observation(), (notice(),), failed, policy)
    assert result.verdict == Verdict.REVIEW_REQUIRED and not result.hold_eligible
    assert is_current(result, observation_revision=1, context=failed, policy=policy)
    assert not is_current(old, observation_revision=1, context=failed, policy=policy)
    recovered = revise(failed, live_status=LiveStatus.VALIDATED,
                       live_validated_at=NOW + timedelta(seconds=1),
                       computed_at=NOW + timedelta(seconds=1))
    assert not is_current(result, observation_revision=1, context=recovered, policy=policy)


def test_implicit_expiry_requires_new_review_and_binds_failure_state():
    policy = VerifierPolicy(live_freshness_seconds=10)
    initial = revise(context(), mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED,
                     live_validated_at=NOW)
    old = verify(observation(), (notice(),), initial, policy)
    expired = revise(initial, computed_at=NOW + timedelta(seconds=10), result_revision=2)
    result = verify(observation(), (notice(),), expired, policy)
    assert result.reasons == ('FRESHNESS_EXPIRED',) and not result.hold_eligible
    assert not is_current(old, observation_revision=1, context=expired, policy=policy)
    assert is_current(result, observation_revision=1,
                      context=revise(expired, computed_at=NOW + timedelta(seconds=11)),
                      policy=policy)
    failed = revise(expired, live_status=LiveStatus.FAILED)
    assert not is_current(result, observation_revision=1, context=failed, policy=policy)


def test_new_source_changed_review_can_be_current_until_dependency_changes_again():
    policy = VerifierPolicy()
    changed = revise(notice().dependency, epoch=2)
    current = revise(context(), current_sources=(changed,), result_revision=2)
    result = verify(observation(), (notice(),), current, policy)
    assert 'SOURCE_VERSION_CHANGED' in result.reasons and not result.hold_eligible
    assert is_current(result, observation_revision=1, context=current, policy=policy)
    later = revise(current, current_sources=(revise(changed, epoch=3),))
    assert not is_current(result, observation_revision=1, context=later, policy=policy)


def test_an_unrelated_review_does_not_survive_a_later_live_failure():
    policy = VerifierPolicy()
    initial = revise(context(), mode=SourceMode.LIVE, live_status=LiveStatus.VALIDATED,
                     live_validated_at=NOW)
    source = revise(notice(), interpretation_complete=False)
    result = verify(observation(), (source,), initial, policy)
    assert result.verdict == Verdict.REVIEW_REQUIRED
    assert not is_current(result, observation_revision=1,
                          context=revise(initial, live_status=LiveStatus.FAILED), policy=policy)


@pytest.mark.parametrize('part', ['previous', 'replacement'])
def test_correction_audit_cannot_cite_unretained_source_evidence(part):
    obs = observation()
    old = obs.fields[0].observation
    values = dict(previous=old, replacement=old)
    values[part] = revise(old, evidence=(source_ref(),))
    correction = Correction(field='LOT', actor_session=obs.session_id,
                            recorded_at=NOW, **values)
    with pytest.raises(ValidationError):
        revise(obs, corrections=(correction,))


def test_final_correction_must_match_current_value_and_chain():
    obs = observation()
    correction = Correction(field='LOT', previous=known('old'), replacement=known('999999'),
                            actor_session=obs.session_id, recorded_at=NOW)
    with pytest.raises(ValidationError):
        revise(obs, corrections=(correction,))
    final = revise(correction, replacement=obs.fields[0].observation)
    assert revise(obs, corrections=(final,)).corrections == (final,)
    broken = revise(correction, previous=known('unrelated'),
                    replacement=obs.fields[0].observation)
    with pytest.raises(ValidationError):
        revise(obs, corrections=(correction, broken))


@pytest.mark.parametrize('name', ['Bertrand Pere & Fils Camembert au lait cru', 'Meadow Vale Brie'])
def test_reviewed_identity_uses_its_own_reviewed_capture(name):
    manifest = json.loads(Path('fixtures/synthetic/manifest.json').read_text())
    fixture = next(row for row in manifest['fixtures'] if row['identity'] == name)
    obs = observation(name)
    assert obs.captures[0].sha256 == fixture['sha256']
    assert obs.identity.name.evidence[0].sha256 == fixture['sha256']


def test_range_grid_preserves_operator_bounds_and_inclusivity():
    rule = revise(notice().products[0].predicates[1], operator=Operator.RANGE, values=(),
                  date_range=DateRange(lower=NOW.date(), upper=(NOW + timedelta(days=5)).date(),
                                       upper_inclusive=False))
    row = compare_predicate(rule, known('2026-10-19', ValueType.DATE))
    assert row.source_operator == Operator.RANGE
    assert row.source_date_range == rule.date_range
    assert row.source_applies


def test_serialized_result_rejects_contradictory_hold_eligibility():
    result = verify(observation(), (notice(),), context(), VerifierPolicy())
    with pytest.raises(ValidationError):
        revise(result, verdict=Verdict.REVIEW_REQUIRED)
    with pytest.raises(ValidationError):
        revise(result, checked_sources=(), candidates=())
    with pytest.raises(ValidationError):
        revise(result, computed_at=NOW.replace(tzinfo=None))


@pytest.mark.parametrize('change', ['actor', 'sources', 'naive_time'])
def test_action_record_rejects_locally_decidable_contradictions(change):
    action = ActionRecord(id='unit-action', session_id='unit-session',
                          incident_id='unit-incident', result_revision=1,
                          observation_revision=1, sources=(notice().dependency,),
                          action_type=ActionType.SIMULATED_HOLD, actor_session='unit-session',
                          confirmed_at=NOW, request_key='unit-key', payload_hash='a'*64)
    update = {'actor_session': 'different'} if change == 'actor' else (
        {'sources': ()} if change == 'sources' else {'confirmed_at': NOW.replace(tzinfo=None)})
    with pytest.raises(ValidationError):
        revise(action, **update)

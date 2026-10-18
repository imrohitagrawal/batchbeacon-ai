"""Actual fixed synthetic suite execution; no persisted attempts or real sources."""

import socket
from dataclasses import replace as dc_replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from batchbeacon import learning_evaluator as evaluator
from batchbeacon.contracts import ValueState
from batchbeacon.evidence_service import replace
from batchbeacon.guidance_policies import GuidanceField, GuidancePolicyId
from batchbeacon.learning_decisions import (
    ActivationBasis,
    GuidanceLimits,
    GuidanceUsage,
    LearningEvidence,
    activation_permitted,
    guidance_decision,
    rollback_binding,
)
from batchbeacon.learning_evaluator import (
    EvaluationPolicy,
    ExecutionStatus,
    LearningEvaluator,
    LearningExecution,
    LearningRejected,
    PreparedSuite,
)
from batchbeacon.retail_contracts import (
    EvaluationStatus,
    GuidanceBinding,
    LearningCase,
    LearningInvariant,
    VersionRef,
    policy_ref,
)
from batchbeacon.retail_projection import CapabilityObservation, CapabilityReason, CapabilityState

NOW = datetime(2026, 10, 18, 7, tzinfo=UTC)
BASE = GuidanceBinding(policy=policy_ref(GuidancePolicyId.V1), activation_revision=1)
CANDIDATE = policy_ref(GuidancePolicyId.V2)


@pytest.fixture
def policy():
    return EvaluationPolicy(
        limits=GuidanceLimits(shared_policy_hash="a" * 64, max_recaptures=2, max_verifications=6)
    )


@pytest.fixture
def suite(policy):
    return PreparedSuite.load(
        Path("fixtures/learning/inputs.json").read_bytes(),
        Path("fixtures/learning/expectations.json").read_bytes(),
        policy,
    )


def runner(suite, policy, **kwargs):
    return LearningEvaluator(
        suite,
        policy,
        wall_clock=kwargs.pop("wall_clock", lambda: NOW),
        monotonic_clock=kwargs.pop("monotonic_clock", lambda: 0.0),
        **kwargs,
    )


def test_actual_six_paired_cases_nine_variants_pass_without_uplift_claim(suite, policy):
    result = runner(suite, policy).run(BASE, CANDIDATE)
    assert result.status == ExecutionStatus.PASSED and not result.failures
    assert tuple(c.case for c in result.cases) == tuple(LearningCase)
    assert sum(len(c.variants) for c in result.cases) == 9
    assert result.invariants == tuple(LearningInvariant)
    for case in result.cases:
        assert case.passed
        for variant in case.variants:
            assert variant.passed
            assert variant.baseline.invariant_hashes == variant.candidate.invariant_hashes
            assert all(
                check.passed for b in (variant.baseline, variant.candidate) for check in b.checks
            )
    assert LearningExecution.model_validate_json(result.model_dump_json(round_trip=True)) == result
    assert len(result.model_dump_json().encode()) <= policy.retail.evaluation_bytes
    assert result.authority == "UNPRIVILEGED_SYNTHETIC_EXECUTION"
    assert "accuracy" not in result.model_dump_json().lower()


def test_guidance_changes_only_intended_wording_and_preserves_case_zeros_ambiguity(suite, policy):
    report = runner(suite, policy).run(BASE, CANDIDATE)
    lot = report.cases[0].variants[0]
    assert (
        lot.baseline.instructions[0].field
        == lot.candidate.instructions[0].field
        == GuidanceField.LOT
    )
    assert "leading zeros" in lot.baseline.instructions[0].text
    assert "one frame" in lot.candidate.instructions[0].text
    assert lot.baseline.instructions != lot.candidate.instructions
    date = suite.inputs.variants[1].observation.fields[1].observation
    assert date.state == ValueState.AMBIGUOUS and date.value is None and date.raw == "01/02/2026"
    assert suite.inputs.variants[4].observation.fields[0].observation.value == "000Ab"
    assert all(
        not v.baseline.instructions and not v.candidate.instructions
        for c in report.cases
        if c.case in (LearningCase.L03, LearningCase.L05, LearningCase.L06)
        for v in c.variants
    )


def test_execution_has_no_io_randomness_or_domain_mutation(suite, policy, monkeypatch):
    run = runner(suite, policy)
    before = (suite.inputs.model_dump_json(), policy.model_dump_json())

    def forbidden(*args, **kwargs):
        raise AssertionError("execution attempted forbidden port")

    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "write_bytes", forbidden)
    import secrets

    monkeypatch.setattr(secrets, "token_bytes", forbidden)
    a = run.run(BASE, CANDIDATE)
    assert run.run(BASE, CANDIDATE) == a
    assert (suite.inputs.model_dump_json(), policy.model_dump_json()) == before


@pytest.mark.parametrize("mutation", ["input_bytes", "expectation_bytes", "input_record"])
def test_prepared_fixed_input_cannot_be_rebound(suite, policy, mutation):
    with pytest.raises(ValueError):
        if mutation == "input_bytes":
            PreparedSuite.load(
                suite.original.replace(b"000Ab", b"000ab"), suite.expectations, policy
            )
        elif mutation == "expectation_bytes":
            PreparedSuite.load(suite.original, suite.expectations + b" ", policy)
        else:
            dc_replace(suite, inputs=replace(suite.inputs, variants=suite.inputs.variants[:-1]))


@pytest.mark.parametrize(
    "change", ["missing_hint", "missing_field", "extra_field", "stale_accepted", "rollback_rewinds"]
)
def test_meaningful_negative_controls_fail_actual_suite(suite, policy, monkeypatch, change):
    if change in {"missing_hint", "missing_field", "extra_field"}:
        original = evaluator.render_guidance

        def broken(p, binding, required):
            if binding.policy.id == GuidancePolicyId.V2:
                if change == "missing_hint":
                    binding = replace(binding, policy=BASE.policy)
                elif change == "missing_field":
                    required = ()
                elif not required:
                    required = (GuidanceField.LOT,)
            return original(p, binding, required)

        monkeypatch.setattr(evaluator, "render_guidance", broken)
    elif change == "stale_accepted":
        monkeypatch.setattr(evaluator, "activation_permitted", lambda *args, **kwargs: True)
    else:
        monkeypatch.setattr(
            evaluator, "rollback_binding", lambda current, **kw: kw["activated_from"]
        )
    report = runner(suite, policy).run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and report.failures == ("CHECK_FAILED",)
    assert any(not c.passed for c in report.cases)


def test_failed_branch_retains_already_executed_outputs(suite, policy, monkeypatch):
    run = runner(suite, policy)
    original = run._branch

    def error(fixture, binding, candidate, now):
        if fixture.case == LearningCase.L02:
            raise ValueError("synthetic internal value must not leak")
        return original(fixture, binding, candidate, now)

    monkeypatch.setattr(run, "_branch", error)
    report = run.run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and report.failures == ("EXECUTION_FAILED",)
    assert len(report.cases) == 1 and report.cases[0].passed
    assert "synthetic internal" not in report.model_dump_json()


@pytest.mark.parametrize("clock_kind", ["wall", "monotonic"])
def test_exact_deadline_is_nonpassing_and_retains_partial_branch(suite, policy, clock_kind):
    calls = [0]

    def clock():
        calls[0] += 1
        elapsed = 0 if calls[0] <= 2 else policy.retail.evaluation_deadline_seconds
        return NOW + timedelta(seconds=elapsed) if clock_kind == "wall" else float(elapsed)

    kwargs = {"wall_clock" if clock_kind == "wall" else "monotonic_clock": clock}
    report = runner(suite, policy, **kwargs).run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.EXPIRED and report.failures == ("DEADLINE_EXCEEDED",)
    assert len(report.cases) == 1
    variant = report.cases[0].variants[0]
    assert variant.baseline is not None and variant.candidate is None


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), True, "0"])
def test_invalid_monotonic_clock_rejected(suite, policy, invalid):
    with pytest.raises(LearningRejected, match="INVALID_CLOCK"):
        runner(suite, policy, monotonic_clock=lambda: invalid).run(BASE, CANDIDATE)


def test_backwards_clock_and_lease_boundary_do_not_pass(suite, policy):
    sequence = iter((0.0, 1.0, 0.5, 0.5))
    report = runner(suite, policy, monotonic_clock=lambda: next(sequence)).run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and report.failures == ("INVALID_CLOCK",)
    assert report.finished_at is None
    with pytest.raises(LearningRejected, match="EXPIRED_LEASE"):
        runner(suite, policy).run(BASE, CANDIDATE, lease_expires_at=NOW)
    with pytest.raises(LearningRejected, match="INVALID_LEASE"):
        runner(suite, policy).run(BASE, CANDIDATE, lease_expires_at=NOW.replace(tzinfo=None))


def test_effective_limits_reach_renderer_input_and_serialized_report(suite, policy):
    report = runner(suite, policy).run(BASE, CANDIDATE)
    size = len(report.model_dump_json().encode())
    exact = replace(policy, retail=replace(policy.retail, evaluation_bytes=size))
    assert len(runner(suite, exact).run(BASE, CANDIDATE).model_dump_json().encode()) == size
    with pytest.raises(LearningRejected, match="REPORT_BOUND_EXCEEDED") as error:
        runner(suite, replace(exact, retail=replace(exact.retail, evaluation_bytes=size - 1))).run(
            BASE, CANDIDATE
        )
    assert error.value.unaccepted.cases == report.cases
    short = replace(policy, retail=replace(policy.retail, max_instruction_chars=10))
    assert runner(suite, short).run(BASE, CANDIDATE).status == ExecutionStatus.FAILED
    n = len(suite.original) + len(suite.expectations)
    assert (
        PreparedSuite.load(suite.original, suite.expectations, replace(policy, input_bytes=n))
        == suite
    )
    with pytest.raises(ValueError, match="INPUT_BOUND_EXCEEDED"):
        PreparedSuite.load(suite.original, suite.expectations, replace(policy, input_bytes=n - 1))


def patched(record, **updates):
    return type(record).model_validate(record.model_dump(round_trip=True) | updates)


def test_pass_cannot_be_claimed_for_missing_variant_or_failed_check(suite, policy):
    report = runner(suite, policy).run(BASE, CANDIDATE)
    with pytest.raises(ValidationError):
        patched(report, cases=report.cases[:-1])
    case = report.cases[0]
    branch = case.variants[0].candidate
    bad = replace(branch, checks=(replace(branch.checks[0], passed=False), *branch.checks[1:]))
    with pytest.raises(ValidationError):
        replace(
            report,
            cases=(
                patched(case, variants=(patched(case.variants[0], candidate=bad),)),
                *report.cases[1:],
            ),
        )


def test_noninitial_baseline_revision_is_exercised(suite, policy):
    report = runner(suite, policy).run(replace(BASE, activation_revision=7), CANDIDATE)
    assert report.status == ExecutionStatus.PASSED and report.baseline.activation_revision == 7


def evidence(suite, policy, index=0):
    item = suite.inputs.variants[index]
    ctx = replace(item.context, computed_at=NOW)
    result = evaluator.verifier.verify(item.observation, (item.notice,), ctx, policy.verifier)
    return LearningEvidence(
        result=result,
        observation=item.observation,
        notices=(item.notice,),
        context=ctx,
        verifier_policy=policy.verifier,
    )


def capacity(e, **changes):
    value = CapabilityObservation(
        session_id=e.observation.session_id,
        capability="NEW_VERIFICATION",
        state=CapabilityState.AVAILABLE,
        reason=CapabilityReason.OBSERVED,
        observed_at=NOW,
        valid_until=NOW + timedelta(seconds=60),
    )
    return replace(value, **changes)


@pytest.mark.parametrize(
    "condition",
    ["own_exhausted", "verification_exhausted", "unavailable", "unknown", "stale", "foreign"],
)
def test_actual_guidance_capacity_denial_preserves_review_and_counts(suite, policy, condition):
    e = evidence(suite, policy)
    usage = GuidanceUsage(acquisitions=1, verifications=1)
    resource = capacity(e)
    if condition == "own_exhausted":
        usage = replace(usage, acquisitions=1 + policy.limits.max_recaptures)
    elif condition == "verification_exhausted":
        usage = replace(usage, verifications=policy.limits.max_verifications)
    elif condition == "unavailable":
        resource = replace(
            resource, state=CapabilityState.UNAVAILABLE, reason=CapabilityReason.BACKEND_UNAVAILABLE
        )
    elif condition == "unknown":
        resource = None
    elif condition == "stale":
        resource = replace(resource, observed_at=NOW - timedelta(seconds=60), valid_until=NOW)
    else:
        resource = replace(resource, session_id="f" * 32)
    before = usage.model_dump_json()
    decision = guidance_decision(
        e.result,
        e.observation,
        e.notices,
        e.context,
        e.verifier_policy,
        usage=usage,
        limits=policy.limits,
        capability=resource,
        read_policy=policy.read,
    )
    assert decision.current and decision.review_request_eligible and not decision.hold_eligible
    assert not decision.requested_fields and usage.model_dump_json() == before


def activation_basis(e):
    def ref(name):
        return VersionRef(id=name, revision=1, content_hash="a" * 64)

    return ActivationBasis(
        candidate=ref("candidate"),
        evaluation=ref("evaluation"),
        suite=ref("suite"),
        inputs=ref("inputs"),
        evaluator=ref("evaluator"),
        base=BASE,
        proposed_policy_hash=CANDIDATE.content_hash,
        evidence_basis_hashes=(e.basis(),),
    )


@pytest.mark.parametrize(
    "field",
    [
        "candidate",
        "evaluation",
        "suite",
        "inputs",
        "evaluator",
        "base",
        "proposed_policy_hash",
        "evidence_basis_hashes",
    ],
)
def test_exact_activation_binding_changes_deny_with_valid_counterpart(suite, policy, field):
    e = evidence(suite, policy, 7)
    target = activation_basis(e)
    options = dict(
        evaluation_status=EvaluationStatus.PASSED, evidence=(e,), retail_policy=policy.retail
    )
    assert activation_permitted(target, target, **options)
    if field == "base":
        changed = replace(target, base=replace(BASE, activation_revision=2))
    elif field == "proposed_policy_hash":
        changed = replace(target, proposed_policy_hash="f" * 64)
    elif field == "evidence_basis_hashes":
        changed = replace(target, evidence_basis_hashes=("f" * 64,))
    else:
        changed = replace(target, **{field: replace(getattr(target, field), content_hash="f" * 64)})
    assert not activation_permitted(target, changed, **options)


def test_semantic_source_change_fails_even_when_all_bindings_are_recomputed(suite, policy):
    e = evidence(suite, policy, 7)
    changed = replace(e, notices=(replace(e.notices[0], review=None),))
    target = activation_basis(changed)
    assert not activation_permitted(
        target,
        target,
        evaluation_status=EvaluationStatus.PASSED,
        evidence=(changed,),
        retail_policy=policy.retail,
    )


def test_rollback_content_restoration_never_restores_old_revision(suite, policy):
    e = evidence(suite, policy, 7)
    old = activation_basis(e)
    applied = GuidanceBinding(policy=CANDIDATE, activation_revision=2)
    rolled = rollback_binding(applied, activated_from=BASE, activated_to=applied)
    assert rolled.policy == BASE.policy and rolled.activation_revision == 3
    assert not activation_permitted(
        old,
        replace(old, base=rolled),
        evaluation_status=EvaluationStatus.PASSED,
        evidence=(e,),
        retail_policy=policy.retail,
    )
    with pytest.raises(ValueError, match="ROLLBACK_BINDING_CHANGED"):
        rollback_binding(rolled, activated_from=BASE, activated_to=applied)


@pytest.mark.parametrize(
    "field,value", [("input_bytes", 0), ("input_bytes", True), ("input_bytes", "262144")]
)
def test_invalid_configuration_rejected(policy, field, value):
    with pytest.raises(ValidationError):
        replace(policy, **{field: value})


@pytest.mark.parametrize(
    "field,value", [("max_recaptures", -1), ("max_verifications", 0), ("max_verifications", True)]
)
def test_invalid_capacity_policy_rejected(policy, field, value):
    with pytest.raises(ValidationError):
        replace(policy.limits, **{field: value})


def test_effective_allowance_and_deadline_overrides_reach_execution(suite, policy):
    no_recapture = replace(policy, limits=replace(policy.limits, max_recaptures=0))
    report = runner(suite, no_recapture).run(BASE, CANDIDATE)
    assert report.configuration_hash == no_recapture.digest()
    assert report.status == ExecutionStatus.FAILED
    assert not report.cases[0].passed
    shorter = replace(policy, retail=replace(policy.retail, evaluation_deadline_seconds=1))
    ticks = iter((0.0, 0.0, 1.0, 1.0))
    report = runner(suite, shorter, monotonic_clock=lambda: next(ticks)).run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.EXPIRED
    assert report.deadline_at - report.started_at == timedelta(seconds=1)


def test_final_serialization_deadline_cannot_return_pass(suite, policy):
    calls = [0]

    def clock():
        calls[0] += 1
        return float(policy.retail.evaluation_deadline_seconds if calls[0] >= 30 else 0)

    report = runner(suite, policy, monotonic_clock=clock).run(BASE, CANDIDATE)
    assert all(c.passed for c in report.cases)
    assert report.status == ExecutionStatus.EXPIRED


def test_candidate_date_normalization_shortcut_fails_actual_oracle(suite, policy, monkeypatch):
    run = runner(suite, policy)
    original = run._branch

    def shortcut(fixture, binding, candidate, now):
        if fixture.case == LearningCase.L02 and binding.policy.id == GuidancePolicyId.V2:
            date_field = fixture.observation.fields[1]
            date_field = replace(
                date_field,
                observation=replace(
                    date_field.observation, state=ValueState.KNOWN, value="2026-10-17"
                ),
            )
            fixture = replace(
                fixture,
                observation=replace(
                    fixture.observation, fields=(fixture.observation.fields[0], date_field)
                ),
            )
        return original(fixture, binding, candidate, now)

    monkeypatch.setattr(run, "_branch", shortcut)
    report = run.run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and not report.cases[1].passed
    variant = report.cases[1].variants[0]
    assert variant.baseline.invariant_hashes != variant.candidate.invariant_hashes


def test_policy_pair_never_silently_falls_back(suite, policy):
    for base, candidate in ((BASE, BASE.policy), (None, CANDIDATE), (BASE, CANDIDATE.model_dump())):
        with pytest.raises(LearningRejected, match="UNSUPPORTED_POLICY_PAIR"):
            runner(suite, policy).run(base, candidate)


@pytest.mark.parametrize(
    "status",
    [EvaluationStatus.RUNNING, EvaluationStatus.FAILED, EvaluationStatus.EXPIRED, "PASSED", True],
)
def test_only_typed_passing_status_can_qualify_for_binding_predicate(suite, policy, status):
    e = evidence(suite, policy, 7)
    target = activation_basis(e)
    assert not activation_permitted(
        target, target, evaluation_status=status, evidence=(e,), retail_policy=policy.retail
    )


def test_all_supported_evidence_must_be_current_and_exact(suite, policy):
    e = evidence(suite, policy, 7)
    other = evidence(suite, policy, 8)
    target = replace(activation_basis(e), evidence_basis_hashes=(e.basis(), other.basis()))
    options = dict(evaluation_status=EvaluationStatus.PASSED, retail_policy=policy.retail)
    assert activation_permitted(target, target, evidence=(e, other), **options)
    assert not activation_permitted(target, target, evidence=(other, e), **options)
    assert not activation_permitted(target, target, evidence=(e,), **options)
    changed = replace(other, observation=replace(other.observation, revision=2))
    rebound = replace(target, evidence_basis_hashes=(e.basis(), changed.basis()))
    assert not activation_permitted(rebound, rebound, evidence=(e, changed), **options)
    lower = replace(policy.retail, max_support_refs=1)
    assert not activation_permitted(
        target,
        target,
        evidence=(e, other),
        evaluation_status=EvaluationStatus.PASSED,
        retail_policy=lower,
    )


def test_clock_provider_failure_preserves_partial_output_without_raw_error(suite, policy):
    calls = [0]

    def clock():
        calls[0] += 1
        if calls[0] > 2:
            raise RuntimeError("internal clock provider detail")
        return 0.0

    report = runner(suite, policy, monotonic_clock=clock).run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and report.failures == ("INVALID_CLOCK",)
    assert report.cases[0].variants[0].baseline is not None
    assert "internal clock" not in report.model_dump_json()


def test_initial_clock_provider_failure_is_safe_rejection(suite, policy):
    def clock():
        raise RuntimeError("internal clock provider detail")

    with pytest.raises(LearningRejected, match="INVALID_CLOCK"):
        runner(suite, policy, wall_clock=clock).run(BASE, CANDIDATE)


def test_unexpected_stage_failure_retains_prior_outputs(suite, policy, monkeypatch):
    run = runner(suite, policy)
    original = run._branch

    def broken(fixture, *args):
        if fixture.case == LearningCase.L02:
            raise RuntimeError("internal stage detail")
        return original(fixture, *args)

    monkeypatch.setattr(run, "_branch", broken)
    report = run.run(BASE, CANDIDATE)
    assert report.status == ExecutionStatus.FAILED and report.failures == ("EXECUTION_FAILED",)
    assert len(report.cases) == 1 and report.cases[0].passed

"""Owned loop with actual pure evaluation and installed SDK/fake RPC persistence."""

from datetime import timedelta
from pathlib import Path

import pytest

from batchbeacon.guest_service import GuestDenied
from batchbeacon.guidance_policies import GuidancePolicyId
from batchbeacon.learning_decisions import GuidanceLimits
from batchbeacon.learning_evaluator import EvaluationPolicy, LearningEvaluator, PreparedSuite
from batchbeacon.learning_service import ActivationConfirmation, LearningState, RollbackConfirmation
from batchbeacon.retail_contracts import EvaluationStatus, FeedbackDetail
from batchbeacon.retail_projection import CapabilityObservation, CapabilityReason, CapabilityState
from tests.unit.test_extraction_proposal import unknown
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import saved
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_reviewed_extraction import acquire, build_reviewed
from tests.unit.test_shared_admission import env as env  # noqa


@pytest.fixture
def learning(setup, env):
    def configure(stores, actions, shared):
        p = EvaluationPolicy(
            retail=stores.guest_policy.retail, limits=GuidanceLimits.from_shared(shared.policy)
        )
        suite = PreparedSuite.load(
            Path("fixtures/learning/inputs.json").read_bytes(),
            Path("fixtures/learning/expectations.json").read_bytes(),
            p,
        )
        evaluator = LearningEvaluator(
            suite, p, wall_clock=lambda: setup[5][0], monotonic_clock=lambda: 0.0
        )

        def capacity(session):
            now = setup[5][0]
            return CapabilityObservation(
                session_id=session.scope.session_id,
                capability="NEW_VERIFICATION",
                state=CapabilityState.AVAILABLE,
                reason=CapabilityReason.OBSERVED,
                observed_at=now,
                valid_until=now + timedelta(seconds=p.read.capability_validity_seconds),
            )

        from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy

        stores.enable_retail(RetailProjector(actions, shared.policy, RetailReadPolicy()))
        stores.enable_learning(actions.evidence, shared.policy, evaluator, capability=capacity)

    c = build_reviewed(setup, env, (0,), configure=configure)
    c[5][0]["label"]["lot"] = unknown(kind="TEXT")
    status = acquire(c)
    assert status.current and status.state == "REVIEW_REQUIRED"
    return c, setup[0].learning


def candidate(learning):
    c, s = learning
    token = c[2]
    incident = c[1].incident_id
    request = s.guidance(token, incident, "guidance")
    feedback = s.feedback(token, incident, "feedback", FeedbackDetail.LOT_CODE_UNCLEAR, request.id)
    proposal = s.candidate(token, "candidate", (feedback.id,))
    return request, feedback, proposal


def test_owned_complete_loop_actual_execution_future_wording_rollback_and_cold_read(learning):
    c, s = learning
    token = c[2]
    incident = c[1].incident_id
    original_usage = saved(c[3], "usage", c[6].capability_hash)
    request, feedback, proposal = candidate(learning)
    attempt = s.evaluate(token, "evaluate", proposal.id)
    assert attempt.status == EvaluationStatus.PASSED
    assert sum(len(case.variants) for case in attempt.execution.cases) == 9
    assert s.evaluate(token, "evaluate", proposal.id) == attempt
    basis = s.prepare_activation(token, attempt.id)
    confirm = ActivationConfirmation(basis=basis, explicit_confirmation=True)
    transition = s.activate(token, "activate", confirm)
    assert s.activate(token, "duplicate-activate", confirm) == transition
    future = s.guidance(token, incident, "future-guidance")
    assert "glare" in future.instructions[0].text
    assert future.binding.activation_revision == 2 and request.binding.activation_revision == 1
    rollback = s.rollback(
        token,
        "rollback",
        RollbackConfirmation(**s.prepare_rollback(token).model_dump(), explicit_confirmation=True),
    )
    assert rollback.next.activation_revision == 3
    restored = s.guidance(token, incident, "restored-guidance")
    assert restored.instructions == request.instructions
    state = s.read(token)
    assert state.active.policy.id == GuidancePolicyId.V1 and state.active.activation_revision == 3
    assert (
        state.requests[0] == request and len(state.evaluations) == 1 and len(state.transitions) == 2
    )
    assert (
        LearningState.model_validate_json(state.model_dump_json(exclude_computed_fields=True))
        == state
    )
    assert saved(c[3], "learning", c[6].capability_hash) == state
    assert saved(c[3], "usage", c[6].capability_hash) == original_usage
    assert len(c[4]) == 2  # No model calls during the entire learning loop.


def test_missing_enrollment_foreign_scope_and_expiry_fail_closed(learning):
    c, s = learning
    token = c[2]
    other, other_session = c[3][2].issue()
    _, _, proposal = candidate(learning)
    with pytest.raises(GuestDenied):
        s.evaluate(other, "foreign", proposal.id)
    name = c[3][0].name("learning", other_session.capability_hash)
    c[3][1].docs.pop(name)
    with pytest.raises(GuestDenied):
        s.read(other)
    c[3][5][0] = c[6].scope.expires_at
    with pytest.raises(GuestDenied):
        s.read(token)


def test_unsupported_feedback_cannot_change_policy_and_missing_capacity_closes_guidance(learning):
    c, s = learning
    token = c[2]
    incident = c[1].incident_id
    feedback = s.feedback(token, incident, "disputed", FeedbackDetail.EXTRACTED_VALUE_DISPUTED)
    with pytest.raises(GuestDenied):
        s.candidate(token, "no-safe", (feedback.id,))
    s.capability = None
    with pytest.raises(GuestDenied):
        s.guidance(token, incident, "no-capacity")
    assert s.read(token).active.activation_revision == 1


def test_actual_failed_evaluation_preserved_and_changed_base_denies_activation(
    learning, monkeypatch
):
    c, s = learning
    token = c[2]
    _, _, proposal = candidate(learning)
    original = s.evaluator.run

    def interrupted(*a, **kw):
        raise RuntimeError("test worker interruption")

    monkeypatch.setattr(s.evaluator, "run", interrupted)
    failed = s.evaluate(token, "interrupted", proposal.id)
    assert failed.status == EvaluationStatus.FAILED and failed.failure == "WORKER_INTERRUPTED"
    monkeypatch.setattr(s.evaluator, "run", original)
    c[3][5][0] += timedelta(seconds=s.policy.evaluation_interval_seconds)
    passed = s.evaluate(token, "explicit-new-attempt", proposal.id)
    confirm = ActivationConfirmation(
        basis=s.prepare_activation(token, passed.id), explicit_confirmation=True
    )
    s.activate(token, "activation", confirm)
    s.rollback(
        token,
        "rollback",
        RollbackConfirmation(**s.prepare_rollback(token).model_dump(), explicit_confirmation=True),
    )
    # Historical duplicate is returned; it never reapplies the policy.
    s.activate(token, "old-replay", confirm)
    assert s.read(token).active.activation_revision == 3
    assert len(s.read(token).evaluations) == 2


def test_changed_confirmation_hashes_are_denied_even_after_logical_activation(learning):
    from batchbeacon.learning_service import changed

    c, s = learning
    token = c[2]
    _, _, proposal = candidate(learning)
    attempt = s.evaluate(token, "evaluate", proposal.id)
    basis = s.prepare_activation(token, attempt.id)
    confirm = ActivationConfirmation(basis=basis, explicit_confirmation=True)
    s.activate(token, "activate", confirm)
    for field, value in [
        ("proposed_policy_hash", "0" * 64),
        ("evidence_basis_hashes", ("0" * 64,)),
    ]:
        altered = ActivationConfirmation(
            basis=changed(basis, **{field: value}), explicit_confirmation=True
        )
        with pytest.raises(GuestDenied, match="learning_confirmation_changed"):
            s.activate(token, "changed-" + field, altered)
    assert len(s.read(token).transitions) == 1


def test_receipts_reserve_rollback_and_attempt_numbers_never_reset(learning, monkeypatch):
    from batchbeacon.learning_service import LearningPolicy

    c, s = learning
    with pytest.raises(ValueError, match="receipt capacity"):
        LearningPolicy(max_receipts=5).validate_capacity(s.guest.policy.retail)
    _, _, proposal = candidate(learning)

    def interrupted(*args, **kwargs):
        raise RuntimeError("interrupted")

    monkeypatch.setattr(s.evaluator, "run", interrupted)
    for number in range(1, 5):
        c[3][5][0] += timedelta(seconds=s.policy.evaluation_interval_seconds)
        result = s.evaluate(c[2], f"attempt-{number}", proposal.id)
        assert result.attempt_number == number and result.status == EvaluationStatus.FAILED
    with pytest.raises(GuestDenied):
        s.evaluate(c[2], "attempt-5", proposal.id)
    assert [e.attempt_number for e in s.read(c[2]).evaluations] == [1, 2, 3, 4]


def test_durable_refresh_and_mutation_throttles_preserve_same_key_recovery(learning):
    from batchbeacon.learning_service import LearningService

    c, s = learning
    token = c[2]
    state = s.refresh(token, "refresh-1")
    cold = LearningService(
        s.store, s.evidence, s.shared_policy, s.evaluator, s.policy, capability=s.capability
    )
    assert cold.read(token) == state
    for key, code in [("refresh-1", "already_admitted"), ("refresh-2", "rate_limited")]:
        with pytest.raises(GuestDenied, match=code):
            cold.refresh(token, key)
    request, feedback, proposal = candidate(learning)
    assert (
        cold.feedback(token, c[1].incident_id, "feedback", feedback.detail, request.id) == feedback
    )
    with pytest.raises(GuestDenied, match="mutation_rate_limited"):
        cold.feedback(token, c[1].incident_id, "too-fast", feedback.detail, request.id)
    attempt = s.evaluate(token, "evaluate", proposal.id)
    assert cold.evaluate(token, "evaluate", proposal.id) == attempt
    with pytest.raises(GuestDenied, match="mutation_rate_limited"):
        cold.evaluate(token, "new-too-fast", proposal.id)
    c[3][5][0] += timedelta(
        seconds=max(
            s.policy.refresh_interval_seconds,
            s.policy.evaluation_interval_seconds,
            s.policy.feedback_interval_seconds,
        )
    )
    assert len(cold.refresh(token, "refresh-2").refresh_keys) == 2
    assert cold.evaluate(token, "new-after-interval", proposal.id).attempt_number == 2
    assert (
        cold.feedback(
            token, c[1].incident_id, "feedback-after-interval", feedback.detail, request.id
        ).id
        != feedback.id
    )
    assert len(c[4]) == 2


def test_learning_rate_configuration_requires_finite_positive_values_and_capacity():
    from pydantic import ValidationError

    from batchbeacon.learning_service import LearningPolicy
    from batchbeacon.retail_contracts import RetailPolicy

    for field in (
        "refresh_interval_seconds",
        "feedback_interval_seconds",
        "evaluation_interval_seconds",
    ):
        for value in (0.0, -1.0, float("inf"), float("nan"), "2"):
            with pytest.raises(ValidationError):
                LearningPolicy(**{field: value})
    with pytest.raises(ValueError, match="base capacity"):
        LearningPolicy(max_refreshes=1000).validate_capacity(RetailPolicy())

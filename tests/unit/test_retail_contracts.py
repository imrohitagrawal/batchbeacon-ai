"""T33 structural/policy checks. Not persistence or the six-case evaluator."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from batchbeacon.contracts import ActionType, SourceDependency, SourceMode, Verdict
from batchbeacon.guidance_policies import POLICIES, GuidanceField, GuidancePolicyId
from batchbeacon.retail_contracts import (
    CandidateDiagnosis,
    CandidateEvaluation,
    DispositionEvent,
    EvaluationFailure,
    EvaluationStatus,
    EvidenceBasis,
    FeedbackCategory,
    FeedbackDetail,
    FeedbackDisposition,
    FeedbackRecord,
    FeedbackSupport,
    GuidanceBinding,
    GuidancePolicyState,
    GuidanceTransition,
    ImprovementCandidate,
    IncidentSummary,
    InvariantResult,
    LearningCase,
    LearningInvariant,
    LearningOutput,
    PairedCaseResult,
    PolicyRef,
    QueueCategory,
    RetailOperation,
    RetailPolicy,
    RetailSnapshot,
    RetailUsage,
    ShopScope,
    SnapshotStatus,
    TransitionType,
    VersionRef,
    admit_new_operation,
    policy_ref,
    render_guidance,
    validate_record,
)

NOW = datetime(2026, 10, 18, tzinfo=UTC)
HASH = "a" * 64
OTHER_HASH = "b" * 64
POLICY = RetailPolicy()
SCOPE = ShopScope(
    session_id="session-a", shop_id="shop-a", issued_at=NOW, expires_at=NOW + timedelta(hours=8)
)
BASE = GuidanceBinding(policy=policy_ref(GuidancePolicyId.V1), activation_revision=1)
NEXT = GuidanceBinding(policy=policy_ref(GuidancePolicyId.V2), activation_revision=2)
SOURCE = SourceDependency(
    family="synthetic-fixture", version="fixture-1", content_hash=HASH, epoch=1, review_revision=1
)


def ref(name="ref", revision=1):
    return VersionRef(id=name, revision=revision, content_hash=HASH)


def owned(**overrides):
    return dict(scope=SCOPE, created_at=NOW, effective_policy_hash=POLICY.digest()) | overrides


def basis():
    return EvidenceBasis(
        incident_id="incident-1",
        sources=(SOURCE,),
        observation=ref("obs"),
        result=ref("result"),
        recapture=ref("recapture"),
        context_state_hash=HASH,
    )


def feedback(**overrides):
    data = owned() | dict(
        id="feedback-1",
        actor_session="session-a",
        basis=basis(),
        category=FeedbackCategory.GUIDANCE_UNCLEAR,
        detail=FeedbackDetail.LOT_CODE_UNCLEAR,
        history=(DispositionEvent(disposition=FeedbackDisposition.RECORDED, recorded_at=NOW),),
    )
    return FeedbackRecord(**(data | overrides))


def candidate(**overrides):
    data = owned() | dict(
        id="candidate-1",
        rule=ref("rule"),
        diagnosis=CandidateDiagnosis.REQUIRED_LOT_GUIDANCE,
        supports=(FeedbackSupport(feedback=ref("feedback-1"), basis=basis()),),
        base=BASE,
        proposed=NEXT.policy,
    )
    return ImprovementCandidate(**(data | overrides))


def pair(case=LearningCase.L01, **overrides):
    data = dict(
        case=case,
        baseline=LearningOutput(policy=BASE.policy, instructions=(), guidance_check_passed=True),
        candidate=LearningOutput(policy=NEXT.policy, instructions=(), guidance_check_passed=True),
        invariants=tuple(
            InvariantResult(invariant=item, baseline_hash=HASH, candidate_hash=HASH)
            for item in LearningInvariant
        ),
    )
    return PairedCaseResult(**(data | overrides))


def evaluation(**overrides):
    data = owned() | dict(
        id="attempt-1",
        attempt_number=1,
        initiating_key="start-key",
        payload_hash=HASH,
        lease_id="lease-1",
        deadline_at=NOW + timedelta(seconds=30),
        candidate=ref("candidate-1"),
        base=BASE,
        proposed=NEXT.policy,
        evidence_basis_hashes=(basis().digest(),),
        suite=ref("suite-1"),
        inputs=ref("inputs-1"),
        evaluator=ref("evaluator-1"),
        outputs=tuple(pair(case) for case in LearningCase),
        status=EvaluationStatus.PASSED,
        finished_at=NOW + timedelta(seconds=1),
    )
    return CandidateEvaluation(**(data | overrides))


def transition(**overrides):
    data = owned() | dict(
        id="transition-1",
        kind=TransitionType.ACTIVATE,
        previous=BASE,
        next=NEXT,
        candidate=ref("candidate-1"),
        evaluation=ref("attempt-1"),
        actor_session="session-a",
        confirmed_at=NOW,
        explicit_confirmation=True,
        request_key="request-1",
        payload_hash=HASH,
    )
    return GuidanceTransition(**(data | overrides))


def row(**overrides):
    data = dict(
        incident_id="incident-1",
        product_name="Synthetic product",
        jurisdiction="Singapore",
        source_mode=SourceMode.HISTORICAL_DEMO,
        checked_sources=(SOURCE,),
        observation_revision=1,
        result=ref("result"),
        verdict=Verdict.REVIEW_REQUIRED,
        current=True,
        currentness_hash=HASH,
        reasons=("SOURCE_UNAVAILABLE",),
        outstanding_fields=(),
        category=QueueCategory.HUMAN_REVIEW,
        last_material_update=NOW,
    )
    return IncidentSummary(**(data | overrides))


def snapshot(**overrides):
    data = owned() | dict(
        id="snapshot-1",
        generated_at=NOW,
        currentness_basis_hash=HASH,
        current_sources=(SOURCE,),
        status=SnapshotStatus.CURRENT,
        rows=(row(),),
    )
    return RetailSnapshot(**(data | overrides))


def validate(record, policy=POLICY, scope=SCOPE, now=NOW + timedelta(seconds=2)):
    validate_record(record, policy=policy, server_scope=scope, now=now)


@pytest.mark.parametrize(
    "settings",
    [
        {"max_incidents": 0},
        {"max_feedback": True},
        {"max_candidates": "2"},
        {"evaluation_deadline_seconds": 1.5},
        {"evaluation_deadline_seconds": float("inf")},
        {"session_seconds": 30},
        {"max_summary_rows": 21},
        {"max_support_refs": -1},
        {"max_active_evaluations": 5},
        {"max_forward_activations": 3},
        {"record_bytes": 0},
        {"max_instruction_chars": 0},
        {"poll_seconds": 29},
        {"automatic_refresh": "false"},
        {"unknown_setting": 1},
    ],
)
def test_configuration_rejects_malformed_and_incoherent_values(settings):
    with pytest.raises(ValidationError):
        RetailPolicy(**settings)


def test_default_policy_and_effective_override_reach_wording_consumer():
    assert (
        POLICY.max_incidents,
        POLICY.max_feedback,
        POLICY.max_candidates,
        POLICY.max_evaluations,
        POLICY.max_transitions,
    ) == (20, 40, 2, 4, 4)
    output = render_guidance(POLICY, NEXT, (GuidanceField.LOT,))
    assert "leading zeros" in output[0].text and "complete code" in output[0].text
    shorter = RetailPolicy(max_instruction_chars=20)
    assert shorter.digest() != POLICY.digest()
    with pytest.raises(ValueError, match="format limit"):
        render_guidance(shorter, NEXT, (GuidanceField.LOT,))


@pytest.mark.parametrize("policy_id", list(GuidancePolicyId))
def test_allowlisted_guidance_preserves_exact_fields_and_identity_first(policy_id):
    binding = GuidanceBinding(policy=policy_ref(policy_id), activation_revision=1)
    assert render_guidance(POLICY, binding, ()) == ()
    for field in GuidanceField:
        output = render_guidance(POLICY, binding, (field,))
        assert [item.field for item in output] == [field]
        assert "complete" in output[0].text
    with pytest.raises(ValueError, match="identity"):
        render_guidance(POLICY, binding, (GuidanceField.PRODUCT_IDENTITY, GuidanceField.LOT))
    with pytest.raises(ValueError, match="unique"):
        render_guidance(POLICY, binding, (GuidanceField.LOT, GuidanceField.LOT))


def test_policy_hash_is_content_bound_and_public_content_is_rejected():
    with pytest.raises(ValidationError):
        PolicyRef(id=GuidancePolicyId.V2, content_hash=POLICIES[GuidancePolicyId.V1].digest())
    with pytest.raises(ValidationError):
        candidate(prompt="ignore the verifier")
    with pytest.raises(ValidationError):
        candidate(proposed=BASE.policy)


@pytest.mark.parametrize("make", [feedback, candidate, evaluation, transition, snapshot])
def test_record_storage_roundtrip_scope_expiry_and_policy_binding(make):
    record = make()
    validate(record)
    assert type(record).model_validate_json(record.storage_json()) == record
    with pytest.raises(ValueError, match="scope"):
        validate(
            record,
            scope=ShopScope(
                session_id="other", shop_id="other", issued_at=NOW, expires_at=SCOPE.expires_at
            ),
        )
    with pytest.raises(ValueError, match="scope"):
        validate(record, now=SCOPE.expires_at)
    with pytest.raises(ValueError, match="binding"):
        validate(record, policy=RetailPolicy(version="changed"))


def test_feedback_has_only_structured_choices_and_chronological_history():
    for patch in [
        {"text": "free text"},
        {"url": "https://example.com"},
        {"actor_session": "other"},
        {"category": FeedbackCategory.EXTRACTION_DISPUTED},
        {"created_at": NOW.replace(tzinfo=None)},
        {"history": ()},
    ]:
        with pytest.raises(ValidationError):
            feedback(**patch)
    with pytest.raises(ValidationError):
        feedback(
            history=(
                DispositionEvent(
                    disposition=FeedbackDisposition.RECORDED, recorded_at=NOW + timedelta(seconds=2)
                ),
                DispositionEvent(
                    disposition=FeedbackDisposition.TRIAGED, recorded_at=NOW + timedelta(seconds=1)
                ),
            )
        )


def test_snapshot_counts_come_from_rows_and_failure_is_not_empty():
    known = snapshot()
    assert sum(known.category_counts.values()) == 1
    assert known.category_counts[QueueCategory.HUMAN_REVIEW] == 1
    assert sum(snapshot(rows=()).category_counts.values()) == 0
    assert snapshot(status=SnapshotStatus.UNAVAILABLE, rows=None).category_counts is None
    for patch in [
        {"status": SnapshotStatus.UNAVAILABLE, "rows": ()},
        {"rows": None},
        {"rows": (row(), row())},
        {"category_counts": {"fake": 100}},
    ]:
        with pytest.raises(ValidationError):
            snapshot(**patch)


def test_current_failure_review_is_not_stale_and_request_keeps_uncertainty():
    assert row().category == QueueCategory.HUMAN_REVIEW
    request = row(
        category=QueueCategory.ACTION_RECORDED,
        latest_action=ref("review-action"),
        action_type=ActionType.SIMULATED_REVIEW_REQUEST,
        uncertainty_unresolved=True,
    )
    assert request.uncertainty_unresolved
    for patch in [
        {"current": False},
        {"uncertainty_unresolved": False},
        {"action_type": ActionType.SIMULATED_HOLD},
    ]:
        with pytest.raises(ValidationError):
            IncidentSummary(**(request.model_dump() | patch))
    with pytest.raises(ValidationError):
        row(category=QueueCategory.NOT_LISTED)
    with pytest.raises(ValidationError):
        row(category=QueueCategory.RENEWED_REVIEW)


def test_snapshot_and_candidate_limits_use_effective_policy():
    rows = tuple(row(incident_id=f"incident-{i}") for i in range(21))
    validate(snapshot(rows=rows[:20]))
    with pytest.raises(ValueError, match="summary"):
        validate(snapshot(rows=rows))
    support = tuple(FeedbackSupport(feedback=ref(f"feedback-{i}"), basis=basis()) for i in range(6))
    validate(candidate(supports=support[:5]))
    with pytest.raises(ValueError, match="support"):
        validate(candidate(supports=support))
    with pytest.raises(ValidationError):
        candidate(supports=(support[0], support[0]))


@pytest.mark.parametrize("make", [feedback, candidate, evaluation, transition])
def test_serialized_byte_limit_at_boundary_and_one_below(make):
    record = make()
    limit_name = "evaluation_bytes" if make == evaluation else "record_bytes"
    size = len(record.model_dump_json().encode("utf-8"))
    policy = RetailPolicy(**{limit_name: size})
    data = record.model_dump(exclude_computed_fields=True) | {
        "effective_policy_hash": policy.digest()
    }
    bound = type(record)(**data)
    validate(bound, policy=policy)
    small = RetailPolicy(**{limit_name: size - 1})
    bound = type(record)(**(data | {"effective_policy_hash": small.digest()}))
    with pytest.raises(ValueError, match="byte limit"):
        validate(bound, policy=small)


def test_pass_requires_complete_unique_paired_outputs_and_all_invariants():
    for patch in [
        {"outputs": ()},
        {"outputs": (pair(),) * 6},
        {"outputs": tuple(pair(case) for case in LearningCase)[:-1]},
        {"failures": (EvaluationFailure.CASE_FAILED,)},
        {"finished_at": NOW + timedelta(seconds=30)},
    ]:
        with pytest.raises(ValidationError):
            evaluation(**patch)
    bad = pair(
        invariants=tuple(
            InvariantResult(invariant=item, baseline_hash=HASH, candidate_hash=OTHER_HASH)
            for item in LearningInvariant
        )
    )
    with pytest.raises(ValidationError):
        evaluation(outputs=(bad,) + tuple(pair(case) for case in list(LearningCase)[1:]))
    with pytest.raises(ValidationError):
        pair(invariants=())
    validate(
        evaluation(
            status=EvaluationStatus.FAILED,
            outputs=(bad,),
            failures=(EvaluationFailure.CASE_FAILED,),
        )
    )


def test_attempt_lease_and_expiry_shape_preserve_failures():
    running = evaluation(status=EvaluationStatus.RUNNING, outputs=(), finished_at=None)
    validate(running)
    with pytest.raises(ValidationError):
        evaluation(status=EvaluationStatus.RUNNING)
    expired = evaluation(
        status=EvaluationStatus.EXPIRED,
        outputs=(),
        finished_at=NOW + timedelta(seconds=30),
        failures=(EvaluationFailure.DEADLINE_EXCEEDED,),
    )
    validate(expired, now=NOW + timedelta(seconds=30))
    with pytest.raises(ValidationError):
        evaluation(status=EvaluationStatus.EXPIRED, outputs=())
    with pytest.raises(ValueError, match="deadline"):
        validate(evaluation(deadline_at=NOW + timedelta(seconds=31)))
    with pytest.raises(ValueError, match="attempt"):
        validate(evaluation(attempt_number=5))


def test_transition_logical_identity_ignores_transport_key_but_binds_revision():
    first = transition()
    retry = transition(id="transition-other", request_key="request-other")
    assert first.logical_identity == retry.logical_identity
    rollback = transition(
        kind=TransitionType.ROLLBACK,
        previous=NEXT,
        next=GuidanceBinding(policy=BASE.policy, activation_revision=3),
        candidate=None,
        evaluation=None,
        rollback_of=ref("transition-1"),
    )
    validate(rollback)
    assert rollback.logical_identity != first.logical_identity
    replay = transition(
        previous=rollback.next, next=GuidanceBinding(policy=NEXT.policy, activation_revision=4)
    )
    assert replay.logical_identity != first.logical_identity
    for patch in [
        {"next": BASE},
        {"explicit_confirmation": False},
        {"actor_session": "other"},
        {"evaluation": None},
    ]:
        with pytest.raises(ValidationError):
            transition(**patch)


def test_initial_policy_and_monotonic_state_contract():
    GuidancePolicyState(**owned(), active=BASE)
    with pytest.raises(ValidationError):
        GuidancePolicyState(**owned(), active=NEXT)
    GuidancePolicyState(**owned(), active=NEXT, last_transition=ref("transition-1"))


@pytest.mark.parametrize(
    "operation,field,limit",
    [
        (RetailOperation.CREATE_INCIDENT, "incidents", 20),
        (RetailOperation.RECORD_FEEDBACK, "feedback", 40),
        (RetailOperation.CREATE_CANDIDATE, "candidates", 2),
        (RetailOperation.START_EVALUATION, "evaluations", 4),
    ],
)
def test_lifetime_reservations_at_limit_and_one_over(operation, field, limit):
    usage = RetailUsage(**{field: limit - 1})
    accepted = admit_new_operation(usage, operation, POLICY)
    assert getattr(accepted, field) == limit
    if operation == RetailOperation.START_EVALUATION:
        # Finishing/failing releases active occupancy only, not the lifetime slot.
        accepted = RetailUsage(evaluations=limit, active_evaluations=0)
    with pytest.raises(ValueError):
        admit_new_operation(accepted, operation, POLICY)
    assert getattr(usage, field) == limit - 1


def test_active_lease_exclusion_and_reserved_rollback_capacity():
    active = admit_new_operation(RetailUsage(), RetailOperation.START_EVALUATION, POLICY)
    with pytest.raises(ValueError):
        admit_new_operation(active, RetailOperation.START_EVALUATION, POLICY)
    usage = RetailUsage()
    for operation in [RetailOperation.ACTIVATE, RetailOperation.ROLLBACK] * 2:
        usage = admit_new_operation(usage, operation, POLICY)
    assert (usage.forward_activations, usage.rollbacks) == (2, 2)
    with pytest.raises(ValueError):
        admit_new_operation(usage, RetailOperation.ACTIVATE, POLICY)
    with pytest.raises(ValueError):
        admit_new_operation(RetailUsage(), RetailOperation.ROLLBACK, POLICY)


def test_overridden_policy_reaches_real_reservation_boundary():
    policy = RetailPolicy(max_feedback=1)
    accepted = admit_new_operation(RetailUsage(), RetailOperation.RECORD_FEEDBACK, policy)
    with pytest.raises(ValueError):
        admit_new_operation(accepted, RetailOperation.RECORD_FEEDBACK, policy)
    assert admit_new_operation(accepted, RetailOperation.RECORD_FEEDBACK, POLICY).feedback == 2


def test_predeclared_learning_registry_is_six_paired_cases_separate_from_core():
    path = Path(__file__).resolve().parents[2] / "fixtures/learning/expectations.json"
    registry = json.loads(path.read_text())
    assert registry["case_count"] == 6
    assert {case["id"] for case in registry["cases"]} == set(LearningCase)
    assert set(registry["invariants"]) == set(LearningInvariant)
    assert set(registry["policies"]) == set(GuidancePolicyId)
    assert "executable evaluator not run" in registry["status"]


def test_negative_summary_rejects_unresolved_reasons_and_uncertainty():
    negative = dict(
        category=QueueCategory.NOT_LISTED, verdict=Verdict.NOT_LISTED_IN_CHECKED_NOTICES
    )
    for patch in [{}, {"reasons": (), "uncertainty_unresolved": True}]:
        with pytest.raises(ValidationError, match="complete current scoped result"):
            row(**(negative | patch))
    validate(snapshot(rows=(row(**(negative | {"reasons": ()})),)))


def test_server_now_rejects_future_completion_and_disposition():
    finished = NOW + timedelta(seconds=20)
    future_pass = evaluation(finished_at=finished)
    future_feedback = feedback(
        history=(DispositionEvent(disposition=FeedbackDisposition.RECORDED, recorded_at=finished),)
    )
    for record in [future_pass, future_feedback]:
        with pytest.raises(ValueError, match="future"):
            validate(record)
        validate(record, now=finished)
    validate(evaluation(status=EvaluationStatus.RUNNING, outputs=(), finished_at=None))


@pytest.mark.parametrize("confirmation", [1, 1.0, 0, "true", None, False])
def test_explicit_confirmation_requires_true_boolean_in_python_and_json(confirmation):
    with pytest.raises(ValidationError):
        transition(explicit_confirmation=confirmation)
    data = json.loads(transition().storage_json()) | {"explicit_confirmation": confirmation}
    with pytest.raises(ValidationError):
        GuidanceTransition.model_validate_json(json.dumps(data))


@pytest.mark.parametrize(
    "category,detail",
    [
        (FeedbackCategory.EXTRACTION_DISPUTED, FeedbackDetail.EXTRACTED_VALUE_DISPUTED),
        (FeedbackCategory.SOURCE_SCOPE_DISPUTED, FeedbackDetail.SOURCE_SCOPE_DISPUTED),
    ],
)
def test_initial_result_feedback_without_recapture_cannot_support_guidance_candidate(
    category, detail
):
    initial_data = basis().model_dump(exclude={"recapture"})
    initial_basis = EvidenceBasis(**initial_data)
    initial_feedback = feedback(basis=initial_basis, category=category, detail=detail)
    validate(initial_feedback)
    assert FeedbackRecord.model_validate_json(initial_feedback.storage_json()) == initial_feedback
    support = FeedbackSupport(feedback=ref("initial-feedback"), basis=initial_basis)
    with pytest.raises(ValidationError, match="recapture"):
        candidate(supports=(support,))
    validate(candidate())


def test_record_limit_counts_utf8_bytes_including_response_fields():
    unicode_source = SourceDependency(**(SOURCE.model_dump() | {"family": "synthetic-é"}))
    unicode_basis = EvidenceBasis(**(basis().model_dump() | {"sources": (unicode_source,)}))
    record = feedback(basis=unicode_basis)
    serialized = record.model_dump_json()
    size = len(serialized.encode("utf-8"))
    assert size > len(serialized)
    for limit, accepted in [(size, True), (size - 1, False)]:
        policy = RetailPolicy(record_bytes=limit)
        bound = feedback(basis=unicode_basis, effective_policy_hash=policy.digest())
        if accepted:
            validate(bound, policy=policy)
        else:
            with pytest.raises(ValueError, match="byte limit"):
                validate(bound, policy=policy)

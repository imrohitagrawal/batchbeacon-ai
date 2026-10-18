"""Owned, bounded guidance lifecycle. Evaluation runs outside retried transactions."""

from datetime import datetime, timedelta
from typing import Annotated, Literal
from uuid import uuid4

from pydantic import Field, TypeAdapter, model_validator

from batchbeacon.contracts import Digest, Record
from batchbeacon.evidence_service import canonical
from batchbeacon.guest_service import GuestDenied, OpaqueId, RequestKey
from batchbeacon.guidance_policies import GuidanceField, GuidancePolicyId, GuidanceText
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
    EXPECTATIONS_SHA256,
    INPUT_SHA256,
    SUITE_ID,
    ExecutionStatus,
    LearningExecution,
)
from batchbeacon.retail_contracts import (
    CandidateDiagnosis,
    DispositionEvent,
    EvaluationStatus,
    EvidenceBasis,
    FeedbackCategory,
    FeedbackDetail,
    FeedbackDisposition,
    FeedbackRecord,
    FeedbackSupport,
    GuidanceBinding,
    GuidanceTransition,
    ImprovementCandidate,
    ScopedRecord,
    ShopScope,
    TransitionType,
    VersionRef,
    policy_ref,
    render_guidance,
)
from batchbeacon.retail_projection import CapabilityObservation

Positive = Annotated[int, Field(gt=0)]


def changed(record, **updates):
    return type(record).model_validate(record.model_dump(exclude_computed_fields=True) | updates)


def reference(record, revision=1):
    return VersionRef(id=record.id, revision=revision, content_hash=record.digest())


def denied(code="learning_unavailable", status=409):
    return GuestDenied(status, code)


class LearningPolicy(Record):
    version: Literal["owned-learning-1"] = "owned-learning-1"
    max_requests: Positive = 24
    request_bytes: Positive = 4096
    max_receipts: Positive = 128
    receipt_bytes: Positive = 512
    base_bytes: Positive = 8192
    max_state_bytes: Positive = 720896

    def validate_capacity(self, retail):
        if self.max_receipts < (
            self.max_requests
            + retail.max_feedback
            + retail.max_candidates
            + retail.max_evaluations
            + retail.max_transitions
        ):
            raise ValueError("receipt capacity must reserve terminal operations and rollback")
        # Reserve space for every admitted terminal report and rollback up front.
        required = (
            self.base_bytes
            + self.max_requests * self.request_bytes
            + (
                retail.max_feedback
                + retail.max_candidates
                + retail.max_evaluations
                + retail.max_transitions
            )
            * retail.record_bytes
            + retail.max_evaluations * retail.evaluation_bytes
            + self.max_receipts * self.receipt_bytes
        )
        if required > self.max_state_bytes:
            raise ValueError("learning aggregate cannot reserve all bounded records")


class GuidanceRequest(ScopedRecord):
    id: OpaqueId
    basis: EvidenceBasis
    evidence_hash: Digest
    usage_hash: Digest
    binding: GuidanceBinding
    capacity: CapabilityObservation
    instructions: tuple[GuidanceText, ...] = Field(min_length=1)


class OwnedEvaluation(ScopedRecord):
    id: OpaqueId
    attempt_number: Positive
    candidate: VersionRef
    base: GuidanceBinding
    initiating_key: RequestKey
    lease: OpaqueId
    deadline_at: datetime
    status: EvaluationStatus
    evidence_hashes: tuple[Digest, ...]
    evaluator_hash: Digest
    configuration_hash: Digest
    execution: LearningExecution | None = None
    finished_at: datetime | None = None
    failure: (
        Literal["DEADLINE_EXCEEDED", "WORKER_INTERRUPTED", "STALE_BASIS", "EVALUATION_FAILED"]
        | None
    ) = None

    @model_validator(mode="after")
    def coherent(self):
        if (
            self.deadline_at.tzinfo is None
            or not self.created_at < self.deadline_at <= self.expires_at
        ):
            raise ValueError("invalid evaluation lease")
        if self.status == EvaluationStatus.RUNNING:
            if self.finished_at is not None or self.execution is not None or self.failure:
                raise ValueError("running evaluation has terminal evidence")
        else:
            if (
                self.finished_at is None
                or not self.created_at <= self.finished_at < self.expires_at
            ):
                raise ValueError("invalid evaluation completion")
            if self.status == EvaluationStatus.PASSED:
                if (
                    self.execution is None
                    or self.execution.status != ExecutionStatus.PASSED
                    or self.finished_at >= self.deadline_at
                    or self.failure is not None
                ):
                    raise ValueError("owned PASS requires a timely actual execution")
            elif self.failure is None:
                raise ValueError("failed attempt must retain its reason")
        return self


class Receipt(Record):
    key: RequestKey
    operation: Literal["guidance", "feedback", "candidate", "evaluation", "activate", "rollback"]
    payload_hash: Digest
    record_id: OpaqueId


class LearningState(Record):
    scope: ShopScope
    configuration_hash: Digest
    active: GuidanceBinding
    requests: tuple[GuidanceRequest, ...] = ()
    feedback: tuple[FeedbackRecord, ...] = ()
    candidates: tuple[ImprovementCandidate, ...] = ()
    evaluations: tuple[OwnedEvaluation, ...] = ()
    transitions: tuple[GuidanceTransition, ...] = ()
    receipts: tuple[Receipt, ...] = ()


class ActivationConfirmation(Record):
    basis: ActivationBasis
    explicit_confirmation: Literal[True]


class RollbackTarget(Record):
    transition: VersionRef
    current: GuidanceBinding


class RollbackConfirmation(RollbackTarget):
    explicit_confirmation: Literal[True]


class LearningService:
    def __init__(self, store, evidence, shared_policy, evaluator, policy=None, *, capability=None):
        policy = policy or LearningPolicy()
        if (
            evidence.store is not store.evidence
            or evaluator.policy.retail != store.guest_policy.retail
        ):
            raise ValueError("learning requires one owned service graph")
        if evaluator.policy.limits != GuidanceLimits.from_shared(shared_policy):
            raise ValueError("learning limits must match shared admission")
        policy.validate_capacity(store.guest_policy.retail)
        if policy.max_state_bytes + 4096 > store.policy.max_document_bytes:
            raise ValueError("learning aggregate exceeds configured document capacity")
        self.store, self.evidence, self.guest = store, evidence, evidence.guest
        self.shared_policy, self.evaluator, self.policy = shared_policy, evaluator, policy
        # An absent observed capability never becomes AVAILABLE.
        self.capability = capability
        self.configuration_hash = canonical(
            {
                "learning": policy.digest(),
                "retail": self.guest.policy.retail.digest(),
                "shared": shared_policy.digest(),
                "evaluation": evaluator.policy.digest(),
                "code": evaluator.code_hash,
            }
        )

    def baseline(self, guest):
        return LearningState(
            scope=guest.scope,
            configuration_hash=self.configuration_hash,
            active=GuidanceBinding(policy=policy_ref(GuidancePolicyId.V1), activation_revision=1),
        )

    def _common(self, guest, now):
        return dict(
            scope=guest.scope, created_at=now, effective_policy_hash=self.configuration_hash
        )

    @staticmethod
    def _bound(record, limit):
        if len(record.model_dump_json().encode()) > limit:
            raise denied("learning_record_limit", 429)

    def _validate(self, state, guest):
        if (
            state is None
            or state.scope != guest.scope
            or state.configuration_hash != self.configuration_hash
        ):
            raise denied("learning_state_unavailable", 503)
        p, r = self.policy, self.guest.policy.retail
        groups = (
            (state.requests, p.max_requests, p.request_bytes),
            (state.feedback, r.max_feedback, r.record_bytes),
            (state.candidates, r.max_candidates, r.record_bytes),
            (state.evaluations, r.max_evaluations, None),
            (state.transitions, r.max_transitions, r.record_bytes),
            (state.receipts, p.max_receipts, p.receipt_bytes),
        )
        for records, maximum, byte_limit in groups:
            if len(records) > maximum:
                raise denied("learning_allowance_exhausted", 429)
            identifiers = [x.key if isinstance(x, Receipt) else x.id for x in records]
            if len(identifiers) != len(set(identifiers)):
                raise denied("learning_state_unavailable", 503)
            for record in records:
                if isinstance(record, ScopedRecord) and (
                    record.scope != guest.scope
                    or record.effective_policy_hash != self.configuration_hash
                ):
                    raise denied("learning_state_unavailable", 503)
                if byte_limit:
                    self._bound(record, byte_limit)
        if (
            sum(e.status == EvaluationStatus.RUNNING for e in state.evaluations)
            > r.max_active_evaluations
        ):
            raise denied("learning_allowance_exhausted", 429)
        if tuple(e.attempt_number for e in state.evaluations) != tuple(
            range(1, len(state.evaluations) + 1)
        ):
            raise denied("learning_state_unavailable", 503)
        for e in state.evaluations:
            self._bound(
                changed(e, execution=None)
                if e.status != EvaluationStatus.PASSED
                else changed(
                    e, status=EvaluationStatus.FAILED, failure="EVALUATION_FAILED", execution=None
                ),
                r.record_bytes,
            )
            if e.execution:
                self._bound(e.execution, r.evaluation_bytes)
        binding = GuidanceBinding(policy=policy_ref(GuidancePolicyId.V1), activation_revision=1)
        forwards = 0
        for t in state.transitions:
            if t.previous != binding:
                raise denied("learning_state_unavailable", 503)
            binding = t.next
            forwards += t.kind == TransitionType.ACTIVATE
        if binding != state.active or forwards > r.max_forward_activations:
            raise denied("learning_state_unavailable", 503)
        self._bound(state, p.max_state_bytes)

    def _operate(self, capability, operation):
        key = self.guest._key(capability)
        s = self.store

        def transaction(tx):
            guest, usage = s._guest(tx, key)
            self.guest._live(guest, key)
            tx.limit_to(guest.scope.expires_at)
            name = s.name("learning", key)
            state = tx.read({name: "learning"})[name]
            self._validate(state, guest)
            now = self.guest._now()
            expired = tuple(
                changed(
                    e, status=EvaluationStatus.EXPIRED, finished_at=now, failure="DEADLINE_EXCEEDED"
                )
                if e.status == EvaluationStatus.RUNNING and now >= e.deadline_at
                else e
                for e in state.evaluations
            )
            working = changed(state, evaluations=expired)
            updated, result = operation(tx, key, guest, usage, working, now)
            self._validate(updated, guest)
            if updated != state:
                tx.write(name, "learning", updated)
            return guest, result

        guest, result = self.guest._storage(lambda: s.run(transaction))
        self.guest._live(guest, key)
        return result

    def read(self, capability):
        return self._operate(capability, lambda tx, k, g, u, s, n: (s, s))

    @staticmethod
    def _find(records, identifier):
        record = next((r for r in records if r.id == identifier), None)
        if record is None:
            raise denied("learning_record_unavailable", 404)
        return record

    def _retry(self, state, key, operation, payload, records):
        TypeAdapter(RequestKey).validate_python(key)
        prior = next((x for x in state.receipts if x.key == key), None)
        if prior is None:
            return None
        if prior.operation != operation or prior.payload_hash != payload:
            raise denied("request_key_conflict")
        return self._find(records, prior.record_id)

    def _append(self, state, key, operation, payload, field, record):
        receipt = Receipt(key=key, operation=operation, payload_hash=payload, record_id=record.id)
        return changed(
            state, **{field: (*getattr(state, field), record)}, receipts=(*state.receipts, receipt)
        )

    def _alias(self, state, key, operation, payload, record):
        r = self.guest.policy.retail
        reserved = (
            self.policy.max_requests
            + r.max_feedback
            + r.max_candidates
            + r.max_evaluations
            + r.max_transitions
        )
        distinct = sum(
            len(getattr(state, field))
            for field in ("requests", "feedback", "candidates", "evaluations", "transitions")
        )
        if len(state.receipts) - distinct >= self.policy.max_receipts - reserved:
            raise denied("learning_alias_limit", 429)
        receipt = Receipt(key=key, operation=operation, payload_hash=payload, record_id=record.id)
        return changed(state, receipts=(*state.receipts, receipt))

    def _basis(self, tx, key, incident):
        snapshot = self.store.evidence.snapshot(tx, key, incident)
        state = self.evidence._check(snapshot, key, incident)
        environment = self.evidence._environment(snapshot)
        obs = state.observations[-1].observation if state.observations else None
        result = state.results[-1] if state.results else None
        if (
            obs is None
            or result is None
            or state.active_result != result.revision
            or result.observation_revision != obs.revision
            or not self.evidence._acquisition_current(snapshot, state)
        ):
            raise denied("learning_evidence_stale")
        for extraction in state.extractions:
            self.evidence._ready(snapshot, incident, extraction.envelope.captures)
        evidence = LearningEvidence(
            result=result,
            observation=obs,
            notices=environment.notices,
            context=environment.at(self.guest._now(), len(state.results)),
            verifier_policy=environment.verifier_policy,
        )
        if not evidence.current():
            raise denied("learning_evidence_stale")
        basis = EvidenceBasis(
            incident_id=incident,
            sources=result.checked_sources,
            observation=VersionRef(id=incident, revision=obs.revision, content_hash=obs.digest()),
            result=VersionRef(id=incident, revision=result.revision, content_hash=result.digest()),
            context_state_hash=evidence.basis(),
        )
        counter = next(i for i in snapshot.usage.incidents if i.incident_id == incident)
        return basis, evidence, counter

    def guidance(self, capability, incident, key):
        session = self.guest.resolve(capability)
        capacity = self.capability(session) if self.capability else None
        identifier = uuid4().hex
        payload = canonical({"incident": incident})

        def operation(tx, k, g, u, state, now):
            prior = self._retry(state, key, "guidance", payload, state.requests)
            if prior:
                return state, prior
            basis, evidence, counter = self._basis(tx, k, incident)
            decision = guidance_decision(
                evidence.result,
                evidence.observation,
                evidence.notices,
                evidence.context,
                evidence.verifier_policy,
                usage=GuidanceUsage(
                    acquisitions=counter.acquisitions, verifications=len(counter.verifications)
                ),
                limits=self.evaluator.policy.limits,
                capability=capacity,
                read_policy=self.evaluator.policy.read,
            )
            if not decision.requested_fields:
                raise denied("guidance_not_available")
            request = GuidanceRequest(
                **self._common(g, now),
                id=identifier,
                basis=basis,
                evidence_hash=evidence.basis(),
                usage_hash=counter.digest(),
                binding=state.active,
                capacity=capacity,
                instructions=render_guidance(
                    self.guest.policy.retail, state.active, decision.requested_fields
                ),
            )
            return self._append(state, key, "guidance", payload, "requests", request), request

        return self._operate(capability, operation)

    def feedback(self, capability, incident, key, detail: FeedbackDetail, request_id=None):
        TypeAdapter(FeedbackDetail).validate_python(detail)
        identifier = uuid4().hex
        payload = canonical({"incident": incident, "detail": detail, "request_id": request_id})

        def operation(tx, k, g, u, state, now):
            prior = self._retry(state, key, "feedback", payload, state.feedback)
            if prior:
                return state, prior
            basis, evidence, _ = self._basis(tx, k, incident)
            category = {
                FeedbackDetail.EXTRACTED_VALUE_DISPUTED: FeedbackCategory.EXTRACTION_DISPUTED,
                FeedbackDetail.SOURCE_SCOPE_DISPUTED: FeedbackCategory.SOURCE_SCOPE_DISPUTED,
            }.get(detail, FeedbackCategory.GUIDANCE_UNCLEAR)
            if request_id is not None:
                request = self._find(state.requests, request_id)
                if request.basis != basis or request.evidence_hash != evidence.basis():
                    raise denied("learning_evidence_stale")
                basis = changed(basis, recapture=reference(request))
            disposition = (
                FeedbackDisposition.HUMAN_INVESTIGATION
                if category != FeedbackCategory.GUIDANCE_UNCLEAR
                else FeedbackDisposition.RECORDED
            )
            history = (DispositionEvent(disposition=FeedbackDisposition.RECORDED, recorded_at=now),)
            if disposition != FeedbackDisposition.RECORDED:
                history += (DispositionEvent(disposition=disposition, recorded_at=now),)
            record = FeedbackRecord(
                **self._common(g, now),
                id=identifier,
                actor_session=g.scope.session_id,
                basis=basis,
                category=category,
                detail=detail,
                history=history,
            )
            return self._append(state, key, "feedback", payload, "feedback", record), record

        return self._operate(capability, operation)

    def _supports(self, tx, key, state, candidate):
        if candidate.base != state.active:
            raise denied("learning_base_changed")
        evidence = []
        for support in candidate.supports:
            f = self._find(state.feedback, support.feedback.id)
            if (
                reference(f) != support.feedback
                or f.basis != support.basis
                or f.basis.recapture is None
            ):
                raise denied("learning_support_changed")
            request = self._find(state.requests, f.basis.recapture.id)
            basis, current, counter = self._basis(tx, key, f.basis.incident_id)
            if (
                reference(request) != f.basis.recapture
                or request.basis != basis
                or changed(f.basis, recapture=None) != basis
                or request.binding != candidate.base
                or request.evidence_hash != current.basis()
                or request.usage_hash != counter.digest()
            ):
                raise denied("learning_evidence_stale")
            evidence.append(current)
        return tuple(evidence)

    def candidate(self, capability, key, feedback_ids):
        ids = tuple(feedback_ids)
        if not 1 <= len(ids) <= self.guest.policy.retail.max_support_refs or len(set(ids)) != len(
            ids
        ):
            raise denied("invalid_learning_support")
        identifier = uuid4().hex
        payload = canonical(ids)

        def operation(tx, k, g, u, state, now):
            prior = self._retry(state, key, "candidate", payload, state.candidates)
            if prior:
                return state, prior
            if state.active.policy.id != GuidancePolicyId.V1:
                raise denied("no_safe_candidate")
            supports = []
            fields = []
            for fid in ids:
                f = self._find(state.feedback, fid)
                field = {
                    FeedbackDetail.LOT_CODE_UNCLEAR: GuidanceField.LOT,
                    FeedbackDetail.DATE_PANEL_UNCLEAR: GuidanceField.BEST_BEFORE,
                }.get(f.detail)
                if (
                    f.category != FeedbackCategory.GUIDANCE_UNCLEAR
                    or field is None
                    or f.basis.recapture is None
                ):
                    raise denied("no_safe_candidate")
                request = self._find(state.requests, f.basis.recapture.id)
                if field not in tuple(i.field for i in request.instructions):
                    raise denied("no_safe_candidate")
                fields.append(field)
                supports.append(FeedbackSupport(feedback=reference(f), basis=f.basis))
            record = ImprovementCandidate(
                **self._common(g, now),
                id=identifier,
                rule=VersionRef(
                    id="required-panel-rule-1",
                    revision=1,
                    content_hash=canonical("fixed-V1-to-V2-required-lot-or-best-before-1"),
                ),
                diagnosis=CandidateDiagnosis.REQUIRED_LOT_GUIDANCE
                if GuidanceField.LOT in fields
                else CandidateDiagnosis.REQUIRED_DATE_GUIDANCE,
                supports=tuple(supports),
                base=state.active,
                proposed=policy_ref(GuidancePolicyId.V2),
            )
            self._supports(tx, k, state, record)
            return self._append(state, key, "candidate", payload, "candidates", record), record

        return self._operate(capability, operation)

    def evaluate(self, capability, key, candidate_id):
        identifier, lease = uuid4().hex, uuid4().hex
        payload = canonical(candidate_id)

        def start(tx, k, g, u, state, now):
            prior = self._retry(state, key, "evaluation", payload, state.evaluations)
            if prior:
                return state, prior
            candidate = self._find(state.candidates, candidate_id)
            evidence = self._supports(tx, k, state, candidate)
            deadline = min(
                now + timedelta(seconds=self.guest.policy.retail.evaluation_deadline_seconds),
                g.scope.expires_at,
            )
            attempt = OwnedEvaluation(
                attempt_number=len(state.evaluations) + 1,
                **self._common(g, now),
                id=identifier,
                candidate=reference(candidate),
                base=state.active,
                initiating_key=key,
                lease=lease,
                deadline_at=deadline,
                status=EvaluationStatus.RUNNING,
                evidence_hashes=tuple(e.basis() for e in evidence),
                evaluator_hash=self.evaluator.code_hash,
                configuration_hash=self.evaluator.policy.digest(),
            )
            return self._append(state, key, "evaluation", payload, "evaluations", attempt), attempt

        attempt = self._operate(capability, start)
        if attempt.id != identifier or attempt.status != EvaluationStatus.RUNNING:
            return attempt  # Same-key recovery never creates or executes another attempt.
        execution = None
        try:
            execution = self.evaluator.run(
                attempt.base, policy_ref(GuidancePolicyId.V2), lease_expires_at=attempt.deadline_at
            )
        except Exception:
            pass  # Failed owned attempt still consumes its reserved lifetime slot.

        def finish(tx, k, g, u, state, now):
            current = self._find(state.evaluations, identifier)
            if current.lease != lease or current.status != EvaluationStatus.RUNNING:
                return state, current
            status, failure = EvaluationStatus.FAILED, "WORKER_INTERRUPTED"
            if execution is not None:
                status, failure = EvaluationStatus.FAILED, "EVALUATION_FAILED"
                if (
                    self._execution_matches(current, execution)
                    and execution.status == ExecutionStatus.PASSED
                ):
                    try:
                        candidate = self._find(state.candidates, candidate_id)
                        evidence = self._supports(tx, k, state, candidate)
                        valid = tuple(e.basis() for e in evidence) == current.evidence_hashes
                    except GuestDenied:
                        valid = False
                    status = EvaluationStatus.PASSED if valid else EvaluationStatus.FAILED
                    failure = None if valid else "STALE_BASIS"
            terminal = changed(
                current, status=status, failure=failure, execution=execution, finished_at=now
            )
            updated = changed(
                state,
                evaluations=tuple(terminal if e.id == identifier else e for e in state.evaluations),
            )
            return updated, terminal

        return self._operate(capability, finish)

    def _execution_matches(self, attempt, execution):
        return bool(
            execution.baseline == attempt.base
            and execution.candidate == policy_ref(GuidancePolicyId.V2)
            and execution.input_hash == INPUT_SHA256
            and execution.expectations_hash == EXPECTATIONS_SHA256
            and execution.evaluator_code_hash == attempt.evaluator_hash == self.evaluator.code_hash
            and execution.configuration_hash
            == attempt.configuration_hash
            == self.evaluator.policy.digest()
            and attempt.created_at <= execution.started_at < attempt.deadline_at
            and execution.deadline_at == attempt.deadline_at
        )

    def _activation(self, tx, key, state, evaluation_id):
        attempt = self._find(state.evaluations, evaluation_id)
        candidate = self._find(state.candidates, attempt.candidate.id)
        if (
            attempt.status != EvaluationStatus.PASSED
            or reference(candidate) != attempt.candidate
            or attempt.execution is None
            or not self._execution_matches(attempt, attempt.execution)
        ):
            raise denied("evaluation_not_activatable")
        evidence = self._supports(tx, key, state, candidate)
        if tuple(e.basis() for e in evidence) != attempt.evidence_hashes:
            raise denied("learning_evidence_stale")
        basis = ActivationBasis(
            candidate=reference(candidate),
            evaluation=reference(attempt),
            suite=VersionRef(id=SUITE_ID, revision=1, content_hash=EXPECTATIONS_SHA256),
            inputs=VersionRef(id="learning-inputs-1", revision=1, content_hash=INPUT_SHA256),
            evaluator=VersionRef(
                id="learning-evaluator-1", revision=1, content_hash=self.evaluator.code_hash
            ),
            base=state.active,
            proposed_policy_hash=candidate.proposed.content_hash,
            evidence_basis_hashes=attempt.evidence_hashes,
        )
        return basis, evidence

    def prepare_activation(self, capability, evaluation_id):
        return self._operate(
            capability, lambda tx, k, g, u, s, n: (s, self._activation(tx, k, s, evaluation_id)[0])
        )

    def activate(self, capability, key, confirmation: ActivationConfirmation):
        confirmation = ActivationConfirmation.model_validate(confirmation)
        payload = confirmation.digest()
        identifier = uuid4().hex

        def operation(tx, k, g, u, state, now):
            prior = self._retry(state, key, "activate", payload, state.transitions)
            if prior:
                return state, prior
            logical = next(
                (
                    t
                    for t in state.transitions
                    if t.kind == TransitionType.ACTIVATE
                    and t.candidate == confirmation.basis.candidate
                    and t.evaluation == confirmation.basis.evaluation
                    and t.previous == confirmation.basis.base
                ),
                None,
            )
            if logical:
                if logical.payload_hash != payload:
                    raise denied("learning_confirmation_changed")
                return self._alias(state, key, "activate", payload, logical), logical
            if not g.demo_manager:
                raise denied("demo_manager_required", 403)
            basis, evidence = self._activation(tx, k, state, confirmation.basis.evaluation.id)
            if not activation_permitted(
                confirmation.basis,
                basis,
                evaluation_status=EvaluationStatus.PASSED,
                evidence=evidence,
                retail_policy=self.guest.policy.retail,
            ):
                raise denied("learning_confirmation_changed")
            r = self.guest.policy.retail
            if (
                sum(t.kind == TransitionType.ACTIVATE for t in state.transitions)
                >= r.max_forward_activations
                or len(state.transitions) + 2 > r.max_transitions
            ):
                raise denied("learning_allowance_exhausted", 429)
            next_binding = GuidanceBinding(
                policy=policy_ref(GuidancePolicyId.V2),
                activation_revision=state.active.activation_revision + 1,
            )
            transition = GuidanceTransition(
                **self._common(g, now),
                id=identifier,
                kind=TransitionType.ACTIVATE,
                previous=state.active,
                next=next_binding,
                candidate=basis.candidate,
                evaluation=basis.evaluation,
                actor_session=g.scope.session_id,
                confirmed_at=now,
                explicit_confirmation=True,
                request_key=key,
                payload_hash=payload,
            )
            updated = self._append(state, key, "activate", payload, "transitions", transition)
            return changed(updated, active=next_binding), transition

        return self._operate(capability, operation)

    def prepare_rollback(self, capability):
        def operation(tx, k, g, u, state, now):
            if not state.transitions or state.transitions[-1].kind != TransitionType.ACTIVATE:
                raise denied("rollback_unavailable")
            return state, RollbackTarget(
                transition=reference(state.transitions[-1]),
                current=state.active,
            )

        return self._operate(capability, operation)

    def rollback(self, capability, key, confirmation: RollbackConfirmation):
        confirmation = RollbackConfirmation.model_validate(confirmation)
        payload = confirmation.digest()
        identifier = uuid4().hex

        def operation(tx, k, g, u, state, now):
            prior = self._retry(state, key, "rollback", payload, state.transitions)
            if prior:
                return state, prior
            logical = next(
                (
                    t
                    for t in state.transitions
                    if t.kind == TransitionType.ROLLBACK
                    and t.rollback_of == confirmation.transition
                    and t.previous == confirmation.current
                ),
                None,
            )
            if logical:
                if logical.payload_hash != payload:
                    raise denied("learning_confirmation_changed")
                return self._alias(state, key, "rollback", payload, logical), logical
            if not g.demo_manager:
                raise denied("demo_manager_required", 403)
            original = self._find(state.transitions, confirmation.transition.id)
            if (
                reference(original) != confirmation.transition
                or original.kind != TransitionType.ACTIVATE
                or state.active != confirmation.current
                or state.active != original.next
            ):
                raise denied("rollback_binding_changed")
            next_binding = rollback_binding(
                state.active, activated_from=original.previous, activated_to=original.next
            )
            transition = GuidanceTransition(
                **self._common(g, now),
                id=identifier,
                kind=TransitionType.ROLLBACK,
                previous=state.active,
                next=next_binding,
                rollback_of=confirmation.transition,
                actor_session=g.scope.session_id,
                confirmed_at=now,
                explicit_confirmation=True,
                request_key=key,
                payload_hash=payload,
            )
            updated = self._append(state, key, "rollback", payload, "transitions", transition)
            return changed(updated, active=next_binding), transition

        return self._operate(capability, operation)

"""Executed fixed synthetic guidance suite, not a persisted learning attempt.

Preparation pins input bytes and records actual owned module hashes. Execution
uses only bounded pure functions and injected clocks. No uploaded report is an
execution credential; the later service must own reservation and publication.
"""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from time import monotonic
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, computed_field, model_validator

from batchbeacon import (
    action_service,
    contracts,
    evidence_service,
    guidance_policies,
    learning_decisions,
    retail_contracts,
    retail_projection,
)
from batchbeacon.contracts import (
    AuthorityNotice,
    Digest,
    ProductObservation,
    Record,
    ValueState,
    Verdict,
    VerificationContext,
    VerifierPolicy,
)
from batchbeacon.domain import verifier
from batchbeacon.evidence_service import canonical, replace
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
from batchbeacon.retail_contracts import (
    EvaluationStatus,
    GuidanceBinding,
    LearningCase,
    LearningInvariant,
    RetailPolicy,
    VersionRef,
    policy_ref,
    render_guidance,
)
from batchbeacon.retail_projection import (
    CapabilityObservation,
    CapabilityReason,
    CapabilityState,
    RetailReadPolicy,
)

INPUT_SHA256 = "3a795d6d11a0841cf2ec50825d5c8b1a612a010f90e558ffd07693540e67a801"
EXPECTATIONS_SHA256 = "3c1dedf155dc68e302da483fc4fca98a0a9b548cc346c8d41b93f86215a073d0"
SUITE_ID = "guidance-six-paired-1"
VARIANTS = (
    (LearningCase.L01, "LOT_REQUIRED"),
    (LearningCase.L02, "DATE_AMBIGUOUS"),
    (LearningCase.L03, "DATE_ALL"),
    (LearningCase.L03, "DATE_NOT_SPECIFIED"),
    (LearningCase.L04, "IDENTITY_UNKNOWN"),
    (LearningCase.L05, "OWN_EXHAUSTED"),
    (LearningCase.L05, "RESOURCE_UNAVAILABLE"),
    (LearningCase.L06, "SOURCE_CHANGED"),
    (LearningCase.L06, "OBSERVATION_CHANGED"),
)
INVARIANTS = tuple(LearningInvariant)


class EvaluationPolicy(Record):
    retail: RetailPolicy = RetailPolicy()
    verifier: VerifierPolicy = VerifierPolicy()
    read: RetailReadPolicy = RetailReadPolicy()
    limits: GuidanceLimits
    input_bytes: Annotated[int, Field(gt=0)] = 262144


class LearningVariant(Record):
    case: LearningCase
    variant: str
    notice: AuthorityNotice
    observation: ProductObservation
    context: VerificationContext
    changed_notice: AuthorityNotice | None
    changed_observation: ProductObservation | None


class LearningInputs(Record):
    version: Literal["learning-inputs-1"]
    scope: Literal["SYNTHETIC_TECHNICAL_ONLY_NO_HUMAN_APPROVAL"]
    variants: tuple[LearningVariant, ...]

    @model_validator(mode="after")
    def fixed_shape(self) -> Self:
        if tuple((v.case, v.variant) for v in self.variants) != VARIANTS:
            raise ValueError("FIXED_VARIANTS_REQUIRED")
        return self


@dataclass(frozen=True)
class PreparedSuite:
    original: bytes
    expectations: bytes
    inputs: LearningInputs

    def __post_init__(self):
        if (
            sha256(self.original).hexdigest() != INPUT_SHA256
            or sha256(self.expectations).hexdigest() != EXPECTATIONS_SHA256
            or LearningInputs.model_validate_json(self.original) != self.inputs
        ):
            raise ValueError("FIXED_INPUT_BINDING_CHANGED")

    @classmethod
    def load(cls, original, expectations, policy):
        if (
            type(original) is not bytes
            or type(expectations) is not bytes
            or len(original) + len(expectations) > policy.input_bytes
        ):
            raise ValueError("INPUT_BOUND_EXCEEDED")
        return cls(original, expectations, LearningInputs.model_validate_json(original))


class Check(Record):
    name: Literal["EXPECTED_SEMANTICS", "WORDING", "INPUT_PRESERVATION", "CASE_GUARDS"]
    passed: bool


class BranchOutput(Record):
    instructions: tuple[GuidanceText, ...]
    # Order is declared once in the report; no invariant or branch is omitted.
    invariant_hashes: tuple[Digest, ...] = Field(min_length=7, max_length=7)
    checks: tuple[Check, ...] = Field(min_length=4, max_length=4)

    @model_validator(mode="after")
    def checks_complete(self) -> Self:
        if tuple(c.name for c in self.checks) != (
            "EXPECTED_SEMANTICS",
            "WORDING",
            "INPUT_PRESERVATION",
            "CASE_GUARDS",
        ):
            raise ValueError("FIXED_CHECKS_REQUIRED")
        return self


class VariantOutput(Record):
    variant: str
    baseline: BranchOutput | None
    candidate: BranchOutput | None

    @computed_field
    @property
    def passed(self) -> bool:
        return bool(
            self.baseline
            and self.candidate
            and self.baseline.invariant_hashes == self.candidate.invariant_hashes
            and all(c.passed for branch in (self.baseline, self.candidate) for c in branch.checks)
        )


class CaseOutput(Record):
    case: LearningCase
    variants: tuple[VariantOutput, ...] = Field(max_length=2)

    @computed_field
    @property
    def passed(self) -> bool:
        return tuple(v.variant for v in self.variants) == tuple(
            v for case, v in VARIANTS if case == self.case
        ) and all(v.passed for v in self.variants)


class ExecutionStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class LearningExecution(Record):
    version: Literal["learning-execution-1"] = "learning-execution-1"
    authority: Literal["UNPRIVILEGED_SYNTHETIC_EXECUTION"] = "UNPRIVILEGED_SYNTHETIC_EXECUTION"
    suite_id: Literal["guidance-six-paired-1"] = SUITE_ID
    input_hash: Digest
    expectations_hash: Digest
    evaluator_code_hash: Digest
    configuration_hash: Digest
    baseline: GuidanceBinding
    candidate: retail_contracts.PolicyRef
    started_at: AwareDatetime
    deadline_at: AwareDatetime
    finished_at: AwareDatetime | None
    invariants: tuple[LearningInvariant, ...]
    cases: tuple[CaseOutput, ...] = Field(max_length=6)
    status: ExecutionStatus
    failures: tuple[
        Literal["CHECK_FAILED", "DEADLINE_EXCEEDED", "INVALID_CLOCK", "EXECUTION_FAILED"], ...
    ]

    @model_validator(mode="after")
    def actual_complete_pass(self) -> Self:
        if self.invariants != INVARIANTS or len({c.case for c in self.cases}) != len(self.cases):
            raise ValueError("EXECUTION_SHAPE_CHANGED")
        if self.deadline_at <= self.started_at or (
            self.finished_at is not None and self.finished_at < self.started_at
        ):
            raise ValueError("EXECUTION_TIME_INVALID")
        if self.status == ExecutionStatus.PASSED and (
            tuple(c.case for c in self.cases) != tuple(LearningCase)
            or not all(c.passed for c in self.cases)
            or self.failures
            or self.finished_at is None
            or self.finished_at >= self.deadline_at
        ):
            raise ValueError("PASS_REQUIRES_COMPLETE_EXECUTION")
        if self.status != ExecutionStatus.PASSED and not self.failures:
            raise ValueError("NONPASS_REQUIRES_FAILURE_EVIDENCE")
        return self


class LearningRejected(ValueError):
    def __init__(self, code, *, unaccepted=None):
        super().__init__(code)
        # Internal, bounded fixed-suite evidence; never an admitted wire report.
        self.unaccepted = unaccepted


class _Expired(Exception):
    pass


class _ClockInvalid(Exception):
    pass


def _version(name, digest):
    return VersionRef(id=name, revision=1, content_hash=digest)


def _wording_ok(variant, policy_id, instructions, expected):
    if tuple(i.field for i in instructions) != expected:
        return False
    text = " ".join(i.text for i in instructions).casefold()
    if variant == "LOT_REQUIRED":
        return (
            "complete" in text
            and "lot" in text
            and "leading zeros" in text
            and (
                policy_id == GuidancePolicyId.V1
                or ("one frame" in text and "flat" in text and "glare" in text)
            )
        )
    if variant == "DATE_AMBIGUOUS":
        return "complete best-before" in text and (
            policy_id == GuidancePolicyId.V1 or ("flat" in text and "glare" in text)
        )
    if variant == "IDENTITY_UNKNOWN":
        return all(word in text for word in ("product name", "brand", "pack size", "product code"))
    return not instructions


class LearningEvaluator:
    def __init__(
        self,
        suite: PreparedSuite,
        policy: EvaluationPolicy,
        *,
        wall_clock=lambda: datetime.now(UTC),
        monotonic_clock=monotonic,
    ):
        # Preparation only. No arbitrary source path/module is accepted.
        suite.__post_init__()
        if len(suite.original) + len(suite.expectations) > policy.input_bytes:
            raise LearningRejected("INPUT_BOUND_EXCEEDED")
        self.suite, self.policy = suite, policy
        self.wall_clock, self.monotonic_clock = wall_clock, monotonic_clock
        modules = (
            action_service,
            contracts,
            evidence_service,
            guidance_policies,
            learning_decisions,
            retail_contracts,
            retail_projection,
            verifier,
        )
        self.code_hash = canonical(
            {
                **{m.__name__: sha256(Path(m.__file__).read_bytes()).hexdigest() for m in modules},
                "batchbeacon.learning_evaluator": sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        )

    def _branch(self, fixture, binding, candidate, now):
        policy = self.policy
        before = fixture.model_dump_json()
        context = replace(fixture.context, computed_at=now)
        result = verifier.verify(fixture.observation, (fixture.notice,), context, policy.verifier)
        observation = fixture.changed_observation or fixture.observation
        notices = (fixture.changed_notice or fixture.notice,)
        usage = GuidanceUsage(acquisitions=1, verifications=1)
        if fixture.variant == "OWN_EXHAUSTED":
            usage = replace(usage, acquisitions=1 + policy.limits.max_recaptures)
        capacity = CapabilityObservation(
            session_id=observation.session_id,
            capability="NEW_VERIFICATION",
            state=CapabilityState.UNAVAILABLE
            if fixture.variant == "RESOURCE_UNAVAILABLE"
            else CapabilityState.AVAILABLE,
            reason=CapabilityReason.BACKEND_UNAVAILABLE
            if fixture.variant == "RESOURCE_UNAVAILABLE"
            else CapabilityReason.OBSERVED,
            observed_at=now,
            valid_until=now + timedelta(seconds=policy.read.capability_validity_seconds),
        )
        decision = guidance_decision(
            result,
            observation,
            notices,
            context,
            policy.verifier,
            usage=usage,
            limits=policy.limits,
            capability=capacity,
            read_policy=policy.read,
        )
        instructions = render_guidance(policy.retail, binding, decision.requested_fields)
        expected = {
            "LOT_REQUIRED": (GuidanceField.LOT,),
            "DATE_AMBIGUOUS": (GuidanceField.BEST_BEFORE,),
            "IDENTITY_UNKNOWN": (GuidanceField.PRODUCT_IDENTITY,),
        }.get(fixture.variant, ())
        stale = fixture.case == LearningCase.L06
        match = fixture.case in (LearningCase.L03, LearningCase.L06)
        semantics = (
            decision.requested_fields == expected
            and decision.current is not stale
            and result.verdict
            == (Verdict.MATCHED_HOLD_FOR_REVIEW if match else Verdict.REVIEW_REQUIRED)
            and decision.hold_eligible == (match and not stale)
            and decision.review_request_eligible == (not match and not stale)
        )
        if fixture.variant == "DATE_AMBIGUOUS":
            date = next(f.observation for f in observation.fields if f.field == "BEST_BEFORE")
            semantics &= date.state == ValueState.AMBIGUOUS and date.value is None
        fields = {f.field.value: f.observation for f in observation.fields}
        predicates = {r.field.value: r for r in fixture.notice.products[0].predicates}
        counters = {"primary": usage.model_dump(mode="json")}
        if fixture.variant == "LOT_REQUIRED":
            case_guards = (
                fields["LOT"].state == ValueState.UNKNOWN
                and predicates["BEST_BEFORE"].operator == "NOT_SPECIFIED"
            )
        elif fixture.variant == "DATE_AMBIGUOUS":
            case_guards = (
                fields["BEST_BEFORE"].state == ValueState.AMBIGUOUS
                and fields["BEST_BEFORE"].value is None
                and fields["BEST_BEFORE"].raw == "01/02/2026"
            )
        elif fixture.case == LearningCase.L03:
            case_guards = (
                predicates["BEST_BEFORE"].operator
                == ("ALL" if fixture.variant == "DATE_ALL" else "NOT_SPECIFIED")
                and fields["BEST_BEFORE"].state == ValueState.UNKNOWN
            )
        elif fixture.case == LearningCase.L04:
            case_guards = (
                observation.identity.name.state == ValueState.UNKNOWN
                and observation.identity.resolved_name is None
                and fields["LOT"].value == predicates["LOT"].values[0] == "000Ab"
            )
        elif fixture.case == LearningCase.L05:
            available = replace(
                capacity, state=CapabilityState.AVAILABLE, reason=CapabilityReason.OBSERVED
            )
            control_usage = GuidanceUsage(acquisitions=1, verifications=1)
            exhausted_own = replace(control_usage, acquisitions=1 + policy.limits.max_recaptures)
            exhausted_verify = replace(control_usage, verifications=policy.limits.max_verifications)

            def check_usage(value, resource):
                return guidance_decision(
                    result,
                    observation,
                    notices,
                    context,
                    policy.verifier,
                    usage=value,
                    limits=policy.limits,
                    capability=resource,
                    read_policy=policy.read,
                )

            valid = check_usage(control_usage, available)
            own_denied = check_usage(exhausted_own, available)
            verification_denied = check_usage(exhausted_verify, available)
            resource_denied = check_usage(
                control_usage,
                replace(
                    available,
                    state=CapabilityState.UNAVAILABLE,
                    reason=CapabilityReason.BACKEND_UNAVAILABLE,
                ),
            )
            case_guards = valid.requested_fields == (GuidanceField.LOT,) and all(
                not v.requested_fields and v.current and v.review_request_eligible
                for v in (own_denied, verification_denied, resource_denied)
            )
            counters.update(
                control=control_usage.model_dump(mode="json"),
                acquisition_limit=exhausted_own.model_dump(mode="json"),
                verification_limit=exhausted_verify.model_dump(mode="json"),
            )
        else:
            case_guards = False  # L06 must execute the binding/rollback checks below.
        if stale:
            original = LearningEvidence(
                result=result,
                observation=fixture.observation,
                notices=(fixture.notice,),
                context=context,
                verifier_policy=policy.verifier,
            )
            current = LearningEvidence(
                result=result,
                observation=observation,
                notices=notices,
                context=context,
                verifier_policy=policy.verifier,
            )
            base = GuidanceBinding(
                policy=policy_ref(GuidancePolicyId.V1),
                activation_revision=binding.activation_revision,
            )
            target = ActivationBasis(
                candidate=_version("fixed-candidate", candidate.digest()),
                evaluation=_version("synthetic-binding-example", canonical("technical-example")),
                suite=_version(SUITE_ID, EXPECTATIONS_SHA256),
                inputs=_version("learning-inputs-1", INPUT_SHA256),
                evaluator=_version("learning-evaluator-1", self.code_hash),
                base=base,
                proposed_policy_hash=candidate.content_hash,
                evidence_basis_hashes=(original.basis(),),
            )
            options = dict(evaluation_status=EvaluationStatus.PASSED, retail_policy=policy.retail)
            valid = activation_permitted(target, target, evidence=(original,), **options)
            changed = replace(target, evidence_basis_hashes=(current.basis(),))
            denied = not activation_permitted(target, changed, evidence=(current,), **options)
            applied = GuidanceBinding(
                policy=candidate, activation_revision=base.activation_revision + 1
            )
            rolled = rollback_binding(applied, activated_from=base, activated_to=applied)
            restored = replace(target, base=rolled)
            replay_denied = not activation_permitted(
                target, restored, evidence=(original,), **options
            )
            case_guards = (
                valid
                and denied
                and replay_denied
                and (
                    rolled.policy == base.policy
                    and rolled.activation_revision == base.activation_revision + 2
                )
            )
        values = (
            [n.model_dump(mode="json") for n in notices],
            observation.model_dump(mode="json"),
            {
                "verifier_required": result.outstanding_fields,
                "requested": decision.requested_fields,
            },
            {"verdict": result.verdict, "reasons": result.reasons},
            {"hold": decision.hold_eligible, "review": decision.review_request_eligible},
            decision.current,
            counters,
        )
        return BranchOutput(
            instructions=instructions,
            invariant_hashes=tuple(canonical(v) for v in values),
            checks=(
                Check(name="EXPECTED_SEMANTICS", passed=semantics),
                Check(
                    name="WORDING",
                    passed=_wording_ok(fixture.variant, binding.policy.id, instructions, expected),
                ),
                Check(name="INPUT_PRESERVATION", passed=before == fixture.model_dump_json()),
                Check(name="CASE_GUARDS", passed=case_guards),
            ),
        )

    def run(self, baseline: GuidanceBinding, candidate, *, lease_expires_at=None):
        if (
            not isinstance(baseline, GuidanceBinding)
            or not isinstance(candidate, retail_contracts.PolicyRef)
            or baseline.policy != policy_ref(GuidancePolicyId.V1)
            or candidate != policy_ref(GuidancePolicyId.V2)
        ):
            raise LearningRejected("UNSUPPORTED_POLICY_PAIR")
        # Revalidate preparation immediately before use; no file/I/O reads here.
        self.suite.__post_init__()
        try:
            started, start_mono = self.wall_clock(), self.monotonic_clock()
        except Exception:
            raise LearningRejected("INVALID_CLOCK") from None

        def valid_clock(wall, mono):
            return (
                isinstance(wall, datetime)
                and wall.tzinfo is not None
                and wall.utcoffset() is not None
                and type(mono) in (int, float)
                and math.isfinite(mono)
            )

        if not valid_clock(started, start_mono):
            raise LearningRejected("INVALID_CLOCK")
        deadline = started + timedelta(seconds=self.policy.retail.evaluation_deadline_seconds)
        if lease_expires_at is not None:
            if not isinstance(lease_expires_at, datetime) or lease_expires_at.tzinfo is None:
                raise LearningRejected("INVALID_LEASE")
            deadline = min(deadline, lease_expires_at)
        if deadline <= started:
            raise LearningRejected("EXPIRED_LEASE")
        duration = (deadline - started).total_seconds()
        last_wall, last_mono = started, start_mono
        outputs = []
        failures = ()
        status = ExecutionStatus.PASSED
        finished = None

        def checkpoint():
            nonlocal last_wall, last_mono
            try:
                wall, mono = self.wall_clock(), self.monotonic_clock()
            except Exception:
                raise _ClockInvalid from None
            if not valid_clock(wall, mono) or wall < last_wall or mono < last_mono:
                raise _ClockInvalid
            last_wall, last_mono = wall, mono
            if wall >= deadline or mono - start_mono >= duration:
                raise _Expired
            return wall

        try:
            for fixture in self.suite.inputs.variants:
                checkpoint()
                a = self._branch(fixture, baseline, candidate, started)
                outputs.append(
                    (
                        fixture.case,
                        VariantOutput(variant=fixture.variant, baseline=a, candidate=None),
                    )
                )
                checkpoint()
                b = self._branch(
                    fixture,
                    GuidanceBinding(
                        policy=candidate, activation_revision=baseline.activation_revision
                    ),
                    candidate,
                    started,
                )
                outputs[-1] = (
                    fixture.case,
                    VariantOutput(variant=fixture.variant, baseline=a, candidate=b),
                )
                checkpoint()
            finished = checkpoint()
            if not all(v.passed for _, v in outputs):
                status, failures = ExecutionStatus.FAILED, ("CHECK_FAILED",)
        except _Expired:
            status, failures, finished = ExecutionStatus.EXPIRED, ("DEADLINE_EXCEEDED",), last_wall
        except _ClockInvalid:
            status, failures = ExecutionStatus.FAILED, ("INVALID_CLOCK",)
        except Exception:
            status, failures, finished = ExecutionStatus.FAILED, ("EXECUTION_FAILED",), last_wall
        cases = tuple(
            CaseOutput(case=case, variants=tuple(v for c, v in outputs if c == case))
            for case in LearningCase
            if any(c == case for c, _ in outputs)
        )
        report = LearningExecution(
            input_hash=INPUT_SHA256,
            expectations_hash=EXPECTATIONS_SHA256,
            evaluator_code_hash=self.code_hash,
            configuration_hash=self.policy.digest(),
            baseline=baseline,
            candidate=candidate,
            started_at=started,
            deadline_at=deadline,
            finished_at=finished,
            invariants=INVARIANTS,
            cases=cases,
            status=status,
            failures=failures,
        )
        if len(report.model_dump_json().encode()) > self.policy.retail.evaluation_bytes:
            raise LearningRejected("REPORT_BOUND_EXCEEDED", unaccepted=report)
        # Serialization is bounded work too; crossing the limit cannot yield PASS.
        try:
            checkpoint()
        except _Expired:
            report = LearningExecution.model_validate(
                report.model_dump(round_trip=True)
                | {
                    "status": ExecutionStatus.EXPIRED,
                    "failures": ("DEADLINE_EXCEEDED",),
                    "finished_at": last_wall,
                }
            )
        except _ClockInvalid:
            report = LearningExecution.model_validate(
                report.model_dump(round_trip=True)
                | {
                    "status": ExecutionStatus.FAILED,
                    "failures": ("INVALID_CLOCK",),
                    "finished_at": None,
                }
            )
        if (
            report.status != ExecutionStatus.PASSED
            and len(report.model_dump_json().encode()) > self.policy.retail.evaluation_bytes
        ):
            raise LearningRejected("REPORT_BOUND_EXCEEDED", unaccepted=report)
        return report

"""Pure guidance decisions over explicit server inputs; no admission or mutation.

These predicates are intended for later owned transactional services. Their
execution alone does not authenticate an input or reserve/activate anything.
"""

from typing import Annotated

from pydantic import Field

from batchbeacon.action_service import ActionService
from batchbeacon.contracts import (
    ActionType,
    AuthorityNotice,
    Digest,
    ProductObservation,
    Record,
    VerificationContext,
    VerificationResult,
    VerifierPolicy,
)
from batchbeacon.domain.verifier import is_current_evidence
from batchbeacon.evidence_service import canonical
from batchbeacon.guidance_policies import GuidanceField
from batchbeacon.retail_contracts import EvaluationStatus, GuidanceBinding, VersionRef
from batchbeacon.retail_projection import CapabilityState, capability_view


class GuidanceLimits(Record):
    shared_policy_hash: Digest
    max_recaptures: Annotated[int, Field(ge=0)]
    max_verifications: Annotated[int, Field(gt=0)]

    @classmethod
    def from_shared(cls, policy):
        return cls(
            shared_policy_hash=policy.digest(),
            max_recaptures=policy.max_recaptures,
            max_verifications=policy.max_verifications,
        )


class GuidanceUsage(Record):
    acquisitions: Annotated[int, Field(ge=0)]
    verifications: Annotated[int, Field(ge=0)]


class GuidanceDecision(Record):
    current: bool
    requested_fields: tuple[GuidanceField, ...]
    hold_eligible: bool
    review_request_eligible: bool
    capacity: CapabilityState


def guidance_decision(
    result,
    observation,
    notices,
    context,
    verifier_policy,
    *,
    usage,
    limits,
    capability,
    read_policy,
):
    current = is_current_evidence(result, observation, notices, context, verifier_policy)
    capacity = capability_view(
        capability, context.computed_at, read_policy, observation.session_id, "NEW_VERIFICATION"
    )
    permitted = (
        current
        and capacity.state == CapabilityState.AVAILABLE
        and usage.acquisitions < 1 + limits.max_recaptures
        and usage.verifications < limits.max_verifications
    )
    fields = (
        tuple(
            GuidanceField.PRODUCT_IDENTITY if item == "IDENTITY" else GuidanceField(item)
            for item in result.outstanding_fields
        )
        if permitted
        else ()
    )
    return GuidanceDecision(
        current=current,
        requested_fields=fields,
        hold_eligible=current and ActionService._eligible(result, ActionType.SIMULATED_HOLD),
        review_request_eligible=current
        and ActionService._eligible(result, ActionType.SIMULATED_REVIEW_REQUEST),
        capacity=capacity.state,
    )


def learning_evidence_basis(result, observation, notices, context, verifier_policy):
    return canonical(
        {
            "result": result.digest(),
            "observation": observation.digest(),
            "notices": [n.digest() for n in notices],
            "source_state": context.model_dump(mode="json", exclude={"computed_at"}),
            "verifier": verifier_policy.digest(),
        }
    )


class ActivationBasis(Record):
    candidate: VersionRef
    evaluation: VersionRef
    suite: VersionRef
    inputs: VersionRef
    evaluator: VersionRef
    base: GuidanceBinding
    proposed_policy_hash: Digest
    evidence_basis_hashes: tuple[Digest, ...] = Field(min_length=1)


class LearningEvidence(Record):
    result: VerificationResult
    observation: ProductObservation
    notices: tuple[AuthorityNotice, ...]
    context: VerificationContext
    verifier_policy: VerifierPolicy

    def basis(self):
        return learning_evidence_basis(
            self.result, self.observation, self.notices, self.context, self.verifier_policy
        )

    def current(self):
        return is_current_evidence(
            self.result, self.observation, self.notices, self.context, self.verifier_policy
        )


def activation_permitted(
    confirmation, authoritative, *, evaluation_status, evidence, retail_policy
):
    """Exact binding/currentness predicate, not an authenticated activation route.

    The later service must derive authoritative/evaluation_status from its own
    immutable records and enforce ownership, expiry, limits and confirmation.
    """
    return bool(
        isinstance(evaluation_status, EvaluationStatus)
        and evaluation_status == EvaluationStatus.PASSED
        and confirmation == authoritative
        and 1 <= len(evidence) <= retail_policy.max_support_refs
        and all(isinstance(e, LearningEvidence) for e in evidence)
        and tuple(e.basis() for e in evidence) == authoritative.evidence_basis_hashes
        and all(e.current() for e in evidence)
    )


def rollback_binding(current, *, activated_from, activated_to):
    """Propose a monotonic return to prior content; performs no transition write."""
    if (
        current != activated_to
        or activated_to.activation_revision != activated_from.activation_revision + 1
        or activated_to.policy == activated_from.policy
    ):
        raise ValueError("ROLLBACK_BINDING_CHANGED")
    return GuidanceBinding(
        policy=activated_from.policy, activation_revision=current.activation_revision + 1
    )

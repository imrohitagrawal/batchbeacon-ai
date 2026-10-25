"""Pure T34 computational projection; no persistence, HTTP or action authority.

Creation requires an already coherent server snapshot and reuses full domain
validators before reducing history. A later writer must persist this derivative
atomically; these functions do not establish that storage/read contract.
"""

import hmac
import json
import secrets
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, computed_field, model_validator

from batchbeacon.acquisition import AcquisitionCompletion, StoredCompletion
from batchbeacon.action_service import ActionService, ActionSnapshot
from batchbeacon.contracts import (
    ActionRecord,
    ActionType,
    AuthorityNotice,
    Digest,
    EvidenceRef,
    ProductObservation,
    Record,
    SourceDependency,
    ValueState,
    Verdict,
    VerificationResult,
)
from batchbeacon.domain.verifier import is_current_evidence
from batchbeacon.evidence_service import EvidenceReceipt, EvidenceSnapshot, canonical, replace
from batchbeacon.guest_service import GuestDenied, OpaqueId
from batchbeacon.guidance_policies import GuidanceField
from batchbeacon.retail_contracts import (
    IncidentSummary,
    QueueCategory,
    RetailSnapshot,
    SnapshotStatus,
    VersionRef,
    validate_record,
)
from batchbeacon.shared_admission import SharedPolicy
from batchbeacon.source_context import ContextFact, ContextManifest, RelatedDocuments

Positive = Annotated[int, Field(gt=0)]


class RetailReadPolicy(Record):
    version: Literal["retail-projection-1"] = "retail-projection-1"
    projection_bytes: Positive = 65536
    snapshot_bytes: Positive = 524288
    context_bytes: Positive = 131072
    capability_validity_seconds: Positive = 60

    @model_validator(mode="after")
    def limits(self) -> Self:
        if max(self.projection_bytes, self.context_bytes) >= self.snapshot_bytes:
            raise ValueError("individual projection/context must fit snapshot bound")
        return self


class QueueFilter(StrEnum):
    ALL = "ALL"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    SIMULATED_HOLDS = "SIMULATED_HOLDS"
    NOT_LISTED = "NOT_LISTED"


class CapabilityState(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class CapabilityReason(StrEnum):
    OBSERVED = "OBSERVED"
    NOT_CONNECTED = "NOT_CONNECTED"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    UNOBSERVED = "UNOBSERVED"
    STALE_OBSERVATION = "STALE_OBSERVATION"


class CapabilityObservation(Record):
    session_id: OpaqueId
    capability: Literal["SAVED_EVIDENCE", "NEW_VERIFICATION"]
    state: CapabilityState
    reason: CapabilityReason
    observed_at: AwareDatetime
    valid_until: AwareDatetime

    @model_validator(mode="after")
    def interval(self) -> Self:
        if self.valid_until <= self.observed_at:
            raise ValueError("capability observation requires positive validity")
        if self.state == CapabilityState.AVAILABLE and self.reason != CapabilityReason.OBSERVED:
            raise ValueError("availability requires an actual capability observation")
        return self


class CapabilityView(Record):
    state: CapabilityState
    reason: CapabilityReason
    observed_at: AwareDatetime | None
    valid_until: AwareDatetime | None


def capability_view(value, now, policy, session_id, capability):
    if value is None or value.session_id != session_id or value.capability != capability:
        return CapabilityView(
            state=CapabilityState.UNKNOWN,
            reason=CapabilityReason.UNOBSERVED,
            observed_at=None,
            valid_until=None,
        )
    valid = (
        value.observed_at <= now < value.valid_until
        and (value.valid_until - value.observed_at).total_seconds()
        <= policy.capability_validity_seconds
    )
    return CapabilityView(
        state=value.state if valid else CapabilityState.UNKNOWN,
        reason=value.reason if valid else CapabilityReason.STALE_OBSERVATION,
        observed_at=value.observed_at,
        valid_until=value.valid_until,
    )


class RunProjection(Record):
    id: OpaqueId
    incident_id: OpaqueId
    binding_hash: Digest
    expected_observation_revision: Annotated[int, Field(ge=0)]
    started_at: AwareDatetime
    deadline: AwareDatetime
    completion_hash: Digest | None
    terminal: Literal["completed", "failed", "timed_out"] | None


class CompletionWitness(Record):
    record: AcquisitionCompletion
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AcquisitionBasis(Record):
    extraction: VersionRef | None
    extraction_run_id: OpaqueId | None
    extraction_valid: bool
    provenance: Literal["fake", "replay", "live"] | None
    observation_extraction_revision: Annotated[int, Field(ge=0)]
    original_observation: VersionRef | None
    original_result: VersionRef | None
    original_result_observation_revision: Annotated[int, Field(ge=0)]
    extraction_receipt: EvidenceReceipt | None
    verification_receipt: EvidenceReceipt | None
    completion: CompletionWitness | None

    def current(self, run, session_id, incident_id, observation_count, result_count, now):
        if run is None:
            return bool(
                self.extraction
                and self.extraction_run_id is None
                and self.provenance in {"fake", "replay"}
                and self.extraction_valid
            )
        witness = self.completion
        if (
            witness is None
            or not self.extraction
            or not self.original_observation
            or not self.original_result
            or not self.extraction_receipt
            or not self.verification_receipt
        ):
            return False
        proof = StoredCompletion(witness.record, witness.created_at, witness.updated_at)
        receipt = witness.record
        return bool(
            proof.timely()
            and run.started_at <= witness.created_at <= now
            and run.completion_hash == receipt.digest()
            and (
                receipt.run_id,
                receipt.session_id,
                receipt.incident_id,
                receipt.binding_hash,
                receipt.deadline,
            )
            == (run.id, session_id, incident_id, run.binding_hash, run.deadline)
            and self.extraction_run_id == run.id
            and self.extraction_valid
            and (receipt.extraction_revision, receipt.extraction_hash)
            == (self.extraction.revision, self.extraction.content_hash)
            and (receipt.observation_revision, receipt.observation_hash)
            == (self.original_observation.revision, self.original_observation.content_hash)
            and (receipt.result_revision, receipt.result_hash)
            == (self.original_result.revision, self.original_result.content_hash)
            and self.original_result_observation_revision == receipt.observation_revision
            and receipt.observation_revision == run.expected_observation_revision + 1
            and receipt.observation_revision <= observation_count
            and receipt.result_revision <= result_count
            and self.observation_extraction_revision == self.extraction.revision
            and (
                self.extraction_receipt.kind,
                self.extraction_receipt.key,
                self.extraction_receipt.revision,
            )
            == ("extraction", receipt.extraction_key, receipt.extraction_revision)
            and (
                self.verification_receipt.kind,
                self.verification_receipt.key,
                self.verification_receipt.revision,
            )
            == ("verification", receipt.verification_key, receipt.result_revision)
        )


class MaterialUpdate(Record):
    changed_at: AwareDatetime
    sequence: Annotated[int, Field(ge=1)]
    semantic_state_hash: Digest
    reference: Annotated[str, Field(min_length=1, max_length=160)]


def material_state_hash(snapshot):
    state, usage = snapshot.evidence, snapshot.usage
    incident = next(i for i in snapshot.guest.incidents if i.id == state.incident_id)
    run = next((r for r in reversed(usage.runs) if r.incident_id == state.incident_id), None)
    counter = next(i for i in usage.incidents if i.incident_id == state.incident_id)
    return canonical(
        {
            "incident": incident.model_dump(mode="json"),
            "extraction": state.extractions[-1].digest() if state.extractions else None,
            "observation": state.observations[-1].observation.digest()
            if state.observations
            else None,
            "result": state.results[-1].digest() if state.results else None,
            "active_result": state.active_result,
            "action": snapshot.actions.actions[-1].digest() if snapshot.actions.actions else None,
            "acquisitions": counter.acquisitions,
            "verifications_used": len(counter.verifications),
            "run": {
                "id": run.id,
                "started_at": run.started_at.isoformat(),
                "deadline": run.deadline.isoformat(),
                "terminal": run.terminal,
                "completion_hash": run.completion_hash,
            }
            if run
            else None,
        }
    )


class IncidentProjection(Record):
    version: Literal["retail-incident-1"] = "retail-incident-1"
    session_id: OpaqueId
    incident_id: OpaqueId
    policy_hash: Digest
    evidence_hash: Digest
    action_state_hash: Digest
    usage_basis_hash: Digest
    observation: ProductObservation | None
    original_observation_hash: Digest | None
    observation_count: Annotated[int, Field(ge=0)]
    result: VerificationResult | None
    result_count: Annotated[int, Field(ge=0)]
    active_result: Annotated[int, Field(ge=1)] | None
    capture_refs: tuple[EvidenceRef, ...]
    run: RunProjection | None
    acquisition: AcquisitionBasis
    acquisitions_used: Annotated[int, Field(ge=0)]
    verifications_used: Annotated[int, Field(ge=0)]
    latest_action: ActionRecord | None
    action_original_result_hash: Digest | None
    material: MaterialUpdate

    @model_validator(mode="after")
    def projection_shape(self) -> Self:
        if (self.observation is None) != (self.original_observation_hash is None) or (
            self.observation is None
        ) != (self.observation_count == 0):
            raise ValueError("observation projection requires original lineage")
        if self.observation and (
            self.observation.corrections
            or self.observation.revision != self.observation_count
            or (self.observation.session_id, self.observation.incident_id)
            != (self.session_id, self.incident_id)
        ):
            raise ValueError("current computational input must be latest owned history-free input")
        if (
            (self.result is None) != (self.result_count == 0)
            or self.result
            and (
                self.result.revision != self.result_count
                or self.result.observation_revision > self.observation_count
                or (self.result.session_id, self.result.incident_id)
                != (self.session_id, self.incident_id)
            )
        ):
            raise ValueError("result projection mismatch")
        if self.active_result is not None and (
            self.active_result != self.result_count
            or self.result.observation_revision != self.observation_count
        ):
            raise ValueError("active result must bind latest observation")
        if (self.latest_action is None) != (self.action_original_result_hash is None):
            raise ValueError("action requires original result reference")
        if self.latest_action and (
            self.latest_action.session_id,
            self.latest_action.incident_id,
        ) != (self.session_id, self.incident_id):
            raise ValueError("action owner mismatch")
        if self.run and self.run.incident_id != self.incident_id:
            raise ValueError("run owner mismatch")
        return self


@dataclass(frozen=True)
class PreparedIncident:
    """In-process validated derivative, not a deserializable persistence credential."""

    record: IncidentProjection
    original: bytes = field(repr=False)
    issuer: object = field(repr=False)
    seal: str = field(repr=False)

    def __post_init__(self):
        if self.original != self.record.model_dump_json().encode():
            raise ValueError("prepared_projection_changed")


def usage_basis(usage, incident_id):
    counter = next((i for i in usage.incidents if i.incident_id == incident_id), None)
    if counter is None:
        raise GuestDenied(503, "retail_snapshot_unavailable")
    run = next((r for r in reversed(usage.runs) if r.incident_id == incident_id), None)
    # Own reservations affect whether a requested recapture can be verified.
    return canonical(
        {
            "session_id": usage.session_id,
            "incident_id": incident_id,
            "acquisitions": counter.acquisitions,
            "verifications": [v.model_dump(mode="json") for v in counter.verifications],
            "latest_run": run.model_dump(mode="json") if run else None,
        }
    )


def ref(identity, revision, content_hash):
    return VersionRef(id=identity, revision=revision, content_hash=content_hash)


class NoticeContextView(Record):
    source: SourceDependency
    authority: str | None
    original_url: str | None
    final_url: str | None
    jurisdictions: tuple[str, ...]
    source_url: str | None
    citation_label: str | None
    human_review: Literal["PENDING", "UNKNOWN"]
    reason: ContextFact
    related_documents: RelatedDocuments
    interpretation: Literal["COMPARED_NOTICE", "NOTICE_CONTEXT_ONLY"]


class RowContext(Record):
    incident_id: OpaqueId
    notices: tuple[NoticeContextView, ...]
    action_historical: bool


class RetailView(Record):
    snapshot: RetailSnapshot
    filter: QueueFilter
    visible_incident_ids: tuple[OpaqueId, ...]
    contexts: tuple[RowContext, ...]
    saved_evidence: CapabilityView
    new_verification: CapabilityView
    read_policy_hash: Digest
    context_binding_hash: Digest

    @computed_field
    @property
    def visible_count(self) -> int:
        return len(self.visible_incident_ids)


class RetailProjector:
    def __init__(
        self,
        actions: ActionService,
        shared_policy: SharedPolicy,
        policy: RetailReadPolicy,
        *,
        contexts: ContextManifest | None = None,
        context_notices: tuple[AuthorityNotice, ...] = (),
    ):
        if actions is None or shared_policy.guest_policy_hash != actions.guest.policy.digest():
            raise ValueError("explicit coherent retail services and policy required")
        context_payload = {
            "manifest": contexts.model_dump(mode="json") if contexts else None,
            "notices": [self._notice_metadata(n) for n in context_notices],
        }
        if (
            len(json.dumps(context_payload, sort_keys=True, separators=(",", ":")).encode())
            > policy.context_bytes
        ):
            raise ValueError("context manifest exceeds effective bound")
        if len({n.dependency.digest() for n in context_notices}) != len(context_notices):
            raise ValueError("context source archive contains duplicate dependencies")
        self.context_bindings = {}
        for context in contexts.notices if contexts else ():
            matches = tuple(
                n
                for n in context_notices
                if n.dependency.version == context.source_id
                and n.dependency.content_hash == context.capture_sha256
                and context.source_url in (n.original_url, n.final_url)
            )
            if len(matches) > 1:
                raise ValueError("context has ambiguous source-family binding")
            if matches:
                self.context_bindings[matches[0].dependency.digest()] = context
        self.context_notices = context_notices
        self.context_binding_hash = canonical(context_payload)
        self.actions, self.evidence, self.guest = actions, actions.evidence, actions.guest
        self.shared_policy, self.policy, self.contexts = shared_policy, policy, contexts
        self._issuer = object()
        # An ephemeral in-process integrity guard, never a storage credential or
        # an ownership signature. Pure project/view calls do not allocate keys.
        self._seal_key = secrets.token_bytes(32)

    @staticmethod
    def _notice_metadata(notice):
        return {
            "source": notice.dependency.model_dump(mode="json"),
            "authority": notice.authority,
            "original_url": notice.original_url,
            "final_url": notice.final_url,
            "jurisdictions": notice.jurisdictions,
        }

    def project(self, key, snapshot: ActionSnapshot, *, material: MaterialUpdate):
        """Pure reduction after full ownership/history validation; no storage calls."""
        return self._seal(self._reduce(key, snapshot, material=material))

    def _reduce(self, key, snapshot, *, material, pending_completion=None):
        # A pending immutable receipt selects original lineage only. It cannot
        # supply a completion timestamp or make an acquisition current.
        if snapshot.evidence is None:
            raise GuestDenied(503, "retail_snapshot_unavailable")
        state = snapshot.evidence
        action_state = self.actions._check(snapshot, key, state.incident_id)
        evidence_snapshot = EvidenceSnapshot(
            snapshot.guest, state, snapshot.environment, snapshot.usage, snapshot.completion
        )
        for extraction in state.extractions:
            self.evidence._ready(evidence_snapshot, state.incident_id, extraction.envelope.captures)
        usage = snapshot.usage
        counter = (
            next((i for i in usage.incidents if i.incident_id == state.incident_id), None)
            if usage
            else None
        )
        if counter is None or usage.session_id != state.session_id:
            raise GuestDenied(503, "retail_snapshot_unavailable")
        run = self.evidence._latest_run(evidence_snapshot, state)
        selected = state.observations[-1] if state.observations else None
        obs = selected.observation if selected else None
        extraction = state.extractions[-1] if state.extractions else None
        proof = snapshot.completion
        receipt = proof.record if proof else pending_completion
        original_obs = next(
            (
                o.observation
                for o in state.observations
                if receipt and o.observation.revision == receipt.observation_revision
            ),
            None,
        )
        original_result = next(
            (r for r in state.results if receipt and r.revision == receipt.result_revision), None
        )
        action = action_state.actions[-1] if action_state.actions else None
        action_result = next(
            (r for r in state.results if action and r.revision == action.result_revision), None
        )
        if material.semantic_state_hash != material_state_hash(snapshot) or not (
            snapshot.guest.scope.issued_at <= material.changed_at <= self.guest._now()
        ):
            raise GuestDenied(503, "retail_material_state_unavailable")
        result = IncidentProjection(
            session_id=state.session_id,
            incident_id=state.incident_id,
            policy_hash=self.configuration_hash,
            evidence_hash=state.digest(),
            action_state_hash=action_state.digest(),
            usage_basis_hash=usage_basis(usage, state.incident_id),
            observation=replace(obs, corrections=()) if obs else None,
            original_observation_hash=obs.digest() if obs else None,
            observation_count=len(state.observations),
            result=state.results[-1] if state.results else None,
            result_count=len(state.results),
            active_result=state.active_result,
            capture_refs=tuple(
                dict.fromkeys(r for e in state.extractions for r in e.envelope.captures)
            ),
            run=RunProjection(
                id=run.id,
                incident_id=run.incident_id,
                binding_hash=run.binding.digest(),
                expected_observation_revision=run.binding.expected_observation_revision,
                started_at=run.started_at,
                deadline=run.deadline,
                completion_hash=run.completion_hash,
                terminal=run.terminal,
            )
            if run
            else None,
            acquisition=AcquisitionBasis(
                extraction=ref("extraction", extraction.revision, extraction.digest())
                if extraction
                else None,
                extraction_run_id=extraction.run_id if extraction else None,
                extraction_valid=bool(extraction and extraction.envelope.validation == "VALID"),
                provenance=extraction.envelope.provenance if extraction else None,
                observation_extraction_revision=selected.extraction_revision if selected else 0,
                original_observation=ref(
                    "observation", original_obs.revision, original_obs.digest()
                )
                if original_obs
                else None,
                original_result=ref("result", original_result.revision, original_result.digest())
                if original_result
                else None,
                original_result_observation_revision=(
                    original_result.observation_revision if original_result else 0
                ),
                extraction_receipt=next(
                    (
                        r
                        for r in state.receipts
                        if receipt and r.kind == "extraction" and r.key == receipt.extraction_key
                    ),
                    None,
                ),
                verification_receipt=next(
                    (
                        r
                        for r in state.receipts
                        if receipt
                        and r.kind == "verification"
                        and r.key == receipt.verification_key
                    ),
                    None,
                ),
                completion=CompletionWitness(
                    record=receipt, created_at=proof.created_at, updated_at=proof.updated_at
                )
                if proof
                else None,
            ),
            acquisitions_used=counter.acquisitions,
            verifications_used=len(counter.verifications),
            latest_action=action,
            action_original_result_hash=action_result.digest() if action_result else None,
            material=material,
        )
        self._bound(result, self.policy.projection_bytes)
        self.guest._live(snapshot.guest, key)
        return result

    def _seal(self, result):
        original = result.model_dump_json().encode()
        return PreparedIncident(
            result, original, self._issuer, hmac.digest(self._seal_key, original, "sha256").hex()
        )

    @property
    def configuration_hash(self):
        return canonical(
            {
                "read": self.policy.digest(),
                "guest": self.guest.policy.digest(),
                "evidence": self.evidence.policy.digest(),
                "action": self.actions.policy.digest(),
                "shared": self.shared_policy.digest(),
            }
        )

    @staticmethod
    def _bound(record, maximum):
        if len(record.model_dump_json().encode()) > maximum:
            raise GuestDenied(503, "retail_snapshot_unavailable")

    def _row(self, projection, guest, environment, now, capability):
        p, result, obs = projection, projection.result, projection.observation
        ready = {
            (c.id, c.sha256)
            for i in guest.incidents
            if i.id == p.incident_id
            for batch in i.batches
            if batch.ready
            for c in batch.captures
        }
        captures_ready = all((r.artifact_id, r.sha256) in ready for r in p.capture_refs)
        current = bool(
            result
            and obs
            and p.active_result == result.revision
            and captures_ready
            and p.acquisition.current(
                p.run, p.session_id, p.incident_id, p.observation_count, p.result_count, now
            )
            and is_current_evidence(
                result,
                obs,
                environment.notices,
                environment.at(now, p.result_count),
                environment.verifier_policy,
            )
        )
        action = p.latest_action
        action_current = bool(
            current
            and action
            and p.action_original_result_hash == result.digest()
            and action.observation_revision == obs.revision
            and action.sources == result.checked_sources
            and self.actions._eligible(result, action.action_type)
        )
        fields = (
            tuple(
                GuidanceField.PRODUCT_IDENTITY if name == "IDENTITY" else GuidanceField(name)
                for name in result.outstanding_fields
            )
            if result
            else ()
        )
        running = bool(
            p.run and p.run.terminal is None and p.run.started_at <= now < p.run.deadline
        )
        if result and not current:
            category = QueueCategory.RENEWED_REVIEW
        elif action_current:
            category = QueueCategory.ACTION_RECORDED
        elif not current and (running or (p.run is None and p.acquisition.extraction is None)):
            category = QueueCategory.IN_PROGRESS
        elif (
            current
            and fields
            and capability.state == CapabilityState.AVAILABLE
            and p.acquisitions_used < 1 + self.shared_policy.max_recaptures
            and p.verifications_used < self.shared_policy.max_verifications
        ):
            category = QueueCategory.NEEDS_EVIDENCE
        elif current and result.verdict == Verdict.NOT_LISTED_IN_CHECKED_NOTICES:
            category = QueueCategory.NOT_LISTED
        else:
            category = QueueCategory.HUMAN_REVIEW
        return IncidentSummary(
            incident_id=p.incident_id,
            product_name=obs.identity.name.value
            if obs and obs.identity.name.state == ValueState.KNOWN
            else "Product identity not established",
            jurisdiction=result.jurisdiction if result else "Not checked",
            source_mode=result.mode if result else environment.context.mode,
            checked_sources=result.checked_sources if result else (),
            observation_revision=p.observation_count,
            result=ref("result", result.revision, result.digest()) if result else None,
            verdict=result.verdict if result else None,
            current=current,
            currentness_hash=canonical(
                {
                    "projection": p.digest(),
                    "environment": environment.digest(),
                    "current": current,
                    "evaluated_at": now.isoformat(),
                }
            ),
            reasons=result.reasons if result else (),
            outstanding_fields=fields,
            category=category,
            stage=("SAVED_REVIEW" if action_current else "COMPARISON_READY" if current
                   else "CHECK_PENDING" if running else "CHECK_INCOMPLETE" if p.run
                   else "LABEL_READY" if ready else "LABEL_REQUIRED"),
            latest_action=ref(action.id, action.result_revision, action.digest())
            if action
            else None,
            action_type=action.action_type if action else None,
            uncertainty_unresolved=bool(
                action_current and action.action_type == ActionType.SIMULATED_REVIEW_REQUEST
            ),
            last_material_update=p.material.changed_at,
        )

    def _context(self, row, environment):
        items = []
        for source in row.checked_sources:
            context = self.context_bindings.get(source.digest())
            notice = next(
                (
                    n
                    for n in (*self.context_notices, *environment.notices)
                    if n.dependency == source
                ),
                None,
            )
            items.append(
                NoticeContextView(
                    source=source,
                    authority=notice.authority if notice else None,
                    original_url=notice.original_url if notice else None,
                    final_url=notice.final_url if notice else None,
                    jurisdictions=notice.jurisdictions if notice else (),
                    source_url=context.source_url if context else None,
                    citation_label=context.citation_label if context else None,
                    human_review=context.human_review if context else "UNKNOWN",
                    reason=context.reason
                    if context
                    else ContextFact(
                        state="UNKNOWN",
                        text=None,
                        locator="Context unavailable for this exact notice version and capture",
                    ),
                    related_documents=context.related_documents
                    if context
                    else RelatedDocuments(
                        state="UNKNOWN", documents=(), locator="No exact bound context available"
                    ),
                    interpretation="COMPARED_NOTICE"
                    if row.verdict == Verdict.NOT_LISTED_IN_CHECKED_NOTICES
                    else "NOTICE_CONTEXT_ONLY",
                )
            )
        return RowContext(
            incident_id=row.incident_id,
            notices=tuple(items),
            action_historical=bool(
                row.latest_action and row.category != QueueCategory.ACTION_RECORDED
            ),
        )

    def view(
        self,
        key,
        guest,
        usage,
        projections,
        environment,
        *,
        selected_filter=QueueFilter.ALL,
        saved_evidence=None,
        new_verification=None,
    ):
        """Derive a bounded shop snapshot; callers must supply an atomic read basis."""
        guest = self.guest._live(guest, key)
        now = self.guest._now()
        if (
            not isinstance(selected_filter, QueueFilter)
            or environment is None
            or usage is None
            or usage.session_id != guest.scope.session_id
        ):
            raise GuestDenied(503, "retail_snapshot_unavailable")
        records = []
        for prepared in projections:
            if (
                not isinstance(prepared, PreparedIncident)
                or prepared.issuer is not self._issuer
                or prepared.original != prepared.record.model_dump_json().encode()
                or not hmac.compare_digest(
                    prepared.seal, hmac.digest(self._seal_key, prepared.original, "sha256").hex()
                )
            ):
                raise GuestDenied(503, "retail_projection_not_prepared")
            records.append(prepared.record)
        projections = tuple(records)
        capability = capability_view(
            new_verification, now, self.policy, guest.scope.session_id, "NEW_VERIFICATION"
        )
        ids = {i.id for i in guest.incidents}
        if (
            len(ids) != len(guest.incidents)
            or len(usage.incidents) != len(ids)
            or {i.incident_id for i in usage.incidents} != ids
            or len(projections) != len(ids)
            or {p.incident_id for p in projections} != ids
            or len(ids)
            > min(self.guest.policy.retail.max_incidents, self.guest.policy.retail.max_summary_rows)
        ):
            raise GuestDenied(503, "retail_snapshot_unavailable")
        for p in projections:
            self._bound(p, self.policy.projection_bytes)
            if (
                p.session_id != guest.scope.session_id
                or p.policy_hash != self.configuration_hash
                or p.usage_basis_hash != usage_basis(usage, p.incident_id)
                or not guest.scope.issued_at <= p.material.changed_at <= now
            ):
                raise GuestDenied(503, "retail_snapshot_unavailable")
        rows = tuple(
            sorted(
                (self._row(p, guest, environment, now, capability) for p in projections),
                key=lambda row: (-row.last_material_update.timestamp(), row.incident_id),
            )
        )
        basis = canonical(
            {
                "projections": [
                    p.digest() for p in sorted(projections, key=lambda p: p.incident_id)
                ],
                "environment": environment.digest(),
                "policy": self.configuration_hash,
                "evaluated_at": now.isoformat(),
                "new_verification": capability.model_dump(mode="json"),
                "context_binding": self.context_binding_hash,
            }
        )
        snapshot = RetailSnapshot(
            id=basis,
            scope=guest.scope,
            created_at=now,
            generated_at=now,
            effective_policy_hash=self.guest.policy.retail.digest(),
            currentness_basis_hash=basis,
            current_sources=environment.context.current_sources,
            status=SnapshotStatus.CURRENT,
            rows=rows,
        )
        validate_record(
            snapshot, policy=self.guest.policy.retail, server_scope=guest.scope, now=now
        )
        attention = {
            QueueCategory.RENEWED_REVIEW,
            QueueCategory.NEEDS_EVIDENCE,
            QueueCategory.HUMAN_REVIEW,
        }

        def visible(row):
            return (
                selected_filter == QueueFilter.ALL
                or (selected_filter == QueueFilter.NEEDS_ATTENTION and row.category in attention)
                or (
                    selected_filter == QueueFilter.SIMULATED_HOLDS
                    and row.category == QueueCategory.ACTION_RECORDED
                    and row.action_type == ActionType.SIMULATED_HOLD
                )
                or (
                    selected_filter == QueueFilter.NOT_LISTED
                    and row.category == QueueCategory.NOT_LISTED
                )
            )

        value = RetailView(
            snapshot=snapshot,
            filter=selected_filter,
            visible_incident_ids=tuple(r.incident_id for r in rows if visible(r)),
            contexts=tuple(self._context(row, environment) for row in rows),
            saved_evidence=capability_view(
                saved_evidence, now, self.policy, guest.scope.session_id, "SAVED_EVIDENCE"
            ),
            new_verification=capability,
            read_policy_hash=self.policy.digest(),
            context_binding_hash=self.context_binding_hash,
        )
        self._bound(value, self.policy.snapshot_bytes)
        self.guest._live(guest, key)  # Recheck immediate expiry after computation.
        return value

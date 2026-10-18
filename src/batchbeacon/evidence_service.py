"""Owned append-only evidence protocol. No HTTP, provider or concrete cloud adapter.

Provision EvidenceState atomically with each guest incident. Store implementations
must read guest, evidence, source environment and shared usage in one transaction.
Only trusted extraction code calls record_extraction; no client result is accepted.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, model_validator

from batchbeacon.contracts import (
    AuthorityNotice,
    Correction,
    Digest,
    EvidenceRef,
    Nonempty,
    ObservedIdentifier,
    ObservedPredicate,
    ObservedValue,
    ProductIdentity,
    ProductObservation,
    Record,
    SourceDependency,
    VerificationContext,
    VerificationResult,
    VerifierPolicy,
)
from batchbeacon.domain.verifier import is_current, verify
from batchbeacon.guest_service import GuestDenied, GuestService, GuestSession, OpaqueId, RequestKey
from batchbeacon.shared_admission import SessionUsage


def replace(record, **updates):
    """Validate replacements; BaseModel.model_copy does not validate updates."""
    return type(record).model_validate(record.model_dump() | updates)


def canonical(value) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class EvidencePolicy(Record):
    version: Nonempty = "owned-evidence-1"
    max_raw_bytes: Annotated[int, Field(gt=0)] = 32768
    max_state_bytes: Annotated[int, Field(gt=0)] = 524288
    max_extractions: Annotated[int, Field(gt=0)] = 3
    max_observations: Annotated[int, Field(gt=0)] = 24
    max_receipts: Annotated[int, Field(gt=0)] = 40

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.max_raw_bytes >= self.max_state_bytes:
            raise ValueError("raw output must fit the state byte bound")
        if self.max_receipts < max(self.max_observations, self.max_extractions):
            raise ValueError("receipt capacity must cover each history limit")
        return self


class ExtractedIdentity(Record):
    # Deliberately has no reviewed resolution, source trust, ownership or verdict.
    name: ObservedValue
    pack: ObservedValue
    identifiers: tuple[ObservedIdentifier, ...] = ()


class ExtractedValues(Record):
    identity: ExtractedIdentity
    fields: tuple[ObservedPredicate, ...]


class ExtractionEnvelope(Record):
    """Internal adapter output, explicitly labelled; storage is not model proof.

    The T10 adapter must redact the original structured response before supplying
    it here, and substantiate live/model/config provenance from its actual receipt.
    Source proposals remain in this original output, never in AuthorityNotice.
    """
    provenance: Literal["fake", "replay", "live"]
    redacted_output_json: str
    validation: Literal["VALID", "INVALID"]
    validation_codes: tuple[Nonempty, ...] = ()
    values: ExtractedValues | None
    model_id: Nonempty
    prompt_version: Nonempty
    configuration_hash: Digest
    sources: tuple[SourceDependency, ...]
    captures: tuple[EvidenceRef, ...] = Field(min_length=1)
    started_at: datetime
    completed_at: datetime

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.started_at.tzinfo is None or self.completed_at.tzinfo is None:
            raise ValueError("extraction times require timezone")
        if self.completed_at < self.started_at:
            raise ValueError("extraction timing is reversed")
        if (self.validation == "VALID") != (self.values is not None):
            raise ValueError("only validated extraction has values")
        if self.validation == "INVALID" and not self.validation_codes:
            raise ValueError("invalid extraction requires diagnostic codes")
        if self.validation == "VALID" and self.validation_codes:
            raise ValueError("validated extraction cannot have failure codes")
        # A failed attempt can contain malformed/empty attempted JSON. Preserve
        # those original redacted bytes with its diagnostic rather than discard
        # the failed evidence or manufacture a successful structured response.
        if self.validation == "VALID":
            parsed = json.loads(self.redacted_output_json)
            if not isinstance(parsed, dict):
                raise ValueError("validated structured response must be an object")
        return self


class SavedExtraction(Record):
    revision: Annotated[int, Field(ge=1)]
    recorded_at: datetime
    envelope: ExtractionEnvelope


class SavedObservation(Record):
    extraction_revision: Annotated[int, Field(ge=1)]
    observation: ProductObservation


class EvidenceReceipt(Record):
    key: RequestKey
    payload_hash: Digest
    kind: Literal["extraction", "correction", "verification"]
    revision: Annotated[int, Field(ge=1)]


class EvidenceState(Record):
    session_id: OpaqueId
    incident_id: OpaqueId
    policy_hash: Digest
    extractions: tuple[SavedExtraction, ...] = ()
    observations: tuple[SavedObservation, ...] = ()
    results: tuple[VerificationResult, ...] = ()
    receipts: tuple[EvidenceReceipt, ...] = ()
    active_result: Annotated[int, Field(ge=1)] | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if tuple(e.revision for e in self.extractions) != tuple(
            range(1, len(self.extractions) + 1)
        ):
            raise ValueError("extraction history is not contiguous")
        if tuple(o.observation.revision for o in self.observations) != tuple(
            range(1, len(self.observations) + 1)
        ):
            raise ValueError("observation history is not contiguous")
        for item in self.observations:
            obs = item.observation
            if obs.session_id != self.session_id or obs.incident_id != self.incident_id:
                raise ValueError("observation owner mismatch")
            if item.extraction_revision > len(self.extractions):
                raise ValueError("missing original extraction")
            original = self.extractions[item.extraction_revision - 1].envelope
            if original.validation != "VALID" or (obs.model_id, obs.prompt_version) != (
                original.model_id, original.prompt_version
            ):
                raise ValueError("observation provenance mismatch")
        if tuple(r.revision for r in self.results) != tuple(range(1, len(self.results) + 1)):
            raise ValueError("result history is not contiguous")
        for result in self.results:
            if result.session_id != self.session_id or result.incident_id != self.incident_id \
                    or result.observation_revision > len(self.observations):
                raise ValueError("result owner or observation mismatch")
        if self.active_result is not None:
            if self.active_result != len(self.results) or self.results[-1].observation_revision \
                    != len(self.observations):
                raise ValueError("active result must use the latest observation/result")
        if len({r.key for r in self.receipts}) != len(self.receipts):
            raise ValueError("duplicate operation keys")
        lengths = {"extraction": len(self.extractions), "correction": len(self.observations),
                   "verification": len(self.results)}
        if any(r.revision > lengths[r.kind] for r in self.receipts):
            raise ValueError("receipt points outside history")
        return self


class EvidenceEnvironment(Record):
    """Server-owned catalog/context snapshot; never supplied by the browser/model."""
    context: VerificationContext
    notices: tuple[AuthorityNotice, ...]
    verifier_policy: VerifierPolicy

    def at(self, now: datetime, result_revision: int) -> VerificationContext:
        return replace(self.context, computed_at=now, result_revision=result_revision)


@dataclass(frozen=True)
class EvidenceSnapshot:
    guest: GuestSession | None
    state: EvidenceState | None
    environment: EvidenceEnvironment | None
    usage: SessionUsage | None = None


class EvidenceStore(Protocol):
    """Atomic snapshot + replace only evidence, with unchanged snapshot on reads.

    Serialize/validate records. Missing/corrupt state is failure, never first use.
    Provision an empty EvidenceState atomically when creating each owned incident.
    Read current guest, catalog/context and usage in the same transaction. Retry
    only pure callbacks, return the committed state, and preserve other domains
    (captures, shared usage, historical actions). Lost ack must not undo commits.
    """
    def transact(
        self, guest_key: str, incident_id: str,
        change: Callable[[EvidenceSnapshot], EvidenceState],
    ) -> EvidenceState: ...


@dataclass(frozen=True)
class EvidenceView:
    state: EvidenceState
    observation: ProductObservation | None
    result: VerificationResult | None
    current: bool
    hold_eligible: bool


class EvidenceService:
    def __init__(self, guest: GuestService, store: EvidenceStore, policy: EvidencePolicy):
        if store is None:
            raise ValueError("explicit evidence store required")
        self.guest, self.store, self.policy = guest, store, policy

    def _check(self, snapshot, key, incident_id):
        guest = self.guest._live(snapshot.guest, key)
        self.guest._incident(guest, incident_id)
        state = snapshot.state
        if state is None or state.session_id != guest.scope.session_id \
                or state.incident_id != incident_id or state.policy_hash != self.policy.digest():
            raise GuestDenied(503, "evidence_state_unavailable")
        self._limits(state)
        return state

    def _limits(self, state):
        if len(state.extractions) > self.policy.max_extractions \
                or len(state.observations) > self.policy.max_observations \
                or len(state.receipts) > self.policy.max_receipts \
                or len(state.model_dump_json().encode()) > self.policy.max_state_bytes:
            raise GuestDenied(429, "evidence_history_limit")
        return state

    def _transaction(self, capability, incident_id, operation):
        key = self.guest._key(capability)
        result = self.guest._storage(self.store.transact, key, incident_id, operation)
        self.guest.resolve(capability)  # Storage completion cannot outlive the guest.
        return result

    @staticmethod
    def _receipt(state, key, payload):
        prior = next((r for r in state.receipts if r.key == key), None)
        if prior and prior.payload_hash != payload:
            raise GuestDenied(409, "evidence_request_conflict")
        return prior

    def _append(self, state, receipt, **updates):
        return self._limits(replace(state, receipts=(*state.receipts, receipt), **updates))

    @staticmethod
    def _ready(snapshot, incident_id, refs):
        incident = GuestService._incident(snapshot.guest, incident_id)
        ready = {(c.id, c.sha256) for b in incident.batches if b.ready for c in b.captures}
        if not refs or any(r.kind.value != "CAPTURE" or (r.artifact_id, r.sha256) not in ready
                           for r in refs):
            raise GuestDenied(422, "capture_evidence_unavailable")

    def _retained(self, capability, incident_id, refs):
        # Object reads never occur inside retryable transactions.
        for ref in refs:
            data = self.guest.image(capability, incident_id, ref.artifact_id)
            if sha256(data).hexdigest() != ref.sha256:
                raise GuestDenied(422, "capture_evidence_unavailable")

    def _extraction_sources(self, snapshot, sources):
        environment = self._environment(snapshot)
        selected = tuple(notice.dependency for notice in environment.notices)
        provided = {dependency.family: dependency for dependency in sources}
        expected = {dependency.family: dependency for dependency in selected}
        current = {dependency.family: dependency
                   for dependency in environment.context.current_sources}
        if not selected or len(provided) != len(sources) or len(expected) != len(selected) \
                or len(current) != len(environment.context.current_sources) \
                or provided != expected \
                or any(current.get(family) != dependency
                       for family, dependency in expected.items()):
            raise GuestDenied(409, "extraction_sources_changed")

    def record_extraction(self, capability, incident_id, request_key, expected_revision,
                          envelope: ExtractionEnvelope) -> EvidenceReceipt:
        """INTERNAL trusted-adapter API; never deserialize it from a guest endpoint."""
        if type(expected_revision) is not int or expected_revision < 0:
            raise GuestDenied(422, "observation_revision_invalid")
        payload = canonical({"kind": "extraction", "expected": expected_revision,
                             "envelope": envelope.model_dump(mode="json")})
        now = self.guest._now()
        if len(envelope.redacted_output_json.encode()) > self.policy.max_raw_bytes \
                or envelope.completed_at > now:
            raise GuestDenied(422, "extraction_envelope_invalid")
        self._retained(capability, incident_id, envelope.captures)
        key = self.guest._key(capability)

        def change(snapshot):
            state = self._check(snapshot, key, incident_id)
            if self._receipt(state, request_key, payload):
                return state
            if len(state.observations) != expected_revision:
                raise GuestDenied(409, "observation_changed")
            if envelope.validation == "VALID":
                # Only new publication needs this fresh binding. Identical committed
                # retries above reconcile history; explicit failures retain their
                # original attempted source without producing an observation.
                self._extraction_sources(snapshot, envelope.sources)
            if envelope.started_at < snapshot.guest.scope.issued_at:
                raise GuestDenied(422, "extraction_envelope_invalid")
            self._ready(snapshot, incident_id, envelope.captures)
            saved = SavedExtraction(revision=len(state.extractions) + 1,
                                    recorded_at=now, envelope=envelope)
            observations = state.observations
            if envelope.values is not None:
                identity = ProductIdentity(**envelope.values.identity.model_dump())
                obs = ProductObservation(
                    session_id=state.session_id, incident_id=incident_id,
                    revision=len(observations) + 1, captures=envelope.captures,
                    identity=identity, fields=envelope.values.fields,
                    model_id=envelope.model_id, prompt_version=envelope.prompt_version,
                )
                observations = (*observations, SavedObservation(
                    extraction_revision=saved.revision, observation=obs))
            return self._append(state, EvidenceReceipt(key=request_key, payload_hash=payload,
                                kind="extraction", revision=saved.revision),
                                extractions=(*state.extractions, saved),
                                observations=observations, active_result=None)

        state = self._transaction(capability, incident_id, change)
        return self._receipt(state, request_key, payload)

    def correct(self, capability, incident_id, request_key, expected_revision,
                field: str, replacement: ObservedValue) -> EvidenceReceipt:
        if type(expected_revision) is not int or expected_revision < 1:
            raise GuestDenied(422, "observation_revision_invalid")
        payload = canonical({"kind": "correction", "expected": expected_revision,
                             "field": field, "replacement": replacement.model_dump(mode="json")})
        key, now = self.guest._key(capability), self.guest._now()
        self._retained(capability, incident_id, replacement.evidence)

        def change(snapshot):
            state = self._check(snapshot, key, incident_id)
            if self._receipt(state, request_key, payload):
                return state
            if not state.observations or len(state.observations) != expected_revision:
                raise GuestDenied(409, "observation_changed")
            saved = state.observations[-1]
            obs = saved.observation
            # Restrict corrections to already retained input panels. Recapture is
            # a new extraction with its own input identity and lifetime admission.
            self._ready(snapshot, incident_id, obs.captures)
            targets = []
            if field in {"PRODUCT_NAME", "PACK"}:
                targets.append(("identity", "name" if field == "PRODUCT_NAME" else "pack"))
            targets.extend(("field", i) for i, v in enumerate(obs.fields) if v.field.value == field)
            targets.extend(("code", i) for i, v in enumerate(obs.identity.identifiers)
                           if v.kind.value == field)
            if len(targets) != 1:
                raise GuestDenied(422, "correction_target_unsupported")
            kind, index = targets[0]
            if kind == "identity":
                previous = getattr(obs.identity, index)
                identity = replace(obs.identity, **{index: replacement}, resolved_name=None,
                                   resolution_review_hash=None)
                fields = obs.fields
            elif kind == "field":
                previous = obs.fields[index].observation
                fields = tuple(replace(v, observation=replacement) if i == index else v
                               for i, v in enumerate(obs.fields))
                identity = obs.identity
            else:
                previous = obs.identity.identifiers[index].observation
                identity = replace(obs.identity, identifiers=tuple(
                    replace(v, observation=replacement) if i == index else v
                    for i, v in enumerate(obs.identity.identifiers)),
                    resolved_name=None, resolution_review_hash=None)
                fields = obs.fields
            if replacement.value_type != previous.value_type:
                raise GuestDenied(422, "correction_type_mismatch")
            correction = Correction(field=field, previous=previous, replacement=replacement,
                                    actor_session=state.session_id, recorded_at=now)
            updated = replace(obs, revision=obs.revision + 1, identity=identity, fields=fields,
                              corrections=(*obs.corrections, correction))
            return self._append(state, EvidenceReceipt(key=request_key, payload_hash=payload,
                                kind="correction", revision=updated.revision),
                                observations=(*state.observations, SavedObservation(
                                    extraction_revision=saved.extraction_revision,
                                    observation=updated)), active_result=None)

        state = self._transaction(capability, incident_id, change)
        return self._receipt(state, request_key, payload)

    @staticmethod
    def _environment(snapshot):
        if snapshot.environment is None:
            raise GuestDenied(503, "source_state_unavailable")
        return snapshot.environment

    def _binding(self, snapshot, state):
        if not state.observations:
            raise GuestDenied(409, "observation_required")
        if state.extractions[-1].envelope.validation != "VALID" \
                or state.observations[-1].extraction_revision != len(state.extractions):
            # A new failed acquisition invalidates earlier evidence for fresh
            # decisions. Editing or replaying the older successful receipt cannot
            # erase that failure. Recovery requires new validated extraction.
            raise GuestDenied(409, "latest_extraction_invalid")
        return canonical({"observation": state.observations[-1].observation.digest(),
                          "environment": self._environment(snapshot).digest(),
                          "next_result_revision": len(state.results) + 1,
                          "evidence_policy": self.policy.digest()})

    def verification_binding(self, capability, incident_id) -> str:
        """Internal input to SharedAdmission.reserve_verification, not a grant.

        Its context_state_hash slot must carry THIS combined digest, which binds
        the observation as well as sources/context/policy. No quota is spent here.
        """
        checked = self.read_evidence(capability, incident_id).state.digest()
        key = self.guest._key(capability)
        binding = []

        def read(snapshot):
            state = self._check(snapshot, key, incident_id)
            if state.digest() != checked:
                raise GuestDenied(409, "verification_dependencies_changed")
            binding[:] = [self._binding(snapshot, state)]
            return state

        self._transaction(capability, incident_id, read)
        return binding[0]

    def publish_verification(
        self, capability, incident_id, request_key, binding
    ) -> EvidenceReceipt:
        """Internal deterministic result computation; no client result accepted.

        Shared admission must already have reserved this exact key + binding.
        Compute and publish in the same pure transaction over the fresh catalog,
        observation and reservation; retries recompute rather than publish stale work.
        """
        checked = self.read_evidence(capability, incident_id).state.digest()
        key, now = self.guest._key(capability), self.guest._now()
        payload = canonical({"kind": "verification", "binding": binding})

        def change(snapshot):
            state = self._check(snapshot, key, incident_id)
            if self._receipt(state, request_key, payload):
                return state
            if state.digest() != checked or self._binding(snapshot, state) != binding:
                raise GuestDenied(409, "verification_dependencies_changed")
            usage = snapshot.usage
            counter = next((i for i in usage.incidents if i.incident_id == incident_id), None) \
                if usage and usage.session_id == state.session_id else None
            reservation = next((r for r in counter.verifications if r.request_key == request_key),
                               None) if counter else None
            if reservation is None or reservation.context_state_hash != binding:
                raise GuestDenied(409, "verification_reservation_required")
            environment = self._environment(snapshot)
            result = verify(state.observations[-1].observation, environment.notices,
                            environment.at(now, len(state.results) + 1),
                            environment.verifier_policy)
            return self._append(state, EvidenceReceipt(key=request_key, payload_hash=payload,
                                kind="verification", revision=result.revision),
                                results=(*state.results, result), active_result=result.revision)

        state = self._transaction(capability, incident_id, change)
        return self._receipt(state, request_key, payload)

    def read_evidence(self, capability, incident_id, revision=None) -> EvidenceView:
        key = self.guest._key(capability)
        views, environments = [], []

        def read(snapshot):
            state = self._check(snapshot, key, incident_id)
            environment = self._environment(snapshot)
            for saved in state.extractions:
                self._ready(snapshot, incident_id, saved.envelope.captures)
            selected = len(state.observations) if revision is None else revision
            if selected != 0 and (type(selected) is not int or not 1 <= selected <= len(
                state.observations
            )) or (selected == 0 and revision is not None):
                raise GuestDenied(404, "evidence_unavailable")
            obs = state.observations[selected - 1].observation if selected else None
            result = next((r for r in reversed(state.results)
                           if obs and r.observation_revision == obs.revision), None)
            current = bool(result and state.active_result == result.revision
                           and obs.revision == len(state.observations)
                           and is_current(result, observation_revision=obs.revision,
                               context=environment.at(self.guest._now(), len(state.results)),
                               policy=environment.verifier_policy))
            environments[:] = [environment]
            views[:] = [EvidenceView(state, obs, result, current,
                                     bool(current and result.hold_eligible))]
            return state

        self._transaction(capability, incident_id, read)
        checked = views[0].state.digest()
        refs = tuple(ref for saved in views[0].state.extractions
                     for ref in saved.envelope.captures)
        self._retained(capability, incident_id, refs)
        # Re-read current state after potentially slow retained-object checks.
        self._transaction(capability, incident_id, read)
        if views[0].state.digest() != checked:
            raise GuestDenied(409, "evidence_changed_during_read")
        value = views[0]
        # The final repository acknowledgment can itself cross a source freshness
        # boundary. Recompute time-derived eligibility after all storage work.
        current = bool(value.current and is_current(value.result,
            observation_revision=value.observation.revision,
            context=environments[0].at(self.guest._now(), len(value.state.results)),
            policy=environments[0].verifier_policy))
        return EvidenceView(value.state, value.observation, value.result, current,
                            bool(current and value.result.hold_eligible))

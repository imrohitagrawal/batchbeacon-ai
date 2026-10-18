"""Explicit simulated actions over a single owned transaction snapshot.

No HTTP route, concrete database, real stock action or model operation. Real
adapters must provide the transaction semantics and CSRF boundary separately.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Protocol, Self
from uuid import uuid4

from pydantic import Field, model_validator

from batchbeacon.contracts import (
    ActionRecord,
    ActionType,
    Digest,
    IncidentEvent,
    Nonempty,
    Record,
    Revision,
    Verdict,
)
from batchbeacon.domain.verifier import VERIFIER_VERSION, is_current
from batchbeacon.evidence_service import (
    EvidenceEnvironment,
    EvidenceService,
    EvidenceSnapshot,
    EvidenceState,
    canonical,
    replace,
)
from batchbeacon.guest_service import GuestDenied, GuestSession, OpaqueId, RequestKey


class ActionPolicy(Record):
    version: Nonempty = "simulated-actions-1"
    max_actions: Annotated[int, Field(gt=0)] = 12
    max_receipts: Annotated[int, Field(gt=0)] = 40
    max_state_bytes: Annotated[int, Field(gt=0)] = 131072

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if self.max_receipts < self.max_actions:
            raise ValueError("receipt limit must cover action limit")
        return self


class ConfirmationTarget(Record):
    action_type: ActionType
    result_revision: Revision
    observation_revision: Revision
    result_hash: Digest
    observation_hash: Digest
    context_state_hash: Digest
    environment_hash: Digest
    action_policy_hash: Digest


class ActionConfirmation(Record):
    target: ConfirmationTarget
    explicit_confirmation: bool

    @model_validator(mode="after")
    def confirmed(self) -> Self:
        if self.explicit_confirmation is not True:
            raise ValueError("explicit confirmation must be true")
        return self


class ActionReceipt(Record):
    key: RequestKey
    payload_hash: Digest
    action_id: OpaqueId


class ActionState(Record):
    session_id: OpaqueId
    incident_id: OpaqueId
    policy_hash: Digest
    actions: tuple[ActionRecord, ...] = ()
    receipts: tuple[ActionReceipt, ...] = ()
    events: tuple[IncidentEvent, ...] = ()

    @model_validator(mode="after")
    def coherent(self) -> Self:
        ids = {a.id for a in self.actions}
        if len(ids) != len(self.actions):
            raise ValueError("duplicate action IDs")
        identities = {(a.result_revision, a.action_type) for a in self.actions}
        if len(identities) != len(self.actions):
            raise ValueError("duplicate logical actions")
        prior_ids = set()
        for action in self.actions:
            if action.session_id != self.session_id or action.incident_id != self.incident_id:
                raise ValueError("action owner mismatch")
            if action.prior_action_id is not None and action.prior_action_id not in prior_ids:
                raise ValueError("prior action must precede this action")
            prior_ids.add(action.id)
        if len({r.key for r in self.receipts}) != len(self.receipts) \
                or any(r.action_id not in ids for r in self.receipts):
            raise ValueError("invalid action receipt history")
        actions = {a.id: a for a in self.actions}
        if any(r.payload_hash != actions[r.action_id].payload_hash for r in self.receipts):
            raise ValueError("receipt payload does not match its action")
        receipts = {r.key: r for r in self.receipts}
        if any(a.request_key not in receipts or receipts[a.request_key].action_id != a.id
               for a in self.actions):
            raise ValueError("original request receipt must be retained")
        if len(self.events) != len(self.actions) or tuple(e.sequence for e in self.events) != tuple(
            range(1, len(self.events) + 1)
        ):
            raise ValueError("one ordered creation event per action required")
        for action, event in zip(self.actions, self.events, strict=True):
            if (event.session_id, event.incident_id, event.result_revision,
                event.observation_revision, event.recorded_at, event.event_type) != (
                    self.session_id, self.incident_id, action.result_revision,
                    action.observation_revision, action.confirmed_at, "ACTION_CREATED"
                ):
                raise ValueError("action event does not match its action")
        return self


@dataclass(frozen=True)
class ActionSnapshot:
    guest: GuestSession | None
    evidence: EvidenceState | None
    environment: EvidenceEnvironment | None
    actions: ActionState | None


class ActionStore(Protocol):
    """One atomic snapshot of current guest, evidence, source environment, actions.

    Validate serialized records. Provision ActionState atomically with incident
    creation; absence never means first use. Retry only pure callbacks. Replace
    only action/receipt/event state, preserving evidence and lifetime counters.
    Real Firestore conflict detection must cover ALL snapshot inputs, not merely
    the action document. No fallback store and no swallowed transaction failure.
    """
    def transact(
        self, guest_key: str, incident_id: str,
        change: Callable[[ActionSnapshot], ActionState],
    ) -> ActionState: ...


@dataclass(frozen=True)
class ActionView:
    action: ActionRecord
    event: IncidentEvent
    current: bool
    requires_renewed_review: bool


class ActionService:
    def __init__(self, evidence: EvidenceService, store: ActionStore, policy: ActionPolicy):
        if store is None:
            raise ValueError("explicit action transaction store required")
        self.evidence, self.guest, self.store, self.policy = evidence, evidence.guest, store, policy

    def _limits(self, state):
        if len(state.actions) > self.policy.max_actions \
                or len(state.receipts) > self.policy.max_receipts \
                or len(state.model_dump_json().encode()) > self.policy.max_state_bytes:
            raise GuestDenied(429, "action_history_limit")
        return state

    def _check(self, snapshot, key, incident_id):
        evidence = self.evidence._check(EvidenceSnapshot(snapshot.guest, snapshot.evidence,
                                                        snapshot.environment), key, incident_id)
        if snapshot.environment is None:
            raise GuestDenied(503, "source_state_unavailable")
        state = snapshot.actions
        if state is None or state.session_id != evidence.session_id \
                or state.incident_id != incident_id or state.policy_hash != self.policy.digest():
            raise GuestDenied(503, "action_state_unavailable")
        self._limits(state)
        results = {r.revision: r for r in evidence.results}
        for action, event in zip(state.actions, state.events, strict=True):
            result = results.get(action.result_revision)
            # Validate original meaning independently of current eligibility.
            # A later update makes history stale; it cannot rewrite its verdict,
            # action type, source mode or reason into a different past decision.
            if result is None or not self._eligible(result, action.action_type) \
                    or action.observation_revision != result.observation_revision \
                    or action.sources != result.checked_sources \
                    or action.confirmed_at < result.computed_at \
                    or event.source_mode != result.mode \
                    or event.reason != self._reason(result):
                raise GuestDenied(503, "action_evidence_unavailable")
        return state

    @staticmethod
    def _eligible(result, action_type):
        return (action_type == ActionType.SIMULATED_HOLD
                and result.verdict == Verdict.MATCHED_HOLD_FOR_REVIEW
                and result.hold_eligible) or (
                    action_type == ActionType.SIMULATED_REVIEW_REQUEST
                    and result.verdict == Verdict.REVIEW_REQUIRED
                    and not result.hold_eligible)

    @staticmethod
    def _reason(result):
        return ";".join(result.reasons) or "SUPPORTED_MATCH_CONFIRMED"

    def _transaction(self, capability, incident_id, change):
        result = self.guest._storage(self.store.transact, self.guest._key(capability),
                                     incident_id, change)
        self.guest.resolve(capability)
        return result

    def _current(self, snapshot, result):
        evidence, environment = snapshot.evidence, snapshot.environment
        if not evidence.observations or evidence.active_result != result.revision \
                or result.revision != len(evidence.results) \
                or result.observation_revision != len(evidence.observations) \
                or result.verifier_version != VERIFIER_VERSION:
            return False
        try:
            self.evidence._ready(
                EvidenceSnapshot(snapshot.guest, evidence, environment), evidence.incident_id,
                evidence.observations[-1].observation.captures)
        except GuestDenied:
            return False
        if not is_current(result, observation_revision=len(evidence.observations),
                          context=environment.at(self.guest._now(), len(evidence.results)),
                          policy=environment.verifier_policy):
            return False
        # A source whose support flags were withdrawn must never sustain a hold,
        # even if a defective source adapter failed to advance its epoch/context.
        if result.hold_eligible:
            sources = {n.dependency.family: n for n in environment.notices}
            for dep in result.checked_sources:
                source = sources.get(dep.family)
                if source is None or source.dependency != dep or source.review is None \
                        or not source.interpretation_complete or not source.source_available \
                        or not source.source_proposal_agrees:
                    return False
        return True

    def _target(self, snapshot, action_type):
        evidence = snapshot.evidence
        if not evidence.results or not evidence.observations:
            raise GuestDenied(409, "current_result_required")
        result = evidence.results[-1]
        if not self._current(snapshot, result):
            raise GuestDenied(409, "current_result_required")
        if not self._eligible(result, action_type):
            raise GuestDenied(409, "action_not_eligible")
        return ConfirmationTarget(action_type=action_type, result_revision=result.revision,
            observation_revision=result.observation_revision, result_hash=result.digest(),
            observation_hash=evidence.observations[-1].observation.digest(),
            context_state_hash=result.context_state_hash,
            environment_hash=snapshot.environment.digest(), action_policy_hash=self.policy.digest())

    def prepare(self, capability, incident_id, action_type: ActionType) -> ConfirmationTarget:
        """Offer a target to review. This performs no confirmation or mutation."""
        checked = self.evidence.read_evidence(capability, incident_id).state.digest()
        key, target = self.guest._key(capability), []

        def read(snapshot):
            state = self._check(snapshot, key, incident_id)
            if snapshot.evidence.digest() != checked:
                raise GuestDenied(409, "evidence_changed_during_read")
            target[:] = [self._target(snapshot, action_type)]
            return state

        self._transaction(capability, incident_id, read)
        return target[0]

    def confirm(self, capability, incident_id, request_key,
                confirmation: ActionConfirmation) -> ActionView:
        if not isinstance(confirmation, ActionConfirmation):
            raise GuestDenied(422, "explicit_confirmation_required")
        key, now = self.guest._key(capability), self.guest._now()
        payload = canonical(confirmation.model_dump(mode="json"))
        action_id, event_id = uuid4().hex, uuid4().hex  # Stable across callback retries.
        result_id = []

        def change(snapshot):
            state = self._check(snapshot, key, incident_id)
            receipt = next((r for r in state.receipts if r.key == request_key), None)
            if receipt:
                if receipt.payload_hash != payload:
                    raise GuestDenied(409, "action_request_conflict")
                result_id[:] = [receipt.action_id]
                return state
            target = confirmation.target
            prior = next((a for a in state.actions if a.result_revision == target.result_revision
                          and a.action_type == target.action_type), None)
            if prior:
                if prior.payload_hash != payload:
                    raise GuestDenied(409, "action_request_conflict")
                result_id[:] = [prior.id]
                return self._limits(replace(state, receipts=(*state.receipts,
                    ActionReceipt(key=request_key, payload_hash=payload, action_id=prior.id))))
            if self._target(snapshot, target.action_type) != target:
                raise GuestDenied(409, "confirmation_target_changed")
            result = snapshot.evidence.results[-1]
            action = ActionRecord(id=action_id, session_id=state.session_id,
                incident_id=incident_id, result_revision=result.revision,
                observation_revision=result.observation_revision, sources=result.checked_sources,
                action_type=target.action_type, actor_session=state.session_id, confirmed_at=now,
                request_key=request_key, payload_hash=payload,
                prior_action_id=state.actions[-1].id if state.actions else None)
            event = IncidentEvent(id=event_id, session_id=state.session_id,
                incident_id=incident_id, sequence=len(state.events) + 1,
                event_type="ACTION_CREATED", result_revision=result.revision,
                observation_revision=result.observation_revision, source_mode=result.mode,
                recorded_at=now, reason=self._reason(result))
            result_id[:] = [action.id]
            return self._limits(replace(state, actions=(*state.actions, action),
                receipts=(*state.receipts, ActionReceipt(key=request_key, payload_hash=payload,
                                                        action_id=action.id)),
                events=(*state.events, event)))

        self._transaction(capability, incident_id, change)
        # The commit can succeed before a concurrent source update. Return fresh
        # historical/current metadata, never imply the update reversed that commit.
        return self.get_action(capability, incident_id, result_id[0])

    def list_actions(self, capability, incident_id) -> tuple[ActionView, ...]:
        key, snapshots = self.guest._key(capability), []

        def read(snapshot):
            state = self._check(snapshot, key, incident_id)
            snapshots[:] = [snapshot]
            return state

        state = self._transaction(capability, incident_id, read)
        snapshot = snapshots[0]
        results = {r.revision: r for r in snapshot.evidence.results}
        views = []
        for action, event in zip(state.actions, state.events, strict=True):
            result = results.get(action.result_revision)
            if result is None or action.observation_revision != result.observation_revision \
                    or action.sources != result.checked_sources:
                raise GuestDenied(503, "action_evidence_unavailable")
            current = self._current(snapshot, result)
            views.append(ActionView(action, event, current, not current))
        return tuple(views)

    def get_action(self, capability, incident_id, action_id) -> ActionView:
        result = next((v for v in self.list_actions(capability, incident_id)
                       if v.action.id == action_id), None)
        if result is None:
            raise GuestDenied(404, "action_unavailable")
        return result

    def reconcile(self, capability, incident_id, result_revision,
                  action_type: ActionType) -> ActionView | None:
        """Owned logical lookup after unknown outcome. Storage failure is not absence."""
        return next((v for v in self.list_actions(capability, incident_id)
                     if v.action.result_revision == result_revision
                     and v.action.action_type == action_type), None)

"""Shared model reservation/run boundary, with no concrete store or provider call.

A production adapter must load the guest, session usage, global balances and
selected attempt in ONE database transaction and retry only its pure callback.
Test stores are explicitly fakes. Nothing initializes an actual allocation or
mounts a paid route. An acknowledged dispatch claim is intent, not a receipt.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated, Literal, Protocol, Self
from uuid import uuid4

from pydantic import AwareDatetime, Field, TypeAdapter, model_validator

from batchbeacon.admission_events import emit
from batchbeacon.attempt_evidence import (
    AttemptEvidenceLimits,
    CompleteUsage,
    NonbillablePolicy,
    NonbillableReceipt,
    ResponseEvidence,
    derive_usage,
    response_evidence,
)
from batchbeacon.cloud_policy import ModelPrice, Money, PositiveMoney, ProjectId
from batchbeacon.contracts import Digest, Record
from batchbeacon.extraction_records import RunBinding
from batchbeacon.guest_service import GuestSession, OpaqueId, RequestKey

Count = Annotated[int, Field(ge=0)]
Positive = Annotated[int, Field(gt=0)]


class Pool(StrEnum):
    DEVELOPMENT = "development"
    PUBLIC = "public"
    PROTECTED = "protected_demo"
    PROBE = "probes"


class PoolAllocation(Record):
    pool: Pool
    ceiling_nanos: PositiveMoney


class SharedPolicy(Record):
    project_id: ProjectId
    guest_policy_hash: Digest
    model_configuration_hash: Digest
    price: ModelPrice
    billable_input_bound: Positive
    billable_output_and_thought_bound: Positive
    billing_bound_evidence_hash: Digest
    reserve_nanos: PositiveMoney
    allowed_tools: tuple[RequestKey, ...] = Field(min_length=1)
    max_attempts_per_operation: Annotated[int, Field(ge=1, le=2)] = 2
    max_calls_per_run: Annotated[int, Field(ge=1, le=4)] = 4
    max_tools_per_run: Annotated[int, Field(ge=1, le=6)] = 6
    max_recaptures: Annotated[int, Field(ge=0, le=2)] = 2
    max_verifications: Annotated[int, Field(ge=1, le=6)] = 6
    run_seconds: Positive = 30
    evidence_limits: AttemptEvidenceLimits = AttemptEvidenceLimits()

    @model_validator(mode="after")
    def sufficient_reserve(self) -> Self:
        if len(self.allowed_tools) != len(set(self.allowed_tools)):
            raise ValueError("duplicate allowed tools")
        if self.reserve_nanos < self.price.cost_nanos(
            self.billable_input_bound, self.billable_output_and_thought_bound
        ):
            raise ValueError("reserve does not cover all bounded billed usage")
        return self


class SharedGrant(Record):
    """Operator evidence, never public request fields or a self-authorizing config."""

    project_id: ProjectId
    policy_hash: Digest
    currency: Literal["INR"]
    root_ceiling_nanos: PositiveMoney
    pools: tuple[PoolAllocation, ...] = Field(min_length=4, max_length=4)
    not_before: AwareDatetime
    expires_at: AwareDatetime
    authority_evidence_hash: Digest
    capacity_evidence_hash: Digest

    @model_validator(mode="after")
    def coherent(self) -> Self:
        if {p.pool for p in self.pools} != set(Pool):
            raise ValueError("each model pool must occur exactly once")
        if sum(p.ceiling_nanos for p in self.pools) > self.root_ceiling_nanos:
            raise ValueError("child pools exceed the root model allocation")
        if self.expires_at <= self.not_before:
            raise ValueError("grant expiry must follow its start")
        return self

    def ceiling(self, pool: Pool) -> int:
        return next(p.ceiling_nanos for p in self.pools if p.pool == pool)


class PoolOpening(Record):
    pool: Pool
    incurred_nanos: Money | None
    outstanding_nanos: Money | None
    lifetime_attempts: Count | None
    evidence_hash: Digest | None

    def verified(self) -> None:
        if any(
            v is None
            for v in (
                self.incurred_nanos,
                self.outstanding_nanos,
                self.lifetime_attempts,
                self.evidence_hash,
            )
        ):
            raise ValueError("unknown opening liabilities or attempts close paid admission")


class Balance(Record):
    pool: Pool
    incurred_nanos: Money
    reserved_nanos: Money
    lifetime_attempts: Count
    opening_evidence_hash: Digest

    @property
    def committed(self) -> int:
        return self.incurred_nanos + self.reserved_nanos


class Phase(Record):
    """Operator-selected development/public/protected phase; absolute ceiling.

    A repeated activation cannot replenish the pool. A bounded protected phase
    must be explicitly supplied by the operator, with its review evidence.
    """

    pool: Literal[Pool.DEVELOPMENT, Pool.PUBLIC, Pool.PROTECTED]
    max_pool_liability_nanos: PositiveMoney
    not_before: AwareDatetime
    expires_at: AwareDatetime
    evidence_hash: Digest

    @model_validator(mode="after")
    def ordered(self) -> Self:
        if self.expires_at <= self.not_before:
            raise ValueError("phase expiry must follow its start")
        return self


class Budget(Record):
    grant_hash: Digest
    policy_hash: Digest
    balances: tuple[Balance, ...] = Field(min_length=4, max_length=4)
    phase: Phase | None = None
    circuit: Literal["open_bound", "open_representation"] | None = None

    @model_validator(mode="after")
    def unique_pools(self) -> Self:
        if {b.pool for b in self.balances} != set(Pool):
            raise ValueError("budget requires exactly one balance per pool")
        return self

    def balance(self, pool: Pool) -> Balance:
        return next(b for b in self.balances if b.pool == pool)


class VerificationReservation(Record):
    request_key: RequestKey
    context_state_hash: Digest


class IncidentUsage(Record):
    incident_id: OpaqueId
    acquisitions: Count = 0
    verifications: tuple[VerificationReservation, ...] = ()


RunFailureReason = Literal['ALLOWANCE_UNAVAILABLE', 'PROVIDER_UNAVAILABLE', 'CHECK_FAILED']


class Run(Record):
    binding: RunBinding
    attempt_ids: tuple[OpaqueId, ...] = ()
    completion_hash: Digest | None = None
    id: OpaqueId
    incident_id: OpaqueId
    request_key: RequestKey
    phase_hash: Digest
    started_at: AwareDatetime
    deadline: AwareDatetime
    calls: Count = 0
    call_operation_keys: tuple[RequestKey, ...] = ()
    tool_ids: tuple[RequestKey, ...] = ()
    terminal: Literal["completed", "failed", "timed_out"] | None = None
    failure_reason: RunFailureReason | None = Field(
        default=None, exclude_if=lambda value: value is None)

    @model_validator(mode='after')
    def coherent_failure(self) -> Self:
        if self.failure_reason is not None and (
                self.terminal not in {'failed', 'timed_out'} or self.completion_hash):
            raise ValueError('failure reason requires an unsuccessful terminal run')
        return self


class SessionUsage(Record):
    session_id: OpaqueId
    incidents: tuple[IncidentUsage, ...] = ()
    runs: tuple[Run, ...] = ()


class Attempt(Record):
    id: OpaqueId
    session_id: OpaqueId
    incident_id: OpaqueId
    run_id: OpaqueId
    pool: Pool
    grant_hash: Digest
    policy_hash: Digest
    phase_hash: Digest
    request_hash: Digest
    operation_key: RequestKey
    model_configuration_hash: Digest
    reserved_at: AwareDatetime
    reserved_nanos: PositiveMoney
    price: ModelPrice
    billable_input_bound: Positive
    billable_output_and_thought_bound: Positive
    run_binding_hash: Digest
    evidence_limits: AttemptEvidenceLimits
    response: ResponseEvidence | None = Field(default=None, repr=False)
    complete_usage: CompleteUsage | None = Field(default=None, repr=False)
    dispatch_claimed: bool = False
    usage_hash: Digest | None = None
    actual_nanos: Money | None = None
    nonbillable_receipt: NonbillableReceipt | None = Field(
        default=None, exclude_if=lambda value: value is None)

    @model_validator(mode="after")
    def coherent_evidence(self) -> Self:
        if self.response is not None and (not self.dispatch_claimed
                or self.response.retained_bytes > self.evidence_limits.max_response_bytes):
            raise ValueError("attempt response inconsistent")
        if self.complete_usage is not None:
            if self.response is None or self.complete_usage != derive_usage(
                    self.response, self.request_hash, self.evidence_limits):
                raise ValueError("attempt usage inconsistent")
        if self.nonbillable_receipt is not None:
            if self.response is None or self.complete_usage is not None \
                    or self.usage_hash is not None or self.actual_nanos != 0:
                raise ValueError("conflicting settlement evidence")
            self.nonbillable_receipt.validate_response(self.response, attempt_id=self.id,
                request_hash=self.request_hash, model_hash=self.model_configuration_hash,
                reserved_at=self.reserved_at)
        elif (self.usage_hash is None) != (self.actual_nanos is None):
            raise ValueError("partial reconciliation receipt")
        if self.usage_hash is not None and (self.complete_usage is None
                or self.usage_hash != self.complete_usage.digest()
                or self.actual_nanos != self.price.cost_nanos(self.complete_usage.input_tokens,
                    self.complete_usage.output_and_thought_tokens)):
            raise ValueError("reconciliation receipt inconsistent")
        if len(self.model_dump_json().encode()) > self.evidence_limits.max_attempt_record_bytes:
            raise ValueError("attempt record exceeds policy")
        return self


LiabilityOperation = Literal["record_response", "reconcile"]


class PredecessorLiabilities(Record):
    """Reviewed, exact original reservations; settlement only, never paid authority.

    Stored in operator runtime configuration, not a public request or the ledger.
    A migration must preserve outstanding balances and fence stale database writers.
    Missing original provider evidence remains unknown after a migration.
    """

    project_id: ProjectId
    database_id: Annotated[str, Field(pattern=r"^(\(default\)|[a-z][a-z0-9-]{0,62})$")]
    namespace: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
    environment_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,63}$")]
    successor_grant_hash: Digest
    successor_policy_hash: Digest
    original_grant: SharedGrant
    original_policy: SharedPolicy
    reservations: tuple[Attempt, ...] = Field(min_length=1)
    nonbillable_policy: NonbillablePolicy | None = None

    @model_validator(mode="after")
    def coherent(self) -> Self:
        p, g = self.original_policy, self.original_grant
        if (p.project_id != self.project_id or g.project_id != self.project_id
                or g.policy_hash != p.digest()
                or self.successor_grant_hash == g.digest()
                or len({a.id for a in self.reservations}) != len(self.reservations)):
            raise ValueError("predecessor liability lineage invalid")
        if (self.nonbillable_policy is not None
                and self.nonbillable_policy.model_configuration_hash != p.model_configuration_hash):
            raise ValueError("predecessor nonbillable binding invalid")
        for a in self.reservations:
            if (not a.dispatch_claimed or a.response is not None or a.actual_nanos is not None
                    or a.grant_hash != g.digest() or a.policy_hash != p.digest()
                    or a.model_configuration_hash != p.model_configuration_hash
                    or a.price != p.price or a.reserved_nanos != p.reserve_nanos
                    or a.billable_input_bound != p.billable_input_bound
                    or a.billable_output_and_thought_bound != p.billable_output_and_thought_bound
                    or a.evidence_limits != p.evidence_limits
                    or not g.not_before <= a.reserved_at < g.expires_at
                    or not p.price.observed_at <= a.reserved_at < p.price.valid_until):
                raise ValueError("predecessor reservation binding invalid")
        return self

    def validate_successor(self, policy: SharedPolicy, grant: SharedGrant):
        if (policy.project_id != self.project_id or grant.project_id != self.project_id
                or grant.policy_hash != policy.digest()
                or policy.digest() != self.successor_policy_hash
                or grant.digest() != self.successor_grant_hash):
            raise ValueError("predecessor successor binding invalid")

    def validate_storage(self, policy):
        if any(getattr(self, key) != getattr(policy, key) for key in (
                "project_id", "database_id", "namespace", "environment_id")):
            raise ValueError("predecessor storage scope invalid")

    def permits(self, budget: Budget, attempt: Attempt, operation: LiabilityOperation | None):
        if (operation not in {"record_response", "reconcile"}
                or budget.grant_hash != self.successor_grant_hash
                or budget.policy_hash != self.successor_policy_hash):
            return False
        # Only these fields can change as original evidence is retained/settled.
        mutable = {"response", "complete_usage", "usage_hash", "actual_nanos",
                   "nonbillable_receipt"}
        return any(a.id == attempt.id and a.model_dump(exclude=mutable)
                   == attempt.model_dump(exclude=mutable) for a in self.reservations)


def settlement_lineage_matches(budget, attempt, operation, predecessor=None):
    if budget is None or attempt is None:
        return False
    if (attempt.grant_hash == budget.grant_hash
            and attempt.policy_hash == budget.policy_hash):
        return True
    return predecessor is not None and predecessor.permits(budget, attempt, operation)


@dataclass(frozen=True)
class Address:
    # All IDs are runtime/server-owned, never a client-supplied authority claim.
    guest_key: str | None = None
    attempt_id: str | None = None
    inspect_session_attempts: bool = False
    liability_operation: LiabilityOperation | None = None


@dataclass(frozen=True)
class Snapshot:
    budget: Budget | None
    guest: GuestSession | None = None
    usage: SessionUsage | None = None
    attempt: Attempt | None = None
    session_attempts: tuple[Attempt, ...] | None = None


@dataclass(frozen=True)
class Change:
    budget: Budget | None
    usage: SessionUsage | None = None
    attempt: Attempt | None = None
    # A denial that MUST commit (e.g. circuit opening) is data until after commit.
    denial: str | None = None
    not_after: datetime | None = None
    reconciliation_required: bool = False


@dataclass(frozen=True)
class RunAdmission:
    run: Run
    fresh: bool


class SharedStore(Protocol):
    """One atomic read/compare/commit, including current guest ownership.

    Return exactly the committed Change. Missing/corrupt/outage state must fail,
    never silently initialize. Do not swallow a callback denial as a successful
    no-op. A callback may repeat. No model/HTTP/object writes are allowed inside.
    create_budget is operator-only, exclusive creation, never upsert/reset.
    The adapter must create SessionUsage atomically with guest issuance before
    shared admission is exposed. Guest-addressed transactions require that record;
    absence is corruption, never a first-use signal or permission to reset quotas.
    Likewise provision IncidentUsage atomically with each owned incident; absent
    incident counters cannot be recovered by resetting lifetime allowances.
    """

    def create_budget(self, budget: Budget) -> None: ...
    def transact(self, address: Address, change: Callable[[Snapshot], Change]) -> Change: ...


class SharedDenied(ValueError):
    pass


class _AllowanceExhausted(SharedDenied):
    """An authenticated reservation exceeded the actual committed allowance."""


class SharedAdmission:
    def __init__(
        self,
        policy: SharedPolicy,
        grant: SharedGrant,
        store: SharedStore,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        nonbillable_policy: NonbillablePolicy | None = None,
        predecessor_liabilities: PredecessorLiabilities | None = None,
    ):
        if store is None:
            raise ValueError("an explicit shared transaction store is required")
        self.policy, self.grant, self.store, self.clock = policy, grant, store, clock
        if nonbillable_policy is not None and \
                nonbillable_policy.model_configuration_hash != policy.model_configuration_hash:
            raise ValueError("nonbillable model binding invalid")
        self.nonbillable_policy = nonbillable_policy
        if predecessor_liabilities is not None:
            predecessor_liabilities.validate_successor(policy, grant)
        self.predecessor_liabilities = predecessor_liabilities

    def _now(self):
        now = self.clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise SharedDenied("aware server clock required")
        return now

    def _authority(self):
        now = self._now()
        if (
            self.policy.digest() != self.grant.policy_hash
            or self.policy.project_id != self.grant.project_id
            or not self.grant.not_before <= now < self.grant.expires_at
            or not self.policy.price.observed_at <= now < self.policy.price.valid_until
        ):
            raise SharedDenied("paid authority or rate evidence unavailable")

    def _budget(self, snapshot, *, require_phase=True):
        self._authority()
        budget = snapshot.budget
        if (
            budget is None
            or budget.grant_hash != self.grant.digest()
            or budget.policy_hash != self.policy.digest()
            or budget.circuit
        ):
            raise SharedDenied("paid ledger unavailable or circuit open")
        if require_phase:
            phase = budget.phase
            if phase is None or not phase.not_before <= self._now() < phase.expires_at:
                raise SharedDenied("no current operator phase")
        return budget

    def _guest(self, snapshot, address):
        guest = snapshot.guest
        if (
            guest is None
            or guest.capability_hash != address.guest_key
            or guest.policy_hash != self.policy.guest_policy_hash
            or not guest.scope.issued_at <= self._now() < guest.scope.expires_at
        ):
            raise SharedDenied("guest expired or invalid")
        if snapshot.usage is None:
            raise SharedDenied("usage unavailable")
        if snapshot.usage.session_id != guest.scope.session_id:
            raise SharedDenied("usage owner mismatch")
        return guest

    @staticmethod
    def _incident(guest, incident_id):
        if not any(i.id == incident_id for i in guest.incidents):
            raise SharedDenied("incident unavailable")

    def _run(self, snapshot, address, run_id):
        guest = self._guest(snapshot, address)
        run = (
            next((r for r in snapshot.usage.runs if r.id == run_id), None)
            if snapshot.usage
            else None
        )
        if run is None:
            raise SharedDenied("run unavailable")
        self._incident(guest, run.incident_id)
        if run.terminal or not run.started_at <= self._now() < run.deadline:
            raise SharedDenied("run ended")
        budget = self._budget(snapshot)
        if run.phase_hash != budget.phase.digest():
            raise SharedDenied("operator phase changed")
        return guest, run, budget

    def initialize(self, openings: tuple[PoolOpening, ...]):
        self._authority()
        if len(openings) != 4 or {o.pool for o in openings} != set(Pool):
            raise SharedDenied("all pool opening liabilities are required")
        balances = []
        for opening in openings:
            opening.verified()
            balance = Balance(
                pool=opening.pool,
                incurred_nanos=opening.incurred_nanos,
                reserved_nanos=opening.outstanding_nanos,
                lifetime_attempts=opening.lifetime_attempts,
                opening_evidence_hash=opening.evidence_hash,
            )
            if balance.committed > self.grant.ceiling(balance.pool):
                raise SharedDenied("opening liabilities exceed pool authority")
            balances.append(balance)
        budget = Budget(
            grant_hash=self.grant.digest(),
            policy_hash=self.policy.digest(),
            balances=tuple(balances),
        )
        self.store.create_budget(budget)

    def activate_phase(self, phase: Phase):
        """Operator-only command; no HTTP route or client phase selector."""

        def change(snapshot):
            budget = self._budget(snapshot, require_phase=False)
            if (
                phase.max_pool_liability_nanos > self.grant.ceiling(phase.pool)
                or phase.not_before < self.grant.not_before
                or phase.expires_at > self.grant.expires_at
                or not phase.not_before <= self._now() < phase.expires_at
            ):
                raise SharedDenied("phase is outside reviewed pool authority")
            return Change(budget=budget.model_copy(update={"phase": phase}))

        self.store.transact(Address(), change)

    def begin_run(self, guest_key: str, incident_id: str, request_key: str,
                  binding: RunBinding) -> Run:
        """Return identity/history; only reserve + a new claim permits dispatch."""
        return self.admit_run(guest_key, incident_id, request_key, binding).run

    def admit_run(self, guest_key: str, incident_id: str, request_key: str,
                  binding: RunBinding, *, not_after: datetime | None = None) -> RunAdmission:
        """Fresh is true only for this newly acknowledged acquisition admission."""
        if not_after is not None and (not_after.tzinfo is None or not_after.utcoffset() is None):
            raise SharedDenied("aware execution deadline required")
        binding = RunBinding.model_validate_json(binding.model_dump_json())
        address = Address(guest_key, inspect_session_attempts=True)
        run_id, started = uuid4().hex, self._now()

        def change(snapshot):
            guest = self._guest(snapshot, address)
            self._incident(guest, incident_id)
            usage = snapshot.usage
            prior = next((r for r in usage.runs if r.request_key == request_key), None)
            if prior:
                if prior.incident_id != incident_id or prior.binding != binding:
                    raise SharedDenied("run request conflict")
                return Change(snapshot.budget, usage, not_after=guest.scope.expires_at)
            if any(r.terminal is None and self._now() < r.deadline for r in usage.runs):
                raise SharedDenied("session already has an active run")
            # Read attempt settlement in the same transaction as new-run admission.
            # Failure/deadline labels do not prove that provider liability ended.
            if self._unsettled(snapshot, guest):
                raise SharedDenied("unresolved check requires operator review")
            budget = self._budget(snapshot)
            if binding.application_configuration_hash != self.policy.model_configuration_hash \
                    or len(binding.model_dump_json().encode()) > \
                    self.policy.evidence_limits.max_run_binding_bytes:
                raise SharedDenied("run binding unavailable")
            incident = next(i for i in guest.incidents if i.id == incident_id)
            ready = {c.id: c for batch in incident.batches if batch.ready for c in batch.captures}
            captures = binding.manifest.captures
            if len({c.id for c in captures}) != len(captures) \
                    or any(ready.get(c.id) != c for c in captures):
                raise SharedDenied("run capture unavailable")
            counter = next(
                (i for i in usage.incidents if i.incident_id == incident_id),
                None,
            )
            if counter is None:
                raise SharedDenied("incident usage unavailable")
            if counter.acquisitions >= 1 + self.policy.max_recaptures:
                raise SharedDenied("lifetime acquisition allowance exhausted")
            deadline = min(
                started + timedelta(seconds=self.policy.run_seconds),
                guest.scope.expires_at,
                budget.phase.expires_at,
                self.grant.expires_at,
                not_after or guest.scope.expires_at,
            )
            if self._now() >= deadline:
                raise SharedDenied("run expired before admission")
            run = Run(
                binding=binding,
                id=run_id,
                incident_id=incident_id,
                request_key=request_key,
                phase_hash=budget.phase.digest(),
                started_at=started,
                deadline=deadline,
            )
            counter = counter.model_copy(update={"acquisitions": counter.acquisitions + 1})
            expired = tuple(
                r.model_copy(update={"terminal": "timed_out"})
                if r.terminal is None and self._now() >= r.deadline
                else r
                for r in usage.runs
            )
            usage = usage.model_copy(
                update={
                    "runs": (*expired, run),
                    "incidents": tuple(i for i in usage.incidents if i.incident_id != incident_id)
                    + (counter,),
                }
            )
            return Change(budget, usage, not_after=guest.scope.expires_at)

        result = self.store.transact(address, change)
        run = next(r for r in result.usage.runs if r.request_key == request_key)
        if self._now() >= result.not_after or (run.id == run_id and self._now() >= run.deadline):
            raise SharedDenied("run ended before admission response")
        return RunAdmission(run, run.id == run_id)

    def reserve(
        self, guest_key: str, run_id: str, attempt_id: str, request_hash: str, *, operation_key: str
    ) -> Attempt:
        address, reserved_at = Address(guest_key, attempt_id), self._now()

        def change(snapshot):
            guest, run, budget = self._run(snapshot, address, run_id)
            if snapshot.attempt:
                old = snapshot.attempt
                if (
                    old.session_id != guest.scope.session_id
                    or old.run_id != run_id
                    or old.request_hash != request_hash
                    or old.operation_key != operation_key
                    or old.run_binding_hash != run.binding.digest()
                    or old.id not in run.attempt_ids
                ):
                    raise SharedDenied("attempt request conflict")
                return Change(
                    budget,
                    snapshot.usage,
                    old,
                    not_after=min(run.deadline, guest.scope.expires_at),
                )
            if attempt_id in run.attempt_ids:
                raise SharedDenied("established attempt unavailable")
            if run.calls >= self.policy.max_calls_per_run:
                raise SharedDenied("run model-call allowance exhausted")
            if (
                run.call_operation_keys.count(operation_key)
                >= self.policy.max_attempts_per_operation
            ):
                raise SharedDenied("logical operation retry allowance exhausted")
            pool = budget.phase.pool
            balance = budget.balance(pool)
            amount = self.policy.reserve_nanos
            if (
                balance.committed + amount
                > min(self.grant.ceiling(pool), budget.phase.max_pool_liability_nanos)
                or sum(b.committed for b in budget.balances) + amount
                > self.grant.root_ceiling_nanos
            ):
                raise _AllowanceExhausted("insufficient uncommitted model allowance")
            attempt = Attempt(
                id=attempt_id,
                session_id=guest.scope.session_id,
                incident_id=run.incident_id,
                run_id=run.id,
                pool=pool,
                grant_hash=self.grant.digest(),
                policy_hash=self.policy.digest(),
                phase_hash=run.phase_hash,
                request_hash=request_hash,
                operation_key=operation_key,
                model_configuration_hash=self.policy.model_configuration_hash,
                run_binding_hash=run.binding.digest(),
                evidence_limits=self.policy.evidence_limits,
                reserved_at=reserved_at,
                reserved_nanos=amount,
                price=self.policy.price,
                billable_input_bound=self.policy.billable_input_bound,
                billable_output_and_thought_bound=self.policy.billable_output_and_thought_bound,
            )
            balance = balance.model_copy(
                update={
                    "reserved_nanos": balance.reserved_nanos + amount,
                    "lifetime_attempts": balance.lifetime_attempts + 1,
                }
            )
            budget = budget.model_copy(
                update={
                    "balances": tuple(balance if b.pool == pool else b for b in budget.balances)
                }
            )
            usage = snapshot.usage.model_copy(
                update={
                    "runs": tuple(
                        r.model_copy(
                            update={
                                "calls": r.calls + 1,
                                "call_operation_keys": (*r.call_operation_keys, operation_key),
                                "attempt_ids": (*r.attempt_ids, attempt_id),
                            }
                        )
                        if r.id == run_id
                        else r
                        for r in snapshot.usage.runs
                    )
                }
            )
            return Change(
                budget, usage, attempt, not_after=min(run.deadline, guest.scope.expires_at)
            )

        try:
            result = self.store.transact(address, change)
        except _AllowanceExhausted:
            emit('allowance_exhausted', self.policy.digest(), self.grant.digest())
            raise
        self._authority()
        if self._now() >= result.not_after:
            raise SharedDenied("reservation expired after commit; reservation retained")
        # A returned reservation is never sufficient to invoke a provider.
        return result.attempt

    def claim_dispatch(
        self,
        guest_key: str,
        run_id: str,
        attempt_id: str,
        request_hash: str,
        model_configuration_hash: str,
    ) -> Attempt:
        address = Address(guest_key, attempt_id)

        def change(snapshot):
            guest, run, budget = self._run(snapshot, address, run_id)
            deadline = min(run.deadline, guest.scope.expires_at)
            attempt = snapshot.attempt
            if (
                attempt is None
                or attempt.session_id != guest.scope.session_id
                or attempt.run_id != run_id
                or attempt.run_binding_hash != run.binding.digest()
                or attempt.id not in run.attempt_ids
                or attempt.request_hash != request_hash
                or attempt.model_configuration_hash != model_configuration_hash
                or attempt.policy_hash != budget.policy_hash
                or attempt.grant_hash != budget.grant_hash
                or attempt.phase_hash != budget.phase.digest()
                or attempt.dispatch_claimed
                or attempt.actual_nanos is not None
            ):
                raise SharedDenied("dispatch claim unavailable")
            return Change(
                budget,
                snapshot.usage,
                attempt.model_copy(update={"dispatch_claimed": True}),
                not_after=deadline,
            )

        result = self.store.transact(address, change)
        self._authority()
        if self._now() >= result.not_after:
            raise SharedDenied("dispatch expired after commit; reservation retained")
        return result.attempt  # Intent only; caller must invoke once or reconcile unknown.

    def claim_tool(self, guest_key: str, run_id: str, tool_operation_id: str, *, tool_name: str):
        """Count a single tool invocation before dispatch; same-ID replay is denied."""
        TypeAdapter(RequestKey).validate_python(tool_operation_id)
        if tool_name not in self.policy.allowed_tools:
            raise SharedDenied("tool is not allowlisted")
        address = Address(guest_key)

        def change(snapshot):
            guest, run, budget = self._run(snapshot, address, run_id)
            if tool_operation_id in run.tool_ids:
                raise SharedDenied("tool invocation already claimed")
            if len(run.tool_ids) >= self.policy.max_tools_per_run:
                raise SharedDenied("tool allowance exhausted")
            usage = snapshot.usage.model_copy(
                update={
                    "runs": tuple(
                        r.model_copy(update={"tool_ids": (*r.tool_ids, tool_operation_id)})
                        if r.id == run_id
                        else r
                        for r in snapshot.usage.runs
                    )
                }
            )
            return Change(budget, usage, not_after=min(run.deadline, guest.scope.expires_at))

        result = self.store.transact(address, change)
        if self._now() >= result.not_after:
            raise SharedDenied("tool invocation expired after commit")

    def reserve_verification(
        self, guest_key: str, incident_id: str, request_key: str, context_state_hash: str
    ):
        """Pure-verification allowance, independent of paid authority/phase/circuit.

        The caller MUST still check currentness on every read and invalidate old
        eligibility even if this allowance is exhausted. Result persistence and
        that caller integration are a separate T09/T16 obligation, not provided here.
        """
        address = Address(guest_key)
        reservation = VerificationReservation(
            request_key=request_key, context_state_hash=context_state_hash
        )

        def change(snapshot):
            guest = self._guest(snapshot, address)
            self._incident(guest, incident_id)
            usage = snapshot.usage
            counter = next(
                (i for i in usage.incidents if i.incident_id == incident_id),
                None,
            )
            if counter is None:
                raise SharedDenied("incident usage unavailable")
            prior = next((v for v in counter.verifications if v.request_key == request_key), None)
            if prior:
                if prior != reservation:
                    raise SharedDenied("verification request conflict")
                return Change(snapshot.budget, usage, not_after=guest.scope.expires_at)
            if len(counter.verifications) >= self.policy.max_verifications:
                raise SharedDenied("lifetime verification allowance exhausted")
            counter = counter.model_copy(
                update={"verifications": (*counter.verifications, reservation)}
            )
            usage = usage.model_copy(
                update={
                    "incidents": tuple(i for i in usage.incidents if i.incident_id != incident_id)
                    + (counter,)
                }
            )
            return Change(snapshot.budget, usage, not_after=guest.scope.expires_at)

        result = self.store.transact(address, change)
        if self._now() >= result.not_after:
            raise SharedDenied("verification expired after commit")
        return reservation

    def finish_run(self, guest_key: str, run_id: str, *, failed: bool = False,
                   failure_reason: RunFailureReason | None = None):
        if failure_reason is not None and (not failed or failure_reason not in {
                'ALLOWANCE_UNAVAILABLE', 'PROVIDER_UNAVAILABLE', 'CHECK_FAILED'}):
            raise SharedDenied('invalid failure reason')
        address = Address(guest_key)

        def change(snapshot):
            # Finishing can release concurrency after paid authority expires, never money.
            guest = self._guest(snapshot, address)
            if snapshot.budget is None or snapshot.usage is None:
                raise SharedDenied("run unavailable")
            run = next((r for r in snapshot.usage.runs if r.id == run_id), None)
            if run is None:
                raise SharedDenied("run unavailable")
            self._incident(guest, run.incident_id)
            if run.terminal:
                return Change(snapshot.budget, snapshot.usage)
            reason = (
                "timed_out" if self._now() >= run.deadline else "failed" if failed else "completed"
            )
            usage = snapshot.usage.model_copy(
                update={
                    "runs": tuple(
                        Run.model_validate(r.model_dump() | {
                            'terminal': reason, 'failure_reason': failure_reason})
                        if r.id == run_id else r
                        for r in snapshot.usage.runs
                    )
                }
            )
            return Change(snapshot.budget, usage)

        self.store.transact(address, change)

    def inspect_run(self, guest_key: str, run_id: str) -> Run:
        """Owned history stays readable without paid authority; it grants no dispatch."""
        address = Address(guest_key)
        def change(snapshot):
            guest = self._guest(snapshot, address)
            run = next((r for r in snapshot.usage.runs if r.id == run_id), None)
            if run is None:
                raise SharedDenied("run unavailable")
            self._incident(guest, run.incident_id)
            return Change(snapshot.budget, snapshot.usage, not_after=guest.scope.expires_at)
        result = self.store.transact(address, change)
        if self._now() >= result.not_after:
            raise SharedDenied("guest expired or invalid")
        return next(r for r in result.usage.runs if r.id == run_id)

    @staticmethod
    def _unsettled(snapshot, guest):
        attempts = snapshot.session_attempts
        expected = {aid: run for run in snapshot.usage.runs for aid in run.attempt_ids}
        if len(expected) != sum(len(r.attempt_ids) for r in snapshot.usage.runs) or \
                attempts is None or len(attempts) != len(expected) or \
                {a.id for a in attempts} != set(expected):
            raise SharedDenied("attempt history unavailable")
        for attempt in attempts:
            run = expected[attempt.id]
            if attempt.session_id != guest.scope.session_id or attempt.run_id != run.id or \
                    attempt.incident_id != run.incident_id or \
                    attempt.run_binding_hash != run.binding.digest() or \
                    attempt.model_configuration_hash != \
                    run.binding.application_configuration_hash or \
                    attempt.phase_hash != run.phase_hash or \
                    attempt.operation_key not in run.call_operation_keys:
                raise SharedDenied("attempt history binding invalid")
        # Historical settled attempts remain readable after an admitted policy
        # migration. This read never grants authority to settle an older grant.
        return any(a.actual_nanos is None for a in attempts)

    def operation_availability(self, guest_key: str, incident_id: str) -> dict:
        """Read-only admission snapshot, never a reservation or authority to dispatch."""
        address = Address(guest_key, inspect_session_attempts=True)
        observed = {}

        def read(snapshot):
            guest = self._guest(snapshot, address)
            self._incident(guest, incident_id)
            counter = next((i for i in snapshot.usage.incidents
                            if i.incident_id == incident_id), None)
            if counter is None:
                raise SharedDenied("incident usage unavailable")
            reason = 'AVAILABLE'
            if self._unsettled(snapshot, guest):
                reason = 'UNRESOLVED_ATTEMPT'
            elif any(r.terminal is None and self._now() < r.deadline
                     for r in snapshot.usage.runs):
                reason = 'ACTIVE_REQUEST'
            elif counter.acquisitions >= 1 + self.policy.max_recaptures:
                reason = 'ACQUISITION_LIMIT'
            else:
                try:
                    budget = self._budget(snapshot)
                    balance = budget.balance(budget.phase.pool)
                    amount = self.policy.reserve_nanos
                    if (balance.committed + amount > min(
                            self.grant.ceiling(budget.phase.pool),
                            budget.phase.max_pool_liability_nanos)
                            or sum(b.committed for b in budget.balances) + amount
                            > self.grant.root_ceiling_nanos):
                        reason = 'ALLOWANCE_UNAVAILABLE'
                except SharedDenied:
                    reason = 'ALLOWANCE_UNAVAILABLE'
            observed.update(extraction_reason=reason,
                            verification_available=len(counter.verifications)
                            < self.policy.max_verifications)
            return Change(None, not_after=guest.scope.expires_at)

        result = self.store.transact(address, read)
        if self._now() >= result.not_after:
            raise SharedDenied("guest expired or invalid")
        return observed

    def reconciliation_required(self, guest_key: str) -> bool:
        """Owned settlement status; no provider call, paid admission or record write."""
        address = Address(guest_key, inspect_session_attempts=True)
        def read(snapshot):
            guest = self._guest(snapshot, address)
            return Change(None, not_after=guest.scope.expires_at,
                reconciliation_required=self._unsettled(snapshot, guest))
        result = self.store.transact(address, read)
        if self._now() >= result.not_after:
            raise SharedDenied("guest expired or invalid")
        return result.reconciliation_required

    def find_run(self, guest_key: str, incident_id: str, request_key: str) -> Run | None:
        """Owned key recovery without rebuilding changed inputs or acquiring permission."""
        address = Address(guest_key)
        def read(snapshot):
            guest = self._guest(snapshot, address)
            self._incident(guest, incident_id)
            prior = next((r for r in snapshot.usage.runs if r.request_key == request_key), None)
            if prior is not None and prior.incident_id != incident_id:
                raise SharedDenied("run request conflict")
            return Change(snapshot.budget, snapshot.usage, not_after=guest.scope.expires_at)
        result = self.store.transact(address, read)
        if self._now() >= result.not_after:
            raise SharedDenied("guest expired or invalid")
        return next((r for r in result.usage.runs if r.request_key == request_key), None)

    def inspect_attempt(self, guest_key: str, run_id: str, attempt_id: str) -> Attempt:
        """Internal owned recovery; raw evidence is never a public response model."""
        address = Address(guest_key, attempt_id)
        def change(snapshot):
            guest = self._guest(snapshot, address)
            run = next((r for r in snapshot.usage.runs if r.id == run_id), None)
            attempt = snapshot.attempt
            if run is None or attempt is None or attempt.id not in run.attempt_ids \
                    or attempt.session_id != guest.scope.session_id or attempt.run_id != run_id \
                    or attempt.incident_id != run.incident_id \
                    or attempt.run_binding_hash != run.binding.digest():
                raise SharedDenied("attempt unavailable")
            self._incident(guest, run.incident_id)
            return Change(snapshot.budget, snapshot.usage, attempt,
                          not_after=guest.scope.expires_at)
        result = self.store.transact(address, change)
        if self._now() >= result.not_after:
            raise SharedDenied("guest expired or invalid")
        return result.attempt

    @staticmethod
    def _attempt_record(attempt):
        try:
            return Attempt.model_validate_json(attempt.model_dump_json())
        except ValueError:
            pass
        raise SharedDenied("attempt evidence invalid or byte limit")

    def record_response(self, attempt_id: str, request_hash: str, raw: bytes, *,
                        status_code: int, complete: bool, observed_bytes: int) -> Attempt:
        """Trusted internal transport only. Original evidence precedes any parsing.

        May complete late; neither guest access nor paid execution is reopened.
        A stored prefix remains incomplete and cannot later be overwritten.
        """
        def change(snapshot):
            budget, attempt = snapshot.budget, snapshot.attempt
            if not settlement_lineage_matches(budget, attempt, "record_response",
                    self.predecessor_liabilities) or attempt.id != attempt_id \
                    or not attempt.dispatch_claimed or attempt.request_hash != request_hash:
                raise SharedDenied("response attempt unavailable")
            response = response_evidence(raw, status_code=status_code, complete=complete,
                observed_bytes=observed_bytes, limits=attempt.evidence_limits)
            if attempt.response is not None:
                if attempt.response != response:
                    raise SharedDenied("response evidence conflict")
                return Change(budget, attempt=attempt)
            attempt = self._attempt_record(attempt.model_copy(update={"response": response}))
            return Change(budget, attempt=attempt)
        return self.store.transact(Address(attempt_id=attempt_id,
            liability_operation="record_response"), change).attempt

    def reconcile(self, attempt_id: str):
        """Derive complete usage from committed original bytes; never caller totals.

        Uses original attempt limits/rate after expiry. No execution is reopened.
        Missing, malformed or incomplete evidence leaves the reservation untouched.
        """
        def change(snapshot):
            budget, attempt = snapshot.budget, snapshot.attempt
            if not settlement_lineage_matches(budget, attempt, "reconcile",
                    self.predecessor_liabilities) or attempt.id != attempt_id:
                raise SharedDenied("reservation unavailable for reconciliation")
            if not attempt.dispatch_claimed:
                raise SharedDenied("no dispatch intent exists for a usage receipt")
            if attempt.response is None:
                raise SharedDenied("complete usage unavailable")
            if attempt.nonbillable_receipt is not None:
                return Change(budget, attempt=attempt)
            if not 200 <= attempt.response.status_code < 300:
                rule = self.nonbillable_policy
                if attempt.grant_hash != budget.grant_hash:
                    rule = self.predecessor_liabilities.nonbillable_policy
                return self._reconcile_nonbillable(budget, attempt, rule)
            usage = derive_usage(attempt.response, attempt.request_hash, attempt.evidence_limits)
            input_tokens, output_and_thought_tokens = (usage.input_tokens,
                                                       usage.output_and_thought_tokens)
            usage_hash = usage.digest()
            cost = attempt.price.cost_nanos(input_tokens, output_and_thought_tokens)
            if attempt.usage_hash is not None:
                if attempt.usage_hash != usage_hash or attempt.actual_nanos != cost \
                        or attempt.complete_usage != usage:
                    raise SharedDenied("conflicting usage receipt")
                return Change(budget, attempt=attempt)
            balance = budget.balance(attempt.pool)
            violation = (input_tokens > attempt.billable_input_bound
                         or output_and_thought_tokens > attempt.billable_output_and_thought_bound
                         or cost > attempt.reserved_nanos)
            representation = cost > 2**63 - 1 or balance.incurred_nanos + cost > 2**63 - 1
            circuit = ("open_representation" if representation
                       else "open_bound" if violation else None)
            if circuit and budget.circuit not in {circuit, "open_representation"}:
                # Commit the stop using the already-durable original response first.
                # A later expanded-record or adapter byte limit cannot roll it back.
                return Change(budget.model_copy(update={"circuit": circuit}), attempt=attempt,
                              denial="usage_circuit_committed")
            attempt = self._attempt_record(attempt.model_copy(update={"complete_usage": usage}))
            if cost > 2**63 - 1:
                return Change(
                    budget.model_copy(update={"circuit": "open_representation"}),
                    attempt=attempt,
                    denial="usage exceeds ledger representation",
                )
            balance = budget.balance(attempt.pool)
            if balance.reserved_nanos < attempt.reserved_nanos:
                raise SharedDenied("inconsistent outstanding reservation")
            incurred = balance.incurred_nanos + cost
            if incurred > 2**63 - 1:
                return Change(
                    budget.model_copy(update={"circuit": "open_representation"}),
                    attempt=attempt,
                    denial="usage exceeds ledger representation",
                )
            # Validate the bound receipt, including digest format, before committing reductions.
            attempt = self._attempt_record(attempt.model_copy(
                update={"usage_hash": usage_hash, "actual_nanos": cost}))
            balance = balance.model_copy(
                update={
                    "incurred_nanos": incurred,
                    "reserved_nanos": balance.reserved_nanos - attempt.reserved_nanos,
                }
            )
            budget = budget.model_copy(
                update={
                    "balances": tuple(
                        balance if b.pool == attempt.pool else b for b in budget.balances
                    ),
                    "circuit": budget.circuit,
                }
            )
            return Change(
                budget,
                attempt=attempt,
                denial="billed usage exceeded its bound" if violation else None,
            )

        address = Address(attempt_id=attempt_id, liability_operation="reconcile")
        result = self.store.transact(address, change)
        if result.denial == "usage_circuit_committed":
            emit('cost_circuit_open', self.policy.digest(), self.grant.digest())
            result = self.store.transact(address, change)
        if result.denial:
            raise SharedDenied(result.denial)


    def _reconcile_nonbillable(self, budget, attempt, policy):
        if policy is None or attempt.actual_nanos is not None \
                or attempt.usage_hash is not None or attempt.complete_usage is not None:
            raise SharedDenied("reviewed nonbillable settlement unavailable")
        receipt = NonbillableReceipt(attempt_id=attempt.id, request_hash=attempt.request_hash,
            response_hash=attempt.response.retained_sha256, policy=policy,
            settled_at=self._now())
        receipt.validate_response(attempt.response, attempt_id=attempt.id,
            request_hash=attempt.request_hash, model_hash=attempt.model_configuration_hash,
            reserved_at=attempt.reserved_at)
        balance = budget.balance(attempt.pool)
        if balance.reserved_nanos < attempt.reserved_nanos:
            raise SharedDenied("inconsistent outstanding reservation")
        attempt = self._attempt_record(attempt.model_copy(update={
            "nonbillable_receipt": receipt, "actual_nanos": 0}))
        balance = balance.model_copy(update={
            "reserved_nanos": balance.reserved_nanos - attempt.reserved_nanos})
        budget = budget.model_copy(update={"balances": tuple(
            balance if b.pool == attempt.pool else b for b in budget.balances)})
        return Change(budget, attempt=attempt)

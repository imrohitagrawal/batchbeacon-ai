"""SA01–14 local transaction fakes, never real capacity or provider permission."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import RLock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from batchbeacon.guest_service import GuestPolicy, GuestService
from batchbeacon.shared_admission import (
    Attempt,
    Budget,
    IncidentUsage,
    Phase,
    Pool,
    PoolAllocation,
    PoolOpening,
    SessionUsage,
    SharedAdmission,
    SharedDenied,
    SharedGrant,
    SharedPolicy,
    Snapshot,
)
from batchbeacon.uploads import sanitize_images
from tests.unit.durable_fixtures import record_wire, run_binding, wire_response
from tests.unit.test_cloud_admission import NANO, NOW
from tests.unit.test_cloud_admission import policy as probe_policy
from tests.unit.test_guest_boundary import ORIGIN, MemoryObjects, MemoryRepository, picture


class AtomicMemoryStore:
    """Explicit fake shared by service instances, with double callback execution."""

    def __init__(self, guests):
        self.guests, self.budget, self.usage, self.attempts = guests, None, {}, {}
        self.lock = RLock()
        self.after_commit = lambda change: None
        self.before_commit = lambda change: None

    def create_budget(self, budget):
        with self.lock:
            if self.budget is not None:
                raise SharedDenied("budget already initialized")
            self.budget = budget.model_dump_json()

    def state(self):
        return Budget.model_validate_json(self.budget) if self.budget else None

    def transact(self, address, callback):
        with self.lock:
            guest = self.guests.get(address.guest_key) if address.guest_key else None
            usage_key = guest.scope.session_id if guest else None
            usage = (
                SessionUsage.model_validate_json(self.usage[usage_key])
                if usage_key in self.usage
                else None
            )
            attempt = (
                Attempt.model_validate_json(self.attempts[address.attempt_id])
                if address.attempt_id in self.attempts
                else None
            )
            snapshot = Snapshot(self.state(), guest, usage, attempt)
            first, result = callback(snapshot), callback(snapshot)
            assert first == result
            self.before_commit(result)
            if result.budget is not None:
                self.budget = result.budget.model_dump_json()
            if result.usage is not None:
                self.usage[result.usage.session_id] = result.usage.model_dump_json()
            if result.attempt is not None:
                self.attempts[result.attempt.id] = result.attempt.model_dump_json()
            self.after_commit(result)
            return result


@pytest.fixture
def env():
    clock = [NOW]
    repo, objects = MemoryRepository(), MemoryObjects()
    gp = GuestPolicy(origin=ORIGIN)
    guests = GuestService(gp, repo, objects, clock=lambda: clock[0])
    token, guest = guests.issue()
    iid = guests.create_incident(token, "i").id
    p = SharedPolicy(
        project_id="synthetic-project",
        guest_policy_hash=gp.digest(),
        model_configuration_hash="a" * 64,
        price=probe_policy().price,
        billable_input_bound=12000,
        billable_output_and_thought_bound=4096,
        billing_bound_evidence_hash="b" * 64,
        reserve_nanos=6 * NANO,
        allowed_tools=("read_source", "read_capture"),
    )
    g = SharedGrant(
        project_id=p.project_id,
        policy_hash=p.digest(),
        currency="INR",
        root_ceiling_nanos=2500 * NANO,
        pools=tuple(
            PoolAllocation(pool=pool, ceiling_nanos=n * NANO)
            for pool, n in [
                (Pool.DEVELOPMENT, 1250),
                (Pool.PUBLIC, 500),
                (Pool.PROTECTED, 600),
                (Pool.PROBE, 150),
            ]
        ),
        not_before=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=2),
        authority_evidence_hash="c" * 64,
        capacity_evidence_hash="d" * 64,
    )
    store = AtomicMemoryStore(repo)
    # Explicit test setup models atomic guest + usage provisioning.
    store.usage[guest.scope.session_id] = SessionUsage(
        session_id=guest.scope.session_id, incidents=(IncidentUsage(incident_id=iid),)
    ).model_dump_json()
    service = SharedAdmission(p, g, store, clock=lambda: clock[0])
    openings = tuple(
        PoolOpening(
            pool=pool,
            incurred_nanos=0,
            outstanding_nanos=0,
            lifetime_attempts=0,
            evidence_hash="e" * 64,
        )
        for pool in Pool
    )
    service.initialize(openings)
    phase = Phase(
        pool=Pool.PUBLIC,
        max_pool_liability_nanos=500 * NANO,
        not_before=NOW,
        expires_at=NOW + timedelta(days=1),
        evidence_hash="f" * 64,
    )
    service.activate_phase(phase)
    return service, store, guests, token, guest.capability_hash, iid, clock, openings


def binding(env):
    return run_binding(env[2], env[3], env[5], env[0].policy.model_configuration_hash)


def begin(env, key="r"):
    service, _, _, _, guest_key, iid, _, _ = env
    return service.begin_run(guest_key, iid, key, binding(env))


def reserve(env, run, *, attempt_id=None, operation_key="extract", request_hash="1" * 64):
    service, _, _, _, key, _, _, _ = env
    return service.reserve(
        key, run.id, attempt_id or uuid4().hex, request_hash, operation_key=operation_key
    )


def claim(env, run, attempt):
    service, _, _, _, key, _, _, _ = env
    return service.claim_dispatch(
        key, run.id, attempt.id, attempt.request_hash, attempt.model_configuration_hash
    )


def test_default_configuration_and_receipt_bindings(env):
    service, store, _, _, _, _, _, _ = env
    run = begin(env)
    assert run.deadline - run.started_at == timedelta(seconds=30)
    attempt = reserve(env, run)
    assert attempt.policy_hash == service.policy.digest()
    assert attempt.grant_hash == service.grant.digest()
    assert attempt.phase_hash == store.state().phase.digest()
    assert attempt.price == service.policy.price
    assert store.state().balance(Pool.PUBLIC).reserved_nanos == 6 * NANO
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 1
    assert not attempt.dispatch_claimed
    assert claim(env, run, attempt).dispatch_claimed
    with pytest.raises(SharedDenied, match="claim unavailable"):
        claim(env, run, attempt)


@pytest.mark.parametrize(
    "field", ["incurred_nanos", "outstanding_nanos", "lifetime_attempts", "evidence_hash"]
)
def test_unknown_opening_rejects_initialization(env, field):
    service, store, _, _, _, _, _, openings = env
    store.budget = None
    bad = (openings[0].model_copy(update={field: None}), *openings[1:])
    with pytest.raises(ValueError, match="unknown"):
        service.initialize(bad)
    assert store.budget is None


def test_exclusive_initialization_and_unknown_liability_survive_reopen(env):
    service, store, _, _, key, _, clock, openings = env
    run = begin(env)
    attempt = reserve(env, run)
    with pytest.raises(SharedDenied, match="already initialized"):
        service.initialize(openings)
    reopened = SharedAdmission(service.policy, service.grant, store, clock=lambda: clock[0])
    assert (
        reopened.reserve(key, run.id, attempt.id, attempt.request_hash, operation_key="extract")
        == attempt
    )
    assert store.state().balance(Pool.PUBLIC).committed == 6 * NANO
    with pytest.raises(SharedDenied, match="conflict"):
        reopened.reserve(key, run.id, attempt.id, "2" * 64, operation_key="extract")


def test_parallel_last_funds_and_public_cannot_draw_protected(env):
    service, store, guests, _, key1, iid1, _, _ = env
    # Server-created incident; the test has no client-controlled pool selector.
    token2, other = guests.issue()
    iid2 = guests.create_incident(token2, "i").id
    store.usage[other.scope.session_id] = SessionUsage(
        session_id=other.scope.session_id, incidents=(IncidentUsage(incident_id=iid2),)
    ).model_dump_json()
    phase = store.state().phase.model_copy(update={"max_pool_liability_nanos": 6 * NANO})
    service.activate_phase(phase)
    runs = [service.begin_run(key1, iid1, "r", binding(env)),
            service.begin_run(other.capability_hash, iid2, "r", run_binding(guests, token2, iid2))]
    services = [service, SharedAdmission(service.policy, service.grant, store, clock=service.clock)]
    keys = [key1, other.capability_hash]

    def attempt(index):
        try:
            return services[index].reserve(
                keys[index], runs[index].id, uuid4().hex, "1" * 64, operation_key="extract"
            )
        except SharedDenied:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(attempt, [0, 1]))
    assert sum(r is not None for r in results) == 1
    assert store.state().balance(Pool.PUBLIC).committed == 6 * NANO
    assert store.state().balance(Pool.PROTECTED).committed == 0
    service.activate_phase(phase)  # Re-activation is not replenishment.
    with pytest.raises(SharedDenied, match="insufficient"):
        service.reserve(key1, runs[0].id, uuid4().hex, "2" * 64, operation_key="another")


def test_one_active_run_race_fixed_identity_and_lifetime_acquisitions(env):
    service, store, _, _, key, iid, clock, _ = env

    def start(req):
        try:
            return service.begin_run(key, iid, req, binding(env))
        except SharedDenied:
            return None

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(start, ["a", "b"]))
    first = next(r for r in results if r)
    assert sum(r is not None for r in results) == 1
    assert service.begin_run(key, iid, first.request_key, binding(env)) == first
    clock[0] = first.deadline
    second = begin(env, "second")
    service.finish_run(key, first.id)  # Late old worker must not release the new slot.
    with pytest.raises(SharedDenied, match="active run"):
        begin(env, "blocked")
    service.finish_run(key, second.id, failed=True)
    third = begin(env, "third")
    service.finish_run(key, third.id)
    with pytest.raises(SharedDenied, match="lifetime acquisition"):
        begin(env, "fourth")
    usage = SessionUsage.model_validate_json(next(iter(store.usage.values())))
    assert usage.incidents[0].acquisitions == 3


@pytest.mark.parametrize("finish", [False, True])
def test_called_timeout_blocks_new_keys_without_changing_liability(env, finish):
    service, store, _, _, key, _, clock, _ = env
    run = begin(env)
    attempt = reserve(env, run)
    assert claim(env, run, attempt)
    clock[0] = run.deadline
    if finish:
        service.finish_run(key, run.id, failed=True)
    before = (store.budget, dict(store.usage), dict(store.attempts))
    with ThreadPoolExecutor(2) as workers:
        def retry(request):
            with pytest.raises(SharedDenied, match="requires operator review"):
                begin(env, request)
        list(workers.map(retry, ["new-key-a", "new-key-b"]))
    assert (store.budget, store.usage, store.attempts) == before
    repeated = service.admit_run(key, run.incident_id, run.request_key, run.binding)
    assert not repeated.fresh and repeated.run.id == run.id
    assert (store.budget, store.usage, store.attempts) == before


def test_call_tool_and_retry_caps_count_individual_attempts(env):
    service, store, _, _, key, _, _, _ = env
    run = begin(env)
    reserve(env, run)
    reserve(env, run)
    with pytest.raises(SharedDenied, match="retry allowance"):
        reserve(env, run)
    reserve(env, run, operation_key="second")
    reserve(env, run, operation_key="second")
    with pytest.raises(SharedDenied, match="model-call"):
        reserve(env, run, operation_key="third")
    for n in range(6):
        service.claim_tool(key, run.id, f"t{n}", tool_name="read_source")
    with pytest.raises(SharedDenied, match="already claimed"):
        service.claim_tool(key, run.id, "t0", tool_name="read_source")
    with pytest.raises(SharedDenied, match="tool allowance"):
        service.claim_tool(key, run.id, "t7", tool_name="read_source")
    with pytest.raises(SharedDenied, match="allowlisted"):
        service.claim_tool(key, run.id, "t8", tool_name="write_source_trust")
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 4


def test_claim_response_loss_never_grants_redispatch(env):
    service, store, _, _, _, _, _, _ = env
    run = begin(env)
    attempt = reserve(env, run)

    def lose(change):
        if change.attempt and change.attempt.dispatch_claimed:
            raise OSError("response lost after commit")

    store.after_commit = lose
    with pytest.raises(OSError):
        claim(env, run, attempt)
    store.after_commit = lambda change: None
    with pytest.raises(SharedDenied, match="claim unavailable"):
        claim(env, run, attempt)
    assert store.state().balance(Pool.PUBLIC).committed == 6 * NANO


def test_exact_post_commit_dispatch_expiry_retains_claim_and_funds(env):
    _, store, _, _, _, _, clock, _ = env
    run = begin(env)
    attempt = reserve(env, run)

    def expire(change):
        if change.attempt and change.attempt.dispatch_claimed:
            clock[0] = run.deadline

    store.after_commit = expire
    with pytest.raises(SharedDenied, match="expired after commit"):
        claim(env, run, attempt)
    assert Attempt.model_validate_json(store.attempts[attempt.id]).dispatch_claimed
    assert store.state().balance(Pool.PUBLIC).reserved_nanos == 6 * NANO


def test_late_reconciliation_uses_bound_price_without_reopening_guest(env):
    service, store, guests, token, key, iid, clock, _ = env
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    clock[0] += timedelta(days=10)
    record_wire(service, attempt)
    service.reconcile(attempt.id)
    expected = attempt.price.cost_nanos(100, 50)
    assert store.state().balance(Pool.PUBLIC).committed == expected
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 1
    service.reconcile(attempt.id)
    with pytest.raises(SharedDenied, match="conflict"):
        record_wire(service, attempt, wire_response(input_tokens=99))
    with pytest.raises(SharedDenied):
        service.begin_run(key, iid, "new", run.binding)
    with pytest.raises(Exception, match="guest_expired"):
        guests.resolve(token)


@pytest.mark.parametrize("tokens", [12001, 10**30])
def test_overbound_circuit_commits_before_error_and_survives_reopen(env, tokens):
    service, store, guests, token, key, iid, _, _ = env
    images = sanitize_images((picture(),), guests.policy.uploads)
    capture = guests.retain(token, iid, "upload", images).captures[0]
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    record_wire(service, attempt, wire_response(tokens, 1))
    with pytest.raises(SharedDenied, match="usage"):
        service.reconcile(attempt.id)
    assert store.state().circuit
    reopened = SharedAdmission(service.policy, service.grant, store, clock=service.clock)
    with pytest.raises(SharedDenied, match="circuit"):
        reopened.reserve(key, run.id, uuid4().hex, "5" * 64, operation_key="another")
    assert guests.image(token, iid, capture.id) == images[0].data
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 1


@pytest.mark.parametrize("bad", [-1, True, 1.2, None])
def test_invalid_usage_cannot_refund_unknown(env, bad):
    service, store, _, _, _, _, _, _ = env
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    record_wire(service, attempt, wire_response(bad, 2))
    with pytest.raises(ValueError):
        service.reconcile(attempt.id)
    assert store.state().balance(Pool.PUBLIC).committed == 6 * NANO


def test_verification_allowance_is_independent_of_paid_state_and_lifetime(env):
    service, store, _, _, key, iid, _, _ = env
    store.budget = None
    for n in range(6):
        service.reserve_verification(key, iid, str(n), "1" * 64)
    service.reserve_verification(key, iid, "0", "1" * 64)
    with pytest.raises(SharedDenied, match="conflict"):
        service.reserve_verification(key, iid, "0", "2" * 64)
    with pytest.raises(SharedDenied, match="verification allowance"):
        service.reserve_verification(key, iid, "7", "2" * 64)
    assert store.budget is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"max_calls_per_run": 5},
        {"max_tools_per_run": 7},
        {"max_recaptures": 3},
        {"max_verifications": 7},
        {"max_attempts_per_operation": 3},
        {"run_seconds": True},
        {"reserve_nanos": 1},
        {"billable_input_bound": None},
        {"run_seconds": float("inf")},
        {"allowed_tools": ("read_source", "read_source")},
    ],
)
def test_strict_policy_rejects_invalid_authority_values(env, overrides):
    p = env[0].policy
    with pytest.raises(ValidationError):
        SharedPolicy.model_validate({**p.model_dump(), **overrides})


def test_foreign_scope_and_policy_change_deny_without_reset(env):
    service, store, guests, _, key, iid, _, _ = env
    run = begin(env)
    attempt = reserve(env, run)
    _, other = guests.issue()
    with pytest.raises(SharedDenied):
        service.begin_run(other.capability_hash, iid, "foreign", run.binding)
    with pytest.raises(SharedDenied):
        service.claim_dispatch(
            other.capability_hash,
            run.id,
            attempt.id,
            attempt.request_hash,
            attempt.model_configuration_hash,
        )
    altered = SharedPolicy.model_validate({**service.policy.model_dump(), "run_seconds": 20})
    fresh = SharedAdmission(altered, service.grant, store, clock=service.clock)
    with pytest.raises(SharedDenied, match="authority"):
        fresh.reserve(key, run.id, uuid4().hex, "2" * 64, operation_key="another")
    assert store.state().balance(Pool.PUBLIC).committed == 6 * NANO


@pytest.mark.parametrize("operation", ["acquisition", "verification"])
@pytest.mark.parametrize("missing", ["session", "incident"])
def test_missing_established_usage_cannot_reset_lifetime_allowances(env, operation, missing):
    service, store, guests, token, key, iid, _, _ = env
    session_id = store.guests.get(key).scope.session_id
    if operation == "acquisition":
        for n in range(3):
            run = service.begin_run(key, iid, str(n), binding(env))
            service.finish_run(key, run.id)

        def invoke():
            return service.begin_run(key, iid, "extra", binding(env))
    else:
        for n in range(6):
            service.reserve_verification(key, iid, str(n), "1" * 64)

        def invoke():
            return service.reserve_verification(key, iid, "extra", "1" * 64)

    with pytest.raises(SharedDenied, match="allowance exhausted"):
        invoke()
    if missing == "session":
        del store.usage[session_id]
    else:
        old = SessionUsage.model_validate_json(store.usage[session_id])
        store.usage[session_id] = old.model_copy(update={"incidents": ()}).model_dump_json()
    before = dict(store.usage)
    with pytest.raises(SharedDenied, match="usage unavailable"):
        invoke()
    assert store.usage == before


@pytest.mark.parametrize("duplicate", [False, True])
def test_reservation_response_after_expiry_denies_without_refund(env, duplicate):
    service, store, _, _, key, _, clock, _ = env
    run = begin(env)
    attempt_id = uuid4().hex
    if duplicate:
        reserve(env, run, attempt_id=attempt_id)

    def expire(change):
        clock[0] = run.deadline

    store.after_commit = expire
    with pytest.raises(SharedDenied, match="reservation expired after commit"):
        service.reserve(key, run.id, attempt_id, "1" * 64, operation_key="extract")
    assert store.state().balance(Pool.PUBLIC).reserved_nanos == 6 * NANO
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 1
    assert not Attempt.model_validate_json(store.attempts[attempt_id]).dispatch_claimed


def test_private_development_phase_charges_only_its_existing_pool(env):
    from batchbeacon.evidence_service import replace
    service, store = env[:2]
    before = store.state()
    phase = replace(before.phase, pool=Pool.DEVELOPMENT,
                    max_pool_liability_nanos=service.policy.reserve_nanos)
    service.activate_phase(phase)
    run = begin(env, 'private-development')
    reserve(env, run)
    after = store.state()
    assert after.balance(Pool.DEVELOPMENT).reserved_nanos == service.policy.reserve_nanos
    assert after.balance(Pool.PUBLIC) == before.balance(Pool.PUBLIC)
    assert after.balance(Pool.PROTECTED) == before.balance(Pool.PROTECTED)
    service.activate_phase(phase)
    assert store.state().balance(Pool.DEVELOPMENT) == after.balance(Pool.DEVELOPMENT)
    with pytest.raises(SharedDenied):
        reserve(env, run, operation_key='another-operation')

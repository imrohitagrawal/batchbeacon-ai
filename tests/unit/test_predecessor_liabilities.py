"""Exact historical settlement after a config change never authorizes new calls."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.evidence_service import replace
from batchbeacon.shared_admission import (
    Address,
    Attempt,
    Change,
    Pool,
    PredecessorLiabilities,
    SharedAdmission,
    SharedDenied,
)
from tests.unit.durable_fixtures import record_wire, wire_response
from tests.unit.test_firestore_store import no_network_or_credentials as no_network_or_credentials  # noqa
from tests.unit.test_firestore_store import setup as setup  # noqa
from tests.unit.test_nonbillable_reconciliation import policy as error_policy
from tests.unit.test_shared_admission import begin, claim, reserve
from tests.unit.test_shared_admission import env as env  # noqa


def manifest(old, policy, grant, attempt, **scope):
    return PredecessorLiabilities(
        project_id=policy.project_id, database_id="(default)", namespace="sdk_tests",
        environment_id="sfa_first", successor_grant_hash=grant.digest(),
        successor_policy_hash=policy.digest(), original_grant=old.grant,
        original_policy=old.policy, reservations=(attempt,), **scope)


def migrate(env, *, rule=None):
    old, store = env[:2]
    run = begin(env)
    a = claim(env, run, reserve(env, run))
    old.finish_run(env[4], run.id, failed=True)
    p = replace(old.policy, model_configuration_hash="2" * 64, run_seconds=50,
                price=replace(old.policy.price, input_nanos_per_million=1))
    g = replace(old.grant, policy_hash=p.digest())
    m = manifest(old, p, g, a, nonbillable_policy=rule)
    # Explicit operator migration fixture: only metadata, never counters/liability.
    store.budget = replace(store.state(), grant_hash=g.digest(),
                           policy_hash=p.digest()).model_dump_json()
    current = SharedAdmission(p, g, store, clock=lambda: env[6][0],
                              predecessor_liabilities=m)
    return old, current, m, a, run


def test_original_usage_settles_once_after_expiry_at_original_price(env):
    old, current, m, a, run = migrate(env)
    store = env[1]
    before = store.state()
    env[6][0] += timedelta(days=3)
    record_wire(current, a, wire_response(100, 10))
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: current.reconcile(a.id), range(2)))
    after = store.state()
    settled = Attempt.model_validate_json(store.attempts[a.id])
    assert settled.actual_nanos == a.price.cost_nanos(100, 10)
    assert settled.actual_nanos != current.policy.price.cost_nanos(100, 10)
    assert settled.grant_hash == m.original_grant.digest()
    assert (after.balance(a.pool).reserved_nanos
            == before.balance(a.pool).reserved_nanos - a.reserved_nanos)
    assert (after.balance(a.pool).incurred_nanos
            == before.balance(a.pool).incurred_nanos + settled.actual_nanos)
    assert after.balance(a.pool).lifetime_attempts == before.balance(a.pool).lifetime_attempts
    assert (after.phase, after.circuit, after.grant_hash, after.policy_hash) == (
        before.phase, before.circuit, before.grant_hash, before.policy_hash)
    with pytest.raises(SharedDenied):
        current.claim_dispatch(env[4], run.id, a.id, a.request_hash, a.model_configuration_hash)
    with pytest.raises(SharedDenied):
        old.reconcile(a.id)
    assert store.state() == after


def test_unknown_original_response_cannot_release_or_redispatch(env):
    _, current, _, a, run = migrate(env)
    before = env[1].state()
    with pytest.raises(SharedDenied, match="complete usage unavailable"):
        current.reconcile(a.id)
    assert env[1].state() == before
    with pytest.raises(SharedDenied):
        current.claim_dispatch(env[4], run.id, a.id, a.request_hash, a.model_configuration_hash)
    assert env[1].state() == before


@pytest.mark.parametrize("field,value", [
    ("request_hash", "3" * 64), ("phase_hash", "3" * 64),
    ("operation_key", "other"), ("run_binding_hash", "3" * 64),
    ("session_id", "3" * 32), ("incident_id", "3" * 32), ("run_id", "3" * 32),
    ("model_configuration_hash", "3" * 64), ("reserved_nanos", 1),
    ("grant_hash", "3" * 64), ("policy_hash", "3" * 64),
    ("dispatch_claimed", False), ("pool", Pool.DEVELOPMENT),
])
def test_allowlist_requires_exact_immutable_original(env, field, value):
    _, current, _, a, _ = migrate(env)
    env[1].attempts[a.id] = replace(a, **{field: value}).model_dump_json()
    before = env[1].state()
    with pytest.raises(SharedDenied):
        record_wire(current, a, wire_response(100, 10))
    assert env[1].state() == before


def test_wrong_budget_missing_manifest_and_response_conflict_deny(env):
    _, current, m, a, _ = migrate(env)
    before = env[1].state()
    for changes in ({"grant_hash": "4" * 64}, {"policy_hash": "4" * 64}):
        env[1].budget = replace(before, **changes).model_dump_json()
        with pytest.raises(SharedDenied):
            record_wire(current, a, wire_response(100, 10))
    env[1].budget = before.model_dump_json()
    current.predecessor_liabilities = None
    with pytest.raises(SharedDenied):
        record_wire(current, a, wire_response(100, 10))
    current.predecessor_liabilities = m
    current.record_response(a.id, a.request_hash, b"{", status_code=200,
                            complete=False, observed_bytes=1)
    with pytest.raises(SharedDenied, match="conflict"):
        record_wire(current, a, wire_response(100, 10))
    with pytest.raises(ValueError):
        current.reconcile(a.id)
    assert env[1].state() == before


@pytest.mark.parametrize("original_rule", [False, True])
def test_nonbillable_uses_only_original_explicit_rule(env, original_rule):
    rule = error_policy(env)
    _, current, _, a, _ = migrate(env, rule=rule if original_rule else None)
    current.nonbillable_policy = replace(rule,
        model_configuration_hash=current.policy.model_configuration_hash)
    raw = b'{"error":{"code":504,"status":"DEADLINE_EXCEEDED","message":"synthetic"}}'
    current.record_response(a.id, a.request_hash, raw, status_code=504,
                            complete=True, observed_bytes=len(raw))
    before = env[1].state()
    if original_rule:
        current.reconcile(a.id)
        settled = Attempt.model_validate_json(env[1].attempts[a.id])
        assert settled.nonbillable_receipt.policy == rule and settled.actual_nanos == 0
    else:
        with pytest.raises(SharedDenied):
            current.reconcile(a.id)
        assert env[1].state() == before


def test_manifest_validation_and_storage_operation_limits(env):
    _, current, m, a, _ = migrate(env)
    for changes in ({"reservations": (a, a)}, {"reservations": ()},
                    {"reservations": (replace(a, dispatch_claimed=False),)},
                    {"original_policy": current.policy},
                    {"project_id": "other-project"}):
        with pytest.raises(ValidationError):
            replace(m, **changes)
    with pytest.raises(ValueError):
        SharedAdmission(current.policy, replace(current.grant, capacity_evidence_hash="9" * 64),
                        env[1], predecessor_liabilities=m)
    assert not m.permits(env[1].state(), a, None)
    assert not m.permits(env[1].state(), a, "claim_dispatch")


def test_installed_sdk_enforces_manifest_before_callback(setup, env):
    from batchbeacon.firestore_store import FirestoreStores
    from tests.unit.durable_fixtures import run_binding
    from tests.unit.firestore_rpc_fake import client
    from tests.unit.test_firestore_store import owned, saved, shared

    stores, server = setup[:2]
    token, session, incident = owned(setup)
    old = shared(setup, env)
    stores.shared.create_budget(env[1].state())
    run = old.begin_run(session.capability_hash, incident.id, "run",
                        run_binding(setup[2], token, incident.id))
    a = old.reserve(session.capability_hash, run.id, "b" * 32, "c" * 64,
                    operation_key="extract")
    a = old.claim_dispatch(session.capability_hash, run.id, a.id,
                            a.request_hash, a.model_configuration_hash)
    p = replace(old.policy, run_seconds=50)
    g = replace(old.grant, policy_hash=p.digest())
    m = manifest(old, p, g, a)
    budget = replace(saved(setup, "budget"), grant_hash=g.digest(), policy_hash=p.digest())
    server.seed(stores._encode(stores.name("budget"), "budget", budget))
    cold = FirestoreStores(client(server), stores.policy, stores.guest_policy,
        stores.evidence_policy, stores.action_policy, predecessor_liabilities=m,
        clock=stores.clock)
    current = SharedAdmission(p, g, cold.shared, predecessor_liabilities=m, clock=stores.clock)
    for address in (Address(attempt_id=a.id),
                    Address(attempt_id=a.id, liability_operation="claim_dispatch")):
        with pytest.raises(OSError):
            cold.shared.transact(address, lambda s: Change(s.budget, attempt=s.attempt))
    with pytest.raises(OSError):
        record_wire(SharedAdmission(p, g, stores.shared, predecessor_liabilities=m),
                    a, wire_response(100, 10))
    record_wire(current, a, wire_response(100, 10))
    current.reconcile(a.id)
    assert saved(setup, "attempt", a.id).actual_nanos == a.price.cost_nanos(100, 10)
    for key, value in (("database_id", "other"), ("namespace", "other"),
                       ("environment_id", "other"), ("project_id", "other-project")):
        with pytest.raises(ValueError, match="scope"):
            FirestoreStores(client(server), replace(stores.policy, **{key: value}),
                stores.guest_policy, stores.evidence_policy, stores.action_policy,
                predecessor_liabilities=m)

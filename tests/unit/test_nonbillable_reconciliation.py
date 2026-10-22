"""Complete provider-error accounting; unknown outcomes never release liability."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.attempt_evidence import NonbillablePolicy
from batchbeacon.shared_admission import Attempt, SharedDenied
from tests.unit.test_shared_admission import begin, claim, reserve
from tests.unit.test_shared_admission import env as env  # noqa


def policy(env, **overrides):
    s, *_, clock, _ = env
    values = dict(
        model_id="gemini-3.8-flash",
        model_configuration_hash=s.policy.model_configuration_hash,
        endpoint="https://aiplatform.googleapis.com/v1/projects/synthetic-project/locations/global/"
        "publishers/google/models/gemini-3.8-flash:generateContent",
        source_url="https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing",
        source_sha256="1" * 64,
        applicability_evidence_sha256="2" * 64,
        effective_from=clock[0] - timedelta(days=1),
        observed_at=clock[0],
        valid_until=clock[0] + timedelta(days=1),
        statuses=(504,),
    )
    return NonbillablePolicy(**(values | overrides))


def failed(env, *, status=504, complete=True, body=None):
    s = env[0]
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    raw = json.dumps(
        body
        or {
            "error": {
                "code": status,
                "status": "DEADLINE_EXCEEDED",
                "message": "private-error-canary",
            }
        }
    ).encode()
    s.record_response(
        attempt.id,
        attempt.request_hash,
        raw,
        status_code=status,
        complete=complete,
        observed_bytes=len(raw),
    )
    s.finish_run(env[4], run.id, failed=True)
    return attempt, run


def test_stranded_reservation_released_once_without_reset_or_false_usage(env):
    s, store = env[:2]
    a, run = failed(env)
    before = store.state()
    # Existing semantics preserve the full reservation in the absence of a reviewed rule.
    with pytest.raises(SharedDenied):
        s.reconcile(a.id)
    assert store.state() == before
    s.nonbillable_policy = policy(env)
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda _: s.reconcile(a.id), range(2)))
    settled = Attempt.model_validate_json(store.attempts[a.id])
    assert settled.actual_nanos == 0 and settled.usage_hash is None
    assert settled.complete_usage is None and settled.nonbillable_receipt is not None
    assert "private-error-canary" in settled.response.original().decode()
    after = store.state()
    assert (
        after.balance(a.pool).reserved_nanos
        == before.balance(a.pool).reserved_nanos - a.reserved_nanos
    )
    assert after.balance(a.pool).incurred_nanos == before.balance(a.pool).incurred_nanos
    assert after.balance(a.pool).lifetime_attempts == before.balance(a.pool).lifetime_attempts
    assert after.phase == before.phase and after.grant_hash == before.grant_hash
    assert after.policy_hash == before.policy_hash and after.circuit == before.circuit
    assert s.inspect_run(env[4], run.id).terminal == "failed"
    assert s.inspect_run(env[4], run.id).calls == 1
    original = store.attempts[a.id]
    s.nonbillable_policy = None  # Compatible rollback reader, no new settlement authority.
    s.reconcile(a.id)
    assert store.attempts[a.id] == original and store.state() == after
    with pytest.raises(SharedDenied):
        claim(env, run, a)


@pytest.mark.parametrize(
    "case",
    [
        "incomplete",
        "missing",
        "wrong_status",
        "bad_body",
        "mixed_usage",
        "wrong_code",
        "wrong_model",
        "future_rule",
        "expired_rule",
        "before_observation",
    ],
)
def test_unsubstantiated_or_out_of_scope_failure_keeps_full_reservation(env, case):
    s, store = env[:2]
    if case == "missing":
        run = begin(env)
        a = reserve(env, run)
        claim(env, run, a)
    else:
        body = {"error": {"code": 504, "status": "DEADLINE_EXCEEDED"}}
        if case == "bad_body":
            body = {"unexpected": "private-error-canary"}
        elif case == "mixed_usage":
            body["usageMetadata"] = {"totalTokenCount": 0}
        elif case == "wrong_code":
            body["error"]["code"] = 503
        a, _ = failed(
            env,
            complete=case != "incomplete",
            status=503 if case == "wrong_status" else 504,
            body=body,
        )
    overrides = {}
    now = env[6][0]
    if case == "wrong_model":
        overrides["model_configuration_hash"] = "b" * 64
    if case == "future_rule":
        overrides.update(
            effective_from=now + timedelta(seconds=1), observed_at=now + timedelta(seconds=1)
        )
    if case == "expired_rule":
        overrides.update(
            observed_at=now - timedelta(seconds=2), valid_until=now - timedelta(seconds=1)
        )
    if case == "before_observation":
        overrides["observed_at"] = now + timedelta(seconds=1)
    s.nonbillable_policy = policy(env, **overrides)
    before, raw = store.state(), store.attempts[a.id]
    with pytest.raises((SharedDenied, ValueError)):
        s.reconcile(a.id)
    assert store.state() == before and store.attempts[a.id] == raw


def test_old_attempt_wire_shape_preserved_and_new_receipt_tampering_denied(env):
    s, store = env[:2]
    a, _ = failed(env)
    assert "nonbillable_receipt" not in json.loads(store.attempts[a.id])
    s.nonbillable_policy = policy(env)
    s.reconcile(a.id)
    raw = json.loads(store.attempts[a.id])
    for change in ("request_hash", "response_hash", "attempt_id"):
        broken = json.loads(json.dumps(raw))
        broken["nonbillable_receipt"][change] = "c" * 64
        with pytest.raises(ValueError):
            Attempt.model_validate(broken)
    raw["actual_nanos"] = 1
    with pytest.raises(ValueError):
        Attempt.model_validate(raw)


@pytest.mark.parametrize(
    "overrides",
    [
        {"statuses": (200,)},
        {"statuses": ()},
        {"statuses": (504, 504)},
        {"source_sha256": ""},
        {"applicability_evidence_sha256": ""},
        {
            "endpoint": "https://other.example/v1/projects/a/locations/global/publishers/google/models/other:generateContent"
        },
    ],
)
def test_invalid_policy_fails_closed(env, overrides):
    with pytest.raises(ValidationError):
        policy(env, **overrides)


def test_verified_error_releases_capacity_for_an_already_admitted_next_run(env):
    from batchbeacon.shared_admission import Pool
    from tests.unit.test_cloud_admission import NANO
    s, store = env[:2]
    a, _ = failed(env)
    budget = store.state()
    balance = budget.balance(Pool.PUBLIC).model_copy(update={'incurred_nanos': 490 * NANO})
    store.budget = budget.model_copy(update={'balances': tuple(
        balance if b.pool == Pool.PUBLIC else b for b in budget.balances)}).model_dump_json()
    next_run = begin(env, 'next-acquisition')
    with pytest.raises(SharedDenied, match='insufficient uncommitted model allowance'):
        reserve(env, next_run)
    assert s.inspect_run(env[4], next_run.id).calls == 0
    s.nonbillable_policy = policy(env)
    s.reconcile(a.id)
    admitted = reserve(env, next_run)
    assert admitted.reserved_nanos == s.policy.reserve_nanos
    assert store.state().balance(Pool.PUBLIC).incurred_nanos == 490 * NANO
    assert store.state().balance(Pool.PUBLIC).lifetime_attempts == 2

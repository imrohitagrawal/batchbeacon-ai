"""T08 denial/concurrency tests; no credentials, network or real spending."""

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from batchbeacon.cloud_policy import (
    ModelPrice,
    ModelProbePolicy,
    OpeningLiabilities,
    PriorAttemptDay,
    ProbeGrant,
    validate_admission,
)
from batchbeacon.operator_admission import AdmissionDenied, OperatorLedger

NOW = datetime(2026, 10, 18, 0, 0, tzinfo=UTC)
NANO = 1_000_000_000


def policy(**overrides):
    values = dict(
        project_id="synthetic-project", model_id="gemini-3.8-flash",
        model_location="global", api_version="v1", thinking_level="LOW",
        price=ModelPrice(
            currency="INR", input_nanos_per_million=143_983_124_998,
            output_nanos_per_million=719_915_624_990,
            evidence_sha256="a" * 64, observed_at=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=2),
        ),
        billable_input_token_bound=12000,
        billable_output_token_bound=4096, billing_bound_evidence_sha256="b" * 64,
        reserve_nanos=6 * NANO,
    )
    return ModelProbePolicy(**(values | overrides))


def grant(p, **overrides):
    return ProbeGrant(**(dict(
        project_id=p.project_id, policy_sha256=p.digest(), pool="model_probes",
        currency="INR", allocation_nanos=150 * NANO,
        not_before=NOW - timedelta(days=1), expires_at=NOW + timedelta(days=2),
        authority_evidence_sha256="c" * 64, global_capacity_evidence_sha256="d" * 64,
    ) | overrides))


def make_ledger(tmp_path, p=None, g=None, prior=0):
    p = p or policy()
    g = g or grant(p)
    ledger = OperatorLedger(tmp_path / "operator.sqlite", p, g)
    ledger.initialize(OpeningLiabilities(
        incurred_nanos=prior, outstanding_nanos=0, evidence_sha256="e" * 64,
        prior_attempt_days=(),
    ), now=NOW)
    return ledger


def test_exact_gross_price_rounds_up_to_nanorupee():
    assert policy().price.cost_nanos(12000, 4096) == 4_676_571_900
    assert policy().price.cost_nanos(1, 0) == 143_984


@pytest.mark.parametrize("values", [
    {"request_timeout_ms": 0}, {"request_timeout_ms": "30000"},
    {"request_timeout_ms": float("inf")}, {"run_deadline_ms": -1},
    {"request_timeout_ms": 30001}, {"sdk_attempts": 5}, {"max_llm_calls": 0},
    {"candidate_count": 2}, {"max_input_tokens": True},
    {"max_input_tokens": 1.1}, {"reserve_nanos": 4 * NANO},
    {"billable_output_token_bound": 4095}, {"calendar_timezone": "Made/Up"},
    {"max_total_attempts": 0}, {"max_daily_attempts": 23},
    {"ledger_lock_timeout_ms": 0}, {"extra_unknown": True},
    {"sdk_attempts": True}, {"max_llm_calls": 1.0}, {"candidate_count": True},
    {"automatic_continuation": True}, {"automatic_continuation": 0},
    {"billable_input_token_bound": 11999},
])
def test_invalid_or_incompatible_configuration_fails(values):
    with pytest.raises(ValidationError):
        policy(**values)


@pytest.mark.parametrize("field", [
    "max_source_bytes", "max_image_bytes", "max_image_pixels",
    "max_response_bytes", "max_count_response_bytes",
])
@pytest.mark.parametrize("value", [0, "1024", float("inf")])
def test_probe_size_policy_rejects_nonpositive_or_nonstrict_values(field, value):
    with pytest.raises(ValidationError):
        policy(**{field: value})


def test_policy_overrides_reach_sdk_consumers_and_change_binding():
    p = policy(request_timeout_ms=9000, run_deadline_ms=12000,
               max_output_tokens=1024, thinking_level="MEDIUM")
    http = p.http_options()
    generation = p.generation_config()
    assert http.timeout == 9000 and http.retry_options.attempts == 1
    assert generation.http_options == http
    assert generation.max_output_tokens == 1024
    assert generation.thinking_config.thinking_level == "MEDIUM"
    assert generation.automatic_function_calling.disable
    assert generation.automatic_continuation is False
    assert not generation.tools and not generation.cached_content
    assert p.digest() != policy().digest()


@pytest.mark.parametrize("overrides", [
    {"project_id": "unrelated-project"}, {"policy_sha256": "f" * 64},
    {"not_before": NOW + timedelta(seconds=1)}, {"expires_at": NOW},
])
def test_allocation_does_not_admit_changed_or_expired_settings(overrides):
    p = policy()
    with pytest.raises(ValueError):
        validate_admission(p, grant(p, **overrides), NOW)


def test_stale_prices_and_naive_clock_fail():
    p = policy()
    g = grant(p, expires_at=NOW + timedelta(days=3))
    with pytest.raises(ValueError, match="price"):
        validate_admission(p, g, NOW + timedelta(days=2))
    with pytest.raises(ValueError, match="timezone"):
        validate_admission(p, g, NOW.replace(tzinfo=None))


@pytest.mark.parametrize("values", [
    (None, 0, "e" * 64), (0, None, "e" * 64), (0, 0, None),
])
def test_unknown_opening_spend_never_creates_ledger(tmp_path, values):
    p = policy()
    ledger = OperatorLedger(tmp_path / "operator.sqlite", p, grant(p))
    with pytest.raises(ValueError, match="unknown"):
        ledger.initialize(OpeningLiabilities(
            incurred_nanos=values[0], outstanding_nanos=values[1], evidence_sha256=values[2],
            prior_attempt_days=(),
        ), now=NOW)
    assert not ledger.path.exists()


def test_restart_keeps_unknown_cost_and_never_reuses_reservation(tmp_path):
    ledger = make_ledger(tmp_path, prior=2 * NANO)
    receipt = ledger.reserve("first", "f" * 64, now=NOW)
    reopened = OperatorLedger(ledger.path, ledger.policy, ledger.grant)
    assert receipt.policy_sha256 == ledger.policy.digest()
    assert reopened.snapshot()["committed_nanos"] == 8 * NANO
    assert reopened.snapshot()["unknown_attempts"] == 1
    with pytest.raises(AdmissionDenied, match="already reserved"):
        reopened.reserve("first", "f" * 64, now=NOW)
    with pytest.raises(AdmissionDenied, match="attempt allowance"):
        reopened.reserve("second", "f" * 64, now=NOW)
    with pytest.raises(FileExistsError):
        reopened.initialize(OpeningLiabilities(
            incurred_nanos=0, outstanding_nanos=0, evidence_sha256="e" * 64,
            prior_attempt_days=(),
        ), now=NOW)


def test_calendar_rollover_does_not_replenish_money_or_total_attempts(tmp_path):
    p = policy(max_total_attempts=1)
    ledger = make_ledger(tmp_path, p)
    ledger.reserve("first", "f" * 64, now=NOW)
    with pytest.raises(AdmissionDenied, match="attempt allowance"):
        ledger.reserve("next-day", "f" * 64, now=NOW + timedelta(days=1))
    assert ledger.snapshot()["committed_nanos"] == 6 * NANO


def test_unknown_reservation_cannot_be_spent_after_restart(tmp_path):
    p = policy(max_daily_attempts=2)
    ledger = make_ledger(tmp_path, p, grant(p, allocation_nanos=10 * NANO))
    ledger.reserve("first", "f" * 64, now=NOW)
    reopened = OperatorLedger(ledger.path, p, ledger.grant)
    with pytest.raises(AdmissionDenied, match="insufficient"):
        reopened.reserve("retry", "f" * 64, now=NOW)


def test_concurrent_reservations_cannot_double_spend(tmp_path):
    p = policy(max_daily_attempts=10)
    ledger = make_ledger(tmp_path, p, grant(p, allocation_nanos=6 * NANO))

    def reserve_one(i):
        other = OperatorLedger(ledger.path, p, ledger.grant)
        try:
            return other.reserve(str(i), "f" * 64, now=NOW)
        except AdmissionDenied:
            return None

    with ThreadPoolExecutor(max_workers=6) as executor:
        receipts = list(executor.map(reserve_one, range(6)))
    assert sum(r is not None for r in receipts) == 1
    assert ledger.snapshot()["committed_nanos"] == 6 * NANO


def test_reconciliation_is_idempotent_but_cannot_reset_attempt_count(tmp_path):
    ledger = make_ledger(tmp_path)
    ledger.reserve("first", "f" * 64, now=NOW)
    for _ in range(2):
        ledger.reconcile("first", input_tokens=1000, output_and_thought_tokens=100,
                         usage_sha256="a" * 64)
    state = ledger.snapshot()
    assert state["committed_nanos"] == 215_974_688
    assert state["attempts"] == 1 and state["unknown_attempts"] == 0
    with pytest.raises(AdmissionDenied, match="conflicting"):
        ledger.reconcile("first", input_tokens=1, output_and_thought_tokens=1,
                         usage_sha256="b" * 64)
    with pytest.raises(AdmissionDenied, match="attempt allowance"):
        ledger.reserve("again", "f" * 64, now=NOW)


def test_usage_overrun_retains_actual_cost_and_opens_circuit(tmp_path):
    p = policy(max_daily_attempts=2)
    ledger = make_ledger(tmp_path, p)
    ledger.reserve("first", "f" * 64, now=NOW)
    ledger.reconcile("first", input_tokens=100000, output_and_thought_tokens=100000,
                     usage_sha256="a" * 64)
    state = ledger.snapshot()
    assert state["committed_nanos"] > 6 * NANO and state["circuit_open"]
    with pytest.raises(AdmissionDenied, match="circuit"):
        ledger.reserve("next", "f" * 64, now=NOW)


def test_missing_ledger_and_changed_config_fail_without_reinitialization(tmp_path):
    ledger = make_ledger(tmp_path)
    p = policy(request_timeout_ms=10000)
    with pytest.raises(AdmissionDenied, match="another policy"):
        OperatorLedger(ledger.path, p, grant(p)).reserve("first", "f" * 64, now=NOW)
    with pytest.raises(AdmissionDenied, match="missing"):
        OperatorLedger(tmp_path / "missing.sqlite", p, grant(p)).reserve(
            "first", "f" * 64, now=NOW,
        )


def test_opening_attempts_are_not_reset_by_new_ledger(tmp_path):
    p = policy()
    ledger = OperatorLedger(tmp_path / "operator.sqlite", p, grant(p))
    ledger.initialize(OpeningLiabilities(
        incurred_nanos=1 * NANO, outstanding_nanos=0, evidence_sha256="e" * 64,
        prior_attempt_days=(PriorAttemptDay(day=NOW.date(), attempts=1),),
    ), now=NOW)
    with pytest.raises(AdmissionDenied, match="attempt allowance"):
        ledger.reserve("again", "f" * 64, now=NOW)
    assert ledger.snapshot()["attempts"] == 1


def test_unknown_prior_attempts_cannot_initialize(tmp_path):
    p = policy()
    ledger = OperatorLedger(tmp_path / "operator.sqlite", p, grant(p))
    with pytest.raises(ValueError, match="unknown"):
        ledger.initialize(OpeningLiabilities(
            incurred_nanos=0, outstanding_nanos=0, evidence_sha256="e" * 64,
            prior_attempt_days=None,
        ), now=NOW)
    assert not ledger.path.exists()


def test_unrepresentable_provider_usage_closes_circuit(tmp_path):
    p = policy(max_daily_attempts=2)
    ledger = make_ledger(tmp_path, p)
    ledger.reserve("first", "f" * 64, now=NOW)
    with pytest.raises(AdmissionDenied, match="representation"):
        ledger.reconcile("first", input_tokens=10**18, output_and_thought_tokens=0,
                         usage_sha256="a" * 64)
    assert ledger.snapshot()["circuit_open"]
    assert ledger.snapshot()["unknown_attempts"] == 1
    with pytest.raises(AdmissionDenied, match="circuit"):
        ledger.reserve("next", "f" * 64, now=NOW)


def test_development_extraction_grant_is_explicit_and_distinct_from_daily_probe():
    p = policy()
    daily = grant(p)
    development = grant(p, pool="development", purpose="development_extraction",
                        allocation_nanos=250 * NANO)
    assert development.digest() != daily.digest()
    validate_admission(p, development, NOW)
    for updates in ({"pool":"development"}, {"purpose":"development_extraction"}):
        with pytest.raises(ValueError):
            grant(p, **updates)


def test_operator_adk_run_suppresses_content_telemetry():
    telemetry = policy().run_config().telemetry
    assert not telemetry.should_add_content_to_legacy_spans
    assert not telemetry.should_emit_experimental_telemetry

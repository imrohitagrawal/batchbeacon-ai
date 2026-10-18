"""DR01–14 shared durable lineage/evidence; explicit in-memory transactions only."""

import json
import traceback
from datetime import timedelta
from hashlib import sha256
from uuid import uuid4

import pytest
from pydantic import ValidationError

from batchbeacon.attempt_evidence import AttemptEvidenceLimits, response_evidence
from batchbeacon.extraction_records import InputManifest, RunBinding
from batchbeacon.shared_admission import (
    Attempt,
    Run,
    SessionUsage,
    SharedAdmission,
    SharedDenied,
    SharedGrant,
    SharedPolicy,
)
from tests.unit.durable_fixtures import record_wire, wire_response
from tests.unit.test_shared_admission import begin, binding, claim, reserve
from tests.unit.test_shared_admission import env as env  # noqa: F401


def saved(env, attempt):
    return Attempt.model_validate_json(env[1].attempts[attempt.id])


def started(env):
    run = begin(env)
    attempt = reserve(env, run)
    claim(env, run, attempt)
    return run, attempt


def configure(env, **limits):
    old, store, *rest = env
    evidence = AttemptEvidenceLimits.model_validate({**old.policy.evidence_limits.model_dump(),
                                                     **limits})
    policy = SharedPolicy.model_validate({**old.policy.model_dump(), "evidence_limits": evidence})
    grant = SharedGrant.model_validate({**old.grant.model_dump(), "policy_hash": policy.digest()})
    budget = store.state().model_copy(update={"policy_hash": policy.digest(),
                                            "grant_hash": grant.digest()})
    store.budget = budget.model_dump_json()
    return (SharedAdmission(policy, grant, store, clock=old.clock), store, *rest)


def test_missing_binding_and_legacy_run_deny_without_reset(env):
    service, store, _, _, key, iid, *_ = env
    with pytest.raises(TypeError):
        service.begin_run(key, iid, "missing")
    assert not SessionUsage.model_validate_json(next(iter(store.usage.values()))).runs
    run = begin(env)
    old = run.model_dump(mode="json")
    del old["binding"]
    with pytest.raises(ValidationError):
        Run.model_validate_json(json.dumps(old))
    with pytest.raises(ValidationError):
        RunBinding.model_validate({})


@pytest.mark.parametrize("field", ["notice_digest", "prompt_hash", "schema_hash", "policy_hash",
                                   "prompt_version", "source_bytes", "source_characters"])
def test_changed_manifest_with_same_key_conflicts(env, field):
    run = begin(env)
    value = 7 if field.endswith(("bytes", "characters")) else \
        "changed" if field == "prompt_version" else "f" * 64
    changed = run.binding.model_copy(update={"manifest": run.binding.manifest.model_copy(
        update={field: value})})
    before = dict(env[1].usage)
    with pytest.raises(SharedDenied, match="conflict"):
        env[0].begin_run(env[4], env[5], "r", changed)
    assert env[1].usage == before


@pytest.mark.parametrize("field,value", [("expected_observation_revision", 1),
    ("application_configuration_hash", "f" * 64), ("logical_operation", "changed")])
def test_changed_run_binding_conflicts(env, field, value):
    run = begin(env)
    with pytest.raises(SharedDenied, match="conflict"):
        env[0].begin_run(env[4], env[5], "r", run.binding.model_copy(update={field: value}))


def test_source_revision_and_capture_order_conflict(env):
    from batchbeacon.uploads import sanitize_images
    from tests.unit.test_guest_boundary import picture
    service, _, guests, token, key, iid, *_ = env
    b = binding(env)
    second = guests.retain(token, iid, "second", sanitize_images((picture(),),
                            guests.policy.uploads)).captures[0]
    b = b.model_copy(update={"manifest": b.manifest.model_copy(
        update={"captures": (*b.manifest.captures, second)})})
    service.begin_run(key, iid, "run", b)
    for changed in [b.manifest.model_copy(update={"captures": b.manifest.captures[::-1]}),
                    b.manifest.model_copy(update={"source": b.manifest.source.model_copy(
                        update={"epoch": b.manifest.source.epoch + 1})})]:
        with pytest.raises(SharedDenied, match="conflict"):
            service.begin_run(key, iid, "run", b.model_copy(update={"manifest": changed}))


@pytest.mark.parametrize("mode", ["foreign", "pending", "hash", "dimensions", "duplicate"])
def test_unowned_or_changed_ready_capture_denied_without_acquisition(env, mode):
    service, store, guests, _, key, iid, *_ = env
    b = binding(env)
    capture = b.manifest.captures[0]
    if mode == "pending":
        session = guests.repository.get(key)
        incident = session.incidents[0]
        batch = incident.batches[0].model_copy(update={"ready": False})
        guests.repository.data[key] = session.model_copy(update={"incidents": (
            incident.model_copy(update={"batches": (batch,)}),)}).model_dump_json()
    else:
        fields = {"foreign": {"id": "f" * 32}, "hash": {"sha256": "e" * 64},
                  "dimensions": {"width": capture.width + 1}, "duplicate": {}}
        captures = (capture, capture) if mode == "duplicate" else \
            (capture.model_copy(update=fields[mode]),)
        b = b.model_copy(update={"manifest": b.manifest.model_copy(update={"captures": captures})})
    before = dict(store.usage)
    with pytest.raises(SharedDenied, match="capture"):
        service.begin_run(key, iid, "denied", b)
    assert store.usage == before


def test_binding_config_limit_and_strict_limit_validation(env):
    b = binding(env)
    env = configure(env, max_run_binding_bytes=10)
    with pytest.raises(SharedDenied, match="binding"):
        env[0].begin_run(env[4], env[5], "run", b)
    assert not SessionUsage.model_validate_json(next(iter(env[1].usage.values()))).runs
    for override in [{"max_response_bytes": True}, {"max_json_depth": 0},
                     {"max_response_bytes": 400000}, {"max_attempt_record_bytes": -1}]:
        with pytest.raises(ValidationError):
            AttemptEvidenceLimits(**override)


def test_terminal_reconciliation_returns_history_without_resumption(env):
    run, attempt = started(env)
    service, store, _, _, key, iid, clock, _ = env
    service.finish_run(key, run.id, failed=True)
    clock[0] = run.deadline + timedelta(seconds=1)
    store.budget = store.state().model_copy(update={"phase": None}).model_dump_json()
    historical = service.begin_run(key, iid, "r", run.binding)
    assert historical.id == run.id and historical.deadline == run.deadline
    assert historical.terminal == "failed" and historical.attempt_ids == (attempt.id,)
    assert service.inspect_run(key, run.id) == historical
    assert service.inspect_attempt(key, run.id, attempt.id).id == attempt.id
    with pytest.raises(SharedDenied, match="ended"):
        reserve(env, run)
    clock[0] += timedelta(days=10)
    with pytest.raises(SharedDenied, match="guest"):
        service.inspect_run(key, run.id)


def test_lost_run_and_reservation_ack_reconstruct_exact_identity(env):
    service, store, _, _, key, iid, *_ = env
    b = binding(env)
    def lost(_):
        raise OSError("test lost ack")
    store.after_commit = lost
    with pytest.raises(OSError):
        service.begin_run(key, iid, "lost", b)
    store.after_commit = lambda _: None
    run = service.begin_run(key, iid, "lost", b)
    aid = uuid4().hex
    store.after_commit = lost
    with pytest.raises(OSError):
        reserve(env, run, attempt_id=aid)
    store.after_commit = lambda _: None
    cold = SharedAdmission(service.policy, service.grant, store, clock=service.clock)
    history = cold.inspect_run(key, run.id)
    assert history.attempt_ids == (aid,) and history.calls == 1
    attempt = cold.inspect_attempt(key, run.id, aid)
    assert attempt.run_binding_hash == b.digest()
    assert cold.reserve(key, run.id, aid, attempt.request_hash, operation_key="extract") == attempt
    assert SessionUsage.model_validate_json(next(iter(store.usage.values()))).incidents[0] \
        .acquisitions == 1


@pytest.mark.parametrize("raw,status", [(b'{"unparsed":', 200), (b'\xff\x00', 500),
                                        (b'provider unavailable', 503)])
def test_original_invalid_bytes_retained_before_parse(env, monkeypatch, raw, status):
    _, attempt = started(env)
    def forbidden(*args):
        raise AssertionError("must retain before interpretation")
    monkeypatch.setattr("batchbeacon.shared_admission.derive_usage", forbidden)
    record_wire(env[0], attempt, raw, status_code=status)
    response = saved(env, attempt).response
    assert response.original() == raw and response.retained_sha256 == sha256(raw).hexdigest()
    assert "body_base64" not in repr(response)
    assert "response=" not in repr(saved(env, attempt))


def test_response_write_once_lost_ack_and_bound_request(env):
    _, attempt = started(env)
    before = env[1].state()
    def lost(_):
        raise OSError("test response commit acknowledgement lost")
    env[1].after_commit = lost
    with pytest.raises(OSError):
        record_wire(env[0], attempt)
    env[1].after_commit = lambda _: None
    assert record_wire(env[0], attempt) == saved(env, attempt)
    for change in [dict(raw=b'different'), dict(status_code=503), dict(complete=False)]:
        with pytest.raises(SharedDenied, match="conflict"):
            record_wire(env[0], attempt, **change)
    with pytest.raises(SharedDenied, match="unavailable"):
        env[0].record_response(attempt.id, "f" * 64, b'{}', status_code=200,
                               complete=True, observed_bytes=2)
    assert env[1].state() == before


def test_missing_and_unclaimed_attempt_evidence_denied(env):
    run = begin(env)
    attempt = reserve(env, run)
    with pytest.raises(SharedDenied, match="unavailable"):
        record_wire(env[0], attempt)
    with pytest.raises(SharedDenied):
        env[0].record_response("f" * 32, attempt.request_hash, b'', status_code=200,
                               complete=False, observed_bytes=0)
    claim(env, run, attempt)
    with pytest.raises(SharedDenied, match="usage"):
        env[0].reconcile(attempt.id)


def test_exact_response_limit_prefix_and_unknown_total(env):
    env = configure(env, max_response_bytes=len(wire_response()))
    _, attempt = started(env)
    record_wire(env[0], attempt)
    assert saved(env, attempt).response.complete
    second = reserve(env, env[0].inspect_run(env[4], attempt.run_id))
    claim(env, env[0].inspect_run(env[4], attempt.run_id), second)
    raw = wire_response() + b' '
    record_wire(env[0], second, raw)
    response = saved(env, second).response
    assert not response.complete and response.observed_bytes == len(raw)
    assert response.retained_bytes == len(raw) - 1
    assert response.retained_sha256 == sha256(raw[:-1]).hexdigest()
    before = env[1].state()
    with pytest.raises(ValueError, match="usage"):
        env[0].reconcile(second.id)
    assert env[1].state() == before


@pytest.mark.parametrize("raw", [b'not-json', b'\xff', b'[]', b'{}',
    b'{"usageMetadata":{},"usageMetadata":{}}',
    wire_response(-1), wire_response(True), wire_response(1.2), wire_response(None),
    wire_response().replace(b'150', b'151'),
    wire_response().replace(b'"thoughtsTokenCount": 0, ', b'').replace(b'150', b'151'),
    wire_response().replace(b'"totalTokenCount": 150', b'"totalTokenCount": NaN'),
    wire_response(extra=[[[[[[[[[[0]]]]]]]]]])])
def test_incomplete_or_invalid_usage_keeps_liability_private(env, raw):
    env = configure(env, max_json_depth=8)
    _, attempt = started(env)
    record_wire(env[0], attempt, raw)
    before = env[1].state()
    with pytest.raises(ValueError, match="complete usage unavailable") as exc:
        env[0].reconcile(attempt.id)
    assert exc.value.__context__ is None
    assert "usageMetadata" not in "".join(traceback.format_exception(exc.value))
    assert env[1].state() == before and saved(env, attempt).complete_usage is None


@pytest.mark.parametrize("field,value", [("cachedContentTokenCount", 1),
    ("toolUsePromptTokenCount", 1), ("cachedContentTokenCount", False),
    ("newBillableTokenCount", 1), ("trafficType", "PROVISIONED_THROUGHPUT"),
    ("promptTokensDetails", [{"modality": "TEXT", "tokenCount": 99}])])
def test_unsupported_or_inconsistent_billing_keeps_reservation(env, field, value):
    _, attempt = started(env)
    payload = json.loads(wire_response())
    payload["usageMetadata"][field] = value
    record_wire(env[0], attempt, json.dumps(payload).encode())
    before = env[1].state()
    with pytest.raises(ValueError, match="usage"):
        env[0].reconcile(attempt.id)
    assert env[1].state() == before


def test_full_metadata_saved_atomically_before_reduction_with_lost_ack(env):
    _, attempt = started(env)
    payload = json.loads(wire_response())
    payload["usageMetadata"].update({"promptTokensDetails": [
        {"modality": "TEXT", "tokenCount": 25}, {"modality": "IMAGE", "tokenCount": 75}],
        "trafficType": "ON_DEMAND", "cachedContentTokenCount": 0})
    record_wire(env[0], attempt, json.dumps(payload).encode())
    def lost(change):
        if change.attempt.complete_usage:
            assert change.attempt.response and change.attempt.usage_hash
            raise OSError("test reconcile ack lost")
    env[1].after_commit = lost
    with pytest.raises(OSError):
        env[0].reconcile(attempt.id)
    env[1].after_commit = lambda _: None
    committed = env[1].state()
    env[0].reconcile(attempt.id)
    assert env[1].state() == committed
    evidence = saved(env, attempt)
    assert json.loads(evidence.complete_usage.metadata_json) == payload["usageMetadata"]
    assert evidence.complete_usage.response_hash == evidence.response.retained_sha256
    assert evidence.complete_usage.request_hash == attempt.request_hash
    assert evidence.usage_hash == evidence.complete_usage.digest()


def test_late_original_limits_and_rate_apply_without_reopening(env):
    run, attempt = started(env)
    env[0].finish_run(env[4], run.id, failed=True)
    env[6][0] += timedelta(days=10)
    changed = env[0].policy.model_copy(update={"evidence_limits": AttemptEvidenceLimits(
        max_response_bytes=1)})
    cold = SharedAdmission(changed, env[0].grant, env[1], clock=env[0].clock)
    record_wire(cold, attempt)
    cold.reconcile(attempt.id)
    assert saved(env, attempt).response.complete
    assert saved(env, attempt).actual_nanos == attempt.price.cost_nanos(100, 50)
    with pytest.raises(SharedDenied, match="guest"):
        cold.inspect_attempt(env[4], run.id, attempt.id)


def test_attempt_record_limit_denies_without_losing_existing_raw(env):
    env = configure(env, max_response_bytes=256, max_attempt_record_bytes=2500)
    _, attempt = started(env)
    record_wire(env[0], attempt)
    before = env[1].state()
    # Tighten the historical fake attempt's allowance to its exact existing size.
    existing = saved(env, attempt)
    size = len(existing.model_dump_json().encode())
    limits = existing.evidence_limits.model_copy(update={"max_attempt_record_bytes": size})
    existing = existing.model_copy(update={"evidence_limits": limits})
    for _ in range(3):
        size = len(existing.model_dump_json().encode())
        existing = existing.model_copy(update={"evidence_limits": limits.model_copy(
            update={"max_attempt_record_bytes": size})})
    env[1].attempts[attempt.id] = existing.model_dump_json()
    with pytest.raises(SharedDenied, match="byte limit"):
        env[0].reconcile(attempt.id)
    assert env[1].state() == before and saved(env, attempt).response == existing.response


def test_response_canonical_base64_and_digest_validate(env):
    response = response_evidence(b'private', status_code=200, complete=True,
                                 observed_bytes=7, limits=AttemptEvidenceLimits())
    for changes in [{"body_base64": response.body_base64 + "\n"},
                    {"retained_bytes": 9}, {"retained_sha256": "f" * 64},
                    {"observed_bytes": 8}]:
        with pytest.raises(ValueError):
            type(response).model_validate({**response.model_dump(), **changes})
    assert InputManifest is type(binding(env).manifest)


def test_missing_established_attempt_cannot_spend_again(env):
    run, attempt = started(env)
    before = env[1].state()
    del env[1].attempts[attempt.id]
    with pytest.raises(SharedDenied, match="established attempt"):
        reserve(env, run, attempt_id=attempt.id)
    assert env[1].state() == before


@pytest.mark.parametrize("tokens,circuit", [(12001, "open_bound"),
                                          (10**30, "open_representation")])
def test_overbound_circuit_survives_expanded_record_size_failure(env, tokens, circuit):
    env = configure(env, max_response_bytes=256, max_attempt_record_bytes=1800)
    run, attempt = started(env)
    record_wire(env[0], attempt, wire_response(tokens, 1))
    before = env[1].state().balance(attempt.pool)
    with pytest.raises(SharedDenied, match="byte limit"):
        env[0].reconcile(attempt.id)
    assert env[1].state().circuit == circuit
    assert env[1].state().balance(attempt.pool) == before
    assert saved(env, attempt).response and saved(env, attempt).complete_usage is None
    with pytest.raises(SharedDenied, match="circuit"):
        reserve(env, run, operation_key="other")

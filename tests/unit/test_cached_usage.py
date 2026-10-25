"""Cached input remains part of full prompt valuation; no provider calls."""

import json

import httpx
import pytest

from batchbeacon.attempt_evidence import derive_usage, response_evidence
from tests.unit.test_durable_attempts import record_wire, saved, started, wire_response
from tests.unit.test_model_runtime import exercise, response
from tests.unit.test_model_runtime import runtime as runtime  # noqa: F401
from tests.unit.test_shared_admission import env as env  # noqa: F401


def cached_body():
    # Sanitized metadata shape from the retained failure, no provider content/IDs.
    return {'usageMetadata': {
        'promptTokenCount': 34616, 'candidatesTokenCount': 712, 'totalTokenCount': 35328,
        'cachedContentTokenCount': 28551, 'trafficType': 'ON_DEMAND',
        'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 33496},
                               {'modality': 'IMAGE', 'tokenCount': 1120}],
        'cacheTokensDetails': [{'modality': 'TEXT', 'tokenCount': 27628},
                              {'modality': 'IMAGE', 'tokenCount': 923}],
        'candidatesTokensDetails': [{'modality': 'TEXT', 'tokenCount': 712}],
    }}


def parse(body, env):
    limits = env[0].policy.evidence_limits
    raw = json.dumps(body).encode()
    receipt = response_evidence(raw, status_code=200, complete=True,
                                observed_bytes=len(raw), limits=limits)
    return derive_usage(receipt, 'a' * 64, limits)


def test_retained_cache_shape_preserves_full_prompt_and_metadata(env):
    body = cached_body()
    usage = parse(body, env)
    assert usage.input_tokens == 34616
    assert usage.output_and_thought_tokens == 712
    assert usage.total_tokens == 35328
    assert json.loads(usage.metadata_json) == body['usageMetadata']


@pytest.mark.parametrize('cached', [0, 1, 100])
def test_cached_subset_is_not_subtracted_or_added_to_price(env, cached):
    service, store = env[:2]
    _, attempt = started(env)
    payload = json.loads(wire_response())
    payload['usageMetadata']['cachedContentTokenCount'] = cached
    record_wire(service, attempt, json.dumps(payload).encode())
    service.reconcile(attempt.id)
    receipt = saved(env, attempt)
    assert receipt.actual_nanos == attempt.price.cost_nanos(100, 50)
    assert receipt.complete_usage.input_tokens == 100
    assert receipt.usage_hash == receipt.complete_usage.digest()
    before = store.state()
    service.reconcile(attempt.id)
    assert store.state() == before


@pytest.mark.parametrize('change', [
    {'cachedContentTokenCount': True}, {'cachedContentTokenCount': -1},
    {'cachedContentTokenCount': 34617}, {'cachedContentTokenCount': 1.0},
    {'cachedContentTokenCount': '28551'}, {'cachedContentTokenCount': None},
    {'cachedContentTokenCount': 0}, {'toolUsePromptTokenCount': 1},
    {'trafficType': 'PROVISIONED_THROUGHPUT'}, {'unknownBillingMeter': 1},
    {'totalTokenCount': 63879},
    {'cacheTokensDetails': [{'modality': 'TEXT', 'tokenCount': 27430},
                           {'modality': 'IMAGE', 'tokenCount': 1121}]},
    {'cacheTokensDetails': [{'modality': 'AUDIO', 'tokenCount': 28551}]},
    {'cacheTokensDetails': [{'modality': 'TEXT', 'tokenCount': 1},
                           {'modality': 'TEXT', 'tokenCount': 28550}]},
    {'cacheTokensDetails': [{'modality': 'TEXT', 'tokenCount': True}]},
    {'cacheTokensDetails': []},
    {'promptTokensDetails': [{'modality': 'TEXT', 'tokenCount': 34616}]},
])
def test_malformed_or_unsupported_cache_usage_preserves_unknown(env, change):
    _, attempt = started(env)
    body = cached_body()
    body['usageMetadata'].update(change)
    record_wire(env[0], attempt, json.dumps(body).encode())
    before = env[1].state()
    with pytest.raises(ValueError, match='complete usage unavailable'):
        env[0].reconcile(attempt.id)
    assert env[1].state() == before
    assert saved(env, attempt).actual_nanos is None


def test_cache_details_without_count_cannot_infer_usage(env):
    body = cached_body()
    del body['usageMetadata']['cachedContentTokenCount']
    with pytest.raises(ValueError):
        parse(body, env)


def test_cached_usage_lost_ack_replay_is_atomic(env):
    _, attempt = started(env)
    body = json.loads(wire_response())
    body['usageMetadata']['cachedContentTokenCount'] = 90
    record_wire(env[0], attempt, json.dumps(body).encode())

    def lost(change):
        if change.attempt.complete_usage:
            assert change.attempt.response and change.attempt.usage_hash
            raise OSError('synthetic lost acknowledgement')

    env[1].after_commit = lost
    with pytest.raises(OSError):
        env[0].reconcile(attempt.id)
    committed = env[1].state()
    env[1].after_commit = lambda _: None
    env[0].reconcile(attempt.id)
    assert env[1].state() == committed
    assert saved(env, attempt).actual_nanos == attempt.price.cost_nanos(100, 50)


def test_application_adk_accepts_cached_response_without_extra_dispatch(runtime):
    body = json.loads(response(runtime[5]))
    body['usageMetadata']['cachedContentTokenCount'] = 75
    raw = json.dumps(body).encode()

    async def handler(request):
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens': 100})
        return httpx.Response(200, content=raw)

    result, calls = exercise(runtime, handler=handler)
    attempt = runtime[1].inspect_attempt(runtime[2], runtime[3].id, result.attempt_id)
    assert result.candidate == json.dumps(runtime[5]).encode()
    assert attempt.response.original() == raw
    assert attempt.complete_usage.input_tokens == body['usageMetadata']['promptTokenCount']
    assert attempt.actual_nanos == attempt.price.cost_nanos(
        attempt.complete_usage.input_tokens, attempt.complete_usage.output_and_thought_tokens)
    assert len(calls) == 2  # One fake count and generation, no hidden retries.

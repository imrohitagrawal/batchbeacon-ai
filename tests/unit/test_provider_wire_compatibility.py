"""Vertex proto3 zero omission and opaque signature compatibility; no paid calls."""

import asyncio
import base64
import json

import httpx
import pytest

from batchbeacon.attempt_evidence import (
    AttemptEvidenceLimits,
    candidate_text,
    derive_usage,
    response_evidence,
)
from tests.unit.test_model_runtime import exercise as model_exercise
from tests.unit.test_model_runtime import response as model_response
from tests.unit.test_model_runtime import runtime as runtime  # noqa: F401
from tests.unit.test_probe_runner import exercise, response_body
from tests.unit.test_shared_admission import env as env  # noqa: F401


def usage(body):
    raw = json.dumps(body).encode()
    limits = AttemptEvidenceLimits()
    response = response_evidence(raw, status_code=200, complete=True,
                                 observed_bytes=len(raw), limits=limits)
    return derive_usage(response, 'a' * 64, limits)


def actual_shape():
    body = response_body()
    body['usageMetadata'] = {'promptTokenCount': 30390, 'candidatesTokenCount': 110,
        'totalTokenCount': 30500, 'trafficType': 'ON_DEMAND',
        'promptTokensDetails': [{'modality':'TEXT','tokenCount':29270},
                               {'modality':'IMAGE','tokenCount':1120}],
        'candidatesTokensDetails': [{'modality':'TEXT','tokenCount':110}]}
    body['candidates'][0]['content']['parts'][0]['thoughtSignature'] = base64.b64encode(
        b'synthetic opaque signature').decode()
    return body


def test_missing_implicit_thoughts_default_is_zero_only_with_exact_total():
    value = usage(actual_shape())
    assert value.input_tokens == 30390 and value.output_and_thought_tokens == 110
    assert value.thought_tokens == 0
    assert 'thoughtsTokenCount' not in value.metadata_json


@pytest.mark.parametrize('change', [
    {'totalTokenCount':30501}, {'thoughtsTokenCount':None}, {'thoughtsTokenCount':True},
    {'thoughtsTokenCount':'0'}, {'thoughtsTokenCount':-1}, {'toolUsePromptTokenCount':1},
    {'cachedContentTokenCount':30391}, {'unknownMeter':1},
])
def test_incomplete_or_unknown_usage_never_fills_residual_thoughts(change):
    body = actual_shape()
    body['usageMetadata'].update(change)
    with pytest.raises(ValueError, match='complete usage unavailable'):
        usage(body)


@pytest.mark.parametrize('part', [
    {'text':'{}','thoughtSignature':'not base64!'}, {'text':'{}','thoughtSignature':None},
    {'text':'{}','thoughtSignature':''}, {'text':'{}','thought':True},
    {'text':'{}','functionCall':{}}, {'text':'{}','unknown':0}, {'thoughtSignature':'YQ=='},
])
def test_only_valid_opaque_signature_can_accompany_visible_text(part):
    with pytest.raises(ValueError):
        candidate_text([part])


def test_operator_adk_reconciles_zero_thoughts_and_retains_signature(tmp_path):
    body = actual_shape()
    # Bound the synthetic test request under its existing synthetic cost policy.
    body['usageMetadata'] = {'promptTokenCount':16,'candidatesTokenCount':1,'totalTokenCount':17}
    result, calls, ledger = asyncio.run(exercise(tmp_path, generation=body))[:3]
    assert result['outcome'] == 'succeeded' and result['billing_outcome'] == 'reconciled'
    assert ledger.snapshot()['unknown_attempts'] == 0
    assert len(calls) == 2


def test_application_adk_preserves_signature_in_original_but_not_proposal(runtime):
    body = json.loads(model_response(runtime[5]))
    metadata = body['usageMetadata']
    metadata['totalTokenCount'] -= metadata.pop('thoughtsTokenCount')
    signature = base64.b64encode(b'synthetic opaque signature').decode()
    body['candidates'][0]['content']['parts'][0]['thoughtSignature'] = signature
    raw = json.dumps(body).encode()
    async def handler(request):
        if str(request.url).endswith(':countTokens'):
            return httpx.Response(200, json={'totalTokens':100})
        return httpx.Response(200, content=raw)
    result, calls = model_exercise(runtime, handler=handler)
    assert result.candidate == json.dumps(runtime[5]).encode()
    assert signature.encode() not in result.candidate
    attempt = runtime[1].inspect_attempt(runtime[2], runtime[3].id, result.attempt_id)
    assert attempt.response.original() == raw and attempt.usage_hash
    assert len(calls) == 2

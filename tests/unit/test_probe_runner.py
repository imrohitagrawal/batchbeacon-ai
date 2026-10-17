"""Real installed ADK/SDK pipeline; only synthetic HTTP and local ledgers."""

import asyncio
import base64
import json
import sqlite3
from datetime import timedelta
from hashlib import sha256
from io import BytesIO

import httpx
import pytest
from google.auth.credentials import AnonymousCredentials
from PIL import Image

from batchbeacon.operator_admission import AdmissionDenied
from batchbeacon.probe_runner import ProbeInput, ProbeRun
from tests.unit.test_cloud_admission import NOW, grant, make_ledger, policy


def payload():
    image = BytesIO()
    Image.new("RGB", (20, 20), "white").save(image, format="PNG")
    source = "Synthetic source title\nSynthetic notice body."
    return ProbeInput(
        source_text=source,
        source_sha256=sha256(source.encode()).hexdigest(),
        image_bytes=image.getvalue(),
        image_sha256=sha256(image.getvalue()).hexdigest(),
        image_mime_type="image/png",
    )


def response_body(**overrides):
    return dict(
        {
            "candidates": [
                {
                    "content": {
                        "role": "model",
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "observed_label_text": "Synthetic label",
                                        "source_title": "Synthetic source title",
                                    }
                                )
                            }
                        ],
                    },
                    "finishReason": "STOP",
                    "index": 0,
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 16,
                "candidatesTokenCount": 1,
                "thoughtsTokenCount": 2,
                "totalTokenCount": 19,
            },
            "modelVersion": "gemini-3.8-flash",
        },
        **overrides,
    )


def credentials():
    value = AnonymousCredentials()
    value.token = "synthetic-mock-token"
    return value


async def exercise(
    tmp_path,
    *,
    count=16,
    generation=None,
    raw_generation=None,
    count_status=200,
    generation_status=200,
    on_count=None,
    on_generate=None,
    p=None,
    clock=None,
):
    p = p or policy()
    ledger = make_ledger(tmp_path, p)
    item = payload()
    run = ProbeRun(ledger, "probe-1", item, tmp_path / "receipt.json", clock=clock or (lambda: NOW))
    requests = []

    async def fake(request):
        requests.append(request)
        if request.url.path.endswith(":countTokens"):
            if on_count:
                await on_count(run, request)
            return httpx.Response(count_status, json={"totalTokens": count})
        if on_generate:
            await on_generate(run, request)
        if raw_generation is not None:
            return httpx.Response(generation_status, content=raw_generation)
        return httpx.Response(
            generation_status, json=response_body() if generation is None else generation
        )

    receipt = await run.execute(transport=httpx.MockTransport(fake), credentials=credentials())
    return receipt, requests, ledger, run


def test_exact_wire_context_and_usage_are_bound_before_generation(tmp_path):
    def run_test():
        return asyncio.run(exercise(tmp_path))

    receipt, requests, ledger, run = run_test()
    assert receipt["outcome"] == "succeeded", receipt
    assert [r.url.path.rsplit(":", 1)[1] for r in requests] == ["countTokens", "generateContent"]
    counted, generated = [json.loads(r.content) for r in requests]
    assert counted == {
        k: generated[k] for k in ("contents", "systemInstruction", "generationConfig")
    }
    parts = generated["contents"][0]["parts"]
    assert parts[0]["text"] == run.payload.source_text
    assert base64.urlsafe_b64decode(parts[1]["inlineData"]["data"]) == run.payload.image_bytes
    assert "batchbeacon_probe" in json.dumps(generated["systemInstruction"])
    assert generated["generationConfig"]["responseJsonSchema"]["properties"]
    assert "candidateCount" not in generated["generationConfig"]
    assert receipt["request_sha256"] == sha256(requests[1].content).hexdigest()
    assert ledger.snapshot()["committed_nanos"] == run.policy.price.cost_nanos(16, 3)
    assert ledger.snapshot()["unknown_attempts"] == 0
    assert json.loads((tmp_path / "receipt.json").read_text()) == receipt


@pytest.mark.parametrize("count", [None, -1, 0, 12001, True, "16", 16.5])
def test_bad_count_never_reserves_or_dispatches(tmp_path, count):
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, count=count))
    assert receipt["outcome"] == "denied"
    assert len(requests) == 1
    assert ledger.snapshot()["attempts"] == 0


def test_count_threshold_is_inclusive(tmp_path):
    receipt, requests, _, _ = asyncio.run(exercise(tmp_path, count=12000))
    assert receipt["outcome"] == "succeeded"
    assert len(requests) == 2


@pytest.mark.parametrize("status", [429, 503])
def test_count_error_has_no_generation_or_reservation(tmp_path, status):
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, count_status=status))
    assert receipt["outcome"] == "denied"
    assert len(requests) == 1 and ledger.snapshot()["attempts"] == 0


@pytest.mark.parametrize("status", [429, 503])
def test_generation_error_is_one_reserved_unknown_attempt(tmp_path, status):
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, generation_status=status))
    assert receipt["outcome"] == "failed_unknown"
    assert len(requests) == 2 and ledger.snapshot()["unknown_attempts"] == 1
    assert ledger.snapshot()["committed_nanos"] == policy().reserve_nanos


@pytest.mark.parametrize("phase", ["count", "generate"])
def test_whole_run_timeout_keeps_only_started_liability(tmp_path, phase):
    async def delayed(*_):
        await asyncio.sleep(0.1)

    p = policy(request_timeout_ms=50, run_deadline_ms=50)
    options = {"on_" + phase: delayed}
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, p=p, **options))
    assert receipt["outcome"] == ("timeout" if phase == "count" else "timeout_unknown")
    assert len(requests) == (1 if phase == "count" else 2)
    assert ledger.snapshot()["attempts"] == (0 if phase == "count" else 1)


def test_expiry_while_counting_prevents_paid_dispatch(tmp_path):
    now = [NOW]

    async def expire(*_):
        now[0] = grant(policy()).expires_at

    receipt, requests, ledger, _ = asyncio.run(
        exercise(tmp_path, on_count=expire, clock=lambda: now[0])
    )
    assert receipt["outcome"] == "denied"
    assert len(requests) == 1 and ledger.snapshot()["attempts"] == 0


def test_expiry_while_reserving_keeps_reserve_without_dispatch(tmp_path):
    now = [NOW]

    async def delayed_reserve(run, _):
        original = run.ledger.reserve

        def reserve(*args, **kwargs):
            result = original(*args, **kwargs)
            now[0] += timedelta(days=3)
            return result

        run.ledger.reserve = reserve

    receipt, requests, ledger, _ = asyncio.run(
        exercise(
            tmp_path,
            on_count=delayed_reserve,
            clock=lambda: now[0],
        )
    )
    assert receipt["outcome"] == "failed_unknown" and not receipt["dispatch_intent"]
    assert len(requests) == 1 and ledger.snapshot()["unknown_attempts"] == 1


@pytest.mark.parametrize(
    "usage",
    [
        {},
        {"promptTokenCount": 16, "candidatesTokenCount": 1, "totalTokenCount": 19},
        {
            "promptTokenCount": 16,
            "candidatesTokenCount": 1,
            "thoughtsTokenCount": 2,
            "totalTokenCount": 18,
        },
        {
            "promptTokenCount": 16,
            "candidatesTokenCount": 1,
            "thoughtsTokenCount": 2,
            "totalTokenCount": 19,
            "cachedContentTokenCount": 2,
        },
    ],
)
def test_incomplete_or_unexpected_usage_never_releases_reserve(tmp_path, usage):
    receipt, _, ledger, _ = asyncio.run(
        exercise(tmp_path, generation=response_body(usageMetadata=usage))
    )
    assert receipt["outcome"] == "usage_unknown"
    assert ledger.snapshot()["unknown_attempts"] == 1
    assert ledger.snapshot()["committed_nanos"] == policy().reserve_nanos


@pytest.mark.parametrize("finish", ["CONTINUATION", "MAX_TOKENS", "SAFETY"])
def test_incomplete_output_is_failure_even_with_known_usage(tmp_path, finish):
    body = response_body()
    body["candidates"][0].update(finishReason=finish, continuationToken="c3ludGhldGlj")
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, generation=body))
    assert receipt["outcome"] == "invalid_output"
    assert len(requests) == 2 and ledger.snapshot()["unknown_attempts"] == 0


def test_output_schema_failure_still_reconciles_actual_usage(tmp_path):
    body = response_body()
    body["candidates"][0]["content"]["parts"] = [{"text": '{"unexpected":"field"}'}]
    receipt, _, ledger, _ = asyncio.run(exercise(tmp_path, generation=body))
    assert receipt["outcome"] == "invalid_output"
    assert ledger.snapshot()["committed_nanos"] == policy().price.cost_nanos(16, 3)
    raw = httpx.Response(200, json=body).content
    assert base64.b64decode(receipt["response_body_base64"]) == raw
    assert receipt["response_sha256"] == sha256(raw).hexdigest()
    assert json.loads((tmp_path / "receipt.json").read_text()) == receipt


def test_malformed_provider_json_is_retained_before_sdk_parsing(tmp_path):
    raw = b'{"candidates": [invalid synthetic response'
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, raw_generation=raw))
    assert receipt["outcome"] == "failed_unknown"
    assert len(requests) == 2
    assert base64.b64decode(receipt["response_body_base64"]) == raw
    assert receipt["response_sha256"] == sha256(raw).hexdigest()
    assert ledger.snapshot()["committed_nanos"] == policy().reserve_nanos
    assert ledger.snapshot()["unknown_attempts"] == 1


def test_final_partial_write_preserves_usage_evidence_and_closes_clients(tmp_path, monkeypatch):
    original_dump = json.dump
    observed = {}

    def fail_final(value, file, *args, **kwargs):
        if value.get("billing_outcome") == "reconciled":
            file.write('{"partial":')
            raise OSError("synthetic partial final write")
        return original_dump(value, file, *args, **kwargs)

    async def observe(run, _):
        observed["ledger"] = run.ledger
        client = run.client
        async_client = client.aio
        original_close, original_aclose = client.close, async_client.aclose

        def close():
            observed["closed"] = True
            original_close()

        async def aclose():
            observed["async_closed"] = True
            await original_aclose()

        monkeypatch.setattr(client, "close", close)
        monkeypatch.setattr(async_client, "aclose", aclose)

    monkeypatch.setattr(json, "dump", fail_final)
    with pytest.raises(OSError, match="partial final write"):
        asyncio.run(exercise(tmp_path, on_generate=observe))
    receipt_path = tmp_path / "receipt.json"
    durable = json.loads(receipt_path.read_text())
    assert durable["usage"] == response_body()["usageMetadata"]
    assert sha256(base64.b64decode(durable["response_body_base64"])).hexdigest() == durable[
        "response_sha256"
    ]
    ledger = observed["ledger"]
    with sqlite3.connect(ledger.path) as db:
        assert db.execute("SELECT usage_sha256 FROM attempt WHERE id='probe-1'").fetchone() == (
            durable["usage_sha256"],
        )
    assert ledger.snapshot()["committed_nanos"] == policy().price.cost_nanos(16, 3)
    assert ledger.snapshot()["unknown_attempts"] == 0
    assert receipt_path.stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob(".probe-*"))
    assert observed["closed"] and observed["async_closed"]


def test_expiry_during_intent_save_does_not_claim_observed_dispatch(tmp_path, monkeypatch):
    now = [NOW]
    original_save = ProbeRun._save

    def expire_after_intent(run):
        original_save(run)
        if run.record["dispatch_intent"]:
            now[0] = run.ledger.grant.expires_at

    monkeypatch.setattr(ProbeRun, "_save", expire_after_intent)
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, clock=lambda: now[0]))
    assert receipt["outcome"] == "failed_unknown"
    assert receipt["dispatch_intent"] is True and "dispatched" not in receipt
    assert "http_status" not in receipt and "response_sha256" not in receipt
    assert [r.url.path.rsplit(":", 1)[1] for r in requests] == ["countTokens"]
    assert ledger.snapshot()["unknown_attempts"] == 1
    assert ledger.snapshot()["committed_nanos"] == policy().reserve_nanos


@pytest.mark.parametrize("phase", ["count", "generate"])
@pytest.mark.parametrize("allow_exact_bytes", [True, False])
def test_response_byte_limits_reach_wire_consumer(tmp_path, phase, allow_exact_bytes):
    body = {"totalTokens": 16} if phase == "count" else response_body()
    size = len(httpx.Response(200, json=body).content)
    key = "max_count_response_bytes" if phase == "count" else "max_response_bytes"
    p = policy(**{key: size if allow_exact_bytes else size - 1})
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, p=p))
    if allow_exact_bytes:
        assert receipt["outcome"] == "succeeded" and len(requests) == 2
    else:
        assert receipt["outcome"] == ("denied" if phase == "count" else "failed_unknown")
        assert len(requests) == (1 if phase == "count" else 2)
        assert ledger.snapshot()["unknown_attempts"] == (0 if phase == "count" else 1)


def test_single_use_and_restart_do_not_repeat_paid_dispatch(tmp_path):
    async def check():
        receipt, _, ledger, run = await exercise(tmp_path)
        with pytest.raises(AdmissionDenied):
            await run.execute()
        requests = []

        def fake(request):
            requests.append(request)
            return httpx.Response(200, json={"totalTokens": 16})

        second = ProbeRun(ledger, "probe-1", payload(), tmp_path / "second.json", clock=lambda: NOW)
        result = await second.execute(
            transport=httpx.MockTransport(fake), credentials=credentials()
        )
        assert result["outcome"] == "denied"
        assert len(requests) == 1 and ledger.snapshot()["attempts"] == 1
        return receipt

    assert asyncio.run(check())["outcome"] == "succeeded"


def test_count_and_generation_share_one_deadline(tmp_path):
    async def delayed(*_):
        await asyncio.sleep(0.06)

    p = policy(request_timeout_ms=100, run_deadline_ms=100)
    receipt, requests, ledger, _ = asyncio.run(
        exercise(
            tmp_path,
            p=p,
            on_count=delayed,
            on_generate=delayed,
        )
    )
    assert receipt["outcome"] == "timeout_unknown"
    assert len(requests) == 2 and ledger.snapshot()["unknown_attempts"] == 1


def test_cancellation_after_dispatch_persists_unknown_receipt(tmp_path):
    async def check():
        started = asyncio.Event()

        async def cancel(*_):
            started.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(exercise(tmp_path, on_generate=cancel))
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(check())
    receipt = json.loads((tmp_path / "receipt.json").read_text())
    assert receipt["outcome"] == "cancelled_unknown" and receipt["reserved"]


def test_changed_pending_generation_cannot_escape_count_binding(tmp_path, monkeypatch):
    original = ProbeRun._request
    parked = []

    async def track(self, request):
        if request.url.path.endswith(":generateContent"):
            parked.append(request)
        await original(self, request)

    monkeypatch.setattr(ProbeRun, "_request", track)

    async def mutate(*_):
        parked[0].url = httpx.URL("https://invalid.example/generateContent")

    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, on_count=mutate))
    assert receipt["outcome"] == "denied"
    assert len(requests) == 1 and ledger.snapshot()["attempts"] == 0


def test_hook_denies_unexpected_sdk_continuation(tmp_path, monkeypatch):
    original = type(policy()).generation_config

    def faulty_config(self):
        value = original(self)
        value.automatic_continuation = True  # Simulate an accidental SDK regression.
        return value

    monkeypatch.setattr(type(policy()), "generation_config", faulty_config)
    body = response_body()
    body["candidates"][0].update(finishReason="CONTINUATION", continuationToken="c3ludGhldGlj")
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, generation=body))
    assert receipt["outcome"] == "failed_unknown"
    assert len(requests) == 2 and ledger.snapshot()["unknown_attempts"] == 1


def test_reported_bound_overrun_opens_circuit(tmp_path):
    usage = {
        "promptTokenCount": 12001,
        "candidatesTokenCount": 1,
        "thoughtsTokenCount": 2,
        "totalTokenCount": 12004,
    }
    receipt, _, ledger, _ = asyncio.run(
        exercise(tmp_path, generation=response_body(usageMetadata=usage))
    )
    assert receipt["outcome"] == "billing_bound_exceeded"
    assert ledger.snapshot()["circuit_open"]


def test_count_threshold_and_billable_bound_are_distinct(tmp_path):
    p = policy(max_input_tokens=100, billable_input_token_bound=12000)
    usage = {
        "promptTokenCount": 200,
        "candidatesTokenCount": 1,
        "thoughtsTokenCount": 2,
        "totalTokenCount": 203,
    }
    receipt, _, ledger, _ = asyncio.run(
        exercise(
            tmp_path,
            p=p,
            count=100,
            generation=response_body(usageMetadata=usage),
        )
    )
    assert receipt["outcome"] == "succeeded"
    assert not ledger.snapshot()["circuit_open"]
    assert ledger.snapshot()["committed_nanos"] == p.price.cost_nanos(200, 3)


@pytest.mark.parametrize(
    "override",
    [
        {"max_source_bytes": 1},
        {"max_image_bytes": 1},
        {"max_image_pixels": 1},
    ],
)
def test_payload_policy_overrides_reach_consumer_before_network(tmp_path, override):
    receipt, requests, ledger, _ = asyncio.run(exercise(tmp_path, p=policy(**override)))
    assert receipt["outcome"] == "denied"
    assert not requests and ledger.snapshot()["attempts"] == 0

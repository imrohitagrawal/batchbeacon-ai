"""Installed ADK -> GenAI -> mock HTTP; no real provider or credential use."""

import asyncio
import json

import httpx
import pytest
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.auth.credentials import AnonymousCredentials
from google.genai import types

from tests.unit.test_cloud_admission import policy


async def exercise(status):
    p = policy(request_timeout_ms=7000, run_deadline_ms=8000, max_output_tokens=1024)
    requests = []

    def fake_provider(request):
        requests.append(request)
        if status != 200:
            return httpx.Response(status, json={
                "error": {"code": status, "message": "synthetic provider failure"},
            })
        return httpx.Response(200, json={
            "candidates": [{"content": {"role": "model", "parts": [{"text": "probe"}]},
                            "finishReason": "STOP", "index": 0}],
            "usageMetadata": {"promptTokenCount": 16, "candidatesTokenCount": 1,
                              "thoughtsTokenCount": 2, "totalTokenCount": 19},
            "modelVersion": p.model_id,
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(fake_provider)) as transport:
        options = p.client_options()
        options["http_options"].httpx_async_client = transport
        credentials = AnonymousCredentials()
        credentials.token = "synthetic-mock-token"
        client = genai.Client(credentials=credentials, **options)
        sessions = InMemorySessionService()
        agent = LlmAgent(
            name="batchbeacon_probe", model=Gemini(model=p.model_id, client=client),
            instruction="Return one synthetic probe word. No tools.",
            generate_content_config=p.generation_config(), tools=[],
        )
        runner = Runner(app_name="batchbeacon_probe", agent=agent, session_service=sessions)
        await sessions.create_session(app_name="batchbeacon_probe", user_id="synthetic",
                                      session_id="probe")
        events = []
        error = None
        try:
            async with asyncio.timeout(p.run_deadline_ms / 1000):
                async for event in runner.run_async(
                    user_id="synthetic", session_id="probe",
                    new_message=types.Content(role="user", parts=[types.Part(text="probe")]),
                    run_config=p.run_config(),
                ):
                    events.append(event)
        except Exception as failure:
            error = failure
        finally:
            await client.aio.aclose()
            client.close()
    return p, requests, events, error


def test_effective_adk_http_request_uses_configured_project_model_and_limits():
    p, requests, events, error = asyncio.run(exercise(200))
    assert error is None
    assert len(requests) == 1
    request = requests[0]
    assert request.url.host == "aiplatform.googleapis.com"
    endpoint = f"/projects/{p.project_id}/locations/global/publishers/google/models/{p.model_id}"
    assert endpoint in str(request.url)
    body = json.loads(request.content)
    generation = body["generationConfig"]
    assert generation["candidateCount"] == 1
    assert generation["maxOutputTokens"] == 1024
    # Installed GenAI 2.31 serializes this nested field using its proto name.
    assert generation["thinkingConfig"]["thinking_level"] == "LOW"
    assert request.extensions["timeout"]["read"] == 7.0
    assert not body.get("tools") and not body.get("cachedContent")
    assert body["contents"] and body["systemInstruction"]
    assert events[-1].usage_metadata.total_token_count == 19


@pytest.mark.parametrize("status", [429, 503])
def test_transient_http_error_does_not_multiply_reserved_attempt(status):
    _, requests, _, error = asyncio.run(exercise(status))
    assert error is not None
    assert len(requests) == 1

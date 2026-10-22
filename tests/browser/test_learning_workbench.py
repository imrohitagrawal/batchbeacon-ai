"""Guidance browser loop over owned fake SDK state and actual pure evaluation."""

import os
import socket
import threading
import time
from datetime import timedelta

import pytest
import uvicorn
from playwright.sync_api import expect, sync_playwright

from batchbeacon.evidence_service import replace
from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.guest_service import GuestService
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.workbench import create_workbench_test_app
from tests.unit.test_firestore_store import setup as setup_factory
from tests.unit.test_learning_service import learning as learning_factory
from tests.unit.test_shared_admission import env as env_factory

pytestmark = pytest.mark.browser


@pytest.fixture
def learning_browser():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    setup, env = setup_factory.__wrapped__(), env_factory.__wrapped__()
    stores, server, guest, evidence, actions, now = setup
    gp = replace(guest.policy, origin=origin, mode="local_test")
    stores.guest_policy = gp
    guest = GuestService(gp, stores.guests, guest.objects, clock=lambda: now[0])
    setup = stores, server, guest, evidence, actions, now
    env[0].policy = replace(env[0].policy, guest_policy_hash=gp.digest())
    c, learning = learning_factory.__wrapped__(setup, env)
    app = create_workbench_test_app(
        c[0],
        c[8],
        RetailRefresh(stores.retail, RefreshPolicy()),
        ExtractionHTTPPolicy(),
        learning=learning,
    )
    runner = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=runner.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not runner.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert runner.started
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel=os.environ.get("BATCHBEACON_TEST_BROWSER_CHANNEL") or None
        )
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        context.add_cookies(
            [
                {
                    "name": gp.cookie_name,
                    "value": c[2],
                    "url": origin,
                    "httpOnly": True,
                    "sameSite": "Strict",
                }
            ]
        )
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(origin + "/?incident=" + c[1].incident_id)
            expect(page.locator("#verdict-title")).to_have_text("Review required")
            yield page, c, learning, errors
        finally:
            context.close()
            browser.close()
            runner.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive()


def test_owned_guidance_browser_evaluation_activation_effect_rollback_and_reload(learning_browser):
    page, c, learning, errors = learning_browser
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    if capture_dir := os.environ.get("BATCHBEACON_CAPTURE_DIR"):
        from pathlib import Path

        Path(capture_dir).mkdir(parents=True, exist_ok=True)
        page.screenshot(
            path=str(Path(capture_dir) / "guidance-eligible-desktop.png"), full_page=True
        )
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).to_contain_text("leading zeros")
    page.locator("#feedback-save").click()
    expect(page.locator("#learning-counts")).to_contain_text("1/40 feedback")
    page.locator("#candidate-create").click()
    expect(page.locator("#candidate-state")).to_contain_text("CANDIDATE READY")
    page.locator("#candidate-evaluate").click()
    expect(page.locator("#candidate-state")).to_contain_text("Attempt 1: PASSED")
    page.locator("#learning-activate").click()
    expect(page.locator("#learning-dialog")).to_be_visible()
    expect(page.locator("#learning-confirm")).to_be_disabled()
    expect(page.locator("#learning-preview")).to_contain_text("avoid glare")
    page.locator("#learning-consent").check()
    page.locator("#learning-confirm").click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 2")
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).to_contain_text("avoid glare")
    page.locator("#learning-rollback").click()
    expect(page.locator("#learning-confirm")).to_be_disabled()
    page.locator("#learning-consent").check()
    page.locator("#learning-confirm").click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 3")
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).not_to_contain_text("glare")
    c[3][5][0] += timedelta(seconds=learning.policy.refresh_interval_seconds)
    page.reload()
    expect(page.locator("#verdict-title")).to_have_text("Review required")
    expect(page.locator("#check")).to_be_enabled()
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 3")
    expect(page.locator("#learning-counts")).to_contain_text("1/4 actual attempts")
    for width in (390, 1440):
        page.set_viewport_size({"width": width, "height": 1000})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert len(c[4]) == 2 and not errors


def test_learning_lost_feedback_response_reconciles_original_key_after_reload(learning_browser):
    page, c, learning, errors = learning_browser
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).to_contain_text("leading zeros")

    def lost(route):
        response = route.fetch()
        assert response.status == 200
        route.abort("failed")

    page.route("**/api/incidents/*/feedback?*", lost, times=1)
    page.locator("#feedback-save").click()
    expect(page.locator("#learning-recover")).to_be_enabled()
    assert len(learning.read(c[2]).feedback) == 1
    c[3][5][0] += timedelta(seconds=learning.policy.refresh_interval_seconds)
    page.reload()
    expect(page.locator("#verdict-title")).to_have_text("Review required")
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#feedback-save")).to_be_disabled()
    page.locator("#learning-recover").click()
    expect(page.locator("#learning-counts")).to_contain_text("1/40 feedback")
    expect(page.locator("#feedback-save")).to_be_enabled()
    assert len(learning.read(c[2]).feedback) == 1
    assert page.evaluate("sessionStorage.getItem('bb_pending')") is None
    assert len(c[4]) == 2 and not errors


def test_old_saved_request_does_not_replace_current_capture_guidance_after_correction(
    learning_browser,
):
    from tests.unit.domain_fixtures import known

    page, c, learning, errors = learning_browser
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).to_contain_text("leading zeros")
    prior = learning.read(c[2]).requests[-1]
    before = c[7].read_evidence(c[2], c[1].incident_id)
    c[7].correct(
        c[2],
        c[1].incident_id,
        "independent-correction",
        before.observation.revision,
        "LOT",
        known("232511", evidence=before.observation.captures[0]),
    )
    binding = c[7].verification_binding(c[2], c[1].incident_id)
    c[0].shared.reserve_verification(
        c[6].capability_hash, c[1].incident_id, "independent-reverify", binding
    )
    c[7].publish_verification(c[2], c[1].incident_id, "independent-reverify", binding)
    now = c[7].read_evidence(c[2], c[1].incident_id)
    assert now.current and now.result.outstanding_fields == ()
    c[3][5][0] += timedelta(seconds=learning.policy.refresh_interval_seconds)
    page.reload()
    expect(page.locator("#verdict-title")).to_have_text("Matches this recall")
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator("#owned-guidance")).to_contain_text("Saved under")
    assert page.locator("#capture-instruction").text_content() != prior.instructions[0].text
    assert not errors


def test_refresh_reports_completion_and_preserves_failures(learning_browser):
    page, c, learning, errors = learning_browser
    page.locator("nav [data-view=guidance]").click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    c[3][5][0] += timedelta(seconds=learning.policy.refresh_interval_seconds)
    requests = []
    page.on("request", lambda r: requests.append((r.method, r.url)))
    page.locator("#learning-refresh").click()
    expect(page.locator("#app-status")).to_have_text("Capture guidance records refreshed.")
    assert len(requests) == 1 and requests[0][0] == "GET"
    assert "/api/learning?incident=" in requests[0][1]
    page.route(
        "**/api/learning?*",
        lambda route: route.fulfill(status=503, json={"error": "evidence_temporarily_unavailable"}),
    )
    page.locator("#learning-refresh").click()
    expect(page.locator("#app-status")).to_have_text("evidence temporarily unavailable")
    expect(page.locator("#learning-counts")).to_contain_text("historical")
    assert not errors

"""Complete source-review UI on local real HTTP, SDK/fake RPC; no source/model truth."""

import os
import socket
import threading
import time
from datetime import timedelta
from pathlib import Path

import pytest
import uvicorn
from google.api_core import exceptions
from playwright.sync_api import expect, sync_playwright

from batchbeacon.evidence_service import replace
from batchbeacon.extraction_api import ExtractionHTTPPolicy
from batchbeacon.guest_service import GuestService
from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.source_service import SourceService
from batchbeacon.workbench import create_workbench_test_app
from tests.unit.test_firestore_store import setup as setup_factory
from tests.unit.test_reviewed_extraction import build_reviewed
from tests.unit.test_shared_admission import env as env_factory
from tests.unit.test_source_runtime import source_service

pytestmark = pytest.mark.browser


@pytest.fixture
def source_browser():
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
    c = build_reviewed(
        setup,
        env,
        (0,),
        configure=lambda s, a, shared: s.enable_retail(
            RetailProjector(a, shared.policy, RetailReadPolicy())
        ),
    )
    source_service(setup)  # Configured source only, no extra retail writer.
    source = SourceService(c[7], stores)
    app = create_workbench_test_app(
        c[0],
        c[8],
        RetailRefresh(stores.retail, RefreshPolicy()),
        ExtractionHTTPPolicy(),
        source=source,
    )
    runner = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    thread = threading.Thread(target=runner.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not runner.started and time.monotonic() < deadline:
        time.sleep(0.02)
    assert runner.started
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            channel=os.environ.get("BATCHBEACON_TEST_BROWSER_CHANNEL") or None
        )
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        try:
            page.goto(origin)
            page.locator("#source-review summary").click()
            expect(page.locator("#source-start")).to_be_enabled()
            yield page, c, source, context, errors
        finally:
            context.close()
            browser.close()
            runner.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive()


def owner(page, c, context):
    guest = c[3][2]
    token = next(
        row["value"] for row in context.cookies() if row["name"] == guest.policy.cookie_name
    )
    return token, guest.resolve(token)


@pytest.mark.parametrize("width", [390, 1440])
def test_complete_empty_original_forward_reopen_reload_keyboard_source_journey(
    source_browser, width
):
    page, c, service, context, errors = source_browser
    page.set_viewport_size({"width": width, "height": 1000})
    expect(page.locator("#source-pair")).to_contain_text("England, Northern Ireland")
    expect(page.locator("#source-pair")).to_contain_text("Wales, Scotland")
    page.locator("#source-start").focus()
    page.keyboard.press("Enter")
    expect(page.locator("#source-status")).to_contain_text("Original UK notice selected")
    expect(page.locator("#source-status")).to_be_focused()
    expect(page.locator("#source-summary")).to_contain_text("original")
    expect(page.locator("#source-summary")).to_contain_text("GB-ENG")
    expect(page.locator("#source-apply")).to_be_enabled()
    assert page.locator("#capture-images img").count() == 0
    assert page.evaluate("state.evidence.result") is None
    expect(page.locator("#check")).to_be_disabled()
    expect(page.locator("#confirm-open")).to_be_disabled()
    before = page.evaluate("state.incident")
    page.locator("#source-apply").click()
    expect(page.locator("#source-status")).to_contain_text("Newer notice selected")
    expect(page.locator("#source-status")).to_contain_text("selection v2")
    expect(page.locator("#source-summary")).to_contain_text("GB-SCT")
    expect(page.locator("#source-apply")).to_be_disabled()
    page.reload()
    expect(page.locator("#source-summary")).to_contain_text("update")
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#queue-rows")).to_contain_text("Needs a label")
    page.locator("#queue-rows a").click()
    expect(page.locator("#source-summary")).to_contain_text("update")
    page.locator("#source-review summary").click()
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("Saved source confirmed")
    token, session = owner(page, c, context)
    assert len(session.incidents) == 1 and session.incidents[0].id == before
    assert service.read(token, before)["selection_revision"] == 2
    assert not c[4] and not errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    capture = os.environ.get("BATCHBEACON_SOURCE_WRITER_CAPTURES")
    if capture:
        destination = Path(capture)
        destination.mkdir(exist_ok=True, parents=True)
        page.screenshot(path=str(destination / f"source-writer-{width}.png"), full_page=True)


@pytest.mark.parametrize("lost_phase", ["create", "select", "response"])
def test_start_unknown_recovery_keeps_original_keys_through_reload(source_browser, lost_phase):
    page, c, service, context, errors = source_browser
    stores, server, *_ = c[3]
    if lost_phase == "response":

        def lost(route):
            response = route.fetch()
            assert response.ok
            route.abort()

        page.route("**/api/source-reviews", lost, times=1)
    else:

        def lost(request):
            names = [w.update.name for w in request.writes]
            payloads = [w.update.fields["payload"].string_value for w in request.writes]
            if (
                any("source_selection" in p for p in payloads)
                if lost_phase == "select"
                else any("/guest-" in name for name in names)
            ):
                raise exceptions.DeadlineExceeded("controlled lost ack")

        server.after_commit = lost
    page.locator("#source-start").click()
    expect(page.locator("#source-recheck")).to_be_visible()
    expect(page.locator("#source-status")).not_to_contain_text("Creating the separate")
    key = page.evaluate("state.sourcePending.operation")
    assert key
    server.after_commit = lambda request: None
    page.reload()
    expect(page.locator("#source-review")).to_have_attribute("open", "")
    expect(page.locator("#source-status")).to_contain_text("needs reconciliation")
    assert page.evaluate("state.sourcePending.operation") == key
    page.locator("#source-recheck").click()
    if lost_phase == "create":
        expect(page.locator("#source-status")).to_contain_text("empty investigation was created")
        expect(page.locator("#source-continue")).to_be_visible()
        assert page.evaluate("state.sourcePending.operation") == key
        page.locator("#source-continue").click()
        expect(page.locator("#source-status")).to_contain_text("Original UK notice selected")
    else:
        expect(page.locator("#source-status")).to_contain_text("Saved source confirmed")
    token, session = owner(page, c, context)
    assert len(session.incidents) == 1
    assert service.reconcile_start(token, key)["start_state"] == "SOURCE_SELECTED"
    assert page.evaluate("sessionStorage.getItem('bb_source_pending')") is None
    assert not c[4] and not errors


def test_forward_lost_response_reconcile_does_not_repeat_or_restore_original(source_browser):
    page, c, service, context, errors = source_browser
    page.locator("#source-start").click()
    expect(page.locator("#source-apply")).to_be_enabled()
    incident = page.evaluate("state.incident")

    def lost(route):
        response = route.fetch()
        assert response.ok
        route.abort()

    page.route(f"**/api/incidents/{incident}/source", lost, times=1)
    page.locator("#source-apply").click()
    expect(page.locator("#source-recheck")).to_be_visible()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    key = page.evaluate("state.sourcePending.operation")
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("selection v2")
    token, _ = owner(page, c, context)
    assert service.read(token, incident, key)["selected_choice"] == "uk-update"
    assert not c[4] and not errors


def test_new_owner_cannot_restore_pending_source_request(source_browser):
    page, c, service, context, errors = source_browser
    page.route("**/api/source-reviews", lambda route: route.abort(), times=1)
    page.locator("#source-start").click()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    old = page.evaluate("state.sourcePending.session_reference")
    context.clear_cookies()
    page.reload()
    expect(page.locator("#source-status")).to_contain_text("not transferred or repeated")
    assert page.evaluate("state.sourcePending") is None
    assert page.evaluate("state.sourceContext.session_reference") != old
    _, session = owner(page, c, context)
    assert not session.incidents and not c[4] and not errors


def test_immediate_expiry_clears_source_controls_pending_and_data(source_browser):
    page, c, service, context, errors = source_browser
    page.locator("#source-start").click()
    expect(page.locator("#source-apply")).to_be_enabled()
    token, session = owner(page, c, context)
    c[3][5][0] = session.scope.expires_at + timedelta(seconds=1)
    page.locator("#source-recheck").click()
    expect(page.locator("#session-state")).to_have_text("Guest access expired")
    expect(page.locator("#source-start")).to_be_disabled()
    assert page.evaluate("state.sourceContext") is None
    assert page.evaluate("state.evidence") is None
    assert not c[4] and not errors


def test_pending_context_read_failure_has_get_recovery_without_replay(source_browser):
    page, c, service, context, errors = source_browser
    page.route("**/api/source-reviews", lambda route: route.abort(), times=1)
    page.locator("#source-start").click()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    key = page.evaluate("state.sourcePending.operation")
    page.route(
        "**/api/source-reviews/context",
        lambda route: route.fulfill(
            status=503,
            content_type="application/json",
            body='{"error":"controlled_context_unavailable"}',
        ),
    )
    page.reload()
    expect(page.locator("#source-status")).to_contain_text("verify access")
    expect(page.locator("#source-recheck")).to_be_visible()
    expect(page.locator("#source-continue")).to_be_hidden()
    assert page.evaluate("state.sourceOwnershipUnknown") is True
    assert page.evaluate("state.sourcePending.operation") == key
    page.unroute("**/api/source-reviews/context")
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("not recorded")
    expect(page.locator("#source-continue")).to_be_visible()
    page.locator("#source-continue").click()
    expect(page.locator("#source-status")).to_contain_text("Original UK notice selected")
    _, session = owner(page, c, context)
    assert len(session.incidents) == 1 and not c[4] and not errors


def test_unrelated_label_work_preserves_source_pending_and_original_reconciliation(source_browser):
    page, c, service, context, errors = source_browser

    def lost(route):
        response = route.fetch()
        assert response.ok
        route.abort()

    page.route("**/api/source-reviews", lost, times=1)
    page.locator("#source-start").click()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    key = page.evaluate("state.sourcePending.operation")
    page.locator("#start-sample").click()
    expect(page.locator("#capture-images img")).to_have_count(1)
    assert page.evaluate("state.sourcePending.operation") == key
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("Saved source confirmed: uk-original")
    expect(page.locator("#capture-images img")).to_have_count(0)
    token, session = owner(page, c, context)
    assert len(session.incidents) == 2
    assert service.reconcile_start(token, key)["start_state"] == "SOURCE_SELECTED"
    assert not c[4] and not errors


def test_delayed_source_context_navigation_does_not_claim_unread_evidence(source_browser):
    page, c, service, context, errors = source_browser

    def lost(route):
        assert route.fetch().ok
        route.abort()

    page.route("**/api/source-reviews", lost, times=1)
    page.locator("#source-start").click()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    deferred = []
    page.route("**/api/source-reviews/context", lambda route: deferred.append(route), times=1)
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("Checking the saved")
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#queue-rows [role=listitem]")).to_have_count(1)
    deferred[0].continue_()
    expect(page.locator("#source-status")).not_to_contain_text("Checking the saved")
    assert "read again" not in page.locator("#source-status").text_content()
    assert page.evaluate("state.view") == "retail"
    assert page.evaluate("state.incident") is None
    assert not c[4] and not errors


def test_partial_source_start_survives_replay_disabled_rollback_and_same_key_restore(
    source_browser,
):
    page, c, service, context, errors = source_browser
    stores, server, *_ = c[3]

    def lost(request):
        if any("/guest-" in w.update.name for w in request.writes):
            raise exceptions.DeadlineExceeded("controlled create ack loss")

    server.after_commit = lost
    page.locator("#source-start").click()
    expect(page.locator("#source-status")).to_contain_text("unknown")
    key = page.evaluate("state.sourcePending.operation")
    server.after_commit = lambda request: None
    active = stores.source_runtime
    stores.source_runtime = replace(active, replay_enabled=False)
    page.reload()
    expect(page.locator("#source-availability")).to_contain_text("temporarily unavailable")
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("empty investigation was created")
    expect(page.locator("#source-continue")).to_be_disabled()
    assert page.evaluate("state.sourcePending.operation") == key
    stores.source_runtime = active
    page.locator("#source-recheck").click()
    expect(page.locator("#source-continue")).to_be_enabled()
    page.locator("#source-continue").click()
    expect(page.locator("#source-status")).to_contain_text("Original UK notice selected")
    _, session = owner(page, c, context)
    assert len(session.incidents) == 1 and not errors and not c[4]


def test_authenticated_inactive_race_keeps_original_pending_key_for_restore(source_browser):
    page, c, service, context, errors = source_browser
    stores = c[3][0]
    active = stores.source_runtime

    def disable(route):
        stores.source_runtime = replace(active, replay_enabled=False)
        route.continue_()

    page.route("**/api/source-reviews", disable, times=1)
    page.locator("#source-start").click()
    expect(page.locator("#source-availability")).to_contain_text("temporarily unavailable")
    key = page.evaluate("state.sourcePending.operation")
    assert key and page.evaluate("sessionStorage.getItem('bb_source_pending')")
    stores.source_runtime = active
    page.locator("#source-recheck").click()
    expect(page.locator("#source-status")).to_contain_text("not recorded")
    page.locator("#source-continue").click()
    expect(page.locator("#source-status")).to_contain_text("Original UK notice selected")
    token, session = owner(page, c, context)
    assert (
        len(session.incidents) == 1
        and service.reconcile_start(token, key)["start_state"] == "SOURCE_SELECTED"
    )
    assert not errors and not c[4]

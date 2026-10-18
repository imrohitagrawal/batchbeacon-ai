"""Admission failure stays distinct from expiry on every public view."""

# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("error, message", [
    ("demo_guest_capacity_unavailable", "Guest access is currently unavailable"),
    ("guest_creation_rate_limited", "Several visitors are opening guest shops"),
])
def test_failed_admission_does_not_call_protected_views(connected_browser, width, error, message):
    page, _, _, errors = connected_browser
    page.set_viewport_size({"width": width, "height": 844})
    page.context.clear_cookies()
    config = page.request.get(page.url.rstrip("/") + "/api/workbench/config").json()
    config["guidance"] = "OWNED_LIFECYCLE_CONNECTED"
    page.route("**/api/workbench/config", lambda route: route.fulfill(json=config))
    page.route("**/api/guest", lambda route: route.fulfill(status=429, json={"error": error}))
    protected = []
    page.on("request", lambda r: protected.append(r.url)
        if "/api/retail/" in r.url or "/api/learning" in r.url else None)
    page.reload()
    expect(page.locator("#app-status")).to_contain_text(message)
    for view in ("retail", "guidance", "workbench"):
        page.locator(f"nav [data-view={view}]").click()
        expect(page.locator("#app-status")).to_contain_text(message)
        expect(page.locator("#app-status")).not_to_contain_text("expired")
    for control in ("queue-filter", "refresh-queue", "learning-refresh", "start-sample"):
        expect(page.locator(f"#{control}")).to_be_disabled()
    page.locator("#tour-open").click()
    expect(page.locator("#tour-dialog")).to_be_visible()
    assert protected == [] and not errors


def test_navigation_during_admission_loads_selected_view_after_success(connected_browser):
    page, _, _, errors = connected_browser
    held = []
    page.route("**/api/guest", lambda route: held.append(route))
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("#example-cards input")).to_have_count(3)
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#refresh-queue")).to_be_disabled()
    assert len(held) == 1
    held[0].continue_()
    expect(page.locator("#queue-status")).to_contain_text("Manual refresh complete")
    expect(page.locator("#refresh-queue")).to_be_enabled()
    assert not errors


@pytest.mark.parametrize("timezone, date, clock, zone", [
    ("Asia/Kolkata", "20 Oct 2026", "03:39", "GMT+5:30"),
    ("UTC", "19 Oct 2026", "22:09", "UTC"),
])
def test_guest_expiry_is_a_dated_local_time_not_a_countdown(
    connected_browser, timezone, date, clock, zone
):
    original, _, _, errors = connected_browser
    context = original.context.browser.new_context(locale="en-GB", timezone_id=timezone)
    page = context.new_page()
    try:
        def session(route):
            response = route.fetch()
            data = response.json()
            data["expires_at"] = "2026-10-19T22:09:07+00:00"
            route.fulfill(response=response, json=data)
        page.route("**/api/guest", session)
        page.goto(original.url)
        expect(page.locator("#start-sample")).to_be_enabled()
        label = page.locator("#session-state")
        for value in ("Guest shop · expires", date, clock, zone):
            expect(label).to_contain_text(value)
        assert not errors
    finally:
        context.close()

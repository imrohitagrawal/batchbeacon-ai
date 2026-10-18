"""Local-only tutorial checks; no cloud/model acceptance."""

# ruff: noqa: F811
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


def test_tour_keyboard_reflow_and_no_requests(connected_browser):
    page, _, _, errors = connected_browser
    requests = []
    page.on("request", lambda request: requests.append((request.method, request.url)))
    output = os.environ.get("BATCHBEACON_TOUR_CAPTURE_DIR")
    for width in (1440, 390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        for size in ("100%", "200%"):
            page.evaluate(
                "(size)=>{document.documentElement.style.fontSize=size;scrollTo(0,0)}", size
            )
            summary = page.locator(".quick-tour summary")
            assert page.locator(".quick-tour").get_attribute("open") is None
            summary.focus()
            summary.press("Enter")
            expect(page.locator(".quick-tour")).to_have_attribute("open", "")
            assert page.locator(".quick-tour li").count() == 5
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                width,
                size,
                "open",
            )
            if output and size == "100%":
                page.screenshot(path=str(Path(output) / f"tour-open-{width}.png"), full_page=True)
            summary.press("Space")
            assert page.locator(".quick-tour").get_attribute("open") is None
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                width,
                size,
                "closed",
            )
            assert page.evaluate(
                'document.activeElement === document.querySelector(".quick-tour summary")'
            )
            if output and size == "100%":
                page.evaluate("scrollTo(0,0)")
                page.evaluate(
                    "() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))"
                )
                page.screenshot(
                    path=str(Path(output) / f"tour-closed-{width}.png"), full_page=False
                )
    page.evaluate("() => new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
    assert requests == [], requests
    assert not errors


def test_runtime_mode_neutral_before_config_and_explicit_after(connected_browser):
    page, _, _, errors = connected_browser
    expect(page.locator("#runtime-title")).to_have_text("Local integration")
    local = page.request.get(page.url.split("?")[0].rstrip("/") + "/api/workbench/config").json()
    page.route("**/api/workbench/config", lambda route: route.abort("blockedbyclient"))
    page.reload()
    expect(page.locator("#runtime-title")).to_have_text("Opening BatchBeacon AI")
    expect(page.locator("#runtime-detail")).to_contain_text("Loading extraction mode")
    page.unroute("**/api/workbench/config")
    page.reload()
    expect(page.locator("#runtime-title")).to_have_text("Local integration")
    local["mode"] = "REAL_VERTEX_EXTRACTION"
    page.route("**/api/workbench/config", lambda route: route.fulfill(json=local))
    page.route("**/api/guest", lambda route: route.abort("blockedbyclient"))
    page.reload()
    expect(page.locator("#runtime-title")).to_have_text("BatchBeacon AI")
    expect(page.locator("#runtime-detail")).to_contain_text("Gemini extraction")
    expect(page.locator("#result-disclosure")).to_have_text("Server result · Gemini extraction")
    assert not errors

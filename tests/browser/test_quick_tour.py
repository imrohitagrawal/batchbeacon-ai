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
            # Linux fallback font metrics exposed a nowrap source link that fit
            # the macOS system font. Check both without hiding or clipping text.
            for font in ("", "Arial, sans-serif"):
                page.evaluate("font => document.body.style.fontFamily = font", font)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), (
                    width,
                    size,
                    "open",
                    font,
                )
            page.evaluate("document.body.style.fontFamily = ''")
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
    expect(page.locator("#runtime-detail")).to_have_text(
        "Live prototype · Real AI analysis · Demo inventory actions"
    )
    expect(page.locator("#result-disclosure")).to_have_text("Server result · Gemini extraction")
    assert not errors


def test_overlay_tour_keyboard_steps_reflow_and_no_requests(connected_browser):
    page, _, _, errors = connected_browser
    requests = []
    page.on("request", lambda request: requests.append(request.url))
    dialog = page.locator("#tour-dialog")
    expect(dialog).not_to_be_visible()
    for width, size in [(1440, "100%"), (390, "100%"), (320, "200%")]:
        page.set_viewport_size({"width": width, "height": 844})
        page.evaluate("size => document.documentElement.style.fontSize=size", size)
        page.locator("#tour-open").click()
        expect(dialog).to_be_visible()
        expect(page.locator("#tour-back")).to_be_disabled()
        for step in range(1, 6):
            expect(page.locator("#tour-title")).to_have_text(f"Step {step} of 5")
            expect(page.locator("#tour-title")).to_be_focused()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            assert dialog.evaluate("d => d.scrollWidth <= d.clientWidth")
            page.locator("#tour-title").press("Tab")
            assert page.evaluate(
                "document.querySelector('#tour-dialog').contains(document.activeElement)"
            )
            if step == 2:
                page.locator("#tour-back").click()
                expect(page.locator("#tour-title")).to_have_text("Step 1 of 5")
                page.locator("#tour-next").click()
            page.locator("#tour-next").click()
        expect(dialog).not_to_be_visible()
        expect(page.locator("#tour-open")).to_be_focused()
        page.locator("#tour-open").click()
        expect(page.locator("#tour-title")).to_have_text("Step 1 of 5")
        page.locator("#tour-title").press("Escape")
        expect(dialog).not_to_be_visible()
        expect(page.locator("#tour-open")).to_be_focused()
        page.locator("#tour-open").click()
        page.locator("#tour-skip").click()
        expect(dialog).not_to_be_visible()
    assert requests == []
    assert not errors


def test_example_previews_explanations_and_top_tour(connected_browser):
    page, _, _, errors = connected_browser
    cards = page.locator('.example-card')
    assert cards.count() == 3
    expect(page.locator('#source-choice')).not_to_be_visible()
    expect(page.locator('#single-source')).to_contain_text('One historical notice')
    source_help = page.locator('#source-help summary')
    source_help.focus()
    source_help.press('Enter')
    expect(page.locator('#source-explanation')).to_contain_text(
        'This check uses the Singapore Food Agency (SFA) cheese recall notice '
        'published on 9 October 2026.'
    )
    source_help.press('Space')
    images = cards.locator('img')
    for image in images.all():
        expect(image).to_be_visible()
        assert image.evaluate('i => i.complete && i.naturalWidth === 1000')
    requests = []
    page.on('request', lambda request: requests.append(request.url))
    for width, size in [(1440, '100%'), (390, '100%'), (320, '200%')]:
        page.set_viewport_size({'width': width, 'height': 844})
        page.evaluate('size => {document.documentElement.style.fontSize=size; scrollTo(0,0)}', size)
        if size == '100%':
            tour = page.locator('#tour-open').bounding_box()
            assert tour['y'] + tour['height'] < 844
        first = cards.first.locator('summary')
        first.focus()
        first.press('Enter')
        expect(cards.first.locator('details')).to_have_attribute('open', '')
        expect(cards.first).to_contain_text('made with raw milk')
        expect(cards.first).to_contain_text('real and historical')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        first.press('Space')
        assert cards.first.locator('details').get_attribute('open') is None
        cards.nth(1).locator('summary').click()
        expect(cards.nth(1)).to_contain_text('producer name')
        cards.nth(1).locator('summary').click()
    assert requests == []
    cards.nth(1).locator('input').check()
    expect(page.locator('#sample-choice')).to_have_value('sfa-b')
    assert not errors

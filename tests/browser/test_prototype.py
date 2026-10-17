"""Visual prototype regressions only; these do not prove product journeys."""

import os
import re
import socket
import subprocess
import sys
import time
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def local_url():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "batchbeacon.app:app", "--app-dir", "src",
         "--host", "127.0.0.1", "--port", str(port), "--no-proxy-headers"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + float(os.environ.get("BATCHBEACON_TEST_START_SECONDS", "15"))
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(url + "/healthz", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if process.poll() is not None:
                    pytest.fail("Local test server exited before readiness")
                time.sleep(0.05)
        else:
            pytest.fail("Local test server did not become ready")
        yield url + "/prototype/"
    finally:
        process.terminate()
        process.wait(timeout=5)


@pytest.fixture
def page(local_url):
    with sync_playwright() as playwright:
        channel = os.environ.get("BATCHBEACON_TEST_BROWSER_CHANNEL")
        browser = playwright.chromium.launch(channel=channel or None)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.goto(local_url)
        yield page
        context.close()
        browser.close()


def test_queue_source_update_keeps_incident_and_disables_old_hold(page):
    page.locator("nav").get_by_role("link", name=re.compile("^Retail queue")).click()
    page.get_by_role("link", name="Alyan Chocolate Truffles 120 g · BB-0039 Scotland").click()
    expect(page.locator("#incident-id")).to_have_text("Incident BB-0039")
    expect(page.locator("#observed-product")).to_have_text("Alyan Dubai Style Chocolate Truffles")
    expect(page.locator("#source-pill")).to_contain_text("UK FSA")
    expect(page.locator("#observed-code")).to_have_text("319456")
    expect(page.locator("#code-type")).to_have_text("Product code")
    expect(page.locator("#observed-market")).to_have_text("Scotland")
    expect(page.locator("#source-link")).to_have_attribute("href", re.compile("update-1$"))
    expect(page.locator("#confirm-open")).to_be_disabled()


def test_hold_preview_requires_deliberate_confirmation_and_saves_nothing(page):
    page.get_by_role("button", name="Review simulated hold").click()
    expect(page.get_by_role("button", name="Confirm preview", exact=True)).to_be_disabled()
    page.get_by_label("I reviewed this example’s identity, batch, date and scope.").check()
    page.get_by_role("button", name="Confirm preview", exact=True).click()
    notice = page.get_by_role("status").filter(has_text="Confirmation preview complete")
    expect(notice).to_contain_text("No stock action was saved")


def test_guidance_has_valid_baseline_and_preview_effect_then_new_revision_rollback(page):
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    expect(page.locator(".wording-comparison > div").first).to_contain_text(
        "Photograph the complete best-before date marking."
    )
    page.get_by_role("button", name="Preview evaluation").click()
    expect(page.locator("#evaluation")).to_contain_text("actual evaluator has not run")
    page.get_by_role("button", name="Review activation").click()
    expect(page.get_by_role("button", name="Activate preview for this shop")).to_be_disabled()
    page.get_by_label("I have reviewed the example wording and evaluation for this shop.").check()
    page.get_by_role("button", name="Activate preview for this shop").click()
    page.get_by_role("button", name="Preview next capture").click()
    expect(page.locator("#capture-instruction")).to_contain_text("avoid glare")
    expect(page.locator("#capture-policy")).to_contain_text("v2")
    page.get_by_role("link", name="Capture guidance", exact=True).click()
    page.get_by_role("button", name="Preview rollback").click()
    expect(page.locator("#active-policy")).to_contain_text("v3")
    page.get_by_role("link", name="Evidence workbench", exact=True).click()
    expect(page.locator("#capture-instruction")).to_have_text(
        "Photograph the complete best-before date marking."
    )
    expect(page.locator("#capture-policy")).to_contain_text("v3")


def test_phone_comparison_reflows_and_queue_has_coherent_list_semantics(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.get_by_label("Preview a state").select_option("missing")
    expect(page.locator("#date-result")).to_have_text("Unknown")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert page.locator("#observed-product").evaluate(
        "el => parseFloat(getComputedStyle(el).fontSize)"
    ) >= 14
    page.locator("nav").get_by_role("link", name=re.compile("^Retail queue")).click()
    incidents = page.get_by_role("list", name="Synthetic shop incidents")
    expect(incidents.get_by_role("listitem")).to_have_count(6)
    page.get_by_label("Show", exact=True).select_option("empty")
    expect(page.get_by_role("heading", name="No examples match this filter")).to_be_visible()

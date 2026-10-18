"""Real browser/HTTP against explicit ADK mock + SDK fake. No cloud acceptance."""

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
from batchbeacon.retail_projection import RetailProjector, RetailReadPolicy
from batchbeacon.retail_refresh import RefreshPolicy, RetailRefresh
from batchbeacon.workbench import create_workbench_test_app
from tests.unit.test_firestore_store import setup as setup_factory
from tests.unit.test_reviewed_extraction import build_reviewed
from tests.unit.test_shared_admission import env as env_factory

pytestmark = pytest.mark.browser


@pytest.fixture
def connected_browser():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    setup, env = setup_factory.__wrapped__(), env_factory.__wrapped__()
    stores, server, guest, evidence, actions, now = setup
    gp = replace(guest.policy, origin=origin, mode='local_test')
    stores.guest_policy = gp
    guest = GuestService(gp, stores.guests, guest.objects, clock=lambda: now[0])
    setup = stores, server, guest, evidence, actions, now
    env[0].policy = replace(env[0].policy, guest_policy_hash=gp.digest())
    def configure(stores, actions, shared):
        stores.enable_retail(RetailProjector(actions, shared.policy, RetailReadPolicy()))
    c = build_reviewed(setup, env, (0,), configure=configure)
    app = create_workbench_test_app(c[0], c[8],
        RetailRefresh(stores.retail, RefreshPolicy()), ExtractionHTTPPolicy())
    runner = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port, log_level='error'))
    thread = threading.Thread(target=runner.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not runner.started and time.monotonic() < deadline:
        time.sleep(.02)
    assert runner.started
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel=os.environ.get('BATCHBEACON_TEST_BROWSER_CHANNEL') or None)
        context = browser.new_context(viewport={'width':1440, 'height':1000})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        try:
            page.goto(origin)
            expect(page.locator('#start-sample')).to_be_enabled()
            yield page, c, context, errors
        finally:
            context.close()
            browser.close()
            runner.should_exit = True
            thread.join(timeout=5)
            assert not thread.is_alive()


def check_sample(page):
    page.get_by_role('button', name='Use this label', exact=True).click()
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#capture-images img')).to_have_count(1)
    page.get_by_role('button', name='Extract and check', exact=True).click()
    expect(page.locator('#verdict-title')).to_have_text('Matches this recall', timeout=20000)


def test_connected_hold_reload_queue_reopen_and_no_browser_errors(connected_browser):
    page, c, context, errors = connected_browser
    check_sample(page)
    assert len(c[4]) == 2
    expect(page.locator('#comparisons [role=table]')).to_have_count(2)
    page.get_by_role('button', name='Review simulated hold', exact=True).click()
    expect(page.get_by_role('dialog')).to_be_visible()
    expect(page.locator('#hold-confirm')).to_be_disabled()
    page.locator('#hold-consent').check()
    page.locator('#hold-confirm').click()
    expect(page.locator('#verdict-title')).to_have_text('Simulated action recorded')
    page.reload()
    expect(page.locator('#verdict-title')).to_have_text('Simulated action recorded')
    page.get_by_role('link', name='Retail queue', exact=True).click()
    expect(page.locator('#queue-rows [role=listitem]')).to_have_count(1)
    expect(page.locator('#queue-rows')).to_contain_text('Simulated action recorded')
    page.locator('#queue-rows a').click()
    expect(page.locator('#verdict-title')).to_have_text('Simulated action recorded')
    expect(page.locator('#confirm-open')).to_be_disabled()
    cookies = context.cookies()
    assert all(cookie['httpOnly'] for cookie in cookies)
    assert page.evaluate('localStorage.length') == 0
    assert len(c[4]) == 2 and not errors


def test_correction_reverify_keeps_history_without_model_recall(connected_browser):
    page, c, _, errors = connected_browser
    check_sample(page)
    page.get_by_role('button', name='Correct a field', exact=True).click()
    page.locator('#correction-field').select_option('LOT')
    page.locator('#correction-value').fill('000Different')
    page.get_by_role('button', name='Save correction', exact=True).click()
    expect(page.locator('#verdict-title')).to_have_text('Evidence needs renewed review')
    expect(page.locator('#confirm-open')).to_be_disabled()
    page.locator('#reverify').click()
    expect(page.locator('#verdict-title')).to_have_text('Not listed in checked notices')
    expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#history')).to_contain_text('Observation v2')
    assert len(c[4]) == 2 and not errors


def test_second_browser_context_cannot_reopen_incident(connected_browser):
    page, c, _, errors = connected_browser
    check_sample(page)
    other = page.context.browser.new_context()
    try:
        p = other.new_page()
        p.goto(page.url)
        expect(p.locator('#app-status')).to_contain_text('unavailable')
        expect(p.locator('#comparisons')).not_to_contain_text('232511')
        expect(p.locator('#confirm-open')).to_be_disabled()
    finally:
        other.close()
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('width', [390,1440])
def test_connected_reflow_and_failed_refresh_preserves_historical_counts(connected_browser, width):
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width':width,'height':1000})
    check_sample(page)
    for view in ['workbench','retail','guidance']:
        page.locator(f'nav [data-view={view}]').click()
        if view == 'retail':
            expect(page.locator('#queue-rows [role=listitem]')).to_have_count(1)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        capture_dir = os.environ.get('BATCHBEACON_CAPTURE_DIR')
        if capture_dir:
            from pathlib import Path
            path = Path(capture_dir)
            path.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(path / f'workbench-{view}-{width}.png'), full_page=True)
    page.locator('nav [data-view=retail]').click()
    before = page.locator('#queue-count').inner_text()
    page.locator('#refresh-queue').click()
    expect(page.locator('#queue-status')).to_contain_text('historical')
    expect(page.locator('#queue-count')).to_have_text(before)
    c[3][5][0] += timedelta(seconds=3)
    page.locator('#refresh-queue').click()
    expect(page.locator('#queue-status')).to_contain_text('Manual refresh complete')
    assert not errors

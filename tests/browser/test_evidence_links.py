"""Reported checklist actions open the actual evidence, not another anchor."""
# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.mark.parametrize('width', [1440, 390])
def test_checklist_opens_retained_image_and_selected_notice(connected_browser, width):
    page, c, context, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 1000})
    page.locator('#start-sample').click()
    expect(page.locator('#capture-images img')).to_have_count(1)
    page.locator('.review-checklist summary').click()
    image_url = page.locator('#capture-images img').get_attribute('src')
    with context.expect_page() as opened:
        page.locator('#inspect-retained-label').click()
    image_page = opened.value
    image_page.wait_for_load_state()
    assert image_page.url.endswith(image_url)
    assert image_page.locator('img').count() == 1
    image_page.close()
    selected_url = page.locator('#source-summary a').get_attribute('href')
    context.route(selected_url, lambda route: route.fulfill(
        status=200, content_type='text/html', body='<h1>Controlled selected notice</h1>'))
    with context.expect_page() as opened:
        page.locator('#inspect-source-notice').click()
    notice_page = opened.value
    notice_page.wait_for_load_state()
    assert notice_page.url == selected_url
    expect(notice_page.locator('h1')).to_have_text('Controlled selected notice')
    notice_page.close()
    assert not c[4] and not errors


def test_retained_targets_follow_panels_and_clear_with_selection_or_expiry(connected_browser):
    page, _, _, errors = connected_browser
    expect(page.locator('#inspect-retained-label')).to_be_hidden()
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#capture-images img')).to_have_count(1)
    old_url = page.locator('#inspect-retained-label').get_attribute('href')
    page.evaluate("state.captures.push({id:'second-panel'});drawCaptures()")
    expect(page.locator('#capture-images a')).to_have_count(2)
    expect(page.locator('#inspect-retained-label')).to_have_text(
        'Open retained label panel 1 (new tab)')
    assert page.locator('#capture-images a').nth(1).get_attribute('href').endswith('/second-panel')
    page.evaluate("state.incident='another-case';state.captures=[];drawCaptures()")
    expect(page.locator('#inspect-retained-label')).to_be_hidden()
    assert page.locator('#inspect-retained-label').get_attribute('href') is None
    assert old_url not in page.locator('#capture-images').inner_html()
    page.evaluate("state.captures=[{id:'another-image'}];drawCaptures();expire()")
    expect(page.locator('#inspect-retained-label')).to_be_hidden()
    assert page.locator('#inspect-retained-label').get_attribute('href') is None
    expect(page.locator('#capture-images a')).to_have_count(0)
    expect(page.locator('#retained-label-help')).to_contain_text('expired')
    assert not errors

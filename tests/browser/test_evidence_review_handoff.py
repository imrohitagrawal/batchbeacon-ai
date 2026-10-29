"""Evidence-first navigation and stable capture geometry; explicit fake SDK/mock ADK."""

import pytest
from playwright.sync_api import expect

from tests.browser import test_workbench
from tests.browser.test_workbench_handoffs import (
    capture,
    checked,
    inside_viewport,
)

pytestmark = pytest.mark.browser
connected_browser = test_workbench.connected_browser


@pytest.mark.parametrize('boundary', ['new-incident', 'expiry'])
def test_capture_geometry_reserved_before_decode_and_node_retained_on_reload(
        connected_browser, boundary):
    """Red if image space collapses while loading or unchanged record reads recreate it."""
    page, c, _, errors = connected_browser
    images = []
    page.route('**/captures/*', lambda route: images.append(route))
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    image = page.locator('#capture-images img')
    expect(image).to_have_count(1)
    expect(image).to_have_attribute('width', '1000')
    expect(image).to_have_attribute('height', '700')
    assert image.bounding_box()['height'] > 100
    assert not image.evaluate('el=>el.complete')
    assert len(images) == 1
    images.pop().continue_()
    page.wait_for_function("()=>document.querySelector('#capture-images img').naturalWidth>0")
    page.evaluate("window.savedImage=document.querySelector('#capture-images img')")
    before = image.bounding_box()['height']
    page.evaluate('loadOwnedIncident(state.incident)')
    assert page.evaluate("savedImage===document.querySelector('#capture-images img')")
    assert image.bounding_box()['height'] == before
    assert image.evaluate('el=>el.complete')
    page.evaluate('clearReview()' if boundary == 'new-incident' else 'expire()')
    expect(image).to_have_count(0)
    assert not page.evaluate('savedImage.isConnected')
    assert len(c[4]) == 0 and len(c[3][1].calls) > 0 and not errors


@pytest.mark.parametrize('width,height', [(1440, 698), (390, 800)])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('activation', ['pointer', 'keyboard'])
def test_label_save_has_one_visible_handoff_with_native_motion_preference(
        connected_browser, width, height, motion, activation):
    """Red if save double-scrolls, skips the receipt, or animates keyboard/reduced motion."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': height})
    page.emulate_media(reduced_motion=motion)
    button = page.locator('#start-sample')
    button.evaluate("el=>el.scrollIntoView({block:'end',behavior:'instant'})")
    page.evaluate('''()=>{
      window.orientationScrolls=[];
      const native=Element.prototype.scrollIntoView;
      Element.prototype.scrollIntoView=function(options){
        orientationScrolls.push({id:this.id,...options});
        return native.call(this,options);
      };
    }''')
    if activation == 'keyboard':
        button.focus()
        button.press('Enter')
    else:
        button.click()
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#label-status')).to_contain_text('Label saved')
    assert page.evaluate('document.activeElement.id') == 'label-status'
    behavior = 'smooth' if activation == 'pointer' and motion == 'no-preference' else 'instant'
    assert page.evaluate('orientationScrolls') == [
        {'id': 'label-status', 'block': 'start', 'behavior': behavior}]
    page.wait_for_function('''()=>{
      const r=document.querySelector('#label-status').getBoundingClientRect();
      const c=document.querySelector('#check').getBoundingClientRect();
      return r.y>=100 && c.bottom<=innerHeight;
    }''')
    inside_viewport(page, '#label-status')
    inside_viewport(page, '#check')
    capture(page, f'label-handoff-{width}-{motion}-{activation}')
    # A real user navigation immediately after save must not be stolen by a later callback.
    page.locator('[data-view=retail]').first.click()
    expect(page.locator('#retail-title')).to_be_focused()
    expect(page.locator('#workbench')).to_be_hidden()
    assert len(c[4]) == 0 and len(c[3][1].calls) > 0 and not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('review', [False, True])
@pytest.mark.parametrize('activation', ['pointer', 'keyboard'])
def test_result_guides_evidence_review_then_returns_to_explicit_action(
        connected_browser, width, review, activation):
    """Red if completed results skip evidence, navigation spends calls or implies approval."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    checked(page, c, review=review)
    primary = page.locator('#review-evidence')
    expect(primary).to_be_visible()
    expect(primary).to_have_class('button primary')
    expect(page.locator('#check')).to_have_class('button secondary')
    expect(page.locator('#confirm-open')).to_have_class('button secondary')
    expect(page.locator('#decision-status')).to_contain_text('Review evidence side by side')
    before = len(c[3][1].calls)
    assert before > 0
    if activation == 'keyboard':
        primary.focus()
        primary.press('Enter')
    else:
        primary.click()
    expect(page.locator('#comparison-title')).to_be_focused()
    inside_viewport(page, '#comparison-title')
    expect(page.locator('#comparison-next')).to_contain_text(
        'identity, lot, required date and scope')
    expect(page.locator('#comparisons [role=table]')).to_have_count(2)
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    page.locator('#comparison-continue').click()
    expect(page.locator('#decision-title')).to_be_focused()
    inside_viewport(page, '#confirm-open')
    expect(page.locator('#confirm-open')).to_be_enabled()
    assert len(c[3][1].calls) == before and len(c[4]) == 2
    capture(page, f'evidence-review-{width}-{review}-{activation}')
    page.locator('#confirm-open').click()
    expect(page.locator('#confirm-dialog')).to_be_visible()
    expect(page.locator('#hold-confirm')).to_be_disabled()
    assert not page.locator('#hold-consent').is_checked()
    assert not errors


@pytest.mark.parametrize('boundary', ['clear', 'expiry', 'stale'])
def test_evidence_navigation_does_not_grant_action_at_invalid_boundary(
        connected_browser, boundary):
    """Red if review navigation grants permission or survives removal of its evidence."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#review-evidence')).to_be_enabled()
    if boundary == 'stale':
        page.evaluate('state.evidence.current=false;state.capabilities.incident.action.available=false;render()')
        expect(page.locator('#verdict-title')).to_have_text('Evidence needs renewed review')
        page.locator('#review-evidence').click()
        expect(page.locator('#comparison-title')).to_be_focused()
        expect(page.locator('#confirm-open')).to_be_disabled()
    else:
        page.evaluate('clearReview()' if boundary == 'clear' else 'expire()')
        expect(page.locator('#review-evidence')).to_be_hidden()
        expect(page.locator('#comparison-continue')).to_be_hidden()
        expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    assert len(c[4]) == 2 and len(c[3][1].calls) > 0 and not errors

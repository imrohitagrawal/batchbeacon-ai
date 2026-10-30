"""Evidence-first navigation and stable capture geometry; explicit fake SDK/mock ADK."""

import re

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


def outlined(region):
    return region.evaluate('''el=>{
      const s=getComputedStyle(el);
      return s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>0;
    }''')


@pytest.mark.parametrize('focus_target', ['field', 'file'])
def test_capture_completion_does_not_leave_an_arrival_for_later_focus(
        connected_browser, focus_target):
    """Red if an upload finishing after focus moves away revives an old label highlight."""
    page, c, _, errors = connected_browser
    checked(page, c)
    sample = page.locator('#sample-choice').input_value()
    response = page.request.get(page.url.split('?')[0] + f'samples/{sample}.png')
    assert response.ok
    page.locator('#capture').click()
    page.locator('#capture-file').set_input_files(
        {'name': 'another.png', 'mimeType': 'image/png', 'buffer': response.body()})
    held = []
    page.route('**/api/incidents/*/captures', lambda route: held.append(route)
               if route.request.method == 'POST' else route.continue_())
    before = len(c[3][1].calls)
    with page.expect_request(lambda request: request.url.endswith('/captures')
                             and request.method == 'POST'):
        page.locator('#upload').click()
    page.wait_for_function('()=>state.busy')
    assert len(held) == 1
    # A real table control remains available while the upload waits for its response.
    if focus_target == 'field':
        page.locator('.field-pick').first.click()
    else:
        page.locator('#capture-file').focus()
    held.pop().continue_()
    page.wait_for_function('()=>!state.busy')
    expect(page.locator('#label-status')).to_contain_text('Label saved')
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('.label-ready-cue')).to_have_count(1)
    expect(page.locator('.label-ready-cue')).to_have_count(0, timeout=5000)
    assert len(c[3][1].calls) > before and len(c[4]) == 2
    after = len(c[3][1].calls)
    page.locator('#check').focus()
    assert not outlined(page.locator('.evidence-panel'))
    expect(page.locator('#check')).to_be_focused()
    assert len(c[3][1].calls) == after and len(c[4]) == 2 and not errors


def test_saved_read_retires_arrival_before_rebuilding_focused_fields(connected_browser):
    """Red if replacing a focused evidence field lets a later focus revive the old arrival."""
    page, c, _, errors = connected_browser
    checked(page, c)
    page.locator('#review-evidence').click()
    region = page.locator('.comparison-panel')
    assert outlined(region)
    page.locator('.field-pick').first.click()
    page.evaluate('window.oldFocusedField=document.activeElement')
    before = len(c[3][1].calls)
    page.evaluate('loadOwnedIncident(state.incident)')
    assert page.evaluate('!oldFocusedField.isConnected')
    assert len(c[3][1].calls) > before
    page.locator('#comparison-title').focus()
    assert not outlined(region)
    assert len(c[4]) == 2 and not errors


def test_decision_stage_survives_cancel_and_saved_read_without_implying_consent(
        connected_browser):
    """Red if dialog cancellation or a saved read moves the decision journey backward."""
    page, c, _, errors = connected_browser
    checked(page, c)
    current = page.locator('#journey-stages [aria-current=step]')
    page.locator('#review-evidence').click()
    page.locator('#comparison-continue').click()
    expect(current).to_contain_text('Your decision')
    page.locator('#confirm-open').click()
    expect(page.locator('#confirm-dialog')).to_be_visible()
    page.keyboard.press('Escape')
    expect(page.locator('#confirm-open')).to_be_focused()
    expect(current).to_contain_text('Your decision')
    page.evaluate('loadOwnedIncident(state.incident)')
    expect(current).to_contain_text('Your decision')
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    assert not page.locator('#hold-consent').is_checked()
    assert page.evaluate('state.actions.length') == 0 and len(c[4]) == 2
    page.locator('#review-evidence').click()
    expect(current).to_contain_text('Evidence comparison')
    page.locator('#comparison-continue').click()
    page.locator('#confirm-open').click()
    page.locator('#hold-consent').check()
    page.locator('#hold-confirm').click()
    expect(page.locator('#verdict-title')).to_have_text('Workspace action recorded')
    expect(current).to_contain_text('Saved review')
    assert page.evaluate('state.actions.length') == 1 and len(c[4]) == 2 and not errors


def test_decision_navigation_updates_the_visible_journey_without_consent(connected_browser):
    """Red if going to the decision leaves Evidence comparison marked as the current step."""
    page, c, _, errors = connected_browser
    checked(page, c)
    current = page.locator('#journey-stages [aria-current=step]')
    page.locator('#review-evidence').click()
    expect(current).to_contain_text('Evidence comparison')
    before = len(c[3][1].calls)
    assert before > 0 and len(c[4]) == 2
    page.locator('#comparison-continue').click()
    expect(current).to_contain_text('Your decision')
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    assert not page.locator('#hold-consent').is_checked()
    assert len(c[3][1].calls) == before and len(c[4]) == 2
    page.locator('#review-evidence').click()
    expect(current).to_contain_text('Evidence comparison')
    assert not errors


@pytest.mark.parametrize('width,height', [(1440, 698), (390, 800)])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('activation', ['pointer', 'keyboard'])
def test_saved_label_heading_precedes_image_and_reachable_extract(
        connected_browser, width, height, motion, activation):
    """Red if save misses the label, Extract precedes its image, or its outline revives."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': height})
    page.emulate_media(reduced_motion=motion)
    button = page.locator('#start-sample')
    if activation == 'keyboard':
        button.focus()
        button.press('Enter')
    else:
        button.click()
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#evidence-title')).to_be_focused()
    page.wait_for_function('''()=>{
      const h=document.querySelector('#evidence-title').getBoundingClientRect();
      return h.top>=100 && h.bottom<=innerHeight;
    }''')
    inside_viewport(page, '#evidence-title')
    region = page.locator('.evidence-panel')
    assert outlined(region)
    assert outlined(page.locator('#check'))
    image = page.locator('#capture-images img')
    expect(image).to_have_count(1)
    assert image.evaluate('async img=>{await img.decode();return img.naturalWidth;}') > 0
    assert image.evaluate("""img=>img.getBoundingClientRect().bottom<=
      document.querySelector('#check').getBoundingClientRect().top""")
    # The full label comes first; short viewports can reach the next control by scrolling.
    page.locator('#check').scroll_into_view_if_needed()
    inside_viewport(page, '#check')
    expect(page.locator('.label-ready-cue')).to_have_count(1)
    expect(page.locator('.label-ready-cue')).to_have_count(0, timeout=5000)
    assert outlined(region)  # Still apparent after the temporary cue ends.
    capture(page, f'section-label-{width}-{motion}-{activation}')
    button.focus()
    assert not outlined(region)
    page.locator('#evidence-title').focus()
    assert not outlined(region)  # Returning focus alone cannot revive an old arrival.
    assert len(c[4]) == 0 and len(c[3][1].calls) > 0 and not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('activation', ['pointer', 'keyboard'])
def test_review_navigation_visibly_identifies_both_destinations(
        connected_browser, width, motion, activation):
    """Red if either navigation destination lacks its visible outline or creates an action."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    page.emulate_media(reduced_motion=motion)
    checked(page, c)
    before = len(c[3][1].calls)
    assert before > 0 and len(c[4]) == 2
    for control, heading, region in [
        ('#review-evidence', '#comparison-title', '.comparison-panel'),
        ('#comparison-continue', '#decision-title', '.decision'),
    ]:
        button = page.locator(control)
        if activation == 'keyboard':
            button.focus()
            button.press('Enter')
        else:
            button.click()
        expect(page.locator(heading)).to_be_focused()
        inside_viewport(page, heading)
        assert outlined(page.locator(region))
        expect(page.locator('.review-ready-cue')).to_have_count(1)
        expect(page.locator('.review-ready-cue')).to_have_count(0, timeout=5000)
        assert outlined(page.locator(region))
        capture(page, f'section-{heading[1:]}-{width}-{motion}-{activation}')
    expect(page.locator('#comparison-continue')).to_have_text('Go to decision')
    inside_viewport(page, '#confirm-open')
    expect(page.locator('#confirm-open')).to_be_enabled()
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    assert len(c[3][1].calls) == before and len(c[4]) == 2 and not errors
    page.evaluate('expire()')
    assert not outlined(page.locator('.decision'))
    assert not outlined(page.locator('.comparison-panel'))
    expect(page.locator('#confirm-open')).to_be_disabled()


@pytest.mark.parametrize('boundary', ['view', 'clear', 'selection'])
def test_review_arrival_does_not_return_after_a_context_change(connected_browser, boundary):
    """Red if a later view, selection or cleared review can revive an old section highlight."""
    page, c, _, errors = connected_browser
    checked(page, c)
    page.locator('#review-evidence').click()
    region = page.locator('.comparison-panel')
    assert outlined(region)
    expect(page.locator('.review-ready-cue')).to_have_count(1)
    if boundary == 'view':
        page.evaluate("show('retail');show('workbench',{focus:false})")
    elif boundary == 'clear':
        page.evaluate('clearReview()')
    else:
        page.locator('#start-sample').click()
        expect(page.locator('#evidence-title')).to_be_focused()
    page.locator('#comparison-title').focus()
    assert not outlined(region)
    expect(page.locator('.review-ready-cue')).to_have_count(0)
    assert len(c[4]) == 2 and len(c[3][1].calls) > 0 and not errors


@pytest.mark.parametrize('width', [1440, 390])
def test_action_affordance_differs_from_inspect_fields_and_keeps_disabled_state(
        connected_browser, width):
    """Red if action buttons resemble field inspectors or disabled actions look enabled."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    checked(page, c)
    styles = page.evaluate('''()=>{
      const read=s=>{const c=getComputedStyle(document.querySelector(s));
        return {background:c.backgroundColor,color:c.color,opacity:Number(c.opacity)};};
      return {navigation:read('#comparison-continue'),action:read('#confirm-open'),
        field:read('.field-pick[aria-pressed="false"]')};
    }''')
    assert styles['navigation']['background'] == styles['action']['background']
    assert styles['action']['background'] != styles['field']['background']
    assert styles['action']['color'] != styles['field']['color']
    # Progress/action controls have light text on a dark fill; inspectors do not.
    def luminance(rgb):
        channels = [float(v) / 255 for v in re.findall(r'[\d.]+', rgb)[:3]]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
                  for v in channels]
        return sum(v * weight for v, weight in zip(linear, [.2126, .7152, .0722], strict=True))
    foreground = luminance(styles['action']['color'])
    background = luminance(styles['action']['background'])
    assert foreground > background
    assert (foreground + .05) / (background + .05) >= 4.5
    expect(page.locator('#confirm-open')).to_be_enabled()
    page.locator('.field-pick').first.click()
    expect(page.locator('.field-pick[aria-pressed=true]')).to_have_count(1)
    expect(page.locator('#field-detail')).not_to_be_empty()
    page.evaluate('state.evidence.current=false;state.capabilities.incident.action.available=false;render()')
    expect(page.locator('#confirm-open')).to_be_disabled()
    disabled = page.locator('#confirm-open').evaluate('el=>getComputedStyle(el).backgroundColor')
    assert disabled != styles['action']['background']
    assert len(c[4]) == 2 and len(c[3][1].calls) > 0 and not errors


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
    assert page.evaluate('document.activeElement.id') == 'evidence-title'
    behavior = 'smooth' if activation == 'pointer' and motion == 'no-preference' else 'instant'
    assert page.evaluate('orientationScrolls') == [
        {'id': 'evidence-title', 'block': 'start', 'behavior': behavior}]
    page.wait_for_function('''()=>{
      const r=document.querySelector('#label-status').getBoundingClientRect();
      return r.y>=100 && r.bottom<=innerHeight;
    }''')
    inside_viewport(page, '#label-status')
    expect(page.locator('#capture-images img')).to_have_count(1)
    assert page.locator('#capture-images img').evaluate("""img=>
      !!(img.compareDocumentPosition(document.querySelector('#check')) &
      Node.DOCUMENT_POSITION_FOLLOWING)""")
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
    inside_viewport(page, '#decision-title')
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


@pytest.mark.parametrize('condition,title', [
    ('not-listed', 'No stock hold is supported'),
    ('stale', 'Evidence needs renewed review'),
    ('source-blocked', 'Evidence needs renewed review'),
    ('unknown-capability', 'Action availability is unknown'),
    ('unknown-action', 'Action availability is unknown'),
    ('unknown-available', 'Action availability is unknown'),
    ('unavailable-action', 'No new action is available'),
    ('unknown-check', 'Resolve the check before an action'),
])
def test_continue_names_actual_unavailable_decision_without_promising_confirmation(
        connected_browser, condition, title):
    """Red if evidence navigation promises confirmation without a current permitted action."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#confirm-open')).to_be_enabled()
    before = len(c[3][1].calls)
    assert before > 0
    page.evaluate('''condition=>{
      state.capabilities.incident.action.available=false;
      if(condition==='not-listed')state.evidence.result.verdict='NOT_LISTED_IN_CHECKED_NOTICES';
      if(condition==='stale'||condition==='source-blocked')state.evidence.current=false;
      if(condition==='source-blocked')state.evidence.source={blocked:true,mode:'LIVE',live_status:'CHANGED'};
      if(condition==='unknown-capability')state.capabilities=null;
      if(condition==='unknown-action')state.capabilities.incident.action=null;
      if(condition==='unknown-available')delete state.capabilities.incident.action.available;
      if(condition==='unknown-check')state.acquisitionUnknown=true;
      render();
    }''', condition)
    page.locator('#review-evidence').click()
    expect(page.locator('#comparison-title')).to_be_focused()
    page.locator('#comparison-continue').click()
    expect(page.locator('#decision-title')).to_be_focused()
    expect(page.locator('#decision-title')).to_have_text(title)
    expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    if condition in ('stale', 'source-blocked', 'unknown-check'):
        expect(page.locator('#review-evidence')).to_have_class('button secondary')
    if condition == 'unknown-capability':
        expect(page.locator('#decision-recheck')).to_be_visible()
    assert len(c[3][1].calls) == before and len(c[4]) == 2 and not errors


def test_failed_capture_retries_on_saved_status_read_but_healthy_capture_is_retained(
        connected_browser):
    """Red if keyed reuse makes a transient broken image survive explicit status recovery."""
    page, c, _, errors = connected_browser
    requests = {'failed': 0, 'healthy': 0, 'allow': False}

    def image_response(route):
        if requests['allow']:
            requests['healthy'] += 1
            route.continue_()
        else:
            requests['failed'] += 1
            route.fulfill(status=503, body='temporarily unavailable')

    page.route('**/captures/*', image_response)
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.route('**/capabilities', lambda route: route.fulfill(
        status=503, json={'error': 'availability_unconfirmed'}))
    page.locator('#check').click()
    expect(page.locator('#verdict-title')).to_have_text('Matches this recall')
    expect(page.locator('#decision-recheck')).to_be_visible()
    page.wait_for_function('''()=>{
      const image=document.querySelector('#capture-images img');
      return image.complete && image.naturalWidth===0;
    }''')
    assert requests['failed'] > 0
    assert page.locator('#capture-images img').bounding_box()['height'] > 100
    requests['allow'] = True
    page.unroute('**/capabilities')
    page.locator('#decision-recheck').click()
    expect(page.locator('#confirm-open')).to_be_enabled()
    expect(page.locator('#capture-images img')).to_have_js_property('naturalWidth', 1000)
    assert requests['healthy'] == 1
    page.evaluate("window.recoveredImage=document.querySelector('#capture-images img')")
    page.evaluate('loadOwnedIncident(state.incident)')
    assert page.evaluate("recoveredImage===document.querySelector('#capture-images img')")
    assert requests['healthy'] == 1 and len(c[4]) == 2 and not errors


def test_native_pointer_scroll_can_be_interrupted_by_a_wheel_gesture(connected_browser):
    """Red if smooth orientation resumes after a user interrupts it with native scrolling."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': 1440, 'height': 698})
    page.emulate_media(reduced_motion='no-preference')
    button = page.locator('#start-sample')
    button.evaluate("el=>el.scrollIntoView({block:'end',behavior:'instant'})")
    page.evaluate('''()=>{
      window.wheelWitness=null;
      window.addEventListener('wheel',()=>{
        const label=document.querySelector('#evidence-title');
        const target=Math.min(document.documentElement.scrollHeight-innerHeight,
          scrollY+label.getBoundingClientRect().top-parseFloat(getComputedStyle(label).scrollMarginTop));
        wheelWitness={y:scrollY,target};
      },{once:true,capture:true,passive:true});
    }''')
    button.click()
    expect(page.locator('#evidence-title')).to_be_focused()
    page.mouse.wheel(0, -600)
    positions = page.evaluate('''()=>new Promise(resolve=>{
      const positions=[];
      function frame(){positions.push(scrollY);
        if(positions.length<60)requestAnimationFrame(frame);else resolve(positions);}
      requestAnimationFrame(frame);
    })''')
    witness = page.evaluate('wheelWitness')
    assert witness and witness['y'] < witness['target'] - 100
    assert positions[-1] < witness['target'] - 100
    assert max(positions[-5:]) - min(positions[-5:]) <= 1
    expect(page.locator('#evidence-title')).to_be_focused()
    assert len(c[4]) == 0 and len(c[3][1].calls) > 0 and not errors


def test_saved_read_keeps_evidence_navigation_space_but_disables_it(connected_browser):
    """Red if refreshing a displayed result removes/reinserts its new navigation controls."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#review-evidence')).to_be_enabled()
    before = len(c[3][1].calls)
    assert before > 0
    page.evaluate('window.savedCapabilities=state.capabilities;state.loading=true;render()')
    for selector in ['#review-evidence', '#comparison-continue']:
        expect(page.locator(selector)).to_be_visible()
        expect(page.locator(selector)).to_be_disabled()
    expect(page.locator('#comparison-next')).to_be_visible()
    expect(page.locator('#review-evidence')).to_have_class('button primary')
    expect(page.locator('#check')).to_have_class('button secondary')
    page.evaluate('state.loading=false;state.capabilities=savedCapabilities;render()')
    expect(page.locator('#review-evidence')).to_be_enabled()
    assert len(c[3][1].calls) == before and len(c[4]) == 2 and not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('operation', ['action', 'capture'])
def test_unknown_request_guides_reconciliation_before_any_new_confirmation(
        connected_browser, width, operation):
    """Red if a real aborted action/upload leaves a confirmation promise or wrong primary."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    checked(page, c)
    expect(page.locator('#confirm-open')).to_be_enabled()
    endpoint = '**/actions' if operation == 'action' else '**/captures'

    def interrupt(route):
        if route.request.method == 'POST':
            route.abort('failed')
        else:
            route.continue_()

    page.route(endpoint, interrupt)
    if operation == 'action':
        page.locator('#confirm-open').click()
        page.locator('#hold-consent').check()
        page.locator('#hold-confirm').click()
    else:
        sample = page.locator('#sample-choice').input_value()
        response = page.request.get(page.url.split('?')[0] + f'samples/{sample}.png')
        assert response.ok
        raw = response.body()
        page.locator('#capture').click()
        page.locator('#capture-file').set_input_files(
            {'name': 'another.png', 'mimeType': 'image/png', 'buffer': raw})
        page.locator('#upload').click()
    expect(page.locator('#app-status')).to_contain_text('Connection interrupted')
    expect(page.locator('#recover')).to_be_enabled()
    assert page.evaluate('!!state.pending && state.capabilities.incident.action.available')
    before = len(c[3][1].calls)
    assert before > 0
    page.locator('#review-evidence').click()
    page.locator('#comparison-continue').click()
    expect(page.locator('#decision-title')).to_be_focused()
    expect(page.locator('#decision-title')).to_have_text('Reconcile pending operation')
    inside_viewport(page, '#decision-title')
    inside_viewport(page, '#recover')
    expect(page.locator('#review-evidence')).to_have_class('button secondary')
    expect(page.locator('#check')).to_have_class('button secondary')
    expect(page.locator('#recover')).to_have_class('button primary')
    expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    page.evaluate('state.pendingOwnershipUnknown=true;controls()')
    expect(page.locator('#decision-title')).to_have_text('Check pending access')
    expect(page.locator('#recover')).to_have_text('Check pending access')
    expect(page.locator('#confirm-open')).to_be_disabled()
    page.evaluate('state.pendingOwnershipUnknown=false;controls()')
    expect(page.locator('#decision-title')).to_have_text('Reconcile pending operation')
    assert len(c[3][1].calls) == before and len(c[4]) == 2
    if operation == 'action':
        assert page.evaluate('state.actions.length') == 0
        page.unroute(endpoint)
        page.locator('#recover').click()
        expect(page.locator('#confirm-open')).to_be_enabled()
        expect(page.locator('#decision-title')).to_have_text('Your confirmation comes next')
        assert page.evaluate('state.actions.length') == 0
        assert not page.evaluate('state.pending')
        page.locator('#confirm-open').click()
        expect(page.locator('#hold-confirm')).to_be_disabled()
        page.locator('#hold-consent').check()
        page.locator('#hold-confirm').click()
        expect(page.locator('#verdict-title')).to_have_text('Workspace action recorded')
        expect(page.locator('#decision-title')).to_have_text('Saved workspace action')
        assert page.evaluate('state.actions.length') == 1
    assert len(c[4]) == 2 and not errors

"""Visible task handoffs with explicit mock ADK and fake SDK; no cloud acceptance."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.browser import test_workbench
from tests.unit.test_extraction_proposal import unknown

pytestmark = pytest.mark.browser
connected_browser = test_workbench.connected_browser


def checked(page, c, *, review=False):
    if review:
        c[5][0]['label']['pack'] = unknown(kind='TEXT')
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.locator('#check').click()
    expect(page.locator('#verdict-title')).to_have_text(
        'Review required' if review else 'Matches this recall', timeout=20000)
    expect(page.locator('#check')).to_be_enabled()
    assert len(c[4]) == 2


def inside_viewport(page, selector):
    box = page.locator(selector).bounding_box()
    header = (page.locator('header').first.bounding_box()
              or page.locator('.app-header nav').bounding_box())
    assert box and header
    assert box['y'] >= header['y'] + header['height']
    assert box['y'] + box['height'] <= page.viewport_size['height']


def capture(page, name):
    if directory := os.environ.get('BATCHBEACON_CAPTURE_DIR'):
        destination = Path(directory)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / (name + '.png')), full_page=True)
        page.screenshot(path=str(destination / (name + '-viewport.png')))


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('review', [False, True])
def test_confirmed_result_reveals_outcome_and_available_next_action(
        connected_browser, width, motion, review):
    """Red if a confirmed check omits its outcome/action handoff, focus or static cue."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    page.emulate_media(reduced_motion=motion)
    checked(page, c, review=review)
    action = 'Review follow-up request' if review else 'Review stock hold'
    outcome = 'Review required' if review else 'Matches this recall'
    expect(page.locator('#decision-status')).to_contain_text(outcome)
    expect(page.locator('#decision-status')).to_contain_text(action)
    expect(page.locator('#confirm-open')).to_have_text(action)
    expect(page.locator('#confirm-open')).to_be_enabled()
    assert page.evaluate('document.activeElement.id') == 'decision-status'
    inside_viewport(page, '#decision-status')
    inside_viewport(page, '#confirm-open')
    cue = page.locator('.decision > .result-ready-cue')
    expect(cue).to_have_count(1)
    expect(cue).to_have_attribute('aria-hidden', 'true')
    assert cue.evaluate('''el=>{
      const s=getComputedStyle(el);
      return {pointer:s.pointerEvents,transform:s.transform,duration:s.animationDuration,
        opacity:el.getAnimations()[0].effect.getKeyframes().map(f=>f.opacity)};
    }''') == {'pointer': 'none', 'transform': 'none', 'duration': '1.2s',
             'opacity': ['1', '1']}
    capture(page, f'completed-{width}-{motion}-{review}')
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    expect(page.locator('#confirm-dialog')).to_have_count(1)
    expect(cue).to_have_count(0, timeout=5000)
    expect(page.locator('#decision-status')).to_contain_text(action)
    assert len(c[4]) == 2 and not errors
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('editor,field', [
    ('capture', 'capture-file'), ('correction', 'correction-field')])
@pytest.mark.parametrize('activation', ['keyboard', 'pointer'])
def test_open_editor_reveals_and_focuses_first_input_without_saving(
        connected_browser, width, motion, editor, field, activation):
    """Red if opening only toggles a below-fold editor, loses a draft or sends a request."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    page.emulate_media(reduced_motion=motion)
    checked(page, c)
    button = page.locator('#' + editor)
    panel = page.locator('#' + editor + '-panel')
    expect(panel).to_be_hidden()
    expect(page.locator('#' + field)).to_have_count(1)
    rpc_before = len(c[3][1].calls)
    assert rpc_before > 0
    if activation == 'keyboard':
        button.focus()
        button.press('Enter')
    else:
        button.click()
    expect(panel).to_be_visible()
    expect(button).to_have_attribute('aria-expanded', 'true')
    assert page.evaluate('document.activeElement.id') == field
    inside_viewport(page, '#' + field)
    cue = panel.locator('.editor-ready-cue')
    expect(cue).to_have_count(1)
    capture(page, f'editor-{editor}-{width}-{motion}-{activation}')
    inside_viewport(page, '#' + editor + '-panel h3')
    if editor == 'correction':
        page.locator('#correction-field').select_option('LOT')
        page.locator('#correction-value').fill('000aB/ ')
    else:
        page.locator('#capture-file').set_input_files(
            {'name': 'draft.png', 'mimeType': 'image/png', 'buffer': b'draft'})
    button.click()
    expect(panel).to_be_hidden()
    expect(button).to_have_attribute('aria-expanded', 'false')
    assert page.evaluate('document.activeElement.id') == editor
    button.click()
    assert page.evaluate('document.activeElement.id') == field
    if editor == 'correction':
        expect(page.locator('#correction-value')).to_have_value('000aB/ ')
    else:
        assert page.locator('#capture-file').evaluate('el=>el.files.length') == 1
    assert len(c[3][1].calls) == rpc_before
    assert len(c[4]) == 2 and not errors
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.parametrize('dispatch', ['button', 'record-reload'])
def test_correction_invalidates_previous_available_action_handoff(connected_browser, dispatch):
    """Red if a saved correction leaves the old completion/action instruction visible."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#decision-status')).to_contain_text('Review stock hold')
    page.locator('#correction').click()
    page.locator('#correction-field').select_option('LOT')
    page.locator('#correction-value').fill('000Different')
    if dispatch == 'button':
        page.locator('#save-correction').click()
    else:
        page.evaluate('saveCorrection()')
    expect(page.locator('#verdict-title')).to_have_text('Evidence needs renewed review')
    expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#decision-status')).not_to_contain_text('Review stock hold')
    assert len(c[4]) == 2 and not errors
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')


@pytest.mark.parametrize('outcome', [409, 503, 'transport'])
def test_refused_review_retires_hint_and_requires_status_read(connected_browser, outcome):
    """Red if refusal retains an action hint/eligibility, or recheck cannot restore it."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#decision-status')).to_contain_text('Review stock hold')
    requests = []

    def refuse(route):
        requests.append(route.request.url)
        if outcome == 'transport':
            route.abort('failed')
        else:
            route.fulfill(status=outcome, json={'error': 'review_refused'})

    page.route('**/actions/prepare**', refuse)
    page.locator('#confirm-open').click()
    expect(page.locator('#app-status')).to_contain_text(
        'Connection interrupted' if outcome == 'transport' else 'review refused')
    assert len(requests) == 1
    expect(page.locator('#decision-status')).not_to_contain_text('Review stock hold')
    expect(page.locator('#confirm-open')).to_be_disabled()
    expect(page.locator('#decision-recheck')).to_be_visible()
    expect(page.locator('#confirm-dialog')).not_to_be_visible()
    page.unroute('**/actions/prepare**')
    page.locator('#decision-recheck').click()
    expect(page.locator('#confirm-open')).to_be_enabled()
    page.locator('#confirm-open').click()
    expect(page.locator('#confirm-dialog')).to_be_visible()
    expect(page.locator('#hold-confirm')).to_be_disabled()
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('editor', ['capture', 'correction'])
def test_record_read_closes_editor_and_resets_expanded_state(connected_browser, editor):
    """Red if a record reload hides an editor but leaves its button expanded."""
    page, c, _, errors = connected_browser
    checked(page, c)
    page.locator('#' + editor).click()
    expect(page.locator('#' + editor)).to_have_attribute('aria-expanded', 'true')
    page.evaluate('loadOwnedIncident(state.incident)')
    expect(page.locator('#' + editor + '-panel')).to_be_hidden()
    expect(page.locator('#' + editor)).to_have_attribute('aria-expanded', 'false')
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('kind', ['source', 'refresh'])
def test_next_task_clears_completed_action_hint_before_navigation(connected_browser, kind):
    """Red if a pending next operation leaves the old available-action instruction."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('#decision-status')).to_contain_text('Review stock hold')
    result = page.evaluate('''async kind=>{
      let release;
      const running=task(()=>new Promise(r=>release=r),kind);
      const during=$('decision-status').textContent;
      show('retail');release();await running;
      return {during,after:$('decision-status').textContent,focus:document.activeElement.id};
    }''', kind)
    assert 'Review stock hold' not in result['during']
    assert 'Review stock hold' not in result['after']
    assert result['focus'] == 'retail-title'
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('reason', ['source-review', 'workspace-block'])
def test_review_request_hint_uses_server_action_capability(connected_browser, reason):
    """Red if unrelated AI/source restrictions hide a server-permitted review request."""
    page, c, _, errors = connected_browser
    checked(page, c, review=True)
    observed = page.evaluate('''reason=>{
      if(reason==='source-review')state.evidence.source={blocked:true,mode:'LIVE',live_status:'NEVER_REQUESTED'};
      else state.workspaceBlock='UNRESOLVED_ATTEMPT';
      controls();
      return {available:state.capabilities.incident.action.available,
        enabled:!$('confirm-open').disabled,copy:completedCheckCopy()};
    }''', reason)
    assert observed['available'] and observed['enabled']
    assert 'Review follow-up request' in observed['copy']
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('transition', ['navigation', 'selection', 'expiry', 'new-task'])
def test_result_cue_is_removed_at_context_boundary(connected_browser, transition):
    """Red if completion attention survives navigation, another selection, expiry or task."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('.result-ready-cue')).to_have_count(1)
    page.evaluate('''async transition=>{
      if(transition==='navigation')show('retail');
      if(transition==='selection')clearReview();
      if(transition==='expiry')expire();
      if(transition==='new-task')await task(async()=>{},'refresh');
    }''', transition)
    expect(page.locator('.result-ready-cue')).to_have_count(0)
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('outcome', ['empty-return', 'failure', 'pending'])
def test_old_current_result_does_not_confirm_a_new_task(connected_browser, outcome):
    """Red if old current evidence alone announces or cues a newly unconfirmed check."""
    page, c, _, errors = connected_browser
    checked(page, c)
    expect(page.locator('.result-ready-cue')).to_have_count(1)
    observed = page.evaluate('''async outcome=>{
      let release;
      const op=task(async()=>{
        if(outcome==='pending')await new Promise(r=>release=r);
        if(outcome==='failure')throw new Error('Unconfirmed new operation');
      },'extraction');
      const during={cue:document.querySelectorAll('.result-ready-cue').length,
        text:$('decision-status').textContent};
      if(release)release();await op;
      return {during,cue:document.querySelectorAll('.result-ready-cue').length};
    }''', outcome)
    assert observed['during']['cue'] == 0 and observed['cue'] == 0
    assert 'completed' not in observed['during']['text'].lower()
    assert len(c[4]) == 2 and not errors

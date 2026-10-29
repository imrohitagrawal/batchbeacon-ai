"""Label-save attention only; controlled adapters, never live source/model proof."""
# ruff: noqa: F811
import os
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401
from tests.browser.test_workbench_recovery import page  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
def test_connected_saved_label_has_temporary_static_cue(connected_browser, width, motion):
    """Red if a real controlled save lacks its static cue, expiry, focus or explicit next step."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 1000})
    page.emulate_media(reduced_motion=motion)
    before = len(c[3][1].calls)
    page.locator('#start-sample').focus()
    page.locator('#start-sample').press('Enter')
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#capture-images img')).to_have_count(1)
    cue = page.locator('.evidence-panel > .label-ready-cue')
    expect(cue).to_have_count(1)
    expect(cue).to_have_attribute('aria-hidden', 'true')
    style = cue.evaluate('''el=>{
      const s=getComputedStyle(el);
      return {opacity:s.opacity,pointer:s.pointerEvents,duration:s.animationDuration,
        transform:s.transform,border:s.borderTopWidth,color:s.borderTopColor,frames:el.getAnimations()[0].effect.getKeyframes()
          .map(f=>f.opacity),position:s.position};
    }''')
    assert style == {'opacity': '1', 'pointer': 'none', 'duration': '1.2s',
                     'transform': 'none', 'border': '2px', 'color': 'rgb(23, 59, 117)',
                     'frames': ['1', '1'], 'position': 'absolute'}
    assert page.evaluate('document.activeElement.id') in ('evidence-title', 'label-status')
    expect(page.locator('#label-status')).to_contain_text('Next, extract and check')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    if capture_dir := os.environ.get('BATCHBEACON_CAPTURE_DIR'):
        destination = Path(capture_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / f'label-ready-{width}-{motion}.png'),
                        full_page=True)
    assert len(c[3][1].calls) > before and not c[4] and not errors
    expect(cue).to_have_count(0, timeout=5000)
    expect(page.locator('#check')).to_be_enabled()


SAVE = '''async ({kind,outcome})=>{
  state.csrf='test';state.expired=false;
  state.config={guidance:'OFF',sources:[],max_images:2,max_image_bytes:999};
  state.incident='case';state.evidence={current:false};state.captures=[];
  const available=outcome!=='unavailable';
  const cap={workspace:{extraction:{available,
    reason:available?'AVAILABLE':'ALLOWANCE_UNAVAILABLE'}},incident:{
      correction:{available:false},verification:{available:false},action:{available:false}}};
  state.capabilities=cap;
  let release,started,saved=false;const calls=[];
  const sent=new Promise(r=>started=r);
  window.fetch=async(url,options={})=>{
    calls.push({url,method:options.method||'GET'});
    if(url.startsWith('/samples/'))return new Response('synthetic');
    if(url.endsWith('/captures') && options.method==='POST'){
      started();return new Promise(r=>release=()=>{
        const failed=['rejected','unknown'].includes(outcome);saved=!failed;
        r(new Response(JSON.stringify(failed?{error:'save unavailable'}:
          {ready:true,captures:[{id:'image'}]}),
          {status:outcome==='rejected'?400:outcome==='unknown'?503:200}));
      });
    }
    const data=url==='/api/incidents'?{incident_id:'case'}:
      url.endsWith('/capabilities')?cap:
      url.endsWith('/evidence')?{current:false,latest_run_id:null}:
      url.endsWith('/captures')?{batches:saved?[{ready:true,captures:[{id:'image'}]}]:[]}:
      {actions:[]};
    return new Response(JSON.stringify(data));
  };
  const saving=kind==='sample'?task(startSample,'upload'):task(()=>upload([
    new File(['synthetic'],'label.png',{type:'image/png'})]),'capture');
  await sent;
  const pendingCue=document.querySelectorAll('.label-ready-cue').length;
  if(outcome==='navigate')show('retail');
  if(outcome==='stale'){state.selection++;state.incident='other';}
  if(outcome==='expired')expire();
  release();await saving;
  return {pendingCue,count:document.querySelectorAll('.label-ready-cue').length,
    next:$('label-status').textContent,disabled:$('check').disabled,
    focus:document.activeElement.id,calls};
}'''


@pytest.mark.parametrize('kind', ['sample', 'manual'])
@pytest.mark.parametrize('outcome', [
    'saved', 'unavailable', 'rejected', 'unknown', 'navigate', 'stale', 'expired',
])
def test_cue_requires_current_confirmed_visible_save(page, kind, outcome):
    """Red if pending/failed/stale saves cue, or a valid saved label never cues."""
    result = page.evaluate(SAVE, {'kind': kind, 'outcome': outcome})
    assert result['pendingCue'] == 0
    assert any(c['method'] == 'POST' and c['url'].endswith('/captures')
               for c in result['calls'])
    assert not any('/acquisitions' in c['url'] for c in result['calls'])
    assert result['count'] == (1 if outcome in ('saved', 'unavailable') else 0)
    if outcome == 'saved':
        assert not result['disabled'] and 'Next, extract and check' in result['next']
    if outcome == 'unavailable':
        assert result['disabled'] and 'extract and check' not in result['next'].lower()
    if outcome == 'navigate':
        assert result['focus'] == 'retail-title'


@pytest.mark.parametrize('clear', ['navigation', 'reset', 'expiry', 'new-work', 'case'])
def test_completed_cue_is_removed_when_context_changes(page, clear):
    """Red if a completed save's cue survives navigation, reset, expiry or new work."""
    result = page.evaluate(SAVE, {'kind': 'sample', 'outcome': 'saved'})
    assert result['count'] == 1
    page.evaluate('''async clear=>{
      if(clear==='navigation')show('retail');
      if(clear==='reset')clearReview();
      if(clear==='expiry')expire();
      if(clear==='new-work')await task(async()=>{},'queue');
      if(clear==='case')await loadIncident('other');
    }''', clear)
    expect(page.locator('.label-ready-cue')).to_have_count(0)


def test_repeated_saves_replace_instead_of_stacking_cues(page):
    """Red if a second confirmed save retains the first cue or creates duplicate cues."""
    first = page.evaluate(SAVE, {'kind': 'sample', 'outcome': 'saved'})
    assert first['count'] == 1
    page.evaluate("window.previousCue=document.querySelector('.label-ready-cue')")
    second = page.evaluate(SAVE, {'kind': 'sample', 'outcome': 'saved'})
    assert second['count'] == 1
    assert page.evaluate('!window.previousCue.isConnected')

"""Readable review arrival and owned Retail handoffs; controlled services only."""
# ruff: noqa: F811
import os
from datetime import timedelta
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import check_sample, connected_browser  # noqa: F401
from tests.browser.test_workbench_recovery import page  # noqa: F401

pytestmark = pytest.mark.browser


def capture(page, name):
    if destination := os.environ.get('BATCHBEACON_CAPTURE_DIR'):
        path = Path(destination)
        path.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(path / (name + '.png')), full_page=False)


@pytest.mark.parametrize('width', [1440, 390])
def test_retained_pixels_precede_explicit_extraction(connected_browser, width):
    """Red if Extract appears above the retained image, or a broken image passes inspection."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 700})
    page.locator('#start-sample').click()
    image = page.locator('#capture-images img')
    expect(image).to_have_count(1)
    pixels = image.evaluate('async img=>{await img.decode();return img.naturalWidth;}')
    assert pixels > 0
    expect(page.locator('#check')).to_be_enabled()
    bounds = page.evaluate("""()=>{const image=$('capture-images').querySelector('img');
      return {image:image.getBoundingClientRect().bottom,
        check:$('check').getBoundingClientRect().top,
        follows:!!(image.compareDocumentPosition($('check'))&Node.DOCUMENT_POSITION_FOLLOWING)};}""")
    capture(page, f'label-order-{width}')
    assert bounds['follows'] and bounds['image'] <= bounds['check'], bounds
    expect(page.locator('#label-status')).to_contain_text('Label saved')
    assert not c[4] and not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('motion', ['no-preference', 'reduce'])
@pytest.mark.parametrize('panel', ['decision', 'correction', 'capture'])
def test_arrival_paint_clears_text_and_native_controls(connected_browser, width, motion, panel):
    """Red if the arrival border paints over flush text or a focused native editor control."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 600})
    page.emulate_media(reduced_motion=motion)
    check_sample(page)
    if panel == 'decision':
        page.locator('#review-evidence').click()
        page.locator('#comparison-continue').click()
        selector, heading = '.decision', '#decision-title'
    else:
        page.locator('#' + panel).press('Enter')
        selector, heading = '#' + panel + '-panel', '#' + panel + '-panel h3'
    region = page.locator(selector)
    expect(region.locator(':scope > [aria-hidden=true]')).to_have_count(1)
    if motion == 'no-preference':
        capture(page, f'arrival-{panel}-{width}')
    for transient in [True, False]:
        if not transient:
            expect(region.locator(':scope > [aria-hidden=true]')).to_have_count(0, timeout=5000)
        clearance = page.locator(heading).evaluate("""el=>{
          const panel=el.closest('.decision,.inline-panel'),box=panel.getBoundingClientRect();
          const range=document.createRange();range.selectNodeContents(el);
          const text=range.getBoundingClientRect(),s=getComputedStyle(panel);
          const cue=panel.querySelector(':scope > [aria-hidden=true]');
          const outlined=s.outlineStyle!=='none',offset=parseFloat(s.outlineOffset)||0;
          let left=outlined?box.left-offset:-Infinity,right=outlined?box.right+offset:Infinity;
          let painted=outlined?parseFloat(s.outlineWidth):0;
          if(cue){const rect=cue.getBoundingClientRect();
            const width=parseFloat(getComputedStyle(cue).borderLeftWidth);
            left=Math.max(left,rect.left+width);right=Math.min(right,rect.right-width);painted=Math.max(painted,width);}
          return {text:text.left,left,right,textRight:text.right,painted};
        }""")
        assert clearance['painted'] > 0
        assert clearance['text'] >= clearance['left'] + 1, clearance
        assert clearance['textRight'] <= clearance['right'], clearance
    if panel == 'correction':
        select = page.locator('#correction-field').bounding_box()
        value = page.locator('#correction-value').bounding_box()
        assert select and value
        assert abs(select['x'] - value['x']) <= 1
        assert abs(select['width'] - value['width']) <= 1
        assert select['height'] >= 44 and value['height'] >= 44
        page.locator('#correction-field').press('ArrowDown')
        page.keyboard.press('Tab')
        expect(page.locator('#correction-value')).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(page.locator('#correction-field')).to_be_focused()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert len(c[4]) == 2 and not errors


def complete(page):
    check_sample(page)
    page.locator('#confirm-open').click()
    page.locator('#hold-consent').check()
    page.locator('#hold-confirm').click()
    expect(page.locator('#verdict-title')).to_have_text('Workspace action recorded')


@pytest.mark.parametrize('width', [1440, 390])
def test_completion_focuses_owned_detail_then_saved_next_step(connected_browser, width):
    """Red if completion lands on a heading/other row, or saved detail returns to label entry."""
    page, c, _, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 800})
    complete(page)
    incident = page.evaluate('state.incident')
    page.locator('#completed-queue').click()
    link = page.locator(f'#queue-rows a[href*="{incident}"]')
    expect(link).to_have_count(1)
    expect(link).to_have_text('View detail')
    expect(link).to_be_focused()
    assert link.evaluate("""el=>{const s=getComputedStyle(el);
      return s.outlineStyle!=='none' && parseFloat(s.outlineWidth)>=2;}""")
    capture(page, f'retail-detail-{width}')
    link.click()
    expect(page.locator('#decision-title')).to_be_focused()
    expect(page.locator('#decision-copy')).to_contain_text('This review is saved')
    expect(page.locator('#confirm-open')).to_be_hidden()
    page.locator('nav [data-view=retail]').click()
    expect(page.locator('#retail-title')).to_be_focused()
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('stage', ['label', 'comparison', 'decision'])
def test_detail_exposes_actual_remaining_review_task(connected_browser, stage):
    """Red if every saved case reopens at the label, or decision review is silently rewound."""
    page, c, _, errors = connected_browser
    if stage == 'label':
        page.locator('#start-sample').click()
        expect(page.locator('#check')).to_be_enabled()
    else:
        check_sample(page)
        if stage == 'decision':
            page.locator('#review-evidence').click()
            page.locator('#comparison-continue').click()
    page.locator('nav [data-view=retail]').click()
    expect(page.locator('#queue-rows a')).to_have_count(1)
    page.locator('#queue-rows a').click()
    target = {'label': 'evidence-title', 'comparison': 'comparison-title',
              'decision': 'decision-title'}[stage]
    expect(page.locator('#' + target)).to_be_focused()
    control = {'label': '#check', 'comparison': '#comparison-continue', 'decision': '#confirm-open'}
    expect(page.locator(control[stage])).to_be_visible()
    assert len(c[4]) == (0 if stage == 'label' else 2) and not errors


@pytest.mark.parametrize('intent', ['tab', 'pointer', 'page-down', 'wheel', 'touch', 'navigate'])
def test_delayed_retail_handoff_yields_to_later_user_intent(connected_browser, intent):
    """Red if a delayed handoff steals focus after the user has continued elsewhere."""
    page, c, _, errors = connected_browser
    complete(page)
    page.evaluate("""()=>{const original=window.fetch;window.fetch=(url,options)=>
      String(url).startsWith('/api/retail/queue')?new Promise(resolve=>{
        window.releaseQueue=()=>original(url,options).then(resolve);
        document.documentElement.dataset.queueHeld='true';}):original(url,options);}""")
    page.locator('#completed-queue').click()
    expect(page.locator('html')).to_have_attribute('data-queue-held', 'true')
    if intent == 'tab':
        page.keyboard.press('Tab')
    elif intent == 'pointer':
        page.locator('#queue-filter').click()
        page.keyboard.press('Escape')
    elif intent == 'page-down':
        page.keyboard.press('PageDown')
    elif intent == 'wheel':
        page.evaluate("""()=>document.addEventListener('wheel',()=>{
          document.documentElement.dataset.wheelObserved='true';},{once:true,capture:true})""")
        page.mouse.wheel(0, 250)
        expect(page.locator('html')).to_have_attribute('data-wheel-observed', 'true')
    elif intent == 'touch':
        page.locator('#queue-filter').dispatch_event('touchstart')
    else:
        page.locator('nav [data-view=workbench]').click()
    page.evaluate('window.laterFocus=document.activeElement')
    page.evaluate('window.releaseQueue()')
    if intent != 'navigate':
        expect(page.locator('#queue-rows a')).to_have_count(1)
    assert page.evaluate('document.activeElement===window.laterFocus')
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('outcome', ['reverse', 'stale-error', 'ordered', 'current-error'])
def test_queue_only_current_request_publishes_rows_and_status(page, outcome):
    """Red if an older response/error replaces a newer filter, or a current failure is hidden."""
    result = page.evaluate("""async outcome=>{
      state.csrf='test';state.expired=false;state.sessionError=null;
      state.config={refresh_interval_seconds:0};state.queueReadAt=0;
      show('retail');const pending=[],calls=[];
      const data=name=>({snapshot:{rows:[{incident_id:name,product_name:name,
        observation_revision:1,jurisdiction:'SG',stage:'LABEL_READY',
        category:'MATCHED_HOLD_FOR_REVIEW',current:true}],generated_at:'2026-10-18T08:00:00Z',
        category_counts:{MATCHED_HOLD_FOR_REVIEW:1}},visible_count:1,visible_incident_ids:[name],
        saved_evidence:{state:'AVAILABLE'},new_verification:{state:'AVAILABLE'}});
      state.queue=data('saved');window.fetch=(url,options={})=>new Promise((resolve,reject)=>{
        calls.push({url,method:options.method||'GET'});pending.push({resolve:name=>resolve(
          new Response(JSON.stringify(data(name)),
            {headers:{'Content-Type':'application/json'}})),reject});});
      $('queue-filter').value='ALL';const first=refresh().catch(()=>{});
      $('queue-filter').value='NEEDS_ATTENTION';const second=refresh().catch(()=>{});
      if(outcome==='ordered'||outcome==='current-error'){
        pending[0].resolve('old');await first;
        if(outcome==='current-error')pending[1].reject(new Error('current unavailable'));
        else pending[1].resolve('new');await second;
      }else{pending[1].resolve('new');await second;
        if(outcome==='reverse')pending[0].resolve('old');
        else pending[0].reject(new Error('older unavailable'));await first;}
      return {filter:$('queue-filter').value,row:state.queue.snapshot.rows[0].product_name,
        status:$('queue-status').textContent,rows:state.queue.snapshot.rows.length,calls};
    }""", outcome)
    assert result['rows'] == 1 and len(result['calls']) == 2
    assert all(call['method'] == 'GET' and '/api/retail/queue?' in call['url']
               for call in result['calls'])
    assert result['filter'] == 'NEEDS_ATTENTION'
    assert result['row'] == ('saved' if outcome == 'current-error' else 'new'), result
    assert ('Refresh unavailable' in result['status']) == (outcome == 'current-error'), result


@pytest.mark.parametrize('outcome', ['stale-success', 'stale-error', 'cached-filter'])
def test_retail_return_replaces_a_snapshot_for_another_filter(connected_browser, outcome):
    """Red if cache/filter mismatch or an interrupted refresh strands the old rows on return."""
    page, c, _, errors = connected_browser
    complete(page)
    page.locator('#completed-queue').click()
    expect(page.locator('#queue-rows [role=listitem]')).to_have_count(1)
    page.evaluate("""()=>{state.config.refresh_interval_seconds=0;
      const original=window.fetch;window.queuePending=[];
      window.fetch=(url,options)=>String(url).startsWith('/api/retail/queue')?
        new Promise((resolve,reject)=>{
          queuePending.push({finish:()=>original(url,options).then(resolve,reject),
            fail:()=>reject(new Error('older queue response unavailable'))});
          document.documentElement.dataset.queueWaits=String(queuePending.length);
        }):original(url,options);}""")
    if outcome == 'cached-filter':
        page.locator('nav [data-view=workbench]').click()
        page.evaluate("$('queue-filter').value='NEEDS_ATTENTION'")
    else:
        page.locator('#queue-filter').select_option('NEEDS_ATTENTION')
        expect(page.locator('html')).to_have_attribute('data-queue-waits', '1')
        page.locator('nav [data-view=workbench]').click()
    page.locator('nav [data-view=retail]').click()
    expected = '1' if outcome == 'cached-filter' else '2'
    expect(page.locator('html')).to_have_attribute('data-queue-waits', expected)
    # Advance the injected server clock past its real refresh gate, not the browser clock.
    c[3][5][0] += timedelta(seconds=3)
    page.evaluate('queuePending.at(-1).finish()')
    expect(page.locator('#queue-rows [role=listitem]')).to_have_count(0)
    expect(page.locator('#queue-rows')).to_contain_text('No incidents match this filter')
    if outcome != 'cached-filter':
        c[3][5][0] += timedelta(seconds=3)
        page.evaluate('queuePending[0].' + ('fail()' if outcome == 'stale-error' else 'finish()'))
    expect(page.locator('#queue-status')).to_have_text(
        'Manual refresh complete. No model call was made.')
    assert page.evaluate("state.queueFilter===$('queue-filter').value && !state.queueDirty")
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('kind', ['blocked-source', 'missing-capability', 'historical-action',
                                 'not-listed', 'unresolved', 'recorded', 'stale-acquisition',
                                 'superseded', 'not-listed-decided', 'unresolved-not-listed',
                                 'recorded-not-listed'])
def test_detail_state_collisions_keep_guidance_and_controls_honest(connected_browser, kind):
    """Red if detail always lands at label entry or promises an action from blocked evidence."""
    page, c, _, errors = connected_browser
    complete(page)
    result = page.evaluate("""kind=>{
      state.reviewAt='comparison';
      if(!['recorded','recorded-not-listed'].includes(kind)){
        if(kind==='historical-action')state.actions=state.actions.map(a=>({...a,current:false,requires_renewed_review:true}));
        else state.actions=[];
        state.capabilities.incident.action.available=false;
      }
      if(kind==='blocked-source'){
        state.evidence.current=false;
        state.evidence.source={...state.evidence.source,blocked:true,refresh_outcome:'CHANGED'};
      }
      if(kind==='historical-action')state.evidence.current=false;
      if(kind==='missing-capability')state.capabilities=null;
      if(kind==='not-listed')state.evidence.result.verdict='NOT_LISTED_IN_CHECKED_NOTICES';
      if(kind==='unresolved')state.acquisition={state:'INCOMPLETE',current:false,reconciliation_required:true};
      if(['stale-acquisition','superseded'].includes(kind)){
        state.evidence.current=false;
        state.acquisition={state:kind==='superseded'?'SUPERSEDED':'STALE',current:false};
      }
      if(kind.includes('not-listed')){
        state.evidence.result.verdict='NOT_LISTED_IN_CHECKED_NOTICES';state.reviewAt='decision';
      }
      if(kind==='unresolved-not-listed')state.acquisition={state:'INCOMPLETE',
        current:false,reconciliation_required:true};
      render();revealReviewTask();
      return {focus:document.activeElement.id,disabled:$('confirm-open').disabled,
        hidden:$('confirm-open').hidden,copy:$('verdict-copy').textContent+' '+
        $('decision-copy').textContent+' '+$('capability-help').textContent};
    }""", kind)
    decision = ('unresolved', 'recorded', 'unresolved-not-listed', 'recorded-not-listed')
    destination = 'decision-title' if kind in decision else 'comparison-title'
    assert result['focus'] == destination
    assert result['disabled'] or result['hidden']
    if kind in ('not-listed', 'not-listed-decided'):
        assert 'not safety' in result['copy']
    elif kind == 'recorded':
        assert 'This review is saved' in result['copy']
    elif kind == 'recorded-not-listed':
        assert 'No hold is supported' in result['copy']
    elif kind in ('unresolved', 'unresolved-not-listed'):
        assert 'unconfirmed' in result['copy']
    assert len(c[4]) == 2 and not errors


def test_multiple_decoded_images_stay_before_unavailable_extraction(connected_browser):
    """Red if only one retained image precedes Extract or unavailable extraction is enabled."""
    page, c, _, errors = connected_browser
    origin = page.evaluate('location.origin')
    files = []
    for sample in ['sfa-a', 'sfa-b']:
        response = page.request.get(origin + '/samples/' + sample + '.png')
        assert response.ok
        files.append({'name': sample + '.png', 'mimeType': 'image/png', 'buffer': response.body()})
    page.evaluate("""async()=>{
      const created=await api('/api/incidents',{method:'POST',operation:key()});
      await loadOwnedIncident(created.incident_id);}""")
    page.locator('#capture').click()
    page.locator('#capture-file').set_input_files(files)
    page.locator('#upload').click()
    expect(page.locator('#capture-images img')).to_have_count(2)
    for image in page.locator('#capture-images img').all():
        assert image.evaluate('async img=>{await img.decode();return img.naturalWidth;}') > 0
        assert image.evaluate("""img=>img.getBoundingClientRect().bottom<=
          $('check').getBoundingClientRect().top""")
    page.evaluate("state.capabilities.workspace.extraction.available=false;controls();")
    expect(page.locator('#check')).to_be_disabled()
    expect(page.locator('#label-status')).to_contain_text('Label saved')
    assert not c[4] and not errors


@pytest.mark.parametrize('outcome', ['delayed', 'failed'])
def test_image_loading_failure_does_not_invent_pixels_or_start_ai(connected_browser, outcome):
    """Red if Extract precedes a pending/failed image or its load starts an AI check."""
    page, c, _, errors = connected_browser
    held = []
    page.route('**/api/incidents/*/captures/*', lambda route: held.append(route))
    with page.expect_request(lambda request: '/captures/' in request.url):
        page.locator('#start-sample').click()
    image = page.locator('#capture-images img')
    expect(image).to_have_count(1)
    expect(page.locator('#check')).to_be_enabled()
    assert held
    dimensions = image.evaluate('img=>({width:img.width,height:img.height,complete:img.complete})')
    assert dimensions['width'] > 0 and dimensions['height'] > 0 and not dimensions['complete']
    assert image.evaluate("""img=>img.getBoundingClientRect().bottom<=
      $('check').getBoundingClientRect().top""")
    if outcome == 'delayed':
        response = page.request.get(held[0].request.url)
        assert response.ok
        held[0].fulfill(status=200, content_type='image/png', body=response.body())
        assert image.evaluate('async img=>{await img.decode();return img.naturalWidth;}') > 0
    else:
        held[0].abort('failed')
        expect(image).to_have_js_property('complete', True)
        assert image.evaluate('img=>img.naturalWidth') == 0
    expect(page.locator('#label-status')).to_contain_text('Label saved')
    expect(page.locator('#capture-images a')).to_be_visible()
    assert page.locator('#capture-images a').get_attribute('href') == page.locator(
        '#inspect-retained-label').get_attribute('href')
    assert not c[4] and not errors


def test_image_ready_but_capability_unavailable_has_no_automatic_check(connected_browser):
    """Red if moving the explicit Extract control ignores a refused server capability."""
    page, c, _, errors = connected_browser

    def unavailable(route):
        response = route.fetch()
        data = response.json()
        data['workspace']['extraction'].update(available=False, reason='ALLOWANCE_UNAVAILABLE')
        route.fulfill(response=response, json=data)

    page.route('**/api/incidents/*/capabilities', unavailable)
    page.locator('#start-sample').click()
    image = page.locator('#capture-images img')
    expect(image).to_have_count(1)
    assert image.evaluate('async img=>{await img.decode();return img.naturalWidth;}') > 0
    expect(page.locator('#check')).to_be_disabled()
    assert image.evaluate("""img=>img.getBoundingClientRect().bottom<=
      $('check').getBoundingClientRect().top""")
    assert not c[4] and not errors

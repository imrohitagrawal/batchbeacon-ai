"""Journey audit regressions. Controlled responses only; no paid inference."""
# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401
from tests.browser.test_workbench_recovery import page  # noqa: F401

pytestmark = pytest.mark.browser


def test_saved_label_has_truthful_next_stage(connected_browser):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    expect(page.locator('#verdict-title')).to_have_text('Label ready')
    expect(page.locator('#label-status')).to_contain_text('No AI check has run')
    assert not c[4] and not errors


@pytest.mark.parametrize('failure', [False, True])
def test_expiry_wins_over_delayed_incident_reads(page, failure):
    result = page.evaluate('''async failure=>{
      state.csrf='test';state.config={guidance:'OFF'};
      let release;const wait=new Promise(r=>release=r);
      window.fetch=async url=>{await wait;return new Response(JSON.stringify(
        url.endsWith('/evidence')?{current:false,latest_run_id:null}:
        url.endsWith('/captures')?{batches:[]}:{actions:[]}),{status:failure?503:200});};
      const loading=task(()=>loadIncident('case'));
      expire();release();await loading;
      return {title:$('verdict-title').textContent,status:$('app-status').textContent,
        evidence:state.evidence,images:$('capture-images').textContent};
    }''', failure)
    assert result['title'] == 'Guest access expired'
    assert 'expired' in result['status']
    assert result['evidence'] is None
    assert 'expired' in result['images']


def test_workspace_block_is_read_without_latest_case_run(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.config={guidance:'OFF'};
      const calls=[];window.fetch=async url=>{calls.push(url);
        return new Response(JSON.stringify(url.endsWith('/capabilities')?{
          workspace:{extraction:{available:false,reason:'UNRESOLVED_ATTEMPT'}},
          incident:{correction:{available:false},verification:{available:false},action:{available:false}}}:
          url.endsWith('/evidence')?{current:false,latest_run_id:null}:
          url.endsWith('/captures')?{batches:[{ready:true,captures:[{id:'image'}]}]}:
          {actions:[]}));};
      await loadIncident('new-case');
      return {disabled:$('check').disabled, recheck:$('refresh-acquisition').hidden,calls};
    }''')
    assert result['disabled'] and not result['recheck']
    assert any(url.endswith('/capabilities') for url in result['calls'])


def test_explicit_navigation_updates_fragment_and_focus(connected_browser):
    page, _, _, errors = connected_browser
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#verdict-title').scroll_into_view_if_needed()
    page.locator('nav [data-view=guidance]').click()
    expect(page).to_have_url(page.url.split('#')[0]+'#guidance')
    expect(page.locator('#guidance-title')).to_be_focused()
    box = page.locator('#guidance-title').bounding_box()
    assert 0 <= box['y'] < 300
    page.go_back()
    expect(page.locator('#workbench')).to_be_visible()
    assert not errors


def test_rejected_second_upload_cannot_reuse_first_label(connected_browser):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.route('**/api/incidents/*/captures', lambda route: route.fulfill(
        status=400, content_type='application/json', body='{"error":"image_rejected"}'
    ) if route.request.method == 'POST' else route.continue_())
    page.locator('#start-sample').click()
    expect(page.locator('#sample-status')).to_contain_text('image rejected')
    expect(page.locator('#check')).to_be_disabled()
    expect(page.locator('#capture-images img')).to_have_count(0)
    expect(page.locator('#label-status')).not_to_contain_text('Label saved')
    assert not c[4] and not errors


def test_extraction_refusal_is_terminal_and_visible(connected_browser):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.route('**/api/incidents/*/acquisitions', lambda route: route.fulfill(
        status=409,content_type='application/json',body='{"error":"allowance_unavailable"}'))
    page.locator('#check').click()
    expect(page.locator('#verdict-title')).to_have_text('Check could not start')
    expect(page.locator('#decision-status')).to_contain_text('allowance unavailable')
    assert not c[4] and not errors


def test_late_extraction_result_stays_with_original_case(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.config={guidance:'OFF'};state.incident='original';
      state.evidence={latest_observation_revision:0};state.captures=[{id:'label'}];
      let release;window.fetch=()=>new Promise(r=>release=r);
      const work=acquire();state.incident='new-case';state.selection++;
      state.acquisition=null;state.evidence={current:false};state.captures=[];
      release(new Response(JSON.stringify({state:'FAILED',run_id:'original-run',current:false})));
      await work;return {incident:state.incident,acquisition:state.acquisition};
    }''')
    assert result == {'incident':'new-case','acquisition':None}


def test_late_guidance_error_cannot_overwrite_new_case(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.incident='old';let release;
      window.fetch=()=>new Promise(r=>release=r);
      const read=loadLearning();state.incident='new';state.selection++;
      text('learning-counts','New selected records');
      release(new Response('{}',{status:503}));try{await read;}catch{}
      return $('learning-counts').textContent;
    }''')
    assert result == 'New selected records'


def test_upload_fingerprint_delay_cannot_retarget_new_case(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.incident='old';state.config={max_images:2,max_image_bytes:999};
      let release;captureFiles=()=>new Promise(r=>release=r);
      const calls=[];window.fetch=async url=>{calls.push(url);return new Response('{}');};
      const uploading=upload([new File(['data'],'label.png',{type:'image/png'})]);
      state.incident='new';state.selection++;release([]);await uploading;
      return {calls,pending:state.pending};
    }''')
    assert result == {'calls':[], 'pending':None}


def test_recovery_reply_cannot_reopen_old_case(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.incident='old';state.config={guidance:'OFF'};
      state.pending={kind:'acquisition',incident:'old',operation:'original'};
      let release;const calls=[];window.fetch=url=>{calls.push(url);
        return new Promise(r=>release=r);};
      const work=recover();state.incident='new';state.selection++;
      release(new Response(JSON.stringify({state:'COMPLETE'})));await work;
      return {incident:state.incident,calls};
    }''')
    assert result['incident'] == 'new' and len(result['calls']) == 1


def test_operation_error_after_reopening_same_case_is_discarded(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.incident='case';state.config={guidance:'OFF'};
      let reject;const work=task(()=>new Promise((r,j)=>reject=j));
      state.incident='other';state.selection++;state.incident='case';state.selection++;
      text('app-status','Freshly reopened case');reject(new Error('Old error'));await work;
      return $('app-status').textContent;
    }''')
    assert result == 'Freshly reopened case'


@pytest.mark.parametrize('reason', ['UNRESOLVED_ATTEMPT','ALLOWANCE_UNAVAILABLE',None])
def test_label_ready_feedback_explains_unavailable_check_at_action(page, reason):
    result = page.evaluate('''reason=>{
      state.csrf='test';state.config={guidance:'OFF'};state.incident='case';
      state.captures=[{id:'label'}];state.evidence={current:false};
      state.workspaceBlock=reason==='UNRESOLVED_ATTEMPT'?reason:null;
      state.capabilities=reason?{workspace:{extraction:{available:false,reason}},
        incident:{correction:{available:false},verification:{available:false},
          action:{available:false}}}:null;
      render();return {copy:$('label-status').textContent,disabled:$('check').disabled};
    }''', reason)
    assert result['disabled']
    assert 'Next, extract and check' not in result['copy']
    assert {None:'could not be confirmed','UNRESOLVED_ATTEMPT':'paused',
            'ALLOWANCE_UNAVAILABLE':'allowance is unavailable'}[reason] in result['copy']


@pytest.mark.parametrize('email', [None, 'rohit@stackclimb.com'])
def test_support_contact_opens_only_an_explicit_mail_link(connected_browser, email):
    from batchbeacon.workbench import SupportContact
    page, c, _, errors = connected_browser
    def configuration(route):
        response = route.fetch()
        data = response.json()
        data['support'] = SupportContact(email=email).public_view()
        route.fulfill(response=response, json=data)
    page.route('**/api/workbench/config', configuration)
    page.reload()
    expect(page.locator('#start-sample')).to_be_enabled()
    page.evaluate("state.workspaceBlock='UNRESOLVED_ATTEMPT';render();")
    page.locator('#operator-help summary').click()
    if email:
        link = page.locator('#support-contact a')
        expect(link).to_have_text('Email the project operator: '+email)
        expect(link).to_have_attribute('href',
            'mailto:rohit@stackclimb.com?subject=BatchBeacon%20support')
        expect(page.locator('#operator-help')).to_contain_text('No email is sent automatically')
    else:
        expect(page.locator('#support-contact')).to_have_text(
            'No public support channel is configured.')
        expect(page.locator('#support-contact a')).to_have_count(0)
    assert not c[4] and not errors

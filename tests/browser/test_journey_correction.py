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
    expect(page.locator('#label-status')).to_contain_text(
        'Saving a label does not start an AI check')
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
      state.workspaceBlock=['UNRESOLVED_ATTEMPT','ACTIVE_REQUEST'].includes(reason)?reason:null;
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


@pytest.mark.parametrize('kind', ['upload', 'capture', 'extraction', 'status', 'verification',
                                 'action', 'queue', 'guidance', 'correction', 'refresh'])
@pytest.mark.parametrize('failure', [False, True])
def test_pending_status_remains_announcable_while_duplicate_work_is_blocked(page, kind, failure):
    result = page.evaluate('''async ({kind,failure})=>{
      state.csrf='synthetic';state.config={guidance:'OFF'};
      let release, reject, dispatches=0;
      const work=task(async()=>{dispatches++;await new Promise((r,j)=>{release=r;reject=j;});
        message('Operation completed.');},kind);
      const el=$(operations[kind].region);
      const pending={text:el.textContent,visible:!el.hidden,role:el.getAttribute('role'),
        busy:!!el.closest('[aria-busy="true"]'),
        buttons:operations[kind].buttons.map(id=>({disabled:$(id).disabled,
          busy:$(id).getAttribute('aria-busy')}))};
      await task(()=>{dispatches++;},kind);
      if(failure)reject(new Error('Operation refused.'));else release();await work;
      return {pending,dispatches,terminal:el.textContent,
        busy:!!el.closest('[aria-busy="true"]'),spinner:el.dataset.busy};
    }''', {'kind': kind, 'failure': failure})
    assert result['pending']['visible'] and result['pending']['text']
    assert result['pending']['role'] == 'status'
    assert not result['pending']['busy']
    assert all(button['disabled'] and button['busy'] == 'true'
               for button in result['pending']['buttons'])
    assert result['dispatches'] == 1
    assert result['terminal'] == ('Operation refused.' if failure else 'Operation completed.')
    assert not result['busy'] and result['spinner'] != 'true'


@pytest.mark.parametrize('width', [390, 1280])
@pytest.mark.parametrize('kind', ['sample', 'manual'])
@pytest.mark.parametrize('reason', ['AVAILABLE', 'ALLOWANCE_UNAVAILABLE',
                                   'UNRESOLVED_ATTEMPT', 'ACTIVE_REQUEST',
                                   'ACQUISITION_LIMIT', None])
def test_upload_handoff_matches_available_next_action(page, width, kind, reason):
    """Both actual upload paths must not direct users to a disabled AI action."""
    page.set_viewport_size({'width': width, 'height': 844})
    result = page.evaluate('''async ({kind,reason})=>{
      state.csrf='test';state.config={guidance:'OFF',max_images:2,max_image_bytes:999};
      state.incident='case';state.evidence={current:false};
      const cap=reason?{workspace:{extraction:{available:reason==='AVAILABLE',reason}},
        incident:{correction:{available:false},verification:{available:false},
          action:{available:false}}}:null;
      state.capabilities=cap;
      state.workspaceBlock=['UNRESOLVED_ATTEMPT','ACTIVE_REQUEST'].includes(reason)?reason:null;
      const calls=[];let saved=false;
      window.fetch=async (url,options={})=>{
        calls.push({url,method:options.method||'GET'});
        if(url.startsWith('/samples/'))return new Response('synthetic');
        let data;
        if(url==='/api/incidents')data={incident_id:'case'};
        else if(url.endsWith('/capabilities'))data=cap;
        else if(url.endsWith('/evidence'))data={current:false,latest_run_id:null};
        else if(url.endsWith('/actions'))data={actions:[]};
        else if(url.endsWith('/captures')){
          if(options.method==='POST'){saved=true;data={ready:true,captures:[{id:'image'}]};}
          else data={batches:saved?[{ready:true,captures:[{id:'image'}]}]:[]};
        }else throw new Error('Unexpected request '+url);
        return new Response(JSON.stringify(data));
      };
      if(kind==='sample')await task(startSample,'upload');
      else await task(()=>upload([
        new File(['synthetic'],'label.png',{type:'image/png'})]),'capture');
      return {global:$('app-status').textContent,
        adjacent:$(kind==='sample'?'sample-status':'capture-status').textContent,
        label:$('label-status').textContent,disabled:$('check').disabled,
        recheckVisible:!$('refresh-acquisition').hidden,
        recheckDisabled:$('refresh-acquisition').disabled,
        focus:document.activeElement.id,calls};
    }''', {'kind': kind, 'reason': reason})
    assert result['global'] == result['adjacent'] == result['label']
    assert result['global'].startswith('Label saved.')
    assert not any('/acquisitions' in call['url'] for call in result['calls'])
    if reason == 'AVAILABLE':
        assert not result['disabled']
        assert 'Next, extract and check' in result['global']
    else:
        assert result['disabled']
        assert 'extract and check' not in result['global'].lower()
        assert result['recheckVisible'] and not result['recheckDisabled']
        assert result['focus'] == 'evidence-title'
        expect(page.locator('#label-status')).to_be_in_viewport()
        expect(page.locator('#refresh-acquisition')).to_be_in_viewport()
        assert {None: 'could not be confirmed',
                'ALLOWANCE_UNAVAILABLE': 'Recheck does not start an AI request',
                'UNRESOLVED_ATTEMPT': 'does not settle the request',
                'ACTIVE_REQUEST': 'does not settle the request',
                'ACQUISITION_LIMIT': 'exhausted'}[reason] in result['global']


@pytest.mark.parametrize('kind', ['sample', 'manual'])
@pytest.mark.parametrize('failure', [False, True])
def test_late_upload_after_same_case_reopen_preserves_current_state(page, kind, failure):
    result = page.evaluate('''async ({kind,failure})=>{
      state.csrf='test';state.config={guidance:'OFF',max_images:2,max_image_bytes:999};
      state.incident='case';state.evidence={current:false};
      let release, started;const sent=new Promise(r=>started=r);let posts=0;
      window.fetch=async (url,options={})=>{
        if(url.startsWith('/samples/'))return new Response('synthetic');
        if(url.endsWith('/captures') && options.method==='POST'){
          posts++;started();return new Promise(r=>release=r);
        }
        const data=url==='/api/incidents'?{incident_id:'case'}:
          url.endsWith('/captures')?{batches:[]}:
          url.endsWith('/capabilities')?null:
          url.endsWith('/evidence')?{current:false,latest_run_id:null}:{actions:[]};
        return new Response(JSON.stringify(data));
      };
      const work=kind==='sample'?task(startSample,'upload'):task(()=>upload([
        new File(['synthetic'],'label.png',{type:'image/png'})]),'capture');
      await sent;
      state.incident='another';state.selection++;
      state.incident='case';state.selection++;
      state.captures=[{id:'current-capture'}];
      pending({kind:'capture',incident:'case',operation:'current-key'});
      operationStatus('label-status','Current label status');
      operationStatus('capture-status','Current capture status');
      text('app-status','Current global status');
      $('evidence-title').focus();
      release(new Response(JSON.stringify(failure?{error:'rejected'}:
        {ready:true,captures:[{id:'stale-capture'}]}),{status:failure?400:200}));
      await work;
      return {captures:state.captures,pending:state.pending?.operation,
        label:$('label-status').textContent,capture:$('capture-status').textContent,
        global:$('app-status').textContent,focus:document.activeElement.id,posts};
    }''', {'kind': kind, 'failure': failure})
    assert result == {'captures': [{'id': 'current-capture'}], 'pending': 'current-key',
                      'label': 'Current label status', 'capture': 'Current capture status',
                      'global': 'Current global status', 'focus': 'evidence-title', 'posts': 1}


@pytest.mark.parametrize('kind', ['sample', 'manual'])
@pytest.mark.parametrize('available', [False, True])
def test_saved_receipt_cannot_contradict_refreshed_availability(page, kind, available):
    result = page.evaluate('''async ({kind,available})=>{
      state.csrf='test';state.config={guidance:'OFF',max_images:2,max_image_bytes:999};
      state.incident='case';state.evidence={current:false};
      let enabled=!available,saved=false;const calls=[];
      const capabilities=()=>({workspace:{extraction:{available:enabled,
        reason:enabled?'AVAILABLE':'ALLOWANCE_UNAVAILABLE'}},incident:{
        correction:{available:false},verification:{available:false},action:{available:false}}});
      state.capabilities=capabilities();
      window.fetch=async(url,options={})=>{
        calls.push({url,method:options.method||'GET'});
        if(url.startsWith('/samples/'))return new Response('synthetic');
        let data;
        if(url==='/api/incidents')data={incident_id:'case'};
        else if(url.endsWith('/capabilities'))data=capabilities();
        else if(url.endsWith('/evidence'))data={current:false,latest_run_id:null};
        else if(url.endsWith('/actions'))data={actions:[]};
        else if(url.endsWith('/captures')){
          if(options.method==='POST'){saved=true;data={ready:true,captures:[{id:'image'}]};}
          else data={batches:saved?[{ready:true,captures:[{id:'image'}]}]:[]};
        }else throw new Error('Unexpected request '+url);
        return new Response(JSON.stringify(data));
      };
      if(kind==='sample')await task(startSample,'upload');
      else await task(()=>upload([
        new File(['synthetic'],'label.png',{type:'image/png'})]),'capture');
      const id=kind==='sample'?'sample-status':'capture-status';
      const before=$(id).textContent;
      enabled=available;await task(recheck,'status');
      return {before,receipt:$(id).textContent,hidden:$(id).hidden,
        label:$('label-status').textContent,disabled:$('check').disabled,
        focus:document.activeElement.id,calls};
    }''', {'kind': kind, 'available': available})
    assert result['before'].startswith('Label saved.')
    assert not result['receipt']
    assert result['disabled'] is not available
    assert ('Next, extract and check' in result['label']) is available
    assert result['focus'] == 'verdict-title'
    assert sum(c['method'] == 'POST' and c['url'].endswith('/captures')
               for c in result['calls']) == 1
    assert not any('/acquisitions' in c['url'] for c in result['calls'])


@pytest.mark.parametrize('response_status', [400, 503])
def test_recheck_preserves_sample_upload_error_or_unknown(page, response_status):
    result = page.evaluate('''async status=>{
      state.csrf='test';state.config={guidance:'OFF',max_images:2,max_image_bytes:999};
      state.incident='case';state.evidence={current:false};let posts=0;
      window.fetch=async(url,options={})=>{
        if(url.startsWith('/samples/'))return new Response('synthetic');
        if(url.endsWith('/captures') && options.method==='POST'){
          posts++;return new Response(JSON.stringify({error:'upload_not_confirmed'}),{status});
        }
        const data=url==='/api/incidents'?{incident_id:'case'}:
          url.endsWith('/captures')?{batches:[]}:
          url.endsWith('/evidence')?{current:false,latest_run_id:null}:
          url.endsWith('/capabilities')?null:{actions:[]};
        return new Response(JSON.stringify(data));
      };
      await task(startSample,'upload');
      const before=$('sample-status').textContent,pendingBefore=state.pending?.operation;
      await task(recheck,'status');
      return {before,after:$('sample-status').textContent,posts,
        pendingBefore,pendingAfter:state.pending?.operation};
    }''', response_status)
    assert result['before'] == result['after'] == 'upload not confirmed'
    assert result['posts'] == 1
    if response_status == 503:
        assert result['pendingBefore'] == result['pendingAfter']
        assert result['pendingAfter']
    else:
        assert result.get('pendingAfter') is None


def test_sample_receipt_refreshes_after_leaving_during_save(page):
    result = page.evaluate('''async()=>{
      state.csrf='test';state.config={guidance:'OFF',max_images:2,max_image_bytes:999};
      state.incident='case';state.evidence={current:false};
      let release,started,saved=false,available=false;let posts=0,acquisitions=0;
      const sent=new Promise(r=>started=r);
      window.fetch=async(url,options={})=>{
        if(url.startsWith('/samples/'))return new Response('synthetic');
        if(url.includes('/acquisitions'))acquisitions++;
        if(url.endsWith('/captures') && options.method==='POST'){
          posts++;started();return new Promise(r=>release=()=>{
            saved=true;r(new Response(JSON.stringify({ready:true,captures:[{id:'image'}]})));
          });
        }
        const data=url==='/api/incidents'?{incident_id:'case'}:
          url.endsWith('/evidence')?{current:false,latest_run_id:null}:
          url.endsWith('/captures')?{batches:saved?[{ready:true,captures:[{id:'image'}]}]:[]}:
          url.endsWith('/capabilities')?{workspace:{extraction:{available,
            reason:available?'AVAILABLE':'ALLOWANCE_UNAVAILABLE'}},incident:{
            correction:{available:false},verification:{available:false},action:{available:false}}}:
          {actions:[]};
        return new Response(JSON.stringify(data));
      };
      const saving=task(startSample,'upload');await sent;
      show('retail');release();await saving;
      const focus=document.activeElement.id;
      show('workbench');available=true;await task(recheck,'status');
      return {focus,receipt:$('sample-status').textContent,disabled:$('check').disabled,
        label:$('label-status').textContent,posts,acquisitions};
    }''')
    assert result['focus'] == 'retail-title'
    assert not result['receipt']
    assert not result['disabled']
    assert 'Next, extract and check' in result['label']
    assert result['posts'] == 1 and result['acquisitions'] == 0

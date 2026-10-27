"""Actual socket streaming plus controlled terminal-envelope browser regressions."""
# ruff: noqa: F811
import asyncio

import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import connected_browser  # noqa: F401
from tests.browser.test_workbench_recovery import page  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.mark.parametrize('connected_browser', [{'progress_response_enabled': True,
    'progress_interval_seconds': .02}], indirect=True)
def test_real_socket_progress_precedes_final_and_ui_waits(connected_browser, monkeypatch):
    page, c, _, errors = connected_browser
    original = c[0].acquire
    async def delayed(*args):
        await asyncio.sleep(.2)
        return await original(*args)
    monkeypatch.setattr(c[0], 'acquire', delayed)
    page.evaluate('''()=>{
      window.progressFrames=[];const realFetch=window.fetch;
      window.fetch=async(...args)=>{
        const r=await realFetch(...args);
        if(!r.headers.get('Content-Type')?.startsWith('application/vnd.batchbeacon'))return r;
        const [observed,consumer]=r.body.tee();
        window.framesComplete=(async()=>{const reader=observed.getReader();
          for(;;){const {value,done}=await reader.read();if(done)break;
            progressFrames.push({text:new TextDecoder().decode(value),
              title:$('verdict-title').textContent,disabled:$('check').disabled});}})();
        return new Response(consumer,{status:r.status,headers:r.headers});
      };
    }''')
    page.get_by_role('button', name='Use this label', exact=True).click()
    expect(page.locator('#check')).to_be_enabled()
    page.get_by_role('button', name='Extract and check', exact=True).click()
    expect(page.locator('#verdict-title')).to_have_text('Matches this recall', timeout=20000)
    frames = page.evaluate('async()=>{await framesComplete;return progressFrames;}')
    assert len(frames) > 1 and 'preparing' in frames[0]['text']
    assert frames[0]['disabled'] and frames[0]['title'] == 'Checking label'
    assert 'acquisition-stages-v2' in ''.join(f['text'] for f in frames)
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('kind', ['success', 'known_error', 'expiry', 'unknown',
    'wrong_protocol', 'invalid_status', 'invalid_body', 'truncated', 'heartbeat_only',
    'late_expiry', 'late_selection'])
def test_browser_requires_valid_final_envelope_and_preserves_recovery(page, kind):
    result = page.evaluate('''async kind=>{
      const incident='a'.repeat(32);state.incident=incident;state.csrf='test';
      state.expiresAt='2099-01-01T00:00:00Z';state.evidence={latest_observation_revision:0};
      state.captures=[{id:'b'.repeat(32)}];state.config={guidance:'OFF'};
      let release;const wait=new Promise(r=>release=r);let finished=false;
      let envelope={protocol:'acquisition-progress-v1',status:200,body:{
        run_id:'c'.repeat(32),incident_id:incident,state:'INCOMPLETE',
        current:false,reconciliation_required:false}};
      if(kind==='known_error')envelope={...envelope,status:429,body:{error:'capacity'}};
      if(kind==='expiry')envelope={...envelope,status:401,body:{error:'guest_unavailable'}};
      if(kind==='unknown')envelope={...envelope,status:503,body:{error:'interrupted',outcome:'unknown'}};
      if(kind==='wrong_protocol')envelope.protocol='wrong';
      if(kind==='invalid_status')envelope.status='200';
      if(kind==='invalid_body')envelope.body={};
      const calls=[];window.fetch=async(url,options)=>{
        calls.push({url,headers:options.headers});
        if(!url.endsWith('/acquisitions'))throw new Error('controlled read unavailable');
        return new Response(new ReadableStream({async start(controller){
          controller.enqueue(new TextEncoder().encode(' \\n'));await wait;
          const encoded=JSON.stringify(envelope);
          if(kind==='heartbeat_only'){controller.error(new Error('network lost'));return;}
          const text=kind==='truncated'?encoded.slice(0,-3):encoded;
          controller.enqueue(new TextEncoder().encode(text.slice(0,10)));
          controller.enqueue(new TextEncoder().encode(text.slice(10)));controller.close();
        }}),{headers:{'Content-Type':'application/vnd.batchbeacon.acquisition+json'}});
      };
      const operation=acquire().catch(()=>{}).finally(()=>finished=true);
      await new Promise(r=>setTimeout(r,10));
      const before={finished,pending:state.pending?.operation,acquisition:state.acquisition};
      if(kind==='late_expiry')expire();
      if(kind==='late_selection'){state.incident='d'.repeat(32);state.selection++;}
      release();await operation;
      return {before,pending:state.pending,expired:state.expired,acquisition:state.acquisition,
        incident:state.incident,calls,title:$('verdict-title').textContent};
    }''', kind)
    assert not result['before']['finished'] and result['before']['pending']
    assert result['before']['acquisition'] is None
    assert result['calls'][0]['headers']['X-BatchBeacon-Progress'] == 'acquisition-stages-v2'
    assert len([c for c in result['calls'] if c['url'].endswith('/acquisitions')]) == 1
    if kind in ('expiry', 'late_expiry'):
        assert result['expired'] and result['acquisition'] is None and result['pending'] is None
        assert result['title'] == 'Guest access expired'
    elif kind == 'known_error':
        assert result['pending'] is None
    else:
        assert result['pending']['operation'] == result['before']['pending']
        if kind == 'success':
            assert result['acquisition']['state'] == 'INCOMPLETE'
        else:
            assert result['acquisition'] is None


@pytest.mark.parametrize('kind', ['valid', 'split_utf8', 'duplicate', 'backward', 'unknown_stage',
    'wrong_sequence', 'extra_terminal', 'extra_line', 'no_terminal', 'wrong_incident',
    'oversized', 'too_many_heartbeats', 'truncated', 'terminal_error', 'disconnect'])
def test_v2_parser_rejects_unconfirmed_stream_without_redispatch(page, kind):
    result = page.evaluate('''async kind=>{
      const incident='a'.repeat(32);state.incident=incident;state.csrf='test';
      state.expiresAt='2099-01-01T00:00:00Z';state.evidence={latest_observation_revision:0};
      state.captures=[{id:'b'.repeat(32)}];state.config={guidance:'OFF'};
      const protocol='acquisition-stages-v2';
      let frames=[{protocol,type:'stage',sequence:0,stage:'preparing'},
        {protocol,type:'stage',sequence:1,stage:'model'},
        {protocol,type:'terminal',sequence:2,status:200,body:{run_id:'c'.repeat(32),
          incident_id:incident,state:'INCOMPLETE',current:false,reconciliation_required:false}}];
      if(kind==='duplicate')frames[1].stage='preparing';
      if(kind==='backward'){frames[0].stage='model';frames[1].stage='preparing';}
      if(kind==='unknown_stage')frames[1].stage='completed';
      if(kind==='wrong_sequence')frames[1].sequence=9;
      if(kind==='extra_terminal')frames.push({...frames.at(-1),sequence:3});
      if(kind==='no_terminal')frames.pop();
      if(kind==='wrong_incident')frames.at(-1).body.incident_id='d'.repeat(32);
      if(kind==='terminal_error'){frames.at(-1).status=503;frames.at(-1).body={error:'provider_unavailable',outcome:'unknown'};}
      let raw=frames.map(f=>JSON.stringify(f)+'\\n').join('');
      if(kind==='extra_line')raw+='\\n';
      if(kind==='oversized')raw=' '.repeat(65537)+raw;
      if(kind==='too_many_heartbeats')raw='\\n'.repeat(65)+raw;
      if(kind==='truncated')raw=raw.slice(0,-4);
      // Split a multibyte unknown-field value across every byte; strict keys reject it.
      if(kind==='split_utf8')raw=raw.replace('"preparing"','"préparing"');
      let posts=0;
      window.fetch=async(url,options)=>{
        if(!url.endsWith('/acquisitions'))throw new Error('controlled unavailable read');
        posts++;
        return new Response(new ReadableStream({start(c){
          const bytes=new TextEncoder().encode(raw);
          if(kind==='disconnect'){c.enqueue(bytes.slice(0,20));c.error(new Error('lost'));return;}
          for(let i=0;i<bytes.length;i++)c.enqueue(bytes.slice(i,i+1));c.close();
        }}),{headers:{'Content-Type':'application/vnd.batchbeacon.acquisition+ndjson'}});
      };
      await acquire().catch(()=>{});
      return {posts,pending:state.pending,acquisition:state.acquisition,
        title:$('verdict-title').textContent};
    }''', kind)
    assert result['posts'] == 1 and result['pending']['operation']
    if kind == 'valid':
        assert result['acquisition']['state'] == 'INCOMPLETE'
    else:
        assert result['acquisition'] is None
    assert result['title'] != 'Matches this recall'


@pytest.mark.parametrize('connected_browser', [{'progress_response_enabled': True,
    'progress_interval_seconds': .02}], indirect=True)
def test_saved_reload_waits_and_key_recovery_stays_read_only(connected_browser):
    page, c, _, errors = connected_browser
    page.get_by_role('button', name='Use this label', exact=True).click()
    expect(page.locator('#check')).to_be_enabled()
    page.evaluate('''()=>{
      const original=fetch;let sent=false;
      const wait=new Promise(r=>window.releaseEvidence=r);
      window.fetch=async(...args)=>{
        if(args[0].endsWith('/acquisitions') && args[1]?.method==='POST'){
          sent=true;window.originalAcquisitionKey=args[1].headers['Idempotency-Key'];}
        if(sent && args[0].endsWith('/evidence'))await wait;
        return original(...args);
      };
    }''')
    page.get_by_role('button', name='Extract and check', exact=True).click()
    expect(page.locator('#label-status')).to_contain_text('Loading saved evidence', timeout=20000)
    expect(page.locator('#check')).to_be_disabled()
    assert page.evaluate('performance.getEntriesByName("batchbeacon.usable-result").length') == 0
    page.evaluate('releaseEvidence()')
    expect(page.locator('#verdict-title')).to_have_text('Matches this recall', timeout=20000)
    assert page.evaluate('performance.getEntriesByName("batchbeacon.usable-result").length') == 1
    page.evaluate('''()=>{
      pending({kind:'acquisition',incident:state.incident,operation:window.originalAcquisitionKey});
      window.recoveryCalls=[];const original=fetch;
      window.fetch=(...args)=>{recoveryCalls.push({url:args[0],method:args[1]?.method});
        return original(...args);};
    }''')
    page.get_by_role('button', name='Reconcile pending operation', exact=True).click()
    expect(page.locator('#recover')).to_be_hidden()
    expect(page.locator('#verdict-title')).to_have_text('Matches this recall')
    assert all(r['method'] == 'GET' for r in page.evaluate('recoveryCalls'))
    assert len(c[4]) == 2 and not errors


@pytest.mark.parametrize('connected_browser', [{'progress_response_enabled': True,
    'progress_interval_seconds': .02}], indirect=True)
def test_failed_saved_reload_reports_recovery_without_usable_result(connected_browser):
    page, c, _, errors = connected_browser
    page.get_by_role('button', name='Use this label', exact=True).click()
    expect(page.locator('#check')).to_be_enabled()
    page.evaluate('''()=>{
      const original=fetch;let sent=false;
      window.fetch=async(...args)=>{
        if(args[0].endsWith('/acquisitions') && args[1]?.method==='POST')sent=true;
        if(sent && args[0].endsWith('/evidence'))throw new Error('controlled read failure');
        return original(...args);
      };
    }''')
    page.get_by_role('button', name='Extract and check', exact=True).click()
    page.wait_for_function("""()=>!state.busy &&
      performance.getEntriesByName('batchbeacon.acquisition.reload_failed').length===1""")
    expect(page.locator('#label-status')).to_contain_text('Recheck saved status')
    expect(page.locator('#label-status')).not_to_contain_text('Loading saved evidence')
    assert page.evaluate('performance.getEntriesByName("batchbeacon.usable-result").length') == 0
    assert page.evaluate(
        'performance.getEntriesByName("batchbeacon.saved-evidence-failed").length') == 1
    assert len(c[4]) == 2 and not errors

"""Reproduced UI recovery/currentness/evidence regressions; intercepted HTTP only."""

import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel=os.environ.get("BATCHBEACON_TEST_BROWSER_CHANNEL") or None
        )
        context = browser.new_context()
        page = context.new_page()
        # Local browser harness only; all external calls are intercepted.
        page.route("http://localhost:8989/**", lambda route: route.fulfill(status=200, body=""))
        page.goto("http://localhost:8989/")
        page.set_content(Path("src/batchbeacon/ui/index.html").read_text())
        code = Path("src/batchbeacon/ui/workbench.js").read_text().replace("task(init);", "")
        page.add_script_tag(content=code)
        yield page
        browser.close()


def test_invalid_json_response_retains_original_acquisition_recovery(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident'; state.evidence={latest_observation_revision:0};
      state.captures=[{id:'owned-capture'}];
      window.fetch=async()=>new Response('{"state":',
       {status:200,
      headers:{'Content-Type':'application/json'}});
      try { await acquire(); } catch(e) {}
      return {pending:state.pending, recoverHidden:document.getElementById('recover').hidden};
    }""")
    assert result["pending"] and result["pending"]["kind"] == "acquisition", result


def test_unknown_action_response_body_retains_action_recovery(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident'; state.target={result_revision:1,
      action_type:'SIMULATED_HOLD'};
      window.fetch=async()=>new Response('{"action":',
       {status:200,
      headers:{'Content-Type':'application/json'}});
      try { await confirm(); } catch(e) {}
      return {pending:state.pending, recoverHidden:document.getElementById('recover').hidden};
    }""")
    assert result["pending"] and result["pending"]["kind"] == "action", result


def test_expiry_removes_prior_current_verdict_and_counts(page):
    result = page.evaluate("""()=>{
      document.getElementById('verdict-title').textContent='Simulated action recorded';
      document.getElementById('verdict-copy').textContent='A simulated hold was saved.';
      document.getElementById('queue-count').textContent='1 saved incident';
      document.getElementById('queue-counts').textContent='Simulated action recorded: 1';
      expire();
      return {verdict:document.getElementById('verdict-title').textContent,
       count:document.getElementById('queue-count').textContent,
       counts:document.getElementById('queue-counts').textContent};
    }""")
    assert (
        result["verdict"] != "Simulated action recorded"
        and "1" not in result["count"]
        and "1" not in result["counts"]
    ), result


def test_comparison_retains_operator_and_reference_for_review(page):
    result = page.evaluate("""()=>{
      state.evidence={result:{candidates:[{product_id:'synthetic-product',
      eligible_jurisdiction:true,
      
        identity:{field:'IDENTITY',
      observed:'Synthetic Brie',
      source_values:['Synthetic Brie'],
      outcome:'MATCH',
      reason:'IDENTITY_MATCH',
      source_operator:null,
      source_date_range:null,
      source_applies:true,
      source_evidence:[{kind:'SOURCE',
      artifact_id:'notice-exact',
      sha256:'a'.repeat(64),
      locator:'product heading'}],
      observation_evidence:[]},
      
        predicates:[{field:'LOT',
      observed:'000aB',
      source_values:['000aB'],
      outcome:'MATCH',
      reason:'EXACT_MATCH',
      source_operator:'EXACT',
      source_date_range:null,
      source_applies:true,
      source_evidence:[{kind:'SOURCE',
      artifact_id:'notice-exact',
      sha256:'a'.repeat(64),
      locator:'lot row 2'}],
      observation_evidence:[{kind:'CAPTURE',
      artifact_id:'capture-exact',
      sha256:'b'.repeat(64),
      locator:'front label lot'}]}]}]}};
      compare();
      [...document.querySelectorAll('#comparisons button')].find(b=>b.textContent==='LOT').click();
      return document.getElementById('comparisons').textContent+' '+
        document.getElementById('field-detail').textContent;
    }""")
    assert "EXACT" in result and "lot row 2" in result and "front label lot" in result, result


def test_date_range_uses_typed_contract_bounds(page):
    result = page.evaluate("""()=>{
      const identity={field:'IDENTITY',
      observed:'Synthetic Brie',
      source_values:['Synthetic Brie'],
      outcome:'MATCH',
      reason:'IDENTITY_MATCH',
      source_operator:null,
      source_date_range:null};
      const date={field:'BEST_BEFORE',
      observed:'2026-10-17',
      source_values:[],
      outcome:'MATCH',
      reason:'DATE_RANGE_MATCH',
      source_operator:'RANGE',
      source_date_range:{lower:'2026-10-01',
      upper:'2026-10-31',
      lower_inclusive:true,
      upper_inclusive:false}};
      state.evidence={result:{candidates:[{product_id:'synthetic',
      eligible_jurisdiction:true,
      identity,
      predicates:[date]}]}};
      compare();
      return document.getElementById('comparisons').textContent;
    }""")
    assert "2026-10-01" in result and "2026-10-31" in result and "undefined" not in result, result


def test_pending_verification_blocks_new_verification(page):
    result = page.evaluate("""()=>{
      state.csrf='owned-csrf';state.incident='owned-incident';state.evidence={observation:{},
      current:false};
      pending({kind:'verification',incident:'owned-incident',operation:'original-key'});
      controls();
      return {reverify:document.getElementById('reverify').disabled,
              correction:document.getElementById('save-correction').disabled};
    }""")
    assert result["reverify"] and result["correction"], result


def test_expired_pending_operation_cannot_lock_new_guest_restart(page):
    result = page.evaluate("""()=>{
      pending({kind:'verification',incident:'expired-incident',operation:'expired-key'});
      expire();
      return {stored:sessionStorage.getItem('bb_pending'),pending:state.pending};
    }""")
    assert result["stored"] is None and result["pending"] is None, result


def test_prepare_cannot_confirm_an_unrendered_observation_revision(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident';state.csrf='owned-csrf';
      state.evidence={current:true,
      observation:{revision:1,
      identity:{name:{value:'Old rendered product'},
      pack:{value:'250 g'}},
      fields:[]},
      result:{revision:1,
      verdict:'MATCHED_HOLD_FOR_REVIEW',
      checked_sources:[]}};
      window.fetch=async()=>new Response(JSON.stringify({target:{action_type:'SIMULATED_HOLD',
      observation_revision:2,
      result_revision:2,
      result_hash:'a'.repeat(64),
      observation_hash:'b'.repeat(64),
      context_state_hash:'c'.repeat(64),
      environment_hash:'d'.repeat(64),
      action_policy_hash:'e'.repeat(64)}}),
      {status:200,
      headers:{'Content-Type':'application/json'}});
      try { await prepare(); } catch(e) {}
      return {open:document.getElementById('confirm-dialog').open,
      text:document.getElementById('confirm-product').textContent};
    }""")
    assert not result["open"], result


def test_platform_429_capture_keeps_exact_operation_and_recovery(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident';state.csrf='csrf';state.expiresAt='future';
      state.config={max_images:2,max_image_bytes:5242880};
      let sent;
      window.fetch=async(path,options)=>{sent=options.headers['Idempotency-Key'];
        return new Response('No available instance',{status:429});};
      await task(()=>upload([new File(['synthetic'],'label.png',{type:'image/png'})]));
      return {sent,pending:state.pending,stored:JSON.parse(sessionStorage.getItem('bb_pending')),
        message:document.getElementById('app-status').textContent,
        recoverHidden:document.getElementById('recover').hidden,
        checkDisabled:document.getElementById('check').disabled};
    }""")
    assert result['pending'] and result['pending']['operation'] == result['sent']
    assert result['stored'] == result['pending'] and result['pending']['kind'] == 'capture'
    assert 'capacity' in result['message'].lower()
    assert not result['recoverHidden'] and result['checkDisabled']


def test_capture_recovery_after_reload_reuses_key_and_rejects_other_bytes(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident';state.csrf='csrf';state.expiresAt='future';
      state.config={max_images:2,max_image_bytes:5242880};
      const file=new File(['synthetic'],'label.png',{type:'image/png'});let calls=[];
      window.fetch=async(path,options)=>{calls.push({path,key:options.headers['Idempotency-Key'],method:options.method});
        return new Response('No available instance',{status:429});};
      try{await upload([file]);}catch(e){}
      const original=state.pending.operation;state.pending=null;
      pending(JSON.parse(sessionStorage.getItem('bb_pending')));
      let rejected=false;try{await upload([new File(['changed'],'label.png')]);}
      catch(e){rejected=e.message.includes('same original images');}
      window.fetch=async(path,options)=>{calls.push({path,key:options.headers['Idempotency-Key'],method:options.method});
        const body=options.method==='GET'?{found:false,batch:null}:{ready:true,captures:[]};
        return new Response(JSON.stringify(body),{status:200});};
      await upload([file]);return {calls,original,rejected,pending:state.pending};
    }""")
    assert result['rejected'] and result['pending'] is None
    assert [r['method'] for r in result['calls']] == ['POST', 'GET', 'POST']
    assert {r['key'] for r in result['calls']} == {result['original']}


def test_capture_recovery_ready_never_reposts_and_pending_keeps_controls(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident';state.csrf='csrf';state.expiresAt='future';
      let calls=[];loadIncident=async id=>{state.incident=id;};
      pending({kind:'capture',incident:state.incident,operation:'original',files:[]});
      window.fetch=async(path,options)=>{calls.push(options.method);
        return new Response(JSON.stringify({found:true,batch:{ready:false,captures:[]}}),
          {status:200});};
      await recover();controls();const held=state.pending.operation;
      const controlsOk=!document.getElementById('upload').disabled &&
        document.getElementById('check').disabled &&
        document.getElementById('start-sample').disabled;
      window.fetch=async(path,options)=>{calls.push(options.method);
        return new Response(JSON.stringify({found:true,batch:{ready:true,captures:[]}}),
          {status:200});};
      await recover();return {calls,held,controlsOk,pending:state.pending};
    }""")
    assert result == {'calls': ['GET', 'GET'], 'held': 'original',
                      'controlsOk': True, 'pending': None}


def test_json503_capture_retains_original_key(page):
    result = page.evaluate("""async()=>{
      state.incident='owned-incident';state.csrf='csrf';state.expiresAt='future';
      state.config={max_images:2,max_image_bytes:5242880};
      window.fetch=async()=>new Response(
        JSON.stringify({error:'evidence_temporarily_unavailable'}),{status:503});
      try{await upload([new File(['synthetic'],'label.png',{type:'image/png'})]);}catch(e){}
      return {pending:state.pending,hidden:document.getElementById('recover').hidden};
    }""")
    assert result['pending'] and result['pending']['kind'] == 'capture'
    assert not result['hidden']

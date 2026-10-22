"""Judge-facing regressions over controlled HTTP/local services, never live AI."""

# ruff: noqa: F811
import os
from datetime import timedelta
from pathlib import Path

import pytest
from playwright.sync_api import expect

from tests.browser.test_learning_workbench import learning_browser  # noqa: F401
from tests.browser.test_workbench import connected_browser  # noqa: F401
from tests.browser.test_workbench_recovery import page  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("status,unresolved", [("FAILED", False), ("TIMED_OUT", False),
    ("INCOMPLETE", False), ("FAILED", True), ("TIMED_OUT", True)])
def test_no_envelope_status_survives_reopen_without_repeating_extraction(page, status, unresolved):
    result = page.evaluate(
        """async([status,unresolved])=>{
      state.csrf='test';state.config={guidance:'OFF'};
      const evidence={latest_run_id:'owned-run',latest_observation_revision:0,
        current:false,observation:null,result:null,extraction_history:[],
        observation_history:[],result_history:[]};
      const calls=[];
      window.fetch=async(url,options)=>{
        calls.push([url,options.method]);
        const body=url.endsWith('/evidence')?evidence:
          url.endsWith('/captures')?{batches:[{ready:true,captures:[{id:'capture'}]}]}:
          url.endsWith('/actions')?{actions:[]}:
          {run_id:'owned-run',state:status,current:false,
            reconciliation_required:unresolved,diagnostics:['CHECK_FAILED']};
        return new Response(JSON.stringify(body),{status:200});
      };
      await loadIncident('owned-incident');
      await loadIncident('owned-incident');
      return {title:$('verdict-title').textContent,copy:$('verdict-copy').textContent,
        checkDisabled:$('check').disabled,holdDisabled:$('confirm-open').disabled,
        statusHidden:$('refresh-acquisition').hidden,pending:state.pending,calls};
    }""",
        [status, unresolved],
    )
    expected = {
        "FAILED": "Extraction failed",
        "TIMED_OUT": "Extraction timed out",
        "INCOMPLETE": "Check outcome unresolved",
    }
    assert result["title"] == ("Check outcome unresolved" if unresolved else expected[status])
    assert result["holdDisabled"] and result["pending"] is None
    assert result["checkDisabled"] == (unresolved or status == "INCOMPLETE")
    assert result["statusHidden"] == (not unresolved and status != "INCOMPLETE")
    if unresolved:
        assert "Operator review is required" in result["copy"]
        assert "explicitly retry" not in result["copy"]
    assert all(method == "GET" for _, method in result["calls"])
    assert len(result["calls"]) == 8


def test_unavailable_saved_status_blocks_new_extraction(page):
    result = page.evaluate("""async()=>{
      state.csrf='test';state.config={guidance:'OFF'};
      window.fetch=async(url)=>{
        if(url.includes('/acquisitions/'))return new Response('{}',{status:503});
        const body=url.endsWith('/evidence')?{latest_run_id:'run',current:false,
          extraction_history:[],observation_history:[],result_history:[]}:
          url.endsWith('/captures')?{batches:[{ready:true,captures:[{id:'capture'}]}]}:
          {actions:[]};
        return new Response(JSON.stringify(body),{status:200});
      };
      await loadIncident('owned-incident');
      return {title:$('verdict-title').textContent,disabled:$('check').disabled,
        statusHidden:$('refresh-acquisition').hidden};
    }""")
    assert result == {"title": "Check status unavailable", "disabled": True, "statusHidden": False}


def test_queue_cached_empty_then_new_case_refreshes_on_return(connected_browser):
    page, c, _, errors = connected_browser
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#queue-rows")).to_contain_text("No incidents")
    page.locator("#new-review").click()
    page.locator("#start-sample").click()
    expect(page.locator("#capture-images img")).to_have_count(1)
    c[3][5][0] += timedelta(seconds=3)
    requests = []
    page.on("request", lambda request: requests.append((request.method, request.url)))
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#queue-rows [role=listitem]")).to_have_count(1)
    page.locator("nav [data-view=workbench]").click()
    page.locator("nav [data-view=retail]").click()
    reads = [(method, url) for method, url in requests if "/api/retail/queue" in url]
    assert len(reads) == 1 and reads[0][0] == "GET"
    assert len(c[4]) == 0 and not errors


def test_guidance_empty_state_and_mobile_expiry(learning_browser):
    page, c, _, errors = learning_browser
    page.goto(page.url.split("?")[0])
    page.locator("nav [data-view=guidance]").click()
    expect(page.locator("#guidance-empty")).to_be_visible()
    expect(page.locator("#guidance-context")).to_have_text("No investigation selected")
    expect(page.locator("#guidance-proposal-section")).to_be_hidden()
    expect(page.locator("#guidance-confirm-section")).to_be_hidden()
    capture_dir = os.environ.get("BATCHBEACON_CAPTURE_DIR")
    if capture_dir:
        Path(capture_dir).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(capture_dir) / "guidance-empty-desktop.png"), full_page=True)
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        expect(page.locator("#session-state")).to_be_visible()
        expect(page.locator("#session-state")).to_contain_text("Workspace access expires")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        if capture_dir:
            page.screenshot(
                path=str(Path(capture_dir) / f"guidance-empty-{width}.png"), full_page=True
            )
    page.locator("#guidance-start").click()
    expect(page.locator("#workbench")).to_be_visible()
    assert len(c[4]) == 2 and not errors


def test_guidance_selection_does_not_offer_another_incident_candidate(page):
    result = page.evaluate("""()=>{
      state.incident='B';state.learning={requests:[],feedback:[],candidates:[
        {id:'A-candidate',supports:[{basis:{incident_id:'A'}}]}],evaluations:[
        {candidate:{id:'A-candidate'},status:'PASSED'}]};
      const selection=learningSelection();return {candidate:selection.candidate??null,
        evaluation:selection.evaluation??null};
    }""")
    assert result == {"candidate": None, "evaluation": None}


def test_failed_new_check_labels_prior_comparison_historical_and_blocks_hold(page):
    result = page.evaluate("""()=>{
      state.csrf='test';state.config={guidance:'OFF'};state.incident='case';
      state.evidence={current:false,extraction_history:[],observation_history:[],result_history:[],
        result:{verdict:'MATCHED_HOLD_FOR_REVIEW',candidates:[],checked_sources:[],
          outstanding_fields:[]}};
      state.acquisition={state:'FAILED',current:false,diagnostics:['CHECK_FAILED']};
      render();return {title:$('verdict-title').textContent,copy:$('verdict-copy').textContent,
        comparison:$('comparisons').textContent,holdDisabled:$('confirm-open').disabled};
    }""")
    assert result["title"] == "Extraction failed"
    assert "Previous saved comparison is historical" in result["copy"]
    assert "historical evidence" in result["comparison"]
    assert result["holdDisabled"]

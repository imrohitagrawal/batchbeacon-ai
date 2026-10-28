"""Owned source rendering in a compatible rollback reader; controlled source metadata."""
import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import expect

from batchbeacon.evidence_service import replace
from batchbeacon.source_state import (
    FamilyRefresh,
    SelectionReceipt,
    SourceCatalog,
    SourceChoice,
    SourceRegistry,
    SourceRuntimeAdmission,
    SourceSelection,
)
from tests.browser.test_workbench import check_sample
from tests.browser.test_workbench import connected_browser as connected_browser
from tests.unit.domain_fixtures import NOW
from tests.unit.test_source_state_reader import enable, refresh, registry_for

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("width", [1440, 390])
@pytest.mark.parametrize("completed", [True, False, None])
def test_reader_reopens_owned_metadata_source_without_default_source_or_ai(
        connected_browser, width, completed):
    page, c, context, errors = connected_browser
    if completed:
        check_sample(page)
    elif completed is False:
        page.get_by_role("button", name="Use this label", exact=True).click()
        expect(page.locator("#capture-images img")).to_have_count(1)
    else:
        origin = page.url.rstrip("/")
        response = page.request.post(origin + "/api/incidents", headers={
            "Origin": origin, "X-CSRF-Token": page.evaluate("state.csrf"),
            "Idempotency-Key": "empty-source-reader"})
        assert response.ok
        page.goto(origin + "/?incident=" + response.json()["incident_id"])
        expect(page.locator("#incident-id")).to_contain_text("Incident")
    stores, server, guest, evidence, actions, now = c[3]
    token = next(row["value"] for row in context.cookies()
                 if row["name"] == guest.policy.cookie_name)
    session = guest.resolve(token)
    incident = parse_qs(urlparse(page.url).query)["incident"][0]
    original = stores.run(lambda tx: stores.evidence.snapshot(
        tx, session.capability_hash, incident).environment)
    dependency = replace(original.notices[0].dependency, family="synthetic-UK-reader",
                         version="synthetic-UK-original", content_hash="a" * 64)
    metadata = replace(original.notices[0], dependency=dependency, authority="UK FSA",
        jurisdictions=("GB-SCT",), review=None, interpretation_complete=False, products=())
    selected = replace(original, notices=(metadata,), context=replace(original.context,
        jurisdiction="GB-SCT", current_sources=(dependency,)))
    catalog = SourceCatalog(default_choice="default", choices=(
        SourceChoice(key="default", environment=original),
        SourceChoice(key="UK-metadata", environment=selected)))
    registry = SourceRegistry(catalog=catalog, families=tuple(FamilyRefresh(
        family=n.dependency.family, epoch=n.dependency.epoch, status="NEVER_REQUESTED")
        for n in (original.notices[0], metadata)))
    stores.source_runtime = SourceRuntimeAdmission(catalog_hash=catalog.digest())
    server.seed(stores._encode(stores.name("source_registry"), "source_registry", registry))
    selection = SourceSelection(catalog_hash=catalog.digest(), choice="UK-metadata",
        environment_hash=selected.digest(), revision=1, selected_at=NOW,
        receipts=(SelectionReceipt(key="synthetic-reader-test", payload_hash="a" * 64,
                                   revision=1),))
    stores.evidence.transact(session.capability_hash, incident,
        lambda snapshot: replace(snapshot.state, source_selection=selection, active_result=None))
    calls = len(c[4])
    page.set_viewport_size({"width": width, "height": 900})
    page.reload()
    expect(page.locator("#source-summary")).to_contain_text("synthetic-UK-original")
    expect(page.locator("#source-summary")).to_contain_text("GB-SCT")
    expect(page.locator("#source-summary")).to_contain_text("Review-only")
    expect(page.locator("#single-source")).to_contain_text("UK FSA")
    expect(page.locator("#check")).to_be_disabled()
    assert page.locator("#inspect-source-notice").get_attribute("href") == metadata.final_url
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    if not completed:
        expect(page.locator("#verdict-copy")).to_contain_text("Source interpretation needs review")
        if completed is False:
            expect(page.locator("#label-status")).to_contain_text(
                "Source interpretation needs review")
        expect(page.locator("#decision-title")).to_have_text("Source review is required")
        expect(page.locator("#capability-help")).to_contain_text("No AI check or stock hold")
    assert not errors
    capture_dir = os.environ.get("BATCHBEACON_SOURCE_READER_CAPTURES")
    if capture_dir:
        destination = Path(capture_dir)
        destination.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(destination / f"source-reader-{width}-{completed}.png"),
                        full_page=True)
    pending = []
    page.route(f"**/api/incidents/{incident}/evidence", lambda route: pending.append(route))
    page.reload()
    expect(page.locator("#source-summary")).to_contain_text("Loading this investigation")
    expect(page.locator("#inspect-source-notice")).to_be_hidden()
    assert page.locator("#inspect-source-notice").get_attribute("href") is None
    assert pending
    pending[0].fulfill(status=503, content_type="application/json",
                       body='{"error":"test_read_failed"}')
    expect(page.locator("#source-summary")).to_contain_text("Selected source unavailable")
    expect(page.locator("#inspect-source-notice")).to_be_hidden()
    assert len(c[4]) == calls


@pytest.mark.parametrize("status", ["UNCHANGED", "CHANGED", "UNAVAILABLE", "EXPIRED"])
def test_reader_names_refresh_outcome_and_live_currentness(connected_browser, status):
    page, c, context, errors = connected_browser
    if status == "UNCHANGED":
        check_sample(page)
    else:
        page.get_by_role("button", name="Use this label", exact=True).click()
        expect(page.locator("#capture-images img")).to_have_count(1)
    enable(c[3], registry_for(c[3]))
    refresh(c[3], "UNCHANGED" if status == "EXPIRED" else status,
            epoch=2 if status == "CHANGED" else 1)
    if status == "EXPIRED":
        c[3][5][0] += timedelta(seconds=30)
    calls = len(c[4])
    page.reload()
    if status == "UNCHANGED":
        expect(page.locator("#source-summary")).to_contain_text("Live source bytes rechecked")
        page.locator("#reverify").click()
        expect(page.locator("#verdict-copy")).to_contain_text(
            "Current for the saved live source check")
    else:
        reason = {"CHANGED": "Live source bytes changed", "UNAVAILABLE": "could not be confirmed",
                  "EXPIRED": "check expired"}[status]
        expect(page.locator("#label-status")).to_contain_text(reason)
        expect(page.locator("#decision-title")).to_have_text("Source review is required")
        expect(page.locator("#check")).to_be_disabled()
    assert len(c[4]) == calls and not errors

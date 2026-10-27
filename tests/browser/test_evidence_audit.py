"""Readable audit UI; controlled backend/model, not human or live acceptance."""

# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import check_sample, connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


def open_field(page):
    check_sample(page)
    page.locator("#comparisons button").first.click()
    page.locator("#field-provenance").locator("..").locator(":scope > summary").click()


@pytest.mark.parametrize("width", [390, 1440])
def test_audit_explains_references_and_opens_actual_evidence(connected_browser, width):
    page, _, context, errors = connected_browser
    page.set_viewport_size({"width": width, "height": 1000})
    open_field(page)
    box = page.locator("#field-provenance")
    expect(box).to_contain_text("Evidence references explain where this comparison came from")
    expect(box.locator("#field-audit")).to_be_hidden()
    with context.expect_page() as opened:
        box.get_by_role("link", name="Open label panel 1 (new tab)").click()
    image = opened.value
    image.wait_for_load_state()
    expect(image.locator("img")).to_have_count(1)
    image.close()
    assert box.get_by_role("link", name="Open official notice (new tab)").get_attribute(
        "href"
    ) == page.locator("#source-summary a").get_attribute("href")
    box.get_by_text("Audit details", exact=True).click()
    expect(box.locator("#field-audit")).to_contain_text("File fingerprints identify saved content")
    expect(box.locator("#field-audit")).to_contain_text("Source references (1)")
    for location in box.locator(".audit-locations").all():
        expect(location).to_be_hidden()
    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
    assert not errors


@pytest.mark.parametrize(
    "mismatch", ["selection", "source_hash", "epoch", "capture_hash", "capture_kind"]
)
def test_evidence_links_use_saved_bindings(connected_browser, mismatch):
    page, _, _, errors = connected_browser
    open_field(page)
    page.evaluate(
        """mismatch=>{
        const c=structuredClone(state.evidence.result.candidates[0]);
        const r=c.identity;
        if(mismatch==='selection')$('source-choice').value='unavailable';
        if(mismatch==='source_hash')r.source_evidence[0].sha256='0'.repeat(64);
        if(mismatch==='epoch')c.source.epoch+=1;
        if(mismatch==='capture_hash')r.observation_evidence=r.observation_evidence.map(x=>({...x,sha256:'0'.repeat(64)}));
        if(mismatch==='capture_kind')r.observation_evidence=r.observation_evidence.map(x=>({...x,kind:'SOURCE'}));
        fieldProvenance(r,r.source_values.join(' / '),'match',c.source);
    }""",
        mismatch,
    )
    box = page.locator("#field-provenance")
    if mismatch in ("source_hash", "epoch"):
        expect(box.get_by_role("link", name="Open official notice (new tab)")).to_have_count(0)
        expect(box).to_contain_text("exact references remain in Audit details")
    elif mismatch in ("capture_hash", "capture_kind"):
        expect(box.get_by_role("link", name="Open label panel 1 (new tab)")).to_have_count(0)
        expect(box).to_contain_text("cannot be opened")
    else:
        expect(box.get_by_role("link", name="Open official notice (new tab)")).to_have_count(1)
    assert not errors


@pytest.mark.parametrize(
    "operator,applies", [("UNKNOWN", None), ("NOT_SPECIFIED", False), ("ALL", True)]
)
def test_exact_references_and_unknown_rule_remain_readable(connected_browser, operator, applies):
    page, _, _, errors = connected_browser
    open_field(page)
    locator = "normalized_box:0.058999999999999997,0.251,0.47699999999999998,0.30499999999999999"
    page.evaluate(
        """args=>{
        const c=structuredClone(state.evidence.result.candidates[0]),r=c.identity;
        r.source_operator=args.operator;r.source_applies=args.applies;r.observed='001Ab';
        r.observation_evidence=[{...r.observation_evidence[0],locator:args.locator},
            {...r.observation_evidence[0],locator:'printed text line 2'}];
        fieldProvenance(r,'Unknown','unknown',c.source);
    }""",
        {"operator": operator, "applies": applies, "locator": locator},
    )
    box = page.locator("#field-provenance")
    expect(box).to_contain_text("2 recorded references")
    expect(box).to_contain_text("001Ab")
    expect(box.get_by_role("link", name="Open label panel 1 (new tab)")).to_have_count(1)
    box.get_by_text("Audit details", exact=True).click()
    expect(box.locator("#field-audit")).to_contain_text(operator)
    expect(box.locator("#field-audit")).to_contain_text(
        "Not recorded" if applies is None else "Yes" if applies else "No"
    )
    locations = box.get_by_text("View exact image coordinates or text location", exact=True)
    expect(locations).to_have_count(2)
    locations.first.click()
    expect(box.locator(".audit-locations").nth(1)).to_contain_text(locator)
    assert not errors


@pytest.mark.parametrize("clipboard", ["success", "denied", "unavailable"])
def test_copy_exact_value_has_truthful_accessible_feedback(connected_browser, clipboard):
    page, _, _, errors = connected_browser
    open_field(page)
    page.evaluate(
        """mode=>{
        window.copyValues=[];
        Object.defineProperty(navigator,'clipboard',{configurable:true,
            value:mode==='unavailable'?undefined:{writeText:async value=>{
                copyValues.push(value);if(mode==='denied')throw new Error('denied');
            }}});
    }""",
        clipboard,
    )
    box = page.locator("#field-provenance")
    box.get_by_text("Audit details", exact=True).click()
    copy = box.get_by_role(
        "button", name="Copy source reference 1 file fingerprint (sha256)", exact=True
    )
    row = copy.locator("..")
    exact = row.locator("code").inner_text()
    assert page.evaluate("copyValues") == []
    copy.focus()
    page.keyboard.press("Enter")
    if clipboard == "success":
        expect(row.get_by_role("status")).to_have_text("File fingerprint (SHA256) copied.")
    else:
        expect(row.get_by_role("status")).to_contain_text("Could not copy automatically")
        fallback = row.locator("textarea")
        expect(fallback).to_be_focused()
        expect(fallback).to_have_value(exact)
        assert fallback.evaluate("el=>el.selectionStart===0 && el.selectionEnd===el.value.length")
    assert page.evaluate("copyValues") == ([] if clipboard == "unavailable" else [exact])
    assert not errors


def test_delayed_copy_cannot_update_changed_or_expired_field(connected_browser):
    page, _, _, errors = connected_browser
    open_field(page)
    page.evaluate("""()=>{
        window.copyValues=[];
        Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:value=>{
            copyValues.push(value);return new Promise(resolve=>window.finishCopy=resolve);
        }}});
    }""")
    box = page.locator("#field-provenance")
    box.get_by_text("Audit details", exact=True).click()
    copy = box.get_by_role("button", name="Copy source reference 1 record id", exact=True)
    copy.evaluate("el=>window.oldCopy=el")
    copy.click()
    page.locator("#comparisons button").nth(1).click()
    page.evaluate("finishCopy()")
    expect(box).not_to_contain_text("copied.")
    page.evaluate("oldCopy.click();expire();oldCopy.click()")
    assert len(page.evaluate("copyValues")) == 1
    expect(box).to_be_empty()
    assert not errors

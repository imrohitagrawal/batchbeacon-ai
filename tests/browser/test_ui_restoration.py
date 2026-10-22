"""UI restoration regressions over local fake SDK/ADK; no cloud/model evidence."""

# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_learning_workbench import learning_browser  # noqa: F401
from tests.browser.test_workbench import check_sample, connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


def test_guidance_stage_does_not_advance_failed_or_running_evaluation(learning_browser):
    page, _, _, errors = learning_browser
    page.locator("nav [data-view=guidance]").click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    page.locator("#guidance-request").click()
    expect(page.locator("#owned-guidance")).to_contain_text("leading zeros")
    page.locator("#feedback-save").click()
    expect(page.locator("#learning-counts")).to_contain_text("1/40")
    page.locator("#candidate-create").click()
    expect(page.locator("#candidate-state")).to_contain_text("CANDIDATE READY")
    page.locator("#candidate-evaluate").click()
    expect(page.locator("#candidate-state")).to_contain_text("PASSED")
    for status in ("FAILED", "RUNNING", "PASSED"):
        page.evaluate(
            "(status)=>{state.learning.evaluations[0].status=status;renderLearning(state.learning);controls();}",
            status,
        )
        expect(page.locator("#guidance-steps [aria-current=step]")).to_have_text(
            "Confirm" if status == "PASSED" else "Evaluate"
        )
    page.evaluate("expire()")
    expect(page.locator("#guidance-steps [aria-current=step]")).to_have_count(0)
    expect(page.locator("#active-wording")).not_to_contain_text("revision 1")
    expect(page.locator("#proposed-wording")).not_to_contain_text("GUIDANCE V2")
    assert not errors


def test_expiry_clears_completed_verdict_presentation(connected_browser):
    page, _, _, errors = connected_browser
    check_sample(page)
    page.locator("#confirm-open").click()
    page.locator("#hold-consent").check()
    page.locator("#hold-confirm").click()
    expect(page.locator("#verdict-title")).to_have_text("Workspace action recorded")
    assert "completed" in page.locator(".verdict").get_attribute("class")
    page.evaluate("expire()")
    expect(page.locator("#verdict-title")).to_have_text("Guest access expired")
    assert "completed" not in page.locator(".verdict").get_attribute("class")
    assert not errors


def test_guidance_reflows_at_320_with_default_and_doubled_text(learning_browser):
    page, _, _, errors = learning_browser
    page.locator("nav [data-view=guidance]").click()
    expect(page.locator("#guidance-policy-state")).to_contain_text("revision 1")
    page.set_viewport_size({"width": 320, "height": 1000})
    for size in ("100%", "200%"):
        page.evaluate("(size)=>document.documentElement.style.fontSize=size", size)
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), size
        select = page.locator("#feedback-detail").bounding_box()
        assert select and select["x"] + select["width"] <= 320
    assert not errors


def test_phone_queue_counts_have_visual_separation(connected_browser):
    page, _, _, errors = connected_browser
    page.locator("nav [data-view=retail]").click()
    expect(page.locator("#queue-status")).to_contain_text("Manual refresh complete")
    for width in (390, 320):
        page.set_viewport_size({"width": width, "height": 844})
        spans = page.locator("#queue-counts > span")
        assert spans.count() > 1
        for index in range(1, spans.count()):
            previous = spans.nth(index - 1).bounding_box()
            current = spans.nth(index).bounding_box()
            assert (
                current["x"] >= previous["x"] + previous["width"] + 8
                or current["y"] >= previous["y"] + previous["height"] + 4
            )
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors

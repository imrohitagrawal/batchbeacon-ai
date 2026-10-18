"""Local prototype usability checks; not integrated or hosted acceptance."""

import re
from io import BytesIO

import pytest
from PIL import Image
from playwright.sync_api import expect
from test_prototype import local_url as local_url  # noqa: F401
from test_prototype import page as page  # noqa: F401

pytestmark = pytest.mark.browser


@pytest.fixture
def refined(page, local_url):
    page.goto(local_url + "refined/")
    return page


def test_native_example_choice_has_keyboard_state_and_recovery(refined):
    examples = refined.locator(".examples")
    if examples.get_attribute("open") is None:
        examples.locator("summary").click()
    choice = refined.get_by_role("radio", name=re.compile("^Supported match"))
    choice.focus()
    refined.keyboard.press("ArrowRight")
    expect(refined.get_by_role("radio", name=re.compile("^Missing date"))).to_be_checked()
    expect(refined.locator("#example-current")).to_have_text("Missing date selected")
    expect(refined.locator("#verdict-title")).to_have_text("One panel is still missing")
    expect(refined.locator("#date-result")).to_have_text("Unknown")
    refined.get_by_role("button", name="Preview recapture").click()
    expect(refined.get_by_label("Preview image selection")).to_be_visible()
    expect(refined.locator("#capture-instruction")).to_contain_text("best-before date")


def test_paired_field_selection_announces_values_and_keeps_focus(refined):
    button = refined.get_by_role("button", name="Best before", exact=True)
    button.focus()
    refined.keyboard.press("Enter")
    expect(button).to_have_attribute("aria-pressed", "true")
    expect(button).to_be_focused()
    expect(refined.locator("#field-detail")).to_have_text(
        "Best before selected. Label: 17 Oct 2026. Notice: 17 Oct 2026. Result: Match."
    )
    assert refined.locator(".field-pick[aria-pressed=true]").count() == 1


def test_confirmation_is_keyboard_gated_and_returns_focus(refined):
    trigger = refined.get_by_role("button", name="Review simulated hold")
    trigger.focus()
    refined.keyboard.press("Enter")
    dialog = refined.get_by_role("dialog")
    expect(dialog).to_be_visible()
    expect(dialog.get_by_role("button", name="Confirm preview", exact=True)).to_be_disabled()
    expect(dialog).to_contain_text("Select the review confirmation above")
    consent = dialog.get_by_role("checkbox")
    consent.focus()
    refined.keyboard.press("Space")
    expect(dialog.get_by_role("button", name="Confirm preview", exact=True)).to_be_enabled()
    refined.keyboard.press("Escape")
    expect(dialog).not_to_be_visible()
    expect(trigger).to_be_focused()


def test_cancel_after_previous_confirmation_cannot_repeat_success(refined):
    trigger = refined.get_by_role("button", name="Review simulated hold")
    trigger.click()
    refined.get_by_role("dialog").get_by_role("checkbox").check()
    refined.get_by_role("button", name="Confirm preview", exact=True).click()
    expect(refined.locator("#toast")).to_contain_text("Confirmation preview complete")
    trigger.click()
    refined.keyboard.press("Escape")
    expect(refined.get_by_role("dialog")).not_to_be_visible()
    expect(refined.locator("#toast")).not_to_be_visible()
    expect(trigger).to_be_focused()


def test_held_history_describes_completed_example_without_new_confirmation(refined):
    refined.get_by_role("link", name="Retail queue", exact=True).click()
    refined.locator('[data-scenario="held"]').click()
    expect(refined.locator("#verdict-title")).to_contain_text("Simulated hold recorded")
    expect(refined.locator("#verdict-copy")).to_contain_text("No stock action was saved")
    expect(refined.locator("#verdict-copy")).not_to_contain_text("before recording")
    expect(refined.locator("#decision-title")).to_have_text("Recorded example")
    expect(refined.locator("#confirm-open")).to_be_disabled()


def test_guidance_lifecycle_current_step_matches_visible_task(refined):
    refined.get_by_role("link", name="Capture guidance", exact=True).click()
    current = refined.locator('.steps [aria-current="step"]')
    expect(current).to_have_text("Candidate")
    refined.get_by_role("button", name=re.compile("^Preview evaluation")).click()
    expect(current).to_have_text("Evaluation")
    refined.get_by_role("button", name=re.compile("^Review activation")).click()
    expect(current).to_have_text("Confirmation")
    refined.get_by_role("checkbox", name=re.compile("^I have reviewed")).check()
    refined.get_by_role("button", name="Activate preview for this shop").click()
    expect(current).to_have_text("Active")
    expect(refined.locator("#rollback-help")).to_contain_text("newer preview revision")
    refined.get_by_role("button", name="Preview rollback").click()
    expect(refined.locator("#active-policy")).to_contain_text("v3")
    expect(refined.locator("#guidance-status")).to_contain_text("Lifetime counters stay unchanged")
    expect(refined.locator("#rollback-help")).to_contain_text("already restored")
    refined.get_by_role("button", name="Reset preview").click()
    expect(current).to_have_text("Candidate")


def test_capture_feedback_stays_with_input_and_cannot_leak_to_another_incident(refined):
    image = BytesIO()
    Image.new("RGB", (12, 12), "white").save(image, format="PNG")
    refined.get_by_role("button", name="Preview recapture", exact=True).click()
    refined.get_by_label("Preview image selection").set_input_files({
        "name": "synthetic-label.png", "mimeType": "image/png", "buffer": image.getvalue(),
    })
    expect(refined.locator("#capture-panel [role=status]")).to_contain_text(
        "Nothing was uploaded or checked"
    )
    expect(refined.locator("#toast")).not_to_be_visible()
    refined.get_by_role("link", name="Retail queue", exact=True).click()
    refined.locator('[data-scenario="missing"]').click()
    refined.get_by_role("button", name="Preview recapture", exact=True).click()
    expect(refined.locator("#capture-status")).to_be_empty()
    assert refined.locator("#capture-file").evaluate("el => el.files.length") == 0


@pytest.mark.parametrize("width", [320, 390, 720, 1280, 1440])
def test_reflow_all_views_and_long_state_labels(refined, width):
    refined.set_viewport_size({"width": width, "height": 900})
    for view in ["workbench", "retail", "guidance"]:
        refined.locator(f'nav a[data-view="{view}"]').click()
        expect(refined.locator(f"#{view}")).to_be_visible()
        if view == "workbench":
            refined.locator(".examples summary").click()
        assert refined.evaluate("document.documentElement.scrollWidth <= innerWidth"), view
    refined.get_by_role("link", name="Check a product", exact=True).click()
    if refined.locator(".state-examples").get_attribute("open") is None:
        refined.locator(".state-examples summary").click()
    for state in ["missing", "stale", "negative", "failure"]:
        refined.get_by_label("Preview a state").select_option(state)
        assert refined.evaluate("document.documentElement.scrollWidth <= innerWidth"), state
    expect(refined.locator("#observed-product")).to_contain_text("Knafeh")


@pytest.mark.parametrize("width", [320, 390, 720, 1440])
def test_doubled_text_keeps_queue_states_inside_their_columns(refined, width):
    refined.set_viewport_size({"width": width, "height": 900})
    # Text-size stress test, separate from native browser zoom and device testing.
    refined.add_style_tag(content=":root { font-size: 32px !important; }")
    assert refined.locator(".skip").evaluate("el => el.getBoundingClientRect().bottom <= 0")
    for view in ["workbench", "retail", "guidance"]:
        refined.locator(f'nav a[data-view="{view}"]').click()
        expect(refined.locator(f"#{view}")).to_be_visible()
        if view == "workbench":
            refined.locator(".examples summary").click()
        assert refined.evaluate("document.documentElement.scrollWidth <= innerWidth"), view
    refined.get_by_role("link", name="Retail queue", exact=True).click()
    expect(refined.locator("#retail")).to_be_visible()
    assert refined.locator(".queue-row > .state-tag").evaluate_all("""tags => tags.every(tag => {
      const box = tag.getBoundingClientRect();
      const row = tag.parentElement.getBoundingClientRect();
      return box.left >= row.left && box.right <= row.right;
    })""")
    refined.goto(refined.url.split("#")[0] + "brand.html")
    refined.add_style_tag(content=":root { font-size: 32px !important; }")
    assert refined.evaluate("document.documentElement.scrollWidth <= innerWidth"), "brand"
    skip = refined.get_by_role("link", name="Skip to main content", exact=True)
    assert skip.evaluate("el => el.getBoundingClientRect().bottom <= 0")
    skip.focus()
    assert skip.evaluate("el => el.getBoundingClientRect().top >= 0")


def test_negative_does_not_compare_lot_or_date_and_disabled_reason_is_visible(refined):
    refined.locator(".examples summary").click()
    refined.get_by_role("radio", name=re.compile("^Same lot")).check()
    expect(refined.locator("#identity-result")).to_have_text("Different")
    expect(refined.locator("#lot-result")).to_have_text("Not used")
    expect(refined.locator("#date-result")).to_have_text("Not used")
    expect(refined.locator("#confirm-open")).to_be_disabled()
    expect(refined.locator("#decision-copy")).to_contain_text("not permission to sell")
    expect(refined.locator("#decision-title")).to_have_text("No hold supported")


def test_queue_empty_state_removes_empty_list_items_and_recovers(refined):
    refined.get_by_role("link", name="Retail queue", exact=True).click()
    refined.get_by_label("Show", exact=True).select_option("empty")
    expect(refined.get_by_role("heading", name="No examples match this filter")).to_be_visible()
    expect(refined.get_by_role("listitem")).to_have_count(0)
    refined.get_by_role("button", name="Show all incidents").click()
    expect(refined.get_by_role("listitem")).to_have_count(6)
    expect(refined.get_by_label("Show", exact=True)).to_be_focused()


@pytest.mark.parametrize("view", ["retail", "guidance"])
def test_skip_link_preserves_current_workspace_destination(refined, view):
    refined.locator(f'nav a[data-view="{view}"]').click()
    # Complete navigation's documented heading-focus step before starting the
    # normal keyboard skip sequence. Queued anchor activation is covered below.
    expect(refined.locator(f"#{view} h1")).to_be_focused()
    skip = refined.get_by_role("link", name="Skip to main content", exact=True)
    skip.focus()
    refined.keyboard.press("Enter")
    expect(refined.locator(f"#{view}")).to_be_visible()
    expect(refined.locator("#workbench")).not_to_be_visible()
    expect(refined.locator("#main")).to_be_focused()


@pytest.mark.parametrize("width", [390, 1440])
@pytest.mark.parametrize("view", ["retail", "guidance"])
def test_queued_route_changes_keep_rapid_skip_on_requested_view(refined, width, view):
    refined.set_viewport_size({"width": width, "height": 900})
    # Both native anchor activations occur before queued hashchange handlers run.
    refined.evaluate("""view => {
      document.querySelector(`nav a[data-view="${view}"]`).click();
      document.querySelector('.skip').click();
    }""", view)
    expect(refined.locator(f"#{view}")).to_be_visible()
    expect(refined.locator(f'nav a[data-view="{view}"]')).to_have_attribute(
        "aria-current", "page"
    )
    expect(refined.locator("#main")).to_be_focused()


@pytest.mark.parametrize("state", ["stale", "failure"])
def test_uk_product_code_and_unrestricted_dates_keep_correct_ui_meaning(refined, state):
    refined.locator(".state-examples summary").click()
    refined.get_by_label("Preview a state").select_option(state)
    expect(refined.locator("#source-date-rule")).to_have_text("All dates")
    expect(refined.get_by_role("button", name="Preview recapture")).not_to_be_visible()
    expect(refined.locator("#capture-not-needed")).to_contain_text("No date-panel recapture")
    refined.get_by_role("button", name="Inspect extracted fields").click()
    code = "319456" if state == "stale" else "318591"
    expect(refined.get_by_label("Product code", exact=True)).to_have_value(code)
    expect(refined.get_by_label("Lot / batch", exact=True)).not_to_be_visible()
    refined.get_by_label("Preview a state").select_option("missing")
    expect(refined.get_by_role("button", name="Preview recapture")).to_be_visible()
    refined.get_by_role("button", name="Inspect extracted fields").click()
    expect(refined.get_by_label("Lot / batch", exact=True)).to_have_value("232511")


def test_reduced_motion_disables_field_animation(refined):
    refined.emulate_media(reduced_motion="reduce")
    refined.get_by_role("button", name="Lot", exact=True).click()
    assert refined.locator(".field-selected").evaluate(
        "element => getComputedStyle(element).animationName"
    ) == "none"


@pytest.mark.parametrize("width", [320, 390, 720, 1440])
def test_persistent_navigation_and_keyboard_focus_after_scroll(refined, width):
    refined.set_viewport_size({"width": width, "height": 700})
    nav = refined.get_by_role("navigation", name="Workspace", exact=True)
    for view in ["retail", "guidance", "workbench"]:
        nav.locator(f'a[data-view="{view}"]').click()
        expect(refined.locator(f"#{view}-title")).to_be_focused()
        refined.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
        bounds = nav.bounding_box()
        assert 0 <= bounds["y"] < 30
        assert bounds["y"] + bounds["height"] < 120
        expect(nav.locator(f'a[data-view="{view}"]')).to_have_attribute(
            "aria-current", "page"
        )
    refined.locator(".technical summary").focus()
    for _ in range(10):
        refined.keyboard.press("Shift+Tab")
        assert refined.evaluate("""() => {
          const el = document.activeElement;
          const r = el.getBoundingClientRect();
          if (el.closest('.app-header') || el.classList.contains('skip')) return true;
          const nav = document.querySelector('nav[aria-label="Workspace"]');
          const header = innerWidth <= 760 ? nav : nav.closest('header');
          return r.top >= header.getBoundingClientRect().bottom && r.bottom <= innerHeight;
        }"""), "Keyboard focus must remain clear of the persistent header"


@pytest.mark.parametrize("width", [320, 390])
def test_phone_section_jumps_clear_persistent_navigation(refined, width):
    refined.set_viewport_size({"width": width, "height": 700})
    for name, target in [("Evidence", "comparison-title"), ("Decision", "verdict-title")]:
        refined.get_by_role("navigation", name="Within this review").get_by_role(
            "link", name=name, exact=True
        ).click()
        nav = refined.get_by_role("navigation", name="Workspace", exact=True).bounding_box()
        heading = refined.locator(f"#{target}").bounding_box()
        assert heading["y"] >= nav["y"] + nav["height"]


def test_guidance_confirmation_moves_focus_and_reset_restores_wording(refined):
    refined.get_by_role("link", name="Capture guidance", exact=True).click()
    refined.get_by_role("button", name=re.compile("^Preview evaluation")).click()
    refined.get_by_role("button", name=re.compile("^Review activation")).click()
    consent = refined.get_by_role("checkbox", name=re.compile("^I have reviewed"))
    expect(consent).to_be_focused()
    refined.keyboard.press("Space")
    refined.get_by_role("button", name="Activate preview for this shop").click()
    refined.get_by_role("button", name="Preview next capture").click()
    expect(refined.locator("#capture-instruction")).to_contain_text("avoid glare")
    refined.get_by_role("link", name="Capture guidance", exact=True).click()
    refined.get_by_role("button", name="Reset preview").click()
    refined.get_by_role("link", name="Check a product", exact=True).click()
    refined.get_by_role("button", name="Preview recapture").click()
    expect(refined.locator("#capture-instruction")).to_have_text(
        "Photograph the complete best-before date marking."
    )


@pytest.mark.parametrize("view", ["workbench", "retail", "guidance"])
def test_rendered_default_text_contrast_and_minimum_legibility(refined, view):
    refined.locator(f'nav a[data-view="{view}"]').click()
    findings = refined.evaluate("""() => {
      const rgb = value => (value.match(/[\\d.]+/g) || []).map(Number);
      const lum = color => color.slice(0,3).map(v => v / 255)
        .map(v => v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4)
        .reduce((a,v,i) => a + v * [.2126,.7152,.0722][i],0);
      const failures = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node;
      while ((node = walker.nextNode())) {
        if (!node.textContent.trim()) continue;
        const el = node.parentElement;
        if (!el || ['SCRIPT','STYLE','OPTION'].includes(el.tagName)) continue;
        const range = document.createRange(); range.selectNodeContents(node);
        const rect = range.getBoundingClientRect();
        if (!rect.width || !rect.height || rect.bottom < 0) continue;
        const style = getComputedStyle(el);
        if (style.visibility === 'hidden' || el.closest('[hidden]')) continue;
        let bg = el; let color;
        while(bg) {
          color = rgb(getComputedStyle(bg).backgroundColor);
          if (color.length === 3 || color[3] === 1) break;
          bg = bg.parentElement;
        }
        color = bg ? color : [255,255,255];
        const fgLum = lum(rgb(style.color)); const bgLum = lum(color);
        const ratio = (Math.max(fgLum,bgLum)+.05)/(Math.min(fgLum,bgLum)+.05);
        const size = parseFloat(style.fontSize);
        const required = size >= 24 || (size >= 18.667 && +style.fontWeight >= 700) ? 3 : 4.5;
        if(ratio < required || size < 11) {
          failures.push({text:node.textContent.trim().slice(0,60),ratio,size});
        }
      }
      return failures;
    }""")
    assert findings == []


def test_recall_reason_is_visible_and_details_preserve_quantity_and_citations(refined):
    expect(refined.locator('#recall-reason')).to_contain_text('Possible Shiga toxin')
    details = refined.locator('#recall-details')
    details.locator('summary').focus()
    refined.keyboard.press('Enter')
    expect(details).to_contain_text('diarrhoea, stomach cramps and vomiting')
    expect(details).to_contain_text('SFA directed')
    for label in ['Total quantity recalled / batch volume', 'Legal proceedings / penalties']:
        expect(details.locator('dt').filter(has_text=label).locator('+ dd')).to_contain_text(
            'Not stated in this notice.'
        )
    expect(refined.locator('#recall-citation a')).to_have_attribute(
        'href', re.compile(r'^https://www.sfa.gov.sg/')
    )
    expect(refined.locator('#recall-review')).to_contain_text('human source review pending')


def test_context_follows_exact_uk_version_then_negative_without_reason_leak(refined):
    refined.get_by_role('link', name='Retail queue', exact=True).click()
    expect(refined.locator('[data-scenario=stale] .queue-reason')).to_contain_text('Salmonella')
    expect(refined.locator('#queue-sources a')).to_have_count(3)
    refined.locator('[data-scenario=stale]').click()
    expect(refined.locator('#recall-reason')).to_have_text('Salmonella contamination')
    expect(refined.locator('#recall-citation a')).to_have_attribute(
        'href', 'https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026'
    )
    refined.locator('#recall-details summary').click()
    expect(refined.locator('#recall-facts')).to_contain_text('World of Sweets')
    expect(refined.locator('#recall-facts')).to_contain_text('point-of-sale notices will')
    expect(refined.locator('#recall-facts')).to_contain_text('enforcement order is not stated')
    expect(refined.locator('#recall-facts')).not_to_contain_text('Wales')
    refined.get_by_role('link', name='Retail queue', exact=True).click()
    refined.locator('[data-scenario=failure]').click()
    expect(refined.locator('#recall-citation a')).to_have_attribute(
        'href', re.compile('update-1$')
    )
    assert refined.locator('#recall-details').get_attribute('open') is None
    refined.locator('#recall-details summary').click()
    expect(refined.locator('#recall-facts')).to_contain_text('Wales and Scotland')
    refined.get_by_role('link', name='Retail queue', exact=True).click()
    expect(refined.locator('[data-scenario=negative] .queue-reason')).to_have_text(
        'No matching recall reason established.'
    )
    refined.locator('[data-scenario=negative]').click()
    expect(refined.locator('#recall-reason')).not_to_contain_text('Salmonella')
    expect(refined.locator('#recall-relation')).to_contain_text('Compared notice only')
    expect(refined.locator('#confirm-open')).to_be_disabled()


def test_context_load_failure_is_unknown_not_absence(refined):
    refined.route('**/source-context.json', lambda route: route.abort())
    refined.reload()
    expect(refined.locator('#recall-reason')).to_have_text('Recall context unavailable')
    refined.locator('#recall-details summary').click()
    expect(refined.locator('#recall-details')).not_to_contain_text('Not stated in this notice')
    expect(refined.locator('#recall-citation')).to_be_empty()


@pytest.mark.parametrize('width', [320, 390, 720, 1440])
def test_expanded_recall_details_reflow_at_normal_and_doubled_text(refined, width):
    refined.set_viewport_size({'width': width, 'height': 900})
    expect(refined.locator('#recall-reason')).to_contain_text('Possible')
    refined.locator('#recall-details summary').click()
    assert refined.evaluate('document.documentElement.scrollWidth <= innerWidth')
    refined.add_style_tag(content=':root { font-size: 32px !important; }')
    assert refined.evaluate('document.documentElement.scrollWidth <= innerWidth')

"""User-facing journey completion and recovery, controlled backend/model only."""
# ruff: noqa: F811
import pytest
from playwright.sync_api import expect

from tests.browser.test_workbench import check_sample, connected_browser  # noqa: F401

pytestmark = pytest.mark.browser


def test_progress_has_one_number_and_no_link_styling(connected_browser):
    page, _, _, _ = connected_browser
    steps = page.locator('#journey-stages')
    assert steps.evaluate("el=>getComputedStyle(el).listStyleType") == 'none'
    assert steps.locator('[aria-current=step]').evaluate(
        "el=>getComputedStyle(el).textDecorationLine") == 'none'
    expect(steps).to_contain_text('Label')
    expect(page.locator('#confirm-open')).to_be_hidden()
    expect(page.locator('#decision-recheck')).to_be_hidden()
    expect(page.locator('#decision-title')).to_have_text('Begin with a label')


def test_renewed_workspace_recovers_old_url_without_old_evidence(connected_browser):
    page, c, context, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    old_url = page.url
    context.clear_cookies()  # Controlled expiry/cookie-loss boundary, not live expiry evidence.
    page.reload()
    expect(page.locator('#app-status')).to_contain_text('unavailable in this workspace')
    assert 'incident=' not in page.url
    assert page.evaluate('state.incident') is None
    expect(page.locator('#start-sample')).to_be_enabled()
    expect(page.locator('#capture-images img')).to_have_count(0)
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    assert page.url != old_url
    assert not c[4] and not errors


@pytest.mark.parametrize('width', [390, 1440])
def test_completed_review_offers_working_next_actions_and_direct_evidence(connected_browser, width):
    page, c, context, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 1000})
    check_sample(page)
    page.locator('#confirm-open').click()
    page.locator('#hold-consent').check()
    page.locator('#hold-confirm').click()
    expect(page.locator('#verdict-title')).to_have_text('Workspace action recorded')
    expect(page.locator('#confirm-open')).to_be_hidden()
    expect(page.locator('#capability-help')).not_to_contain_text('before confirming')
    with context.expect_page() as opened:
        page.locator('#saved-label-link').click()
    image_page = opened.value
    image_page.wait_for_load_state()
    assert image_page.url.endswith(page.locator('#capture-images img').get_attribute('src'))
    image_page.close()
    assert page.locator('#saved-notice-link').get_attribute('href') == (
        page.locator('#source-summary a').get_attribute('href'))
    page.locator('#completed-queue').click()
    expect(page.locator('#queue-rows [role=listitem]')).to_have_count(1)
    expect(page.locator('#queue-rows a')).to_have_text('View detail')
    expect(page.locator('#queue-rows a')).to_be_focused()
    page.locator('#queue-rows a').click()
    expect(page.locator('#completed-next')).to_be_visible()
    page.locator('#completed-next').click()
    expect(page.locator('#sample-choice')).to_be_focused()
    expect(page.locator('#verdict-title')).to_have_text('Ready for evidence')
    assert 'incident=' not in page.url
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert len(c[4]) == 2 and not errors


def test_field_evidence_and_history_explain_values_before_technical_details(connected_browser):
    page, _, _, errors = connected_browser
    check_sample(page)
    page.locator('#comparisons button').first.click()
    page.locator('#field-provenance').locator('..').locator('summary').first.click()
    expect(page.locator('#field-provenance')).to_contain_text('Your label')
    expect(page.locator('#field-provenance')).to_contain_text('Recall notice')
    expect(page.locator('#field-audit')).to_be_hidden()
    page.locator('#history').locator('..').locator(':scope > summary').click()
    expect(page.locator('#history')).to_contain_text('AI check 1')
    expect(page.locator('#history')).to_contain_text('Label details')
    expect(page.locator('#history-audit')).to_be_hidden()
    assert not errors


def test_route_without_incident_clears_previous_selection(connected_browser):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.evaluate("""history.pushState(null,'',location.pathname+'#workbench');
        window.dispatchEvent(new PopStateEvent('popstate'))""")
    expect(page.locator('#capture-images img')).to_have_count(0)
    assert page.evaluate('state.incident') is None
    expect(page.locator('#check')).to_be_disabled()
    assert not c[4] and not errors


def test_unselected_source_and_expiry_clear_direct_links(connected_browser):
    page, _, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#saved-notice-link')).to_be_visible()
    page.evaluate("$('source-choice').value='missing';sourceView()")
    expect(page.locator('#saved-notice-link')).to_be_hidden()
    assert page.locator('#saved-notice-link').get_attribute('href') is None
    page.evaluate('expire()')
    expect(page.locator('#saved-label-link')).to_be_hidden()
    assert page.locator('#saved-label-link').get_attribute('href') is None
    expect(page.locator('#renew-workspace')).to_be_visible()
    assert page.locator('#renew-workspace').get_attribute('href') == '/'
    assert not errors


@pytest.mark.parametrize('view', ['retail', 'guidance'])
def test_blank_history_route_preserves_destination(connected_browser, view):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.evaluate("""view=>{history.pushState(null,'',location.pathname+'#'+view);
        window.dispatchEvent(new PopStateEvent('popstate'));}""", view)
    expect(page.locator('#'+view)).to_be_visible()
    assert page.url.endswith('#'+view)
    assert page.evaluate('state.incident') is None
    assert not c[4] and not errors


@pytest.mark.parametrize('owned', [True, False])
def test_pending_restore_checks_membership_not_just_expiry(connected_browser, owned):
    page, c, context, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    incident = page.evaluate('state.incident')
    page.evaluate("pending({kind:'acquisition',incident:state.incident,operation:'original-operation'})")
    if not owned:
        context.clear_cookies()
    else:
        # Reproduce hosted latency: a visible recovery control is not completed restoration.
        page.add_init_script("""(() => {
          const originalFetch = window.fetch;
          window.fetch = async (url, options = {}) => {
            if (url === '/api/incidents' && (options.method || 'GET') === 'GET') {
              await new Promise(resolve => { window.releaseMembership = resolve; });
            }
            return originalFetch(url, options);
          };
        })();""")
    page.reload()
    if owned:
        expect(page.locator('#recover')).to_be_visible()
        expect(page.locator('#recover')).to_be_disabled()
        assert page.evaluate('state.incident') is None
        assert page.evaluate('state.pending.operation') == 'original-operation'
        page.evaluate('window.releaseMembership()')
        expect(page.locator('#recover')).to_be_enabled()
        expect(page.locator('#capture-images img')).to_have_count(1)
        assert page.evaluate('state.incident') == incident
        expect(page.locator('#start-sample')).to_be_disabled()
    else:
        expect(page.locator('#start-sample')).to_be_enabled()
        assert page.evaluate('state.pending') is None
        assert page.evaluate('state.incident') is None
    assert not c[4] and not errors


def test_pending_membership_failure_rechecks_without_replaying(connected_browser):
    page, c, _, errors = connected_browser
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    page.evaluate("pending({kind:'verification',incident:state.incident,operation:'original-key'})")
    page.route('**/api/incidents', lambda route: route.fulfill(
        status=503, content_type='application/json', body='{"error":"unavailable"}'))
    page.reload()
    expect(page.locator('#recover')).to_have_text('Check pending access')
    expect(page.locator('#start-sample')).to_be_disabled()
    sent = []
    page.on('request', lambda request: sent.append((request.method, request.url)))
    page.locator('#recover').click()
    expect(page.locator('#recover')).to_be_enabled()
    assert not any(method == 'POST' for method, _ in sent)
    assert page.evaluate('state.pending.operation') == 'original-key'
    page.unroute('**/api/incidents')
    page.locator('#recover').click()
    expect(page.locator('#recover')).to_have_text('Reconcile pending operation')
    assert not any(method == 'POST' for method, _ in sent)
    assert not c[4] and not errors


@pytest.mark.parametrize('width', [1440, 390])
@pytest.mark.parametrize('mode', ['fragment_navigation', 'reload_after_custody_loss'])
def test_unavailable_fragment_arrives_at_visible_recovery(connected_browser, width, mode):
    page, c, context, errors = connected_browser
    page.set_viewport_size({'width': width, 'height': 844})
    page.locator('#start-sample').click()
    expect(page.locator('#check')).to_be_enabled()
    old_url = page.url.split('#')[0]
    context.clear_cookies()
    if mode == 'fragment_navigation':
        # First change document; a hash-only goto would not rerun initialization.
        page.goto(old_url.split('?')[0])
        expect(page.locator('#start-sample')).to_be_enabled()
        page.goto(old_url + '#evidence-title')
    else:
        page.evaluate("history.replaceState(null,'',location.pathname+"
                      "location.search+'#evidence-title')")
        page.reload()
    expect(page.locator('#review-recovery')).to_be_visible()
    expect(page.locator('#start-sample')).to_be_enabled()
    expect(page.locator('#app-status')).to_be_focused()
    for selector in ['#app-status', '#review-recovery']:
        box = page.locator(selector).bounding_box()
        assert box['y'] >= 0 and box['y'] + box['height'] <= page.viewport_size['height']
    page.keyboard.press('Tab')
    expect(page.locator('#recovery-choose')).to_be_focused()
    page.keyboard.press('Enter')
    expect(page.locator('#sample-choice')).to_be_focused()
    assert not c[4] and not errors

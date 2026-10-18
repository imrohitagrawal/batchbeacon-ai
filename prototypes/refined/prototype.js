// Reversible visual-state examples; reads only the local draft source-context JSON.
// No model call, upload, storage or saved action.
const $ = (id) => document.getElementById(id);
const views = ['workbench', 'retail', 'guidance'];
let recallManifest = null;
let recallScenario = 'match';
const sourceForScenario = (name) => name === 'stale' ? 'FSA-PRIN-47-2026' : name === 'failure' ? 'FSA-PRIN-47-2026-update-1' : 'sfa-cheese-2026-10-09';
const factText = (fact) => fact?.state === 'STATED' && fact.text ? fact.text : fact?.state === 'NOT_STATED' ? 'Not stated in this notice.' : 'Not verified from this notice.';
function citation(notice, prefix = '') {
  const a = document.createElement('a'); a.href = notice.source_url;
  a.textContent = prefix + notice.citation_label; a.target = '_blank'; a.rel = 'noreferrer';
  return a;
}
function renderRecallContext() {
  const notice = recallManifest?.notices.find(n => n.source_id === sourceForScenario(recallScenario));
  $('recall-facts').replaceChildren(); $('recall-citation').replaceChildren();
  $('recall-attribution').textContent = ''; $('recall-licence').hidden = true;
  $('recall-relation').textContent = recallScenario === 'negative'
    ? 'Compared notice only. No matching recall reason is established for this invented product.'
    : 'This describes the notice, not a contamination test of your item.';
  if (!notice) {
    $('recall-reason').textContent = 'Recall context unavailable';
    $('recall-basis').textContent = 'Open the official source to review the recall reason and details.';
    $('recall-review').textContent = 'Context could not be loaded; no missing detail is treated as absent from the notice.';
    return;
  }
  $('recall-reason').textContent = factText(notice.reason);
  $('recall-basis').textContent = factText(notice.basis);
  $('recall-review').textContent = 'Context addition · human source review pending';
  const labels = {health_risks:'Authority-stated health risks',affected_products:'Affected packs, identifiers and dates',total_quantity:'Total quantity recalled / batch volume',businesses:'Recalling business / importers',company_action:'Company action at publication',regulatory_action:'Regulatory action at publication',legal_action:'Legal proceedings / penalties',consumer_advice:'Authority advice to buyers',geography:'Notice geography'};
  Object.entries(labels).forEach(([key,label]) => {
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = factText(notice[key]);
    if(notice[key]?.locator) { const loc = document.createElement('small'); loc.className = 'fact-locator'; loc.textContent = 'Source section: ' + notice[key].locator; dd.append(loc); }
    $('recall-facts').append(dt,dd);
  });
  const documents = notice.related_documents;
  const dt = document.createElement('dt'); dt.textContent = 'Linked customer notices';
  const dd = document.createElement('dd');
  if (documents?.state === 'PRESENT' && documents.documents?.length) {
    documents.documents.forEach(documentLink => {
      let url;
      try { url = new URL(documentLink.url); } catch { return; }
      if (url.protocol !== 'https:' || url.username || url.password) return;
      const link = document.createElement('a'); link.href = url.href;
      link.className = 'customer-notice-link'; link.target = '_blank'; link.rel = 'noopener noreferrer';
      link.textContent = 'Company customer notice (external PDF) — linked by FSA';
      dd.append(link);
      const title = document.createElement('small'); title.className = 'fact-locator';
      title.textContent = documentLink.title; dd.append(title);
    });
    if (dd.childNodes.length) {
      const note = document.createElement('small'); note.className = 'fact-locator';
      note.textContent = 'Opens in a new tab. Linked from this notice version; attachment contents have not been reviewed by BatchBeacon.';
      dd.append(note);
    } else dd.textContent = 'Linked document unavailable. Open the official notice for its customer guidance.';
  } else dd.textContent = documents?.state === 'NONE_STATED'
    ? 'No linked customer notice stated in this reviewed capture.'
    : 'Customer-notice links have not been verified for this source. Open the official notice for its customer guidance.';
  $('recall-facts').append(dt, dd);
  $('recall-citation').append(citation(notice, 'Source: '));
  $('recall-attribution').textContent = notice.attribution;
  $('recall-licence').hidden = !notice.source_id.startsWith('FSA-');
}
function renderQueueReasons() {
  document.querySelectorAll('.queue-row[data-scenario]').forEach(row => {
    const notice = recallManifest?.notices.find(n => n.source_id === sourceForScenario(row.dataset.scenario));
    row.querySelector('.queue-reason').textContent = row.dataset.scenario === 'negative'
      ? 'No matching recall reason established.'
      : notice ? 'Notice reason: ' + factText(notice.reason) + ' · ' + notice.citation_label
      : 'Recall context unavailable · open review for source.';
  });
  $('queue-sources').replaceChildren();
  recallManifest?.notices.forEach(notice => $('queue-sources').append(citation(notice)));
}
fetch('source-context.json', {cache: 'no-store'}).then(response => {
  if (!response.ok) throw new Error('Context unavailable');
  return response.json();
}).then(data => {
  if (data.version !== 'recall-context-draft-1' || !Array.isArray(data.notices)) throw new Error('Context unavailable');
  recallManifest = data;
}).catch(() => { recallManifest = null; }).finally(() => { renderRecallContext(); renderQueueReasons(); });
function showView(event) {
  const requested = (event?.newURL ? new URL(event.newURL).hash : location.hash).slice(1);
  const current = views.includes(requested) ? requested : document.querySelector('.view:not([hidden])')?.id || 'workbench';
  views.forEach((name) => { $(name).hidden = name !== current; });
  document.querySelectorAll('[data-view]').forEach((a) => { a.classList.toggle('selected', a.dataset.view === current); if (a.dataset.view === current) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current'); });
  $('page-name').textContent = {workbench: 'Check a product', retail: 'Retail queue', guidance: 'Capture guidance'}[current];
}
addEventListener('hashchange', showView); showView();
const scenarios = {
  match: ['Matches this recall', 'Product, pack, lot and date align with the selected Singapore notice. Review the evidence before recording a simulated hold.', '', 'Review simulated hold →'],
  missing: ['One panel is still missing', 'The best-before date is unreadable. A shared lot is not enough to support a match. Capture the date panel or request human review.', 'Recapture 1 of 2 · illustrative counter. A correction does not reset this allowance.', 'Preview review request →'],
  stale: ['Source changed — review again', 'The genuine UK update expands the recall to Wales and Scotland. The previous result is historical; inspect the new notice before any action.', 'Historical result · approval disabled until a new current verification exists. This state preview uses a separate UK incident.', 'Verification required'],
  negative: ['No matching identity in this scope', 'Meadow Vale Brie is an invented third product. Sharing lot 232511 with either recalled cheese does not establish product identity. This is not clearance to sell.', '', 'No hold available'],
  failure: ['Review required', 'The check is unavailable. Retained evidence remains visible, but it cannot support a current match or clearance.', 'Illustrative service failure · no live model was called. Retrying must remain within the incident allowance.', 'Preview review request →']
};
function statePreview(name) {
  recallScenario = name; $('recall-details').open = false; renderRecallContext();
  const held = name === 'held';
  if (held) name = 'match';
  $('scenario').value = name; $('toast').hidden = true;
  const [title, copy, banner, action] = scenarios[name];
  $('verdict-title').textContent = title; $('verdict-copy').textContent = copy;
  $('state-banner').textContent = banner; $('state-banner').hidden = !banner;
  $('verdict').className = `verdict ${['missing','stale','failure'].includes(name) ? 'review' : name === 'negative' ? 'neutral' : ''}`;
  $('confirm-open').textContent = action; $('confirm-open').disabled = ['stale','negative'].includes(name);
  $('observed-date').textContent = name === 'missing' ? 'Unreadable' : '17 Oct 2026';
  $('label-date').textContent = name === 'missing' ? 'Not captured' : '17/10/2026';
  $('date-result').textContent = name === 'missing' ? 'Unknown' : 'Match'; $('date-result').className = `result-text ${name === 'missing' ? 'unknown' : 'match'}`;
  $('observed-product').textContent = name === 'negative' ? 'Meadow Vale Brie (synthetic)' : 'Camembert Superieur Au Lait Cru';
  $('label-name').innerHTML = name === 'negative' ? 'Meadow Vale<br>Brie' : 'Camembert<br>Superieur<br>Au Lait Cru';
  $('identity-result').textContent = name === 'negative' ? 'Different' : 'Match'; $('identity-result').className = `result-text ${name === 'negative' ? 'different' : 'match'}`;
  $('lot-result').textContent = name === 'negative' ? 'Not used' : 'Match';
  $('workbench-title').textContent = name === 'stale' ? 'Source update · review required' : name === 'negative' ? 'Different product · same lot' : 'Check a product against official recalls.';
  $('comparison-title').textContent = name === 'stale' ? 'Previous evidence · historical example' : 'Evidence, side by side';
  $('decision-title').textContent = {
    match: 'Your confirmation comes next', missing: 'Resolve the missing evidence',
    stale: 'Current verification required', negative: 'No hold supported',
    failure: 'Human review required'
  }[name];
  $('decision-copy').textContent = name === 'stale' ? 'Old results cannot authorize a new hold.' : 'A result never places stock on hold automatically.';
  const uk = name === 'stale' || name === 'failure';
  const truffle = name === 'stale';
  const product = uk ? (truffle ? 'Alyan Dubai Style Chocolate Truffles' : 'Alyan Dubai Style Crunchy Knafeh and Pistachio Milk Chocolate') : held ? 'Bertrand Pere & Fils Camembert au lait cru' : 'Camembert Superieur Au Lait Cru';
  const code = uk ? (truffle ? '319456' : '318591') : '232511';
  const pack = uk ? (truffle ? '120 g' : '100 g') : '250 g';
  const market = truffle ? 'Scotland' : uk ? 'England' : 'Singapore';
  $('observed-product').textContent = name === 'negative' ? 'Meadow Vale Brie (synthetic)' : product;
  $('source-product').textContent = product;
  $('label-name').textContent = name === 'negative' ? 'Meadow Vale Brie' : product;
  $('label-origin').textContent = uk ? 'SYNTHETIC CAPTURE' : 'FRANCE';
  ['label-size','observed-pack','source-pack'].forEach(id => $(id).textContent = pack);
  ['label-code','observed-code','source-code'].forEach(id => $(id).textContent = code);
  $('code-type').textContent = uk ? 'Product code' : 'Lot'; $('label-code-type').textContent = uk ? 'PRODUCT CODE' : 'LOT';
  $('source-date-rule').textContent = uk ? 'All dates' : '17 Oct 2026';
  if (uk) { $('observed-date').textContent = 'Not needed'; $('label-date').textContent = 'Not captured'; $('date-result').textContent = 'Unrestricted'; }
  $('observed-market').textContent = market; $('source-market').textContent = truffle ? 'England + Northern Ireland (original)' : uk ? 'England, Northern Ireland, Wales, Scotland' : 'Singapore';
  $('scope-result').textContent = truffle ? 'Historical' : 'In scope';
  $('scope-result').className = `result-text ${truffle ? 'unknown' : 'match'}`;
  $('source-pill').textContent = uk ? 'UK FSA · United Kingdom' : 'SFA · Singapore';
  $('source-title').textContent = uk ? 'Alyan chocolate recall' : 'Raw-milk cheese recall';
  $('source-date').textContent = truffle ? 'Original · 24 Sep 2026 · replaced by 25 Sep update' : uk ? 'Updated notice · 25 September 2026' : 'Notice issued 9 October 2026 · Singapore';
  $('source-link').href = uk ? 'https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026-update-1' : 'https://www.sfa.gov.sg/news-publications/newsroom/recall-of-raw-milk-cheese-products-due-to-potential-presence-of-shiga-toxin-producing-escherichia-coli';
  $('source-link').textContent = truffle ? 'Open update ↗' : 'Open source ↗';
  $('incident-id').textContent = 'Incident ' + (truffle ? 'BB-0039' : uk ? 'BB-0043' : held ? 'BB-0038' : name === 'missing' ? 'BB-0041' : name === 'negative' ? 'BB-0040' : 'BB-0042');
  $('confirm-product').textContent = `${product} · ${pack} · ${uk ? 'Product code' : 'Lot'} ${code}`;
  if (held) {
    $('workbench-title').textContent = 'Bertrand Camembert · hold history';
    $('verdict').className = 'verdict completed';
    $('verdict-title').textContent = 'Simulated hold recorded · example';
    $('verdict-copy').textContent = 'This illustrative history shows a hold recorded after a human reviewed the matching evidence. No stock action was saved in this prototype.';
    $('decision-title').textContent = 'Recorded example';
    $('decision-copy').textContent = 'The example hold is already shown. Inspect its evidence without recording a duplicate.';
    $('confirm-open').textContent = 'Hold already shown'; $('confirm-open').disabled = true;
  }
  if (name === 'failure') { $('workbench-title').textContent = 'Alyan chocolate · check unavailable'; $('comparison-title').textContent = 'Retained evidence · check unavailable'; }
  $('correction-product').value = $('observed-product').textContent;
  $('correction-code').value = code;
  $('correction-code-label').textContent = uk ? 'Product code' : 'Lot / batch';
  $('capture').hidden = uk;
  $('capture-not-needed').hidden = !uk;
  document.querySelector('.evidence-caption strong').textContent = uk ? 'Product panel' : 'Front + date panel';
  document.querySelector('.context-line').textContent = 'Historical example · ' + market;
  document.querySelectorAll('input[name="example"]').forEach(input => {input.checked = input.value === name && !held;});
  const selected = document.querySelector('input[name="example"]:checked');
  $('example-current').textContent = selected ? selected.parentElement.querySelector('strong').textContent + ' selected' : 'Other state selected';
  document.querySelectorAll('.field-pick').forEach(button => button.setAttribute('aria-pressed', 'false'));
  document.querySelectorAll('.comparison-row').forEach(row => row.classList.remove('field-selected'));
  $('field-detail').textContent = 'Select a field to inspect its label and notice values.';
  $('capture-panel').hidden = true; $('capture').setAttribute('aria-expanded', 'false');
  $('capture-file').value = ''; $('capture-status').textContent = '';
  $('correction-panel').hidden = true; $('correction').setAttribute('aria-expanded', 'false');
  if (name === 'negative') {
    $('date-result').textContent = 'Not used';
    $('decision-copy').textContent = 'No hold is supported by this example. A scoped no-match is not permission to sell.';
  }
  $('confirm-open').textContent = $('confirm-open').textContent.replace(' →', '');
  $('source-link').textContent = $('source-link').textContent.replace(' ↗', '');
  $('confirm-product').textContent += uk ? '' : ' · Best before 17 October 2026 · Singapore';


}
$('scenario').addEventListener('change', (e) => statePreview(e.target.value));
$('capture').addEventListener('click', () => { $('capture-panel').hidden = !$('capture-panel').hidden; $('capture').setAttribute('aria-expanded', String(!$('capture-panel').hidden)); });
$('correction').addEventListener('click', () => { $('correction-panel').hidden = !$('correction-panel').hidden; $('correction').setAttribute('aria-expanded', String(!$('correction-panel').hidden)); });
function toast(text, completed = false) { $('toast').textContent = text; $('toast').className = `toast${completed ? ' completed' : ''}`; $('toast').hidden = false; }
$('capture-file').addEventListener('change', e => { $('capture-status').textContent = e.target.files.length ? 'Image selected locally. Nothing was uploaded or checked.' : ''; });
$('hold-consent').addEventListener('change', (e) => { $('hold-confirm').disabled = !e.target.checked; });
$('confirm-open').addEventListener('click', () => {
  if ($('scenario').value !== 'match') { toast('Review request preview only. No request has been saved.'); return; }
  $('toast').hidden = true;
  $('hold-consent').checked = false; $('hold-confirm').disabled = true;
  $('confirm-dialog').returnValue = ''; $('confirm-dialog').showModal();
});
$('confirm-dialog').addEventListener('close', () => { if ($('confirm-dialog').returnValue === 'confirmed') toast('Confirmation preview complete. No stock action was saved.', true); });
document.querySelectorAll('[data-scenario]').forEach((a) => a.addEventListener('click', () => { statePreview(a.dataset.scenario); requestAnimationFrame(() => $('workbench-title').focus()); }));
$('new-review').addEventListener('click', () => { statePreview('match'); location.hash = 'workbench'; });
function filterQueue() { const value = $('queue-filter').value; let count = 0; document.querySelectorAll('[data-category]').forEach((row) => { row.parentElement.hidden = value !== 'all' && row.dataset.category !== value; if (!row.parentElement.hidden) count++; }); $('empty-queue').hidden = count !== 0; }
$('queue-filter').addEventListener('change', filterQueue); $('reset-filter').addEventListener('click', () => { $('queue-filter').value = 'all'; filterQueue(); $('queue-filter').focus(); });
let stage = 0;
function guidanceStage() {
  $('evaluation').hidden = stage < 1; $('activation-check').hidden = stage !== 2;
  $('guidance-state').textContent = ['Draft example','Evaluation example','Confirmation required','Active example'][stage];
  $('guidance-next').textContent = ['Preview evaluation','Review activation','Activate preview for this shop','Preview next capture'][stage];
  $('guidance-next').disabled = stage === 2 && !$('activate-consent').checked;
  document.querySelectorAll('.steps li').forEach((li,i) => {
    if (i === stage) li.setAttribute('aria-current', 'step');
    else li.removeAttribute('aria-current');
  });
}
$('activate-consent').addEventListener('change', guidanceStage);
$('guidance-next').addEventListener('click', () => {
  if (stage < 3) { stage++; if(stage === 3) { $('active-policy').textContent = 'v2 · clearer date-panel guidance (preview)'; $('guidance-status').textContent = 'Preview activated. Future examples use the clearer wording; no stored policy changed.'; $('rollback').disabled = false; $('rollback-help').textContent = 'Restore the original wording as a newer preview revision.'; $('capture-instruction').textContent = 'Photograph the complete best-before date marking. Keep the pack flat and avoid glare.'; $('capture-policy').textContent = 'Guidance v2 · preview'; } guidanceStage(); if (stage === 2) $('activate-consent').focus(); }
  else { location.hash = 'workbench'; statePreview('missing'); $('capture-panel').hidden = false; $('capture').setAttribute('aria-expanded', 'true'); }
});
$('rollback').addEventListener('click', () => { $('active-policy').textContent = 'v3 · original wording restored (preview)'; $('capture-instruction').textContent = 'Photograph the complete best-before date marking.'; $('capture-policy').textContent = 'Guidance v3 · preview'; $('guidance-status').textContent = 'Rollback preview: a new revision restores original wording. Lifetime counters stay unchanged.'; $('rollback').disabled = true; $('rollback-help').textContent = 'Original wording is already restored in this preview.'; });
$('guidance-reset').addEventListener('click', () => { stage = 0; $('activate-consent').checked = false; $('active-policy').textContent = 'v1 · original guidance'; $('guidance-status').textContent = ''; $('rollback').disabled = true; $('rollback-help').textContent = 'Available after a guidance activation preview.'; $('capture-instruction').textContent = 'Photograph the complete best-before date marking.'; $('capture-policy').textContent = 'Guidance v1 · preview'; guidanceStage(); });

document.querySelectorAll('input[name="example"]').forEach(input => input.addEventListener('change', () => statePreview(input.value)));
document.querySelectorAll('.field-pick').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.field-pick').forEach(other => other.setAttribute('aria-pressed', String(other === button)));
  document.querySelectorAll('.comparison-row').forEach(row => row.classList.remove('field-selected'));
  const row = button.closest('.comparison-row'); row.classList.add('field-selected');
  const cells = row.querySelectorAll('[role="cell"]');
  $('field-detail').textContent = `${button.textContent} selected. Label: ${cells[0].textContent}. Notice: ${cells[1].textContent}. Result: ${cells[2].textContent}.`;
}));
$('code-type').click();
addEventListener('hashchange', () => { if (views.includes(location.hash.slice(1))) document.querySelector('.view:not([hidden]) h1').focus(); });
document.querySelectorAll('.view h1').forEach(heading => heading.tabIndex = -1);

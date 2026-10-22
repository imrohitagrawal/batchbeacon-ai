'use strict';
const $ = id => document.getElementById(id);
const labels = {MATCHED_HOLD_FOR_REVIEW:'Matches this recall', NOT_LISTED_IN_CHECKED_NOTICES:'Not listed in checked notices', REVIEW_REQUIRED:'Review required', NEEDS_RENEWED_REVIEW:'Needs renewed review', SIMULATED_ACTION_RECORDED:'Workspace action recorded', IN_PROGRESS:'In progress', NEEDS_EVIDENCE:'Needs evidence', NEEDS_HUMAN_REVIEW:'Needs human review'};
const state = {config:null, csrf:null, incident:null, evidence:null, captures:[], actions:[], target:null, busy:false, pending:null, queue:null, queueDirty:true, queueReadAt:0, acquisition:null, acquisitionUnknown:false, expired:false};
const key = () => crypto.randomUUID();
const text = (id, value) => { $(id).textContent = value; };
const node = (tag, value, className) => { const e=document.createElement(tag); if(value!==undefined)e.textContent=value; if(className)e.className=className; return e; };
function message(value, kind='info') { text('app-status',value); $('app-status').hidden=!value; $('app-status').dataset.kind=kind; }
const admissionMessages = {demo_guest_capacity_unavailable:'Guest access is currently unavailable. The guided tour and example previews remain available.', guest_creation_rate_limited:'Several visitors are opening workspaces at once. Please wait a moment, then reload to try again.'};
function requireSession() { if(!state.csrf || state.expired)throw new Error(state.sessionError || (state.expired?'Your guest session expired. Reload to request a new evaluation workspace.':'Your evaluation workspace is still opening. Please wait.')); }
function safeError(e) { return e.message || 'The operation could not be confirmed. Reopen saved evidence before trying again.'; }
function pending(value) { if(value)value={...value,session_expires_at:state.expiresAt}; state.pending=value; if(value)sessionStorage.setItem('bb_pending',JSON.stringify(value)); else sessionStorage.removeItem('bb_pending'); $('recover').hidden=!value; $('learning-recover').hidden=!value || value.kind!=='learning'; }
async function api(path, {method='GET', body, operation}={}) {
  const headers={}; if(method!=='GET')headers['X-CSRF-Token']=state.csrf || '';
  if(operation)headers['Idempotency-Key']=operation;
  if(body && !(body instanceof FormData)){headers['Content-Type']='application/json';body=JSON.stringify(body);}
  let response; try { response=await fetch(path,{method,body,headers,credentials:'same-origin',cache:'no-store'}); }
  catch { const e=new Error('Connection interrupted. The outcome is unknown; reconcile before retrying.'); e.unknown=true; throw e; }
  let data; try { data=await response.json(); } catch { const reason=response.status===429 ? 'Service capacity is temporarily unavailable (429).' : `The server response could not be confirmed (${response.status}).`; const e=new Error(`${reason} Reconcile the original operation before retrying.`); e.status=response.status;e.unknown=true; throw e; }
  if(!response.ok){const e=new Error(admissionMessages[data.error] || (data.error || 'Request unavailable').replaceAll('_',' '));e.status=response.status;e.unknown=data.outcome==='unknown' || response.status>=500;if(response.status===401)expire();throw e;}
  return data;
}
function expire() { pending(null); state.expired=true; state.csrf=null; state.evidence=null; state.target=null; state.captures=[]; state.actions=[]; $('capture-images').replaceChildren(node('p','Guest access expired. Saved records are no longer accessible.')); $('comparisons').replaceChildren(); $('queue-rows').replaceChildren(); $('history').replaceChildren(); $('confirm-dialog').close(); text('session-state','Guest access expired'); text('verdict-title','Guest access expired'); text('verdict-copy','Evidence is no longer available in this session.'); text('decision-copy','Start a new evaluation workspace to continue.'); text('queue-count','Guest access expired; counts unavailable.'); $('queue-counts').replaceChildren(); text('queue-capability','Guest access expired; availability unknown.'); text('confirm-product',''); text('field-detail',''); state.queue=null;state.queueDirty=true;state.acquisition=null;state.acquisitionUnknown=false;state.learning=null;state.learningTarget=null;document.querySelector('.verdict').className='verdict neutral';text('active-wording','Guest access expired; wording unavailable.');text('proposed-wording','Guest access expired; proposal unavailable.');for(const step of $('guidance-steps').children)step.removeAttribute('aria-current');$('learning-dialog').close();$('owned-guidance').replaceChildren();$('learning-report').replaceChildren();$('learning-history').replaceChildren();text('learning-counts','Guest access expired; counts unavailable.'); message('Your guest session expired. Reload to request a new evaluation workspace.'); controls(); }
function controls() {
  const off=state.busy || !state.csrf || state.expired;
  $('refresh-queue').disabled=off; $('queue-filter').disabled=off; for(const id of ['start-sample','new-review','upload','save-correction','reverify','source-choice','sample-choice'])$(id).disabled=off || !!state.pending;
  $('upload').disabled=off || (!!state.pending && state.pending.kind!=='capture');
  $('check').disabled=off || !state.incident || !state.captures.length || !!state.pending || unresolvedAcquisition();
  text('check',state.acquisition?.state==='FAILED'?'Retry extraction':'Extract and check');
  $('refresh-acquisition').hidden=!unresolvedAcquisition(); $('refresh-acquisition').disabled=off;
  $('capture').disabled=off || !state.incident || (!!state.pending && state.pending.kind!=='capture');
  $('correction').disabled=off || !state.evidence?.observation || !!state.pending;
  const eligible=!acquisitionProblem() && state.evidence?.current && ['MATCHED_HOLD_FOR_REVIEW','REVIEW_REQUIRED'].includes(state.evidence?.result?.verdict);
  const recorded=state.actions.some(a=>a.current && !a.requires_renewed_review);
  $('confirm-open').disabled=off || !eligible || recorded || !!state.pending;
  $('hold-confirm').disabled=off || !$('hold-consent').checked || !state.target;
  $('recover').disabled=off; for(const radio of document.querySelectorAll('#example-cards input'))radio.disabled=off || !!state.pending; text('action-help',state.expired?'Guest access expired. Reload to open a new evaluation workspace.':state.busy?'Saving or checking evidence. Please wait.':state.pending?'The previous outcome needs reconciliation before another operation.':unresolvedAcquisition()?'The last outcome is unresolved. Recheck its saved status before starting another extraction.':!state.csrf?'Opening your evaluation workspace. If access is unavailable, the notice above explains why.':!state.incident?'Choose an example, then select Use this label.':!state.captures.length?'Add a readable sample label image before extraction.':recorded?'Workspace action saved. Open Retail queue to find this investigation.':'Extract and check uses the available bounded model allowance. The server explains any unavailable capacity; no action is automatic.'); learningControls(off);
}
async function task(operation) { if(state.busy)return; state.busy=true; controls(); message(''); try {await operation();}catch(e){message(safeError(e),'error');}finally{state.busy=false;controls();} }
function show(view) { for(const el of document.querySelectorAll('.view'))el.hidden=el.id!==view; for(const a of document.querySelectorAll('[data-view]')){if(a.dataset.view===view)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}text('page-name',view==='retail'?'Retail queue':view==='guidance'?'Capture guidance':'Check a product'); }
const exampleExplanations = {
  'sfa-a': 'French product name: Camembert cheese made with raw milk. “Superieur” is part of the recorded name, not a quality assessment by BatchBeacon.',
  'sfa-b': 'Bertrand Pere & Fils is the producer name. “Camembert au lait cru” means Camembert cheese made with raw milk.',
  'sfa-third': 'An invented Brie product for checking product identity separately from a shared batch number.'
};
function exampleCards() {
  const box=$('example-cards');box.replaceChildren();
  for(const sample of state.config.samples){
    const card=node('div',undefined,'example-card');const label=node('label');
    const radio=node('input');radio.type='radio';radio.name='example';radio.value=sample.id;radio.checked=sample.id===$('sample-choice').value;
    radio.addEventListener('change',()=>{$('sample-choice').value=sample.id;});
    const copy=node('span');const preview=node('img');preview.src=`/samples/${encodeURIComponent(sample.id)}.png`;preview.alt=`Sample label preview: ${sample.name}`;preview.width=1000;preview.height=700;
    copy.append(node('strong',sample.name),preview,node('small','Select Use this label to load this image for analysis.'));label.append(radio,copy);
    const help=node('details',undefined,'example-help');const summary=node('summary','ⓘ About this example');
    help.append(summary,node('p',exampleExplanations[sample.id] || 'The original product name is retained for exact identity matching.'),node('p','This label image was created for testing. Gemini reads the actual image; the linked official recall notice is real and historical. Original product names are preserved for matching.'));
    card.append(label,help);box.append(card);
  }
}
$('sample-choice').addEventListener('change',()=>{for(const radio of document.querySelectorAll('#example-cards input'))radio.checked=radio.value===$('sample-choice').value;});
function sourceView() { const selected=state.config.sources.find(s=>s.selection===$('source-choice').value); const container=$('source-summary');container.replaceChildren(); if(!selected)return; const n=selected.notice; const single=state.config.sources.length===1; $('source-choice').hidden=single; $('source-choice-label').hidden=single; $('single-source').hidden=!single; text('single-source',`Reviewed source: ${n.authority} · ${n.jurisdictions.join(', ')} · ${n.published_at}. One historical notice is available for this check.`); text('source-explanation',n.dependency.family==='sfa-cheese-2026' && n.dependency.version==='sfa-cheese-2026-10-09'?'This check uses the Singapore Food Agency (SFA) cheese recall notice published on 9 October 2026. It covers this reviewed historical notice, not all recalls. A result does not confirm that a product is safe to consume.':`This check uses the selected historical ${n.authority} notice dated ${n.published_at}. It does not search every recall or establish that a product is safe.`); container.append(node('strong',`${n.authority} · ${n.jurisdictions.join(', ')}`),node('p',`Published ${n.published_at} · historical version ${n.dependency.version}`)); const a=node('a','Open exact source notice'); a.href=n.final_url;a.target='_blank';a.rel='noreferrer';container.append(a,node('p','The selected notice describes a recall, not a contamination test of this item. Additional recall context remains under human review.','context-line')); }
function drawCaptures() { const box=$('capture-images');box.replaceChildren();if(!state.captures.length)box.append(node('p','No ready label images.'));state.captures.forEach((c,i)=>{const image=node('img');image.src=`/api/incidents/${state.incident}/captures/${c.id}`;image.alt=`Retained sample label, panel ${i+1}`;box.append(image);}); }
function compare() { const box=$('comparisons');box.replaceChildren();const result=state.evidence?.result;
  if(!result){box.append(node('p',acquisitionProblem()?'No accepted comparison is available from the last check.':'No deterministic result yet.'));return;}
  if(acquisitionProblem())box.append(node('p','Previously saved comparison · historical evidence','context-line'));
  for(const candidate of result.candidates){const section=node('section');section.append(node('h3',`${candidate.product_id} · ${candidate.eligible_jurisdiction?'within selected jurisdiction':'outside selected jurisdiction'}`));const table=node('div',undefined,'comparison-table');table.setAttribute('role','table');table.setAttribute('aria-label',`Evidence for ${candidate.product_id}`);const header=node('div',undefined,'comparison-row table-heading');header.setAttribute('role','row');for(const title of ['Field','Your label','Recall notice','Result']){const cell=node('span',title);cell.setAttribute('role','columnheader');header.append(cell);}table.append(header);
    for(const r of [candidate.identity,...candidate.predicates]){const row=node('div',undefined,'comparison-row');row.setAttribute('role','row');const head=node('strong');head.setAttribute('role','rowheader');const button=node('button',r.field.replaceAll('_',' '),'field-pick');button.type='button';button.setAttribute('aria-pressed','false');head.append(button);const source=r.source_values.length?r.source_values.join(' / '):r.source_date_range?`${r.source_date_range.lower_inclusive?"[":"("}${r.source_date_range.lower} – ${r.source_date_range.upper}${r.source_date_range.upper_inclusive?"]":")"}`:r.source_operator || 'Not specified';const outcome=r.outcome==='NOT_APPLICABLE'?'Not used':r.outcome.toLowerCase();button.addEventListener('click',()=>{for(const b of box.querySelectorAll('button'))b.setAttribute('aria-pressed','false');button.setAttribute('aria-pressed','true');for(const selected of box.querySelectorAll('.field-selected'))selected.classList.remove('field-selected');row.classList.add('field-selected');text('field-detail',`${r.field}: label ${r.observed ?? 'Unknown'}; notice ${source}; ${outcome}. ${r.reason.replaceAll('_',' ')}. Operator: ${r.source_operator || 'identity'}; applies: ${r.source_applies ?? 'not specified'}. Source evidence: ${r.source_evidence.map(e=>`${e.artifact_id} · ${e.locator} · SHA256 ${e.sha256}`).join('; ') || 'none'}. Label evidence: ${r.observation_evidence.map(e=>`${e.artifact_id} · ${e.locator} · SHA256 ${e.sha256}`).join('; ') || 'none'}.`);});row.append(head);for(const value of [r.observed ?? 'Unknown',source,outcome]){const c=node('span',value);c.setAttribute('role','cell');row.append(c);}table.append(row);}section.append(table);box.append(section); }
}
function fields() {const obs=state.evidence?.observation;if(!obs)return [];return [{field:'PRODUCT_NAME',observation:obs.identity.name},{field:'PACK',observation:obs.identity.pack},...obs.fields];}
function correctionValue() {const f=fields().find(f=>f.field===$('correction-field').value);$('correction-value').value=f?.observation.value ?? '';}
function captureInstruction() {const result=state.evidence?.result;text('capture-instruction',result?.outstanding_fields?.length ? `Required evidence: ${result.outstanding_fields.join(', ').replaceAll('_',' ')}. Include the complete requested marking; keep case and leading zeros readable.` : 'Include the full product name, pack, lot and required date panel. Preserve readable case and leading zeros.');}
function unresolvedAcquisition() { return state.acquisitionUnknown || ['INCOMPLETE','TIMED_OUT'].includes(state.acquisition?.state); }
function acquisitionProblem() {
  if(state.acquisitionUnknown)return {title:'Check status unavailable',copy:'The last check could not be read. Recheck its saved status; no new extraction has been started.'};
  const a=state.acquisition;
  if(!a || a.current || a.state==='COMPLETE')return null;
  const reasons={
    ALLOWANCE_UNAVAILABLE:'The available AI allowance could not admit this check. Saved evidence remains available; a new attempt still requires server admission.',
    PROVIDER_UNAVAILABLE:'The AI service could not complete this check. You may explicitly retry when service capacity is available.',
    CHECK_FAILED:'The check failed before a usable extraction was saved. Its precise cause is unavailable here. You may explicitly retry within the remaining allowance.',
    PROPOSAL_INVALID:'The proposed extraction was not accepted. Inspect the retained label before explicitly retrying or adding a readable capture.',
    IDENTITY_EVIDENCE_DISAGREEMENT:'The extracted identity disagrees with the retained label evidence. No new comparison or action was created.',
    IDENTITY_INPUT_UNAVAILABLE:'This label cannot establish identity within the reviewed image scope. Choose an approved example or retain it for review.',
    SOURCE_DISAGREEMENT:'The proposed source conditions disagree with reviewed evidence. No new comparison or action was created.',
    SOURCE_REVIEW_REQUIRED:'The source interpretation requires review before a comparison can be accepted.'
  };
  if(a.state==='INCOMPLETE')return {title:'Check outcome unresolved',copy:'The saved operation is not complete. Recheck its status before another extraction; this does not start an AI call.'};
  if(a.state==='TIMED_OUT')return {title:'Extraction timed out',copy:'This check reached its deadline without a confirmed result. Recheck saved status without starting another AI call. If it remains timed out, operator review is required; another extraction is unavailable in this workspace.'};
  if(a.state==='STALE' || a.state==='SUPERSEDED')return {title:'Evidence needs renewed review',copy:'The previous check no longer supports a current action. Review and reverify the saved evidence.'};
  return {title:a.state==='FAILED'?'Extraction failed':'Extraction needs review',copy:reasons[a.diagnostics?.[0]] || 'No accepted comparison is available from this check. Review the retained evidence before explicitly trying again.'};
}
function render() {const e=state.evidence;const result=e?.result;const failed=e?.extraction_history?.at(-1)?.validation==='INVALID';const problem=acquisitionProblem();const recorded=state.actions.find(a=>a.current&&!a.requires_renewed_review);text('incident-id',state.incident?`Incident ${state.incident.slice(0,8)}`:'No incident selected');
  document.querySelector('.verdict').className='verdict'+(problem?' neutral':recorded?' completed':(!result || result.verdict==='NOT_LISTED_IN_CHECKED_NOTICES')?' neutral':'');
  text('verdict-title',problem?problem.title:recorded?'Workspace action recorded':e?.observation&&!e.current?'Evidence needs renewed review':result?labels[result.verdict]:failed?'Extraction needs review':'Ready for evidence');
  text('verdict-copy',problem?`${problem.copy}${result?' Previous saved comparison is historical; it cannot authorize a new action.':''}`:recorded?(recorded.action.action_type==='SIMULATED_HOLD'?'A stock hold was recorded in this workspace. No live inventory was changed.':'A request for further review was saved in this workspace. Uncertainty remains unresolved.'):result?`Checked ${result.checked_sources.length} selected notice version(s). ${e.current?'Current for the saved historical source selection.':'Historical result; no new action is available.'}`:failed?'The extraction was not accepted. Review the retained evidence; no comparison or action was created.':'Choose an example and use its label, then select Extract and check.');
  text('decision-title',problem?'Resolve the check before an action':recorded?'Saved workspace action':'Your confirmation comes next');
  text('decision-copy',problem?'No new action is available from this check. Retained evidence and earlier actions remain in the review history.':result?.verdict==='NOT_LISTED_IN_CHECKED_NOTICES'?'No hold is supported by these checked notices. This is not safety, clearance or permission to sell.':recorded?'The server retains the confirmed evidence revisions and source epochs.':'A result never places stock on hold automatically.');
  captureInstruction(); const action=result?.verdict==='REVIEW_REQUIRED'?'Review follow-up request':'Review stock hold';text('confirm-open',action);$('reverify').hidden=!e?.observation || !!e.current;compare();
  $('correction-field').replaceChildren(...fields().map(f=>{const o=node('option',f.field.replaceAll('_',' '));o.value=f.field;return o;}));correctionValue();
  const history=$('history');history.replaceChildren();for(const x of e?.extraction_history || [])history.append(node('p',`Extraction v${x.revision} · ${x.validation==='INVALID'?'not accepted':'accepted'} · ${x.prompt_version}`));for(const o of e?.observation_history || [])history.append(node('p',`Observation v${o.revision} · extraction v${o.extraction_revision} · ${o.correction_count} correction(s)`));for(const r of e?.result_history || [])history.append(node('p',`Result v${r.revision} · observation v${r.observation_revision} · ${labels[r.verdict]} · ${r.checked_sources.map(s=>s.version).join(', ')}`));for(const f of fields())history.append(node('p',`${f.field}: raw “${f.observation.raw}”; normalized “${f.observation.value ?? 'Unknown'}”; state ${f.observation.state}`)); for(const c of e?.observation?.corrections || [])history.append(node('p',`Correction ${c.field}: “${c.previous.value ?? c.previous.raw}” → “${c.replacement.value ?? c.replacement.raw}”`)); for(const a of state.actions)history.append(node('p',`${a.action.action_type==='SIMULATED_HOLD'?'Stock hold':'Request for further review'} · result v${a.action.result_revision} · ${a.requires_renewed_review?'historical — renewed review required':'current saved action'}`)); controls(); }
async function loadIncident(id, knownAcquisition=null) {
  state.incident=id;state.evidence=null;state.actions=[];state.target=null;state.captures=[];state.acquisition=knownAcquisition;state.acquisitionUnknown=false;
  drawCaptures();render();$('capture-panel').hidden=true;$('correction-panel').hidden=true;$('capture-file').value='';text('capture-status','');
  const url=new URL(location.href);url.searchParams.set('incident',id);history.replaceState(null,'',url);
  const [e,c,a]=await Promise.all([api(`/api/incidents/${id}/evidence`),api(`/api/incidents/${id}/captures`),api(`/api/incidents/${id}/actions`)]);
  state.evidence=e;state.captures=c.batches.filter(b=>b.ready).at(-1)?.captures || [];state.actions=a.actions;
  if(e.latest_run_id){
    try {state.acquisition=await api(`/api/incidents/${id}/acquisitions/${e.latest_run_id}`);}
    catch(error){if(state.expired)throw error;state.acquisitionUnknown=true;message('Saved check status is unavailable. Recheck it before another extraction.','error');}
  }
  drawCaptures();render();show('workbench');
}

async function captureFiles(files) {
  return Promise.all(files.map(async file=>({bytes:file.size,sha256:[...new Uint8Array(await crypto.subtle.digest('SHA-256',await file.arrayBuffer()))].map(x=>x.toString(16).padStart(2,'0')).join('')})));
}
async function reconcileCapture(p) {
  return api(`/api/incidents/${p.incident}/capture-reconciliation`,{operation:p.operation});
}
async function upload(files) {
  if(!files.length)throw new Error('Choose at least one sample label image.');
  if(files.length>state.config.max_images || files.some(f=>f.size>state.config.max_image_bytes))throw new Error('The selected images exceed this workspace’s upload limits.');
  if(state.pending && state.pending.kind!=='capture')throw new Error('Reconcile the pending operation first.');
  const resuming=!!state.pending;
  const fingerprints=await captureFiles(files);
  if(state.pending) {
    const p=state.pending;
    if(p.incident!==state.incident || JSON.stringify(p.files)!==JSON.stringify(fingerprints))throw new Error('Select the same original images in the same order to resume this upload.');
    const observed=await reconcileCapture(p);
    if(observed.found && observed.batch.ready){pending(null);await loadIncident(p.incident);message('The original upload is already retained. No images were uploaded again.');return;}
  } else pending({kind:'capture',incident:state.incident,operation:key(),files:fingerprints});
  const operation=state.pending.operation;
  const data=new FormData();files.forEach(f=>data.append('images',f));
  try {
    const result=await api(`/api/incidents/${state.incident}/captures`,{method:'POST',operation,body:data});
    if(!result.ready){const e=new Error('The original upload is pending. Reconcile before continuing.');e.unknown=true;throw e;}
    pending(null);state.captures=result.captures;drawCaptures();text('capture-status','Images retained for this incident. Select Extract and check to process them.');
  } catch(e){if(!e.unknown && !resuming)pending(null);throw e;}
}
async function startSample() {const response=await fetch(`/samples/${$('sample-choice').value}.png`);if(!response.ok)throw new Error('Sample unavailable.');const blob=await response.blob();const created=await api('/api/incidents',{method:'POST',operation:key()});state.incident=created.incident_id;state.queueDirty=true;await upload([new File([blob],'synthetic-label.png',{type:'image/png'})]);await loadIncident(state.incident);message('Sample label uploaded. Extract and check when ready.');}
async function acquire() {state.queueDirty=true;const operation=key();pending({kind:'acquisition',incident:state.incident,operation});try{const result=await api(`/api/incidents/${state.incident}/acquisitions`,{method:'POST',operation,body:{source_selection:$('source-choice').value,capture_ids:state.captures.map(c=>c.id),expected_observation_revision:state.evidence.latest_observation_revision}});if(['INCOMPLETE'].includes(result.state)){state.acquisition=result;render();message('Acquisition is incomplete. Reconcile the original request before starting another.');return;}pending(null);await loadIncident(state.incident,result);const problem=acquisitionProblem();message(problem?problem.copy:'Extraction and comparison completed.',problem?'error':'success');}catch(e){if(!e.unknown)pending(null);else if(!state.expired){state.acquisitionUnknown=true;render();}throw e;}}
async function prepare() {const kind=state.evidence.result.verdict==='MATCHED_HOLD_FOR_REVIEW'?'SIMULATED_HOLD':'SIMULATED_REVIEW_REQUEST';const data=await api(`/api/incidents/${state.incident}/actions/prepare?action_type=${kind}`);if(data.target.observation_revision!==state.evidence.observation.revision || data.target.result_revision!==state.evidence.result.revision){await loadIncident(state.incident);throw new Error('Evidence changed before confirmation. Review the newly loaded values, then prepare the action again.');}state.target=data.target;text('confirm-title',kind==='SIMULATED_HOLD'?'Review this stock hold':'Review this follow-up request');text('confirm-product',`${state.evidence.observation.identity.name.value || 'Unresolved identity'} · ${state.evidence.observation.identity.pack.value || 'Unknown pack'} · ${state.evidence.observation.fields.map(f=>`${f.field}: ${f.observation.value ?? 'Unknown'}`).join(' · ')} · observation v${data.target.observation_revision} · result v${data.target.result_revision} · sources ${state.evidence.result.checked_sources.map(s=>`${s.version} (epoch ${s.epoch})`).join(', ')}`);text('hold-confirm',kind==='SIMULATED_HOLD'?'Confirm stock hold':'Confirm review request');$('hold-consent').checked=false;text('confirm-status','');$('confirm-dialog').showModal();controls();}
async function confirm() {state.queueDirty=true;const target=state.target;pending({kind:'action',incident:state.incident,operation:key(),target});try{await api(`/api/incidents/${state.incident}/actions`,{method:'POST',operation:state.pending.operation,body:{target,explicit_confirmation:true}});pending(null);$('confirm-dialog').close();await loadIncident(state.incident);message('Workspace action saved. No live inventory was changed.');}catch(e){$('confirm-dialog').close();if(!e.unknown)pending(null);state.target=null;await loadIncident(state.incident);throw e;}}
async function recover() {state.queueDirty=true;const p=state.pending;if(!p)return;if(p.kind==='capture'){const result=await reconcileCapture(p);if(result.found && result.batch.ready){pending(null);await loadIncident(p.incident);message('The original upload is retained. No images were uploaded again.');}else{await loadIncident(p.incident);show('workbench');$('capture-panel').hidden=false;$('capture').setAttribute('aria-expanded','true');message('The original upload is '+(result.found?'pending':'not recorded')+'. Select the same original images in the same order, then Upload selected images to resume its original request.');}return;}else if(p.kind==='learning'){const value=await api(p.path,{method:'POST',operation:p.operation,body:p.body});pending(null);renderLearning(value.learning_state);show('guidance');return;}else if(p.kind==='verification'){await api(`/api/incidents/${p.incident}/verifications`,{method:'POST',operation:p.operation});}else if(p.kind==='acquisition'){const result=await api(`/api/incidents/${p.incident}/acquisitions/reconcile`,{operation:p.operation});if(result.state==='INCOMPLETE'){message('The original acquisition is still unresolved. No new request was started.');return;}}else{const result=await api(`/api/incidents/${p.incident}/actions/reconcile?result_revision=${p.target.result_revision}&action_type=${p.target.action_type}`);if(!result.found){message('No committed action found. Review the current evidence before making another decision.');}}pending(null);await loadIncident(p.incident);}
async function refresh() {requireSession();const remaining=state.queueReadAt+(state.config.refresh_interval_seconds*1000)-Date.now();if(remaining>0){text('queue-status','Waiting briefly before refreshing the saved snapshot…');await new Promise(resolve=>setTimeout(resolve,remaining));requireSession();}text('queue-status','Refreshing this workspace…');try{const data=await api(`/api/retail/queue?filter=${$('queue-filter').value}`,{operation:key()});state.queue=data;state.queueDirty=false;state.queueReadAt=Date.now();const rows=data.snapshot.rows;const container=$('queue-rows');container.replaceChildren();text('queue-count',`${rows.length} saved incident(s) · ${data.visible_count} shown · snapshot ${new Date(data.snapshot.generated_at).toLocaleTimeString()}`);$('queue-counts').replaceChildren(...Object.entries(data.snapshot.category_counts).map(([category,n])=>node('span',`${labels[category]}: ${n}`)));for(const row of rows.filter(r=>data.visible_incident_ids.includes(r.incident_id))){const item=node('div');item.setAttribute('role','listitem');const link=node('a',undefined,'queue-row');link.href=`?incident=${row.incident_id}#workbench`;link.addEventListener('click',e=>{e.preventDefault();task(()=>loadIncident(row.incident_id));});const name=node('div');name.append(node('strong',row.product_name),node('small',`Incident ${row.incident_id.slice(0,8)} · observation v${row.observation_revision}`));link.append(name,node('span',row.jurisdiction),node('span',labels[row.category],`state-tag ${row.category==='SIMULATED_ACTION_RECORDED'?'completed':'neutral'}`),node('span',row.current?'View saved evidence':'Review evidence'));item.append(link);container.append(item);}if(!data.visible_count)container.append(node('p','No incidents match this filter.','empty-state'));text('queue-capability',`Saved evidence: ${data.saved_evidence.state.toLowerCase()}. New verification: ${data.new_verification.state.toLowerCase()}. Counts cover this evaluation workspace only.`);text('queue-status','Manual refresh complete. No model call was made.');}catch(e){text('queue-status',`Refresh unavailable. ${state.queue?'The displayed snapshot is historical; its counts are not a current reading.':'Counts are unknown.'}`);throw e;}}
for(const a of document.querySelectorAll('[data-view]'))a.addEventListener('click',e=>{e.preventDefault();show(a.dataset.view);if(a.dataset.view==='retail'&&(!state.queue||state.queueDirty))task(refresh);if(a.dataset.view==='guidance'&&state.config?.guidance==='OWNED_LIFECYCLE_CONNECTED')task(loadLearning);});
$('new-review').addEventListener('click',()=>{show('workbench');$('sample-choice').focus();});
for(const id of ['capture','correction'])$(id).addEventListener('click',()=>{const p=$(id+'-panel');p.hidden=!p.hidden;$(id).setAttribute('aria-expanded',String(!p.hidden));});
$('source-choice').addEventListener('change',sourceView);$('correction-field').addEventListener('change',correctionValue);
$('start-sample').addEventListener('click',()=>task(startSample));$('check').addEventListener('click',()=>task(acquire));$('upload').addEventListener('click',()=>task(()=>upload([...$('capture-file').files])));
$('confirm-open').addEventListener('click',()=>task(prepare));$('hold-consent').addEventListener('change',controls);$('hold-confirm').addEventListener('click',()=>task(confirm));$('recover').addEventListener('click',()=>task(recover));
$('confirm-dialog').addEventListener('close',()=>{state.target=null;$('hold-consent').checked=false;controls();$('confirm-open').focus();});
$('save-correction').addEventListener('click',()=>task(async()=>{state.queueDirty=true;const f=fields().find(f=>f.field===$('correction-field').value);const replacement={...f.observation,state:'KNOWN',value:$('correction-value').value,raw:$('correction-value').value};await api(`/api/incidents/${state.incident}/corrections`,{method:'POST',operation:key(),body:{expected_revision:state.evidence.latest_observation_revision,field:f.field,replacement}});await loadIncident(state.incident);message('Correction saved. Previous results are historical until re-verification.');}));
$('reverify').addEventListener('click',()=>task(async()=>{state.queueDirty=true;const operation=key();pending({kind:'verification',incident:state.incident,operation});try {await api(`/api/incidents/${state.incident}/verifications`,{method:'POST',operation});pending(null);}catch(e){if(!e.unknown)pending(null);throw e;}await loadIncident(state.incident);message('Corrected evidence was deterministically re-verified. No model call was made.');}));
$('refresh-acquisition').addEventListener('click',()=>task(()=>loadIncident(state.incident)));
$('refresh-queue').addEventListener('click',()=>task(refresh));$('queue-filter').addEventListener('change',()=>task(refresh));
async function init() {state.config=await api('/api/workbench/config');if(state.config.mode==='REAL_VERTEX_EXTRACTION'){text('runtime-title','BatchBeacon AI');text('runtime-detail','Real AI analysis · Non-production data');text('result-disclosure','Server result · Gemini extraction');}else{text('runtime-title','Local integration');text('runtime-detail','Test extraction · Non-production data · Test storage');text('result-disclosure','Server result · test extraction');}for(const row of state.config.samples){const option=node('option',row.name);option.value=row.id;$('sample-choice').append(option);}for(const row of state.config.sources){const option=node('option',`${row.notice.authority} · ${row.notice.dependency.version}`);option.value=row.selection;$('source-choice').append(option);}exampleCards();sourceView();if(state.config.guidance==='OWNED_LIFECYCLE_CONNECTED'){$('learning-controls').hidden=false;text('guidance-state-title','Your workspace’s capture guidance');text('guidance-state-copy','Saved requests, feedback and evaluated wording changes belong to this evaluation workspace only.');}else{text('guidance-state-copy','Capture guidance is unavailable in this configuration.');}let session;try{session=await api('/api/guest',{method:'POST'});}catch(e){state.sessionError=safeError(e);text('session-state',state.expired?'Guest access expired':'Guest access unavailable');text('queue-count','Guest access unavailable; counts unknown.');text('learning-counts','Guest access unavailable; counts unknown.');throw e;}state.csrf=session.csrf_token;state.expiresAt=session.expires_at;text('session-state',`Workspace access expires ${new Date(session.expires_at).toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'})}`);const ttl=Date.parse(session.expires_at)-Date.parse(state.config.server_time);if(ttl>0)setTimeout(expire,ttl);try{const saved=JSON.parse(sessionStorage.getItem('bb_pending')||'null');pending(saved?.session_expires_at===session.expires_at?saved:null);}catch{pending(null);}const id=new URLSearchParams(location.search).get('incident')||state.pending?.incident;if(id)await loadIncident(id);else{const view=document.querySelector('nav [aria-current=page]')?.dataset.view;if(view==='retail')await refresh();if(view==='guidance'&&state.config.guidance==='OWNED_LIFECYCLE_CONNECTED')await loadLearning();}controls();}
task(init);

function learningSelection() {
  const l=state.learning;
  const request=l?.requests.filter(r=>r.basis.incident_id===state.incident).at(-1);
  const feedback=l?.feedback.filter(f=>f.basis.incident_id===state.incident).at(-1);
  const candidate=l?.candidates.filter(c=>c.supports.some(s=>s.basis.incident_id===state.incident)).at(-1);
  const evaluation=l?.evaluations.filter(e=>e.candidate.id===candidate?.id).at(-1);
  return {request,feedback,candidate,evaluation};
}
function currentGuidance(request) {const e=state.evidence,a=state.learning?.active;return !!(request && e?.current && request.basis.incident_id===state.incident && request.basis.observation.revision===e.observation?.revision && request.basis.result.revision===e.result?.revision && request.binding.activation_revision===a?.activation_revision && request.binding.policy.content_hash===a?.policy.content_hash);}
function learningControls(off) {
  const enabled=state.config?.guidance==='OWNED_LIFECYCLE_CONNECTED';
  const blocked=off || !enabled || !!state.pending;
  const context=state.learning?.context;
  const valid=context && context.incident_id===state.incident;
  const actionIds={request:'guidance-request',feedback:'feedback-save',candidate:'candidate-create',evaluate:'candidate-evaluate',activate:'learning-activate',rollback:'learning-rollback'};
  $('learning-refresh').disabled=off || !enabled;
  $('learning-recover').disabled=off;
  for(const [name,id] of Object.entries(actionIds)){
    const availability=valid?context.actions[name]:null;
    $(id).disabled=blocked || !availability?.available;
    text(id+'-help',availability?.reason || 'Refresh guidance for the selected investigation.');
    $(id).classList.remove('primary');$(id).classList.add('secondary');
  }
  $('learning-confirm').disabled=blocked || !state.learningTarget || !$('learning-consent').checked;
  const {request,feedback,candidate,evaluation}=learningSelection();
  text('guidance-context',state.incident?`Selected investigation ${state.incident.slice(0,8)}${state.evidence?.observation?.identity?.name?.value?' · '+state.evidence.observation.identity.name.value:''}`:'No investigation selected');
  text('guidance-next',valid?context.summary:'Open an investigation and refresh guidance to see its available next step.');
  $('guidance-empty').hidden=!!state.incident;
  $('guidance-feedback-section').hidden=!state.incident;
  $('guidance-proposal-section').hidden=!feedback && !candidate;
  $('guidance-confirm-section').hidden=!candidate && !state.learning?.transitions.length;
  $('proposed-wording-panel').hidden=!candidate;
  document.querySelector('.guidance-feedback').open=!!request && !feedback;
  $('guidance-steps').hidden=!state.incident;
  let next=null;
  if(valid && !blocked){
    if(context.actions.rollback.available)next='learning-rollback';
    else if(context.actions.activate.available)next='learning-activate';
    else if(candidate && context.actions.evaluate.available && evaluation?.status!=='PASSED')next='candidate-evaluate';
    else if(context.actions.candidate.available && (!candidate || !candidate.supports.some(s=>s.feedback.id===feedback?.id)))next='candidate-create';
    else if(request && !feedback && context.actions.feedback.available)next='feedback-save';
    else if(context.actions.request.available)next='guidance-request';
  }
  if(next){$(next).classList.remove('secondary');$(next).classList.add('primary');}
}

async function loadLearning() {
  requireSession();
  try {
    const l=await api('/api/learning'+(state.incident?'?incident='+encodeURIComponent(state.incident):''),{operation:key()});renderLearning(l);
  } catch(e) {text('learning-counts',state.learning?'Refresh failed. Displayed records are historical; current counts are unknown.':'Guidance records unavailable; counts unknown.');throw e;}
}
function renderLearning(l) {
    state.learning=l;
    const {request,feedback,candidate,evaluation}=learningSelection();
    const policyText=(id)=>state.config.guidance_policies[id]?.instructions.map(i=>i.text).join(' ') || 'Wording unavailable.';
    text('active-wording',`${l.active.policy.id.replaceAll('_',' ')} · revision ${l.active.activation_revision}. ${policyText(l.active.policy.id)}`);
    text('proposed-wording',candidate?`${candidate.proposed.id.replaceAll('_',' ')}. ${policyText(candidate.proposed.id)} Status: ${candidate.status.replaceAll('_',' ')}.`:'No saved proposal. Record incident-linked feedback first.');
    const stage=evaluation?.status==='PASSED'?3:candidate?2:feedback?1:0;for(const [i,item] of [...$('guidance-steps').children].entries()){if(i===stage)item.setAttribute('aria-current','step');else item.removeAttribute('aria-current');}
    text('guidance-state-title','Capture guidance for this investigation');text('guidance-policy-state',`${l.active.policy.id.replaceAll('_',' ')} · revision ${l.active.activation_revision}`);
    text('learning-counts',`${l.feedback.length}/${l.limits.feedback} feedback · ${l.candidates.length}/${l.limits.candidates} candidates · ${l.evaluations.length}/${l.limits.evaluations} actual attempts · observed ${new Date(l.observed_at).toLocaleTimeString()}`);
    text('owned-guidance',request?`${request.instructions.map(i=>i.text).join(' ')} Saved under ${request.binding.policy.id}, revision ${request.binding.activation_revision}.`:'No saved request for this incident. Current required fields and available capacity determine whether guidance can be requested.');
    if(currentGuidance(request))text('capture-instruction',request.instructions.map(i=>i.text).join(' '));else {captureInstruction();if(request)text('owned-guidance',`${$('owned-guidance').textContent} Historical saved guidance; request current guidance before using it for this evidence or wording revision.`);}
    text('candidate-state',candidate?`${candidate.status.replaceAll('_',' ')} · ${candidate.base.policy.id} → ${candidate.proposed.id}. ${evaluation?`Attempt ${evaluation.attempt_number}: ${evaluation.status}.`:'Not evaluated.'}`:feedback?`Feedback ${feedback.detail.replaceAll('_',' ').toLowerCase()} recorded. Source/extraction disputes require human investigation.`:'No candidate exists. Record evidence-linked feedback first.');
    const report=$('learning-report');report.replaceChildren();
    for(const e of l.evaluations){report.append(node('p',`Attempt ${e.attempt_number}: ${e.status}${e.failure?` · ${e.failure.replaceAll('_',' ')}`:''}`));for(const c of e.execution?.cases || [])report.append(node('p',`${c.case}: ${c.passed?'passed':'failed'} · ${c.variants.map(v=>v.variant.replaceAll('_',' ')).join(', ')}`));}
    if(!l.evaluations.length)report.append(node('p','No actual execution recorded.'));
    $('learning-history').replaceChildren(...l.transitions.map(t=>node('p',`${t.kind}: ${t.previous.policy.id} r${t.previous.activation_revision} → ${t.next.policy.id} r${t.next.activation_revision}. Saved historical transition.`)));
}
async function learningMutation(path,body) {
  if(state.incident)path+='?incident='+encodeURIComponent(state.incident);
  const operation=key();pending({kind:'learning',incident:state.incident,operation,path,body});
  try {const value=await api(path,{method:'POST',operation,body});pending(null);renderLearning(value.learning_state);return value;}
  catch(e){if(!e.unknown)pending(null);throw e;}
}
async function prepareLearning(kind) {
  const evaluation=learningSelection().evaluation;
  const target=await api(kind==='activate'?`/api/learning/activation/prepare?evaluation=${evaluation.id}`:'/api/learning/rollback/prepare');
  state.learningTarget={kind,target};$('learning-consent').checked=false;
  text('learning-confirm-title',kind==='activate'?'Review evaluated capture wording':'Review guidance rollback');
  const box=$('learning-preview');box.replaceChildren();
  for(const id of ['GUIDANCE_V1','GUIDANCE_V2']){box.append(node('h3',id.replaceAll('_',' ')));for(const item of state.config.guidance_policies[id].instructions)box.append(node('p',item.text));}
  box.append(node('p',kind==='activate'?`Passing evaluation ${evaluation.id.slice(0,8)}. Base activation revision ${target.base.activation_revision}.`:`Return to prior wording with a new revision after ${target.current.activation_revision}. Earlier records stay unchanged.`));
  $('learning-dialog').showModal();
}
$('guidance-start').addEventListener('click',()=>{show('workbench');$('sample-choice').focus();});
$('guidance-queue').addEventListener('click',()=>{show('retail');if(!state.queue||state.queueDirty)task(refresh);});
$('learning-refresh').addEventListener('click',()=>task(async()=>{await loadLearning();message('Capture guidance records refreshed.','success');}));
$('learning-recover').addEventListener('click',()=>task(recover));
$('guidance-request').addEventListener('click',()=>task(()=>learningMutation(`/api/incidents/${state.incident}/guidance`)));
$('feedback-save').addEventListener('click',()=>task(()=>learningMutation(`/api/incidents/${state.incident}/feedback`,{detail:$('feedback-detail').value,request_id:currentGuidance(learningSelection().request)?learningSelection().request.id:null})));
$('candidate-create').addEventListener('click',()=>task(()=>learningMutation('/api/learning/candidates',{feedback_ids:[learningSelection().feedback.id]})));
$('candidate-evaluate').addEventListener('click',()=>task(()=>learningMutation(`/api/learning/candidates/${learningSelection().candidate.id}/evaluations`)));
$('learning-activate').addEventListener('click',()=>task(()=>prepareLearning('activate')));
$('learning-rollback').addEventListener('click',()=>task(()=>prepareLearning('rollback')));
$('learning-consent').addEventListener('change',controls);
$('learning-confirm').addEventListener('click',()=>task(async()=>{const {kind,target}=state.learningTarget;const body=kind==='activate'?{basis:target,explicit_confirmation:true}:{...target,explicit_confirmation:true};$('learning-dialog').close();await learningMutation(`/api/learning/${kind==='activate'?'activation':'rollback'}`,body);message('Wording transition saved for this evaluation workspace. Request fresh guidance to see its effect.');}));
$('learning-dialog').addEventListener('close',()=>{state.learningTarget=null;$('learning-consent').checked=false;controls();});

// Optional explanatory overlay; shared copy, no API or workflow side effects.
let tourStep=0;
const tourItems=()=>[...document.querySelectorAll('.quick-tour li')];
function renderTour(){const items=tourItems();text('tour-title',`Step ${tourStep+1} of ${items.length}`);text('tour-text',items[tourStep].textContent);$('tour-back').disabled=tourStep===0;text('tour-next',tourStep===items.length-1?'Done':'Next');$('tour-title').focus();}
$('tour-open').addEventListener('click',()=>{tourStep=0;$('tour-dialog').showModal();renderTour();});
$('tour-back').addEventListener('click',()=>{if(tourStep>0){tourStep--;renderTour();}});
$('tour-next').addEventListener('click',()=>{if(tourStep===tourItems().length-1)$('tour-dialog').close();else{tourStep++;renderTour();}});
$('tour-skip').addEventListener('click',()=>$('tour-dialog').close());
$('tour-dialog').addEventListener('close',()=>$('tour-open').focus());

'use strict';
const $ = id => document.getElementById(id);
const labels = {MATCHED_HOLD_FOR_REVIEW:'Matches this recall', NOT_LISTED_IN_CHECKED_NOTICES:'Not listed in checked notices', REVIEW_REQUIRED:'Review required', NEEDS_RENEWED_REVIEW:'Needs renewed review', SIMULATED_ACTION_RECORDED:'Workspace action recorded', IN_PROGRESS:'In progress', NEEDS_EVIDENCE:'Needs evidence', NEEDS_HUMAN_REVIEW:'Needs human review'};
const state = {config:null, csrf:null, incident:null, evidence:null, captures:[], actions:[], target:null, busy:false, pending:null, pendingOwnershipUnknown:false, queue:null, queueDirty:true, queueReadAt:0, acquisition:null, acquisitionUnknown:false, expired:false, capabilities:null, workspaceBlock:null, selection:0, sessionGeneration:0, viewGeneration:0, view:"workbench", operation:null, checkFailure:null, loading:false};
const key = () => crypto.randomUUID();
const text = (id, value) => { $(id).textContent = value; };
const node = (tag, value, className) => { const e=document.createElement(tag); if(value!==undefined)e.textContent=value; if(className)e.className=className; return e; };
function message(value, kind='info') { if(state.expired && !value.includes('expired'))return; if(state.operation && (state.operation.selection!==state.selection || (state.operation.incident && state.operation.incident!==state.incident)))return; if(state.operation)operationStatus(state.operation.region,value,kind);  text('app-status',value); $('app-status').hidden=!value; $('app-status').dataset.kind=kind; }
const admissionMessages = {demo_guest_capacity_unavailable:'Guest access is currently unavailable. The guided tour and example previews remain available.', guest_creation_rate_limited:'Several visitors are opening workspaces at once. Please wait a moment, then reload to try again.'};
function requireSession() { if(!state.csrf || state.expired)throw new Error(state.sessionError || (state.expired?'Your guest session expired. Reload to request a new evaluation workspace.':'Your evaluation workspace is still opening. Please wait.')); }
function safeError(e) { return e.message || 'The operation could not be confirmed. Reopen saved evidence before trying again.'; }
function pending(value) { if(value)value={...value,session_expires_at:state.expiresAt}; state.pending=value;state.pendingOwnershipUnknown=false; if(value)sessionStorage.setItem('bb_pending',JSON.stringify(value)); else sessionStorage.removeItem('bb_pending'); $('recover').hidden=!value; $('learning-recover').hidden=!value || value.kind!=='learning'; }
async function api(path, {method='GET', body, operation}={}) {
  const generation=state.sessionGeneration;
  const assertActive=()=>{if(state.expired || generation!==state.sessionGeneration){const e=new Error('Stale response');e.stale=true;throw e;}};
  const headers={}; if(method!=='GET')headers['X-CSRF-Token']=state.csrf || '';
  const progress=method==='POST' && /^\/api\/incidents\/[a-f0-9]{32}\/acquisitions$/.test(path);
  if(progress)headers['X-BatchBeacon-Progress']='acquisition-progress-v1';
  if(operation)headers['Idempotency-Key']=operation;
  if(body && !(body instanceof FormData)){headers['Content-Type']='application/json';body=JSON.stringify(body);}
  let response; try { response=await fetch(path,{method,body,headers,credentials:'same-origin',cache:'no-store'}); }
  catch { const e=new Error('Connection interrupted. The outcome is unknown; reconcile before retrying.'); e.unknown=true; throw e; }
  assertActive();
  let data; try { data=await response.json(); } catch { const reason=response.status===429 ? 'Service capacity is temporarily unavailable (429).' : `The server response could not be confirmed (${response.status}).`; const e=new Error(`${reason} Reconcile the original operation before retrying.`); e.status=response.status;e.unknown=true; throw e; }
  assertActive();
  let status=response.status;
  if(response.headers.get('Content-Type')?.split(';')[0]==='application/vnd.batchbeacon.acquisition+json'){
    const object=v=>v!==null && typeof v==='object' && !Array.isArray(v);
    const body=data?.body;
    const success=object(body) && /^[a-f0-9]{32}$/.test(body.run_id) && body.incident_id===path.split('/')[3] && ['COMPLETE','REVIEW_REQUIRED','FAILED','TIMED_OUT','INCOMPLETE','SUPERSEDED','STALE'].includes(body.state) && typeof body.current==='boolean' && typeof body.reconciliation_required==='boolean';
    if(!progress || !response.ok || !object(data) || Object.keys(data).sort().join(',')!=='body,protocol,status' || data.protocol!=='acquisition-progress-v1' || !Number.isInteger(data.status) || !(data.status===200?success:data.status>=400 && data.status<=599 && object(body) && typeof body.error==='string' && body.error.length>0)){
      const e=new Error('The final server response could not be confirmed. Reconcile the original operation before retrying.');e.unknown=true;throw e;
    }
    status=data.status;data=body;
  }
  if(status<200 || status>=300){const e=new Error(admissionMessages[data.error] || (data.error || 'Request unavailable').replaceAll('_',' '));e.status=status;e.code=data.error;e.unknown=data.outcome==='unknown' || status>=500;if(status===401)expire();throw e;}
  return data;
}
function expire() { state.sessionGeneration++;state.selection++;state.capabilities=null;state.workspaceBlock=null;state.loading=false;state.operation=null;for(const el of document.querySelectorAll('.operation-status')){el.textContent='Guest access expired.';delete el.dataset.busy;}pending(null); state.expired=true; state.csrf=null; state.evidence=null; state.target=null; state.captures=[]; state.actions=[]; drawCaptures(); $('comparisons').replaceChildren(); $('queue-rows').replaceChildren(); $('history').replaceChildren(); $('confirm-dialog').close(); text('session-state','Guest access expired'); text('verdict-title','Guest access expired'); text('verdict-copy','Evidence is no longer available in this session.'); text('decision-copy','Start a new evaluation workspace to continue.'); text('queue-count','Guest access expired; counts unavailable.'); $('queue-counts').replaceChildren(); text('queue-capability','Guest access expired; availability unknown.'); text('confirm-product',''); text('field-detail','');text('field-provenance',''); state.queue=null;state.queueDirty=true;state.acquisition=null;state.acquisitionUnknown=false;state.learning=null;state.learningTarget=null;document.querySelector('.verdict').className='verdict neutral';text('active-wording','Guest access expired; wording unavailable.');text('proposed-wording','Guest access expired; proposal unavailable.');for(const step of $('guidance-steps').children)step.removeAttribute('aria-current');$('learning-dialog').close();$('owned-guidance').replaceChildren();$('learning-report').replaceChildren();$('learning-history').replaceChildren();text('learning-counts','Guest access expired; counts unavailable.'); $('completed-actions').hidden=true;$('confirm-open').hidden=false;$('review-recovery').hidden=false;$('renew-workspace').hidden=false;$('recovery-choose').hidden=true;$('recovery-queue').hidden=true;message('Your guest session expired. Open a new workspace to continue. Reviews from the expired workspace cannot be reopened or transferred.'); controls(); }
function controls() {
  const off=state.busy || !state.csrf || state.expired;
  $('refresh-queue').disabled=off; $('queue-filter').disabled=off; for(const id of ['start-sample','new-review','completed-next','recovery-choose','upload','save-correction','reverify','source-choice','sample-choice'])$(id).disabled=off || !!state.pending;
  $('upload').disabled=off || (!!state.pending && state.pending.kind!=='capture');
  $('check').disabled=off || !state.incident || !state.captures.length || !!state.pending || !state.capabilities?.workspace?.extraction?.available || unresolvedAcquisition();
  text('check',state.acquisition?.state==='FAILED' && !unresolvedAcquisition()?'Retry extraction':'Extract and check');
  for(const id of ['refresh-acquisition','decision-recheck']){$(id).hidden=!state.incident || (!unresolvedAcquisition() && !!state.capabilities?.workspace?.extraction?.available);$(id).disabled=off || !state.incident;}
  $('capture').disabled=off || !state.incident || (!!state.pending && state.pending.kind!=='capture');
  $('correction').disabled=off || !state.capabilities?.incident?.correction?.available || !!state.pending;
  $('save-correction').disabled=$('correction').disabled;
  $('reverify').disabled=off || !state.capabilities?.incident?.verification?.available || !!state.pending;
  const eligible=state.capabilities?.incident?.action?.available;
  const recorded=state.actions.some(a=>a.current && !a.requires_renewed_review);
  $('confirm-open').disabled=off || !eligible || recorded || !!state.pending;
  $('hold-confirm').disabled=off || !$('hold-consent').checked || !state.target;
  $('recover').disabled=off;text('recover',state.pendingOwnershipUnknown?'Check pending access':'Reconcile pending operation'); for(const radio of document.querySelectorAll('#example-cards input'))radio.disabled=off || !!state.pending; text('action-help',state.expired?'Guest access expired. Reload to open a new evaluation workspace.':state.busy?'Saving or checking evidence. Please wait.':state.pending?'The previous outcome needs reconciliation before another operation.':state.workspaceBlock?capabilityHelp():state.acquisitionUnknown?'Saved check status is unavailable. Recheck before another operation.':!state.csrf?'Opening your evaluation workspace. If access is unavailable, the notice above explains why.':!state.incident?'Choose an example, then select Use this label.':!state.captures.length?'Add a readable sample label image before extraction.':!state.capabilities?.workspace?.extraction?.available?capabilityHelp():recorded?'Workspace action saved. Open Retail queue to find this investigation.':'Extract and check uses the available bounded model allowance. The server explains any unavailable capacity; no action is automatic.'); learningControls(off); if(state.operation){const op=state.operation;for(const id of op.buttons || []){text(id,op.label);$(id).setAttribute('aria-busy','true');}}
}
const operations={
  upload:{region:'sample-status',buttons:['start-sample'],label:'Saving label…',pending:'Saving this label image… No AI request has been sent.'},
  capture:{region:'capture-status',buttons:['upload'],label:'Uploading images…',pending:'Uploading the selected label images…'},
  extraction:{region:'label-status',buttons:['check'],label:'Extracting and checking…',pending:'Requesting label extraction and waiting for the AI response…'},
  status:{region:'decision-status',buttons:['refresh-acquisition','decision-recheck'],label:'Checking saved status…',pending:'Reading saved status… No new AI request is being sent.'},
  verification:{region:'decision-status',buttons:['reverify'],label:'Verifying evidence…',pending:'Comparing corrected evidence using fixed rules… No AI request is being sent.'},
  action:{region:'decision-status',buttons:['hold-confirm'],label:'Saving action…',pending:'Saving your confirmed workspace action…'},
  queue:{region:'queue-status',buttons:['refresh-queue'],label:'Refreshing queue…',pending:'Reading this workspace’s saved investigations…'},
  guidance:{region:'guidance-status',buttons:['learning-refresh'],label:'Refreshing guidance…',pending:'Reading this investigation’s guidance records…'},
  correction:{region:'label-status',buttons:['save-correction'],label:'Saving correction…',pending:'Saving the corrected field with its history…'},
  refresh:{region:'app-status',buttons:[],label:'Loading…',pending:'Loading saved records…'}
};
function operationStatus(id,value,kind='info') {const el=$(id);delete el.dataset.completedLabelSave;el.textContent=value;el.hidden=!value;el.dataset.kind=kind;}
function clearCompletedSampleReceipt() {if($('sample-status').dataset.completedLabelSave)operationStatus('sample-status','');}
function reveal(id) {const el=$(id);el.focus({preventScroll:true});el.scrollIntoView({block:'start',behavior:'instant'});}
async function task(operation,kind='refresh') {
  if(state.busy)return;
  const op={...operations[kind],kind,view:state.viewGeneration,selection:state.selection};
  const original=(op.buttons || []).map(id=>[id,$(id).textContent]);
  state.busy=true;state.operation=op;message('');operationStatus(op.region,op.pending);
  // Keep live status eligible for immediate announcement; busy belongs to buttons.
  $(op.region).dataset.busy='true';controls();
  if(kind==='extraction'){clearCompletedSampleReceipt();text('verdict-title','Checking label');text('verdict-copy','Waiting for accepted extraction and comparison. No result is confirmed yet.');setStage(1);}
  let succeeded=false;
  try {await operation();succeeded=true;if($(op.region).textContent===op.pending)operationStatus(op.region,'');}
  catch(e){if(!state.expired && !e.stale && op.selection===state.selection)message(safeError(e),'error');}
  finally{
    delete $(op.region).dataset.busy;for(const [id,label] of original){text(id,label);$(id).removeAttribute('aria-busy');}
    state.busy=false;state.operation=null;controls();
    const current=!state.expired && op.selection===state.selection && (!op.incident || op.incident===state.incident);
    if(current && kind==='upload' && succeeded && state.captures.length && !state.pending && $('sample-status').textContent)$('sample-status').dataset.completedLabelSave='true';
    if(current && op.view===state.viewGeneration){
      if(['upload','capture'].includes(kind) && succeeded && state.captures.length){if(!state.capabilities?.workspace?.extraction?.available)reveal('label-status');else if(kind==='upload'){reveal('evidence-title');if($('check').getBoundingClientRect().bottom>innerHeight)reveal('label-status');}}
      if(['extraction','verification','status','action'].includes(kind))reveal('verdict-title');
    }
  }
}
function show(view,{navigate=true,focus=true}={}) {
  if(!['workbench','retail','guidance'].includes(view))view='workbench';
  state.view=view;state.viewGeneration++;
  for(const el of document.querySelectorAll('.view'))el.hidden=el.id!==view;
  for(const a of document.querySelectorAll('[data-view]')){if(a.dataset.view===view)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}
  text('page-name',view==='retail'?'Retail queue':view==='guidance'?'Capture guidance':'Check a product');
  if(navigate){const url=new URL(location.href);url.hash=view;if(url.href!==location.href)history.pushState(null,'',url);}
  if(focus)reveal(view==='retail'?'retail-title':view==='guidance'?'guidance-title':'workbench-title');
}
async function routeView(view,options={}) {
  show(view,options);
  try {if(view==='retail'&&(!state.queue||state.queueDirty))await refresh();if(view==='guidance'&&state.config?.guidance==='OWNED_LIFECYCLE_CONNECTED'&&(!state.learning||state.learningStale||state.learning.context?.incident_id!==state.incident))await loadLearning();}
  catch(e){if(!e.stale&&!state.expired)message(safeError(e),'error');}
}
window.addEventListener('popstate',async()=>{const url=location.href,id=new URLSearchParams(location.search).get('incident');try{if(id&&id!==state.incident)await loadIncident(id);else if(!id&&state.incident)clearReview({resetRoute:false});if(location.href===url)await routeView(location.hash.slice(1)||'workbench',{navigate:false});}catch(e){if(!e.stale&&!state.expired)message(safeError(e),'error');}});
function setStage(index){for(const [i,step] of [...$('journey-stages').children].entries()){if(i===index)step.setAttribute('aria-current','step');else step.removeAttribute('aria-current');}}
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
function sourceView() { const selected=state.config.sources.find(s=>s.selection===$('source-choice').value); const container=$('source-summary');container.replaceChildren();const inspect=$('inspect-source-notice');inspect.hidden=true;inspect.removeAttribute('href');$('source-notice-help').hidden=false;syncEvidenceLinks();if(!selected)return; const n=selected.notice; const single=state.config.sources.length===1; $('source-choice').hidden=single; $('source-choice-label').hidden=single; $('single-source').hidden=!single; text('single-source',`Reviewed source: ${n.authority} · ${n.jurisdictions.join(', ')} · ${n.published_at}. One historical notice is available for this check.`); text('source-explanation',n.dependency.family==='sfa-cheese-2026' && n.dependency.version==='sfa-cheese-2026-10-09'?'This check uses the Singapore Food Agency (SFA) cheese recall notice published on 9 October 2026. It covers this reviewed historical notice, not all recalls. A result does not confirm that a product is safe to consume.':`This check uses the selected historical ${n.authority} notice dated ${n.published_at}. It does not search every recall or establish that a product is safe.`); container.append(node('strong',`${n.authority} · ${n.jurisdictions.join(', ')}`),node('p',`Published ${n.published_at} · historical version ${n.dependency.version}`)); const a=node('a','Open exact source notice'); a.href=n.final_url;a.target='_blank';a.rel='noopener noreferrer';inspect.href=n.final_url;inspect.hidden=false;$('source-notice-help').hidden=true;syncEvidenceLinks();container.append(a,node('p','The selected notice describes a recall, not a contamination test of this item. Additional recall context remains under human review.','context-line')); }
function syncEvidenceLinks() {
  for(const [from,to] of [['inspect-retained-label','saved-label-link'],['inspect-source-notice','saved-notice-link']]) {
    const source=$(from),target=$(to),href=source.getAttribute('href');
    target.hidden=state.expired || !state.incident || source.hidden || !href;
    target.removeAttribute('href');
    if(!target.hidden){target.href=href;target.textContent=source.textContent;}
  }
}
function drawCaptures() {
  const box=$('capture-images');box.replaceChildren();
  const inspect=$('inspect-retained-label');inspect.hidden=true;inspect.removeAttribute('href');
  $('retained-label-help').hidden=false;
  text('retained-label-help',state.expired?'Guest access expired; retained images are no longer accessible.':'Add a label to inspect its retained image.');
  if(state.expired || !state.captures.length){syncEvidenceLinks();box.append(node('p',state.expired?'Guest access expired. Saved records are no longer accessible.':'No ready label images.'));return;}
  state.captures.forEach((c,i)=>{
    const href=`/api/incidents/${state.incident}/captures/${c.id}`;
    const link=node('a');link.href=href;link.target='_blank';link.rel='noopener noreferrer';
    const image=node('img');image.src=href;image.alt=`Retained sample label, panel ${i+1}`;
    link.append(image,node('span',`Open full-size label panel ${i+1} (new tab)`));box.append(link);
    if(i===0){inspect.href=href;inspect.hidden=false;$('retained-label-help').hidden=true;text('inspect-retained-label',state.captures.length>1?'Open retained label panel 1 (new tab)':'Open retained label (new tab)');}
  });
  syncEvidenceLinks();
}
function compare() { text('field-detail','');text('field-provenance','Select an evidence field to inspect its source and label references.');const box=$('comparisons');box.replaceChildren();const result=state.evidence?.result;
  if(!result){box.append(node('p',acquisitionProblem()?'No accepted comparison is available from the last check.':'No deterministic result yet.'));return;}
  if(state.loading)box.append(node('p','Refreshing saved evidence. Displayed comparison is the previous reading.','context-line'));
  if(acquisitionProblem())box.append(node('p','Previously saved comparison · historical evidence','context-line'));
  for(const candidate of result.candidates){const section=node('section');section.append(node('h3',`${candidate.identity.source_values.join(' / ') || candidate.product_id} · ${candidate.eligible_jurisdiction?'within selected jurisdiction':'outside selected jurisdiction'}`));const table=node('div',undefined,'comparison-table');table.setAttribute('role','table');table.setAttribute('aria-label',`Evidence for ${candidate.product_id}`);const header=node('div',undefined,'comparison-row table-heading');header.setAttribute('role','row');for(const title of ['Field','Your label','Recall notice','Result']){const cell=node('span',title);cell.setAttribute('role','columnheader');header.append(cell);}table.append(header);
    for(const r of [candidate.identity,...candidate.predicates]){const row=node('div',undefined,'comparison-row');row.setAttribute('role','row');const head=node('strong');head.setAttribute('role','rowheader');const button=node('button',r.field.replaceAll('_',' '),'field-pick');button.type='button';button.setAttribute('aria-pressed','false');head.append(button);const source=r.source_values.length?r.source_values.join(' / '):r.source_date_range?`${r.source_date_range.lower_inclusive?"[":"("}${r.source_date_range.lower} – ${r.source_date_range.upper}${r.source_date_range.upper_inclusive?"]":")"}`:r.source_operator || 'Not specified';const outcome=r.outcome==='NOT_APPLICABLE'?'Not used':r.outcome.toLowerCase();button.addEventListener('click',()=>{for(const b of box.querySelectorAll('button'))b.setAttribute('aria-pressed','false');button.setAttribute('aria-pressed','true');for(const selected of box.querySelectorAll('.field-selected'))selected.classList.remove('field-selected');row.classList.add('field-selected');text('field-detail',`${fieldLabel(r.field)}: label ${r.observed ?? 'Unknown'}; notice ${source}; ${outcome}. ${r.reason.replaceAll('_',' ').toLowerCase()}.`);fieldProvenance(r,source,outcome);});row.append(head);for(const value of [r.observed ?? 'Unknown',source,outcome]){const c=node('span',value);c.setAttribute('role','cell');row.append(c);}table.append(row);}section.append(table);box.append(section); }
}
function fieldLabel(value) {return ({IDENTITY:'Product identity',PRODUCT_NAME:'Product name',PACK:'Pack size',LOT:'Lot number',BEST_BEFORE:'Best-before date',USE_BY:'Use-by date'})[value] || value.replaceAll('_',' ').toLowerCase();}
function facts(rows) {const dl=node('dl',undefined,'evidence-facts');for(const [label,value] of rows)dl.append(node('dt',label),node('dd',String(value)));return dl;}
function technicalDetails(title,id,content) {const detail=node('details',undefined,'technical');detail.append(node('summary',title));const body=node('div');body.id=id;body.append(...content);detail.append(body);return detail;}
function fieldProvenance(r,source,outcome) {
  const box=$('field-provenance');box.replaceChildren();
  const rule=r.source_operator?({EXACT:'Must match exactly, including case and leading zeros.',ALL:'The notice covers all values for this field.',NOT_SPECIFIED:'The notice does not specify a restriction for this field.',UNKNOWN:'The notice condition is unknown; it cannot establish a match.'})[r.source_operator] || r.source_operator.replaceAll('_',' ').toLowerCase():'Product identity is checked before the lot and date.';
  box.append(facts([['Field',fieldLabel(r.field)],['Your label',r.observed ?? 'Unknown — not established from the label'],['Recall notice',source],['Comparison',outcome.replaceAll('_',' ')],['Rule',rule],['Why',r.reason.replaceAll('_',' ').toLowerCase()]]));
  const linked=new Set();for(const ref of r.observation_evidence){if(linked.has(ref.artifact_id))continue;linked.add(ref.artifact_id);const panel=state.captures.findIndex(c=>c.id===ref.artifact_id);if(panel>=0){const a=node('a',`Open label panel ${panel+1} (new tab)`);a.href=`/api/incidents/${state.incident}/captures/${state.captures[panel].id}`;a.target='_blank';a.rel='noopener noreferrer';box.append(a,node('br'));}}
  const selected=state.config?.sources?.find(x=>x.selection===$('source-choice').value);
  if(selected)box.append(node('p',`Selected notice: ${selected.notice.authority}, published ${selected.notice.published_at}. The exact notice link is above.`));
  box.append(technicalDetails('Technical references','field-audit',[node('p',`Operator: ${r.source_operator || 'identity'}; applies: ${r.source_applies ?? 'not specified'}. Source evidence: ${r.source_evidence.map(e=>`${e.artifact_id} · ${e.locator} · SHA256 ${e.sha256}`).join('; ') || 'none'}. Label evidence: ${r.observation_evidence.map(e=>`${e.artifact_id} · ${e.locator} · SHA256 ${e.sha256}`).join('; ') || 'none'}.`)]));
}
function reviewHistory(e) {
  const box=$('history');box.replaceChildren();
  if(!e){box.append(node('p','No saved evidence.'));return;}
  const checks=node('ol');
  for(const x of e.extraction_history || []) {
    const item=node('li');item.append(node('strong',`AI check ${x.revision}: ${x.validation==='INVALID'?'not accepted':'accepted extraction'}`));
    const observations=(e.observation_history || []).filter(o=>o.extraction_revision===x.revision);
    for(const o of observations){const results=(e.result_history || []).filter(r=>r.observation_revision===o.revision);for(const r of results)item.append(node('p',`${r.revision===e.result?.revision?(e.current?'Latest saved comparison':'Latest comparison — renewed review required'):'Earlier comparison'}: ${labels[r.verdict]}. ${o.correction_count} field correction(s).`));}
    checks.append(item);
  }
  if(checks.children.length)box.append(checks);
  if(fields().length){box.append(node('h4','Label details'),facts(fields().map(f=>[fieldLabel(f.field),f.observation.value ?? (({UNKNOWN:'Unknown — no accepted value',NOT_SPECIFIED:'Not specified',ALL:'All values'})[f.observation.state] || f.observation.state)])));}
  for(const c of e.observation?.corrections || [])box.append(node('p',`${fieldLabel(c.field)} corrected from “${c.previous.value ?? c.previous.raw}” to “${c.replacement.value ?? c.replacement.raw}”. Original text is retained in the technical record.`));
  for(const a of state.actions)box.append(node('p',`${a.action.action_type==='SIMULATED_HOLD'?'Simulated stock hold':'Request for further review'}: ${a.current&&!a.requires_renewed_review?'current saved action':'earlier action — renewed review required'}. No live inventory was changed.`));
  const audit=[];
  for(const x of e.extraction_history || [])audit.push(node('p',`Extraction v${x.revision} · ${x.validation==='INVALID'?'not accepted':'accepted'} · ${x.prompt_version}`));
  for(const o of e.observation_history || [])audit.push(node('p',`Observation v${o.revision} · extraction v${o.extraction_revision} · ${o.correction_count} correction(s)`));
  for(const r of e.result_history || [])audit.push(node('p',`Result v${r.revision} · observation v${r.observation_revision} · ${labels[r.verdict]} · ${r.checked_sources.map(s=>s.version).join(', ')}`));
  for(const f of fields())audit.push(node('p',`${f.field}: raw “${f.observation.raw}”; normalized “${f.observation.value ?? 'Unknown'}”; state ${f.observation.state}`));
  for(const a of state.actions)audit.push(node('p',`${a.action.action_type} · result v${a.action.result_revision} · ${a.current&&!a.requires_renewed_review?'current saved action':'historical — renewed review required'}`));
  box.append(technicalDetails('Technical review record','history-audit',audit));
}
function fields() {const obs=state.evidence?.observation;if(!obs)return [];return [{field:'PRODUCT_NAME',observation:obs.identity.name},{field:'PACK',observation:obs.identity.pack},...obs.fields];}
function correctionValue() {const f=fields().find(f=>f.field===$('correction-field').value);$('correction-value').value=f?.observation.value ?? '';}
function captureInstruction() {const result=state.evidence?.result;text('capture-instruction',result?.outstanding_fields?.length ? `Required evidence: ${result.outstanding_fields.join(', ').replaceAll('_',' ')}. Include the complete requested marking; keep case and leading zeros readable.` : 'Include the full product name, pack, lot and required date panel. Preserve readable case and leading zeros.');}
function unresolvedAcquisition() { return !!state.workspaceBlock || state.acquisitionUnknown || state.acquisition?.reconciliation_required || state.acquisition?.state==='INCOMPLETE'; }
function acquisitionProblem() {
  if(state.acquisitionUnknown)return {title:'Check status unavailable',copy:'The last check could not be read. Recheck its saved status; no new extraction has been started.'};
  const a=state.acquisition;
  if(!a || a.current || a.state==='COMPLETE')return null;
  if(a.reconciliation_required)return {title:'Check outcome unresolved',copy:'An AI attempt in this workspace has an unconfirmed outcome. Recheck saved status without starting another AI call. Operator review is required while it remains unresolved; another extraction is unavailable in this workspace.'};
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
  if(a.state==='TIMED_OUT')return {title:'Extraction timed out',copy:'This check reached its deadline without a confirmed result. Its reserved AI usage is accounted for. A new extraction requires an explicit request and available allowance.'};
  if(a.state==='STALE' || a.state==='SUPERSEDED')return {title:'Evidence needs renewed review',copy:'The previous check no longer supports a current action. Review and reverify the saved evidence.'};
  return {title:a.state==='FAILED'?'Extraction failed':'Extraction needs review',copy:reasons[a.diagnostics?.[0]] || 'No accepted comparison is available from this check. Review the retained evidence before explicitly trying again.'};
}
function render() {if(state.expired)return;const failure=state.checkFailure?.incident===state.incident?state.checkFailure:null;const e=state.evidence;const result=e?.result;const failed=e?.extraction_history?.at(-1)?.validation==='INVALID';const problem=acquisitionProblem();const recorded=state.actions.find(a=>a.current&&!a.requires_renewed_review);text('incident-id',state.incident?`Incident ${state.incident.slice(0,8)}`:'No incident selected');
  document.querySelector('.verdict').className='verdict'+(problem?' neutral':recorded?' completed':(!result || result.verdict==='NOT_LISTED_IN_CHECKED_NOTICES')?' neutral':'');
  text('verdict-title',problem?problem.title:failure&&!e?.current?failure.title:recorded?'Workspace action recorded':e?.observation&&!e.current?'Evidence needs renewed review':result?labels[result.verdict]:state.loading?'Loading saved evidence':failed?'Extraction needs review':state.captures.length?'Label ready':'Ready for evidence');
  text('verdict-copy',failure&&!problem&&!e?.current?failure.copy:problem?`${problem.copy}${result?' Previous saved comparison is historical; it cannot authorize a new action.':''}`:recorded?(recorded.action.action_type==='SIMULATED_HOLD'?'A stock hold was recorded in this workspace. No live inventory was changed.':'A request for further review was saved in this workspace. Uncertainty remains unresolved.'):result?`Checked ${result.checked_sources.length} selected notice version(s). ${e.current?'Current for the saved historical source selection.':'Historical result; no new action is available.'}`:failed?'The extraction was not accepted. Review the retained evidence; no comparison or action was created.':state.loading?'Reading this investigation’s saved records.':state.captures.length?labelReadyCopy():'Choose an example and use its label, then select Extract and check.');
  text('decision-title',problem?'Resolve the check before an action':recorded?'Saved workspace action':!state.incident?'Begin with a label':!result?'Next, check the label':'Your confirmation comes next');
  text('decision-copy',problem?'No new action is available from this check. Retained evidence and earlier actions remain in the review history.':!state.incident?'Choose an example, then select Use this label. You will review the extracted evidence before any action.':!result?'Saving a label does not check it. When available, select Extract and check to compare its details with the selected notice.':result?.verdict==='NOT_LISTED_IN_CHECKED_NOTICES'?'No hold is supported by these checked notices. This is not safety, clearance or permission to sell.':recorded?'This review is saved. Find it in your retail queue, or choose another label to begin a separate check. Your saved review remains available until this workspace expires.':'A result never places stock on hold automatically.');
  setStage(recorded&&!problem?4:result?2:state.captures.length?1:0);
  $('completed-actions').hidden=!recorded || !!problem || state.loading;
  $('confirm-open').hidden=!result || (!!recorded && !problem);
  $('check').classList.toggle('primary',!recorded);$('check').classList.toggle('secondary',!!recorded);
  if(!result && state.captures.length && !problem)operationStatus('label-status',labelReadyCopy());
  text('check-explanation-copy',problem?problem.copy:result?'Gemini proposed the label details. Fixed rules compared accepted identity first, then lot, required date and notice scope. Review each field below; unknown or missing evidence is not a match.':'No accepted AI check is available for this label. Uploading only saves the image.');
  text('capability-help',!state.incident?'Choose a label to begin.':recorded&&!problem?'No further confirmation is needed for this saved action.':capabilityHelp());$('operator-help').hidden=!state.workspaceBlock;syncEvidenceLinks();$('case-reference').value=state.incident || '';
  captureInstruction(); const action=result?.verdict==='REVIEW_REQUIRED'?'Review follow-up request':'Review stock hold';text('confirm-open',action);$('reverify').hidden=!e?.observation || !!e.current;compare();
  $('correction-field').replaceChildren(...fields().map(f=>{const o=node('option',f.field.replaceAll('_',' '));o.value=f.field;return o;}));correctionValue();
  reviewHistory(e); controls(); }
function labelReadyCopy(){return 'Label saved. '+(state.capabilities?.workspace?.extraction?.available?'Next, extract and check its details. Saving a label does not start an AI check.':capabilityHelp());}
function capabilityHelp(){
  const reason=state.capabilities?.workspace?.extraction?.reason;
  if(state.workspaceBlock)return 'New AI checks in this workspace are paused while an earlier request is resolved. Your saved label and notice remain available. Recheck reads status only; it does not settle the request.';
  if(!state.capabilities)return 'Availability could not be confirmed. Recheck saved status before another operation.';
  if(reason==='ACQUISITION_LIMIT')return 'This case’s extraction allowance is exhausted. Inspect saved evidence or correct a completed extraction when available.';
  if(reason==='ALLOWANCE_UNAVAILABLE')return 'AI allowance is unavailable. Review the saved label and selected notice, or choose Recheck saved status to check availability. Recheck does not start an AI request.';
  if(!state.capabilities.incident.correction.available && state.evidence?.observation)return 'This case has no completed latest extraction. Its earlier comparison is historical; correction and reverification cannot complete that request.';
  return 'Inspect product identity, exact lot, required date and the selected notice before confirming an eligible action.';
}
function clearReview({navigate=false,resetRoute=true}={}) {
  state.selection++;state.incident=null;state.evidence=null;state.captures=[];state.actions=[];state.target=null;state.capabilities=null;state.acquisition=null;state.acquisitionUnknown=false;state.checkFailure=null;state.loading=false;state.learning=null;state.learningTarget=null;state.learningStale=true;
  $('confirm-dialog').close();$('capture-panel').hidden=true;$('correction-panel').hidden=true;$('capture-file').value='';
  $('capture').setAttribute('aria-expanded','false');$('correction').setAttribute('aria-expanded','false');
  for(const id of ['label-status','decision-status','sample-status','capture-status'])operationStatus(id,'');
  for(const id of ['owned-guidance','learning-report','learning-history'])$(id).replaceChildren();
  drawCaptures();render();
  if(!resetRoute)return;
  const url=new URL(location.href);url.searchParams.delete('incident');url.hash='workbench';
  if(navigate)history.pushState(null,'',url);else history.replaceState(null,'',url);
}
function chooseAnotherLabel() {
  if(state.busy || state.expired || state.pending)return;
  clearReview({navigate:true});message('');$('review-recovery').hidden=true;show('workbench',{navigate:false,focus:false});
  document.querySelector('.examples').open=true;reveal('sample-choice');
}
function unavailableReview() {
  clearReview();text('app-status','This saved review is unavailable in this workspace. Its access may have expired, or it may belong to another workspace. Choose a label to start a new check, or open the retail queue for reviews available here.');
  $('app-status').hidden=false;$('app-status').dataset.kind='error';$('review-recovery').hidden=false;$('renew-workspace').hidden=true;$('recovery-choose').hidden=false;$('recovery-queue').hidden=false;
}
async function loadIncident(id,knownAcquisition=null) {
  if(state.expired)return;
  clearCompletedSampleReceipt();$('review-recovery').hidden=true;
  const selection=++state.selection,session=state.sessionGeneration;
  const valid=()=>!state.expired && session===state.sessionGeneration && selection===state.selection;
  const changed=state.incident!==id;
  state.incident=id;state.learningStale=true;state.capabilities=null;state.loading=true;state.target=null;
  if(changed){operationStatus('label-status','');operationStatus('decision-status','');state.checkFailure=null;state.evidence=null;state.actions=[];state.captures=[];state.acquisition=knownAcquisition;state.acquisitionUnknown=false;}
  else if(knownAcquisition)state.acquisition=knownAcquisition;
  drawCaptures();render();$('capture-panel').hidden=true;$('correction-panel').hidden=true;$('capture-file').value='';text('capture-status','');
  const url=new URL(location.href);url.searchParams.set('incident',id);history.replaceState(null,'',url);
  try {
    const [e,c,a,cap]=await Promise.all([api(`/api/incidents/${id}/evidence`),api(`/api/incidents/${id}/captures`),api(`/api/incidents/${id}/actions`),api(`/api/incidents/${id}/capabilities`).catch(error=>{if(error.stale||state.expired)throw error;return null;})]);
    if(!valid())return;
    state.evidence=e;state.captures=c.batches.filter(b=>b.ready).at(-1)?.captures || [];state.actions=a.actions;
    state.capabilities=cap?.workspace?.extraction && cap?.incident?cap:null;
    if(state.capabilities)state.workspaceBlock=['UNRESOLVED_ATTEMPT','ACTIVE_REQUEST'].includes(cap.workspace.extraction.reason)?cap.workspace.extraction.reason:null;
    state.acquisition=knownAcquisition;state.acquisitionUnknown=false;
    if(e.latest_run_id){try {const acquisition=await api(`/api/incidents/${id}/acquisitions/${e.latest_run_id}`);if(!valid())return;state.acquisition=acquisition;}
      catch(error){if(!valid())return;state.acquisitionUnknown=true;message('Saved check status is unavailable. Recheck it before another extraction.','error');}}
    if(!valid())return;state.loading=false;drawCaptures();render();
  } catch(error){if(!valid())return;state.loading=false;state.capabilities=null;if(error.status===404 && !error.unknown){unavailableReview();return false;}render();throw error;}
  return true;
}
async function loadOwnedIncident(id,known=null){
  const selection=state.selection,op=state.operation;
  if(op&&op.selection!==selection)return;
  try {return await loadIncident(id,known);}
  finally {if(op&&state.selection===selection+1&&state.incident===id)op.selection=state.selection;}
}
async function recheck(){
  if(await loadOwnedIncident(state.incident)===false || state.expired)return;
  const checked=new Date().toLocaleTimeString();
  message(`${!state.capabilities?'Availability is still unconfirmed; no new AI request was sent.':unresolvedAcquisition()?'Still unresolved; no new AI request was sent.':'Saved status refreshed; no new AI request was sent.'} Checked at ${checked}.`);
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
  const incident=state.incident,selection=state.selection; const selected=()=>!state.expired&&state.incident===incident&&state.selection===selection; if(state.operation)state.operation.incident=incident;
  const resuming=!!state.pending;
  const fingerprints=await captureFiles(files);
  if(!selected())return;
  if(state.pending) {
    const p=state.pending;
    if(p.incident!==state.incident || JSON.stringify(p.files)!==JSON.stringify(fingerprints))throw new Error('Select the same original images in the same order to resume this upload.');
    const observed=await reconcileCapture(p);
    if(!selected())return;
    if(observed.found && observed.batch.ready){pending(null);await loadOwnedIncident(p.incident);message('The original upload is already retained. No images were uploaded again.');return;}
  } else pending({kind:'capture',incident,operation:key(),files:fingerprints});
  const operation=state.pending.operation;
  const data=new FormData();files.forEach(f=>data.append('images',f));
  try {
    const result=await api(`/api/incidents/${incident}/captures`,{method:'POST',operation,body:data});
    if(!result.ready){const e=new Error('The original upload is pending. Reconcile before continuing.');e.unknown=true;throw e;}
    if(!selected())return;pending(null);state.captures=result.captures;drawCaptures();render();operationStatus('label-status',labelReadyCopy());operationStatus('capture-status',labelReadyCopy());message(labelReadyCopy());
  } catch(e){if(selected() && !e.unknown && !resuming)pending(null);throw e;}
}
async function startSample() {
  const selection=state.selection;
  const response=await fetch(`/samples/${$('sample-choice').value}.png`);
  if(!response.ok)throw new Error('Sample unavailable.');
  const blob=await response.blob();requireSession();if(state.selection!==selection)return;
  const created=await api('/api/incidents',{method:'POST',operation:key()});
  state.queueDirty=true;if(state.selection!==selection)return;await loadOwnedIncident(created.incident_id);
  if(state.incident!==created.incident_id||state.expired||state.selection!==selection+1)return;
  if(state.operation)state.operation.incident=created.incident_id;
  const uploadSelection=state.selection;
  await upload([new File([blob],'synthetic-label.png',{type:'image/png'})]);
  if(state.incident!==created.incident_id||state.expired||state.selection!==uploadSelection)return;
  await loadOwnedIncident(created.incident_id);
  message(labelReadyCopy());
}
async function acquire() {
  const incident=state.incident,selection=state.selection;
  const selected=()=>!state.expired&&state.incident===incident&&state.selection===selection;
  if(state.operation)state.operation.incident=incident;
  state.checkFailure=null;state.queueDirty=true;const operation=key();
  pending({kind:'acquisition',incident,operation});
  try {
    const result=await api(`/api/incidents/${incident}/acquisitions`,{method:'POST',operation,body:{source_selection:$('source-choice').value,capture_ids:state.captures.map(c=>c.id),expected_observation_revision:state.evidence.latest_observation_revision}});
    if(result.state==='INCOMPLETE'){
      if(selected()){state.acquisition=result;render();message('The request is incomplete. Recheck saved status; no new AI request will be sent.');}
      return;
    }
    pending(null);if(!selected())return;
    await loadOwnedIncident(incident,result);
    if(state.incident!==incident||state.expired)return;
    const problem=acquisitionProblem();const value=problem?problem.copy:'Extraction and comparison completed. Review identity, lot, required date and source scope.';
    message(value,problem?'error':'success');operationStatus('decision-status',value,problem?'error':'success');
  } catch(e) {
    if(!e.unknown)pending(null);
    if(!selected())return;
    try {await loadOwnedIncident(incident);}catch(readError){if(readError.stale||state.expired)return;}
    if(state.incident!==incident||state.expired)return;
    if(e.unknown)state.acquisitionUnknown=true;
    state.checkFailure={incident,title:'Check could not start',copy:`The check could not finish: ${safeError(e)}. Saved evidence remains available. No product conclusion follows from this failure.`};
    render();operationStatus('decision-status',safeError(e),'error');throw e;
  }
}
async function prepare() {const incident=state.incident,selection=state.selection;if(state.operation)state.operation.incident=incident;const kind=state.evidence.result.verdict==='MATCHED_HOLD_FOR_REVIEW'?'SIMULATED_HOLD':'SIMULATED_REVIEW_REQUEST';const data=await api(`/api/incidents/${state.incident}/actions/prepare?action_type=${kind}`);if(state.expired||state.incident!==incident||state.selection!==selection)return;if(data.target.observation_revision!==state.evidence.observation.revision || data.target.result_revision!==state.evidence.result.revision){await loadOwnedIncident(state.incident);throw new Error('Evidence changed before confirmation. Review the newly loaded values, then prepare the action again.');}state.target=data.target;text('confirm-title',kind==='SIMULATED_HOLD'?'Review this stock hold':'Review this follow-up request');text('confirm-product',`${state.evidence.observation.identity.name.value || 'Unresolved identity'} · ${state.evidence.observation.identity.pack.value || 'Unknown pack'} · ${state.evidence.observation.fields.map(f=>`${f.field}: ${f.observation.value ?? 'Unknown'}`).join(' · ')} · observation v${data.target.observation_revision} · result v${data.target.result_revision} · sources ${state.evidence.result.checked_sources.map(s=>`${s.version} (epoch ${s.epoch})`).join(', ')}`);text('hold-confirm',kind==='SIMULATED_HOLD'?'Confirm stock hold':'Confirm review request');$('hold-consent').checked=false;text('confirm-status','');$('confirm-dialog').showModal();setStage(3);controls();}
async function confirm() {
  const incident=state.incident,selection=state.selection,target=state.target;
  if(state.operation)state.operation.incident=incident;
  state.queueDirty=true;pending({kind:'action',incident,operation:key(),target});
  try {
    await api(`/api/incidents/${incident}/actions`,{method:'POST',operation:state.pending.operation,body:{target,explicit_confirmation:true}});
    pending(null);$('confirm-dialog').close();
    if(state.expired||state.incident!==incident||state.selection!==selection)return;
    await loadOwnedIncident(incident);message('Workspace action saved. No live inventory was changed.');
  } catch(e) {
    $('confirm-dialog').close();if(!e.unknown)pending(null);state.target=null;
    if(state.expired||state.incident!==incident||state.selection!==selection)return;
    await loadOwnedIncident(incident);throw e;
  }
}
async function saveCorrection(){
  const incident=state.incident,selection=state.selection;
  if(state.operation)state.operation.incident=incident;
  state.queueDirty=true;const f=fields().find(f=>f.field===$('correction-field').value);
  const replacement={...f.observation,state:'KNOWN',value:$('correction-value').value,raw:$('correction-value').value};
  await api(`/api/incidents/${incident}/corrections`,{method:'POST',operation:key(),body:{expected_revision:state.evidence.latest_observation_revision,field:f.field,replacement}});
  if(state.expired||state.incident!==incident||state.selection!==selection)return;
  await loadOwnedIncident(incident);message('Correction saved. Previous results are historical until re-verification.');
}
async function reverify(){
  const incident=state.incident,selection=state.selection;
  if(state.operation)state.operation.incident=incident;
  state.queueDirty=true;const operation=key();pending({kind:'verification',incident,operation});
  try {await api(`/api/incidents/${incident}/verifications`,{method:'POST',operation});pending(null);}
  catch(e){if(!e.unknown)pending(null);throw e;}
  if(state.expired||state.incident!==incident||state.selection!==selection)return;
  await loadOwnedIncident(incident);message('Corrected evidence was deterministically re-verified. No model call was made.');
}
async function recover() {
  if(state.pendingOwnershipUnknown) {
    await restorePending({expires_at:state.expiresAt});
    if(state.pending?.incident) {
      await loadOwnedIncident(state.pending.incident);
      message('Pending access confirmed. Select Reconcile pending operation to check the original request. No operation was replayed.');
    } else unavailableReview();
    return;
  }
  state.queueDirty=true;const p=state.pending;if(!p)return;
  const selection=state.selection;const selected=()=>!state.expired&&state.selection===selection;
  if(state.operation)state.operation.incident=state.incident;
  if(p.kind==='capture'){
    const result=await reconcileCapture(p);if(!selected())return;
    if(result.found&&result.batch.ready){pending(null);await loadOwnedIncident(p.incident);message('The original upload is retained. No images were uploaded again.');}
    else {await loadOwnedIncident(p.incident);if(state.expired||state.incident!==p.incident)return;$('capture-panel').hidden=false;$('capture').setAttribute('aria-expanded','true');message('The original upload is '+(result.found?'pending':'not recorded')+'. Select the same original images in the same order, then Upload selected images to resume its original request.');}
    return;
  }
  if(p.kind==='learning'){
    const value=await api(p.path,{method:'POST',operation:p.operation,body:p.body});pending(null);
    if(selected()&&state.incident===p.incident){renderLearning(value.learning_state);controls();}return;
  }
  if(p.kind==='verification')await api(`/api/incidents/${p.incident}/verifications`,{method:'POST',operation:p.operation});
  else if(p.kind==='acquisition'){
    const result=await api(`/api/incidents/${p.incident}/acquisitions/reconcile`,{operation:p.operation});
    if(!selected())return;
    if(result.state==='INCOMPLETE'){message('The original acquisition is still unresolved. No new request was started.');return;}
  } else {
    const result=await api(`/api/incidents/${p.incident}/actions/reconcile?result_revision=${p.target.result_revision}&action_type=${p.target.action_type}`);
    if(!selected())return;
    if(!result.found)message('No committed action found. Review the current evidence before making another decision.');
  }
  pending(null);if(selected())await loadOwnedIncident(p.incident);
}
async function refresh() {requireSession();const remaining=state.queueReadAt+(state.config.refresh_interval_seconds*1000)-Date.now();if(remaining>0){text('queue-status','Waiting briefly before refreshing the saved snapshot…');await new Promise(resolve=>setTimeout(resolve,remaining));requireSession();}text('queue-status','Refreshing this workspace…');try{const data=await api(`/api/retail/queue?filter=${$('queue-filter').value}`,{operation:key()});state.queue=data;state.queueDirty=false;state.queueReadAt=Date.now();const rows=data.snapshot.rows;const container=$('queue-rows');container.replaceChildren();text('queue-count',`${rows.length} saved incident(s) · ${data.visible_count} shown · snapshot ${new Date(data.snapshot.generated_at).toLocaleTimeString()}`);$('queue-counts').replaceChildren(...Object.entries(data.snapshot.category_counts).map(([category,n])=>node('span',`${labels[category]}: ${n}`)));for(const row of rows.filter(r=>data.visible_incident_ids.includes(r.incident_id))){const item=node('div');item.setAttribute('role','listitem');const link=node('a',undefined,'queue-row');link.href=`?incident=${row.incident_id}#workbench`;link.addEventListener('click',e=>{e.preventDefault();show('workbench');loadIncident(row.incident_id).then(()=>{if(state.view==='workbench'&&!state.expired)reveal('evidence-title');}).catch(error=>{if(!state.expired&&!error.stale)message(safeError(error),'error');});});const name=node('div');name.append(node('strong',row.product_name),node('small',`Incident ${row.incident_id.slice(0,8)} · observation v${row.observation_revision}`));link.append(name,node('span',row.jurisdiction),node('span',({LABEL_REQUIRED:'Needs a label',LABEL_READY:'Label saved — ready to check',CHECK_PENDING:'Check pending',CHECK_INCOMPLETE:'Check incomplete'}[row.stage] || labels[row.category]),`state-tag ${row.category==='SIMULATED_ACTION_RECORDED'?'completed':'neutral'}`),node('span',row.stage==='LABEL_READY'?'Open label and check':row.stage==='LABEL_REQUIRED'?'Add a label':row.current?'View saved evidence':'Review evidence'));item.append(link);container.append(item);}if(!data.visible_count)container.append(node('p','No incidents match this filter.','empty-state'));text('queue-capability',`Saved evidence: ${data.saved_evidence.state.toLowerCase()}. New verification: ${data.new_verification.state.toLowerCase()}. Counts cover this evaluation workspace only.`);text('queue-status','Manual refresh complete. No model call was made.');}catch(e){if(state.expired||e.stale)throw e;text('queue-status',`Refresh unavailable. ${state.queue?'The displayed snapshot is historical; its counts are not a current reading.':'Counts are unknown.'}`);e.message=$('queue-status').textContent+' '+safeError(e);throw e;}}
for(const a of document.querySelectorAll('[data-view]'))a.addEventListener('click',e=>{e.preventDefault();routeView(a.dataset.view);});
for(const id of ['new-review','completed-next','recovery-choose'])$(id).addEventListener('click',chooseAnotherLabel);
for(const id of ['capture','correction'])$(id).addEventListener('click',()=>{const p=$(id+'-panel');p.hidden=!p.hidden;$(id).setAttribute('aria-expanded',String(!p.hidden));});
$('source-choice').addEventListener('change',sourceView);$('correction-field').addEventListener('change',correctionValue);
$('start-sample').addEventListener('click',()=>task(startSample,'upload'));$('check').addEventListener('click',()=>task(acquire,'extraction'));$('upload').addEventListener('click',()=>task(()=>upload([...$('capture-file').files]),'capture'));
$('confirm-open').addEventListener('click',()=>task(prepare));$('hold-consent').addEventListener('change',controls);$('hold-confirm').addEventListener('click',()=>task(confirm,'action'));$('recover').addEventListener('click',()=>task(recover));
$('confirm-dialog').addEventListener('close',()=>{state.target=null;$('hold-consent').checked=false;controls();setStage(state.actions.some(a=>a.current&&!a.requires_renewed_review)?4:state.evidence?.result?2:0);if(!$('confirm-open').hidden)$('confirm-open').focus();});
$('save-correction').addEventListener('click',()=>task(saveCorrection,'correction'));
$('reverify').addEventListener('click',()=>task(reverify,'verification'));
for(const id of ['refresh-acquisition','decision-recheck'])$(id).addEventListener('click',()=>task(recheck,'status'));
$('refresh-queue').addEventListener('click',()=>task(refresh,'queue'));$('queue-filter').addEventListener('change',()=>task(refresh,'queue'));
function renderSupport() {
  const target=$('support-contact');target.replaceChildren();
  const support=state.config?.support;
  if(!support?.email || !support?.mailto){target.textContent='No public support channel is configured.';return;}
  const link=node('a',`Email the project operator: ${support.email}`);link.href=support.mailto;
  target.append(link,node('span',' (opens your email app)'));
}
async function restorePending(session) {
  let saved=null;try{saved=JSON.parse(sessionStorage.getItem('bb_pending') || 'null');}catch{}
  pending(saved?.session_expires_at===session.expires_at?saved:null);
  if(!state.pending?.incident)return;
  // Equal expiry timestamps are not proof of the same owner. Verify custody before replay.
  state.pendingOwnershipUnknown=true;
  const owned=await api('/api/incidents');
  if(!Array.isArray(owned.incident_ids))throw new Error('Pending-operation ownership could not be confirmed. Reload to check again; no new operation was sent.');
  state.pendingOwnershipUnknown=false;
  if(!owned.incident_ids.includes(state.pending.incident)) {
    pending(null);
    message('The previous operation is unavailable in this workspace. Its records and accounting have not been changed.');
  }
}
async function init() {state.config=await api('/api/workbench/config');renderSupport();if(state.config.mode==='REAL_VERTEX_EXTRACTION'){text('runtime-title','BatchBeacon AI');text('runtime-detail','Real AI analysis · Non-production data');text('result-disclosure','Server result · Gemini extraction');}else{text('runtime-title','Local integration');text('runtime-detail','Test extraction · Non-production data · Test storage');text('result-disclosure','Server result · test extraction');}for(const row of state.config.samples){const option=node('option',row.name);option.value=row.id;$('sample-choice').append(option);}for(const row of state.config.sources){const option=node('option',`${row.notice.authority} · ${row.notice.dependency.version}`);option.value=row.selection;$('source-choice').append(option);}exampleCards();sourceView();if(state.config.guidance==='OWNED_LIFECYCLE_CONNECTED'){$('learning-controls').hidden=false;text('guidance-state-title','Your workspace’s capture guidance');text('guidance-state-copy','Saved requests, feedback and evaluated wording changes belong to this evaluation workspace only.');}else{text('guidance-state-copy','Capture guidance is unavailable in this configuration.');}let session;try{session=await api('/api/guest',{method:'POST'});}catch(e){state.sessionError=safeError(e);text('session-state',state.expired?'Guest access expired':'Guest access unavailable');text('queue-count','Guest access unavailable; counts unknown.');text('learning-counts','Guest access unavailable; counts unknown.');throw e;}state.csrf=session.csrf_token;state.expiresAt=session.expires_at;text('session-state',`Workspace access expires ${new Date(session.expires_at).toLocaleString(undefined,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'})}`);const ttl=Date.parse(session.expires_at)-Date.parse(state.config.server_time);if(ttl>0)setTimeout(expire,ttl);await restorePending(session);const id=state.pending?.incident||new URLSearchParams(location.search).get('incident');if(id)await loadOwnedIncident(id);show(['retail','guidance'].includes(location.hash.slice(1))?location.hash.slice(1):'workbench',{navigate:false,focus:false});{const view=document.querySelector('nav [aria-current=page]')?.dataset.view;if(view==='retail')await refresh();if(view==='guidance'&&state.config.guidance==='OWNED_LIFECYCLE_CONNECTED')await loadLearning();}render();}
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
  const selected=state.selection;
  try {
    const l=await api('/api/learning'+(state.incident?'?incident='+encodeURIComponent(state.incident):''),{operation:key()});if(selected!==state.selection||state.expired)return;renderLearning(l);controls();
  } catch(e) {if(selected!==state.selection||state.expired||e.stale)return;text('learning-counts',state.learning?'Refresh failed. Displayed records are historical; current counts are unknown.':'Guidance records unavailable; counts unknown.');throw e;}
}
function renderLearning(l) {
    state.learning=l;state.learningStale=false;
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
  const selection=state.selection,incident=state.incident;if(state.operation)state.operation.incident=incident;
  if(state.incident)path+='?incident='+encodeURIComponent(state.incident);
  const operation=key();pending({kind:'learning',incident:state.incident,operation,path,body});
  try {const value=await api(path,{method:'POST',operation,body});pending(null);if(!state.expired&&state.selection===selection&&state.incident===incident)renderLearning(value.learning_state);return value;}
  catch(e){if(!e.unknown)pending(null);throw e;}
}
async function prepareLearning(kind) {
  const selection=state.selection,incident=state.incident;if(state.operation)state.operation.incident=incident;
  const evaluation=learningSelection().evaluation;
  const target=await api(kind==='activate'?`/api/learning/activation/prepare?evaluation=${evaluation.id}`:'/api/learning/rollback/prepare');
  if(state.expired||state.selection!==selection||state.incident!==incident)return;
  state.learningTarget={kind,target};$('learning-consent').checked=false;
  text('learning-confirm-title',kind==='activate'?'Review evaluated capture wording':'Review guidance rollback');
  const box=$('learning-preview');box.replaceChildren();
  for(const id of ['GUIDANCE_V1','GUIDANCE_V2']){box.append(node('h3',id.replaceAll('_',' ')));for(const item of state.config.guidance_policies[id].instructions)box.append(node('p',item.text));}
  box.append(node('p',kind==='activate'?`Passing evaluation ${evaluation.id.slice(0,8)}. Base activation revision ${target.base.activation_revision}.`:`Return to prior wording with a new revision after ${target.current.activation_revision}. Earlier records stay unchanged.`));
  $('learning-dialog').showModal();
}
$('guidance-start').addEventListener('click',()=>{show('workbench');$('sample-choice').focus();});
$('guidance-queue').addEventListener('click',()=>{show('retail');if(!state.queue||state.queueDirty)task(refresh,'queue');});
$('learning-refresh').addEventListener('click',()=>task(async()=>{await loadLearning();message('Capture guidance records refreshed.','success');},'guidance'));
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

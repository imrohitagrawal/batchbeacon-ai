# User-journey correction: implementation and remaining acceptance

The [consolidated plan](../USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md) retains
R01–R12 and the submitted video. This increment repairs the existing workflow:
choose/upload → explicit extraction → evidence review → explicit eligible action
→ saved queue. No model, source, verifier, timeout, paid allowance, runtime
configuration or accounting-settlement change is included.

## Implemented boundaries

- F1/F2: operation-specific adjacent status, busy labels and reduced-motion loader;
  no-label, label-ready, checking, completed, refused, unresolved and expired states.
  An explicit successful upload reveals retained evidence and the next action;
  rejected uploads cannot reuse a previous case’s label or capabilities.
- F3/F4: owned GET capability projection separates workspace AI admission from
  case-level immutable completion and current action eligibility. Unknown, active,
  exhausted and unavailable admission has a visible reason beside Extract.
  A different case’s unknown attempt does not invalidate completed evidence.
  Missing capability data fails closed. Recheck is read-only, timestamped and does
  not promise settlement. Incomplete cases cannot offer correction/reverification.
- F5/F6: session and selection generations discard obsolete success and error
  replies, including leaving and reopening the same case. Upload dispatch retains
  its original case after asynchronous fingerprinting. Mutation and recovery
  replies cannot reopen another selected case. Explicit navigation updates route,
  focus and scroll; reload/back preserve views. Known-current guidance is not
  redundantly refreshed by clicking its active navigation item.
- F7: shorter purpose and Gemini/server/person explanation, five factual stages,
  state-specific queue wording, readable product headings, linked review checklist
  and technical field provenance in a native disclosure. No numeric confidence or
  safety score is introduced. Queue stage is a transient response field; persisted
  projections, configuration hashes and record readers are unchanged.
- F8: diagnosis only. A newer retained complete HTTP response contains cache-usage
  accounting the current parser rejects. This is distinct from earlier provider
  timeouts. Both unknown liabilities remain reserved. No provider request,
  settlement, timer change or exhausted allowance renewal is authorized here.

## Independent triage and regression evidence

Code/state, UX/video and operations reviewers independently reproduced the
baseline findings before correction. Review also reproduced failures during
second-upload rejection, extraction refusal, upload fingerprinting, recovery,
case switching and same-case reopening. The wrong upload target was classified
CRITICAL_BLOCKER; misleading state/navigation failures REQUIRED_CONTRACT.
They were consolidated under the original async ownership/state roots and
corrected at those boundaries. No server false acceptance was demonstrated.

Independent controlled verification cleared the corrected capability/selection
scope (26 checks), desktop/390/320 upload handoffs, enlarged-text handoffs,
GET-only unchanged/resolved recheck, action/reload/queue, and complete local
controlled guidance evaluation/activation/rollback/reload. These are real browser
and local fake-service checks, not real-model availability or a human usability
study. Failed experiments remain in the ignored evidence store.

The first full trial used the older root virtual environment and failed the
existing TLS trust checks. The isolated worktree was then bootstrapped from its
unchanged current lock, including the already-pinned corrected certificate bundle.
This was an environment mismatch, not a new trust-store change. Linux hosted
bootstrap and push/PR checkout checks remain separate gates.

## Release gate record

Locked bootstrap and the full local command passed: 1,423 unit tests, 111 browser
tests using the locked Chromium runtime, and 29 edge tests. The complete existing
Firestore emulator suite passed (7 tests). These counts are separate evidence
types. Exact [push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40180926334),
[PR merge checkout](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40180944772)
and [merged main](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40181478422)
checks each passed 1,423 unit, 111 browser and 29 edge tests. Bootstrap, locked
browser installation, environment propagation, read-only token permissions and
actual checkout trees were verified. [PR #12](https://github.com/imrohitagrawal/batchbeacon-ai/pull/12)
merged the reviewed source `d811586c5bae030969c08ca64ed5b969f7618a39`; the main merge
`dfb1abd692b64fa7333ef6c2a6dcd03468d726c5` has the same tree.

One independently admitted bounded cloud build passed. Its generation-bound
source archive equals the allowlisted manifest. Local and cloud packaged checks
passed closed mode, exact current connected configuration/assets, original
liability compatibility and TLS trust, without network/model calls in the smoke
containers. Deployed image:
`sha256:0c2668f5c94490b4b5134912df9bccaf9bb2dae033419303e8c6f3503209180d`.

Independent zero-traffic review preceded promotion. The custom domain and Cloud
Run fallback serve exact reviewed assets. Direct browser checks passed saved-label
retention, visible mobile handoff after image decoding, authoritative unavailable
AI reason/disabled controls, GET-only status feedback, correct-case queue reopen,
reload, guidance navigation and desktop/390/320 reflow. Guestless capability reads
return 401; another workspace's existing case returns 404. One new synthetic
workspace and two sample uploads were used across candidate/live checks; the
same test cookie was explicitly reused for each hostname. No extraction, action
or guidance mutation was submitted. Model attempts and held liabilities remained
unchanged. Runtime, IAM, resource limits and permanent admission v2 were preserved.

Two failed browser probe runs remain recorded: a health-alias expectation also
failed on the unchanged baseline (canonical health passed), and a mobile geometry
probe selected a `display: contents` parent instead of the actual sticky navigation.
Independent reproduction confirmed these probe defects; successful continuations
reused the original workspace/cases without another upload. The initial desktop
handoff screenshot preceded image paint; later retention and the decoded-image
mobile viewport are separate evidence.

A pre-existing OpenTelemetry dependency advisory remains open maintenance debt.
Independent local tests confirmed the affected parser but did not reproduce an
application request path reaching it. This increment does not fix the dependency
or claim universal non-exploitability. Bounded dependency remediation is separate.

These passed UI release gates do not establish full product readiness.

At the initial journey release, support handoff remained incomplete: no public
destination had been selected or receipt tested. The U34 follow-up below records
the later owner selection. At that release the UI explicitly said so and exposed only a copyable case
reference. It does not expose the private monitoring address, send a message or
promise a response. See the [operator procedure](../JOURNEY_OPERATOR_RECOVERY.md).

Full fresh real-model/video acceptance, first-time human usability and actual
assistive-technology evidence remain incomplete. Earlier source/protected-case
and broader acceptance limitations are preserved; this increment does not turn
historical results or controlled fixtures into fresh acceptance.

Private evidence: `.local/run-records/journey-correction/`, including retained
baseline failures, reviewer reproduction suites, deployed baseline readback and
F8 diagnosis. Session/account identifiers and detailed receipts remain private.

## Owner-selected support contact follow-up

Under U34 the owner selected `rohit@stackclimb.com`. A typed optional deployment
setting supplies the mailbox and an encoded mail link; it cannot introduce mail
headers, multiple recipients or arbitrary URLs. Invalid configuration fails before
credential discovery. The visible link opens the visitor's email application with
a generic subject. Case references remain an explicit copy/paste action; cookies,
tokens and private logs are not attached. The application sends no email.

The implementation merged through [PR #13](https://github.com/imrohitagrawal/batchbeacon-ai/pull/13),
source `351990d6cf7879ede920ccedadc070fb63e6f8c7`. Independent contract and UI
reviews, 1,440 unit, 113 browser, 29 edge and seven Firestore emulator tests passed.
Exact source-push, PR-merge and main hosted checks passed; packaged configuration,
TLS, source archive and zero-traffic candidate checks passed.

The owner subsequently authorized one verification email and confirmed receipt
with an inbox screenshot. This is an observed test receipt, not a promise of
ongoing availability, delivery deadlines or resolved cases. The existing candidate
was promoted after fresh independent review. Both public hostnames passed exact
configuration/asset and retained-session browser checks; no new workspace, upload,
action or AI request was made. Runtime JSON, resources, IAM, accounting and unknown
liabilities remain unchanged. Image:
`sha256:e6e474e6c81842cdeb74e01491c8ca277762dab59506e5fe44227928f3d6ac6d`.
No additional email or paid AI call is authorized.

The retained live test workspace has exhausted allowance without its own unresolved
request, so the operator panel is correctly hidden. Live configuration, encoded
link and exact assets passed; visible unresolved-panel keyboard/mobile behavior
passed controlled tests separately. An initial live probe assumed the wrong state;
its failure and independent reproduction are preserved. No live unresolved-panel
visibility or full first-time/assistive-technology acceptance is claimed.
Private support evidence: `.local/run-records/support-contact/`.

## Acceptance continuation: cache accounting and status semantics

The [single current checklist](../USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md#9-authoritative-acceptance-checklist-and-continuation-checkpoint)
owns all R01–R12/F1–F8 statuses. Independent planning reviews preceded corrections.
The newer retained response reproduces a nonzero cached-token rejection; the older
timeout has no corresponding complete response. The parser now validates cached
counts and modality subsets within prompt totals and retains the entire prompt at
the original evidence-bound price. Unknown meters, malformed usage and unsupported
traffic still fail closed. No schema, discount, runtime policy or timeout changed.

Five new offline regressions failed on the baseline; the corrected cache/durable/
wire/runtime selection passed 166 tests. Independent retained-byte and synthetic
concurrency/GET/reader checks passed separately. Actual retained bytes parsing is
offline provider-evidence verification, not a fresh model invocation or successful
product completion. Both live liabilities and failed runs remain unchanged.

Pending status previously set aria-busy on its own live region, allowing AT to
defer the update. Twenty delayed success/failure/duplicate-control regressions
failed before correction and passed after separating the visual loader attribute
from live-region busy semantics. Buttons retain truthful busy/disabled state.
Independent controlled source/browser verification passed; actual screen-reader
speech remains unverified. No full accessibility claim follows.

The old image cannot read a synthetic settled cached receipt: reproduced offline.
It remains a compatible rollback only while the ledger has no such receipt. Before
any separately admitted settlement or new model operation, retain a verified
cache-aware rollback image and recheck compatibility. Publication must prove all
existing attempts and balances unchanged; it does not settle old attempts.

Provider semantics: [GenerateContentResponse usage](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse)
and [implicit caching](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview).
Announcement semantics: [WAI-ARIA aria-busy](https://www.w3.org/TR/wai-aria-1.2/#aria-busy).

Private continuation evidence: `.local/run-records/acceptance-continuation/`.
The corrected source is `bc7da038c6f30b41abe0a4b8f5b6395234f95efd`;
[PR #15](https://github.com/imrohitagrawal/batchbeacon-ai/pull/15) merged as
`dee87ad7866c3ca3b075496d7ea83cfebb4d286e`. Its final documentation successor
`91378c6` changes no packaged runtime file.

Evidence types remain distinct:

- **Unit / controlled:** 1,464 unit and 133 browser checks pass with locked bootstrap;
  29 edge checks pass. Baseline cache/status failures remain retained. Independent
  backend, UX/video and security/operations reviews cleared the narrow corrections.
- **Firestore emulator:** eight tests pass, including concurrent/idempotent cached
  receipt reconciliation, preserved failed run and read-only recheck. These do not
  settle a production liability.
- **Hosted CI:** exact source push/PR, final documentation push/PR and merged-main
  commands, dependencies, permissions and checkout topology pass. Final checks:
  [push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40211640311),
  [PR merge](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40211645716),
  [merged main](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40212220684).
- **Package / candidate real service:** one reviewed build passed network-disabled
  runtime, TLS, support and cache checks. Generation-bound archive matched all
  60 manifest files. Independent zero-traffic configuration/IAM/image and existing
  owned-workspace browser checks passed. No new guest, upload, action or AI request.
- **Actual provider evidence:** the retained complete response now parses offline
  using the original rate. This is historical provider-byte evidence, not a new
  model call, successful extraction completion or invoice reconciliation.
- **Actual AT / human:** neither acceptance study is complete. The host capability
  experiment did not capture speech and restored its then-original off state.
  Later owner activation/recheck and failed disable supersede that state observation;
  see the resumption chronology below. This is not a screen-reader pass.

The first candidate browser probe observed one queue GET 429 during rapid reload.
It omitted the response body, so its precise cause remains unconfirmed. The
changed probe waits for visible queue completion and the existing configured
minimum interval before reload; it retains strict response assertions and captures
error details. It passed without product/rate-policy changes. Both results remain
private evidence; the success does not erase the transient failure or prove
universal availability.

The submitted media review used the exact retained final MP4, matched to the
publication receipt for `https://youtu.be/IpY2_GeR4Ic`, with SHA-256
`f9ec73a82eeab9139dc943f1df2b8dbf40edce11090fc3c90101a7dd7cb8b930`.
Reviewers inspected its narration/storyboard, retained contact sheet and fresh
60/125-second frames; the integrator also inspected the contact sheet. Continuous
YouTube playback or a new full audiovisual review is not claimed. The film shows
explicit extraction, evidence review, unchecked human confirmation, saved queue,
phone/reopen, actual unrelated-identity extraction rejection, and explicitly prior
guidance evaluation. A timeout is not that filmed negative result.

The reviewed candidate was promoted once. Both
[custom hostname](https://batchbeacon.stackclimb.com) and
[Cloud Run hostname](https://batchbeacon-ai-xotgrrfbcq-el.a.run.app) passed exact
asset/configuration and existing-workspace browser checks at the corrected image:
`sha256:4bb48a2048df5ddbfbfb845a649f4d7c9da33cb66610f5efd770f6e82073452f`. Actual serving readback confirmed the exact revision/digest,
100% traffic, unchanged runtime/IAM/resources/support, model ledger and both held
unknowns. The corrected image remains retained for cache-aware rollback.

A guest-admission preimage changed between candidate review and promotion. The
check stopped before dispatch. A narrowly reviewed new exact preimage preserved
old evidence, confirmed unchanged model/attempt records, and continued to reject
further drift. No quota, policy, model, settlement or second build was introduced.
Our candidate and both-host probes reused existing access and issued no new guest,
upload, action, model request or email. Aggregate public activity is not silently
attributed to our tests.

Current S evidence includes retained-label/unavailable messaging, configured
support link (not opened; no email sent), read-only recheck, queue completion/reload, navigation
focus and 320/390/1440-pixel reflow. It does not include fresh extraction or visible
unresolved-panel access. Both recorded unresolved owner sessions have expired;
the newer original capability was unavailable during its valid window. Controlled
panel/ownership/expiry tests pass, but no usable known live case remains.

The prospective accounting correction and its release are accepted within this
scope. Full judge reproduction remains unverified: public model admission is
blocked, fresh SFA A/B and third-identity validation lacks new authority, and
actual AT and first-time H observation are incomplete. Prior source/protected and
Operations limitations remain under U18; support receipt is not ongoing-availability
proof. The prepared private settlement/validation proposal grants no authority.


## Acceptance resumption — 26 October 2026

No product code, runtime, deployment, source rules or submitted media changed.
Independent refreshed release/API reads confirm the same source/image, full traffic,
configuration/IAM and exact assets/support on both hosts. PR15/16 and final main CI
remain successful; the earlier full suites are reused because their code/config
bindings remain valid. Initial accounting inventory preserved both unknowns. The
subsequent explicitly authorized Operation A settles only the newer retained usage;
independent complete-inventory readback verifies the exact postimage, older hold,
failed/timed-out runs and expired ownership. No legitimate active unresolved owner
is available. No extraction completion, action or session recovery was fabricated.

The private Operation A packet now includes a narrow transactional preimage/version
and exact-postimage wrapper around the existing SharedAdmission/Firestore path.
31primary and21independent fake-SDK tests plus3actual isolated emulator cases cover
exact two-document writes, protected records, drift, replay and uncertain commit
acknowledgement. Cache-aware reader/retained image compatibility passes; the prior
reader cannot be used now that a cached settled receipt exists. The final private
dispatch driver received focused tamper tests and independent review, then fresh
exact admission and one guarded transaction under the owner's A-only authorization.
Direct readback and independent verification confirm completion; shared public
capacity reopened, with none reserved for validation. Runtime/image preflight is
external to the transaction and relies on sole-integrator deployment control. No
generation or token-count call ran during Operation A. The separately authorized
U37 model series stopped at its first pre-call image guard; see below.

The experience reviewer freshly verified the same220-second MP4 hash and inspected
all44five-second sampled positions across the full sequence plus full narration/
storyboard. This is complete-sequence sampled visual review, not continuous playback
or actual subjective audio listening. No new narrative blocker was substantiated.

A current-source local fake-service fixture was prepared for human observation.
Controlled checks cover delayed success, refusal, unknown usage and upload error;
agent-operated Chrome observed selection/saving, immediate processing, completion,
unchecked confirmation, saved simulated action, queue/reopen and reload. Fixture
clock/data/storage are synthetic and disclosed. These are C/B evidence, not live
provider, actual assistive technology or first-time human results.

VoiceOver chronology: the historical restored-OFF result predates the owner's later
manual activation and failed disable. Owner permission exists; the recorded tool
handoff failed without a visible permission prompt. A fresh supported inventory
reported VoiceOver not running; the later owner report explicitly establishes
owner-observed ON. During the first human-operated controlled task the owner heard
nothing. This is a recorded AT failure with unlocalized cause: the pending
diagnostic found silence on other webpages too, persisting after the owner
reported settings correct. Working ordinary AT output is unestablished. No application
root cause, speech pass or completed AT acceptance is inferred. No native app retry,
setting change or restriction bypass occurred. The remaining AT tasks and uncoached
novice study are incomplete.

The canonical section9 register retains every R01–R12/F1–F8 and all historical
broader limits. Exact evidence, failures, owner-decision packet and resource cleanup
are private under `.local/run-records/acceptance-resume-20261026/`. Current public
records omit ledger arithmetic; prior historical disclosure remains unmodified.


U37's first pre-call image guard stopped before any generation or token count.
The operation proposal incorrectly treated Mac-local PNG serialization as the
expected deployed byte hash. Independent metadata/generation-bound storage reads
and pixel comparison verify identical approved third-label pixels with different
PNG bytes. This is an operation-manifest preparation defect, not a demonstrated
wrong-image or product defect; the precise encoder cause is unproved. Original
failure evidence remains immutable. A corrected, independently reviewed proposal
required a fresh explicit decision and reuse of the existing owned workspace
and saved third capture, without adding calls, retries, time or budget. U38 supplied
that separate authority after 23 focused capture-verifier tests and independent
review of fixed approved pixels, conditioned storage provenance and immutable
actual server-byte bindings.


B2 then passed fresh exact guards and executed one generation. The complete HTTP200
response ended normally but put “Invented third identity,” the printed explanatory
subtitle, into the product-name field. The server correctly refused the identity
before comparison/action. Independent offline translation confirmed source agreement;
pack, lot and date were correct. This is an incorrect extraction and failed model
acceptance, not a deterministic nonmatch, timeout or successful negative case.
The generation and retained usage are directly evidenced; one associated count is
inferred from the unchanged guarded path, with no separately retained count bytes
or original serialized wire request body. Request hash/input/configuration bindings
and complete response bytes are retained privately.

Automatic conservative original-rate settlement passed independent recomputation
and complete-inventory comparison. No new unknown, unrelated record/version change,
comparison or action occurred; the older hold remains. First-failure stop ended the
series: SFA A/B and retries were not attempted. Independent final both-host assets,
configuration and runtime reads pass. Actual browser evidence covers processing,
duplicate-control disabling, refusal, correct image, queue/reopen/reload and phone
context. These do not establish actual speech or novice comprehension. The lingering
upload receipt is advisory wording ambiguity beside a truthful current refusal.
No application source, image, configuration or submitted media changed.

The canonical register retains fresh positive and deterministic-negative M gates,
AT/H, unavailable legitimate live-panel evidence and broader U18 limitations. Future
changed model evaluation requires a reviewed bounded proposal and new authority;
remaining slots in the stopped series cannot be used. Private independent final
proof and screenshots are under `backend/operation-b2/` in the resumption evidence.


## Unpaid third-label diagnosis and candidate regression — 26 October 2026

The original label prints “Meadow Vale Brie” immediately above “Invented third
identity” in the same large type. The complete provider output already contains
both lines in `label.name.raw` and `value`, with a box enclosing both. The generic
ProposedValue schema permits this string; schema validity cannot establish semantic
field correctness. Translation preserves KNOWN raw/value equality, and name
normalization only case-folds/joins whitespace. The additional words therefore
fail the exact retained-identity boundary before comparison or action. This is a
model field-selection failure with correct protective refusal, not a parser-added
subtitle, encoding mismatch, source substitution or timeout.

The exact effective runtime instruction was v6, not the module's v5 default.
Reconstruction through the deployed pure request guard and retained image/source,
schema, settings and ADK suffix produces the stored canonical request digest
`b20c1a37b0e0b35ba73611a94b0691e6e962a182b41b1927febd939e7f80e24f`.
This proves canonical semantic request identity, not unavailable original wire
whitespace/order, headers or separate token-count response bytes. Retained response
replay independently confirms source agreement and identity disagreement.

Layout adjacency and lack of explicit product-name versus caption instructions
are plausible contributors. The evidence does not reveal which feature caused
Gemini's choice. The smallest proposed correction appends general field-selection
instructions to effective v6: preserve genuine multiline brand/variant text,
exclude clearly separate demonstration captions, retain selected text verbatim and
use ambiguity instead of guessing. No expected name/lot/verdict is injected.
`tests/fixtures/name-field-prompt-candidate.json` is inert, not production config.
No sample, schema or identity-guard change is proposed. Candidate effectiveness
requires a separately authorized real-model experiment.

Eleven added unit/controlled cases (61 with existing reviewed-extraction tests)
exercise the actual installed ADK mock request, prompt/hash propagation, subtitle
refusal, correct A/B and third-identity controls, genuine multiline names,
raw/value mismatch, ambiguity and wrong recalled-name substitution. These authored
responses test boundaries, not Gemini behavior. Independent review reproduced them.
Full local suites pass 1,475 unit, 133 browser and 29 edge checks. Prior eight
Firestore product tests remain historical; this phase additionally exercises three
actual loopback conditional-migration tests and private pure-plan guards. No live
cloud/provider operation or production activation occurred.

Private migration preparation exposed two defects before any execution: a proposed
Firestore verify write is unsupported by the actual SDK, and an initial readback
classifier accepted changed creation metadata. Both are REQUIRED_CONTRACT operation
preparation defects. The corrected design uses a real transaction reading all exact
preimages, then one conditional budget-payload write; readback preserves every
other metadata field and compares aware timestamps. Original failures are retained.
Zero active owners and fenced/drained writers remain prerequisites; transactional
version guards alone do not prove complete inventory or prevent phantom creation.
Only budget policy/grant hashes change; original unknown liability, failed runs,
expiry, cached receipts and all other documents remain exact. No production
executor or admission result is inferred from an emulator pass.

Independent product/AT review also verified a labelled in-process fixture in which
one held mock attempt settles without completing its failed extraction. Normal
owned saved-status checks show unchanged hold, then failed/resolved status; no
comparison/action is created. Guestless/foreign/expired access and duplicate
moderator transitions are guarded. No network, native setting or paid call is
involved. A human procedure and observation form are prepared; neither actual AT
speech nor first-time human comprehension has passed.

The video claim and the stricter requirement remain separate: filmed protective
refusal is recognizable and now actually observed under U38; successful deterministic
identity-based nonmatch remains a REQUIRED_CONTRACT model-acceptance gap. Fresh A/B
model validation remains open. Controlled positive flow, sampled-video parity,
production failure behavior and future human comprehension are distinct evidence.
The same canonical register retains all 20 requirements and broader U18 limitations.
Private exact proof, reviews, failures, proposal and cleanup are under
`.local/run-records/third-label-correction-20261026/`.


### Conditional migration expiry-recovery amendment

The initial budget-only proposal was subsequently superseded on one compatibility
point. Controlled SDK decoder/service/HTTP evidence reproduced repeated 503 for a
retained expired cookie: stale guest configuration markers were rejected before
ordinary expiry validation. Normal cookie-absent issuance still worked. This was an
R09 REQUIRED_CONTRACT in the conditional operation proposal, not a live migration
or ownership bypass. No affected proposal was executed.

The smallest corrected plan also updates only the two derived configuration markers
on already-expired guest envelopes. Every guest payload, ownership, expiry, incident,
learning/retail record and history remains unchanged. Target markers derive from the
exact typed runtime and reviewed source binding. The retained expired guest
postimages now decode normally and are rejected with 401 in both forward and inverse
controls, permitting existing expiry cleanup without restoring access. The source
preimages include both historical and current learning markers; inverse targets the
reviewed runtime markers instead of restoring obsolete values.

The revised pure plan passes 32 focused checks. Four actual loopback Firestore tests
cover the bounded conditional metadata writes and complete transaction-read inventory,
lost acknowledgement, and atomic refusal after budget, attempt or guest drift.
Independent backend/operations verification passed for the revised proposal;
production activation still requires an explicit owner decision and fresh admission.
Existing call/spending/window limits, zero-active-owner
rule, unknown-liability stop and deferred rollback remain unchanged. No production
source or deployment changed; the original budget-only evidence is retained privately.


### U40 consolidated conditional operation preparation

The owner kept C1 unauthorized and requested one complete conditional packet, not
an isolated test ending with routine recovery undecided. The private REQUEST and
attended RUNBOOK now cover third → A → B, all-pass candidate reopening, known-stop
natural-expiry inverse/restoration, unknown-liability retention/ordinary-only
access, and exact partial-setup cleanup. Separate validation and recovery deadlines,
full conditional commitments, fresh admission, original source/runtime/price/record
bindings and stop conditions are explicit. No live mutation or provider call occurred.

Independent review reproduced three REQUIRED_CONTRACT preparation issues: a case
proof could be reused for another case; dispatch could use the later recovery
window; duplicate transaction-read rows were collapsed. Corrections bind the exact
pending identity/capture/config/intent, fix an immutable absolute validation deadline
and reject invalid read sets before Commit. Operations review additionally caught
an unbounded buffered service response despite a bounded transfer precharge. The
adapter now streams within configured bounds, precharges final-chunk/overhead
allowance and retains unusable acknowledgement as uncertain without replay.
These were private coordinator defects, not deployed application regressions.

The final focused suite passes53 unit/controlled checks. Independent backend review
also exercises18 targeted negative/branch cases. Six actual anonymous-loopback
Firestore tests exercise the current transaction adapter, lost-ack readback, fence
field preservation and rejection of duplicate/missing/unexpected/stale reads. An
initial no-op fence fixture expected a changed postimage; the failed evidence is
preserved and the fixture now uses a different fence value. Both owned emulator
processes were stopped and verified. The retained32 planner/decoder and4 migration
emulator checks remain separate prior evidence, not recounted as new tests.

The original application, tests/fixtures prompt candidate and public UI are unchanged.
No new hosted release check, cloud read, deployed verification, real-model result,
AT speech or novice observation is claimed. Existing hosted/application evidence is
reused for unchanged source. Actual runtime versions, prices and balances remain
fresh execution prerequisites, never fabricated from hypothetical postimages.
All20canonical requirements remain; broader U18 gates and historical Git disclosure
remain unchanged. Details, exact hashes, initial findings and final specialist
reviews are under `.local/run-records/conditional-execution-20261026/`.


### U41 fresh admission evidence, no activation

The owner approved the exact conditional packet and reiterated full commitment
admission before any mutation. Ten bounded cloud GETs read the current service,
revision, IAM and complete fixed-readTime namespace. The typed ledger shows less
available public model capacity than the approved whole commitment; the exact
shortfall is private. One attempt reservation fitting does not meet the stronger
whole-envelope condition. Independent backend verification confirms the stop.

All318previously retained document contents and versions remain exact, including
22attempts and11failed runs among24runs. The319threcord is an expired historical
refresh record created before this operation, consistent with earlier B2 owned
refresh observations; exact caller attribution is not proved. Service, revision
and typed runtime remain unchanged. No active owner or nonterminal run exists in
the observed inventory. The original unknown liability is preserved exactly.

Eight separate cookie-free public GETs verify health, opening HTML, application
JavaScript and config on both hostnames. These are real-service read observations,
not a new browser journey or actual model acceptance. No guest was issued. No cloud
write, generation, token count, settlement or access fence was dispatched. The
execution clock was not started and no rollback is necessary. Outstanding non-model
obligations were reviewed separately; no full financial admission is claimed.
Existing AT/novice procedures remain ready, with actual participation/output gaps
unchanged. Exact receipts and independent reviews accompany the private packet.


### U42 supervised model observation and operational corrections

The owner removed financial stop thresholds for supervised testing. Existing typed
DEVELOPMENT-phase support covered the finite three-case workload, preserving public
allocations and the original unresolved liability. No unlimited public mode or
manual settlement was introduced. The private operator adapter initially sent a
query field rejected by the actual Cloud Run API. Complete readback proved no
candidate effect; original controls were restored. Validation-only comparison
isolated one unsupported query parameter, and the corrected activation was then
independently verified. This failure remains retained, not counted as deployment
success. Current image/application source is unchanged; prompt configuration and
compatible metadata changed through reviewed guarded operations.

Private operational timing and aggregate transfer-cost estimates were amended
explicitly under the continuation instruction. Actual request/response bounds,
original overall authority horizon, natural owner expiry, call accounting and
unknown-outcome protections remain. Eighty focused private coordinator/adapter
checks pass, including failed acknowledgements, exact fresh readback, original
horizon, no replay and ordinary-only recovery. These are not eighty new application
unit tests, new hosted CI, actual AT speech or human usability observations.

The actual third-label request included the candidate instruction, established by
exact canonical request hash reconstruction. Gemini nevertheless selected both the
product name and the separate sample caption as a KNOWN name. Source translation
agreed and other inspected label fields were correct. The unchanged identity guard
refused the extraction: no comparison or action was created. One generation settled
automatically in DEVELOPMENT; public balances and older liability remain unchanged,
with no new unknown. No A/B or retry followed. This is a failed model-acceptance case
and a successful protective refusal, not a passing deterministic nonmatch.

Actual browser evidence confirms immediate Saving label / Extracting and checking
feedback, disabled competing controls, retained-label completion, focus handoff,
truthful rejection, and a queue with one needs-human-review case and zero actions.
Independent UX review retains lingering upload/status messages as duplicate F7
advisory ambiguity. Working screen-reader output, novice comprehension and a
legitimate active unresolved panel remain unverified. Safe changed recovery restores
ordinary access while keeping extraction closed on the coherent candidate; failed
case history and original expiry remain intact, with no inverse after reopening.

Next correction work must address field selection using the retained exact request
and response; merely retrying the failed prompt or weakening identity validation is
not a fix. A field-specific schema/instruction candidate with unrelated examples is
an offline recommendation, not proven efficacy or an activated change. All twenty
requirements remain in section 9 of the canonical plan. Detailed operation, model,
review and UI evidence stays in the ignored supervised acceptance record.


## U43 name-schema correction: local implementation checkpoint

Independent backend/AI, product/UX/accessibility and operations planning reviews
completed after fresh deployed service and complete inventory reconciliation.
The sole production change adds name-specific response schema guidance; an explicit
versioned prompt candidate adds generic field-selection examples. Original samples,
identity rules, translator, source review and historical failed responses remain.

Local verification: 1,483 unit tests, 133 browser tests, 29 edge tests and eight
Firestore emulator tests pass. An initial test-line lint failure was corrected;
its log is retained. Independent backend review ran 19 boundary tests and replayed
both exact failed provider responses through the current translator/pure identity
guard: source agreement and protective identity refusal remain. Actual ADK mock
requests carry the exact schema and prompt. These are controlled regressions, not
proof that the new model experiment succeeds.

New image, hosted checks, compatible active-owner migration and actual third/A/B
acceptance are pending at this checkpoint. Fresh reads show ordinary access open,
paid extraction closed and the historical unknown preserved. Actual screen-reader,
unfamiliar-user and live unresolved-panel evidence remain pending. Private evidence:
`.local/run-records/name-schema-acceptance-20261026/`.


## U43 name-schema, reasoning and request-delivery correction

PR #20 source `9deb89d` and immutable image
`sha256:5f02919d372975b0e99f7f8bb254b650ff02551353a4af61ca928ee93b73e3e0`
passed1,483unit/133browser/29edge/eightFirestore-emulator tests, exact hosted
push/PR/main topology and allowlisted packaged-source checks. Generic field-boundary
schema/prompt retained original labels, raw/value semantics and deterministic guards.

Actual LOW still selected the caption into the name and was refused. HIGH first
returned complete provider504; a longer finite request returned complete200 with
MAX_TOKENS, incomplete source JSON and no label proposal. Exact canonical requests,
original responses and usage/price receipts were independently checked. All known
outcomes settled automatically; historical unknown liability and failed custody
remain. No fresh A/B or successful nonmatch is established.

The last customhost response timed out while origin processing completed. Original-key
reconciliation recovered the saved known failure with exhausted allowance and no
comparison/action, without a second AI request. This is actual delivery recovery,
not unknown-accounting panel acceptance. The finite Worker timer proof was narrowed:
it did not remove the separate proxy idle limit and ends at response headers.

Three independent specialists reviewed the local correction: opt-in JSON whitespace
heartbeats on the same request, explicit final protocol/status/body validation,
immutable-expiry recheck and worker ownership through disconnect. Typed progress
policy is disabled by default; activation and actual hosted delivery remain gated.
Focused23unit/12browser/30edge checks passed, including real Uvicorn early chunks,
ASGI2.0/2.4 disconnects and original-key recovery. Additional independent cancellation
and browser error/expiry probes passed. These are not real-model or human evidence.

Current public availability, next release steps and private run pointers are in
STATE. The existing section9 register retains all20 requirements, exact submitted
video parity, AT/unfamiliar-human dependencies and broader disclosed quality gates.


## U43 progress release and observed availability feedback

PR21 source a0d2320 / merged main c178b8b passed full local1,506unit/145browser/
30edge/eight emulator and exact hosted push/PR/main1,506/145/30 checks. The
allowlisted generation-bound Cloud Build source and five packaged offline smokes
passed. Image09dd9bde is deployed Ready100%; independent readback verifies exact
assets on both origins, unchanged service permissions and all retained accounting.
Compatible metadata changes preserved owners and domain records. The edge change
only preserves no-transform; other routes/settings remain unchanged. One new owner
was issued normally and issuance refenced, with paid admission closed. No model call
on the enlarged output configuration has occurred. Selected A capture pixels,
storage generation and ownership independently pass; both saved A records remain.

The user's next-step confusion was reproduced independently in both upload paths:
terminal receipt instructed extraction while capability disabled the button.
Classified REQUIRED_CONTRACT under R02/F1/R05/R09, not an authorization failure.
Backend, product/UX and operations reviews support one shared availability-aware
handoff, reason-specific recovery and guarded focus. No runtime/model/policy change.
Implementation and review are pending release; full hosted and packaged-image
verification remain required before deployment. Initial test lint failure is retained
and corrected. Root unrelated changes remain untouched.

The user reports VoiceOver reads navigation/static content. Exact automatic
pending/terminal speech and uncoached unfamiliar-user completion are unverified.
Recordings affected by reported tab switching are excluded. Concurrent Voice Control
was observed; speech feedback interference is a hypothesis, not audio-verified.
VoiceOver was turned off as requested. No automated/AX result substitutes for human
acceptance. All R01–R12/F1–F8 and broader source/protected/Operations gates remain.

Independent review also reproduced an existing F5 violation in both upload paths:
a late response after leaving and reopening the same case could replace current
capture/status and clear a newer pending key. Four primary success/refusal
regressions failed before correction and pass afterward. The correction reuses the
captured selection guard at the response/error boundary and guards sample-flow
continuation. It preserves the original server operation and does not retry it.
Independent verification and final full checks govern release of this correction.

Final local validation passes1,506unit/173browser/30edge/eight Firestore emulator tests. Independent backend verification passes77 journey/recovery checks; UX verification passes89 targeted checks and real-CSS desktop/narrow probes. These are controlled local results; exact hosted and deployed correction checks are still pending, as are actual human and model acceptance.

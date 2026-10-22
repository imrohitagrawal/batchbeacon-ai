# Video parity and judge-readiness implementation plan

Status: execution authorized; the core positive workflow is restored and independently
verified on the deployed correction. Both positive examples passed actual AI journeys;
the unrelated-label call returned a provider 504 and cannot count as negative acceptance.
All seven authorized calls, including U32's single failed retry, are used. U31's approved transfer and original-liability migration
are applied without releasing the unknown reservation. [M7](evidence/M7-judge-readiness.md)
records exact results, failures and the remaining gate. No submission change or optional
new guidance sample is included. This remains a bounded correction plan.

## 1. Objective and factual baseline

A fresh judge should be able to follow the submitted [220-second video](https://youtu.be/IpY2_GeR4Ic) through the supported historical-SFA workflow on the [live prototype](https://batchbeacon.stackclimb.com), obtain a defensible result, explicitly record an eligible workspace action and reopen the same evidence within the guest session. Uncertainty, service failure and expired access must remain understandable and must never become a successful result.

The video was recorded from a working release. Later changes addressed access, terminology, expiry, rate policy and hosting configuration. The audit reproduced failure of the first SFA sample twice in separate fresh browsers: acquisition FAILED/CHECK_FAILED, no comparison and disabled hold. This establishes a present failure, not that the UI edits caused it. Separate confirmed UI defects are misleading failure recovery, cached queue content and hidden mobile expiry. Subsequent read-only accounting review established that both failed audit runs dispatched no generation: a complete provider HTTP 504 response retained its conservative reservation, leaving insufficient uncommitted public allowance. Completed SFA A/B responses in the retained inventory have the expected identities. Three unrelated-label responses include explanatory text in the identity and are rejected, consistent with the video; no identity-rule change is justified. A prior rejection on the same incident must not be attributed to its later timeout.

Baseline provenance: STATE identifies application commit f0d9c0f974baf5e68992d274d48c8bddcc59fba1 and its deployed image. Audited deployed workbench JS/CSS match local source. Repository HEAD contains subsequent documentation and unrelated uncommitted operational updates; do not overwrite or include those implicitly. Record actual refs and runtime bindings anew before execution. Historical passing evidence must remain labelled historical.

Primary evidence and detailed reviewer notes are in ignored `.local/run-records/video-ui-audit/`. Public documentation must exclude session IDs, exact operational timing, private logs and provider response bodies.

## 2. Scope and execution decisions

- Preserve the approved Evidence in focus layout, real Gemini through ADK, deterministic verifier, Firestore, Cloud Run, three existing label examples and historical source disclosures.
- Repair extraction and its durable failure/recovery contract first; then queue freshness, guidance eligibility/clarity, mobile expiry and judge-guide provenance.
- Preserve U26 terminology. Visual synchrony means equivalent recognizable controls, workflow and truthfulness; it does not require restoring old words that the owner deliberately changed.
- Preserve ownership/expiry, explicit confirmation, currentness, deduplication, existing grant/pools/counters, UK review-only and no-real-inventory-effect boundaries.
- No model substitution, arbitrary parser relaxation, hardcoded successful result, silent replay as live AI, universal clearance, new countries, accounts, consumer dashboard or video replacement.
- No unfinished Work Package or Multi-Work-Package framework. Use repository tasks, one integrator and independent read-only reviewers.
- The owner authorized execution of this plan. Reuse applicable existing grants; independent technical review remains required. No switch of collaboration mode is claimed by this document.

Two delivery increments are recommended: A restores extraction and truthful failure handling; B completes already identified usability/provenance corrections. Each deployed increment must pass its applicable gates; B must not unnecessarily delay restoration of A. Integrate before one release if that is quicker and equally verifiable.

A new unclear-label public example is an optional, separately declared extension (section 7), not a prerequisite for fixing the filmed main path. Default execution scope excludes it until explicitly included in the implementation scope.

## 3. Video-to-application acceptance contract

| Video segment | Current obligation | Required acceptance evidence |
| --- | --- | --- |
| 0:00–0:49: problem, scope, human decision | Clearly explain retailer use, sample data, selected historical coverage and no safety/real-inventory clearance | First-screen and tutorial review; preserve disclosures |
| 0:49–1:06 extraction; 1:06–1:26 comparison | Default SFA sample uses actual retained image and actual bounded ADK/Gemini; deterministic identity-first comparisons are inspectable | Fresh deployed UI journey plus bound extraction/source/result evidence, not mock response |
| 1:26–1:40: explicit hold | Current supported match can open a confirmation; no automatic action; server rechecks revisions | Actual confirmation, one persisted logical action; duplicate and stale-confirmation regressions |
| 1:40–1:56: queue/reopen/mobile | Saved case/action survives reload within same session, queue is current when revisited, phone view exposes result | Same-cookie desktop reload and 390px viewport; separate fresh-mobile main path where admitted |
| 1:56–2:15: unrelated same-lot label | Never match solely from lot; reject disagreement or produce a supported scoped negative | Pure deterministic counterexample plus bounded real example. Video's rejected extraction is a valid safe outcome, not a promised successful non-match |
| 2:15–2:35: guidance and prior checks | Explain eligibility, fixed evaluation, explicit activation and monotonic rollback; represent prior evidence accurately | Local integrated lifecycle/denial tests; honest public ineligibility; actual deployed loop only if eligible evidence path is admitted |
| 2:35–2:57: services/check counts | Actual architecture remains as stated; historical check counts are not current accuracy or availability | Traceable filmed/current release matrix and fresh check results; no rewriting video counts |
| 2:57–3:40: vision and close | Accounts/consumer/aggregate/broader-country features remain visibly planned; Ops partial | Claim/link review; current scope unchanged |

Exact timestamps are navigation aids, not acceptance of every individual frame. Review full narration and captions alongside these assertions.

## 4. Phase A0 — establish the repair boundary

Owner: integrator. Independent reviewer checks evidence and scope.

1. Inspect branch, status, deployed image, runtime non-secret configuration, traffic and actual cloud project. Never rely on the globally selected CLI project. Preserve unrelated dirty files; use a clean isolated branch/worktree if needed. Only one writer edits shared contracts/deployment.
2. Create a private preflight manifest: accepted findings, paths, source/runtime hashes, test cases, rollback target, operation/call/spend bounds and finite execution admission. If charged-line budgets are used, declare them here rather than in generic source code.
3. Verify private paths are ignored and untracked, and scan intended public history/media before commit/push.
4. Read current application ledger, outstanding reservations, active pool, price evidence and remaining service allocations. Historical balance and healthy landing-page status are not current admission.
5. Preserve two failed attempts and locate their owned run/attempt records. No new inference is needed just to reconfirm the same failure.

Exit: an exact deployed/source/configuration baseline, approved bounded scope and actionable diagnostic evidence inventory. No speculative rollback or spend increase.

## 5. Phase A1 — diagnose and repair extraction

Likely inspection surfaces: `model_runtime.py`, `attempt_evidence.py`, `shared_admission.py`, `extraction_service.py`, `extraction_api.py`, `runtime.py`, source/identity configuration and the relevant installed locked SDK behavior. These are candidate surfaces, not authorization to rewrite all of them.

### Diagnostic decision tree

| Durable observation | Investigate next | Do not infer |
| --- | --- | --- |
| No generation attempt exists | Configuration/grant validation, input preparation, credentials, countTokens, deadline and admission failures | That generation provider is down or budget was spent |
| Reserved but undispatched | Dispatch claim, final request/config binding, deadline, attempt transitions | That no liability exists without authoritative evidence |
| Dispatched, no complete response | Transport/cancellation/timeout, durable response write and uncertain outcome reconciliation | Zero charge, safe repeated generation or a successful result |
| Retained non-2xx/incomplete response | Sanitized provider status, payload-size/encoding limits, model availability/permissions | Permission to change provider/model or relax controls |
| Complete response but usage not reconciled | Exact usage schema, arithmetic, SDK/provider compatibility and billing-mode support | Permission to accept invented totals or release unknown reservations |
| Reconciled usage but no extraction | Candidate finish reason/parts/schema, source translation, identity decision and publication | Permission to normalize unknown/unsupported evidence into success |

SDK/provider logs are deliberately suppressed to avoid private content disclosure; absence of ERROR logs does not prove health. `ModelFailure` is currently caught without durable reason and no-envelope failures collapse to CHECK_FAILED. Use existing immutable attempt evidence first. If pre-generation diagnostics are absent, add bounded safe failure classification before a single declared diagnostic experiment; keep raw payloads private and do not enable unrestricted logging.

Compare the actual filmed release, subsequent code changes and runtime/configuration changes. State causal conclusions only when the failed boundary is reproduced. If only UI presentation changed and model execution is unchanged, report that distinction.

Implement the smallest verified correction. Add a regression that fails with the demonstrated defect. Keep one bounded workflow, immutable provenance and authoritative usage settlement. Any tunable timeout/size/retry/cap change belongs in the typed validated configuration boundary and its effective hash. Do not increase limits just to get a pass. Unknown costs remain reserved until authoritative reconciliation. No model/network calls inside retryable database transactions.

Exit: root cause supported by evidence, failing regression passes after correction, independently verified boundary behavior, and a bounded actual service/model confirmation when admitted. A parser/SDK/provider change requires fresh official-version verification during implementation.

## 6. Phase A2 — durable truthful status and recovery

Inspection/edit surfaces: `extraction_service.py`, `shared_admission.py`, `evidence_service.py`, incident/extraction API views and `ui/workbench.js`; extend `index.html` only for necessary status/actions.

- Expose a small server-owned safe status/reason/recovery projection from durable run/attempt evidence. Prefer an additive compatible field/read view; assess persisted-schema compatibility before choosing storage changes.
- Distinguish initial draft, active client request pending, unresolved durable outcome, completed current, review-required, failed, stale/superseded and expired. An admitted/nonterminal Run does not prove a worker remains active. A failed run without an extraction envelope must never look like untouched Ready for evidence.
- Preserve prior evidence as historical, with active failure and currentness separately visible. Reopen/reload must recover status from server state, not only a transient banner or local storage.
- Map operational classes to concise actionable copy: temporary capacity, timeout, service unavailable, invalid extraction, unsupported/source disagreement, allowance unavailable, access expired and unknown outcome. Where cause cannot be recovered, say it is unknown; do not invent one.
- For unknown outcomes reconcile the original operation/key before any new generation. For definitive failure, make the next explicit action depend on server eligibility and remaining allowance. No automatic retries on reopen, repeated clicking or page navigation; do not add a second model attempt implicitly.
- Preserve disabled hold until the server supplies a current eligible result. Never enable hold merely because the UI recovered or a prior action exists.
- Keep exact internal errors/request/account IDs out of public messages. Store a bounded non-secret private diagnostic event useful to the operator; align any event with existing monitoring without new notification destinations or induced production failures.

Regression cases: failed/no-envelope/reload, prior-success then new failure, unknown-response/reconcile, definitive failure/retry admission, timeout/429/503, invalid output, expiry, denied access, stale evidence and duplicate action. Test request counts and logical action counts, not merely text.

Exit: AC-26 operational explanation/recovery and required journey states verified across API, integrated browser and persistence reads, with independent review.

## 7. Phase B — focused usability and parity corrections

### B1 Queue freshness

Edit `ui/workbench.js` and focused queue/browser tests. Mark cached queue state dirty after changes that affect rows; perform one bounded refresh on next queue entry or current visible queue update. Deduplicate concurrent reads and respect existing manual-refresh limits. Retain timestamped historical rows with clear refresh failure messaging; do not replace failure with zero counts. No polling/listener service is needed.

Acceptance: empty-queue-first -> create case -> return shows new row; hold/correction/new result update row/currentness correctly; repeated rapid navigation creates no unbounded requests; failed refresh preserves stale labels; refresh makes zero model/action calls. Applicable AC-33–36 remain server-enforced.

### B2 Capture guidance clarity and eligibility

Edit `learning_service.py`/API projection as necessary and `ui/index.html`, `ui/workbench.js`, `ui/workbench.css`; use existing eligibility/decision functions as the single authority, not client reimplementation.

Show the selected investigation and purpose. Empty state offers Check a product/Open saved queue. Complete labels explain that no further capture guidance is needed. No-safe-candidate feedback remains valid feedback with an honest outcome. Show the current stage and one primary next action; put revisions, counters and historical detail behind accessible disclosure. Disabled actions have specific nearby reasons. Preserve request, structured feedback, proposal, actual evaluation, explicit activation and rollback semantics. Distinguish refresh success, unchanged data, failure and stale records.

Test empty, matched/ineligible, eligible, feedback-only/no safe candidate, proposed, evaluating, failed/passed evaluation, active, rollback, stale basis, expired and unknown outcome. Preserve all six fixed evaluator cases and nine variants where applicable; do not call them model-accuracy tests.

**Optional extension: fresh judge guidance scenario.** Current controlled tests inject an unknown field; that is not a public live-model path. Production identity admission binds approved image hashes, so cropping or blurring an existing image is not a harmless UI tweak. If explicitly included, create one labelled synthetic incomplete-label asset and a narrowly reviewed identity/provenance admission; keep source predicates, budgets and eligibility unchanged. The actual image must lack the required lot/date and actual Gemini must support the resulting uncertainty. No forced UNKNOWN, forged record, seeded live verdict or correction trick. Require asset/hash/source-scope review and actual end-to-end loop evidence. If not included or not successful, show truthful ineligibility and prior-evidence explanation; do not claim fresh full-loop reproducibility.

### B3 Mobile and guide

Keep expiry date/time/timezone discoverable at 390px; retain the existing 320px and 200%-text/zoom checks; preserve eight-hour access. Verify touch, keyboard focus, announcements, source-link wrapping and modal consent/return behavior. Retain recognizable workbench hierarchy and U26 wording.

Update judge guide to distinguish filmed release, current deployed release, allowed same-session persistence, current labels and supported scenarios. Correct obsolete commit reference only after verified deployment. Keep submitted PDF/video unchanged and all original artifacts intact.

## 8. Correctness and negative-test matrix

Zero false acceptance is a release criterion for the declared cases, not a claim of universal zero errors. No genuine negative or unsupported case below may produce an unsupported match, safety/clearance statement or enabled hold.

| Test family | Expected behavior | Evidence layer |
| --- | --- | --- |
| SFA A and B supported positives | Correct identity and applicable lot/date scope; eligible match only with valid current evidence | Pure verifier, API integration, actual model/deployed positives |
| Third identity with shared lot | Supported scoped non-match or explicit rejected/review extraction; never positive from lot alone | Pure independent expected oracle plus actual selected example |
| Wrong lot, case/leading zeros, typed codes, date bounds | Exact typed comparisons; no unintended normalization | Existing/new targeted deterministic tests |
| Missing/ambiguous fields; ALL vs NOT_SPECIFIED vs UNKNOWN | Preserve distinctions and necessary review; no invented values | Verifier/proposal/API tests; eligible live extension only if admitted |
| UK/foreign/out-of-scope source | Review-only or appropriate scoped rejection; no new UK match admission | Reviewed-source/verifier contracts |
| Source epoch/observation/result change | Prior results/actions historical; stale confirmation denied transactionally | Integration, fake RPC, emulator and targeted real Firestore checks |
| Model/source/capacity/cost failure | No false negative/clearance; truthful state and bounded recovery | Fault injection in isolated local harness; no production outage |
| Duplicate click/key, lost acknowledgement, reopen | Reconcile original outcome; one logical action; no hidden model rerun | API/browser plus actual persistence readback |
| Guestless/foreign/expired/CSRF | Access denied without cross-session leakage or repeated unauthorized retry | API/edge/browser and bounded deployed isolation checks |
| Guidance failures/stale candidate/evaluation/base | No invalid activation; monotonic rollback and unchanged allowances | Existing fixed suite, integrated lifecycle and persistence boundary tests |

Reuse existing tests under `tests/unit/test_model_runtime.py`, `test_extraction_service.py`, `test_extraction_api.py`, `test_extraction_publication.py`, `test_identity_resolution.py`, `test_verifier_contract.py`, `test_action_service.py`, `test_learning_service.py`, `test_retail_http.py`, and relevant shared-budget/store tests. Extend browser tests in `test_workbench_recovery.py`, `test_workbench.py`, `test_learning_workbench.py`, `test_guest_admission_ui.py` for reproduced gaps. Avoid tests that simply mirror implementation.

U18's incomplete full 24-development/eight-protected evaluation and human custody are not silently reopened as passed or waived. The bounded repair matrix is regression acceptance, not a protected accuracy study. Do not access hidden H answers. More coverage does not justify unsupported accuracy claims.

## 9. Verification and hosted parity

Evidence categories must be separate: pure/unit, fake-RPC/API, intercepted-browser, real local server/browser, emulator, actual Firestore, actual Gemini, hosted CI and deployed browser. Passing CI cannot substitute for the paid-model route that failed in this audit.

Inspected workflow `.github/workflows/checks.yml`: push and pull_request, Ubuntu runner, contents:read, checkout persist-credentials:false, Python from `.python-version`, uv 0.11.18 and originally ten-minute job timeout. Observed cold dependency bootstrap required a reviewed twenty-minute timeout; test commands and permissions are unchanged. Required execution sequence (read from existing workflow; NOT newly run in this planning turn):

```sh
python -m pip install uv==0.11.18
./scripts/bootstrap.sh
uv run --frozen --no-build playwright install --with-deps chromium
BATCHBEACON_BROWSER_CHECKS=1 ./scripts/check.sh
node --test tests/edge/worker.test.mjs
```

The CI uv install belongs in the isolated runner, not a new global workstation install. `check.sh` checks lock, ruff, unit and optionally browser suites; it explicitly excludes real service/model/deployed acceptance. Use project-local admitted tooling on the workstation.

Before immutable candidate evidence, execute complete integration coverage, including the four existing Firestore emulator cases with valid admitted `BATCHBEACON_EMULATOR_CONFIG`. Missing emulator settings/skip is NOT RUN, not full-suite success. If adding a required emulator hosted job, declare its isolated bootstrap/config/no-secrets command in the increment and independently review it; do not silently expand cloud resources.

Enumerate direct-head versus PR merge checkout SHA, push/PR environments, dependency bootstrap, permissions, env propagation, full commands, manifest hashes and exact required status contexts from actual host settings. Run actual hosted push and PR checks; verify selected merge strategy yields tested content and verify resulting head/CI. No stale green status attached to another tree. Do not change protections or fabricate APPROVED reviews.

Only freeze the candidate after all required checks on its topology pass. If hosted checks expose a missed environment, add the executable regression, rerun relevant/full required checks and regenerate affected evidence. Historical counts are not a fixed target; current exact counts and skipped cases must be reported.

## 10. Deployment, live acceptance and rollback

1. Build from the tested candidate, preserve artifact/source/config bindings and conduct independent readback. Inspect the exact selected upload archive against an allowlisted manifest, excluding `.local`, `.batchbeacon`, private history/media and unintended files; verify equality with the generation-bound uploaded object and inspect the resulting unmounted image; the inspected repository has no root `.gcloudignore`, so `.dockerignore` alone is not evidence of safe cloud upload selection. Record archive/image inspection before deployment. Runtime-only fixes still require relevant configuration and real-service checks; code-only green checks do not prove runtime compatibility.
2. Prefer an existing supported candidate revision/tag path with no new IAM/public resource expansion. Use only the same dedicated project/service within existing caps. Hold a ready candidate at zero production traffic until independent configuration/IAM/resource verification passes. A candidate endpoint is not proof that the custom-host cookie/origin path works.
3. Preserve current grant dates, policy hashes, guest accounting, image ownership and active records. Backward-compatible readers/projections are preferred. Any required migration is conditional, counter-preserving, separately reviewed and reversible where possible.
4. Verify effective runtime identity/IAM/resource limits, traffic routing, source/image versions, served assets and guest/security boundaries. Verify fallback host separately; cookies are hostname-specific.
5. Conduct bounded candidate real-model acceptance before broad promotion where supported, then fresh custom-host acceptance after promotion. Capture actual extraction, comparisons, explicit hold, queue freshness, reload/reopen and mobile presentation. Independently reproduce the main positive journey; SFA B and unrelated-label assertions retain their own evidence. Do not force a particular nondeterministic text response.
6. Check actual retained records/actions, expiry/currentness and no duplicate operation. Any safety/ownership/counter violation blocks promotion immediately. Any fresh main-path failure prevents a judge-ready declaration even if the page/health endpoint is green.
7. Roll back a newly introduced regression only to a verified compatible image/configuration combination. Do not blindly route to a pre-extension revision with expired grants or old guest limits. The pre-repair deployment already has an extraction failure; returning to it restores that baseline, NOT judge readiness. If no working compatible target exists, retain truthful unavailable/review states and proceed with a newly bounded correction plan.

No induced production provider outage, unbounded load test, broad data deletion or secret exposure is necessary. Any load/fault cases use isolated harnesses unless a specifically bounded real-service test is admitted.

## 11. Resource bounds and stopping rules

Before any external operation populate the private manifest with current remaining balances, reservations, effective per-attempt reservation, exact case order and maximum new generation attempts. Proposed base scope: at most one changed diagnostic generation if evidence is insufficient, then at most five acceptance invocations shared across candidate/live stages (candidate SFA A, fresh custom-host SFA A, independent fresh custom-host SFA A, SFA B and unrelated label). A1 confirmation and fresh-mobile acceptance must use these same allocated slots; they are not additional calls. This is a planning ceiling, not a spend grant or a guarantee it fits available pools. Plan optional guidance calls separately.

Serialize model calls and settle/read back each outcome before another. Use actual current reservation/charge semantics; small expected token cost does not override a large required reservation. Do not consume the protected reserve, shift pools, increase caps, switch provider/model or clear counters merely to complete tests. If budget/admission cannot support required live gates, document that exact constraint and request only the material additional authority actually needed. Do not call a partially verified candidate ready.

After two unchanged failures, stop repeating and diagnose; the current two-failure record already meets that condition. Every further real attempt needs a changed hypothesis/configuration or a corrected candidate and an explicit bound. Continue independent non-paid local work while a paid/service path is blocked. No arbitrary time promise before diagnosis; estimate the correction after A1 identifies its boundary.

## 12. Independent review, disposition and closeout

- Integrator owns code, contracts, canonical state and deployment. Independent technical reviewer verifies the defect/correction and persistence/security boundaries. Independent judge reviewer validates first-time UI, video parity and limitations. Video/release reviewer checks provenance, exact CI topology and deployment evidence. Roles are real agent reviews, not human review impersonation.
- Classify findings after reproduction: CRITICAL_BLOCKER or REQUIRED_CONTRACT blocks; ADVISORY_DEBT, DUPLICATE and OUT_OF_SCOPE are recorded without unbounded scope growth. Track F1 extraction failure and F2 recovery presentation as linked defects with separately testable outcomes; consolidate their root cause only if diagnosis establishes that they share one. Queue/guidance/mobile/provenance are explicit scoped improvements, not invented security failures.
- Each blocker correction receives independent verification. Update the plan when the demonstrated root cause changes scope; do not silently expand into a redesign or provider migration.
- Produce a compact final evidence index: video claim -> test -> observed result -> code/config/source/image hash -> deployed revision. Preserve failures, incomplete gates and assistance. Record false-positive/unsafe-action counts for the declared cases, actual latency/sample count and model costs/unknowns without extrapolating global reliability.
- Update STATE, judge guide, focused usability plan and handoff only for verified work; keep STATE bounded. Existing unrelated dirty operational docs require deliberate reconciliation before staging. Verify ignored/untracked private paths and intended staged diff/history, commit/push within authorization, and verify remote ref and hosted results.

Definition of done: main filmed route works in primary and independent fresh deployed tests; both positive examples meet supported expectations; declared negative/safety cases have zero false acceptances; failures/reopen/reconciliation are truthful; queue/mobile and scoped guidance corrections pass; all required hosted/service checks pass on bound artifacts; rollback/remaining limitations are documented. This establishes credible tested judge readiness, not a guarantee of a win or every future request succeeding.

## 13. Execution handoff

Execution is authorized: reconcile this plan with current STATE and private preflight; complete A0/A1; preserve failed evidence; make the smallest supported correction; obtain independent technical verification; complete A2 and scoped B items; run sections 8–10 gates; close out section 12. Do not execute the optional unclear-label extension unless explicitly included. Do not claim Plan mode or a native Goal started merely because this document exists.

## 14. Plan review record

The final draft received independent implementation, judge/UX and video/release review. Review amendments incorporated: exact video checkpoints; upload manifest/object/image verification and zero-traffic candidate gate; no inference of worker liveness; explicit allocation of acceptance calls; no premature common-root-cause claim for extraction and presentation. Implementation reviewer passed substantive gates; judge reviewer confirmed scope/UX acceptance in its substantive readback; video/release conditional acceptance was addressed with the specified artifact and timestamp corrections. Private review notes remain under `.local/run-records/video-ui-audit/`. This review approves the plan quality within those scopes, not code correctness, source/gold custody or a deployed release.


## Execution refinement — verified provider error accounting

The correction uses an optional typed policy bound to the exact model, configuration, endpoint, allowed HTTP status, validity and retained official pricing/applicability hashes. Only a complete qualifying provider error can receive a separate nonbillable receipt. Unknown outcomes retain their reservation; incurred charges, lifetime attempts, acquisition counters, grant, phase and circuit are preserved. Historical applicability is an explicitly reviewed inference, not an invented provider publication timestamp. Financial reconciliation never creates a successful extraction.

Before writing new optional receipt/reason fields, provision and verify a compatible rollback reader with settlement disabled. Both rollback and final candidate require exact push and pull-request merge CI, full local integration checks, allowlisted source packaging and generation-bound archive verification. Persist dispatch intent before build/deploy commands; unknown outcomes require reconciliation. Bind candidate acceptance to its exact head, revision, image and runtime. The original deployed image cannot be used after the new record shapes are written.

## Execution refinement — unknown provider outcomes

A complete qualifying HTTP error and a client timeout without any retained response have different accounting evidence. The latter must retain its original reservation. New-run admission now checks complete owned attempt history in the same transaction and rejects unsettled original usage. A settled failed proposal may be explicitly retried; no failure state creates a comparison. Browser and actual-emulator checks cover this distinction.

The failed prompt-correction attempt prevents readiness acceptance and consumes the third of six model slots. At that checkpoint, three remaining acceptance slots were blocked by public capacity; the subsequent U31 refinement below supersedes that restriction within its exact bounds. The owner subsequently approved [U31](OWNER_DECISIONS.md#u31--bounded-model-pool-reallocation), moving ₹150 from development to public capacity within the unchanged total, with the unknown original reservation held. That decision permits only this specific exception to §11's pool-transfer prohibition. Before any deadline/grant change, preserve explicit original-grant liability and settlement lineage, refresh balances and independently review conditional migration and one changed diagnostic. The UI/accounting release is a truthful failure-handling correction, not a completed main-path acceptance.


## Execution refinement — approved pool transfer and remaining acceptance

U31 explicitly authorizes the ₹150 development-to-public transfer; it does not
increase the ₹6,000 lifetime ceiling, release the unknown ₹250, or add model calls.
The exact original liability manifest and permanent guest-admission version fence
must remain effective after conditional metadata migration. Elapsed time does not
prove old worker termination; database metadata conflicts reject stale writers.

Three remaining model slots are serialized: a new SFA A case in an existing unused
workspace on the zero-traffic candidate at 390px, then fresh public-host SFA B and
unrelated-label cases after successful candidate promotion. Candidate A uses the
disclosed Origin-forwarding test harness. An independent reviewer reopens that same
A case on the ordinary public host without another generation or new guest. This
replaces the originally proposed additional fresh independent A generation within
the unchanged six-call ceiling; it is not evidence of a separate fresh public A
model invocation. Each paid outcome must settle or remain conservatively reserved
before the next slot. A failed positive or generic negative failure cannot pass.

After migration, rollback must preserve the permanent admission fence, current
metadata and a compatible original-liability reader. The old admission hash and
pre-manifest image must not be restored. Actual results and limitations are in M7.


## U32 — one additional validation call, now consumed

The owner explicitly approved exactly one additional same-case unrelated-label
retry, increasing the test ceiling from six to seven calls within the existing
₹650 public pool and ₹6,000 total. The original unknown ₹250 remains reserved.
The seventh call again returned a complete provider 504, with no accepted result
or action. Both failures remain evidence. No eighth call or automatic retry is
included. After two unchanged failures, diagnose and prepare a changed bounded
latency/input-context experiment; do not relax identity rules or call either
provider error a successful negative result. M7 records the current unpassed gate.

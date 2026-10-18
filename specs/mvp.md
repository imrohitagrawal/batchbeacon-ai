# BatchBeacon AI MVP specification

Status: implementation specification, not implementation evidence. Baseline: approved [product brief](../HACKATHON_BRIEF.md), Edition 1.0. Operating rules: [master prompt](../HACKATHON_CODEX_MASTER_PROMPT.md). Scope and conflict decisions: [EXECUTION](../docs/EXECUTION.md). All acceptance checks below start **NOT RUN**.

## 1. Product outcome and scope authority

BatchBeacon AI helps retail teams connect official recall evidence to product photographs, check product identity and jurisdiction-specific restrictions, request missing evidence, approve a simulated action, and reopen decisions after source changes. Name and root/repository slug are fixed: **BatchBeacon AI / `batchbeacon-ai`**.

Preserve all eleven original P0 IDs. Owner U07 additionally requires P0-12 (retailer console), P0-13 (bounded operational learning) and the private operations obligations. The new scope extends the approved product; it does not replace the recall-verification differentiator or waive original acceptance. Winning competitiveness and a useful demonstrable workflow take priority over technology breadth. A smaller interface is an implementation simplification; dropping the second authority, genuine update, ADK, real AI, persistence, isolation or human approval is a material scope change requiring the owner.

Initial users: retail worker capturing a label; manager reviewing evidence and the retail queue; hackathon judge using an isolated synthetic guest shop; evidence custodian reviewing the supported notice corpus; private operator reviewing availability, costs and technical evidence. Customer-facing means retailer-facing, consistent with the approved product. One synthetic shop maps one-to-one to the existing guest session; production customer accounts are excluded. The guest can receive a server-issued **demo manager** capability for its own incident. This is not authentication of a real retail manager.

## 2. P0 requirements and acceptance

### P0-01 Evidence corpus

Support Singapore Food Agency and UK Food Standards Agency, two countries including JAPAC and non-JAPAC, plus the genuine original/update pair. Use brief source IDs S08–S10 and its corpus IDs. Preserve UK subnational coverage so the expansion to Wales/Scotland is representable. The two countries' products are separate incidents, not a shared outbreak.

**AC-01:** Every supported notice version has authority, country/subnational scope, original/final URL, published/updated/retrieved timestamps, content hash, immutable family/version ID, source mode, rights note, supported-format status and independently reviewed interpretation metadata. Null/missing review metadata is not approval.

**AC-02:** Gemini-proposed source restrictions are retained separately and checked against a human-reviewed manifest. A mismatch, incomplete fetch, unsupported predicate or missing source location is visible and review-only. A model cannot set `reviewed=true`. Correcting the reviewed manifest requires custodian evidence and a new revision; replacing bad inference with the manifest is not counted as successful extraction.

**AC-03:** The UI shows the exact checked authority, jurisdiction, version/date, coverage and historical/live status at the result. Original UK evidence is explicitly historical. A new result cannot silently treat an unavailable or changed source as current. Full authority pages, images and logos are not publicly bundled without permitted rights.

**AC-03 context addition (owner, 18 October 2026):** Preserve and cite the notice’s
recall reason and reported basis, authority-stated health risks, affected packs /
identifiers / lot-date restrictions, total recalled quantity when stated, actors,
company actions, regulatory actions, reported legal proceedings and authority
consumer guidance. The reason must be findable in the workbench and retail queue;
detailed context may use a clearly actionable disclosure. Bind to the exact notice
version/capture, preserve possible versus confirmed-at-source wording, and keep
NOT_STATED distinct from UNKNOWN. Pack size is not aggregate recalled quantity;
a regulatory notice is not proof of legal proceedings. Attribute historical
source summaries and link complete advice; no personalized medical advice or
individual-item contamination finding. New context requires source review and
cannot silently inherit an existing predicate approval. See
[context audit](../docs/evidence/M1-recall-context.md).

### P0-02 Real source and label extraction

Gemini extracts proposed notice rules and label identity/lot/date fields using a validated structured schema and evidence locations. Default candidate is `gemini-3.8-flash`; actual availability, endpoint, settings, SDK and quota must be verified locally. Preserve source-specific codes `319456` and `318591` as product codes, not invented GTINs. Reviewed brand/product/variant/pack identity is usable when a source code is not printed on the package.

**AC-04:** At least one authorized deployed run demonstrates actual Gemini inference from a selected source and synthetic package image. Save redacted raw structured output, validator result, model/prompt version, source/capture hash and timing. A replay, precomputed source interpretation or provider fake is labelled separately from live label inference.

**AC-05:** Store raw observations and extraction separately from user corrections. Every correction has actor/session, field, previous/new value and timestamp; it creates a new observation revision and invalidates prior result/approval eligibility. Corrections and source-extraction disagreements remain visible in evaluation reporting.

### P0-03 Bounded ADK workflow and deployed application

Use one bounded Google ADK workflow in the Python application on Cloud Run, with Firestore domain persistence. A direct SDK diagnostic is acceptable preflight; a direct-SDK-only final product does not satisfy this requirement. No second agent runtime is needed.

**AC-06:** A deployed trace proves user input → application backend → ADK/Gemini → deterministic verifier → visible result, with persisted domain state. Record the actual runtime identity and tested package/model configuration. A health endpoint or provider-only script is not the vertical slice.

**AC-07:** Enforce limits in server state: normally 2–4 model calls and at most six tool operations per evidence run, with at most two recapture runs per incident. Provider retries count toward these limits; no hidden SDK/ADK retry multiplication. Each run has a wall-clock deadline and terminal reason. Approval is a separate server endpoint, never an unconstrained model write.

### P0-04 Deterministic, scoped comparison

**AC-08:** Identity is established before lot/date matching through a trustworthy typed identifier or a reviewed combination of brand/product/variant/pack attributes. Similar wording or equal lot alone is insufficient. Preserve raw lot case and leading zeros; only reviewed normalization is permitted. Ambiguous dates/aliases route to review.

**AC-09:** Implement the predicate/result rules in sections 4–5. Test all supported operators and explicitly refuse unsupported ones. Unknown extraction is never `ALL` or `NOT_SPECIFIED`. Do not ask for a lot/date when the complete reviewed rule imposes no such restriction.

**AC-10:** Return a field-by-field evidence grid with source restriction, observed value, comparison outcome and valid evidence references. No result, badge, explanation or action implies safe consumption, sale clearance, contamination detection or worldwide completeness. Foreign positive evidence is a review signal.

### P0-05 Targeted recapture

**AC-11:** Missing required evidence produces a specific request linked to an unresolved predicate, such as the lot/date panel, with capture guidance. A useful second image can resolve a supported case; unrelated evidence does not.

**AC-12:** After two recapture requests, unresolved evidence stays `REVIEW_REQUIRED`, with an available simulated review-request action. Server counters persist across refresh, retries and corrections; no reset-by-refresh loop. A new incident is separately rate-limited. Budget exhaustion and model/source failure are explicit reasons, not a negative result.

### P0-06 Genuine source update and renewed review

**AC-13:** An authorized replay of UK original → actual update changes the incident's active source dependency, invalidates every dependent result (including old negatives), removes current approval eligibility and shows the changed geography/predicates. Previously recorded actions/events remain historical and marked as requiring renewed review.

**AC-14:** Guest replay affects only its own incident. Guests cannot publish, edit or promote the globally curated source registry. For an actual detected source change, a trusted backend records a new family epoch; every result read and action approval checks that epoch. Background marking may be lazy, but stale-result safety cannot depend on completing a background sweep.

**AC-15:** Race tests cover update before approval, update during approval, update after approval, cached result after update, and corrected observation after approval. No stale approval becomes a current action. Re-review produces a new result/action linked to prior history. Backward replay cannot resurrect approval; use a new labelled demo incident to restart the original scenario.

### P0-07 Deliberate, persistent simulated action

**AC-16:** Only an explicit user confirmation can request `SIMULATED_HOLD` for a supported matched result or `SIMULATED_REVIEW_REQUEST` for a review-required case. A negative never enables release-to-sale. Review requests preserve the uncertainty and are not holds disguised as a positive conclusion. No real stock, message, refund, disposal or regulatory system is changed.

**AC-17:** The action transaction verifies server-established session ownership and demo-manager capability, active observation/result revisions, selected source hashes/epochs, action type and a confirmation payload bound to that result. A simulated hold requires a current supported matched result and eligible source freshness/mode under NF-03. A deliberately selected, fully reviewed frozen historical demo can support a clearly dated current-as-of result and labelled simulated hold while its bound dependencies remain unchanged. A failed/expired live refresh cannot restore hold eligibility by relabelling the old result or source as historical. A simulated review request may record a current `REVIEW_REQUIRED` result caused by unavailable, unreviewed, expired or changed evidence, preserving that reason; it does not require hold eligibility. First materialize a new review-result revision if the previous result became stale. Client-supplied actor/role/result claims are untrusted. The logical action identity is unique for `(session, incident, result_revision, action_type)`, independent of repeated/new client request keys.

**AC-18:** Concurrent duplicate requests create exactly one action and one corresponding action-created event. An identical replay returns the existing action. Reusing a request key with a different payload returns conflict. A lost response is reconciled by reading the logical action before replay. Page refresh preserves the record. Model calls, external fetches and non-idempotent side effects never run inside a retriable Firestore transaction callback.

### P0-08 Isolated guest path and bounded data

**AC-19:** Issue a high-entropy server-owned guest session with a short expiry, secure HttpOnly cookie in deployment, SameSite policy and request-origin/CSRF checks for mutations. Bind every incident/observation/result/action/list/object read and write to its owner. Direct Firestore client access is denied; backend IAM and application authorization are independently tested. Do not log session tokens or place them in URLs/localStorage.

**AC-20:** Two fresh sessions cannot read, enumerate, update, approve or replay each other's records, including guessed IDs, nested resource IDs and image references. Expired/invalid sessions receive a useful denial without exposing record existence. A public guest cannot change source trust, rate limits, spend limits or retention.

**AC-21:** Use public authority evidence and freshly created, visibly labelled synthetic demo images only. Accept selected sample assets plus supported synthetic upload/capture. Enforce the limits in section 7; reject malformed/oversized/unsupported inputs before inference. No real personal, supplier, customer or inventory data is collected for P0.

### P0-09 Evaluation and source support

**AC-22:** Freeze and execute the 24 development cases D01–D24 and eight validation cases H01–H08 under the discipline in section 8. The 12 decidable development IDs are declared and human-audited before tuning. At least 10/12 resolve correctly without manually replacing the entire extraction. Preserve denominator, abstentions, disagreements and assistance.

**AC-23:** All deterministic invariants pass; every material result field has manually audited source/observation support; zero observed critical false reassurance, unauthorized writes and cross-session access in the declared suites. Report counts and scope, not a claim of zero real-world risk. Any such observed critical failure blocks release.

**AC-24:** All eight final cases execute under the frozen candidate configuration. A case is held-out only if builders have not accessed/tuned against it. An evidence custodian holds private expected answers; public Git contains categories/hashes and sanitized results, not a supposedly hidden answer key. Exposure/failure-driven tuning relabels the exposed cases as regression and requires a new genuinely held-out set for that claim. Never delete the failed run.

**AC-25:** Compare with a competent same-model, source-grounded one-shot baseline when feasible. Use equivalent initial evidence, reviewed metadata access, output schema and abstention guidance; report recapture's extra information and human effort. A missing baseline or human study is a disclosed limitation with reduced innovation/impact claims, as permitted by the brief, not an invented success. The 30% time-improvement target is not a release result.

### P0-10 Reliability, telemetry and security

**AC-26:** Timeout/429/503/source failures, invalid output and exhausted budgets produce an explicit operational reason plus useful review/retry guidance. Never show cached output as a fresh successful request. Unauthorized requests are not repeatedly retried. For transient reads/model calls, allow at most two total attempts within the run budget; inspect SDK and ADK defaults as well.

**AC-27:** Redacted evidence includes request/run/case IDs, source/observation/model/prompt/verifier versions, duration, token/call usage, result and error class. Health/readiness and provider/source status are observable without public secrets, internal account details or raw images. Estimate costs with the verified rate source and record unknown non-model costs as unknown.

**AC-28:** Before public exposure, validate authorization, upload/parser boundaries, source allowlist/redirect defenses, tool allowlists, prompt injection handling, secret/dependency/license checks, concurrency and budget controls. Bound global usage across all instances, not just one process/session. A budget alert is not an instantaneous cap.

### P0-11 Judge access and submission

**AC-29:** The original four hero flows in section 3 and F5/F6 in the retail extension pass through the deployed frontend/backend in clean browser contexts. Verify refresh/persistence, mobile capture/upload fallback, keyboard navigation and cross-session denial. No developer cookies or privileged credentials are needed by a judge. A shared prerecorded video is not deployed-path evidence.

**AC-30:** The repository, Cloud Run URL, prescribed-template English PDF, video, description and judge guide describe the same verified release. Apply the form constraints and duration conflict in [SOURCES](../docs/SOURCES.md). The public source must be event-built with dependency/asset provenance. The final submission requires owner approval and observed platform confirmation.

**AC-31:** Keep the submitted URL and dependencies usable through the published evaluation/results window. Record release tag/image digest, resource owner, retention of rollback artifacts and a critical-repair procedure. After deadline, do not silently add new judged features.

### P0-12 Retail operations console

Owner U07 requires a separate retailer-facing queue over the current synthetic guest shop's incidents. Its complete criteria **AC-32–36**, queue precedence, limits, journey F5 and tests are in [retail-operations.md](retail-operations.md). It must derive scoped counts/rows from persisted state, reopen A's evidence workbench, show renewed-review needs, and preserve the original result/action semantics. No real inventory dashboard or public technical-operations data is implied.

### P0-13 Controlled operational learning

Owner U07 requires a delivered loop with a visible effect. Its complete criteria **AC-37–43**, versioned contracts, fixed L01–L06 evaluation, activation/rollback rules and journey F6 are in [retail-operations.md](retail-operations.md). P0 supports structured feedback → evidence-linked allowlisted recapture-guidance candidate → executed pure evaluation → explicit shop-scoped activation → changed subsequent guidance → rollback. It does not train the model or change source truth, verifier decisions, extraction, permissions or budgets.

Private **BatchBeacon Operations** remains a separate IAM-protected native dashboard. [OPERATIONS OPS-01–07](../docs/OPERATIONS.md#4-approved-private-operations-dashboard) adds actual availability/alert/configuration evidence; optional external notification delivery is distinguished from required dashboard-visible policies. Neither surface is completed by planning text.

## 3. User journeys and judge-visible proof

All guest journeys operate on synthetic records in a single session. Only the curated source reader crosses into shared read-only evidence; application writes remain session-owned.

| Journey / demo | User, trigger and input | State transitions and outcome | Highest-risk failure and proof |
| --- | --- | --- | --- |
| J1 / F1 Supported match and action | Guest demo manager selects Singapore notice, uploads labelled identity and lot/date panels. | `DRAFT → EXTRACTING → RESULT_AVAILABLE → ACTION_RECORDED`; result class is matched, confirmation eligibility is separate, evidence grid precedes confirmation; refresh retains action. | Duplicate/stale approval, extraction disagreement and source outage deny action or route to review. Show actual Gemini trace and exactly one persistent action. |
| J2 / F2 Same lot, different product | Worker checks a fully identified synthetic third product bearing the same lot. | `RESULT_AVAILABLE` with a scoped not-listed verdict; coverage/date/limitations remain visible. No release button. | Both SFA products A and B are affected: B is **not** a negative fixture. Incomplete identity or another unresolved candidate becomes review. Show identity row that prevents lot-only matching. |
| J3 / F3 Missing evidence recovery | Worker provides identity but unreadable required lot. | `EXTRACTING → NEEDS_EVIDENCE → EXTRACTING → RESULT_AVAILABLE`, with matched or review-required verdict; unresolved evidence after the second request remains review. | Refresh, unrelated upload, ambiguous date and exhausted budget cannot bypass counters. Show a specific panel request, its new evidence and an exhausted case. |
| J4 / F4 Update and renewed review | Judge starts a labelled historical UK case, then selects its genuine newer notice. | Earlier result/action becomes historical; active result is stale/review-required; re-evaluation against the new scope produces a new result; manager reconfirms if eligible. | Wales/Scotland update, old negatives, pending approval and cached results all invalidate; other sessions are untouched. Show before/after source versions and linked history. |

Add J5/F5 (owned retail review queue) and J6/F6 (controlled guidance improvement) exactly as specified in [the extension](retail-operations.md). Preserve F1–F4 as the core recall story.

For each journey, the UI must provide loading, empty, success, uncertainty, invalid input, unavailable AI/source, stale/cached/historical, permission-denied and safe-retry states. Corrections preserve raw observations. The audit drawer and technical proof remain secondary to the evidence and next human action.

For F4, prefer a reviewed Scotland or Wales scenario: the original source's out-of-scope evidence yields `REVIEW_REQUIRED`, and the genuine update can support a match. Never script the old out-of-scope state as reassuring clearance. Separately test invalidation of an actual historical negative using a fully decidable excluded product in the old eligible scope.

## 4. Result and predicate rules

### Result vocabulary

| Internal result | Meaning and permitted action |
| --- | --- |
| `MATCHED_HOLD_FOR_REVIEW` | Evidence matches the restrictions in the checked notice; offer deliberate simulated hold. No contamination/lab conclusion. |
| `NOT_LISTED_IN_CHECKED_NOTICES` | Complete checked evidence excludes this verified identity under stated restrictions; display exact coverage. No safe-to-eat, sale, worldwide or regulatory clearance. |
| `REVIEW_REQUIRED` | Missing/uncertain/conflicting/out-of-scope/stale/unavailable evidence; targeted recapture if possible, otherwise simulated review request. |

Reason codes include `IDENTITY_UNCERTAIN`, `PREDICATE_UNKNOWN`, `DATE_AMBIGUOUS`, `OUT_OF_SCOPE`, `SOURCE_UNREVIEWED`, `SOURCE_UNAVAILABLE`, `SOURCE_VERSION_CHANGED`, `FRESHNESS_EXPIRED`, `MODEL_UNAVAILABLE`, `BUDGET_EXHAUSTED`, `RECAPTURE_EXHAUSTED`, `OBSERVATION_CHANGED`. A transport error is not a fourth successful verdict.

### Predicate operators

| Operator | Required semantics |
| --- | --- |
| `EXACT` | Compare typed values under the reviewed normalization policy; lot text remains exact by default. |
| `SET` | Match one explicitly listed reviewed value, retaining which member supported the result. |
| `RANGE` | Only an explicitly supported typed range with declared inclusive/exclusive bounds and unambiguous dates/units; otherwise review. Do not implement speculative natural-language ranges just to fill the enum. |
| `ALL` | Explicit unrestricted scope stated by the fully reviewed authority record. |
| `NOT_SPECIFIED` | Full source review confirms that this field imposes no restriction. It does not establish the observed value or product identity. |
| `UNKNOWN` | Missing, ambiguous, incomplete or unsupported interpretation. It cannot match as a wildcard or support a negative. |

Comparison outcomes: `MATCH`, `MISMATCH`, `UNKNOWN`, `NOT_APPLICABLE`. Not-applicable is distinct from a mismatch and requires an applicability reason.

### Aggregation order

1. Validate identity, jurisdiction, source completeness/trust, source mode/freshness and version dependencies. A global blocker routes to review. No selected/eligible checked coverage cannot produce a negative.
2. Evaluate applicable product records independently. A supported fully matching eligible record supports a matched result when global gates pass.
3. A negative requires complete verified identity and supported exclusion across all relevant checked candidates, without unresolved candidate evidence or an out-of-scope positive signal. One mismatching candidate cannot hide another unknown candidate.
4. Otherwise return review, specifying the unresolved predicate or scope. Test aggregation explicitly rather than comparing only the first matching row.

## 5. Domain contracts and consistency

Use versioned JSON/Pydantic contracts owned by the integrator. Generate boundary schemas if useful; do not introduce a second spec framework. Proposed code location is `src/batchbeacon/contracts.py`; creation and exact paths are [implementation tasks](tasks.md), not existing artifacts.

| Record | Required fields / invariant |
| --- | --- |
| `AuthorityNotice` | Notice family/version/hash, authority, country/subnational scope, original/final URL, dates, retrieval/mode/status; immutable evidence content; trusted interpretation-review revision separate from inference. |
| `AffectedProductRule` | Notice-version parent, raw name, reviewed identity attributes, typed identifiers, predicates, applicability, source locators; unknown cannot inherit a wildcard. |
| `ProductObservation` | Session/incident, observation revision, capture hash/reference, raw/extracted values and field locations, model/prompt IDs; correction records separate. |
| `VerificationResult` | Immutable result revision, observation revision, complete checked-source dependency set/epochs, per-record/predicate outcomes, result/reasons, evidence references, outstanding evidence, verifier version, computed time/cache provenance. |
| `ActionRecord` | Logical action ID, result/source/observation revisions, server actor/session, explicit confirmation time, request key/payload hash, simulation=true, prior-action link when re-reviewed. |
| `IncidentEvent` | Server-created sequence/event ID, event type/time, relevant revision references, source mode and redacted reason. Append-only application history; no claim of legal tamper-proofing. |

Separate incident progress from verdict: `DRAFT`, `EXTRACTING`, `NEEDS_EVIDENCE`, `RESULT_AVAILABLE`, `ACTION_RECORDED`, `STALE_REVIEW`, `FAILED_REVIEW`. Old records remain immutable; a server-derived currentness overlay indicates staleness. A historical demo snapshot is a valid **as-of demonstration**, distinct from a dependency that changed after verification.

Approval reads/writes and active-version changes use Firestore transaction semantics. The source epoch and incident/observation/result revisions participate in concurrency checks. Record and reconcile unknown write outcomes; do not infer failure from a timeout. Never call Gemini within the transaction callback.

## 6. Grounding and AI boundaries

P0 uses metadata/lexical source selection and bounded whole-notice context for the tiny supported corpus. No embeddings/index, hybrid search, reranker or GraphRAG is required. Describe actual source-grounded retrieval accurately; static manifest lookup alone is not advanced RAG. Citations identify the immutable notice version and material section/short evidence span; capture references identify the image hash and field location. Verify references and substantive support.

AI proposes extraction and supported explanations/recapture wording. Backend owns trust/completeness, result aggregation, permissions, mutation, budgets and termination. The ADK workflow has allowlisted source-read/extract/verify/recapture/explain tools; no arbitrary HTTP, shell, database mutation or messaging tool. Treat source/photo/tool text as untrusted data.

The delivered P0-13 operational learning loop changes only an allowlisted, versioned shop-scoped recapture-guidance presentation policy, after actual evaluation and explicit confirmation. Its effect and rollback must be demonstrated. Logging feedback alone cannot pass. Global model/prompt/verifier/source changes remain controlled releases with affected real-model evaluation and independent review. Feedback is untrusted and never becomes a gold label or an accuracy numerator. Optional challenger `gemini-4-argon` is P1 only after verified access and a fair comparison; it cannot consume the held-out set during selection.

## 7. Necessary non-functional requirements

These are proposed prototype limits, not regulatory thresholds or measured production SLOs. The integrator may tighten them; material changes require a decision entry and affected verification.

| ID | Initial requirement / verification |
| --- | --- |
| NF-01 Upload boundary | JPEG/PNG/WebP only; at most two images per request, 5 MiB each, 20 megapixels per image and 24 megapixels combined; inspect decoded type/dimensions and memory bounds, strip EXIF, reject malformed data before model use. No SVG, archives, arbitrary remote images or user PDF source ingestion. Camera failure has a file-upload fallback. |
| NF-02 Session/data retention | Proposed guest expiry 8 hours, enforced immediately on every access. Retain the sanitized image bytes actually supplied to Gemini in private Cloud Storage for the short review window, with a source/capture hash and server-authorized reference; discard unnecessary raw upload/EXIF. This bounded use of the brief's optional storage is selected because a hash alone cannot support visual evidence review after refresh. Require storage authority/private access and target removal of live image objects after 24 hours; expiry denies access immediately. Record actual lifecycle delay and soft-delete retention, which can keep deleted objects for seven further days under default policy. Do not claim guaranteed physical deletion at 24 hours or weaken an existing bucket by assumption. Firestore TTL is delayed/billable and does not remove subcollections automatically; expire/clean child records explicitly, including feedback/candidate/evaluation/activation records. See [OPERATIONS retention](../docs/OPERATIONS.md#3-image-and-record-retention-correction) for primary sources and verification. Evaluation fixtures and their exact model-input images stay with the evidence custodian under approved retention; public synthetic fixtures require rights/provenance. Memory-only local fallback is labelled and cannot pass retained-image audit/refresh gates. Do not persist faces/personal/business data for P0. |
| NF-03 Freshness | Historical curated snapshots are default and always dated. Deliberate selection of a fully reviewed frozen historical demo establishes a server-recorded as-of demonstration context, bound to source hashes/epochs and observation/result revisions. A supported match may enable only a clearly labelled simulated hold; it makes no live-recall or sale-clearance claim. `LIVE_REFRESHED` source status requires successful allowlisted fetch and interpretation revalidation, with proposed freshness expiry 24 hours after successful fetch. A changed hash immediately blocks current decisions until reviewed. An expired/failed live refresh leaves retained evidence viewable as historical but the active result review-required and hold-ineligible; changing a label or mode field cannot remove that failure. Restoring live eligibility requires successful revalidation and a new current result. An intentional switch to a historical demo uses a separately rate-limited new demo incident and new result, retaining the failed live incident/history and never resetting its allowances. Source-epoch or observation changes invalidate dependent results in either mode. This interval is an engineering policy, not assurance that no newer recall exists. Continuous recall ingestion/monitoring is excluded; the approved service-availability monitoring remains required. |
| NF-04 Resource limits | At most four model calls/six tools per evidence-acquisition run; initial run plus at most two recapture runs per incident, with a lifetime recapture counter that never resets on correction/update. Source-update or user-correction verification reuses retained typed observations deterministically and can proceed after those three runs, within a separate proposed six-verifications-per-incident limit. Source/observation invalidation and access/currentness checks always run even after this verification allowance is exhausted; quota exhaustion cannot preserve a stale approval. If new AI extraction is necessary after that acquisition budget, leave review-required or start a separately rate-limited new incident; never silently reset counters. Proposed 30-second run deadline and one active run/session; start with two Cloud Run instances and bounded per-instance concurrency after actual verification. Add persistent global quota reservation and a separate demo reserve within the owner-approved budget. Missing cost state closes model admission; in-flight/cloud costs remain possible. |
| NF-05 Timing | Target warm normal-run p95 <15 s, recapture <10 s, visible local progress within 1 s. Report actual warm p50/p95, sample count and cold starts separately. Record miss as a product limitation, not a fabricated pass; unusable timeout/error behavior blocks the journey. |
| NF-06 Access/usability | Keyboard-complete flow; semantic labels, visible focus, announced status/errors, non-color-only outcomes, readable contrast, reduced-motion handling and a usable 390 px-wide capture layout. No horizontal loss of crucial identifiers at 200% zoom. Automated plus manual evidence, without a certification claim. |
| NF-07 Security | Same-origin UI/API by default; strict input/output schemas and ownership checks; fixed source URL/path allowlist, HTTPS, redirect revalidation and private-network denial. Least-privilege runtime/build/deploy identities; secrets through secure supported mechanisms. Secret scans cover code/history and exported media, not only current source. |
| NF-08 Build/release | Locked/reproducible local build; explicit check discovery for UI/backend; deterministic checks separated from controlled real-service/model checks; known source/image digest deploy; clean-session judge verification and rollback compatibility. A skipped check is not green evidence. |

## 8. Tests, evaluations and evidence registry

Test IDs below are planned obligations, not tests already created. Exact executable paths/commands are created and recorded during M1–M3; link their run IDs back here and to tasks.

| Test family | Derivation and coverage | Requirements |
| --- | --- | --- |
| UT-IDENTITY | Typed codes, exact lot/case/leading zero, reviewed aliases, pack/variant identity, same-lot third product | P0-04 AC-08–10 |
| UT-PREDICATES | Operator truth tables, ambiguity, complete vs unknown source, all-candidate aggregation | P0-01/04 |
| UT-STATE | Recapture counters, corrections, source epochs/currentness, cache key dependency changes; deliberate historical as-of eligibility versus failed-live-refresh downgrade denial | P0-05/06/07 |
| IT-CONTRACT | API input/output/evidence-reference validation, bounded tool arguments, model failure mapping | P0-02/03/10 |
| IT-ACTION | Duplicate/concurrent/idempotency conflict/lost-response reconciliation; version race and history; dated historical-demo hold succeeds when eligible, while expired/failed live evidence cannot regain hold by relabelling | P0-06/07 |
| IT-ISOLATION | Two sessions; GET/list/nested-object/approval/replay denial; expiry and CSRF; global-source mutation denial | P0-08 |
| IT-BOUNDARY | Upload/context/source-fetch limits, prompt injection, redirects/private network, budgets and retries | P0-03/08/10 |
| RT-FIRESTORE | Actual deployed runtime identity, database read/write/transactions, restart persistence, races and isolation in synthetic namespace | P0-03/06/07/08 |
| EV-DEV | D01–D24 through real model; deterministic controls also run independently | P0-02/04/05/06/09/10 |
| EV-FINAL | H01–H08 under frozen release with private custody; failures retained | P0-09 |
| EV-BASELINE | Competent same-model comparison; human timing if feasible, assistance/cost reporting | P0-09 AC-25 |
| B-F1–B-F6 | Real-server then hosted browser journeys; persistence, denied access, actual frontend/backend, queue and full guidance loop | P0-01–13 |
| UT-RETAIL / IT-RETAIL | Queue precedence, owned counts/rows/filter/detail, limits, no inference on refresh, currentness/expiry and denied cross-shop access | P0-12 AC-32–36 |
| EV-LEARN | Actual fixed L01–L06 guidance checks with baseline/candidate/suite hashes and failures; no H answers or paid model call | P0-13 AC-39 |
| IT-LEARN | Evidence-linked feedback, allowed candidate, failed/stale/mismatched evaluation denial, explicit activation, duplicate/unknown outcome, future effect and rollback | P0-13 AC-37–43 |
| OPS-CHECK | Private access, populated success/failure, cheap uptime, dashboard-visible alert incident, budget/retention and private-run-record evidence; optional notification delivery separately labelled | P0-10, OPS-01–07 |
| B-A11Y | Keyboard/mobile/focus/error/status/contrast/zoom/reduced-motion checks | P0-11 / NF-06 |
| SEC-RELEASE | Secret/license/dependency/authorization boundary review and safe privileged-CI handling | P0-08/10/11 |
| REL-GATES | Deliberate failed check in isolated fixture turns CI red, then green after fix; exact candidate artifact/access checks | P0-11 / NF-08 |

Development cases preserve the brief exactly by category: D01–06 supported positives/unrestricted date/recapture; D07–12 identity/predicate near misses; D13–18 ambiguity, missing fields and exhausted recapture; D19–24 genuine update, unknown-vs-wildcard, injection, outage, duplicate approval and cross-session attack. Freeze D01–D12 as the 12 decidable cases only after human confirmation; never move a failed case out post hoc. D07 uses a third synthetic wrong identity, since both SFA A/B cases are positive.

H01–H08 categories: two unseen-layout positives; two hard identity/predicate negatives; two ambiguous captures; one source dependency; one adversarial/error case. This handoff intentionally supplies no hidden answers. Report final outcomes, extraction fidelity/support, actual disposition, critical failures, recapture, correction, latency and cost; do not grade exact explanatory wording. One lightweight pytest-backed evaluation harness plus optional compatible ADK metrics is sufficient; no stacked RAGAS/DeepEval/promptfoo dependency.

Each evidence record includes command, UTC time, source commit or tree digest, environment, case IDs/denominator, model/prompt/verifier/dataset/source versions, result (`PASS`, `FAIL`, `NOT RUN`, `BLOCKED`, `NOT APPLICABLE` with reason), failures, assistance and artifact path. Distinguish unit, fake/emulator, real service, real model, real browser and hosted judge evidence. Never add overlapping snapshots into a total.

## 9. P1, P2 and exclusions

| Priority | Scope and admission |
| --- | --- |
| P1 | Verified linked multinational incident; second tested language; GS1/barcode only with supported identifier equivalence; evidence/action export; stronger-model comparison; extra prompt screening; charts of actual measurements. Admit only after all P0 gates pass and the packaging reserve is protected. |
| P2 | Continuous recall ingestion; authority-specific legal/operational adapters; validated entity resolution; justified vector/hybrid/graph retrieval; private ERP/POS/supplier integrations; real retailer notifications; production identity/regional privacy; expanded observability; broader model/preference learning and commercial operations. The bounded private dashboard, synthetic retail console and P0-13 guidance loop are current P0, not deferred here. |

Excluded: medical/infant-feeding advice; contamination detection from a photo; safe-to-eat/sale clearance; autonomous stock release/disposal/refunds/messages; regulatory certification; worldwide completeness; arbitrary web ingestion; new model training; production customer/identity records; fabricated product-proof images; multiple agent frameworks or runtime swarm; Kubernetes/Temporal/platform buildout. Fresh visibly simulated label fixtures are permitted and must not masquerade as real product evidence.

The unfinished **StackClimb Work Package Protocol** and **Multi-Work-Package Orchestration** are explicitly excluded as operational dependencies. FormBridge remains only a historical contingency in the original brief, requiring a new explicit owner-approved product decision; no task in this plan builds or pivots to it.

## Owner update: design and operations scope

U01 approves 160-second core and 230-second submission videos. U02 accepts A's workbench structure in principle and rejects the previous visual finish. Final visual approval covers the replacement high-fidelity workbench/retail-console set; actual running-UI checks follow. All three original directions remain selection evidence. See [OWNER_DECISIONS](../docs/OWNER_DECISIONS.md).

U07 adds P0-12/13 and OPS-01–07. U09–U12 grant the bounded cloud/budget/public/repository execution scope; their verification gates remain. This extension is material schedule risk on one machine. Reforecast from the actual integrated slice; do not quietly demote it to P1 or shrink the original 24-development/eight-final evaluation obligations. A missed mandatory gate stays NOT READY unless the owner explicitly changes scope.


# BatchBeacon AI: retailer console and controlled operational learning

**Status: planning specification. Application implementation: NOT IMPLEMENTED. Every test, evaluation, hosted journey and promotion demonstration: NOT RUN.** Proposed record names, routes and evidence paths below are future implementation obligations, not existing capabilities.

This owner-requested extension adds **P0-12** and **P0-13** while preserving every P0-01–11 requirement in [mvp.md](mvp.md). BatchBeacon AI remains a recall-evidence verification product. Read the approved originals, [execution plan](../docs/EXECUTION.md), [owner decisions](../docs/OWNER_DECISIONS.md), [operations plan](../docs/OPERATIONS.md) and [UI direction record](../docs/UI_DIRECTIONS.md).

Reuse the owner's existing scoped grants **U07 and U09–U12** as recorded in OWNER_DECISIONS; do not request the same scope permission again or infer broader authority. Exact spending, resources, exposure and notification scope comes from those grants. The integrator records them from the owner instruction before execution. This specification neither provisions anything nor supplies missing machine/account facts.

## 1. Scope and product boundaries

**Recorded working assumption:** customer means a retailer using BatchBeacon. P0 represents that retailer as one visibly synthetic demo shop mapped one-to-one to the existing server-issued guest session. The existing demo-manager capability permits only that session's simulated actions and the bounded guidance-policy choices below. It does not authenticate a real manager or create a production retailer account.

There are two distinct surfaces:

| Surface | Audience and permitted content |
| --- | --- |
| Retailer console | Current demo shop's checks, missing evidence, renewed review, simulated actions, structured feedback and its scoped improvement candidates. Reuses the A evidence workbench for the actual check and decision. |
| Private BatchBeacon Operations dashboard | Authorized operator's availability, runtime, source/model failures, cost/circuit state and technical evidence. It is governed by OPERATIONS; guest access to global logs, metrics, budgets and operator controls is denied. |

One FastAPI application and the existing Firestore/session boundaries suffice. Do not add an analytics database, identity platform, model-training service, job-orchestration system or second backend for this extension. A's workflow is accepted in principle; the old visual treatment is rejected. One replacement high-fidelity approval set covers the workbench and retailer console together. Independent backend/environment work continues while that visual approval is pending.

This extension includes a delivered deterministic **operational guidance improvement loop**. It changes a fixed recapture-guidance policy for the current synthetic shop after evidence review, actual fixture evaluation and explicit approval. It does not change Gemini extraction, model prompts, source trust, predicates, verdicts, permissions, budgets or real business actions. Feedback is neither source truth nor a model-accuracy label.

## 2. P0-12: retailer console for the current demo shop

Provide one bounded queue over persisted checks. Selecting a row opens its A workbench and the exact evidence/history. The console's aggregates are derived views of domain state, not a second source of truth.

### AC-32: scope and access

The console and every list, count, filter, nested-detail and feedback/improvement endpoint derive ownership from the server-established guest session. Client-supplied shop, actor or role IDs cannot establish authority. A clean guest can reach its own console, start a check and reopen an owned check. The UI identifies the synthetic shop, session scope and expiry; it makes no claim of a real authenticated retailer workspace.

### AC-33: meaningful, consistent summaries

Counts and rows derive from the same bounded server snapshot of persisted incidents. Each row identifies the incident/product, checked authority/jurisdiction, source mode/version, currentness, current result/reason, outstanding evidence and latest relevant simulated action. Include the snapshot observation time. A count is a workflow count, never model accuracy, safe products, actual stock units, money saved or products physically held. Distinguish empty, loading, unavailable and expired states. Counts for the six categories below reconcile to the included incident total.

### AC-34: review navigation and currentness

Opening a row preserves its incident/evidence identity and enters the A workbench. Source updates and observation corrections alter the derived currentness and queue category on the next read/refreshed snapshot. Historical actions remain inspectable but cannot make an invalidated row appear currently approved. Every consequential incident action still uses the existing result-bound server authorization/confirmation endpoints. No bulk approvals, inline stock mutation or release-to-sale action is added.

### AC-35: isolated, bounded aggregation

Two sessions cannot read, enumerate or infer each other's incident count, product name, action, feedback, candidate, evaluation or policy state, including through filters, guessed IDs and errors. Enforce the limits in section 7. Read at most 20 incident summary rows per response; load evidence/history lazily. Counts may cover the current bounded shop snapshot, or an explicitly labelled page if a compatible existing workspace requires pagination; never silently label truncated counts as a full-shop total. Console refresh performs no Gemini call, source fetch, action creation or policy activation.

### AC-36: availability and evidence honesty

Any retailer-facing service status is a limited, timestamped capability statement derived from actual observations, such as new verification being unavailable while saved evidence can still be opened. Missing or stale observations are unknown. An HTTP/landing-page success is not a successful Gemini journey. Distinguish an available service showing historical recall evidence from unavailable inference, exhausted allowance and stale source evidence. Public views exclude global technical metrics, budgets, project/account IDs, internal operator links and the owner's personal schedule.

### Queue-category precedence

These are navigation categories, not new verifier verdicts. Apply the following rules in order to the server-derived current state:

| Order | Category | Rule |
| --- | --- | --- |
| 1 | Needs renewed review | A dependency changed or current result is otherwise stale. This takes precedence over any old recorded action. |
| 2 | Simulated action recorded | A current, eligible action record is bound to the current result. Show its actual type. A simulated review request also states that the underlying uncertainty is unresolved. |
| 3 | In progress | An active acquisition run, or a draft with no completed current result, is in progress. Retained prior evidence is labelled as such. |
| 4 | Needs evidence | A current missing-evidence request can still be acted on within the existing recapture and resource limits. |
| 5 | Needs human review | Other current review-required cases, failed/unavailable/exhausted cases, or a matched case awaiting confirmation. |
| 6 | Not listed in checked notices | A complete current scoped negative under the existing verifier rules. Preserve checked coverage and limitations. |

An unrecognized or inconsistent state falls back to Needs human review with a diagnostic reason; it cannot become a negative or recorded-action state. A current simulated review request must never be labelled resolved. A source/currentness read is required before assigning a currently approved category; a delayed background sweep is insufficient. Keep every action endpoint's independent currentness check even when the console is stale.

Default presentation is a compact category/count strip plus a readable queue, ordered by last material update with a stable tie-breaker. Do not invent a medical severity score or AI urgency ranking. A query failure retains an explicit unavailable/stale snapshot state rather than silently substituting zero incidents.

## 3. P0-13: evidence-grounded operational learning

Deliver the complete persisted path: structured feedback → evidence-linked candidate → fixed offline evaluation → explicit shop-scoped activation → changed future guidance → rollback. One supported candidate family is sufficient for P0.

### AC-37: evidence-linked structured feedback

The user can record feedback against an owned observation/result/recapture revision. Store the server scope/actor, selected category/detail code, timestamp and exact source/result/observation/recapture references. **Structured choices only; no free-text feedback, attachment or arbitrary URL.** Preserve the original record and disposition history. Feedback cannot replace extraction, approve a source manifest, become gold truth or change a verdict. Existing field corrections continue through AC-05 and invalidate result/approval eligibility normally.

### AC-38: bounded candidate creation

A versioned deterministic rule may select a fixed allowlisted recapture-guidance variant when supported feedback and the linked evidence identify an applicable missing-field problem. Retain diagnosis, supporting feedback/evidence references, rule version, base guidance policy and proposed policy ID/hash. Limit support references to five owned feedback records per candidate. Unsupported feedback remains recorded as NO_SAFE_CANDIDATE or pending human investigation; the service does not invent a fix. Public requests cannot supply prompt text, executable content, source predicates or arbitrary policy values.

### AC-39: actual predeclared offline evaluation

Execute the fixed six-case L01–L06 suite in section 6 with both baseline and candidate policies. Record suite/fixture/evaluator versions and hashes, baseline/candidate hashes, base activation revision, actual case outputs, failures, timestamps and terminal status. A client-supplied pass flag is never authoritative. Evaluation uses pure bounded functions and fixed reviewed synthetic fixtures; it invokes no Gemini, arbitrary shell/code, uploaded tests, live source fetch or dynamic file path. The suite and acceptance rules are declared before candidate evaluation and are separate from D01–D24 and H01–H08.

### AC-40: explicit, version-bound activation

Activation requires the session's server-issued demo-manager capability and explicit confirmation showing the before/after guidance, supporting evidence, actual evaluation and scope. The server checks candidate ID/hash, evaluation ID/hash and passing status, suite version, base policy ID/hash, expected monotonic activation revision and current owned evidence-basis revisions. If the relevant source epoch, observation, result, candidate, suite or base policy changed, the old approval/evaluation binding cannot authorize activation. A new candidate or evaluation must be prepared as applicable. No global policy or other shop is changed.

### AC-41: visible effect and monotonic rollback

At least one subsequent eligible recapture request uses the activated guidance and records its policy ID/hash and activation revision. Prior evidence, requests, results, actions and instructions remain immutable. Rollback is a deliberate confirmed transition to the prior allowlisted policy content, bound to the expected current activation revision and the referenced activation record. **Every accepted activation or rollback increments activation_revision; rollback never rewinds it.** Old activation confirmations cannot be replayed after rollback. Neither operation resets recapture/run/verification limits, spends model allowance, changes observation values, revives stale approval or alters source/verdict/permission rules.

### AC-42: truthful learning status and counts

The retailer sees its recorded feedback, candidate dispositions, executed evaluation results and activation/rollback history. Count only actual records with their status and observation time. Feedback volume is not an accuracy denominator; a fixture pass establishes only the declared checks. Describe this as operational guidance improvement or a controlled improvement loop. Do not claim model self-training, improved accuracy, faster work or reduced business loss without the appropriate measured evidence. Keep operator-global learning summaries private.

### AC-43: complete deployed proof and failure behavior

Demonstrate one persisted feedback → candidate → evaluation → approval → future changed guidance → rollback path in the deployed synthetic environment. Refresh retains its records. Verify cross-session denial, failed evaluation, mismatched hashes, stale source/observation/base-policy races, duplicate activation, uncertain-write reconciliation and stale rollback denial. A feedback form, static candidate screenshot or roadmap paragraph alone does not satisfy P0-13. All required demonstration and test statuses remain NOT RUN until executed.

### Supported policy family and honest example

Use fixed, reviewed variants such as GUIDANCE_V1 and GUIDANCE_V2 for recapture presentation. These identifiers are proposals to materialize and version in the real workspace. Both variants must already satisfy P0-05; never weaken the baseline to manufacture improvement. Policy text can only render a valid backend-generated missing-evidence request. It cannot choose required fields or initiate a capture/model call.

An applicable feedback choice might say the lot-code guidance was unclear. Its recapture record must actually show a required unresolved lot field. A candidate may add a short hint about finding the printed LOT/Batch code, showing the complete code with leading zeros and avoiding glare. Required date guidance appears only when the current verifier requires that field. No lot/date request is invented for an ALL or NOT_SPECIFIED restriction. An identity problem continues to require identity evidence first.

The evaluation checks field relevance, the intended hint, length/format constraints and unchanged domain invariants. If both variants pass, report that accurately; do not manufacture an uplift score. Human approval may select the clearer variant while user-benefit claims remain unverified. Feedback disputing extraction or source scope follows the existing correction/custodian process; it cannot automatically select a new extraction or verifier policy.

The future changed-guidance proof uses a genuinely eligible later request or a separately rate-limited new incident. Do not reset an exhausted incident. All displayed demo states must come from actual stored state or carry explicit seed/replay labels.

## 4. Contracts, transitions and consistency

Use the existing integrator-owned JSON/Pydantic contracts and Firestore persistence. Proposed additions are minimal; adapt their code paths to the actual compatible workspace instead of introducing another specification framework.

| Record | Required fields and invariants |
| --- | --- |
| RetailSnapshot | Server scope, generated_at, bounded incident summaries, source-epoch/currentness basis, row/category counts and snapshot ID/hash. Counts and rows share that basis. Prefer bounded summary reads over loading every evidence/action child. |
| FeedbackRecord | ID, server session/shop/actor, incident and exact source/result/observation/recapture references, category/detail enums, time, disposition and expiry. No free text or credential-bearing identifiers. |
| ImprovementCandidate | ID, scope, fixed candidate type, rule version, bounded supporting feedback/evidence references, base policy ID/hash and activation revision, proposed allowlisted policy ID/hash, diagnosis code, status and expiry. Candidate content is immutable. |
| CandidateEvaluation | Server-issued attempt ID and monotonic attempt number, scope, initiating request key/payload hash, candidate/base hashes, expected activation revision, evidence-basis hashes, suite/input/evaluator versions, six paired case outputs/outcomes, start/end time, terminal status and expiry. A stored status has supporting execution evidence. |
| GuidancePolicyState | Scope, active allowlisted policy ID/hash, monotonic activation_revision, last transition ID and expiry. Start from the release's declared baseline. It never points to a customer-supplied template. |
| GuidanceTransition | ID, scope, activation or rollback, previous/new policy IDs/hashes, expected/resulting activation revisions, candidate/evaluation references where applicable, server actor, explicit confirmation time, logical identity and payload hash, rollback reference and expiry. |

Candidate progression is RECORDED → TRIAGED → CANDIDATE_READY → EVALUATED_PASS or EVALUATED_FAIL → APPLIED_DEMO → ROLLED_BACK, with explicit NO_SAFE_CANDIDATE, STALE_BASIS and denied/error dispositions when applicable. These are proposed application states, not evidence that a transition has already run.

Evaluate outside the activation transaction. Activation atomically checks the authoritative candidate/evaluation/base/evidence state, then changes only the scoped guidance pointer, increments its revision and creates exactly one corresponding transition/event. Rollback atomically checks the current revision and referenced activation before creating a new higher revision. No model call, source fetch or non-idempotent external operation belongs in a retriable transaction callback.

A fixed-suite evaluation has a server-owned lease with a proposed 30-second absolute deadline and unique attempt identity. **A transport retry and a deliberate new evaluation are different operations.** The server atomically reserves one lifetime slot and assigns the attempt ID/number for an accepted explicit start request. Retries carrying that attempt ID or its original initiating request key return the same in-progress/terminal report without another reservation; the same key with a different payload conflicts. If the start response is lost, reconcile using its original key before deciding whether a new attempt exists. A network retry must never silently become a new start.

If the worker is interrupted, expire an abandoned RUNNING attempt to FAILED/EXPIRED, release only the active-evaluation slot, and retain its consumed lifetime allowance and failure evidence. Late completion must compare the lease identity/status and cannot overwrite an expired/terminal report. After a terminal attempt, an explicit user request for a new evaluation may use unchanged candidate/suite/base/evidence inputs; it receives a new server-issued attempt ID/number and consumes another available lifetime slot. Preserve all prior attempts, including failures, and bind activation to the exact selected passing attempt ID/hash. Reject a new start while an attempt is active or the four-attempt lifetime cap is exhausted. Cover lost-start-response reconciliation, same-attempt retries, explicit new attempts with unchanged inputs, interruption, timeout, late completion and lifetime-cap preservation in IT-LEARN.

Define logical transition uniqueness using scope, transition type, candidate/evaluation or rollback reference, expected activation revision and target policy. Identical retries, including a different transport request key, return the existing transition. Reusing a key with different content conflicts. Reconcile a lost response by reading the logical transition before retrying. After a rollback, the changed activation revision prevents resurrection through an old activation payload even if the policy content equals an earlier version.

Source/currentness and feedback-policy state remain separate. Future guidance always consumes current backend-required fields and the existing remaining allowances. An activated wording policy cannot keep an earlier source result current. No guest write can alter the shared curated source registry or promote a model/verifier release.

## 5. User journeys and demo evidence

Preserve F1–F4. Add F5 and F6 to the existing real-server and hosted browser verification rather than creating another test pipeline.

| Journey | Sequence | Highest-risk failure and evidence |
| --- | --- | --- |
| J5 / F5 Retail review queue | Return to the owned console; inspect/filter persisted checks; open a row in A; perform an existing permitted review action; return after a genuine source update. | Snapshot counts match owned rows. The update moves the affected incident to renewed review while preserving historical action evidence. A second session has independent counts and cannot access the row. |
| J6 / F6 Controlled improvement | Record applicable structured feedback; inspect an evidence-linked candidate; execute L01–L06; review/confirm activation; observe subsequent eligible guidance at its new version; confirm rollback. | The real stored chain survives refresh. Failed/stale evaluation and cross-session activation are denied. Changed guidance is visible and versioned. Core verdicts, source truth, permissions and lifetime counters are unchanged. |

Reuse owned incidents generated by F1–F4 where useful. Convenience seed data must be visibly synthetic/replay data and create actual persisted records; it cannot substitute for required real Gemini evidence. A public guide must never imply that a prerecorded or seeded state was freshly inferred.

Preserve the owner-approved 160-second core and 230-second submission cut; no repeat duration approval is needed. Keep the core recall story in the first 160 seconds. A proposed remaining allocation is 160–180 seconds console, 180–210 controlled-loop evidence, 210–225 private operations/availability and measured release proof, 225–230 links/limits. These are storyboard allocations, not measured exports. Bind actual media and guide claims to the frozen candidate and demonstrated F5/F6 records.

## 6. Fixed offline suite and test obligations

**Every test and evaluation in this section: NOT RUN.** Materialize the suite and independent expected outcomes before candidate implementation/evaluation. A separate reviewer or accurately labelled role-based pass derives expectations from requirements and reviewed development fixtures. Do not write expectations by copying candidate output.

| Case | Fixture condition | Required invariant and guidance check |
| --- | --- | --- |
| L01 | Required lot unresolved; reviewed source imposes no date restriction | Request the required lot only; the selected candidate supplies its declared full-code/leading-zero hint. No invented date request or changed verdict/action eligibility. |
| L02 | A required date marking is ambiguous | Preserve ambiguity; request the complete relevant marking using the supported guidance. No assumed date normalization or invented match. |
| L03 | Reviewed ALL/NOT_SPECIFIED field imposes no additional restriction | No new recapture request for that field. A presentation policy cannot turn a non-required field into required evidence. |
| L04 | Product identity remains unresolved | Preserve identity-first recovery. Lot agreement or a guidance variant cannot bypass identity. |
| L05 | Recapture or acquisition budget is exhausted | No additional acquisition or counter reset. Preserve review-required state and the supported simulated review-request path. |
| L06 | Source or observation changed after a result/confirmation | Preserve renewed review and stale-action denial; a stale candidate/evaluation/base confirmation cannot activate. Reverting policy content never rewinds activation revision. |

The fixed suite has **six paired cases**, evaluated for baseline and candidate; do not present the paired outputs as twelve independent scenarios. Predeclare required invariant checks and the target guidance check. Passing requires all six declared cases and every critical invariant to pass. Preserve failed outputs. Evaluation reports identify what was and was not measured, with no fabricated user-benefit score.

The existing **24 development + eight final cases remain a separate core evaluation set**. Do not add L01–L06 or feedback records to its denominator. Preserve the 10/12 decidable development gate and H01–H08 custody. The learning evaluator never reads private H inputs/answers. A candidate affecting extraction, model prompts, verifier rules or source interpretation is outside this loop and requires a separately controlled release and affected core evaluation.

| Test family | Coverage and task links |
| --- | --- |
| UT-RETAIL | Queue precedence, snapshot/count reconciliation, stale action categorization, unresolved review-request labels and safe fallback for inconsistent state. T33/T34; AC-33/34. |
| IT-RETAIL | Owned list/filter/count/detail; guessed IDs; expiry; bounded reads and polling; no inference/mutation on refresh; unavailable/stale status. T34; AC-32–36. |
| EV-LEARN | Actual fixed L01–L06 execution, independent declared expectations, baseline/candidate/suite hashes, bound reports and preserved failures. T33/T35; AC-38/39/42. |
| IT-LEARN | Feedback enums/ownership; no arbitrary candidate content; failed or changed evaluation denial; source/observation/base-policy races; same-attempt retry and lost-start-response reconciliation versus explicit new evaluation attempts; lease expiry/late completion; duplicate/uncertain activation; future guidance effect; monotonic rollback; unchanged lifetime limits. T35; AC-37–43. |
| B-F5 | Hosted console/row navigation, persistence, real counts and source-update category change in fresh owned contexts. T22/T34. |
| B-F6 | Hosted complete loop, retained records, denial branch, later visible guidance version and rollback. T22/T35. |

Extend IT-ISOLATION and RT-FIRESTORE with new records/routes and activation transactions. Extend B-A11Y with queue filters, table/mobile adaptation, candidate comparison, evaluation status announcements, confirmation and focus return. Extend SEC-RELEASE with public-data and private-operator separation. Reuse existing harnesses and evidence writers; no additional evaluation platform is needed.

## 7. Data, cost and runtime bounds

These are finite prototype limits, not measured safe capacity. They apply on the server across instances and restarts; client controls alone are insufficient.

| Resource | P0 bound and behavior |
| --- | --- |
| Shop/session | One synthetic demo shop per existing guest session; eight-hour expiry remains enforced on every access. No real multi-user shop membership or cross-session account recovery. |
| Incidents | At most 20 per session, enforced when creating the incident. No more than 20 summary rows per response. If existing compatible data requires pagination, make the page/count scope explicit; do not delete data or scan an unbounded history. |
| Feedback | At most 40 records/session; structured enums only. Each record binds one owned evidence context. Reject unknown/free-text fields. |
| Candidates | At most two distinct immutable candidates/session, from one fixed allowlisted guidance family. At most five supporting feedback references/candidate. |
| Evaluations | At most four accepted pure fixed-suite evaluation attempts/session, each retaining one report; one active attempt/session. A same-attempt retry returns that report without a new reservation. After a terminal attempt, an explicit new evaluation may reuse the same inputs but requires a new server-issued attempt identity and consumes another lifetime slot. Failed/expired attempts still count; no report deletion, network retry or restart resets the cap. No model or source-network calls. |
| Guidance transitions | At most two forward activations/session, with a rollback allowance reserved for each; therefore at most four accepted activation/rollback transitions. A valid current rollback is not starved by spending the forward-activation allowance. |
| Record size | Feedback/candidate/transition records at most 8 KiB each; evaluation report at most 16 KiB. Store fixture IDs/hashes, bounded outputs and evidence references, not duplicate source documents or image bytes. |
| Reads | Fetch bounded incident summaries and the finite curated source-family currentness records. Do not load full observations, action histories or images for queue counts. Detail/event reads are bounded and paginated where needed. |
| Refresh | Manual refresh by default. If background refresh is added, no faster than once per 30 seconds, no overlapping refresh, pause while the page is hidden, and back off on failure. A return to visibility may perform one bounded refresh. |
| Rate/cost controls | Deduplicate concurrent reads, rate-limit manual refresh and feedback/evaluation mutations, and count Firestore/Storage/monitoring costs within the existing granted allowance. Model-free does not mean cloud-cost-free. No unbounded polling, listeners or scans. |

Denial, timeout or missing cost/admission state cannot be represented as a zero count, evaluation pass or completed activation. Preserve known historical data with an explicit stale/unavailable label where authorized access remains possible. The full app being unavailable cannot be solved by a status widget served by the same failing process; actual external availability monitoring remains an OPERATIONS obligation.

Apply expiry to every added child record; access denial does not wait for Firestore TTL. Cleanup and physical-deletion delays follow the existing disclosed policy. Evaluation fixtures and approved sanitized release evidence have separately recorded retention. Keep session capabilities, hidden expected answers and personal data out of logs and public Git. **Do not publish the owner's personal schedule, attendance/sleep/return windows or other private availability details in the retailer console, technical screenshots, public guide, demo, logs or public evidence.** Any necessary private run-expiry/ownership facts stay in an approved private operator record.

## 8. Implementation tasks and verification order

All tasks below are **NOT IMPLEMENTED / NOT RUN**. Insert them by dependency into [tasks.md](tasks.md); their numeric IDs do not postpone them until after T32 closeout.

| Task | Dependencies and bound | Required output, acceptance and evidence |
| --- | --- | --- |
| T33 Retail/learning contracts and independent cases | M1 after T05a; prepare alongside T06 before extension implementation. | Freeze AC-32–43 mappings, queue rules, contracts, limits, structured feedback enums, fixed reviewed guidance variants and independent L01–L06 expectations. Evidence: proposed docs/evidence/M1-retail-learning-contracts.md; UT-RETAIL/EV-LEARN specifications. |
| T34 Retail console | Backend start after T33 + T09 ownership; Final visual integration after T06 replacement approval; provisional functional UI follows tasks.md and the T12 shell. Sign-off waits for T11/T16 currentness integration. | Owned persisted queue/counts/filters, A navigation, bounded reads, correct historical/availability/uncertainty states and isolation. Evidence: proposed docs/evidence/M3-retail-console.md; UT/IT-RETAIL, B-F5 and affected B-A11Y/RT-FIRESTORE. |
| T35 Controlled operational learning | T33 + T09; feedback references T15 recapture/correction semantics. Integrate before candidate freeze/final review. | Actual persisted feedback/candidate/fixed evaluation; explicit version-bound activation; subsequent changed guidance; monotonic rollback; all denial/race/limit checks. Evidence: proposed docs/evidence/M3-learning-loop.md; EV/IT-LEARN, B-F6 and affected RT-FIRESTORE. |

Required existing-task integration:

- T06's high-fidelity approval set covers A workbench, retailer console and feedback/candidate/evaluation/confirmation states together. Preserve the original three directions as historical evidence; do not repeat A/B/C selection.
- T17 implements that accepted visual system. Only their final visual treatment depends on T06/UI-SELECTED, not T17 completion. Backend and reversible provisional work follow the start dependencies in tasks.md; final T17 sign-off includes their relevant UI without a circular dependency.
- T19 covers actual added persistence/isolation/transaction races. T20 records active guidance-policy versions while retaining the core denominator and held-out discipline.
- T22 executes F1–F6 with the existing hosted browser infrastructure. T24/G3 includes both new P0 requirements and actual loop evidence.
- T26 freezes candidate-rule, guidance-policy and learning-suite versions with model/prompt/verifier/source versions. T27–T29 bind deck/video/guide/claims to actual console and loop evidence. T32 records scoped-policy rollback and added-record retention.

For each test/evidence artifact record UTC time, exact command or supported invocation, source revision/tree hash, endpoint/revision if hosted, case IDs/denominator, policy/candidate/suite/input hashes, actual output, failures, assistance and PASS/FAIL/NOT RUN/BLOCKED status. Do not expose session tokens or hidden answers. A pure fixture evaluation is not a real-model evaluation; a stored report without verified execution is not acceptance.

## 9. Release, fallback and explicit exclusions

P0-12 requires a real owned queue over persisted records. P0-13 requires the complete demonstrated loop, including future effect and rollback. A screenshot-only console, feedback log, hardcoded pass or roadmap-only learning story cannot close them. Protect the execution plan's fixed verification/submission reserve. If the added required scope cannot be completed, report the exact unmet gate and obtain a concrete scope decision; do not silently remove core recall requirements or relabel an incomplete loop as delivered.

A native design workflow may replace an unavailable skill while meeting the same approved visual-quality gate. Neither rejected original wireframes nor a new framework are automatic quality fallbacks. Impeccable/Emil source research is not installation/application evidence.

Excluded from this extension: consumer-facing health advice; inventory quantity/value tracking; ERP/POS/supplier integrations; real holds/releases/refunds/messages; multi-store administration; production retailer/customer identities; cross-guest collaboration; bulk approval; configurable analytics; free-text feedback; arbitrary candidate generation; production preference training; automatic global prompt/model/source/verifier promotion; continuous recall ingestion; new orchestration or training platforms. The unfinished StackClimb Work Package Protocol and Multi-Work-Package Orchestration remain excluded operational dependencies.

Availability monitoring and the private technical dashboard are required only within their recorded owner scope and OPERATIONS acceptance. They do not establish continuous recall monitoring or a successful AI journey. Final visual approval refers to shown high-fidelity artifacts; final submission refers to the concrete verified release. Reuse existing valid owner grants and the approved video duration without repeated permission requests.

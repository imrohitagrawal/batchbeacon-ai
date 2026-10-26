# BatchBeacon: consolidated user-journey audit and correction plan

25 October 2026 · Baseline audit and accepted implementation specification.

Current requirement status and remaining gates are owned by the authoritative checklist in section 9; [M9](evidence/M9-user-journey-correction.md) retains supporting evidence. The observations below preserve the original audit; they are not a claim about the corrected candidate or current release.

**Original audit verdict (before PRs #12–#14):** the filmed workflow exists, but then-current progress, stage guidance and recovery controls do not yet support a dependable unaided judge walkthrough. A successful upload can look like nothing happened. Some recovery controls offer operations the server correctly rejects. Preserve the video’s recognizable workflow and repair these boundaries together.

## 1. All owner requests retained in one scope

| ID | Owner requirement | Where addressed |
|---|---|---|
| R01 | Thoroughly use and check functionality, including Use this label and Extract and check | Live observations, code review, controlled reproductions; findings F1–F5 |
| R02 | Loader, meaningful processing/completion/error messages, and visible next step | F1–F2; implementation A; acceptance matrix |
| R03 | New-user, product-code and usability perspectives together | Three independent review roles; evidence and limitations below |
| R04 | Preserve the submitted YouTube flow so judges recognize it | Section 3 video contract; no video replacement or broad redesign |
| R05 | Explain overall purpose and end-to-end operation | Section 4 goal, stages and decision information |
| R06 | Explain the AI agent in text, not voice | Section 4 Gemini/ADK/server/human roles |
| R07 | Explain unconfirmed outcome, why it happens and what can resolve it | F3–F4; section 5 recovery contract |
| R08 | Tell users what to verify, how, and which evidence/source to use | Section 4 decision matrix and review checklist |
| R09 | Useful recommendations and permitted actions when AI cannot complete the task | Section 5 state-specific recovery; no dead-end or impossible actions |
| R10 | Consider confidence/score without misleading the user | Field-level evidence states; no uncalibrated numeric confidence |
| R11 | Research and deep analysis; preserve every discussed issue in one workstream | This register, current screenshots, code/video reviews and section 8 research |
| R12 | Expert next plan and release criteria | Sections 6–7; incomplete model gates stay explicit |

## 2. What was actually examined

- Current custom-host Chrome session, desktop 1470×754 and mobile 390×844. The browser reused the owner’s existing workspace; this was **not a fresh guest or blinded first-user study**.
- One new sample-only case was created and its image retained. No AI extraction, correction, verification mutation, hold or guidance change was submitted in this audit. Existing cases were inspected read-only. A saved-status recheck used only reads.
- Live queue, existing unresolved case, historical comparison, mobile decision view, guidance eligibility, tour steps 1–2 and Escape focus restoration were inspected. Phone guidance had no observed horizontal overflow; expiry was readable. These observations do not certify full accessibility.
- Deployed JavaScript and both stylesheets were downloaded and exactly matched reviewed source `99587e251cf3d3835aa83648cab3e2e8c1647398`.
- Independent implementation reviewer ran **52 existing targeted local tests**, then separate delayed/intercepted reproductions. Independent usability reviewer inspected the live screenshots and separately ran four acquisition-completion rejection cases. These are local tests, not new live-model passes.
- Independent video reviewer rehashed the retained 220-second submitted MP4 against its publication receipt, read its narration/storyboard, extracted a new contact sheet and inspected key frames. This was renewed inspection of the exact historical artifact, not a new continuous YouTube playback or subjective audio review.
- Private evidence: `.local/run-records/usability-audit-20261025/`, including code-review.md, usability-review.md, video-review.md, live-asset-binding.json and ordered screenshots. Session identifiers and private run details are excluded here.

The previous seven-call validation ceiling is exhausted. No eighth call was made. October 22’s positive model tests remain historical evidence; the unrelated-label provider failures remain an open acceptance gate. Today’s owner-workspace unresolved state must not be assigned those older calls’ exact cause without its own authoritative receipt review.

### Findings and triage

| ID / classification | Demonstrated behavior and impact | Smallest responsible correction |
|---|---|---|
| F1 REQUIRED_CONTRACT | Live Use this label disables/re-enables with the same text. At completion the success notice was above the viewport and Extract below it. No visible handoff. The upload itself succeeded. Controlled mobile extraction also retained the normal button label and generic waiting text. | Adjacent operation-specific status; indeterminate loader; persistent completion/error; explicit next-step handoff. |
| F2 REQUIRED_CONTRACT | After a retained image exists and Extract is enabled, the result panel still says Ready for evidence and instructs choosing/uploading a label. | Render distinct no-label, label-ready, checking, completed, failed, unresolved and expired states. |
| F3 REQUIRED_CONTRACT | The live unresolved case shows enabled Correct a field/Reverify corrected evidence, while the server rejects these for a latest acquisition without immutable completion. On mobile the visible recovery CTA is Reverify; the requested Recheck is far above in another panel. Guidance repeats Check or reverify. | Server-owned operation capabilities and reasons; offer only valid actions beside the explanation. Consolidate all three symptoms under this root cause. |
| F4 REQUIRED_CONTRACT | Controlled reproduction: open an incident without a latest run after a known workspace-wide unresolved attempt. The client clears the warning, enables Extract and hides Recheck; server still denies generation. Live uploaded-but-unchecked case in the same workspace showed the same misleading availability. | Project workspace admission independently from the selected incident’s latest run; preserve/refresh authoritative scope on navigation and reload. Client cache never becomes authority. |
| F5 REQUIRED_CONTRACT | Controlled delayed GET returns after expiry and restores evidence/Ready for evidence over Guest access expired. Extract stays disabled; no server access bypass demonstrated. | Session/selection generation checks; discard stale success and error responses; expiry remains terminal for that client session. |
| F6 REQUIRED_CONTRACT | Live mobile navigation from a deep decision view to Capture guidance landed near the bottom, hiding the page purpose. The URL retained the earlier decision fragment. | Consistent view routing, scroll and keyboard focus after explicit navigation; preserve position only where useful and intentional. Test reload/back behavior before claiming it fixed. |
| F7 ADVISORY_DEBT | Long orientation fills the first desktop viewport; uploaded-but-unchecked queue items say In progress; raw candidate IDs and technical evidence terms add work for a newcomer. | Short goal and start action; state-specific queue wording; product names and plain explanations before technical provenance. |
| F8 REQUIRED_CONTRACT — existing readiness gate | Current full model/video acceptance remains incomplete. A spinner or copy correction cannot fix provider availability or settle an unknown attempt. | Separate bounded operational diagnosis and independently reviewed timing/accounting correction, with explicit new authority before any further paid validation. |

No demonstrated server false acceptance or authorization bypass was found in these reproductions. This is not a universal zero-error claim. Source references: `src/batchbeacon/ui/workbench.js` task/controls (24–40), acquisition status/render/load (71–111), sample/acquisition and navigation handlers (140–155); `evidence_service.py` acquisition currentness (431–462), correction/verification guards (614–615, 649–652); `shared_admission.py` unsettled workspace attempts/read-only reconciliation (898–929). Line numbers refer to the audited source.

## 3. Video remains the workflow contract

[Submitted video](https://youtu.be/IpY2_GeR4Ic): **choose label → extract and compare → review evidence → explicitly confirm an eligible workspace action → reopen in queue**. Guidance stays a contextual extension of that journey.

| Video segment | Preserve | Required current behavior |
|---|---|---|
| 0:49–1:06 | Choose example, Use this label, retained image, Extract and check | Clearly separate choosing, uploading and AI checking; reveal the next action. Upload alone never starts AI. |
| 1:06–1:26 | Identity-first, field-by-field comparison and source evidence | Display accepted values, source values and supported comparison; open readable provenance on demand. |
| 1:26–1:40 | Explicit review and confirmation | Only a current eligible result opens the action; show no-live-inventory effect and unchecked consent. |
| 1:40–1:56 | Saved queue, reopen and mobile | Correct case, label, result and action survive same-session reload; return directly to useful evidence. |
| 1:56–2:15 | Unrelated product never matches merely because lot agrees | Supported nonmatch or genuine extraction rejection; timeout is not negative acceptance. |
| 2:15–2:35 | Guidance purpose and prior evaluation evidence | Explain eligibility; do not promise that every complete example can exercise a new full lifecycle. |
| 2:35–3:40 | Architecture and future vision | Historical counts stay historical; consumer/accounts/broader coverage remain planned. |

The video shortens waiting and reframes results. It does not establish good real-time feedback or unaided usability. Quiet progress was present in the recorded flow too; this is not evidence that post-video UI edits caused every problem. Keep the approved visual treatment, original examples, source scope and meaningful controls; add clear feedback and transitions around them.

## 4. What the application should tell the user

**Goal:** help a retail reviewer compare a product label with a selected official recall notice, understand the evidence and record a deliberate review action. This prototype uses sample labels/inventory and historical evidence; recorded actions do not change live stock. It does not certify safety or search all recalls.

**AI role, in ordinary text:** “Gemini reads the label image and proposes the product, lot and date. The app compares accepted details with the selected official notice using fixed rules. You inspect the evidence before confirming an action.” A secondary How this works detail can explain that one bounded Google ADK workflow coordinates extraction; Firestore retains owned evidence and Cloud Run hosts the app. Do not imply a multi-agent product, autonomous recall authority, self-improvement of the verifier or voice functionality.

Show the stage prominently: **1 Label → 2 AI extraction → 3 Evidence comparison → 4 Your decision → 5 Saved review**. Each stage reflects actual state, not an animated simulation of backend steps.

### The evidence that supports a decision

| Information | Explain to the user | Decision it supports |
|---|---|---|
| Retained image | This is the label used for this investigation; distinguish new capture from previously saved image. | Is this the intended product/label? |
| Extracted identity | Product/brand/pack exactly as available; readable versus missing/conflicting. | Does the proposed identity agree with the visible label? |
| Lot and required date | Original label value beside accepted interpretation; preserve case, zeros, unknowns and applicability distinctions. | Is the relevant batch/date comparison supported? |
| Official notice | Authority, exact link, publication/version, jurisdiction and historical coverage. | Is this the relevant source and scope? |
| Comparison | Match/mismatch/not-used/unknown with plain reasons; identity comes first. | Which fields support or prevent a scoped match? |
| Evidence condition | Current, previous/historical, incomplete or awaiting request resolution. | Can this evidence support a new action now? |
| Suggested next step | A valid control plus why it is available, and what it changes. | Review/correct/add evidence where supported, recheck, escalate, or explicitly confirm an eligible action. |

Review checklist: inspect full product identity first; inspect exact lot and any required date; verify the notice’s scope and version; inspect differences; confirm only an action that is currently eligible. The app should link to the evidence at each step. This is a product review workflow, not medical advice or authority to release stock for sale.

**Confidence:** use evidence states such as “field read,” “missing,” “conflicts with label,” “identity matched,” and “check incomplete,” each backed by facts. Do not call an operational failure “0% confidence.” Do not invent a safety score, general certainty badge or percentage from model prose. A numeric model-confidence feature would require a defined target, calibration, evaluation and a separate accepted scope; it is not needed for this repair.

## 5. Useful outcomes and recovery, without misleading promises

| Actual state | User-facing explanation | Valid next steps and limits |
|---|---|---|
| Label ready | “Label saved. Next, extract and check its details.” | Show retained image and Extract only when authoritative workspace admission permits; otherwise show the workspace block. No AI yet. |
| Request pending | “Requesting label extraction…” / “Waiting for the AI response…” when accurate. | Indeterminate loader and elapsed time if useful; no invented percent or guaranteed finish. Prevent duplicate work. |
| Current supported match | “These details match this selected notice.” | Inspect identity/lot/date/source, then explicitly review an eligible workspace action. No safety/contamination claim. |
| Supported scoped nonmatch | “Not listed in the notice checked.” | Inspect identity/source scope; explain limited coverage. No safe-to-eat or sale-release conclusion. |
| Missing/conflicting extraction | Name the affected fields and evidence. | Clearer image or supported correction only when the server allows it; otherwise a defined review path. Never override identity/source checks. |
| Known settled service failure | “The check could not finish.” Give the verified plain-language reason. | Preserve image/source; offer an explicit retry only if currently admitted. No hidden retry. |
| Unconfirmed request/accounting outcome | “We can’t confirm a completed AI check. Your saved label is available. New AI checks in this workspace are paused while the earlier request is resolved.” | Primary Recheck saved status beside the message; View saved label/notice; real operator escalation route when configured. For a selected case whose latest acquisition is incomplete, show its previous comparison separately as historical and disable its futile correction/reverify actions. Preserve valid capabilities of other completed cases; never fabricate a result. |
| Expired session | Access expired; explain the supported new-workspace path and what will not transfer. | Keep expired state despite late replies; no automatic resurrection of evidence or claim of persistent account recovery. |

Workspace-wide unknown accounting blocks new AI requests; case-level completion/currentness separately governs saved evidence, correction, reverification and actions. Only label a selected comparison historical when its own currentness requires it.

“Unconfirmed” is operational: the app lacks authoritative completion/settlement for an attempt. It is not an AI conclusion about a product. **Recheck is read-only and does not itself repair or settle the attempt.** After rechecking, display “Still unresolved; no new AI request was sent” with a checked-at time, or the newly confirmed result if the server has one. Do not promise automatic resolution or a response time without an implemented process.

Escalation must be real. If there is no approved support destination/operator procedure, state that limitation and define the owner-operated process before advertising “Contact support” or “We’ve notified someone.” Showing a copyable support reference can be scoped separately; never send messages or expose private logs automatically. Opening another label/workspace must not be promoted as a way around unknown liability.

## 6. Bounded implementation sequence

### A. Visible feedback and correct stage rendering

- Replace anonymous busy handling with a small typed operation/stage model: upload, extraction, read-only status check, deterministic verification, queue/guidance refresh, action save.
- Use an adjacent status region and stable operation-specific button text, accessible busy state and an indeterminate visual indicator. Keep success, unchanged status and failure messages visible near the action. Respect reduced motion.
- Preserve the old evidence while refreshing, explicitly marked as loading/historical; do not briefly reset a reopened case to Ready for evidence.
- After an explicit completed upload, reveal the label and next action. After checking, reveal the current result/failure. Do not steal focus during background refresh.
- Distinguish label-ready from no-label and update queue labels from actual stage. A new user must not infer that upload starts AI.

### B. Truthful capabilities and resilient navigation

- Introduce/reuse one owned server capability projection for workspace extraction availability and case-level correction, deterministic verification and action eligibility, with safe reasons. Keep these distinct scopes.
- Preserve known workspace blocks across new/no-run case selection, then reconcile with authoritative current state. Fail closed on missing capability data without fabricating a reason.
- Disable impossible recovery actions and fix guidance’s repeated reverify advice for incomplete acquisitions. Keep valid correction for genuinely completed-but-stale evidence.
- Discard late responses after expiry or a newer session/selection. Make explicit view navigation reveal its heading/next action, and keep URL/history/reload behavior consistent.

### C. Evidence and agent explanation

- Add concise Gemini/server/person role text at entry and a What happened in this check detail tied to actual evidence.
- Put status, scope, reasons and a primary next step together. Use product names before raw candidate IDs; put technical provenance behind details.
- Implement the state-specific copy above and a real escalation procedure; do not invent a score or new autonomous feature.

Minimum operator-handoff acceptance: identify the responsible project operator and an owner-approved existing contact channel; show a copyable case reference without private logs; give the user a visible route and explain what information to provide. Define the operator’s receipt review/reconciliation procedure and how the user checks for resolution. Verify the handoff works before advertising it, and state honestly if no channel is configured. Do not promise notification, delivery or a response deadline without evidence. Choosing/publishing a contact destination remains an explicit owner decision; this plan does not expose the private monitoring address or authorize outbound messages.

### D. Verify, then release within the existing operating scope

- Reproduce each finding with a failing regression before fixing its smallest boundary. Independent reviewers verify corrections and classify any new findings by demonstrated impact.
- Run the full relevant local suite, exact hosted push/PR commands and merge topology; bind production assets/configuration and verify live desktop/mobile transitions before declaring the release complete.
- UI repair and provider/outstanding-attempt resolution are linked but separate gates. Preserve source/verifier/ownership/expiry/consent/deduplication/accounting and the compatible original-liability/admission fence.
- Any runtime deadline or settlement change needs a freshly bounded operational plan and inventory. Any further paid call needs new explicit authority; the exhausted seven-call grant is not renewed by this audit.

## 7. Observable acceptance, not only green tests

| Scenario | Pass condition |
|---|---|
| Slow upload / failed upload | Visible operation-specific status at the actual click position on desktop/phone; success shows retained image and next action; error stays adjacent. |
| Slow extraction / accepted result / known failure / unknown result | Distinct honest states, no duplicate/automatic generation, appropriate terminal message and valid next action. A failed request is never a nonmatch. |
| Same unresolved workspace, new case and reload | The authoritative workspace block remains visible; no misleading enabled Extract on a case with no latest run. |
| Old comparison plus incomplete newer run | Historical evidence remains labelled; correction/reverify/action controls agree with the server. |
| Status recheck, unchanged and resolved | GET-only; visible checked/unchanged/resolved feedback; no promise the GET performs settlement. |
| Expiry during outstanding reads | Delayed success or failure cannot restore evidence or replace expired guidance. |
| Navigation while pending; queue reopen | Correct selected case/view, no silent dropped navigation, no unexpected return to another view; heading/next task visible below sticky navigation. |
| Keyboard and assistive technology | Enter/Space equivalent, sensible focus destination, Escape restoration where applicable; status announcements are meaningful. Test with actual assistive technology before claiming full compliance. |
| Responsive layout | Desktop, 390px, 320px and text enlargement: feedback/result/primary action visible at meaningful positions; no obscured target/overflow. Avoid auto-scroll test APIs masking the defect. |
| Guidance lifecycle | Controlled empty, eligible, ineligible, feedback, proposal, evaluating, failed/passed, activated and rollback states. Historical video evaluation is not a fresh live pass. |
| Judge/video rehearsal | Follow the filmed stages without a narrator or developer explaining where to scroll. Record observed assistance and failure. Actual model gates remain separate from controlled fixture passes. |

The UI/capability corrections can be developed and tested with controlled fixtures without paid calls. Read-only deployment checks cannot establish actual model availability. A true first-time human usability session and full fresh live/model acceptance remain separate evidence obligations.

## 8. Research used and application to this product

- [W3C WCAG 2.2: Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html): waiting, completion and errors need programmatically determinable status so assistive technology can notify users without unnecessary focus changes. This supports accessible adjacent status updates; existing role=status alone does not prove that sighted users see offscreen feedback. We have not established a complete WCAG conformance verdict.
- [Google PAIR: Mental Models](https://pair.withgoogle.com/guidebook-v2/chapter/mental-models/): introduce capabilities and limits progressively and preserve a useful path when AI fails. Application: simple role explanation, contextual guidance and access to saved label/source while verification is unavailable.
- [Google PAIR: Explainability and Trust](https://pair.withgoogle.com/guidebook-v2/chapter/explainability-trust/): explanations, data sources and appropriately designed confidence communication should support calibrated trust. Application: evidence-backed field states and clear scope, rather than unvalidated confidence percentages.
- [Google PAIR: Errors and Graceful Failure](https://pair.withgoogle.com/chapter/errors-failing/): distinguish failure sources and provide actionable paths forward. Application: request failure versus uncertain extraction, concrete recovery capabilities, and no controls that lead to predictable rejection.

Research informs the recommendations; the defects above are substantiated by this application’s live observations, code and controlled reproductions. Additional features are not required to restore the submitted journey. No guarantee of a win, universal correctness, food safety or provider availability follows from this plan.

## 9. Authoritative acceptance checklist and continuation checkpoint

This section is the single current acceptance register. Sections 1–8 retain the
accepted requirements and original audit, including failures; M9 supplies detailed
release evidence rather than a competing checklist. A row can be implemented and
still incomplete. `U` = unit; `C` = controlled/fake service; `E` = Firestore emulator;
`B` = browser; `CI` = hosted checks; `S` = deployed real service; `M` = actual model;
`AT` = actual assistive technology; `H` = first-time human observation. Historical
evidence is explicitly dated and never substituted for current M/AT/H acceptance.

Recovery readbacks confirmed the prior support image, runtime/IAM/ledger and
both-host assets; those baseline observations remain historical. Current correction
evidence is recorded in M9 and the register below. Detailed receipts are private under
`.local/run-records/acceptance-continuation/operations-review/`.

Recovered baseline: remote main `accf95e` included PRs #12–#14; the prior support
release source was `351990d`. Root checkout is older with unrelated changes and is
preserved. U34's confirmed single-email receipt and later promotion supersede all
earlier support-not-configured statements. U28–U30 authority was retained in that
older checkout; U31's public model pool is ₹650, total remains ₹6,000. No additional
AI/countTokens/retry/email or settlement authority follows from this continuation.

Current technical release: PR #15 merged; source `bc7da038c6f30b41abe0a4b8f5b6395234f95efd` and image
`sha256:4bb48a2048df5ddbfbfb845a649f4d7c9da33cb66610f5efd770f6e82073452f` are verified on both public hostnames. M9 records exact CI/package,
real-service/browser evidence and failures. This is technical release acceptance,
not complete model, assistive-technology or human acceptance.

### Requirement-by-requirement register

| ID | Acceptance criterion retained | Implementation and evidence | Remaining gate / role / next action |
|---|---|---|---|
| R01 | Exercise every meaningful control; label selection persists and explicit extraction alone starts AI. | Implemented F1–F6; current 1,464 U / 133 B / 29 edge / eight E and exact push/PR/main CI pass; historical S upload and M positives distinguished. | Current S retained-label/recheck/queue/reload/focus/mobile checks pass on both hosts. Accounting reconciliation is complete under U36. U38 fresh M third-case failed extraction and stopped the series; no later cases/retries permitted. Integrator retains failure; future changed experiment needs reviewed scope and new authority. |
| R02 | Immediate accessible progress, duplicate prevention and visible completion/refusal/error with next action. | Implemented F1/F2; pending live region now remains nonbusy while visual loader/buttons reflect actual state. Twenty baseline failures now pass; independent C/B review passes. Current S upload handoff and M pending/refusal feedback observed under U38; no speech inferred. | Owner-operated AT reported no speech in the first controlled task; also silent on other webpages after a manual settings check; cause unknown. Accessibility reviewer/integrator must verify actual pending/terminal output and remaining tasks; role=status alone is not acceptance. |
| R03 | First-user, product, code and usability perspectives assess the whole journey. | Independent technical product/code/video reviews in M9; agent walkthroughs only. | Mandatory H: a first-time participant follows the short procedure below; owner arranges participant, integrator records assistance. |
| R04 | Preserve filmed choose/upload → extract/compare → review → confirm → queue/reopen, plus unrelated-label and guidance behavior. | Section 3 segment contract; exact retained-video provenance review and controlled positive flow in M9. Earlier M positives and unrelated-call failures retained. | Mandatory M+H remains: U38 third identity was refused for incorrect extracted name, not a deterministic nonmatch; A/B were not attempted. The filmed protective refusal is supported independently of the still-failed deterministic nonmatch. U39 candidate/changed-experiment preparation does not close either fresh A/B or nonmatch M acceptance; H participation needed. |
| R05 | Explain purpose, sample data, limited notice coverage and complete journey. | F7 text/stages implemented; M9 C/B and both-host S purpose/retained-workspace observations pass. | Mandatory H comprehension: participant explains purpose and next step without coaching. Preserve no safety/clearance/worldwide claim. |
| R06 | Text explains Gemini proposal, one bounded ADK workflow, deterministic rules and human consent. | F7 implementation/source, C/B review and current S exact assets. No voice feature. | Mandatory H comprehension; judge reviewer checks current text against code/video. |
| R07 | Explain request/accounting uncertainty separately from uncertain extracted fields, cause/unknowns and truthful recovery. | F3/F4 implemented; M9 C/B, F8 retained-byte parser correction verified offline; older no-response timeout distinguished. Support active. | Mandatory S panel: newer session was unexpired at discovery but its original capability was unavailable; both known unresolved sessions have now expired. No usable known live case remains. A future legitimately owned active state is required; never restore, transfer or manufacture a paid state. |
| R08 | Link intended image, identity, exact lot/date, source/scope/version and differences to review/action. | F7 checklist, provenance and currentness; M9 C/B, historical M evidence. | U38 M review found the printed subtitle included in the product name; source translation agrees with review and identity guard refuses. Backend/integrator retains this REQUIRED_CONTRACT model-acceptance gap; H and future valid M outcomes remain. |
| R09 | Only presently permitted actions; read-only recheck, support contact and expired recovery are honest. | F3–F6 capabilities, ownership/expiry, configured support; M9 U/C/B/CI/S (live panel absent in test workspace). | Mandatory live-panel dependency and AT/H; never imply notification, response deadline, settlement or transferable expired case. |
| R10 | Evidence-backed field states; no invented confidence or safety score. | Implemented without numeric confidence; source/C/B review in M9. | H confirms nonmatch is understood as scoped, not safety; any contrary response is a finding, not a pass. |
| R11 | Research, code/history/video review, retained failed evidence and complete requirement coverage. | Sections 1–8 and M9 retained; four required specialist perspectives completed, findings reproduced/classified and corrections independently verified. Exact submitted MP4/narration provenance reviewed; fresh sampled visual review covers all 44 five-second positions across the complete sequence. | Integrator retains failed evidence and updates this register after remaining external acceptance; no continuous-video or unavailable speech review claimed. |
| R12 | Reviewed bounded plan, dependencies, meaningful regression, release/rollback and honest closeout. | Sections 6–7 plus this checkpoint; independent planning/correction/release reviews completed in dependency order. | Authorized technical correction/release work complete with both-host S checks and durable handoff. Operation A is independently complete. B2 capture correction independently verified; first M case failed and series stopped. Integrator closes evidence/release; future changed M experiment needs review/new authority, AT/H and live-panel state remain blocked. |
| F1 | Adjacent upload/extraction progress and visible saved-label handoff, errors cannot reuse prior label. | Implemented; current U/C/B/CI regressions pass, including corrected nonbusy progress semantics; current S upload/save and M processing/refusal observed. | R02 actual AT and H remain; U37 fresh upload passed; U38 reused and reverified that retained image. Lingering upload receipt after extraction is tracked advisory ambiguity below. |
| F2 | Distinct no-label/ready/checking/completed/failed/unresolved/expired stages reflect facts. | Implemented; current U/C/B/CI covers completion, refusal, failure, stale response and corrected progress; S nonmodel subset and U38 actual M pending/refusal. | Fresh successful M completion remains F8; actual protective refusal observed, but AT must hear pending/terminal transitions. |
| F3 | Owned case capabilities disable futile recovery; recheck beside unresolved explanation. | Implemented; M9 U/C/B/CI, deployed API/config and support. | Visible S panel remains incomplete: original capability was unavailable during its valid interval and both known unresolved sessions are now expired. Need a future legitimately owned active case, not an extra paid attempt to create one. |
| F4 | Workspace block survives no-run case, navigation and reload independently of selected result. | Implemented; M9 U/C/B/CI; S allowance-unavailable subset. | S own-unresolved state unavailable: both historical owner sessions expired; new U38 failed extraction settled normally and has no unknown request, so no panel is expected. Controlled panel/reload evidence passes; integrator awaits a legitimate active case. |
| F5 | Late success/error cannot overwrite expiry or another selected case. | Implemented; independently reproduced regressions and current full U/C/B/CI pass. | Controlled race coverage complete for this increment; no claim of live race injection or H/AT acceptance. |
| F6 | Explicit navigation reveals destination, focus and scroll; reload/back/reopen preserve context. | Implemented; current C/B keyboard/race tests and both-host S navigation focus, mobile, queue and reload pass. | U38 refused-case queue/reopen/reload and mobile context also pass. Actual AT/H remains; agent browser operation is not human usability. |
| F7 | Clear short purpose, readable queue/status, technical details disclosed on demand. | Implemented advisory clarity work; M9 C/B and both-host S observations. | Lingering upload receipt after extraction is ADVISORY_DEBT: historical upload-specific wording beside truthful refusal, no demonstrated false result/action. Product owner tracks a later small wording/clearing improvement; R05/R06 H comprehension remains mandatory. |
| F8 | Supported usage/accounting, preserved unknowns, actual successful complete positive and unrelated/wrong-product validation. | PARTIAL. Strict cache-subset parser implemented and independently verified with retained provider bytes, U/C/E; original-rate valuation preserved, newer usage settled under U36 and older unknown held. Earlier no-response timeout remains distinct. | Operation A is owner-authorized and independently verified: newer retained usage settled, older liability held, failed runs/expired ownership preserved. Cache-aware rollback is now mandatory. U38 produced one incorrect-name M response, correctly refused and automatically settled with no new unknown; series stopped before A/B. REQUIRED_CONTRACT model-acceptance gap remains. U39 offline field-selection diagnosis/candidate regression is complete; actual candidate efficacy remains unproved. Exact one-case proposal is prepared privately; new explicit activation/model authority is required. No retries under U37/U38. |

### Classification and independent work

Mandatory current closeout: R01–R12, F1–F6/F8, active source/ownership/consent and
budget invariants, current model/video demonstration, visible recovery where an
authorized case is available, actual AT and first-time H evidence. Implemented F7
is retained; further cosmetic cleanup is advisory. A reproduced accessibility
announcement failure is R02 REQUIRED_CONTRACT, not optional polish.

Historical broader gates remain incomplete under U18's disclosed narrower demo:
full six deployed journeys, complete 24-development/eight-protected evaluation and
custody, remaining UK/source truth, full Operations telemetry/physical cleanup and
baseline/impact study. U17 keeps UK review-only. They must not be called complete
or silently promoted into new authority. U30 monitoring/receipt evidence updates
only its actual coverage; a health check does not prove AI availability. The
pre-existing OpenTelemetry advisory remains ADVISORY_DEBT absent reproduced app
impact. Reclassify only with evidence, preserving the previous disposition.

While model/settlement/human paths are blocked, proceed with plan reconciliation,
retained-byte diagnosis, offline regression/correction, controlled browser and
emulator checks, current deployed read-only checks, video provenance/comparison,
AT capability investigation, and concrete human/model procedures.

### Reviewed correction plan and execution order (retained checkpoint)

1. Recover exact main/deployment/support/config/accounting state and retained video;
   substantiate each new finding. Primary owns this register; independent reviewers
   cover product/UX/AT, backend/accounting, security/operations and judge/video.
2. F8 smallest candidate boundary is strict provider usage decoding and its ledger
   consumer. Cached tokens are a subset of prompt tokens, not additional tokens.
   Confirm official schema and price evidence before choosing an accounting rule.
   Do not infer cache discounts, suppress unexpected meters, change countTokens
   behavior, increase timeouts, change model or clear unknown reservations.
3. Before dependent changes, independently review exact proposed counting, pricing,
   original-attempt compatibility and rollback. Existing readers rederive stored
   usage, so accepting cached receipts can make older images incompatible even
   without adding a field. Require executable old/new-reader and immutable-record
   proofs, a compatible rollback plan, and explicit activation/settlement boundaries.
   If a price/policy decision is required, keep affected activation blocked while
   preparing and testing all independent code and evidence.
   Reviewed accounting decision: preserve the existing ModelPrice full-prompt and
   output-plus-thought calculation and original attempt-bound rate. This is a
   conservative ledger valuation, not a provider invoice; no cache discount or
   new tariff is inferred. CompleteUsage fields and existing digests stay unchanged.
   Validate nonnegative integer cached counts no greater than prompt total and,
   where both modality breakdowns exist, each cached modality within its prompt
   modality. Continue refusing tool use, unknown meters and non-on-demand traffic.
   The correction is prospective parsing capability, not authority to settle.
   Current public uncommitted capacity is below the unchanged per-attempt
   reservation. Exact live ledger values remain private. No new provider dispatch
   is admitted.
   Both historical unknown attempts and all ledger receipts must remain unchanged
   through publication. The prior image is a valid rollback only while this
   executable unchanged-ledger fence holds. Retain the corrected image as a
   cache-aware rollback candidate before any separately authorized settlement or
   model operation; recheck reader compatibility at that later boundary.
4. Required F8 regressions: valid zero/partial/all cached counts; strict type/range
   and prompt-subset constraints; modality totals/subsets; duplicate/unknown meters;
   incomplete/non-2xx/over-bound evidence; exact total including reasoning; original
   request/response/price hashes; no accidental double counting or discounts;
   atomic/idempotent/lost-ack settlement; old unknown record unchanged; GET recheck
   makes no settlement/provider call; actual fake ADK consumer receives valid usage.
5. Any reproduced R02 announcement problem is corrected only at the status/busy
   boundary. Prove pending text is announced before a delayed response, terminal
   success/refusal/error announced once, duplicate submission prevented, reduced
   motion and stale-response guards preserved. Automated semantics and actual AT
   observations are recorded separately.
6. Run full locked local unit/browser/edge and complete emulator suite. Before any
   release freeze, exact hosted Linux bootstrap, push direct-head and PR merge-ref,
   full commands, contents:read/persist-credentials:false, browser environment,
   status context and resulting merge tree must pass. Documentation-only changes
   still receive applicable hosted checks; local green does not substitute.
7. Runtime publication requires fresh finite cost/inventory admission, allowlisted
   package manifest, source/archive/image/config binding, network-disabled packaged
   checks and compatible rollback. Expired historical helpers are evidence only.
   Review a zero-traffic candidate before promotion, then check both hostnames'
   actual digest/config/assets and affected desktop/mobile behavior, with before/
   after accounting proof. Do not use a release smoke to perform settlement.
8. Only after accounting/admission prerequisites are sound, present a bounded
   validation request: exact cases, maximum calls/spend, effective configuration,
   unchanged source/prompt/model, stop conditions, ambiguous-outcome treatment and
   pass/fail evidence. Funds are not call authority. No paid operation is authorized
   by this plan or by an offline passing fixture.

The preimplementation checkpoint above is retained as history. Parser/status
corrections, full controlled suites, hosted/release checks and independent review are
complete. Both-host S checks passed; remaining external evidence stays explicit in
the register/M9.

### Human and actual-AT acceptance procedure

Use the current verified candidate and record its source/assets, browser/device,
participant familiarity, task, actual observations, assistance and outcome. Keep
personal details and session references private. A developer walkthrough cannot
fill H and automated accessibility checks cannot fill AT.

First-time participant: read the opening page and explain purpose/AI/human roles;
choose a sample, use the label and identify the next step; inspect retained label
and exact source; interpret an unavailable or unresolved check and try GET recheck;
open queue, reopen, reload, navigate on phone and explain expiry/support limitations.
Observe without coaching; record every hesitation, mistaken safety inference,
silent click or requested assistance. Full extraction/result/confirmation tasks
wait for admitted paid validation or use explicitly labelled controlled fixtures;
fixture observations never certify live model availability.

AT operator: record actual screen reader/browser/version and speech/output; use
keyboard to select/upload, hear immediate progress and terminal status, inspect
field/source evidence, move through confirmation with unchecked consent, reopen
queue, recheck unchanged/resolved state, and handle failure/expiry. Use controlled
slow/failure fixtures to avoid paid calls. Verify focus after navigation/dialogs,
no duplicate or suppressed announcements, and hidden/ineligible controls. Establish the current setting before any temporary change and restore it afterward.
The later owner-authorized recheck supersedes the earlier no-toggle commitment;
failed tool permission handoff does not imply absent conversational permission. If tools cannot observe speech, prepare this procedure
and record AT as NOT RUN, never PASS from DOM roles or a screenshot.

### Planning review disposition

Independent backend and operations reviewers cleared the strict-cache/full-rate
proposal and conditional rollback before implementation. Product/UX/video review
cleared this checklist and substantiated the R02 pending-region defect: the
`role=status` element is `aria-busy=true` for the entire request, permitting AT to
defer the pending announcement. Correct only this boundary by keeping the live
status nonbusy, retaining busy buttons and an independent visual loader state.
This proves suppressible semantics, not observed VoiceOver speech suppression.
A historical VoiceOver capability experiment restored its then-original off state
but could not observe speech. The owner subsequently authorized a recheck, manually
enabled VoiceOver, and requested disable; tool access prevented that disable.
The later capability inventory reports VoiceOver not running, which does not
verify the accessibility setting or spoken output. That inventory did not close AT. In the later owner-operated fixture attempt the
owner reported VoiceOver ON and no speech; diagnosis is pending. No setting was
changed by the agent and no restoration is claimed. Private plan reviews and baseline
reproductions are retained under the acceptance-continuation evidence directory.

### Historical closeout before U36

The following pre-resumption decision state is retained as history. U36 and the
resumption disposition below supersede its pending Operation A status.

Authorized unblocked correction and nonpaid verification are complete for this
increment. No complete product-readiness claim follows. The next owner decision
is narrowly scoped reconciliation of the newer retained complete receipt only,
using prepared private before/after records and idempotency/lineage guards. It
requires fresh exact admission and compatible rollback checks; the older unknown
liability and failed extraction remain unchanged. Releasing excess reservation
would reopen shared public capacity, not exclusively reserve validation capacity.
No settlement is executed or authorized by this document.

After any separately authorized reconciliation is independently verified, refresh
actual admission and present the prepared request for at most three sequential
model generations and associated token counts: SFA A, SFA B and third identity.
There is no retry allowance; stop at the first failure, ambiguity, capacity or
configuration drift. Detailed limits, unchanged configuration and pass/fail cases
are private. No new paid call is authorized now. H and AT procedures above are
ready for an actual participant/operator; they cannot be completed by agent review.
Live unresolved-panel acceptance needs a future legitimately owned active state;
expired cases cannot supply it and no paid call may manufacture it.


### Acceptance-resume planning checkpoint — 26 October 2026

The owner requests continuation from the completed technical closeout, preserving
all R01–R12/F1–F8 definitions above. Root changes remain unrelated and preserved;
the clean acceptance worktree is the sole integration location. No new product
implementation, redesign or repeated broad suite is justified by recovery so far.
Independent product/UX/accessibility, backend/accounting, security/operations and
judge/video reviewers cover this checkpoint. Their exact review and fresh evidence
are private in `.local/run-records/acceptance-resume-20261026/`.

Dependency order and acceptance:

1. Refresh remote/deployed source, immutable image, runtime/support, both-host
   assets, accounting inventory and document versions. Reuse still-bound unit,
   controlled, emulator, browser and hosted evidence; keep each evidence type
   distinct. At this initial checkpoint no model, token-count, settlement or email
   was authorized; the subsequent A-only decision below supersedes settlement scope.
2. Prepare Operation A only for the newer retained complete response. The prior
   packet proves offline arithmetic but lacks an execution wrapper that pins the
   reviewed document versions inside the transaction. This is a REQUIRED_CONTRACT
   preparation gap for R12/F8, not a newly demonstrated public application defect.
   After independent plan review, prepare the smallest private wrapper around the
   existing SharedAdmission and Firestore transaction path: compare exact guarded
   document preimages/versions in the transaction, allow only target/budget writes,
   require the reviewed postimages, preserve older liability/failed runs/ownership,
   abort drift, and classify uncertain acknowledgement through authoritative reads.
   Test drift, replay, concurrency, failed acknowledgement and write restrictions
   offline and with the existing loopback emulator. Do not execute a live write.
3. Verify a retained cache-aware rollback against the proposed settled receipt.
   The earlier reader is incompatible after such a receipt; do not offer it as a
   post-settlement rollback. Present the precise refreshed operation and shared
   public-capacity consequence for explicit owner decision only after preparation.
4. Extend submitted-video review across the accessible complete sequence with
   accurately labelled sampled visuals and retained narration. Preserve publication;
   sampled frames, complete decoding and actual audiovisual listening are distinct.
   Correct AT chronology: earlier OFF restoration predates later owner activation
   and failed disable. Owner authorization exists; the tool permission handoff
   failed without an owner-visible prompt. Current setting/spoken output are not
   verified. Use a supported capability inventory or human-operated procedure;
   never bypass restrictions or infer missing conversational permission.
5. Prepare actual screen-reader and unfamiliar-participant tasks using current,
   clearly labelled controlled slow/failure fixtures without provider calls. Retain
   H/AT as incomplete until actual observations exist. Check for a legitimate
   owned active unresolved case; never restore expired ownership or create a paid
   failure to obtain panel evidence.
6. Only after separately authorized A and independent post-verification, refresh
   Operation B as a separate owner decision: third identity first, then SFA A/B,
   at most three sequential generations and associated token counts, no retries,
   unchanged configuration and reservation, stop on first failure/unknown/drift.
   Available capacity is neither authority nor exclusive validation capacity.

The lifetime ceiling and existing pools remain unchanged. No build/deployment is
planned. Any later publication receives applicable exact hosted checks and private
content scanning; application-source identity remains separate from documentation
head. Existing historical broader U18 gates and Git-history disclosure limitations
remain open. This checkpoint changes execution preparation and evidence chronology,
not accepted scope or completed implementation.


### Resumption verification and disposition

Fresh real-service reads confirm the same application source/image, 100% serving
revision, runtime/IAM, both-host assets and support configuration. Remote PR15/16
and their checks remain successful; documentation main is not packaged source.
The initial refreshed accounting inventory retained both liabilities and terminal
failed/timed-out runs. After the explicit A-only decision, independently verified
readback records the newer retained usage and releases its excess reservation. The
older liability and all seven protected records, including failed runs and expired
ownership, are unchanged; no extraction completion or action was created. Shared
public capacity reopened and is not reserved for validation. No legitimate active
owned unresolved case was available. Newly observed empty
workspace records are unattributed public activity, not our model tests. Exact
ledger values/versions remain private. No provider call or email occurred in this A phase; the later B2 result is recorded below.

The R12/F8 preparation gap is corrected privately:31focused fake-SDK checks,
21independent fake-SDK checks and3actual loopback emulator cases verify exact
transaction guards, two-document write scope, replay and lost-acknowledgement
readback. Independent review confirms cache-aware rollback compatibility. This
preparation was followed by explicit owner authorization for Operation A only.
Focused dispatch-binding tests and independent review preceded the single guarded
transaction. Authoritative readback and an independent complete inventory verify
the exact postimage and absence of unrelated changes. An acknowledgement alone was
not treated as completion. This does not close F8 model acceptance. Operation B
was then separately authorized with unchanged limits and negative case first; its chronology follows below.

Current-source controlled human fixtures are prepared for delayed success,
identity-evidence refusal, unresolved accounting and upload error. Their fake-service
verification passes. Agent-operated browser checks observed immediate saving and
checking feedback, completion, unchecked consent, simulated action, queue/reopen
and reload. This is C/B evidence only. The fixture uses a disclosed simulated
clock; it is not deployed/model, screen-reader speech or novice-human evidence.
The prior defective baseline fixture remains retained and must not be reused as
the current candidate. The owner subsequently operated the success fixture and
reported VoiceOver enabled but no speech during the requested actions. Record this
as an observed AT failure with cause unlocalized, not a pass or yet a demonstrated
application defect. The follow-up reports silence on other webpages too and no speech after a manual
settings check. Ordinary AT output remains unestablished; exact browser/version,
spoken output and remaining tasks are still missing. First-time H participation remains unavailable. A supported
inventory was read; no native app retries or accessibility-setting changes were
made. Human tasks and moderator setup are in the private handoff.

All twenty rows above retain their acceptance criteria and current classifications.
R01/R04/R08/F8 remain incomplete after the failed U38 model case; further changed evaluation requires new authority; R02/F1/F2/F6
require actual AT; R03/R05/R06/R10 and relevant journey/recovery rows require novice
observations; R07/R09/F3/F4 retain the unavailable legitimate live-panel dependency.
F5 controlled coverage and completed implementation stay accepted. R11/R12 recovery,
review and truthful evidence reconciliation are updated, with dependent gates open.
Further F7 cosmetics remain advisory. Full judge reproduction and full product
readiness are not certified; the narrower U18 scope and broader historical gaps
remain distinct.


### Operation B execution checkpoint

Operation A passed independent post-verification. The refreshed private B manifest
and primary/backend/security reviews bind exact existing samples, historical SFA
source, model/prompt/deadlines, rate evidence, call/commitment ceilings and stop
conditions. U37 records explicit owner authority. Fresh admission precedes one
owned workspace and each sequential case: third identity first, then SFA A/B.
Independent content and accounting verification must pass before advancing;
wrong extraction, refusal, timeout, uncertainty or failed admission stops the
series. No call result is inferred from the approval or the accounting repair.

The owner additionally reports VoiceOver silent on other webpages. Working AT
output is not yet established; no application-specific cause is demonstrated.
The owner reports settings correct but continued silence after the supported
manual check; the precise cause and versions remain unknown. No agent setting
change or permission bypass occurred. Actual AT acceptance remains incomplete.


The first U37 pre-call guard stopped the series before token counting or generation:
the retained PNG byte hash differed from the proposal's locally encoded hash.
Independent version-bound storage reads and decoded-pixel comparison prove the
correct approved label pixels, not a changed product image. Classify this as a
REQUIRED_CONTRACT private operation-manifest preparation defect; the exact encoder
cause remains unproved. Preserve the original failed guard and zero-call outcome.
A corrected proposal must bind fixed approved pixels and actual retained bytes with
ownership/object-version provenance, retain the existing workspace/capture and all
limits, and obtain a fresh explicit decision. No silent hash rebase or restart.


U38 separately authorizes the corrected private B2 packet after primary and
independent capture/authority review; 23 focused verifier checks pass. Fixed
approved original/pixel hashes, current owned capture, version-conditioned storage
reads and immutable actual server-byte bindings replace the erroneous universal
encoder assumption. Same workspace/capture, original absolute window and combined
limits remain. Fresh immediate guards must pass before the sole third-case dispatch,
and independent actual content/accounting review precedes any next case.


### B2 execution outcome and current closeout

Fresh exact capture/version, source, configuration, ledger and ownership guards
passed. One explicit extraction started one actual generation; associated token
counting is supported by the unchanged guarded runtime path, without a separately
retained raw count response. The complete provider response included the printed
subtitle “Invented third identity” in the product name. Pack, lot/date and reviewed
source translation were consistent, but the name failed the retained-identity
check. The application displayed “Extraction needs review,” explained that the
identity disagreed and created no comparison or action. This is a REQUIRED_CONTRACT
model-acceptance gap with a working protective refusal, not a passing deterministic
nonmatch or a trust bypass. The model's internal reason is unproved.

Independent content/accounting review confirms automatic original-rate settlement,
no new unknown liability, preserved older hold and all unrelated records/versions.
The series stopped at this first failure. No SFA A/B attempt or retry occurred;
unused slots are not permission to continue. Existing failed evidence, including
local analysis-helper errors, is retained. Future model-field correction or changed
evaluation requires a bounded reviewed proposal and new paid authority; do not
change the label/prompt/model to evade this stop.

Real browser observations verify immediate processing, disabled duplicate controls,
truthful refusal, evidence image, queue with zero actions, reopening, reload and
phone context. Both hosts still serve the exact unchanged application assets and
configuration. No legitimate owned unknown-request panel became available: this
failed extraction settled normally. Lingering upload-specific next-step wording
is advisory ambiguity; the active result is truthful. Actual AT remains blocked
by silent general VoiceOver output and H by missing unfamiliar participation.
Recognizable video workflow and controlled positive coverage remain supported;
fresh full judge reproduction and full product readiness are not established.


### Unpaid third-label correction checkpoint — 26 October 2026

The owner authorizes unpaid root-cause diagnosis, smallest offline correction,
regression and independent review after the stopped U38 case. No new generation,
token count, retry, settlement or deployment is authorized. Primary remains sole
integrator; the clean integration branch starts at PR17's merged tree. Root edits
and all original sample/video/failure evidence are preserved.

1. Reconstruct the available canonical request from retained source/capture, exact
   effective prompt and schema, then compare its digest with the stored attempt.
   Distinguish canonical JSON identity from unavailable original wire serialization.
2. Trace the observed two-line name and box through schema, translation and unchanged
   identity guard. Classify field-selection failure separately from hypotheses about
   layout/prompt influence and unknown model-internal reasoning.
3. Independently review a general product-name field-selection clarification. Preserve
   genuine multiline names, raw/value equality, ambiguity handling and all trust
   rules. No name trimming, fuzzy guard, answer injection or sample alteration.
   Prepare the exact inert prompt candidate through the existing typed configuration
   boundary; do not activate a new prompt or runtime by publishing tests.
4. Add focused unpaid regression for the observed failure and positive/negative
   controls, verify the candidate reaches the sealed mock ADK request, and distinguish
   mock outcomes from model efficacy. Privately replay exact retained bytes.
5. Prepare the precise changed experiment and compatible activation/rollback needs
   before any owner decision. Keep the original series stopped and preserve pools,
   older liability and lifetime ceiling. No alternate ledger/workspace bypass.
6. Refine human/AT procedures and observation records without setting changes or
   repeating failed native access. Filmed protective refusal and successful
   deterministic nonmatch remain separate acceptance claims.

Exact candidate, tests, request reconstruction and specialist reviews are private
under `.local/run-records/third-label-correction-20261026/`. Publication of authorized
regressions/documentation receives exact hosted checks and privacy scanning; any
future runtime activation must receive its own reviewed concrete operation.


### U39 correction checkpoint outcome

All 20 rows above were reconciled against the unchanged deployed application and
new offline evidence. R01/R04/R08/F8 retain the model-acceptance gap; the exact
canonical request and retained response now substantiate the field-selection cause.
The candidate reaches sealed mock ADK requests but its model efficacy is unproved.
R02/F1/F2/F6 retain actual AT; R03/R05/R06/R10/F7 retain first-time H; R07/R09/F3/F4
retain the legitimate live-panel dependency. New controlled resolved-recheck coverage
does not fill that S gap. R11/R12 now include independent diagnosis, correction,
private transaction/rollback preparation and exact publication checks. F5 and all
completed trust/ownership/consent controls remain unchanged. No requirement was
waived or downgraded; M9 separates all evidence types.

The prompt candidate is test-only. A future activation needs its concrete owner
decision, fresh current admission and reviewed exact mutation bindings. Forward and
inverse migration both require zero active owners; the inverse additionally forbids
unknown candidate usage. Only budget policy/grant hashes change, with all documents
read/guarded transactionally. No active or expired guest metadata is rewritten.
After a future one-case experiment, retain candidate configuration with paid phase
closed while any owner is active or candidate liability unknown; no unconditional
rollback, scheduled retry or session expiry is claimed. Private REQUEST.md records
one changed experiment, exact limits and public availability consequences.

Actual screen-reader preparation now includes a separately labelled controlled
unresolved-to-settled-failed transition and moderator procedure. The owner-operated
silent-baseline observation is preserved; no additional permission is needed, but
ordinary screen-reader output must work before attributing missing announcements
to the app. An unfamiliar participant remains necessary for the uncoached walkthrough.
No human completion is inferred from agent fixture review.

# BatchBeacon: consolidated user-journey audit and correction plan

25 October 2026 · Baseline audit and accepted implementation specification.

Implementation status and remaining gates are tracked in [M9](evidence/M9-user-journey-correction.md). The observations below preserve the original audit; they are not a claim about the corrected candidate or current release.

**Verdict:** the filmed workflow exists, but current progress, stage guidance and recovery controls do not yet support a dependable unaided judge walkthrough. A successful upload can look like nothing happened. Some recovery controls offer operations the server correctly rejects. Preserve the video’s recognizable workflow and repair these boundaries together.

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

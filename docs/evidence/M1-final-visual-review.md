# Consolidated visual review candidate

Current palette/control-spacing addendum: [M1-palette-final](M1-palette-final.md).
The original captures and hashes below remain the earlier review record.

Status: recommended for owner visual review; U02 remains open. This is a reversible
local prototype, not a release candidate or an integrated product acceptance.

The owner requested one thorough review across the entire design discussion.
Original Impeccable 4.6 context was already initialized in this design session;
its polish playbook and craft floor guided this pass. Technical audit dimensions
were used as a checklist, without claiming a formal accessibility certification
or a complete scored audit. Two independent read-only reviewers checked source,
behavior and rendered evidence. The primary retained sole write responsibility.

## Candidate and rationale

- Rich dark blue `#173B75` gives the paired-label B and wordmark clearer color and
  definition. Coral `#F05A36` preserves the second label. Geometry represents the
  product evidence and authority record being aligned, not a safety seal.
- Vibrant gold `#FFBF00` identifies the next deliberate action. Dark navy text and
  a visible border preserve readability. White keeps evidence dense but legible.
- Pale blue frames label evidence; lavender/violet distinguish candidate wording.
  Mint returns for completed simulated holds and guidance changes. A scoped
  negative stays neutral; green does not indicate food safety or sale clearance.
- Desktop retains the selected evidence workbench and persistent header. Phone
  retains the destination row while scrolling and offers Label/Evidence/Decision
  jumps. No intercepted scrolling, snap effects or new decorative animation.
- Native controls, full selection boundaries, underlines, explicit state words,
  pressed/current semantics and deliberate consent keep choices identifiable.

## Inspect the candidate

Local interactive workbench: `http://127.0.0.1:8765/prototype/refined/`.
Identity study: `http://127.0.0.1:8765/prototype/refined/brand.html`.

| Surface | Desktop | Phone |
| --- | --- | --- |
| Workbench | [Full page](../ui/final-candidate/workbench-desktop.jpg) | [First view](../ui/final-candidate/workbench-phone.jpg), [selected evidence](../ui/final-candidate/evidence-phone.jpg) |
| Retail queue | [Full page](../ui/final-candidate/retail-desktop.jpg) | [Full page](../ui/final-candidate/retail-phone.jpg) |
| Guidance confirmation | [Full page](../ui/final-candidate/guidance-confirmation-desktop.jpg) | [Full page](../ui/final-candidate/guidance-confirmation-phone.jpg) |
| Completion | [Activated guidance](../ui/final-candidate/guidance-completed-desktop.jpg) | [Held history](../ui/final-candidate/held-phone.jpg) |
| Identity | [Full page](../ui/final-candidate/brand-desktop.jpg) | [Full page](../ui/final-candidate/brand-phone.jpg) |
| Other decisions | — | [Hold confirmation](../ui/final-candidate/confirmation-phone.jpg), [scoped negative](../ui/final-candidate/negative-phone.jpg) |

## Reproduced findings and disposition

| Finding | Classification and demonstrated impact | Correction and verification |
| --- | --- | --- |
| Skip link changed retail/guidance to workbench | REQUIRED_CONTRACT: keyboard destination violated NF-06. A rapid route/skip sequence also exposed queued hash-event ordering. | Preserve the current view for section anchors; consume each hash event's new URL. Independent pre-fix reproduction and 120 rapid post-fix trials; sequential and deterministic regression cases. |
| Empty queue reset lost focus to body | REQUIRED_CONTRACT: hidden reset button interrupted keyboard recovery. | Return focus to the visible queue filter; browser regression and independent verification. |
| UK product code labelled lot/batch in extracted fields | REQUIRED_CONTRACT: typed-code meaning violated AC-08. | Scenario-specific Product code / Lot / batch accessible label; both UK cases and SFA return verified. |
| All-date notice requested date recapture | REQUIRED_CONTRACT: unnecessary evidence request violated AC-09. | Explain that a date panel is not needed; remove that recapture control for the two UK examples. Missing-date SFA capture remains available. |
| Held history and negative inherited a pending-confirmation heading | ADVISORY_DEBT: conflicting next-step copy in a non-persistent prototype. | Completed history says Recorded example; negative says No hold supported; missing/failure name the required recovery. Regression and final visual inspection. |
| Guidance progress and comparison labels were ambiguous | ADVISORY_DEBT: current step lagged the displayed task; current v1 contradicted active v2. | One current Candidate/Evaluation/Confirmation/Active step; fixed Baseline/Candidate comparison labels. Browser regression and independent inspection. |
| Previous confirmation message remained during a new dialog | ADVISORY_DEBT: stale feedback, not a reproduced new false confirmation in installed Chrome. | Hide old feedback and clear dialog return value before opening; Escape and Go back restore focus without success feedback. |

All reproduced required findings were independently verified after correction.
The final visual reviewer inspected all 13 captures and recommends owner
presentation, with no reproduced regression or media publication concern.
Private reproduction/failure logs are retained in the ignored local evidence store.
No source predicate, contract implementation or approval authority was changed.

## Verification and limits

Locked local check: lock validation, Ruff, 118 unit tests and 36 browser tests PASS
in installed Chrome. The earlier full run found the queued skip-link race; that
failed report is retained, followed by the corrected full pass. A final narrow
state-title change passed all seven affected-test follow-up cases. The refined suite
contains 32 cases; four additional cases cover the archived prototype.

Rendered review covers 1440×1000 and 390×844 viewports, with full-page captures
where useful. Automated reflow covers 320/390/720/1280/1440; independent additional
breakpoint checks cover 760/761/800/900/1190/1191. Keyboard selection, native modal
consent/cancel/focus return, skip/queue recovery, guidance activation/rollback,
missing/stale/negative/failure examples, reduced motion and rendered text contrast
were exercised. The bounded Impeccable layout detector returned zero findings;
that result is distinct from visual judgment. No browser errors were observed
in the manually inspected workbench/guidance path.

| Color pair | Contrast |
| --- | --- |
| Rich brand blue / white | 10.94:1 |
| Navy / gold action | 9.19:1 |
| Violet / lavender | 6.12:1 |
| Completion green / mint | 7.32:1 |
| Completion boundary / mint | 3.78:1 |

The main surface is approximately 55 KB of uncompressed HTML/CSS/JS/SVG with no
external fonts or UI libraries. This is source inspection, not a measured network
performance, uptime, load or adoption result. No real-user usability study ran.

Native 200% browser zoom could not be verified with the available browser control;
viewport reflow is not a substitute. Hardware touch, screen readers, other engines,
real camera capture, live model/persistence, service availability and full integrated
accessibility remain unverified. The candidate shows honest prototype states and
makes no saved-action or evaluated-learning claim. Final DESIGN/integration waits
for U02; UK/remaining human source review, final-case custody and submission gates
remain separate.

## Reviewed source binding

- `index.html`: `69988051bbb62ae49d29f029a7559d5bddd08e0e7aa2cedf1056dfa226746bcf`
- `style.css`: `f7616f7bd3fb753ed1c94cca12288975c12ee85703f95b9580224f4f1f5bf6f2`
- `prototype.js`: `d250cfb51cb412fe34055296743825be41fedf7f5e76364922f3cd8398314122`
- `brand.html`: `f14eb146486e937599a82d26e92bc815ebeaa56eb536d253e8ced6468d7676b5`
- `mark.svg`: `91de6636356363512a9c5809a2e0ccea3410f8a384f46367b186d043ca835b0a`
- `mark-mono.svg`: `63cbe564af08a25f212295e5588529b5b64a2881fe0a337c20148ec8b4cfac12`

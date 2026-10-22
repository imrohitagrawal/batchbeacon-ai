# Focused retail UI usability audit and correction

Status: planned, not completed. The owner reported clutter and unclear controls
on Capture guidance after submission. Earlier functional, keyboard, reflow and
selected visual checks do not establish a complete usability audit or a human
first-time usability study. U23/U24 repair access and immediate clarity; they do
not close this activity. U26 subsequently replaces repeated synthetic/demo UI
terminology with Evaluation workspace and Non-production data, while preserving
action-effect disclosures. It does not close the broader hierarchy/layout audit.

## Initial findings, not a completed audit

Inspection of the owner's screenshot, current guidance rendering and the deployed
empty-shop desktop view supports these starting findings:

- No investigation is selected, but the page exposes all later workflow controls.
  The empty state needs a prominent route to checking or reopening a product.
- The active wording, proposed wording, quotas and later-stage actions compete
  for attention before the visitor knows which action is available.
- Generic prerequisite copy does not explain each individual disabled action.
- Identifiers such as GUIDANCE V1 and terms such as fixed evaluation require
  explanation or lower visual priority for a first-time judge.
- Existing mobile CSS hides the guest-session expiry label below 760px. Make
  session status discoverable and verify its actual visibility on narrow screens.
- The successful refresh message uses the shared amber notice treatment. Success,
  warnings and failures should have distinguishable semantics and presentation.

These are reproduced clarity findings for the next layout correction, not proof
that every state or page has been audited. The current deployed desktop view has
more spacing and grouping than the original screenshot, but the workflow remains
long and exposes unavailable future actions.

## Scope and acceptance

Start with Capture guidance, then verify navigation into it from Check a product
and Retail queue on desktop and mobile. Preserve the approved Evidence in focus
visual direction, synthetic scope, server eligibility, explicit confirmations and
all ownership/budget controls. No new model calls are required for the audit;
local controlled fixtures cover the lifecycle states.

1. A first-time visitor can explain the page purpose, whether it applies to their
   current investigation, and the next available action from the opening view.
2. An empty shop has a clear route to checking a product. A selected investigation
   is identifiable. Do not show technical counters as the main starting point.
3. Show one primary next action per stage. Group supporting controls, reveal later
   steps as relevant, and give nearby reasons for unavailable actions. Preserve
   access to historical records and rollback when applicable.
4. Refresh shows loading, successful completion, unchanged records, failure and
   historical-data status clearly. It must not imply generation or evaluation.
5. Explain feedback, proposed wording, evaluation and confirmation in ordinary
   language. Put identifiers, quotas and execution detail behind accessible details
   where they are not needed for the current decision.
6. Test empty, eligible, feedback recorded, proposal, evaluation running/failed/
   passed, active, rollback, expired guest, failed load and uncertain-operation
   recovery states. Preserve all server prerequisites and confirmation boundaries.
7. Verify desktop and narrow mobile layouts, keyboard focus, screen-reader names,
   readable spacing, wrapping and touch controls. The mobile example shortcut
   should be understandable as navigation to the same examples.

## Evidence and delivery

Produce a prioritized findings register with reproduced state, impact, smallest
correction and acceptance. Independently review the implementation and run
appropriate regression, hosted and deployed checks before release. Keep private
screenshots and run details ignored; publish only sanitized findings. Report
expert inspection, automated checks and actual human usability observations
separately. A human usability study is not claimed unless it actually occurs.

The requested layout correction is authorized; this plan is not evidence that
an audit ran, a redesign shipped, or a background task was scheduled. Any later
cloud release must retain the existing finite service and spending boundaries.

## Scoped execution update

The [video-parity repair](evidence/M7-judge-readiness.md) implements contextual guidance eligibility, an empty-state route to checking a product, selected-investigation history, later-stage disclosure, queue invalidation and visible mobile expiry. Local controlled desktop/mobile checks and independent review passed. This does not close the entire lifecycle usability matrix above or constitute a human usability study. Current positive real-AI journeys and failure recovery passed; the unrelated-label provider failure leaves full parity incomplete, as documented in M7.

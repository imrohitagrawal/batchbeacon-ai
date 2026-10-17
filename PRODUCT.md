# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated implementation choice under kickoff: one Python FastAPI application,
Jinja templates and native CSS/JavaScript; bounded Google ADK/Gemini extraction,
deterministic verification, Firestore, private image storage and Cloud Run.

## Users and tasks

BatchBeacon AI helps a retailer review a synthetic product label against a small,
reviewed SFA Singapore / UK FSA recall corpus. Identity precedes batch comparison.
The user inspects evidence, resolves a missing panel, reviews an honest scoped
result and deliberately records a simulated hold or human-review request.
A session-owned shop console prioritizes incidents; an evaluated, explicitly
confirmed guidance change can improve subsequent capture instructions and be
rolled back. Technical operations remain private and separate.

## Constraints and terminology

Canonical truth is in specs/mvp.md, specs/retail-operations.md and
docs/OWNER_DECISIONS.md. This adapter does not replace those contracts.
AI proposes extraction; deterministic server policy owns decisions and action
eligibility. Unknown and stale evidence cannot imply clearance. All shop data,
labels and actions are synthetic. No contamination, safe-to-eat or release claim.
Two genuine authorities and a genuine UK source update remain required.

## Accessibility and visual decisions

The owner approved the current Evidence in focus treatment on 18 October 2026.
U02 / UI-SELECTED is complete; see docs/evidence/M1-visual-approval.md for the exact
artifact and scope. Root DESIGN.md captures the approved visual system and governs
faithful implementation. The system uses rich blue/coral identity, vivid gold
primary actions, peach selection, pale-blue evidence and secondary controls,
lavender proposed guidance and mint completed simulated workflow states.

Operational web interface: readable desktop and phone capture, keyboard focus,
contrast, visible control boundaries, touch targets and reduced motion. Selection
and outcomes must be understandable without color. Mint denotes a completed
simulated workflow step, never product safety or permission to sell. Persistent
navigation and explicit recovery support task continuity. Visual recognition of
actions is a first-class review concern alongside technical accessibility checks.

The user requires a current, carefully finished interface whose purpose is clear
at first glance. Apple, MakeMyTrip, Cleartrip and Google are quality references;
Stackclimb navy/coral and Impeccable soft colors/gold informed the chosen palette.
They are not instructions to copy brand assets. The supplied Impeccable screenshots
were affirmative color references, not a new list of prohibited patterns. Detailed
UI/UX judgment is delegated. Keep the paired-label B mark and the approved system.

Earlier rejected treatments and palette evolution remain in docs/evidence/ and
prototypes/. Do not reopen those choices or repeat the design questionnaire.
The usability audit, corrected state paths and evidence limitations are recorded
in docs/evidence/M1-usability-audit.md. No accessibility certification, native-zoom,
screen-reader or physical-device pass has been claimed. T17 still requires real
application integration and running-UI verification.

SFA first-slice human source review is complete. Remaining UK/development-gold
review, protected final-case custody and final submission approval remain open.

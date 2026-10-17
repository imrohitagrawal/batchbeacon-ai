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

Operational web interface, readable desktop and phone capture, keyboard focus,
adequate contrast, touch targets and reduced motion. Workflow A is accepted in
principle; its previous finish was rejected. Replacement visual approval remains
open, as do completed human source review and final submission approval.

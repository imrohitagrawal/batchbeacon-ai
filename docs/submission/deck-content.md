# BatchBeacon AI — prescribed deck copy plan

Preparation only. This is editable copy mapped to the organizer's original
16-slide template, not a completed presentation, final performance report or
submission. Evidence basis: the T35 pure-evaluator checkpoint and the linked
scope records below. Refresh actual capability claims before final authoring.

The authorized working template retains the 10 × 5.625 inch canvas, original
masters, black organizer header, logos and typography. Downloaded originals and
the unedited working copy remain private. All 16 original pages were inspected.
No shared organizer document was modified.

## 1. Team Details

Product: BatchBeacon AI

Team name: use the exact registered team name after checking the authenticated
entry. The product name does not establish the registered team name.

Team leader: Rohit Agrawal

Members: Aayushi Priya, Niharika Aggarwal, Priyanca Shelke

Problem statement: Retail & Commerce: Intelligent Customer and Business Experiences

Source: [owner-attested roster](../OWNER_DECISIONS.md),
[approved brief](../../HACKATHON_BRIEF.md). Preserve the organizer's heading and
artwork. Final roster parity remains a platform check.

## 2. Download instructions

Organizer instruction page. Retain unchanged in the working copy. Exclude from
the final audience export after confirming that content slots remain complete.
It instructs participants to download and edit locally, not request shared edits.

## 3. Brief about the idea

BatchBeacon AI helps retail staff compare a product label with official recall
evidence and prepare an action for a manager to review.

A lot number alone is insufficient. The product identity, pack, applicable date
and jurisdiction must agree with the notice. Missing or changed evidence keeps
the result in review.

Initial scope: selected Singapore SFA and UK FSA notices, with synthetic labels
and simulated stock actions. The app is under implementation.

Source: [product scope](../../specs/mvp.md),
[current status](../STATE.md). This states intended product behavior and bounded
coverage. It does not claim worldwide monitoring or deployed completeness.

## 4. Opportunities

Retail staff need a clear connection between the package in front of them and
the exact conditions in an official notice.

BatchBeacon's proposed distinction is the combined workflow: identity before
lot comparison, targeted evidence recovery, source-version checks and explicit
manager confirmation. Existing products already offer scanning, alerts and
recall matching. The individual features are not claimed as inventions.

Hypothesis: this workflow can make a recall investigation easier to inspect and
resume. User benefit and performance against a competent one-shot model baseline
remain unmeasured.

Source: [brief innovation thesis and comparators](../../HACKATHON_BRIEF.md).
Do not imply a fresh competitive benchmark or superiority over named products.

## 5. Features offered

| Feature | Demonstrated status |
| --- | --- |
| Identity and field comparison with explicit uncertainty | Local deterministic implementation and tests |
| Owned evidence history and simulated approval rules | Local adapters, injected HTTP and tests |
| Product workbench, retail queue and capture guidance | Owner-approved visual prototype |
| Currentness-first queue rows and counts | Pure supplied-snapshot computation |
| Allowlisted guidance evaluation | Six actual fixed cases under both policies |
| Connected model, saved queue and guidance activation | Runtime integration incomplete |

Source: [state](../STATE.md), [queue](../evidence/M2-retail-projection.md),
[evaluation](../evidence/M2-learning-evaluator.md). At final authoring, replace
this implementation-state table with the actual delivered feature set and its
remaining limits. Do not promote a prototype control to a working backend.

## 6. Process flow diagram or Use-case diagram

Editable diagram content, to be authored in the existing slide:

1. Staff opens an isolated synthetic shop and selects a product example.
2. Staff captures label evidence for the selected jurisdiction and notice.
3. The bounded model workflow proposes extracted fields.
4. Server code checks identity, source support, conditions and currentness.
5. Missing evidence requests a specific follow-up within remaining allowances.
6. Supported evidence allows the manager to review a simulated action.
7. Changed source or observation requires renewed review before another action.

Label the diagram “Intended connected workflow”. The local injected journey and
visual prototype exercise portions of it. Actual deployed model execution is
still pending. Never draw an automatic path from model output to stock mutation.

Source: [MVP journeys](../../specs/mvp.md),
[coordinator scope](../evidence/M2-extraction-coordinator.md).

## 7. Wireframes/Mock diagrams

Use the owner-approved Evidence in focus workbench and phone evidence view from
the usability capture manifest. Preserve all visible simulation labels.

Caption: “Approved visual prototype. Runtime integration is in progress.”

Source: [visual approval](../evidence/M1-visual-approval.md),
[capture manifest](../ui/usability/manifest.json). Do not use an earlier rejected
palette or direction. Do not imply that screenshots demonstrate deployed flow.

## 8. Architecture diagram

One application service contains the web interface, bounded ADK workflow,
deterministic verifier, session ownership and simulated-action controls.

The intended deployment uses Cloud Run. Gemini proposes extraction. Firestore
stores owned records and policy state. Private Cloud Storage retains sanitized
label images for the bounded retention period. Authority notices enter through
an allowlisted, versioned evidence boundary and human source review.

Trust distinction: server rules own comparison, currentness, limits and action
creation. Model output and user input remain untrusted proposals.

Diagram labels must distinguish locally implemented adapters from services that
have not been provisioned or exercised under the deployed identity.

Source: [architecture](../EXECUTION.md), [external status](../STATE.md).

## 9. Technologies

| Technology | Responsibility and observed scope |
| --- | --- |
| Python, FastAPI and native web templates | Local application and interface |
| Google ADK and Gemini | Bounded extraction workflow, installed SDK and mock transport checked; actual model call pending |
| Firebase / Cloud Firestore | Owned persistent records; SDK and local emulator checks, actual service sign-off pending |
| Cloud Run | Intended application hosting; deployment pending |
| Private Cloud Storage | Sanitized image retention; local adapter checks, deployed identity checks pending |
| pytest and Playwright | Automated domain, boundary and prototype-browser checks |

Do not claim Firebase Authentication, Firebase Hosting, a second runtime or
services that are not part of this implementation.

Source: [state](../STATE.md), [runtime scope](../evidence/M2-model-runtime.md).

## 10. Estimated implementation cost

Optional template slot. The owner approved a finite ₹6,000 incremental cloud
envelope through the funded period. This is a spending ceiling, not a measured
cost per check or a forecast of production economics.

Actual model cost, warm/cold latency and complete service overhead remain
unmeasured. Paid admission is closed while required billing bounds and prior
liabilities remain unsubstantiated.

Source: [approved budget and pools](../OPERATIONS.md), [status](../STATE.md).
Final slide should use actual bounded measurements if available, or state that
cost evaluation remains pending. Do not manufacture a low per-check estimate.

## 11. Snapshots of the prototype

Use the approved workbench, recapture and confirmation captures. Label them
“Visual prototype”. Keep captions about the visible task:

- Compare the label with source evidence.
- Request the missing panel.
- Review a simulated action before confirming it.

Capture a fresh genuine source-update state only when the connected flow works.
Do not pass a staged prototype or synthetic backend fixture off as a real model
result. Re-capture source-context additions if they form part of the final demo.

Source: [approved captures](../ui/usability/manifest.json),
[source-context scope](../evidence/M1-recall-context-verification.md).

## 12. Prototype Performance report/Benchmarking

| Evidence | Result and denominator |
| --- | --- |
| Local automated suite at the evaluator checkpoint | 1,233 unit cases and 50 prototype-browser cases passed |
| Fixed guidance evaluation | Six grouped cases, nine variants, 18 branch executions; baseline and candidate both passed |
| Guidance output size | One actual run produced 14,814 response bytes within the 16,384-byte bound |
| Real Gemini extraction quality and baseline comparison | Not run |
| Deployed six-journey, latency and cost measurements | Not run |
| Human final-case evaluation | Pending protected custody and execution |

Automated test counts are not product accuracy percentages. The six guidance
cases are separate from the development and final-case datasets. No uplift,
enterprise reliability or safety certification follows from these checks.

Source: [evaluator evidence](../evidence/M2-learning-evaluator.md),
[evaluation registry](../../specs/mvp.md). Add the exact tested release revision
and hosted result at final assembly. Preserve failures and limitations.

## 13. Additional Details/Future Development

Future evidence exploration could filter a reviewed corpus by recall reason,
hazard and symptoms explicitly mentioned by an authority. Distinct recall
events, notice updates and affected products would remain separate counts.

Broader historical coverage requires reviewed identity linkage and a defined
coverage period. Continuous ingestion, ERP integration and production stock
actions are outside the current demo.

Source-linked company notices directly support the existing evidence workflow.
Their exact version and unreviewed attachment status must remain visible.

Source: [recall analytics proposal](../RECALL_ANALYTICS.md). This is a future
proposal, not implemented filtering or a claim about observed illness cases.

## 14. Links

Public repository: https://github.com/imrohitagrawal/batchbeacon-ai

Demo video: pending actual exported and reviewed recording.

Final product: pending actual deployed and verified URL.

The template says “3 Minutes”. Owner U01 authorizes a 160-second core and a
230-second submission cut under the documented source conflict. Recheck the
current form and measure the actual export. Do not submit placeholders or
localhost addresses.

Source: [decisions](../SOURCES.md), [U01/U16](../OWNER_DECISIONS.md).

## 15. Blank content page

The downloaded page has the standard header and an empty white body. No hidden
text requirement was found in the PPTX text structure or visual render. Preserve
it in the working source and omit from final audience export if unused.

## 16. Closing page

Keep the original organizer “Thank you” artwork and proportions. It contains no
additional BatchBeacon field to fill. Do not replace organizer branding with a
new product illustration.

## Final assembly checks

The presentation still needs an admitted authoring runtime, complete copy fitting
and editable diagrams, fresh candidate screenshots, actual product/video links,
final evidence and human submission review. Validate every filled slide against
the original, clickable links, accessible legibility and English copy. Export a
PDF below 4,900,000 bytes and inspect every page before it can become a submission
artifact. This copy plan does not satisfy T27 final sign-off.

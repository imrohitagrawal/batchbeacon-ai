# BatchBeacon AI — draft judge guide

Preparation only. There is no verified hosted judge application yet. This guide
describes the planned evaluation route; it is not a report that the routes work.
Final URLs, timings and screenshots must bind to T26 before this becomes the
candidate's guide. See [current implementation status](../STATE.md).

## Purpose and scope

BatchBeacon helps retail staff compare a product label against selected official
recall evidence and prepare a reviewable simulated action. The demonstration uses
fresh synthetic labels in an isolated guest shop. Its source corpus is finite,
with selected SFA Singapore and UK FSA notices. Historical examples retain their
exact dates, versions and jurisdiction. This is not worldwide recall coverage.

An inconclusive or out-of-scope result stays in review. A scoped no-match does not
establish safety or permission to sell. No real inventory changes occur.

## Planned walkthrough

| Journey | What the judge should verify | Current delivery status |
| --- | --- | --- |
| F1: supported product | Actual model extraction, readable paired evidence, explicit confirmation and the same saved action after refresh | Local injected behavior and visual prototype checked; deployed journey pending |
| F2: same lot, different identity | The third synthetic identity cannot become a match from lot agreement alone | Deterministic local checks; deployed journey pending |
| F3: incomplete evidence | The app asks for a specific missing panel, retains revisions and stops recapture at its limit | Partial local rules and prototype; connected journey pending |
| F4: genuine source update | The actual UK update changes scope and makes the old result/confirmation historical | Source captured; human interpretation and connected journey pending |
| F5: retail queue | Counts, filters and reopened incident agree within the owned shop; refresh does not create a new check | Pure projection and prototype checked; persistent queue pending |
| F6: guidance learning | Actual fixed evaluation precedes explicit activation; later capture guidance changes; rollback restores content at a newer revision | Pure evaluator and prototype checked; owned lifecycle pending |

Both reviewed SFA cheese identities are positive source examples. The different
product counterexample uses a third invented identity. Do not relabel the second
SFA cheese as a negative example. The UK parent/attachment lot and date difference
is explicitly pending source review and must be resolved before final F4 guidance.

## Reading the evidence

The final app should expose the selected authority/version, applicable product
conditions and reason for recall alongside the label comparison. Additional
context must distinguish stated facts, missing information and unreviewed content.
Company notices retain their issuer and exact link. A health-risk statement is
not a report of illness in a checked item or a count of affected people.

Retail queue counts are incidents in the current synthetic shop. Future recall
analytics would need separate event/product/version definitions and a declared
corpus and period. It is not available as a delivered feature in this draft.

## Accessibility and recovery

The approved design supports visible focus, keyboard controls, labelled actions,
readable selection states, responsive layouts and explicit confirmation dialogs.
Prototype browser checks do not establish complete accessibility conformance.
Native zoom, screen reader, physical-device and connected-runtime checks remain
part of final validation.

Before release, record the actual behavior for expired sessions, unavailable
sources, exhausted allowances, delayed requests and saved historical evidence.
The judge guide must describe observed recovery paths, not invent a retry that
silently starts another billable attempt or a fresh lifetime allowance.

## Evidence and access to fill at release

Public repository: https://github.com/imrohitagrawal/batchbeacon-ai

Hosted application, approved video and deck: pending verified candidate artifacts.

The final guide must identify the exact release revision, supported browsers,
source versions, actual success/failure counts and measured runtime limitations.
Local tests, SDK mocks, emulator checks, model evaluation and deployed journeys
must remain separately labelled. No final-case answers belong in this guide.

Current references: [source scope](../evidence/M1-source-review.md),
[UI approval](../evidence/M1-visual-approval.md),
[queue computation](../evidence/M2-retail-projection.md),
[fixed evaluation](../evidence/M2-learning-evaluator.md),
[attachment review](../evidence/M1-attachment-inspection.md).

## Future scope

[The B0–B3 roadmap](../ROADMAP.md) records ATT-01: linked customer PDFs,
page-cited text/table extraction and reviewed product-image evidence. These are
planned capabilities; existing private attachment inspection is not an app feature.

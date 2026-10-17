# Replacement A treatment — owner review

**REVISION REQUESTED BY OWNER — NOT APPROVED.** This is a native HTML/CSS/JavaScript prototype, not
the final product or final DESIGN. Original A/B/C artifacts are preserved.

Open the running [local treatment](http://127.0.0.1:8765/prototype/) to switch
between the evidence workbench, retail queue and capture guidance. Every page
labels its synthetic/nonpersistent nature. Static browser captures:

| Surface | Desktop, 1440 px | Phone, 390 px |
| --- | --- | --- |
| Workbench / recapture | [Desktop](../ui/replacement-a/workbench-desktop.jpg) | [Phone](../ui/replacement-a/workbench-phone.jpg) |
| Retail queue | [Desktop](../ui/replacement-a/retail-desktop.jpg) | [Phone](../ui/replacement-a/retail-phone.jpg) |
| Guidance / evaluation / confirmation | [Desktop](../ui/replacement-a/guidance-desktop.jpg) | [Phone](../ui/replacement-a/guidance-phone.jpg) |

The treatment uses a dark green workspace rail, quiet light work surfaces,
aligned evidence comparisons and explicit semantic state text. Synthetic label,
authority evidence and next human decision are adjacent on desktop. Phone
comparison rows become readable paired evidence blocks; the queue becomes a
labelled incident list. Technical evidence stays secondary.

Actual inspections: desktop and phone screenshots through connected Chrome;
no horizontal overflow at 390 px. Four headless Chrome regressions pass against
a real local server: complete UK incident/source binding, deliberate confirmation,
targeted baseline + later changed guidance + increasing rollback preview, phone
reflow and queue semantics. These are prototype tests only, not runtime source,
action, learning, security or hosted acceptance.

## Targeted Emil review applied

| Before | After | Why |
| --- | --- | --- |
| Four compressed phone comparison columns | Paired evidence blocks, main values 14.1 px | Keep identifiers readable without horizontal loss |
| Queue advertised a table but used link rows | Labelled list and list items with incident links | Preserve coherent accessible navigation |
| Recapture/correction disclosures lacked expanded state | aria-controls and aria-expanded; native file input | Announce control state and preserve upload fallback |
| UK update text shared a Singapore record | Complete UK product/code/authority/market/incident binding | Keep source-update meaning visible and truthful |
| Generic capture baseline | Already-targeted date request; candidate adds glare/position advice | Do not manufacture an improvement through a deficient baseline |
| Policy label changed alone | Later example displays changed wording and rollback revision | Make the intended future effect inspectable without claiming persistence |

Primary reproduced the review findings and corrected the smallest boundaries.
Skill adaptation provenance correction was independently verified. Independent
verification of prototype corrections is running; final visual approval stays open.

Limits: no real extraction/upload, persistent action, real evaluator, isolation,
live currentness, actual counts or feedback storage. Mobile hardware camera and
full 200% zoom/contrast/a11y review remain later running-product gates. The local
server is a preparation process, not a public deployment or background guarantee.

Owner response: “Revise the treatment.” Targeted feedback requested; preserve this
version as review history. Independent technical recovery verified all four
prototype regressions; that does not grant human visual approval.

## Direction interview amendment

Owner feedback: generic AI dashboard; old appearance and inadequate enterprise
finish; unclear application purpose on first glance; off/obsolete colors. Desired
result: eye-catching yet calm, soothing deliberate colors and a distinctive layout.
Quality references: Apple, MakeMyTrip, Cleartrip and Google's color combinations.
The owner delegated the first-30-second experience and detailed design judgment.
These answers complete the first Impeccable shape interview round. They are not
approval of a replacement treatment. Original pinned init/shape/new-work guidance
is now loaded; executable direction-selection admission is being checked separately.

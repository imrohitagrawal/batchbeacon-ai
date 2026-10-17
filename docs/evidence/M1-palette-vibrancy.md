# Focused gold and violet refinement

Status: historical lighter-navy candidate; richer-blue refinement follows below.
Rendered palette refinement under owner-delegated design judgment;
technical and independent visual follow-up PASS. Final integration remains gated.

The owner confirms that everything else looks fine, asks whether the existing
identity is navy, prefers Stackclimb navy, requests a more vibrant yellow/gold,
and highlights the violet/periwinkle and purple-magenta family on Impeccable.
This narrows the open design decision to palette refinement. It does not accept
an unseen revision or close source review, runtime or final submission gates.

The live workbench wordmark computes to rgb(30, 37, 59), exactly #1E253B. The
upper label in the original mark is the same navy; the lower is #F05A36 coral.
The owner then found that navy too black at header size and delegated the
choice of a lighter navy. Use #34466F for the wordmark and upper logo shape;
it is an intentional adaptation, not a claim of an exact Stackclimb asset match.
Keep #1E253B for reading text/control boundaries and #F05A36 for the lower shape.
The Impeccable reference's icon fill was observed as
oklch(0.62 0.2 280) and yellow annotation as oklch(0.84 0.19 80.46).
These are affirmative color references, not instructions about the pictured UI.

Design judgment: calm navy structure with a more vivid golden action. Use
#FFBF00 (hover #EDB000) in the existing primary-action role, retaining navy text
and border. Use the violet family for proposed capture guidance: a pale #F1EDFF
surface and deeper #6243B5 label. This replaces the mint surface rather than
adding another equally prominent accent. The instruction body stays navy.
Gold consistently identifies the next action, including guidance confirmation;
violet identifies wording under consideration. Status words, selected outlines,
confirmation checkboxes and current-page cues remain explicit.

## Acceptance before verification

- Wordmark and upper mark use lighter navy #34466F; geometry/coral remain intact.
- Main action default/hover text meets 4.5:1 and has a 3:1 control boundary.
- Proposed guidance label/body meet 4.5:1 on the lavender surface.
- Phone and desktop workbench, guidance and identity render without clipping.
- Existing keyboard, selection, persistent-navigation and confirmation checks pass.
- No layout, product claims, action behavior or scrolling behavior changes.

Scope: reversible local prototype, no model or saved action. Original Impeccable
4.6 context was already initialized in this design session; colorize and craft
floor were loaded for this refinement. The owner delegated these color refinements after reviewing the layout. Record
that narrow delegation; do not invent approval of final runtime integration.


## Verified result

Six actual browser captures were inspected, at 1440×1000 desktop and 390×844
phone. The phone guidance view is scrolled to the proposed wording and action,
with the persistent destination row visible.

- [Workbench desktop](../ui/palette-vibrancy/workbench-desktop.jpg) and
  [phone](../ui/palette-vibrancy/workbench-phone.jpg)
- [Guidance desktop](../ui/palette-vibrancy/guidance-desktop.jpg) and
  [phone](../ui/palette-vibrancy/guidance-phone.jpg)
- [Identity desktop](../ui/palette-vibrancy/brand-desktop.jpg) and
  [phone](../ui/palette-vibrancy/brand-phone.jpg)

| Foreground/background | Contrast |
| --- | --- |
| Brand navy / white | 9.33:1 |
| Navy / gold action | 9.19:1 |
| Navy / hover gold | 7.82:1 |
| Violet label / lavender | 6.12:1 |
| Navy instruction / lavender | 13.23:1 |

The browser computed the action as rgb(255,191,0), with rgb(30,37,59) text and
border. Existing 21 refined browser checks PASS in installed Chrome. No new UI
behavior or tests were added for this token-only change. A bounded original-engine
layout scan using absolute source paths returned zero findings. An initial scan
with relative paths did not access the sources; its private failure is retained
and is not claimed as a pass.

A read-only independent reviewer inspected all six captures and source colors,
recalculated contrast and found no material regression. This is a continuation
review, not a fresh-context finish review or accessibility certification. Real
200% zoom, hardware/screen-reader checks and integrated runtime remain outstanding.
The owner delegated the final shade choice; no repeated palette questionnaire is
required. Preserve the existing final visual integration, human-source and
submission boundaries.

Reviewed source bindings:

| File | SHA-256 |
| --- | --- |
| style.css | `488d4d3a6077ba21ff664d2f553ddf4ac87b9f05380534067903c43c314a69c4` |
| mark.svg | `b808d390f28a581efc8e0f836a62ad77ad86a74cb0140eafc62d94ce0fd720a3` |
| mark-mono.svg | `08db004d243648bc6fb46ea7f3e4fc873bf736ebcc593877a6d7328588d0bb5b` |
| brand.html | `195df3909b157ba2793041b01fe7ff791b918f6143a186a7c0dac3f60a5c2f36` |


## Richer dark-blue identity follow-up

Owner found #34466F too dull and requested the darker blue side. Chosen #173B75
has more blue saturation and less gray; it replaces only the identity navy in
wordmark, color mark and single-color mark. The coral and current gold/violet
roles remain. The previous captures and reviewed hashes above are historical.
Acceptance: same geometry and dimensions; visibly blue at header/16px sizes;
body text on white >=4.5:1, phone canvas >=4.5:1; no clipping or new behavior.
Richer-blue follow-up PASS: four desktop/phone captures, independent visual
review and 10.94:1 white / 10.30:1 canvas contrast. Subsequently superseded by
the consolidated candidate, including restored mint for completed workflow states;
see [final visual review](M1-final-visual-review.md). Historical captures remain.

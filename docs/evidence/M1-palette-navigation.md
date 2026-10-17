# Palette and persistent navigation refinement

Status: owner requested refinement; provisional, no final visual approval.

The owner explicitly referenced color combinations in the supplied Impeccable
screenshot, including yellow/gold. That was an affirmative palette reference,
not a request to avoid the pictured colors or layouts. The primary's initial
interpretation was corrected. Later references supersede the earlier broad
exclusion of soft blue, mint and cream. The accepted Evidence in focus structure
and product behavior remain the basis of this refinement.

## Reference findings and product judgment

The live [Stackclimb](https://stackclimb.com/) page was inspected. Its current
page uses dark fields and gold; the owner separately supplied the logo pair
`#1E253B` / `#F05A36`. Both are valid references, with different roles.
[Impeccable](https://impeccable.style/) was scrolled through its soft-color
gallery and interactive work area: white remains dominant, soft surfaces group
content, and golden yellow creates focused emphasis. These observations concern
color and composition, not an adoption or accessibility study.
[Neo Mirai](https://impeccable.style/neo-mirai/) was inspected at its opening and
through agenda/speakers. Its persistent navigation, section-specific current
location and alternating broad compositions preserve orientation as the page
changes. Its illustration-led conference treatment belongs to that surface.

BatchBeacon's purpose is to compare exact packaging evidence with an authority
record and support a deliberate next step. The recommended palette uses navy
for legibility and structure, golden yellow for the next deliberate action,
coral in the paired-label identity, and pale blue around label evidence. Mint is
reserved for the proposed wording comparison; it never means safe or approved.
White carries detailed evidence. Cream review messages retain explicit status
words. This is a design judgment, not a claim about universal color psychology.

## Acceptance established before final verification

- Three primary destinations remain visible and usable after scrolling each view.
- Desktop retains the header; phone retains only the navigation row, leaving the
  brand and prototype notice in normal document flow. No second sticky row.
- Current destination has a full boundary, distinct fill, underline and
  `aria-current`; selected evidence has its own full boundary and explicit words.
- At 320/390/720/1280/1440px, no horizontal page overflow. Focus and phone section
  anchors stay below persistent navigation. Modal confirmation remains above it.
- Body/button text meets 4.5:1 (3:1 for qualifying large text); color alone does
  not communicate outcome, current page or selection.
- Native scrolling remains under user control; no scroll interception, forced
  page snapping or content hidden until animation. Reduced-motion behavior remains.
- Logo retains original paired-label geometry and is reviewed in color and mono.

Independent pre-edit layout assessment recommended persistent top navigation:
three destinations fit, while a sidebar would narrow the evidence comparison.
Reading order, grouping, rhythm, density, adaptation and extremes were assessed
from source and existing captures independently of mechanical output. Separate
bounded layout scan returned no findings before this edit.

| Before | Proposed treatment | Why |
| --- | --- | --- |
| Navigation scrolls away | Persistent desktop header; compact phone navigation | Switch tasks without losing access to the three destinations |
| Charcoal and burnt orange | Navy, gold, coral identity and restrained soft surfaces | Carry the owner's references into the product's evidence/action hierarchy |
| Uniform neutral support regions | Pale blue label region; mint proposed wording | Distinguish supporting material without adding containers |
| No sticky-header clearance | Scroll padding around anchors and focused controls | Keep the target readable during navigation |

## Rendered verification

The actual local candidate is at [workbench](http://127.0.0.1:8765/prototype/refined/)
and [identity study](http://127.0.0.1:8765/prototype/refined/brand.html).

| Role | Color | Verification or justification |
| --- | --- | --- |
| Primary text, navigation, boundaries | Navy `#1E253B` | 15.18:1 against white |
| Deliberate primary action | Gold `#E8B44C` | Navy text 8.00:1; hover 6.82:1; navy border makes the control boundary explicit |
| Paired-label mark | Coral `#F05A36` | Owner-supplied logo reference; not used behind ordinary white text (3.38:1) |
| Label evidence region | Pale blue `#EAF0F8` | Secondary text `#535D71` 5.77:1 |
| Proposed wording | Mint `#E6F2EB` | Secondary text 5.76:1; not an approval indication |
| Evidence selection | Pale gold `#FFF2CF` | Navy boundary, pressed state and explicit selected-field announcement |

Primary checks: locked environment/Ruff PASS; 64 unit and 25 local browser tests
PASS, including 21 refined-prototype cases. Six new cases cover persistent
navigation/backward keyboard focus at four widths and unobscured phone section
anchors at two widths. Initial navigation tests raced the existing asynchronous
hash-change heading focus; awaiting that actual completed navigation before
scrolling removed the test race. The initial failed log remains private. No
product defect was dismissed to obtain the pass. Before/after bounded layout
detector scans returned no findings. This is not a full accessibility audit.

Actual captures, inspected at 1440×1000 desktop and 390×844 phone:

- [Workbench desktop](../ui/palette-navigation/workbench-desktop.jpg) and
  [phone](../ui/palette-navigation/workbench-phone.jpg)
- [Phone after jumping to evidence](../ui/palette-navigation/evidence-phone-scrolled.jpg)
- [Retail desktop](../ui/palette-navigation/retail-desktop.jpg) and
  [phone](../ui/palette-navigation/retail-phone.jpg)
- [Guidance desktop](../ui/palette-navigation/guidance-desktop.jpg) and
  [phone confirmation](../ui/palette-navigation/guidance-phone.jpg)
- [Identity study](../ui/palette-navigation/brand-desktop.jpg)

No scrolling library, scroll listener, forced snap, reveal delay or new animation
was introduced. Browser-native scrolling and the existing reduced-motion path
remain. Sticky navigation has an opaque surface and scroll clearance. Actual
200% browser zoom, screen-reader/hardware testing and hosted availability remain
open integration checks; responsive-width checks are not claimed as substitutes.

This is a local visual prototype, not integrated runtime, human source review or
final submission evidence. U02 final visual approval remains open.

Independent technical rerun: 21 refined browser tests PASS in installed Chrome.
All eight captures and changed sources were inspected; no reproduced blocker.
Separate design-review continuation found no material presentation issue. That
review continued the pre-edit assessment and is not claimed as a fresh-context
finish review. Both dispositions permit provisional owner presentation only.

Reviewed source bindings:

| File | SHA-256 |
| --- | --- |
| style.css | `7f1c411a7edf4a819bd7df486103ba2e364968130f9bcc6dc69bdf3dff3daf38` |
| mark.svg | `2681e24c53a570da0e42de3909d43e6ae8183c15147204100fdbdea86cc01bf6` |
| mark-mono.svg | `96c4dd88db2a23f02ddcc864042d5b8682d547e2e7954dd1b859140c393dd4c7` |
| brand.html | `d1b5efde1b429cb148c15ab3ba6ab123690db11227d28a75768e3b5055769579` |
| test_refined.py | `60d9f0c1be78915eb948d85594d5fb1a80e6486bf45dae9ec111fc29c8dcfdd4` |

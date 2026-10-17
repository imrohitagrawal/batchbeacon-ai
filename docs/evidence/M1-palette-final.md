# Final palette and control-spacing refinement

Status: designer recommendation prepared for the existing U02 visual review.
This supersedes the selection fill and queue-control dimensions in
[M1-final-visual-review](M1-final-visual-review.md); its remaining behavior,
verification history and limitations still apply. No final visual approval is inferred.

The owner supplied before/after screenshots, delegated the final palette judgment,
and requested consistent current-state boxes and breathing room around the retail
filter arrow. Those personal browser screenshots were inspected in conversation
and are not copied into this public repository. The captures below contain only
the synthetic local prototype.

## Final choice

Keep the newer rich-blue/coral identity, white workspace, pale-blue evidence panel,
and vivid gold primary action. Restore the earlier pale-peach selection fill. The
previous pale gold selection unified the accent family, but made selection too
similar to the next action and review conditions. Peach gives selection its own
role while connecting to the coral label in the mark. This is a design judgment,
not an accessibility requirement or a claim that the earlier palette failed.

| Role | Color | Reason |
| --- | --- | --- |
| Wordmark / upper label | Rich dark blue `#173B75` | Clearly blue, stronger definition than the rejected muted navy |
| Lower label / brand signature | Coral `#F05A36` | Preserves the owner’s Stackclimb reference |
| Reading text / navigation / focus | Deep navy `#1E253B` | Strong legibility on light surfaces |
| Primary action | Gold `#FFBF00`, hover `#EDB000` | Vivid, controlled emphasis with navy text |
| Selected evidence / choice | Pale peach `#FFF3ED` | Distinct from gold actions; full outline and explicit selection words |
| Label evidence | Pale blue `#EAF0F8` | Groups source material without competing with the decision |
| Candidate guidance | Lavender `#F1EDFF`, violet `#6243B5` | Identifies proposed wording, separate from active guidance |
| Completed workflow | Mint `#E6F2EB`, green `#20573E` | Completed simulated hold or guidance change; never food safety |
| Review condition | Cream `#FFF2D8`, brown `#6A4A05` | Draws attention to the evidence review requirement |

White and cool near-white occupy most of the page; strong colors are small accents.
The owner’s Impeccable screenshots are positive color references. Their surrounding
example labels are not treated as instructions to reject those colors.

The direction takes color inspiration from [Stackclimb](https://stackclimb.com/)
and [Impeccable](https://impeccable.style/), with persistent navigation informed by
the requested [Neo Mirai scrolling reference](https://impeccable.style/neo-mirai/).
It keeps ordinary page scrolling and the existing desktop header/phone navigation.
The evidence-review task does not benefit from adding decorative scrolling effects.

Current guidance supports stable color roles: [Apple recommends consistent color
meaning for status and interactivity](https://developer.apple.com/design/human-interface-guidelines/color?changes=_5_2),
and [Google Material separates accent, surface and semantic roles](https://m3.material.io/styles/color/the-color-system).
Applying those principles here is a design inference, not a claim to copy their
interfaces or establish a measured industry-wide color trend. No palette can
establish adoption or a hackathon result without product and user evidence.

## Controls and accessibility

All six retail Current state labels now share 138 × 36 CSS pixels at the default
text size, with centered text. These are status labels within linked rows, not
separate small click targets. The native select retains its keyboard and popup
behavior; its chevron sits in a 16 px box inset 14 px from the right edge, with
44 px right padding protecting the text. Forced-colors mode restores the native
arrow. No custom JavaScript menu was introduced.

Measured sRGB contrast uses source/computed colors, not antialiased screenshot
pixels. [WCAG text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
requires 4.5:1 for normal text and 3:1 for qualifying large text. Selection and
states also use words, outlines and native semantics, following
[Use of Color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

| Pair | Ratio |
| --- | --- |
| Navy / peach selection | 13.95:1 |
| Dark coral selection text / peach | 5.30:1 |
| Secondary text / peach | 6.08:1 |
| Navy / gold action, normal / hover | 9.19:1 / 7.82:1 |
| Rich blue / white | 10.94:1 |
| Violet / lavender | 6.12:1 |
| Green / mint | 7.32:1 |
| Control boundary / white | 3.98:1 |

Lock, Ruff and all 118 unit tests passed. All 36 existing browser tests passed
using installed Chrome, including keyboard focus, reflow, persistent navigation,
consent, state recovery and default rendered-text contrast. The initial command
could not launch the absent bundled Chromium executable; that setup failure was
retained separately and resolved by explicitly selecting the already installed
Chrome channel. No application failure was hidden. Hosted CI installs its own
pinned Chromium runtime; its result is recorded separately.

The prepared original Impeccable 4.6 polish playbook and craft floor were applied;
context and the completed direction workshop were not restarted. The bounded
layout detector ran once after this delta and returned zero findings. This is not
a formal certification.
Automated ArrowDown/Enter selection could not be verified for the native select;
the independent reviewer reproduced the same limitation on an unstyled native
control without application JavaScript. Programmatic native selection and filter
results passed, as did focus visibility. No custom menu was substituted.
Native 200% zoom, screen-reader/hardware-touch testing, other browser engines and
integrated runtime accessibility remain unverified as recorded in the earlier review.

Independent read-only finish review passed 79 rendered checks across
320/390/720/760/761/800/1190/1440 px widths: no horizontal overflow,
status/action overlap, text-contrast failure or browser error. All six status
labels measured 138 × 36 px at each tested width. Forced-color emulation restored
the native select appearance, removed the SVG and preserved focus/selection
outlines. Disabled text measured 5.16:1. All six current captures were visually
inspected and their metadata checked. No reproduced critical or required-contract
finding remained; the reviewer recommended this exact revision for owner review.

## Current captures

| Surface | Desktop | Phone |
| --- | --- | --- |
| Workbench | [Full page](../ui/palette-final/workbench-desktop.jpg) | [Example choices](../ui/palette-final/workbench-phone.jpg), [selected evidence](../ui/palette-final/evidence-phone.jpg) |
| Retail queue | [Full page](../ui/palette-final/retail-desktop.jpg) | [Full page](../ui/palette-final/retail-phone.jpg) |
| Brand and palette | [Full page](../ui/palette-final/brand-desktop.jpg) | Earlier geometry and size checks remain applicable |

Live review: `http://127.0.0.1:8765/prototype/refined/`.
Prior captures remain historical; guidance/held states retain their approved-for-
review roles. The shared checkbox selection fill also becomes peach.

## Source binding

- `index.html`: `69988051bbb62ae49d29f029a7559d5bddd08e0e7aa2cedf1056dfa226746bcf`
- `style.css`: `3b945be3e38e6f3e1ed9eb0aa4fc3f1152e73b813cd581623ad58826bde98a00`
- `prototype.js`: `d250cfb51cb412fe34055296743825be41fedf7f5e76364922f3cd8398314122`
- `brand.html`: `712cb62be62f2e987f7377c0e577895ba09459980f01ee0cae01b1fe359b6926`
- `mark.svg`: `91de6636356363512a9c5809a2e0ccea3410f8a384f46367b186d043ca835b0a`
- `mark-mono.svg`: `63cbe564af08a25f212295e5588529b5b64a2881fe0a337c20148ec8b4cfac12`

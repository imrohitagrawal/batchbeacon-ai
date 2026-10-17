# Cross-view alignment finish pass

Status: owner-requested refinement of the existing visual candidate. Palette and
workflow meaning are unchanged. This supersedes the layout/source binding in
[M1-palette-final](M1-palette-final.md); its color rationale and checks still apply.
U02 final visual review, source review, runtime and final submission remain distinct.

The owner asked about mint and retail heading/value alignment, then requested a
check of other text alignment. Mint was not removed: `#E6F2EB` remains the fill for
completed simulated holds and completed guidance, with `#20573E` text. It is a
small functional state accent; the surrounding table remains white.

## Reproduced alignment issues and corrections

All four observations below are ADVISORY_DEBT visual consistency issues, without
a demonstrated false result, inaccessible path or accepted-contract violation.

| Observation | Correction |
| --- | --- |
| Retail Current state heading started at the left edge while badge text was centered | Center both heading and badges on the same column axis. Product, Market and Next step headings retain the same left edge as their text values. |
| At 761 px the queue heading and body computed different track widths; Market drifted about 6.17 px | Share one 8.625 rem status-width token between the column minimum and badge width; use explicit flexible tracks for other columns. |
| Guidance evaluation values started about 46.84 px apart because labels had different widths | Use a shared 9 rem label column and flexible value column; stack label/value pairs on phone. |
| At 761 px the candidate wording label wrapped while baseline did not, shifting paragraph starts by 24 px | Stack the wording pair at widths up to 900 px. Wider views preserve side-by-side comparison. |

The workbench comparison already has common column origins across its headers
and values. The independent review exercised 35 width/scenario combinations,
including missing, negative and UK states. Form labels/input edges align without
clipped controls. Dialog text and consent share a content edge; paired action
buttons share their row and height, including wrapping together at 320 px.
Phone lifecycle wrapping is orderly. No unrelated layout or color was changed.

## Verification

Primary rendered review inspected queue, workbench evidence columns, guidance
evaluation, desktop/phone confirmation and the 800 px stacked guidance treatment.
The existing targeted browser suite passed 16 cases after the first alignment
corrections; the subsequent boundary changes passed all 11 affected reflow/guidance
cases. These are local installed-Chrome checks, separate from hosted execution.
The previous complete suite and hosted palette run remain linked in
[M1-hosted-ci](M1-hosted-ci.md); they do not automatically cover this later delta.

Independent correction verification passed all nine widths, including the
900/901 px boundary. Queue header/body tracks match; status centers differ by at
most 0.008 CSS px from layout quantization. Wording labels have equal height and
paragraph offsets on both sides of the stacking breakpoint. All four captures
were visually inspected; no overflow or cell clipping remained.

Keyboard-native-select automation, native zoom, screen-reader, hardware touch,
other-engine and integrated-runtime limits remain as recorded in the palette
review. No real-user adoption or full accessibility certification is claimed.

## Current rendered evidence

- [Retail queue: centered status column and visible mint completion](../ui/alignment-final/retail-desktop.jpg)
- [Guidance: aligned label/value columns](../ui/alignment-final/guidance-desktop.jpg)
- [Guidance at 800 px: stacked wording comparison](../ui/alignment-final/guidance-tablet.jpg)
- [Guidance on phone](../ui/alignment-final/guidance-phone.jpg)

Live prototype: `http://127.0.0.1:8765/prototype/refined/`. Reload an existing tab
to load the stylesheet changes. Earlier captures remain historical evidence.

## Source binding

- `index.html`: `69988051bbb62ae49d29f029a7559d5bddd08e0e7aa2cedf1056dfa226746bcf`
- `style.css`: `14719b83950fb7b048b1806a49ef36a4390b50d75b71e4c39cbf267e6ab8c5b9`
- `prototype.js`: `d250cfb51cb412fe34055296743825be41fedf7f5e76364922f3cd8398314122`
- `brand.html`: `712cb62be62f2e987f7377c0e577895ba09459980f01ee0cae01b1fe359b6926`
- `mark.svg`: `91de6636356363512a9c5809a2e0ccea3410f8a384f46367b186d043ca835b0a`
- `mark-mono.svg`: `63cbe564af08a25f212295e5588529b5b64a2881fe0a337c20148ec8b4cfac12`

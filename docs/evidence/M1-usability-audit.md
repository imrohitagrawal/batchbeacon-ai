# Impeccable audit and user-task usability review

**Later owner decision, 18 October 2026:** [U02 is now approved](M1-visual-approval.md)
for the current refined treatment. The observations below retain their original
review-time status; earlier rejected treatments are not retroactively approved.

Status: corrected local visual prototype, ready for owner review. U02 remains open.
This report supersedes the control/alignment treatment and source binding in
[M1-alignment-final](M1-alignment-final.md). Earlier reports remain historical.
The palette rationale in [M1-palette-final](M1-palette-final.md) remains applicable.

## Implementation integrity verdict

**PASS within the tested prototype scope.** Product identity, the label/notice
comparison, scoped results and deliberate confirmation form a coherent workflow.
The UI describes its examples and unsaved actions explicitly. The original admitted
Impeccable 4.6.0 audit playbook was applied; its pinned 0.1.15 source detector ran
against the four final refined source files with `detect --json --no-config` and
returned `[]`, exit 0. This was a source scan, not a rendered accessibility scan.
It does not prove that users can discover or understand the controls.

A separate independent reviewer inspected the rendered controls, complete state
paths and captures. The primary reproduced and corrected the findings. No palette
restart, repeated design questionnaire or final DESIGN approval was inferred.

## Audit health score

| Dimension | Score | Evidence and limit |
| --- | ---: | --- |
| Accessibility | 3/4 | Labels, keyboard state/focus, dialog consent/exits, contrast, status feedback and reduced motion checked. Screen-reader and native zoom coverage remain incomplete. |
| Performance | 4/4 | Lean static prototype: about 58 KiB of HTML/CSS/JS/mark; no framework, external font, initial third-party request or layout animation loop. This is not a production load or Core Web Vitals benchmark. |
| Theming | 3/4 | Shared semantic palette and action tokens; a few disabled-state and badge literals remain. Deliberately light-only; a dark theme is not an accepted requirement. |
| Responsive design | 3/4 | Desktop/phone, breakpoint checks, synthesized touch and doubled-root-text stress pass. Physical devices and native browser zoom are not established by those checks. |
| Implementation integrity | 4/4 | Shared control treatment, honest prototype states, product-specific comparison and source-only detector result verified in context. |
| **Total** | **17/20 — Good** | A local technical audit assessment, not certification or release approval. |

The formal audit, after the first control corrections, found **0 P0, 0 P1, 1 P2
and 3 P3** findings. The P2 and two P3s were corrected and independently verified;
one P3 token-consolidation item remains advisory. The initial audit score was
16/20 with responsive design at 2/4. Earlier owner-reported findings and their
corrections are retained separately below rather than erased by the final score.

## Why the earlier review missed visible problems

The earlier review over-weighted functional behavior, DOM geometry and contrast.
A control could pass because it was a real button, keyboard-accessible and large
enough, even though its appearance did not make the action obvious. Underlined
reset/inspection actions were judged individually; the review did not compare
all controls serving the same purpose. Static stage text also looked like a link.

Reviews followed the latest palette or alignment change rather than a complete
inventory of controls and states. This missed local-feedback placement, stale
helper wording and what happens after changing incidents. A second test weakness
was reproduced: a geometry read could occur before a hash-navigation update,
misattributing a result to the next page. Geometry checks now wait for the intended
view to be visible; the independent measurement script also waits for rendering.

A fresh UI-tab reload additionally exposed cached earlier CSS. Versioned local
asset references now load the corrected stylesheet/script. This explains that
observed stale rendering only; it is not an explanation for all earlier misses.

## Owner-reported and journey findings — corrected

These are ADVISORY_DEBT under repository impact triage: the prototype still offered
working controls and saved no real data. That classification does not make visual
usability optional. Each was corrected within the authorized refinement scope.

| Finding | User impact | Correction and verification |
| --- | --- | --- |
| Secondary actions did not look consistently actionable | Preview recapture, Inspect extracted fields and Reset preview were harder to recognize; static lifecycle text looked like a link | Shared pale-blue button fill, blue text/border, hover/pressed treatment; rotating disclosure chevrons; framed field selectors and history/example disclosures; boxed reset; explicit current-step text. Pointer, keyboard, synthesized touch and visual checks passed. |
| Queue headings/values used mixed visual anchors | The three columns appeared misaligned despite some correct grid coordinates | All four headings and their cell containers share left origins; badges retain centered internal text and consistent dimensions. Next-step destinations visibly look like links. Default and narrow layouts independently checked. |
| Feedback placement/state could mislead on later actions | A selected-file message appeared far from the input; the old selection could persist when moving to another example; rollback help stayed stale | File status is local to capture, selection/status clear on incident change, read-only fields say so before the controls, and rollback helper updates with its state. New browser regression reproduces cross-incident selection behavior; lifecycle regression checks helper transitions. |

Mint remains `#E6F2EB` with dark-green text for completed **simulated workflow
steps**, including the hold example and activated guidance. It does not mean a
product is safe. Gold remains the primary action, peach the selected evidence,
blue the secondary action/evidence family and lavender the proposed guidance.

## Formal audit findings and disposition

### [P2] Enlarged-text layout exceeded narrow viewports — corrected

- **Location:** `prototypes/refined/style.css` mobile queue, brand, navigation,
  examples and review jumps; `brand.html` identity layout and heading.
- **Category:** Responsive design / Accessibility.
- **Impact:** At doubled root text, badges exceeded mobile tracks; unwrappable
  branding/navigation and a long heading could exceed the 320–390 px viewport.
  These symptoms share intrinsic-size/nowrap constraints and are one root cause.
- **Standard:** Relevant to text resizing/reflow. This test changes root font size;
  it is not native browser zoom and does not by itself decide NF-06 compliance.
- **Correction:** Shrinkable grid tracks, bounded badge width, wrapping navigation
  and examples, intentional wordmark wrap opportunity and long-heading wrapping.
  Scroll clearance scales with text. Added a regression that failed before the fix.
- **Verification:** Four-width browser regression and independent 32-case matrix
  pass, including expanded examples/panels, guidance confirmation and identity page.
- **Suggested command applied:** `$impeccable adapt`, followed by polish.
- **Repository triage:** ADVISORY_DEBT with a reproduced accessibility-related
  usability impact. Native-zoom acceptance remains separately unverified.

### [P3] “Unrestricted” split awkwardly in the result column — corrected

- **Location:** `prototypes/refined/style.css`, `.comparison-row` grid definition.
- **Category:** Responsive design / Implementation integrity.
- **Impact:** At 761/800 px the UK date result wrapped within the word, slowing scan
  reading. No content was lost and no result changed.
- **Correction:** Reserve an 80 px minimum result track shared by headers and rows.
- **Verification:** The word stays intact at 761/800/900/901/1190 px; column origins
  remain equal. Mobile comparison retains its separate two-column layout.
- **Standard:** Readability; no specific WCAG violation established.
- **Suggested command applied:** `$impeccable layout`, followed by polish.
- **Repository triage:** ADVISORY_DEBT, resolved.

### [P3] Enlarged skip link peeked into the banner — corrected

- **Location:** `prototypes/refined/style.css`, `.skip` and `.skip:focus`.
- **Category:** Responsive design / Accessibility.
- **Impact:** The fixed negative offset hid the default link, but part of its
  taller enlarged-text version remained visible without focus. Visual inspection
  caught this even though page-overflow assertions passed.
- **Correction:** Hide it relative to its own height, constrain it to the viewport,
  and restore it on focus. Enlarged-text tests now assert both states.
- **Standard:** Visual clarity; no inaccessible path was demonstrated.
- **Suggested command applied:** `$impeccable polish`.
- **Repository triage:** ADVISORY_DEBT, resolved.

### [P3] Remaining color literals — deferred advisory

- **Location:** `prototypes/refined/style.css`, disabled controls, notice/badge
  borders, label-paper colors and backdrop; some identity-study CSS.
- **Category:** Theming / maintainability.
- **Impact:** Future palette maintenance needs care in a few selectors. No visible
  mismatch or contrast failure was reproduced in the checked states.
- **Recommendation:** Consolidate literals when preparing the final design system
  after U02, preserving the reviewed palette. Do not change colors just to remove
  literals. Unused historical `.text-button` styling can be removed in that pass.
- **Standard:** No demonstrated accessibility violation; dark mode is out of scope.
- **Suggested next command:** `$impeccable document`, then `$impeccable polish`.
- **Repository triage:** ADVISORY_DEBT, owned by the integrator; not a release blocker.

## Verification coverage

The inventory covers **45 application controls plus two identity-page links**:
navigation/skip/brand/source links, three example radios, three disclosure summaries,
two selects, phone section jumps, recapture/inspection, file selection, two read-only
fields, five field selectors, scenario action, six queue rows, new/empty-queue
recovery, guidance progression/reset/rollback/consent and dialog exits/confirmation.

| User task or state | Checked behavior |
| --- | --- |
| Understand a product check | Purpose, synthetic label, paired evidence, selected field and next action visible together; keyboard field selection announces paired values. |
| Missing evidence or failed check | Recapture/review-request controls and local feedback; disabled-state reason; UK all-date cases do not request a needless date capture. |
| Changed source or different identity | Historical/negative scope remains explicit; unsupported hold stays disabled. |
| Retail queue | Six destinations, all/attention/held/empty filters, empty recovery, common column origins and equal default badges. |
| Deliberate hold preview | Unchecked/checked consent, disabled/enabled action, close/Go back/Escape, reopen, focus return and success preview. Nothing is saved. |
| Guidance lifecycle | Candidate/evaluation/confirmation/active, consent, next capture, reset, rollback, updated helper and unchanged illustrative lifetime limits. |
| Accessibility and reflow | Keyboard paths, focus visibility, semantic state, reduced motion, text contrast, 44 px effective targets, enlarged text and phone navigation. Label areas count as radio/checkbox targets. |

- **41 local browser tests PASS** in fresh Chrome; earlier regressions retained.
- Independent route/control checks at 320/390/720/761/800/900/901/1190/1440 px;
  focused path checks cover all scenario/queue/guidance states.
- Independent final matrix: **32 combinations PASS** = four widths × default or
  doubled root text × workbench/retail/guidance/identity. Workbench includes expanded
  examples and both panels; guidance includes confirmation. No page overflow or
  JavaScript errors in these cases; inspected modal contents stay reachable.
- Synthesized Chrome touch passed disclosures, fields inspection, modal consent
  and cancel, queue destination and guidance reset. No custom drag gesture exists.
- Secondary-action text contrast: 8.76:1 default, 7.85:1 hover/expanded, 6.75:1
  pressed. Selected accent on peach: 5.30:1. Color is supplemented by words,
  borders, underlines or native state. Automated contrast is not full WCAG proof.
- Eight fresh synthetic captures independently checked for layout and publication
  privacy. Source/capture hashes are in [the manifest](../ui/usability/manifest.json).
- This report records local evidence. Hosted evidence is tracked separately in STATE;
  no release candidate or immutable freeze is declared.

## Review artifacts

[Interactive local prototype](http://127.0.0.1:8765/prototype/refined/).

| Desktop | Phone |
| --- | --- |
| [Workbench](../ui/usability/workbench-desktop.jpg) | [Recapture](../ui/usability/recapture-phone.jpg) |
| [Retail queue](../ui/usability/retail-desktop.jpg) | [Retail queue](../ui/usability/retail-phone.jpg) |
| [Guidance](../ui/usability/guidance-desktop.jpg) | [Guidance](../ui/usability/guidance-phone.jpg) |
| | [Read-only fields](../ui/usability/fields-phone.jpg) |
| | [Confirmation](../ui/usability/confirmation-phone.jpg) |

## Review method from this point

Before presenting a changed screen: inventory every actionable and read-only
control; inspect appearance before clicking; exercise default, selected, expanded,
disabled, feedback, failure and recovery states; complete the whole user task using
pointer and keyboard; compare all controls sharing a role; check narrow and enlarged
text layouts; verify actual loaded assets; then obtain an independent rendered
review. Functional tests and heuristic usability findings remain separate evidence.
Screenshots are reviewed at task moments, not only at the top of each page.

Outstanding verification: native browser zoom (including the explicit NF-06
200% requirement), screen-reader announcements, native-select ArrowDown/Enter operation, physical touch devices, cross-engine
behavior, production performance and runtime journeys. The browser permission
boundary did not allow the native Chrome control needed for the intended zoom
exercise; no permission workaround was attempted. Root-text stress is reported
separately. Select-option value changes were automated; that does not establish the native dropdown keyboard path. A representative first-time-user study has not been performed.

**U02 concrete visual approval, remaining human source/gold review and final
submission gates remain open.** This audit cannot close those gates or establish
enterprise readiness. It also cannot guarantee that no further usability issue exists.

References: [W3C resize text](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html),
[W3C target-size minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
[W3C consistent identification](https://www.w3.org/WAI/WCAG22/Understanding/consistent-identification.html).
The audit's 44 px target heuristic is stricter than the WCAG 2.2 AA 24 px minimum
with its exceptions; passing that heuristic is not certification.

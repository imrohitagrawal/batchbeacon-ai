---
name: BatchBeacon AI — Evidence in focus
description: A precise, approachable interface for reviewing product and recall evidence.
colors:
  brand-navy: "#173B75"
  brand-coral: "#F05A36"
  beacon-gold: "#FFBF00"
  primary-hover: "#EDB000"
  canvas: "#F7F8FA"
  surface: "#FFFFFF"
  ink: "#1E253B"
  muted: "#535D71"
  line: "#D5DBE4"
  control: "#748096"
  accent: "#B93819"
  selected: "#FFF3ED"
  evidence-surface: "#EAF0F8"
  secondary-surface: "#DCE7F7"
  secondary-hover: "#CBDCF2"
  secondary-active: "#B8CDE9"
  proposed-surface: "#F1EDFF"
  guidance-ink: "#6243B5"
  completed-surface: "#E6F2EB"
  completed-ink: "#20573E"
  completed-border: "#54836A"
  warning: "#FFF2D8"
  warning-ink: "#6A4A05"
typography:
  headline:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "2rem"
    fontWeight: 650
    lineHeight: 1.2
    letterSpacing: "-0.03em"
  headline-phone:
    fontSize: "1.75rem"
  title:
    fontSize: "1.25rem"
    fontWeight: 650
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  evidence:
    fontSize: "0.875rem"
  metadata:
    fontSize: "0.75rem"
  action:
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  tag: "4px"
  input: "6px"
  action: "8px"
  container: "12px"
  workbench: "16px"
spacing:
  compact: "8px"
  small: "12px"
  regular: "16px"
  panel: "20px"
  section: "24px"
  large: "28px"
  desktop-gutter: "40px"
components:
  button-primary:
    backgroundColor: "{colors.beacon-gold}"
    textColor: "{colors.ink}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    padding: "11px 16px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-secondary:
    backgroundColor: "{colors.secondary-surface}"
    textColor: "{colors.brand-navy}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    padding: "11px 16px"
  button-secondary-hover:
    backgroundColor: "{colors.secondary-hover}"
  button-secondary-active:
    backgroundColor: "{colors.secondary-active}"
  field-selector:
    backgroundColor: "{colors.secondary-surface}"
    textColor: "{colors.brand-navy}"
    rounded: "{rounded.input}"
    padding: "6px 8px"
  select:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.input}"
    padding: "8px 44px 8px 12px"
  input-readonly:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    rounded: "{rounded.input}"
    padding: "9px"
  navigation-current:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.surface}"
    rounded: "{rounded.action}"
    padding: "10px 16px"
  state-completed:
    backgroundColor: "{colors.completed-surface}"
    textColor: "{colors.completed-ink}"
    rounded: "{rounded.tag}"
    padding: "5px 8px"
    width: "8.625rem"
  guidance-container:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.container}"
    padding: "28px"
---

# Design System: BatchBeacon AI

## Overview

**Creative North Star: "Evidence in focus"**

The interface is calm, direct and visibly actionable. Rich blue identity and a
small number of vivid gold actions sit on light, carefully separated surfaces.
Color helps people locate evidence, distinguish a proposal from a completed step,
and recognize their next action. Clear language and visible boundaries carry the
same meaning when color is unavailable.

This is the owner-approved visual system, extracted from the refined prototype
at `b145ac6f25ef55c633fb61723694da54be811614`. See the
[U02 approval record](docs/evidence/M1-visual-approval.md) and
[source/capture manifest](docs/ui/usability/manifest.json). The original directions
and rejected intermediate palettes remain historical. This document records
visual authority; it does not certify runtime behavior or accessibility compliance.

**Key Characteristics:**

- Evidence and decisions have distinct, readable places.
- Primary and secondary controls look actionable before interaction.
- Color roles remain stable across desktop, phone and every workflow state.
- Persistent navigation, visible focus and explicit recovery support task continuity.

## Colors

Vivid accents sit beside soft blue, peach, lavender and mint surfaces, with strong
navy text and restrained neutral separators. The frontmatter carries normative
values; names below refer to those tokens.

### Primary

- **Beacon gold** identifies the next principal action. Its dark label and outline
  preserve readability and its boundary; the hover variant is slightly deeper.
- **Brand navy** identifies the wordmark, the upper label in the mark and secondary
  action labels/borders. Keep the visibly blue identity separate from darker body ink.

### Secondary

- **Brand coral** completes the paired-label mark. **Accent** is its darker,
  readable relative for selected controls, radio marks and underlined field labels.
- **Selected peach** identifies the chosen example/evidence field; combine it with
  an outline, checked input or explicit selected text. Gold remains the action color.
- **Evidence surface** separates the supplied label or baseline wording. The
  stronger **secondary surface/hover/active** family identifies clickable controls.

### Tertiary

- **Proposed surface / guidance ink** identify candidate guidance, before activation.
- **Completed surface / ink / border** identify a recorded simulated workflow step.
  Mint never means that a product is safe, cleared for sale or free of recall risk.
- **Warning / warning ink** support unresolved evidence, changed scope and review
  attention. A scoped negative result remains neutral, not mint.

### Neutral

- **Canvas** surrounds the workspace; **surface** contains the task.
- **Ink** carries body text, active navigation, outlines and headings.
- **Muted** carries supporting context; it must remain readable on its actual surface.
- **Line** separates content. **Control** outlines selectable or editable boundaries.

**The Meaning Rule.** Every consequential state has a text label and a structural
cue; color alone never conveys selection, availability or outcome.

## Typography

Use the native system sans-serif stack throughout. The hierarchy comes from size,
weight and spacing; no downloaded display font or decorative serif is introduced.
Headlines use the headline role, reducing to headline-phone at the phone breakpoint.
Section titles use title; ordinary text uses body; dense evidence uses evidence;
supporting captions use metadata. Action labels use action.

Paragraphs use `max-width: 70ch`, an approximate typographic measure. Dates and identifiers use
tabular numerals. Preserve case and leading zeros in evidence. Text may wrap inside
flex/grid children; headings and long evidence must not force page overflow.
Metadata at 12px is the current lower bound, not a target for ordinary reading.

## Layout

The workspace has a maximum width of 1600px and desktop side gutters of 40px,
reducing to 24px at 1190px and 20px at 760px. Content sections use boundaries,
alignment and spacing to establish hierarchy. Exact surface composition lives in
the implementation and its surface brief; new screens need not copy the workbench.

The current workbench aligns label, comparison and decision in three columns with
minimum widths of 210px, 430px and 230px and proportions .85:2:.95. At 1190px,
the label becomes 240px wide and the decision moves below; at 760px all panels
stack. Phone comparison rows repeat the two evidence labels beside their values.
Guidance uses a 2.2:1 layout; wording comparisons stack at 900px and the main layout
stacks at 760px.

Queue headers and cell containers share left origins. Consistent state badges have
centered text internally, a width of 8.625rem and a minimum height of 36px; this is
not a reason to center the whole column. Queue rows are the links. Narrow layouts
stack the product and next action and preserve readable market/state alignment.

The desktop header remains visible on scroll. On phones the destination row stays
visible while the brand scrolls normally. Navigation wraps under enlarged text.
Scroll offsets and the skip link must keep the target and focused control visible.

## Elevation & Depth

The system uses tonal surfaces and borders rather than decorative shadows. Dialogs
use a translucent navy backdrop (`#1E253B80`) and a clearly bounded light panel.
Focus outlines express keyboard location rather than elevation. Do not add lifted
card effects to every row, field or piece of evidence.

## Shapes

Use gently curved action corners, tighter field/tag corners and wider container
corners according to the rounded tokens. Most boundaries are 1px; selected evidence
uses a 2px outline and keyboard focus uses a 3px outline with a 4px offset. Queue
row focus is inset to avoid clipping. The paired-label B mark is the existing
original [SVG](prototypes/refined/mark.svg); preserve its silhouette, rich blue/coral
colors and mono variant. Do not replace it with a generic circle or status dot.

## Components

### Buttons and disclosures

Gold primary actions and blue secondary actions share a minimum 44px height,
centered labels and the action typography. Secondary hover and pressed states use
their dedicated tokens. Reset is a boxed secondary action. Recapture and field
inspection have a chevron and explicit expanded state. The five evidence field
selectors are framed controls; selecting one also outlines its evidence row.

Native details disclosures retain their triangle and receive a visible boundary.
Source and destination links are underlined; they must not resemble inert captions.
Disabled actions use the implemented gray treatment and a nearby reason or
availability condition. Static lifecycle steps use an explicit current marker,
not link styling. Gold actions do not need a new pressed-color token.

### Inputs and selection

Use native labeled controls. Selects have a minimum 44px height and a 16px chevron
inset 14px from the right; the text reserves 44px of right padding. Read-only
extracted fields have a dashed boundary, muted text and an explanation before the
fields. Editable and read-only fields must remain distinguishable. File selection
feedback sits beside the input and clears when the incident changes.

Example choices and confirmation checkboxes have a framed full-label hit area.
Selection adds peach fill plus outline and checked/selected semantics. Keep the
native control and logical focus order; never rely on a colored container alone.

### Navigation and containers

Current navigation has ink fill, a light label, underline and `aria-current`.
Inactive navigation remains plainly recognizable as a destination. White containers
use the line border. Evidence and candidate wording use their assigned tonal
surfaces. On small screens, reduce padding and stack content instead of hiding
required evidence or actions.

### Status and confirmation

State labels have consistent dimensions and explicit wording. Complete simulated
actions use mint; proposed guidance uses lavender; attention uses amber or coral
with the current text label. Status color does not imply product clearance.

Confirmations use a native modal dialog no wider than 540px, bounded by the viewport
with 16px clearance and internal scrolling when needed. Keep close/cancel visible,
retain focus, and return focus to the invoking action. Approval needs the explicit
acknowledgment; a result or click on evidence never records an action by itself.

### Motion and accessibility verification

The only current decorative transition is the selected-evidence background
animation (160ms, ease-out), enabled only without reduced-motion preference.
Keep semantic state changes immediate and persistent when motion is disabled.
Forced-color mode preserves selection outlines, disabled semantics and native
select appearance. Test initial recognition as well as behavior: every visible
control must explain what it does before hover, including narrow/enlarged views.

The recorded browser checks and Impeccable audit cover the prototype scope.
Native zoom, screen-reader and physical-device evidence remain open. Running
application integration must rerun affected state paths and accessibility checks.

## Do's and Don'ts

### Do

- Do preserve the approved color roles across every route and state.
- Do align headings and values by their shared column containers.
- Do show a visible boundary and clear label for an action before hover.
- Do pair color with text, shape, checked state or another structural cue.
- Do inspect default, expanded, error, empty, disabled and confirmed states on desktop and phone.

### Don't

- Don't use mint to imply safety, clearance or permission to sell.
- Don't turn static stage labels into apparent links.
- Don't make reset, recapture or evidence inspection look like inert text.
- Don't hide overflow by clipping required evidence or focus indicators.
- Don't treat prototype tests or visual approval as runtime or source-truth acceptance.


## Recall-context extension

The owner requested explicit cited reasons and notice details after U02 approval.
Keep the approved visual system: a visible reason and reported basis in the
comparison panel, a blue native disclosure for detailed context, and a short
notice-reason line under each queue product. Direct dated source links remain
underlined. Expanded details use definition-list headings and body values;
quantity and legal absence are explicit. Context follows the exact source version
and remains separate from the comparison result and simulated action state.
This is a faithful information extension, not a new palette or visual direction.
New source facts retain their separate human-review gate.

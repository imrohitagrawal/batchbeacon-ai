# Journey completion and recovery correction

The owner's five screenshots exposed gaps in the earlier technical acceptance:
duplicate progress numbering, raw technical provenance/history, an unexplained
unavailable-record error after guest renewal, no useful post-save action, and a
combined evidence link that only moved focus. Earlier endpoint/browser passes
remain evidence of those tested paths; they did not establish a complete human
usability pass.

## Implemented behavior

- One numbered progress sequence shows the current stage without link styling.
  The initial state asks for a label; comparison and confirmation have distinct stages.
- Selected-field evidence explains the label value, notice value, comparison and
  rule. Exact identifiers, coordinates, hashes and revision lineage remain in
  optional technical disclosures. Product names, lot case/leading zeros, typed
  dates, unknowns, correction history and historical results are preserved.
- A current saved action offers **View in retail queue** and **Check another label**.
  The latter selects an empty review without creating, uploading or calling AI.
  Earlier reviews remain in the owned queue. Saving never changes live inventory.
- Separate **Open retained label (new tab)** and **Open official notice (new tab)**
  links open their actual targets. Selection changes and expiry clear stale links.
- A definitive unavailable-record response clears the inaccessible selection and
  old incident URL, completes initialization and offers a useful next step.
  The message does not guess whether the cause was expiry or another workspace.
  Expired access offers a clean new-workspace link, not restoration of old records.
- Back/Forward to an unselected route clears the old case and preserves the selected
  page. Pending operation keys and workspace-wide unresolved blocks are retained.
  Restored pending requests verify membership in the current workspace; matching
  expiry timestamps alone are not ownership proof. If membership is unknown,
  **Check pending access** performs reads only. Reconciliation requires a separate
  explicit action after ownership is confirmed.

## Verification and scope

Independent backend, product/accessibility and operations reviews substantiated
the defects before implementation. Six new baseline regressions failed for the
reported causes. Separate baseline probes reproduced the correct server refusal
with broken client recovery and the blank-route selection mismatch. Initial test
harness/configuration failures remain retained and excluded from passing evidence.

Additional reviewer findings—stale source-link copies, initial render mismatch,
blank-route destination changes and replay before pending ownership verification—
were corrected at the responsible UI boundary. Required independent rechecks,
full local/hosted commands, packaged-source provenance and deployed readbacks are
tracked privately in `.local/run-records/journey-completion-20261027/`. Local tests
use explicit fake model/storage fixtures; they are not new real-model acceptance.
The previously reviewed real third/A/B and browser results retain their exact
runtime scope. This correction does not change model, backend, source corpus,
accounting, runtime deadlines, allowances, credentials or cloud resource limits.

A source commit is implemented evidence, not proof that it is serving. Release
status and deployed verification are recorded in the correction's pull request
and private checkpoint. No additional paid model call is needed for these UI-only
changes. Public judging availability remains governed by its existing finite phase.

## Open acceptance

All [R01–R12/F1–F8](../USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md#9-authoritative-acceptance-checklist-and-continuation-checkpoint)
remain mandatory. Owner screenshots are reported defects, not uncoached first-use
or automatic screen-reader evidence. Corrected unfamiliar-user comprehension and
completion, returning-user retest and actual VoiceOver pending/terminal speech
remain unverified. Legitimate active unknown-accounting-panel evidence, source/gold
review, protected final-case custody/full quality evaluation, live-source update,
continuous video/audio certification and broader Operations gates remain open.

# Acquisition completion and current-result eligibility

Status: LOCAL/PARTIAL T10. No provider call, actual database, runtime route or
cloud activation. This slice extends the existing reviewed evidence protocol.

Only freshly acknowledged run admission can identify a new executor; replay and
lost admission acknowledgment return the original identity without fresh authority.
An earlier absolute preparation deadline can shorten admission, never extend it.
The latest admitted acquisition controls eligibility: a failed, active, unknown
or timed-out newer run cannot leave an older result current or restore it through
correction, re-verification or action confirmation.

A running acquisition can publish one input-bound extraction and provisional
verification. These remain ineligible until a create-only completion document
binds their exact receipts, observation/result hashes, run configuration and
immutable deadline. The adapter retains Firestore's output-only creation and
update timestamps. Missing, mismatched, changed or late proof fails closed.
Server creation must precede the deadline; a local pre-commit check is insufficient.
Late history may persist. A later owned read can resolve an already committed,
on-time proof without restarting the model or rewriting that proof.

The completion document and a digest marker on its run are committed atomically.
The marker prevents an established missing document from being recreated with a
new timestamp. Every eligibility consumer requires both matching records. Source,
observation, later-acquisition and action races share the transaction's read set.

## Independent verification and corrections

Pre-code CO01–17 acceptance defines the wider coordinator scope. Independent
review reproduced two REQUIRED_CONTRACT defects in this bounded slice:

- CO07: a retained-image read after completion could cross the deadline and still
  return fresh success. The response now rechecks after that blocking read.
- CO15: retrying after removal of an established completion could recreate it.
  The atomic run marker now denies this recovery; immutable history is preserved.

Both regressions failed before their corrections. Independent negative controls
fail when each responsible guard is disabled. Independent verification passed
281 focused cases; those counts overlap the complete suite. Additional SDK fault
probes covered atomic proof/marker commit, lost acknowledgment, missing/mismatched
markers, unchanged historical retries, conflicting receipts and source/correction/
later-acquisition races. No remaining required finding was identified in this scope.

Complete local checks passed locked dependency validation, Ruff, 820 unit tests
and 50 Chrome browser tests. [Hosted run 39103833753](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39103833753)
passed at `583bd4a2ab13974a8c930fbea034c7fa42bd078e` with the same unit/Chromium
counts and locked bootstrap. A subsequent assertion-only correction compares
protobuf documents structurally: map serialization order had caused an intermittent
false test failure. Independent verification retained the failure and proved the
new assertion still detects payload and server-timestamp changes. Installed
SDK tests use explicit RPC fakes, not actual Firestore timing or cross-instance
runtime evidence. Human source review, T08 paid admission and final submission
remain separate gates. The owned model factory and coordinator are next.

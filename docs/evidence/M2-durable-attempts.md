# Durable extraction run and attempt evidence

Status: LOCAL/PARTIAL T10 integration preparation. No provider call, real database,
runtime ledger, public route or deployment was activated.

Each acquisition now requires an immutable input manifest, expected observation
revision, application configuration digest and logical operation. The admission
transaction checks exact owned READY capture metadata. An identical start key
reconciles its original run; changed inputs conflict and historical runs cannot
resume. Populated legacy records missing these bindings fail closed.

Reservations atomically append ordered attempt IDs to the run and preserve its
binding digest. Attempts are separate from the three-acquisition history limit.
Missing established attempts cannot silently reserve again. Dispatch remains a
single-use, newly acknowledged claim; this slice does not itself transmit requests.

The trusted transport-facing recording method retains bounded original response
bytes, status, completeness, observed length and the retained-byte hash before
usage interpretation. Absent, complete and truncated responses remain distinct.
Identical writes reconcile; changed evidence conflicts. Private raw bodies are
excluded from representations and sanitized validation errors have no payload
exception chain. Actual transport capture and public serialization are later gates.

Accounting no longer accepts caller-supplied token totals or a response hash. It
derives complete usage from committed original strict JSON, retaining all accepted
usage metadata. Duplicate keys, non-finite values, inconsistent totals, unsupported
usage categories, incomplete bodies and non-success statuses cannot reduce the
reservation. The original attempt's rates and limits govern late reconciliation;
accounting never restores guest access or dispatch permission.

## Independent acceptance and correction

DR01–14 were derived before implementation. Independent review reproduced one
REQUIRED_CONTRACT defect: an expanded usage record could exceed a storage bound
before the cost-limit circuit was committed. The original response and liability
survived, but another attempt could still be reserved. The Firestore document-size
manifestation was classified as the same root cause, not a separate finding.

The correction commits the circuit with the existing bounded evidence first, then
attempts expanded usage/accounting. Record, actual SDK document and generated
commit-request limits cannot undo the first committed stop. Lost acknowledgment
also retains the stop; later reconciliation accounts once if storage permits.
No reservation is refunded merely because richer evidence cannot be persisted.

Independent verification passed **183 focused tests and Ruff**. Three checked-in
size/circuit regressions fail when the first circuit commit is disabled. Separate
SDK fault probes covered a lost first-commit acknowledgment, an oversized second
commit request and cold late accounting. Original failing evidence, negative
controls, exact hashes and private receipts remain in ignored local records.
No further reproduced blocker was found in this bounded slice.

Final complete local checks passed locked dependency validation, Ruff,
**784 unit and 48 Chrome browser tests**. Focused counts overlap.
[Hosted run 39102688210](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39102688210)
passed at `5cb498e11a03a26aab55358aed8d29e67e899c9b`: locked bootstrap, Ruff,
784 unit and 48 Chromium checks. Complete log and remote main were verified.
Fake/SDK tests are not real Firestore
atomicity or provider evidence; no release freeze follows.

## Next dependency

The application still needs its admitted prompt/configuration, owned ADK client
factory, final-request validation/counting, response capture before SDK parsing,
fresh-run versus replay disposition, and one coordinator. Publication must bind
run state, deadline and current inputs transactionally; a failed or unknown new
acquisition must not revive an older result. Actual provider authenticity,
redaction, real-service acceptance, T08 cost admission and human source review
remain separate. Configuration and synthetic prices do not grant paid authority.

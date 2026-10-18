# T09 owned observation history — local protocol checkpoint

Status: LOCAL/PARTIAL, independently reviewed. This is an isolated service
protocol with explicit fake stores and extraction envelopes. No actual Firestore,
Storage, model provenance, HTTP route or deployed journey is claimed.

## Behavior

Each incident requires an evidence state provisioned atomically with its creation.
Missing or corrupt established state fails closed. Every operation checks the
current guest capability, policy, incident ownership and expiry. A slow storage
acknowledgment cannot extend guest access. Capture references must match that
incident's ready retained images, including nested field evidence; bytes are
checked outside retryable transactions.

Original redacted extraction responses, validation outcome, model/prompt/config,
source and capture dependencies, timing and fake/replay/live labels are retained
separately from observations. Failed attempted structured responses can remain
malformed or empty; they retain diagnostic codes and cannot create observations.
The trusted T10 adapter must substantiate live provenance and redaction. This
storage API alone cannot prove extraction accuracy or a real provider call.

Corrections derive the previous value, actor/session, timestamp and revision on
the server. Supported targets preserve code case, leading zeros and ambiguous
dates. Ambiguous identifier targets, stale revisions and type changes deny.
Identity changes clear reviewed resolution. Originals remain immutable; corrections
and valid recaptures append revisions and remove current-result eligibility.
A failed later extraction remains a blocker until new validated extraction; edits
or retries of an older receipt cannot restore its success.

Operation keys bind canonical payloads. Identical retries reconcile the original
receipt after lost acknowledgment, without reactivating superseded revisions.
Conflicting reuse denies. Competing corrections against one base revision permit
one transition. History and UTF-8 payload limits are typed configuration bound
into the evidence state; reaching a limit never silently truncates history.

Verification consumes no model call. It requires a previously committed shared
verification reservation binding observation digest/revision, source/context,
verifier policy and next result revision. The pure verifier computes and publishes
inside the same transaction over that current snapshot; there is no client-result
write. Reads derive currentness afresh even when verification is exhausted or paid
admission is unavailable. Old positives and negatives become stale; a current
failure-bound review result is distinct from hold eligibility. Freshness is checked
again after the final storage acknowledgment.

## Review and regression evidence

Independent OE01–12 acceptance was derived before builder code. Two findings were
reproduced before correction:

| Finding | Demonstrated impact | Classification and correction |
| --- | --- | --- |
| OE-R01 | A fresh verification after a failed recapture could reuse the older observation and restore a positive result | CRITICAL_BLOCKER: false acceptance in the local protocol. Require latest validated extraction lineage before new verification; preserve failed evidence and earlier stale history. Both direct retry and intervening correction cases fail under the former behavior. |
| OE-R02 | Invalid malformed, array or empty attempted JSON was rejected before its validation failure could be retained | REQUIRED_CONTRACT: diagnostic evidence loss. Parse successful output strictly; retain failed raw responses with diagnostics and without observations. Four failure shapes covered. |

Original failing logs and corrected runs remain in ignored `.local/run-records/`.
Initial fixture-only failures concerned test corruption injection and a negative
case lacking reviewed identity resolution; their evidence is preserved separately.
No real user/model incident or public endpoint was involved in these local tests.

Independent verification passed all **50 focused cases**, Ruff and whitespace
checks. All six new regressions fail when their former behavior is restored in
memory. Additional lost-acknowledgment, concurrent-publication, source-change and
expiry probes passed. No remaining reproduced blocker exists in this local slice.

Full locked local checks passed: **375 unit and 48 Chrome browser tests**. Counts
overlap; do not add them. Hosted checkpoint verification remains pending. No
release freeze follows.

## Remaining integration gates

The concrete store must atomically provision evidence and counters with guest/
incident records; validate serialized history; read the current source environment
and shared reservation in the same transaction; and preserve unrelated historical
actions and allowances. Tests use a fake reservation insertion at that seam, not
proof of a real SharedStore/EvidenceStore integration or Firestore contention.

Real source-refresh coordination, T10 provenance, T11 approval races, deployed
isolation, object lifecycle/IAM, runtime UI and end-to-end failure presentation
remain required. No human source approval is inferred. T09 remains partial.

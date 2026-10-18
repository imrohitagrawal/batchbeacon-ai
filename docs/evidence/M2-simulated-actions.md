# T11 simulated-action transactions — local protocol checkpoint

Status: LOCAL/PARTIAL, independently reviewed. Explicit
fake stores exercise the protocol. No HTTP action route, Firestore transaction,
real stock change, provider call or deployed journey is claimed.

## Confirmation and history

Preparation returns an exact result/observation/source-environment/policy target
for review; it creates no action. Confirmation requires a strict boolean true and
that exact target. Ownership, incident membership, demo-manager capability,
active revisions, source currentness and action-specific eligibility come from
server state in the same transaction. No client actor, role, verdict or source
review flag supplies authority.

A hold requires a current supported matched result. A current review-required
result can support a simulated review request and retains the failure reason.
A new SOURCE_VERSION_CHANGED review result may retain the old checked source
while binding the newer context; this is not hold eligibility. Scoped negatives
support neither action. Failed live evidence cannot regain hold eligibility by
being relabelled historical. Ready capture metadata and withdrawn source support
also participate in currentness checks.

The logical identity is session + incident + result revision + action type.
Concurrent clicks with different keys create one action and one creation event.
Every accepted key retains its payload binding; changed reuse conflicts. Lost
acknowledgments reconcile through owned logical lookup; unavailable storage never
masquerades as an absent action. IDs and timestamps are stable across pure callback
retries. Action, receipt and event commit together without changing evidence or
lifetime counters. No model, external fetch, message or stock effect runs inside.

Past records remain immutable. Every read checks their original result/action/
source/mode/reason relationships, then separately calculates currentness using
fresh source and observation state. Later updates make actions historical and
require renewed review. A duplicate may return the existing historical action;
it never creates renewed approval. A fresh eligible result can be explicitly
confirmed as a new action linked to prior history.

History limits and byte caps are typed, validated and hashed configuration. Full
capacity still permits existing lookup and identical replay. A new alias key
requires receipt capacity so its conflict protection is never silently omitted.
Expiry is checked during operations and after storage; a committed action survives
a late acknowledgment while expired guest access is denied.

## Independent acceptance and reproduced corrections

A read-only reviewer derived A01–18 before implementation. Two issues were
reproduced and corrected at their responsible boundaries:

| Finding | Impact / classification | Correction |
| --- | --- | --- |
| A-R01 | Literal-true validation accepted integer 1 despite strict record configuration; REQUIRED_CONTRACT input coercion | Strict boolean field plus true-only validator; false/null/string/numeric inputs deny. Original failed check retained. |
| A-R02 | Injected serialized history could change a review request into a current hold, or change its event mode/reason; REQUIRED_CONTRACT semantic store-validation failure, not an exposed client write | Check original action eligibility, observation/source references, chronology and event mode/reason against its immutable result before reads or receipt mutations. Three former-behavior failures retained. |

Independent correction verification passed **113 action/evidence/domain tests**
(including all 40 action cases), Ruff and 13 extra race/currentness/concurrency
probes. Old-behavior controls reproduced the strict-confirmation and all three
semantic-history failures. No remaining reproduced blocker exists in this local
slice. Full locked local checks passed: **415 unit and 48 Chrome browser tests**.
Counts overlap; do not add them. Hosted checkpoint verification is pending.
Logs and source-bound review receipts remain in ignored `.local/run-records/`.
No release freeze follows.

## Remaining gates

The real adapter must atomically provision action state with the incident and
read all guest/evidence/source/action inputs in one conflict-detecting transaction.
A series of separate repository reads cannot substitute for that boundary.
Firestore contention, restarts, actual Storage availability/retention, runtime
origin/CSRF routes, T10 provenance and UI confirmation integration remain unproven.
Initial model/extraction-failure result materialization and source-refresh
orchestration remain T10/T15/T16 integration work. Paid admission, human source
review and final submission gates are unchanged. T11 is not complete.

# T09 shared model admission — local protocol checkpoint

Status: LOCAL/PARTIAL. This implements the shared transaction boundary and tests
it with explicitly injected fakes. No Firestore adapter, actual allocation,
provider call, public paid route or deployed cross-instance proof is claimed.

## Behavior and ownership

A strict policy binds project, guest policy, model configuration, observed rates,
billed-token bounds, reservation amount, tool allowlist, call/retry/tool limits and
run deadline. A separate operator grant binds the finite root and four child
pools, capacity/authority evidence and expiry. Configuration is not authority;
the real T08 billing/capacity evidence remains unsubstantiated. Test prices,
liabilities and bounds are synthetic examples, not a spending permission.

The shared-store protocol reads the current guest, owned session/incident usage,
global ledger and selected attempt in one atomic transaction. Guest and incident
counters must be provisioned atomically with those records. Missing established
state denies; it never initializes zero counters or replenishes an allowance.
Operator budget creation is exclusive. Public/protected phase ceilings are
absolute liabilities, not top-ups, and callers cannot select a pool by role claim.

A stable start key creates one run with one immutable deadline and at most one
active run per guest. Initial acquisition plus two recaptures retain their lifetime
counts after failure or expiry. Each model attempt reserves root/pool capacity and
consumes a call slot; at most two attempts per logical operation and four per run.
Allowlisted tools have separate single-use invocation IDs and a six-operation cap.
All policy values can be tightened through the validated configuration boundary.

Reservation is separate from a one-time dispatch claim. Only a newly acknowledged
claim may lead to one provider invocation when T10 wires that boundary. A claim is
intent, not a provider receipt. A lost acknowledgment cannot grant redispatch;
unknown liabilities remain reserved. Post-commit expiry denies returned admission
without erasing the committed reservation or counters.

Trusted complete usage reconciles its original attempt/rate even after expiry,
without reopening execution. Over-bound usage or unrepresentable cost durably
opens the circuit before an error is returned. A late worker terminates only its
own run; it cannot clear a newer run. Pure verification has its own six-use counter
and works without paid ledger/phase availability. Retained-image access remains
in the guest service and is independent of the paid circuit.

## Independent acceptance and corrections

A read-only reviewer derived SA01–14 before the implementation. Two reproduced
REQUIRED_CONTRACT findings were corrected and independently verified:

| Finding | Reproduced impact | Correction and regression |
| --- | --- | --- |
| SA-R01 | Deleting established session or nested incident usage reset exhausted acquisition/verification allowances | Require both initialized owned counter records; four exhausted-then-deleted cases deny without reconstruction. Original failing evidence retained. |
| SA-R02 | New/duplicate reservations returned metadata after commit crossed the run/session deadline; dispatch still had a separate guard | Recheck authority/deadline after commit; two persistent regressions and eight independent boundary probes verify denial without refund. |

The reviewer also exercised competing claims, lost reserve/claim/reconciliation
responses, circuit persistence and expired-worker isolation. Restoring the old
behaviors in memory made the corresponding regressions fail. No remaining
reproduced blocker exists in this bounded local slice. A phase change after an
already acknowledged, reserved claim does not retroactively erase that intent;
no extra liability or duplicate dispatch was observed. Universal instantaneous
revocation is not claimed.

## Verification and remaining work

**36 focused cases and Ruff passed** at independently bound source/test hashes.
Full local locked checks passed: **325 unit and 48 Chrome browser tests**.
Hosted checkpoint verification is pending.
Detailed acceptance, original failures, corrections and reviewer receipts remain
in ignored `.local/run-records/`. Counts overlap with full-suite totals.

Actual Firestore atomicity, multi-instance admission, guest/incident plus counter
provisioning, request/session rate limits, provider wire-attempt enforcement and
remaining account funds are not proven by the fake store. T10 must check remaining
deadline at the actual provider consumer. T09/T16 integration must run currentness
and invalidation on every read even after deterministic verification is exhausted;
the counter method documents but does not itself implement that caller behavior.
Observation/correction persistence and T11 simulated-action transactions follow.
Real T08/T09 and public-admission gates remain open. No source approval or release
freeze follows from this checkpoint.

# Owned guidance lifecycle — local integration checkpoint

The enrolled Firestore adapter now atomically provisions one bounded learning
aggregate with a new guest. Missing enrollment or records fail closed; reads do
not recreate state or reset lifetime counters. An immutable guidance request binds
current source/observation/result, actual acquisition completion, incident usage,
observed capability and the active wording revision. Unknown capacity denies a
new actionable request.

Structured feedback can produce only the fixed V1→V2 wording candidate. Source
and extraction disputes remain human investigation. The owned evaluator reserves
one numbered attempt/lease, executes the actual fixed six-case/nine-variant suite
outside database transactions, and retains complete execution evidence. A passing
owned report and exact current evidence/base bindings precede explicit activation.
Rollback changes the pointer to prior content at a higher revision. Prior guidance
and shared model/acquisition/verification counters remain unchanged.

Independent local SDK/fake-RPC integration verified the full persisted loop,
cold reads, source races, missing completion, lost-start acknowledgment, lease
expiry, ownership and HTTP denial boundaries. Three required corrections were
reproduced and verified: full confirmation hashes on logical retries, reserved
receipt capacity for rollback, and explicit monotonically numbered attempts.
New-key aliases retain their content binding, consume a bounded alias allowance,
and cannot consume the reserved distinct-operation/rollback receipt slots.
Eleven independent integrated probes passed; the complete HTTP loop also passed.

Current full local checkpoint: 1,307 unit checks and 63 Chrome checks passed.
Those existing browser checks do not establish the newly connected guidance
controls' complete F6 journey. The six learning cases are not added to the core
model-quality denominator. Local fixtures and injected capability observations
are explicitly test evidence, not actual cloud availability or model success.

Remaining T35 gates: durable HTTP refresh/mutation throttling, running guidance
browser flow and recovery, actual deployed Firestore races, capacity observation
integration and public/security acceptance. These gates are open; P0-13 and T17
are not complete. The production preparation entry point still stays closed.

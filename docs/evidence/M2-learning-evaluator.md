# Fixed guidance evaluation — pure first slice

This T35 increment actually executes the six predeclared L01–L06 cases under
the two existing allowlisted wording policies. Nine condition variants run in
both branches, for 18 branch executions. Both policies pass the fixed safe
cases; this establishes no accuracy uplift or measured improvement in capture.
T35, AC-43 and the connected learning journey remain incomplete.

The requirements-derived acceptance and synthetic inputs were recorded before
candidate execution. Inputs use entirely fictional labels and an example.invalid
authority; their technical review marker is explicitly not human approval. No
development-gold source or protected final-case input was read or relabeled.
The earlier expectation registry is unchanged and retains its historical status.

## Executed behavior

Each branch calls the existing deterministic verifier, semantic currentness
check and allowlisted renderer. Independent expected behavior checks required
fields, ambiguity, identity, currentness and action eligibility. Every variant
records actual instructions and seven paired invariant hashes: source truth,
observations, required fields, verdict/reasons, action eligibility, currentness
and lifetime counter inputs. Missing variants or any failed check prevent PASS.

- L01 asks for a missing lot, preserving case and leading-zero guidance.
- L02 preserves the ambiguous raw date without inventing a normalized date.
- L03 separately exercises ALL and NOT_SPECIFIED without unnecessary guidance.
- L04 requires identity recovery despite an equal lot; identity cannot be skipped.
- L05 executes valid capacity, own acquisition exhaustion, own verification
  exhaustion and resource denial. Counts do not reset; review eligibility remains.
- L06 executes changed-source and changed-observation currentness, exact
  confirmation bindings and monotonic rollback. Restoring earlier policy content
  does not restore an earlier revision or make an old confirmation valid.

The reusable guidance and activation predicates operate on explicit typed inputs.
They do not authenticate records, reserve capacity, prove a real evaluation
passed, or write an activation. The later owned service must derive authoritative
state and evaluation status itself and enforce ownership, expiry, lifetime limits,
idempotency and atomic transitions. Uploaded execution reports cannot authorize it.

## Bounds and lineage

Preparation admits exact pinned fixture/expectation bytes and hashes the fixed
owned modules that govern the checks. Execution performs no file, network,
storage, provider, random-ID or model operation. Reports bind those code/input
hashes, both policies and the complete effective non-secret configuration.
Shared acquisition/verification limits are supplied explicitly, without creating
a real budget or allowance. The retained execution uses synthetic-only limits.

Existing strict RetailPolicy bounds remain: 30-second evaluation deadline,
16,384-byte report and 240-character instruction defaults. An input-byte bound
of 262,144 and the existing typed verifier/read policies are configurable and
hash-bound. Exact boundaries and effective overrides are exercised. No report
limit was increased. Oversize reports are rejected without truncation; the full
fixed artifact remains internal unaccepted evidence.

Aware wall time and finite monotonic time are checked around each branch and
after serialization. An optional shorter lease limits execution; equality expires.
Checks are cooperative, with no claim of hard thread interruption. Failed or
expired reports retain all completed and partially completed branch outputs.
Initial clock failure rejects preparation for execution; later clock or stage
failure returns a fixed-code nonpassing artifact without raw exception detail.

The response includes computed pass fields. Durable strict-record serialization
uses round_trip=True; ordinary response JSON is not an accepted record input.
An actual local run passed six cases/nine variants/18 branches in 14,814 response
bytes (14,604 strict-record bytes), within the unchanged report bound. These
measurements describe that run, not every possible timestamp representation.

## Verification and remaining work

Two reproduced REQUIRED_CONTRACT root causes were corrected at the evaluator
boundary, with failed evidence retained privately. Final deadline/invalid-clock
conversion initially included computed fields and failed strict parsing, losing
the partial report; conversion now uses strict round-trip data. Provider clock
and unexpected stage exceptions initially escaped and discarded partial output;
fixed boundary handling preserves nonpassing evidence. BaseException interruption
semantics remain unchanged. The generic record helper was not broadened.

Focused tests pass 57 cases. They cover actual execution, independent
semantic negative controls, mutation/purity, policy and fixture lineage, exact
input/report bytes, deadlines, partial failures, typed activation binding and
monotonic rollback. The independent semantic review passed 264 affected checks
before the final failure-boundary correction, then 83 targeted checks on the
corrected source. A separate clock/size/purity review passed all 57 primary cases
and 37 private probes on that same source. Both independently verified the two
corrections with controls that restore the failures. Full local locked bootstrap,
Ruff, 1233 unit and 50 Chrome checks PASS. Hosted checkpoint `f93762b`,
[run 39110509339](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39110509339),
passed locked bootstrap/Ruff, 1233 unit and 50 Chromium checks. Remote head verified.

No persisted feedback/candidate, reserved evaluation attempt, lease transaction,
activation/rollback write, changed future recapture, HTTP route or UI integration
is implemented by this increment. These require the next owned service and
adapter work, then real-service and browser evidence. T08, human UK/new context,
remaining gold/H custody and final submission gates are unchanged. U02 stays
approved; no release freeze is claimed.

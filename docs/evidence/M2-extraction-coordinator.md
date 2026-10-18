# Owned extraction coordinator and status recovery

Status: LOCAL/PARTIAL T10. The complete installed-ADK journey ran against mocked
HTTP and the generated Firestore SDK with a synthetic RPC server. No real model,
cloud resource, application mount or paid runtime was activated.

The owned command selects only a server-listed source, retained capture IDs and
expected observation revision. Preparation, admission, counting, generation and
publication share the original deadline, including a carried monotonic deadline.
Only a newly acknowledged admission executes. Retries and lost-admission recovery
look up the original run before rebuilding changed inputs; they never redispatch.

A valid source-agreeing proposal publishes one extraction, deterministic result
and immutable completion proof. Source disagreement retains an invalid diagnostic
envelope without observation values. Missing or ambiguous fields retain their
typed state. Completion, not a terminal flag alone, establishes a finished current
result. A newer failed/incomplete acquisition cannot revive an older result.
Status contains bounded workflow states and revisions, without provider bodies,
private accounting or storage errors. Unknown publication outcomes reconcile by
run/request key; no automatic retry, refund or history reset follows.

## Corrections and verification

Independent review reproduced private storage exception chaining at the outer
owned entry points. Sanitized errors are now raised outside the handling context;
traceback negative controls verify the boundary. A second reproduced defect let
withdrawn source review leave evidence/status current while the action endpoint
correctly denied a hold. Shared pure semantic currentness validation now compares
the stored result against the actual current source support and predicates, even
if an adapter fails to advance its epoch. It creates no result, quota reservation
or receipt and preserves deliberate re-verification.

The deadline test originally depended on real setup fitting a one-second window.
A slower host could safely reject earlier and fail its expected call count. The
regression now controls monotonic time and exercises the real asyncio timeout
callback, including preparation and extra setup overhead. Product deadlines were
not relaxed. The original failures remain in private verification evidence.

Coverage includes success → simulated hold → refresh, both affected SFA identities,
unresolved third identity, missing date, source disagreement, invalid/foreign
captures, withdrawn review, source/predicate changes, malformed/failed transport,
concurrent duplicate commands, lost admission/publication acknowledgments,
expired ownership, bounded lifetime acquisitions, output redaction and delayed
blocking phases. Independent final verification passed 396 overlapping scoped tests, Ruff and nine
additional end-to-end/support probes. Negative controls restored five currentness
failures and two deadline failures. Full local locked/Ruff checks passed 936 unit
and 50 Chrome tests. Exact-head
hosted validation remains pending at this checkpoint.

## Remaining integration

An unfamiliar raw product name alone stays REVIEW_REQUIRED. The reviewed synthetic
third-identity negative still needs a server-owned identity-resolution binding;
model output cannot supply its review authority. HTTP extraction routes, reviewed
fixture integration, source selection/update orchestration, real service/model
checks and connected UI remain. Human UK/context/gold/H and final-submission gates
remain separate. No release or accuracy claim follows from these synthetic tests.

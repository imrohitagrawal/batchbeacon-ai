# Injected extraction HTTP journey

Status: LOCAL/PARTIAL T10/T12 integration. The explicit offline test factory now
connects guest/upload/evidence/actions with the owned extraction coordinator.
Default application routes remain unchanged. No provider, cloud resources, paid
allowance, deployment or real-service journey was activated.

The start command accepts only a server source selector, one/two retained capture
IDs and expected observation revision. The owned incident comes from the path and
the operation key from a single header. Cookie ownership, origin and CSRF precede
body parsing. Strict JSON, actual streamed byte limits, encoding/read deadlines,
extra-field rejection and unambiguous authority headers remain enforced.

Run status and original-key recovery are read-only and model-free. Recovery keys
stay in headers. A run must belong to both the session and requested incident.
Responses contain bounded workflow state/revisions only. Lost-response or deadline
uncertainty directs recovery through the original key, without claiming rollback,
refund, cancelled provider execution or a new attempt.

The existing threadpool drives the async coordinator inside a synchronous worker,
keeping blocking store/object work off the ASGI event loop. Configured process
capacity is acquired nonblocking inside that worker and released only when it
actually finishes. Shared admission remains the distributed lifetime/cost/run
authority. Client cancellation cannot terminate a Python thread or release its
capacity early. Original-key status resolves any completed result afterward.
The coordinator deadline starts at coordinator entry; preceding HTTP reads and
threadpool scheduling are distinct, so this is not a fixed HTTP-latency guarantee.

## Review and checks

Independent fault probes reproduced two REQUIRED_CONTRACT defects: cookie-name
whitespace was normalized differently from the actual parser, allowing ambiguous
capability input; and scope could expire after worker acknowledgement but before
response serialization. Cookie-key normalization now matches the parser, and the
immutable server scope is rechecked at the response boundary. Original failures
are retained; five checked-in regressions cover the corrections.

The focused HTTP matrix passes 65 cases using installed ADK, generated Firestore
SDK and mocked HTTP/RPC. It covers a complete request→extraction→evidence→explicit
simulated hold→refresh journey, strict/duplicate input and headers, source fields
that cannot assert authority, session/incident denial, unknown completion recovery,
private errors/headers, expiry, event-loop responsiveness, worker cancellation,
capacity overrides and default-app absence. Independent verification passed all 65 primary cases and 15 additional probes;
negative controls reproduced both original defects. Full local locked/Ruff checks
passed 1001 unit and 50 Chrome tests. Exact-head hosted validation is pending. These are local protocol tests, not actual
model accuracy, deployed performance, real Firestore or user-facing runtime proof.

The approved UI is unchanged. Identity-fixture resolution, source orchestration,
real-service/model admission, connected UI, remaining human source/gold/H review
and final submission retain their gates. No release freeze follows.

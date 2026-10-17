# T08 — bounded operator runner preparation

Status: local installed-SDK/mock-HTTP boundary verified. **Paid admission remains
closed; G0-X has not passed.** This increment creates no public endpoint and makes
no real model, database, storage or deployment claim.

## Implemented boundary

`probe_runner.py` connects the installed ADK and GenAI SDK to the durable operator
ledger. It validates exact source/image bytes and sanitized still-image limits,
counts the final ADK request including its instruction and output schema, and
compares counted and generated context at the final HTTP hook. It restricts the
endpoint, method, configuration and request count; it disables retries and SDK
continuation. A fresh policy/deadline check surrounds counting, reservation and
dispatch intent.

CountTokens is an admission estimate. A separate, evidence-backed billable input
bound and response-plus-reasoning bound are required for the reservation. Test
fixture values are synthetic and do not substantiate a real provider billing
ceiling. The runner's timeout and response-byte limits also do not establish a
server-side billing bound.

Finite byte/pixel limits are strict typed policy fields. The final request,
effective policy, grant and input hashes bind the private receipt. Successful HTTP
response bytes are retained before parsing, including invalid JSON/schema output.
Complete usage evidence is saved durably before reducing a reservation. Unknown,
interrupted or incomplete outcomes retain the full reservation; over-bound usage
opens the cost circuit. The journal records dispatch intent without asserting
provider receipt. Atomic replacement preserves the preceding receipt when a later
write fails; client cleanup still runs.

This is an explicitly initialized, serialized operator adapter. It cannot replace
T09's persistent cross-instance public admission and guest isolation boundary.
No real allocation has been initialized.

## Review findings and corrections

The independent reviewer reproduced three **REQUIRED_CONTRACT** findings within
the accepted evidence-integrity requirements. All were corrected at their
responsible boundary and independently verified:

| Root cause | Reproduced impact | Correction and regression |
| --- | --- | --- |
| In-place receipt rewrite | A failed final write could destroy the usage evidence after reducing the ledger reservation. | Atomic private replacement; inject a partial write after reconciliation, then verify the preceding receipt/hash, retained ledger evidence and both client closures. |
| Raw output absent | A schema-invalid response retained only a hash, preventing inspection of the actual evidence. | Save bounded exact bytes before parsing; verify invalid-schema and malformed-JSON bytes and hashes. |
| Dispatch label overstated transport | Expiry after the intent save could prevent HTTP transmission while the receipt claimed dispatch. | Record intent only; expire at that point and prove only CountTokens reached the transport, with full unknown reservation retained. |

Independent negative controls made the relevant regressions fail when each
correction was removed. Exact-byte and one-byte-over count/generation response
limits also passed. Original failure records remain in the ignored local evidence
store; no remaining reproduced blocker exists in this local increment.

## Actual verification

- **104 focused tests passed**, covering runner, admission and installed-SDK
  transport; independent reviewer repeated these and Ruff/whitespace checks.
- **222 full unit tests passed**, with the existing Starlette/httpx deprecation
  warning. Locked dependency check and Ruff passed.
- Initial default local browser invocation could not launch because the bundled
  Playwright browser was absent. This was an environment prerequisite failure,
  not a browser assertion failure. The explicit installed-Chrome run passed all
  **41 browser tests**. Exact hosted bundled-browser verification remains separate.

These tests inject credential-free mock HTTP responses into the real installed
SDKs. They are not actual paid inference or provider-compatibility evidence.

## Remaining real-admission proof

The bounded follow-up research did not establish a complete safe reservation
within the existing model-probe pool. [Google's image tokenization documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/image-understanding#image_tokenization)
provides resolution-specific image allocations, but the runner does not yet bind
an explicit resolution. [Token-count guidance](https://firebase.google.com/docs/ai-logic/count-tokens)
does not make the approximate characters-per-token ratio a worst-case byte bound.
The installed local tokenizer does not support the candidate model; another
model's tokenizer is not admissible evidence.

The [model card](https://deepmind.google/models/model-cards/gemini-3-8-flash/) and
[thinking guidance](https://firebase.google.com/docs/ai-logic/thinking) describe
output limits and the response/thinking relationship. The reviewed material did
not establish the complete endpoint-applicable numeric billing ceiling needed
for this Vertex request. No conditional arithmetic is promoted into a bound.

At the retained account rates, reserving the full published input context alone
exceeds the model-probe pool before output. Prior incurred/unbilled liabilities
and available global capacity also remain unsubstantiated. Price discovery is not
proof of zero prior spend. Keep admission closed; do not borrow protected pools,
increase authority, substitute an unreviewed model or initialize from fixture data.
Independent source/custody preparation may continue while these facts are resolved.

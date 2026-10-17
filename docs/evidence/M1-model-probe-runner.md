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

## Hosted timing correction

Hosted run [39078682730](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39078682730)
at `a319365f87a475f9a476686caf09567c9f200c73` passed bootstrap, browser installation,
lock and Ruff, then returned **221 unit passes / one failure**; browser assertions
were not reached. The failed test assumed setup plus CountTokens would always fit
inside 100ms, so it expected expiry only after reservation. On the slower host the
same overall deadline expired before reservation. The application stopped safely;
no false acceptance, lost reservation or additional dispatch was reproduced.

Classification: **REQUIRED_CONTRACT** for deterministic test/hosted-check
portability. The owner is the primary integrator. The correction replaces real
sleeps with a controlled monotonic clock and exercises the real event-loop
timeout callback. Three cases cover expiry during generation, during counting and
before the first HTTP request, with the corresponding request and reservation
counts. Runtime code and the approved visuals are unchanged. The original failed
hosted logs are retained privately; corrected hosted verification is still required.

The correction passed **106 focused tests**, **224 full unit tests**, lock/Ruff
and **41 local Chrome browser tests**. Independent verification reproduced the
focused pass and used negative controls: disabling the outer timeout made the
generation-expiry case fail; disabling both deadline mechanisms made all three
cases fail. The failed hosted log hash is preserved. No runtime code changed.

A second hosted run, [39078921450](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39078921450),
passed the corrected shared-deadline cases but found the same timing assumption
in the separate per-phase timeout test (**223 passes / one failure**, browser
assertions not reached). This is a **DUPLICATE** symptom of the same test-portability
root cause. The first correction and review were too narrowly scoped to the
initial failing test. The revised plan audits every sleep/deadline use in the
runner, transport and admission suites before the next checkpoint.

The remaining per-phase test now controls monotonic time during setup and expires
the real outer timeout inside the selected HTTP phase. It additionally verifies
the exact retained monetary liability. No positive real sleep remains under the
short probe-test deadlines. Runtime enforcement and the approved UI remain unchanged.
Both failed hosted records remain retained; no release evidence has been frozen.

Independent timeout-family review then passed all 106 focused checks and the full
224-unit/41-Chrome suite. Injecting 120ms of real setup reproduced both prior phase
failures and passed all five corrected timing cases. Disabling both deadline
mechanisms made all five fail. A separate primary full run found an intermittent
normal skip-link test sequencing issue, documented in M1-usability-audit.md; its
correction waits for navigation completion and preserves the separate rapid-path
regression. These changes affect tests only. Fresh hosted verification remains
the final checkpoint requirement.

## Verified hosted checkpoint

[Run 39079297482](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39079297482)
passed at `eee8e265dba3e7dcf799a604c66d5e9cd0940da7`: locked wheel bootstrap,
bundled Chromium installation, lock/Ruff, **224 unit and 41 browser tests**. Logs
were inspected and the remote main ref verified. Both previous failures remain
preserved. This closes the local/hosted preparation correction; real paid inference,
Firestore/image/service probes, public security and release gates remain open.

# T08 external admission — acceptance and preparation

Status: IN PROGRESS. No real model call, runtime database/image probe or deployment
has passed. This record does not close G0-X, G1, visual approval or public access.

## Acceptance established before implementation

An independent read-only reviewer derived these cases from AGENTS, OPERATIONS,
EXECUTION, EXECUTION_POLICY, `prompts/02-first-slice.md`, MVP and task T08 before
inspecting new builder code. The integrator retains the requirements snapshot
hashes and detailed discovery evidence in ignored `.local/run-records/`.

| ID | Required evidence |
| --- | --- |
| G0X-01 | Typed, immutable effective configuration; explicit project, model, currency, finite limits and expiry; configuration hash in receipts. Invalid, incompatible or expired input fails before work. |
| G0X-02 | Actual target resource/API/IAM inspection, exact commands and finite cost allocation. No implicit replacement, public storage or broader runtime privileges. |
| G0X-03 | Durable atomic reservation before paid attempts, including retries; restart, exhaustion, duplicate and unknown-outcome tests. Unknown prior liabilities never initialize as zero. |
| G0X-04 | Actual bounded ADK/Gemini trace after fake transport proves effective timeout, attempt, tool and call limits; invalid output remains a failure. |
| G0X-05 | Count/bound exact final context including image, source, system instructions and schema. Retained image bytes match supplied bytes. Unproved output/reasoning bounds refuse the proposed reservation. |
| G0X-06 | Real Firestore write/read/transaction under deployed runtime identity, then fresh-request persistence. No external effects in retryable transactions. |
| G0X-07 | Private uniform-access bucket with public-access prevention; exact image read, wrong-owner/anonymous/expired denial and retained metadata. Access expiry does not wait for deletion. |
| G0X-08 | Private Cloud Run revision/digest and actual deploy/build/runtime identities; inspected instance/concurrency/CPU/memory/time limits. Anonymous access denied; health makes no model call. |
| G0X-09 | Version/configuration/input hashes, attempts, duration, usage, gross cost and terminal outcome. Failed/unknown outcomes retained; public evidence contains no credentials or account details. |

T08 may use a serialized operator-only durable reservation for a controlled probe.
It cannot serve as the public application ledger: T09 must implement shared
cross-instance admission, guest ownership and upload controls. T10/T11/T13 still
own the integrated source/image/ADK/verifier/confirmed-action/refresh journey.

## Installed dependency inspection

Observed versions: ADK 2.12.0, google-genai 2.31.0, Firestore 2.34.1 and Storage
3.17.1. Installed code confirms HTTP timeouts are milliseconds and retry attempts
include the original call. Absent retry options produce one attempt, but an empty
retry-options object defaults to five. ADK's default call limit is 500 and
nonpositive values disable enforcement. Explicit settings are required.

Primary references: [ADK runtime configuration](https://adk.dev/runtime/runconfig/),
[GenAI SDK](https://googleapis.github.io/python-genai/),
[Gemini 3.8 Flash](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash),
[thinking configuration](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/thinking),
[token counting](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/get-token-count).

Verified account INR model rates are recorded in [M1-cloud-pricing](M1-cloud-pricing.md).
Prices alone do not prove remaining funds. The proposed 12,000-input/4,096-total-
output bound gives ₹4.67657189993504 gross; it is not an admitted paid budget until
complete billed usage bounds and prior liabilities are substantiated.

## Local preparation result

`cloud_policy.py` now provides strict immutable model/price/timeout/attempt settings
and a separate reviewed-allocation record. `operator_admission.py` provides an
explicitly initialized private SQLite ledger. Unknown prior money or attempt
history refuses initialization. Reservations commit atomically, survive restart,
cannot be reused, and retain their full liability on interruption. Calendar
rollover does not replenish money or lifetime attempt counts. Only complete
provider usage can reconcile an existing reservation. Changed settings/grants,
expired windows and exhausted balances deny new work.

No real allocation/ledger has been initialized. Evidence hashes in these records
refer to reviews that the operator must actually substantiate; constructing a
record is not authority. This module is not attached to any public endpoint.

Validation on the current source: lock and Ruff passed; **164 unit tests passed**,
including 42 admission cases and four mock-transport cases. The latter run the
installed ADK and GenAI SDK together through an in-memory HTTP transport with
synthetic credentials. They observe the configured project/global/model endpoint,
one candidate, output limit, seven-second HTTP timeout override, LOW thinking,
no tools/cache, and one HTTP attempt on both 429 and 503. The SDK serializes the
nested thinking field as `thinking_level`; actual provider compatibility is still
unverified. These tests do not count as real inference or completed extraction.

Independent review passed the initial 39 admission cases and 20 additional checks,
including eight competing processes with exactly one affordable reservation,
expiry/day boundaries, restart, changed grants and private-file controls. A
reproduced **ADVISORY_DEBT** finding concerned impossibly large reported usage:
the ledger rejected it without blocking later attempts. A small correction now
persists an open cost circuit while retaining the unknown reservation. Its failing
regression was preserved before the correction. Incremental independent review
passed all 43 admission/transport cases, Ruff and whitespace checks; it separately
verified the overflow circuit survives restart and denies another attempt.
A subsequent installed-SDK check reproduced a separate **REQUIRED_CONTRACT**
gap: automatic continuation followed a provider continuation token with a second
HTTP request inside one ADK call, despite retries being disabled. The failing
mock regression observed two requests. The policy now explicitly disables that
SDK feature and rejects attempts to enable it in this single-attempt adapter.
The regression observes one request after correction. Independent verification
reproduced two requests using the prior commit's exact configuration and one with
the correction, passed all 46 focused cases and rejected malformed Python/JSON
feature settings. No reproduced blocking finding remains in this increment.

Local browser tests were not repeated for this backend-only preparation. The
existing UI revision has its own verified hosted result in [M1-hosted-ci](M1-hosted-ci.md).
The initial T08 revision `bd2292ce4694ff3766a8d5b875cb09f5d532f200` passed
[hosted CI](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39075077395):
lock/Ruff, 161 unit and 36 bundled-Chromium browser tests. Its logs were inspected.
That run predates the continuation correction and does not verify the later code.

## External discovery result

Five missing APIs were enabled under U10: Run, Vertex AI, Cloud Build, Artifact
Registry and IAM. A subsequent successful listing verified them. No database,
image bucket, runtime account, application build, deployment or model call was
created by this increment. Successful scoped resource lists returned no Firestore
database, project Storage bucket, Mumbai Cloud Run service or Mumbai Artifact
Registry repository. Default build identity and resulting service-agent bindings
were retained privately and independently reviewed. The resolved default is the
Compute Engine default service account; it has no direct role in the observed
project policy. The legacy Cloud Build identity has `roles/cloudbuild.builds.builder`.
New service agents have provider service-agent roles; no service-account Owner/Editor
binding appeared. Source-build/runtime permissions remain unverified. API
dependencies additionally enabled Container Registry, IAM Credentials and Pub/Sub.
Refresh relevant resource discovery before creation; earlier account/database/
bucket snapshots predate this enablement.

The authenticated current-month billing report lists charged projects but no
BatchBeacon entry. This is a lagged reported-cost observation, not proof of zero
incurred/unbilled costs. The report DOM is retained privately; a CSV download
was attempted but completion was not verified. No paid balance is inferred.

## Still required before paid execution

Substantiate prior liabilities/global capacity and the complete response/reasoning
billing bound; bind the exact counted request bytes; integrate single-use admission
and a fresh deadline check at the actual call boundary; exercise timeout/unknown
outcomes there. Complete actual identity/IAM, resource-price, private deployment,
Firestore and image-access checks before claiming G0-X. Public admission remains
dependent on T09's shared ledger and security boundary.

## Subsequent runner checkpoint

The [bounded operator runner](M1-model-probe-runner.md) now binds the exact final
count/generation context, single-use ledger reservation and fresh deadline checks
at the installed-SDK HTTP boundary. Independent regression verification closed
three receipt/output/dispatch-evidence findings. The record above preserves earlier
checkpoint counts; the newer local boundary has 104 focused and 222 full unit passes.
Real bounds, prior liabilities, service probes and public runtime admission remain
open. U02 was separately approved in M1-visual-approval.md; T08 does not grant it.

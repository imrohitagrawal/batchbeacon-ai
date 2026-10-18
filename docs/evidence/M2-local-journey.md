# T12 incident HTTP boundary — local protocol checkpoint

Status: LOCAL/PARTIAL. The explicit injected test factory exposes evidence,
correction, action preparation, confirmation, history and reconciliation routes.
The default preparation app and approved visual prototype remain unchanged.
Preseeded fake stores prove wire behavior, not a complete new-guest product journey.

## Access, commands and responses

Only the configured guest cookie supplies bearer authority. Every incident/action
read is owned and expiry checked. Mutations and identical retries require exact
Origin plus session CSRF; owned incident lookup precedes command-body parsing.
Client-supplied actors, roles, verdicts and source-review flags are rejected.

JSON bodies have typed, hashed byte and read-time limits. The reader counts actual
stream bytes regardless of Content-Length, enforces UTF-8 JSON and rejects duplicate
keys, non-object bodies, unsupported encodings, malformed and excessively nested
input. Cancellation propagates. Strict JSON schemas reject numeric confirmation
and coerced revisions. Request keys are bounded; command handlers do not invent
retry keys. GET bodies, duplicate query keys and unrecognized query fields deny.
Existing guest list/capture reads now enforce the same body-free contract.

Evidence responses preserve selected original values, corrections, provenance,
capture references, revision histories and freshly computed currentness. Internal
provider-response bodies, capability identities and configuration diagnostics are
not retail response fields. An old correction retry reports both its recorded
revision and the latest evidence state; it never reactivates the old observation.

Preparation creates no action. Confirmation carries the exact reviewed target and
strict explicit true into the transactional action service. Concurrent keys still
deduplicate one logical simulated action. Changed dependencies make past actions
historical; lost acknowledgments preserve uncertainty. An unavailable write returns
503 with unknown outcome, and a failed reconciliation never reports absent success.
All handled responses retain private cache, no-sniff and no-referrer headers.
No extraction, result, source-trust, budget or operator write endpoint is exposed.

## Independent acceptance and corrections

A read-only reviewer derived HTTP01–14 before implementation, covering access,
stream limits, strict wire inputs, provenance, idempotency, races, unknown outcomes,
configuration and service reconstruction. Two reproduced defects were corrected:

| Finding | Demonstrated impact / classification | Correction |
| --- | --- | --- |
| HTTP-R01 | Replaying an old correction always reported that verification was required, even when the latest state had been verified; REQUIRED_CONTRACT response-currentness error, no stored-history reactivation | Read fresh evidence after the stored receipt and return separate recorded/latest revisions and currentness. |
| HTTP-R02 | A 20,007-byte deeply nested JSON command within the byte cap returned an unhandled plain-text 500 without private cache headers; REQUIRED_CONTRACT error-response violation, no mutation | Map parser recursion failure to the existing safe 422 invalid-command response. Both mutation routes are covered. |

Independent recheck: **122 API/guest tests**, Ruff and whitespace checks passed.
The reviewer restored each previous behavior in memory and observed its regression
fail. Additional probes covered streamed-body expiry, uncertain correction commits,
altered target hashes and overridden receipt limits. No remaining reproduced
blocker was found in this local slice. Failed and passing outputs, exact source
hashes and classification receipts are retained in ignored `.local/run-records/`.

Full locked local checks passed: **477 unit and 48 Chrome browser tests**, plus
lock validation and Ruff. Counts overlap with the focused checks; do not add them.
[Hosted run 39084510141](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39084510141)
passed at `314ef06e36439668ce02c4e019d59c8d2730f6fe`: locked wheel bootstrap,
browser installation, lock/Ruff, **477 unit and 48 Chromium browser tests**.
Hosted logs and exact checkout inspected; remote main verified. No release freeze.

## Remaining integration gates

The real store must atomically provision session usage with guest creation and
incident usage/evidence/action state with incident creation, then use one coherent
conflict-detecting snapshot for all participating services. This factory does not
manufacture missing records: a newly created incident without that adapter returns
an explicit unavailable-state error. No frontend is connected to this factory.

Actual Firestore/Storage behavior, real bounded extraction, complete incident
journeys, runtime UI acceptance and deployment remain unverified. Paid admission,
pending source-context/UK human review and final submission gates are unchanged.
No task-complete, real-model, hosted-product or release-freeze claim follows.

# Original reservation settlement after a configuration change

Status: local preparation only. This does not change the deployed runtime, transfer
budget, release an unknown reservation, or pass current real-model acceptance.
[M7](M7-judge-readiness.md) remains the deployed repair evidence.

Changing the model configuration or grant previously made an original outstanding
attempt fail the ledger's strict grant comparison. The optional
`RuntimeConfig.predecessor_liabilities` manifest allows only recording the original
response and reconciling its usage for explicitly listed reservations. Both the
Firestore adapter and admission service enforce the same manifest.

The manifest binds the original policy/grant, exact claimed unknown reservations,
successor grant/policy, and project/database/namespace/environment. Immutable attempt
fields must still match. Settlement uses the original price and limits, charges the
same cumulative pool once, and does not rewrite historical grant identifiers or
reopen guest access, results, actions or the original dispatch. Nonbillable settlement
requires a separately bound original rule. Missing bytes remain unknown; configuration
cannot recreate a lost provider response. No new public settlement route exists.

Omitting the manifest preserves existing runtime serialization/digests. The new image
can read existing configuration; an old image cannot parse a configuration containing
the new field. Activation or rollback involving a changed grant requires its own
reviewed compatible configuration and conditional metadata migration.

## Verification and limitations

- Combined local unit suite: 1,414 passed, plus two subsequently added
  migration-boundary regressions passed. Browser suite: 96 passed; edge suite: 29 passed. Targeted tests cover exact binding mismatches,
  expired original-rate settlement, unknown/partial response retention, concurrent
  idempotency, original-only error policy, runtime injection and SDK adapter checks.
- Actual local Firestore emulator: seven passed, including concurrent settlement across
  independent clients after a counter-preserving metadata change, and permanent
  rejection of old guest issuers without resetting counters. This is not cloud
  IAM or deployed service evidence.
- Independent implementation review: 32 targeted tests plus 11 additional binding
  and operation checks passed. Independent deadline review: 16 tests passed.
- Controlled tests cover a proposed 40-second HTTP timeout within a 50-second run,
  generation after the former 30-second deadline, remaining-time clipping, late
  accounting without fresh success, cancellation and unresolved-call retry denial.
  The new delayed-response tests advance injected UTC and use immediate fake HTTP
  responses. They do not prove real elapsed-time completion or provider reliability.
- HTTP ownership/body processing precedes the acquisition timer. Synchronous
  Firestore persistence/reconciliation/finalization can outlast that timer. Ten seconds
  of nominal margin under Cloud Run's 60-second timeout is not a worst-case guarantee.
  The proposed settings remain a bounded experiment, not an activated timeout fix.

Review advisory: a preexisting generic configuration with multiple calls and an
undrained active old run can reserve a new attempt under a successor policy. The
actual one-call production configuration excludes that additional-call scenario;
migration additionally fences old issuers and existing-session database writers. This preparation does not certify arbitrary active-run migrations.

## Remaining activation gates

1. Apply the owner-approved [U31](../OWNER_DECISIONS.md#u31--bounded-model-pool-reallocation)
   transfer only through reviewed conditional migration; preserve the total ceiling
   and original unknown reservation. Refresh actual balances before any paid admission.
2. Bind a reviewed manifest to the exact retained attempt and successor runtime. Close
   admission and conditionally migrate every guest metadata binding plus budget and
   grant. Reopen only with `guest-admission-2`, preserving all limits, dates and
   counters; never restore the old admission hash. Old existing-session transactions
   conflict and then fail their metadata check; old issuers fail the permanent hash
   fence. Neither terminal records nor elapsed time proves worker termination.
   Already dispatched provider calls and private object uploads may finish; retain
   every original claimed liability, and reject old publication. Preserve liability and
   existing owned records. Do not apply a successor error rule to an earlier call.
3. Complete exact hosted push/PR checks, source packaging, compatible rollback,
   finite build admission and independent runtime/migration verification before deployment.
4. Run one explicitly bounded changed real-model experiment, then the remaining
   video-parity acceptance cases only if actual capacity and prior outcomes permit.
   A successful local test or healthy page does not close the real-model gate.

Private reproduction, failed harness attempts and independent review receipts remain
in the ignored evidence store. No provider call or cloud mutation was made for this
local preparation.

The combined compatibility image also includes the [TLS trust correction](M9-tls-trust.md).
After metadata migration, rollback must retain the new admission fence and a reader
that understands the original-liability manifest. Restoring the original image or
admission hash is not a safe rollback.

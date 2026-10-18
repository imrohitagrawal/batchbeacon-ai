# Owned persistent retail queue and refresh

T34 now has a local integrated persistence and HTTP path. Incident creation,
capture readiness, acquisition/usage changes, evidence/corrections/completion and
simulated actions atomically update compact per-incident summaries. A central
finalizer reads original records and validates the staged domain overlay before
the single Firestore commit. No provider, source or object call occurs there.

The guest envelope binds the projection configuration. An unconfigured or
incompatible writer cannot access an enrolled shop. Existing unenrolled shops
are not silently migrated; missing summaries fail unavailable without GET repair.
Summary creation reuses full identity, evidence-history and action validators.

Cold queue reads obtain the owned guest/usage, complete bounded summary set,
current source environment and genuine immutable completion metadata in one
transaction. They never read full evidence/action histories or fetch images.
The normal planned maximum is `3 + N + C <= 43` documents for 20 incidents and
20 completion references, with at most three BatchGets. Independent measured
20-draft reads used 23 documents/two BatchGets. These are SDK/fake-RPC results,
not measured Cloud Firestore cost or service behavior.

Pending completion receipts contain no invented timestamps. The summary retains
original observation/result/receipt bindings; the reader hydrates create/update
times from the actual completion document. Late or changed metadata cannot make
a result current. Later corrections preserve the original completion lineage.
Fresh source semantics are checked on every queue read, including changes without
an epoch increment. Historical actions cannot conceal renewed-review needs.

Material sequence/time tracks the last incident transition. Usage-only lineage
refresh preserves that sequence when the meaningful state is unchanged. Global
source changes alter currentness at read time; they do not invent an incident
update timestamp or rewrite every summary. Counts cover the complete bounded shop
before filtering. Empty, unavailable, expired and unknown capability remain distinct.

`GET /api/retail/queue` uses the HttpOnly guest cookie and strict filter/request-key
input. The public response omits session/shop identifiers and internal policy
hashes, identifies the synthetic shop, and includes expiry, snapshot time and
limited capability observations. Successful saved-view access does not establish
working inference. The endpoint is mounted only by an explicitly injected app;
the default preparation application remains unchanged at this checkpoint.

Manual refresh admission is persistent across clients. One typed policy controls
minimum interval, finite session allowance and lease duration. Claim and release
each read guest/usage/admission and write only admission metadata; these six extra
reads and two metadata writes are separate from the read-only queue. Unknown claim
acknowledgement starts no queue read and retains the consumed allowance. Failed
reads do not refund it. Lease deadlines apply before Begin, to every data RPC and
after acknowledgement. Guest expiry is rechecked before the HTTP response.

## Verification and limits

Requirements-first independent acceptance covered every producer, cold restore,
completion truth, source races, ownership, expiry, material ordering and bounded
reads. The durable-store review passed 14 integrated cases plus six independent
probes. HTTP/refresh passed 18 integrated cases plus 27 independent probes.
No reproduced critical or required-contract defect remains in this reviewed local
scope. A draft deadline-propagation concern was corrected before a reproduced
blocker classification; its independent probes now pass. Test-construction
failures and the initial unavailable bundled-browser attempt remain private history.

The combined checkpoint passed lock validation/Ruff, the complete 1265-unit suite
and 50 installed-Chrome checks. Exact-head hosted checks remain pending; this
document does not declare a release freeze. Existing
Starlette/httpx deprecation is advisory dependency debt.

Real Firestore atomicity, deployed cross-instance behavior and network cancellation,
cloud cost admission, actual Gemini, connected browser journeys, UK/human gold/H
custody, guidance activation and final submission remain separate gates. T34 as a
whole is not complete. No paid call, resource creation or public exposure occurred
in this increment.

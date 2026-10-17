# T05 — reviewed-SFA domain checkpoint

Status: T05a interfaces and T05b pure verifier PASS for the reviewed first SFA
slice. This is a local interface checkpoint, not a release/evidence freeze. UK
human review, full development gold and protected final cases remain open.

The trusted immutable Pydantic records cover source review/dependencies,
identity/code types, predicates, retained observations/correction lineage,
verification context/results and simulated action/event records. Model/client
outputs must not establish these trusted records or actor/source authority.

The pure verifier checks identity before lot/date restrictions; preserves exact
identifier spelling, predicate operators/ranges and evidence references; aggregates
review-required cases conservatively; and separates currentness from eligibility
for a simulated hold. No network, model, persistence or transaction runs here.

## Acceptance and corrections

Independent acceptance cases were derived before implementation. Independent
review subsequently found six roots; primary reproduced them and preserved the
failed test evidence privately before correcting the responsible boundaries.

| Root | Classification and correction | Verification |
| --- | --- | --- |
| One matching typed code concealed another contradictory known code | REQUIRED_CONTRACT: contradictory identifiers now require review; reviewed alternatives remain allowed | Regression + independent rerun |
| Correction evidence/chain could detach from retained observations | REQUIRED_CONTRACT: both old/new support, chronology, field and final-value binding validated | Regression + independent rerun |
| Reviewed B/third unit inputs cited A's capture | REQUIRED_CONTRACT: each reviewed identity binds its own manifest hash | Manifest assertion + independent rerun |
| RANGE comparison discarded bounds/inclusivity | REQUIRED_CONTRACT: result rows retain operator, applies and typed bounds | Boundary/serialization tests + independent rerun |
| Serialized result could contradict eligibility/evidence | REQUIRED_CONTRACT: eligibility, candidate/source and decidable-result coherence validated | Rejection tests + independent rerun |
| Read currentness omitted live failure/freshness/policy, then over-rejected new failure-bound review results | REQUIRED_CONTRACT: bind effective context state and policy; compare it on every read, without quota-dependent reverification | Original failing evidence and four additional AC-17 failure cases retained; independent exact-boundary/unchanged-state/reordered-dependency probes PASS |

Currentness includes a context-state hash covering mode, jurisdiction, historical
selection, live status/validation time, selected current source dependencies and
result revision, plus effective freshness blockers. Clock advancement within the
same state is allowed; crossing freshness or changing state invalidates the old
result. A newly materialized REVIEW_REQUIRED result can be current for a simulated
review request while remaining hold-ineligible. This hash is lineage evidence,
not a credential or substitute for server session authorization.

## Actual verification

`BATCHBEACON_TEST_BROWSER_CHANNEL=chrome BATCHBEACON_BROWSER_CHECKS=1 ./scripts/check.sh`
passed lock validation, Ruff, **64 unit tests** and **19 local browser tests**.
The 64 include two preparation-shell checks; browser counts include four earlier
prototype checks and 15 refined-prototype checks. These are separate evidence
classes, not an evaluation-accuracy denominator.

Independent reviewer reran 64 unit tests, Ruff and the 15 refined browser tests,
and closed both remaining currentness and focus corrections. Reviewed hashes:

- contracts.py: `a36d6727be766119f2ffacc61e4dc41dc9bb82a4dd14d9f99900c831ed506504`
- domain/verifier.py: `4205eedbcc51f4432b1d496f209a257d3ed700d0c81884829ded1da364a0e639`
- test_domain_review_regressions.py: `51b560676de644bb42f7744a7b383420963f88f6281c21dd1353bfff60b4620f`

Advisory: installed FastAPI/Starlette emits a test-client httpx deprecation warning;
tests pass with the reviewed locked dependency set. No new dependency was added.
The full endpoint isolation, action transaction, quota and real-service contracts
remain integration obligations. T33 acceptance preparation can now proceed.

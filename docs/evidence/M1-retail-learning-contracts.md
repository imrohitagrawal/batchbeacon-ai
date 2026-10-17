# T33 — retailer and guidance contracts

Status: T33 local contracts PASS after independent correction verification.
Acceptance was derived independently before implementation. This is not T34/T35 persistence, evaluator execution or deployed proof.
Source: specs/retail-operations.md AC-32–43 and specs/mvp.md P0-12/13.

## Predeclared acceptance

Independent read-only review established these obligations before extension code:

- Strict immutable records reject unknown/free-text content, malformed IDs/hashes,
  naive or reversed times, duplicate references and nonpositive revisions.
- Server session/shop ownership and immediate expiry bind every child. Schemas
  carry scope but cannot authenticate a client or authorize a write.
- Snapshot rows/counts use one timestamped currentness basis, preserve incident,
  source coverage, result and actual action identity, and reconcile six categories.
  Query failure is unavailable, never a fabricated empty shop.
- Feedback binds actor, exact source/observation/result references, applicable
  recapture reference and
  structured category/detail/disposition history. It is not source or gold truth.
- Immutable candidates bind a fixed family, rule, owned feedback/evidence,
  base policy/revision and allowlisted proposed policy/hash. Unsupported feedback
  stays NO_SAFE_CANDIDATE or investigation; public arbitrary content is rejected.
- Evaluations bind attempt identity/number, original request key/payload hash,
  lease/deadline, candidate/base/evidence, suite/input/evaluator and effective
  configuration hashes. PASS requires six unique paired outputs and every
  declared invariant. Failure/expiry preserves execution evidence and allowance.
- Scoped policy transitions bind prior/next allowlisted content, exact expected
  revision, explicit actor/confirmation and candidate/evaluation or rollback
  reference. Every transition increments revision. Logical uniqueness excludes
  transport keys; a retry must not create another transition.

Queue precedence: renewed review → current eligible action → acquisition/draft →
actionable missing evidence → human review → complete current scoped negative.
Inconsistent input falls back to human review. A new current failure-bound review
is not stale merely because the source is unavailable. A current review request
still says uncertainty unresolved. Exact currentness comes from T05 verification;
client flags and old action records cannot establish approval.

## Six paired learning cases

| Case | Independent expected behavior |
| --- | --- |
| L01 | Required unresolved lot, date unrestricted: lot only, candidate adds complete-code/leading-zero hint. |
| L02 | Required ambiguous date: request the complete relevant marking; preserve ambiguity. |
| L03 | Exercise both ALL and NOT_SPECIFIED: no request for that unrestricted field. |
| L04 | Unresolved identity despite same lot: identity-first recovery, no lot/date shortcut. |
| L05 | Recapture or acquisition exhausted: no additional acquisition/reset; review-required and supported review request remain. |
| L06 | Source or observation changed: renewed review, stale action/activation denial; rollback creates a higher revision. |

Both policies already satisfy P0-05. Their source truth, observations, required
fields, verdict/reasons, eligibility, currentness and lifetime counters remain
unchanged. Six paired cases are six scenarios, separate from D01–D24/H01–H08.
The builder does not read H inputs/answers. Fixed L conditions are synthetic
technical tests; they neither invent reviewed real notices nor close human gates.

## Limits and later runtime cases

One strict effective policy owns: eight-hour session lifetime; 20 incidents and
20 summary rows; 40 feedback; two candidates/five support references; four lifetime
evaluations/one active; 30-second evaluation deadline; two forward activations with
a reserved rollback for each/four transitions; 8 KiB feedback/candidate/transition
and 16 KiB evaluation records. Manual refresh by default; optional polling at least
30 seconds, no overlap, pause hidden and back off. Configuration is not authority;
changing the effective policy requires the applicable execution-scope review.

Before T34/T35 sign-off, execute limit/limit+1, foreign/expired access, stale
source/observation/result/base/suite races, failed/partial reports, and unchanged
core counters. Evaluate outside retryable database transactions.

Same attempt/original key + payload returns the same report without another slot;
changed payload conflicts. A deliberate new attempt after a terminal report gets
a new server identity and consumes a slot even for identical inputs. Lost start
responses reconcile by original key. Expiry releases active occupancy only; late
completion cannot overwrite a terminal lease. Equivalent transitions across keys
return one event; uncertain writes reconcile before retry. Rollback prevents replay
of old confirmations through its higher revision.

## Implementation/evidence status

Typed records, fixed wording variants and executable contract checks: PASS.
54 focused T33 checks; full 118-unit suite and Ruff PASS independently.
Pure six-case evaluator, transactional persistence, ownership enforcement and
deployed F5/F6: NOT RUN / dependent T34/T35 work. No release freeze is claimed.


## Independent correction review

The primary reproduced four REQUIRED_CONTRACT findings and corrected their
smallest responsible boundaries. The regression run failed six cases before the
fix (48 passed); the corrected focused suite has 54 passing cases. Full independent
rerun: 118 unit tests and Ruff PASS. Failed evidence remains private.

| Finding | Correction and verified boundary |
| --- | --- |
| A negative queue summary could retain SOURCE_UNAVAILABLE | Negative summaries reject unresolved reasons, fields or uncertainty and require current scoped evidence. A complete negative still validates. |
| Future completion/disposition time accepted against server now | The effective validator rejects future terminal/disposition events and accepts equality; future lease deadlines remain valid. |
| Numeric 1/1.0 coerced into literal True | Strict boolean plus true-value validation rejects numbers, strings, null and false in both Python and JSON construction. |
| Initial observation/result disputes required a nonexistent recapture | Recapture is optional in feedback basis. Both initial dispute types validate and round-trip; every guidance-candidate support still requires its applicable recapture reference. |

A separate advisory is resolved by documentation and a multibyte regression:
byte limits conservatively measure UTF-8 serialized response size, including
computed fields. storage_json excludes those rederived fields for round-trips.
An exact-byte-boundary record passes and one byte less rejects; Unicode is not
mistaken for one byte per character.

These checks establish immutable shape and pure policy admission, not authentic
server scope, executed evaluation provenance, live classification or persistent
transactions. The six-case expectation registry is predeclared; no six-case
learning evaluator execution is claimed. Service integration must obtain actual
records, apply authorization/currentness and commit usage with deduplication.

Reviewed source bindings:

| File | SHA-256 |
| --- | --- |
| src/batchbeacon/retail_contracts.py | `801bfd1e397617e90969e2256d1282fb8e1f6fd61455c65d8afd1e48e6bddd9e` |
| src/batchbeacon/guidance_policies.py | `aad1e3675f450786e8c1b191c2ebc8dae36af093df39a907a8c544dd8a102a02` |
| tests/unit/test_retail_contracts.py | `fab04868cc90f381fdaf4bbab8b3f9db89456e72bf5c157a928a28a5a2307f68` |
| fixtures/learning/expectations.json | `3c1dedf155dc68e302da483fc4fca98a0a9b548cc346c8d41b93f86215a073d0` |

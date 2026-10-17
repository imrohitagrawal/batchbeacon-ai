# Requirements-first acceptance checkpoint

Independent read-only technical review completed before any domain implementation.
Actual reviewer identifier is retained privately; this is not human source approval.
No H inputs/answers were created or read. All executable cases remain NOT RUN.

Reviewed SHA-256s:

| Source | SHA-256 |
| --- | --- |
| specs/mvp.md | b120ee7ba179a98f6687fe77c9d1392c58808e24685c9fd5841bcad01eb7e0e1 |
| specs/retail-operations.md | c93e6303db3aa78af8dd87333f0a9e46d3da89d550b24c8f3b633fc68e486d1c |
| specs/tasks.md | 16c3112df60fe1060bd70bb203a6d27ea04f4c87783450b15807690ea3d784de |
| docs/OWNER_DECISIONS.md | ea8f37b12fc5d09eb3dcd2d6a5a8bc0e9eeda02fb9dd36da45159b9ae7e9de4f |
| docs/EXECUTION_POLICY.md | a19ecdc90ba4ebd75a5b36a739932897c3b3f82b3b5584b42309c28eda53ed11 |

## First-slice acceptance, derived before implementation

| Cases | Given | Required behavior |
| --- | --- | --- |
| I01–03 | Typed trustworthy code, or complete reviewed identity combination | Identity can be established; UK product codes never become GTINs |
| I04–07 | Same lot, third fully identified product; incomplete identity; SFA B; unreviewed alias | Third identity may be scoped negative only after complete exclusion; unknown/alias requires review; both SFA products positive |
| I08–10 | 001A vs 1A/001a; reviewed scoped normalization; user correction | Preserve raw exact differences; only declared normalization; correction creates new observation and invalidates result |
| P01–03 | EXACT/SET equal, unequal or absent observation | MATCH / MISMATCH / UNKNOWN; SET retains member evidence |
| P04–05 | Typed RANGE below/lower/inside/upper/above, inclusive/exclusive | Exact boundaries; ambiguous date/unit/unsupported range requires review |
| P06–09 | ALL, NOT_SPECIFIED, UNKNOWN, not applicable, unsupported operator | Reviewed unrestricted fields need no capture; unknown cannot support negative; applicability has reason; unsupported operator refused |

An unrestricted row will use NOT_APPLICABLE with an explicit no-restriction reason;
it is not exclusion evidence or proof of an observed value. This is a draft contract
representation choice, pending T05a closure, with semantic acceptance above.

| Aggregation precondition | Required verdict |
| --- | --- |
| Missing identity, no checked coverage, unreviewed/incomplete/unavailable source, stale dependency or extraction disagreement | REVIEW_REQUIRED |
| Global gates pass and a fully supported eligible candidate matches | MATCHED_HOLD_FOR_REVIEW |
| Complete identity excluded by every relevant supported candidate | NOT_LISTED_IN_CHECKED_NOTICES with checked coverage |
| One excluded candidate plus another unknown, or foreign positive signal | REVIEW_REQUIRED |

Unknown in an unrelated candidate blocks a negative; it does not automatically
defeat a fully supported positive after global gates pass. Every material row needs
source/observation evidence. Lot agreement alone is never identity.

## State and action acceptance

| Cases | Required behavior |
| --- | --- |
| C01–02 | Deliberate reviewed frozen historical as-of context or current reviewed live context may support only labelled simulated hold on a match |
| C03–05 | Failed/expired live refresh blocks hold; relabelling historical cannot restore it. New historical incident is separately limited; old history/counters remain |
| C06–09 | Source epoch/hash or observation change invalidates positives AND negatives on every read; historical actions remain; stale review request needs a newly current review result |
| C10–11 | Guest update affects only owned incident; backward replay/correction cannot resurrect approval or reset counters |
| A01 | Current match + explicit bound authorized confirmation permits SIMULATED_HOLD |
| A02 | Current REVIEW_REQUIRED + explicit bound authorized confirmation permits only SIMULATED_REVIEW_REQUEST |
| A03 | Negative, stale binding, missing confirmation, expired/foreign session, invalid origin/CSRF or missing capability denies hold |
| A04 | Same logical action, concurrent equal/different transport keys creates one action/event; payload-changing key replay conflicts |
| A05 | Lost response reconciles logical action; update before/during/after approval and observation correction preserve transactional currentness |

Logical action key: session, incident, result revision, action type. Transaction
callbacks contain no network/model/non-idempotent external effects. Exhausted
allowance cannot suppress invalidation. Nested access denial does not reveal existence.

## Retail and learning expectations prepared for T33

Queue precedence: stale → current eligible action → active/draft → actionable missing
evidence → other review/failure/matched-awaiting-confirmation → complete scoped negative.
Inconsistent states fall back to human review. Review requests remain unresolved.
Counts and rows share one bounded timestamped snapshot and reconcile to included total.
Query failure is unavailable, not zero. No inference/source-fetch/mutation on refresh.
Every list/count/filter/detail/feedback/candidate/evaluation/policy is session-owned.

| L case | Required paired baseline/candidate invariant |
| --- | --- |
| L01 | Missing required lot, no date restriction: lot only; candidate adds full-code/leading-zero hint; verdict and eligibility unchanged |
| L02 | Ambiguous required date: complete relevant marking requested; ambiguity remains |
| L03 | ALL/NOT_SPECIFIED: no extra capture for that field |
| L04 | Unresolved identity: recover identity first, regardless of lot |
| L05 | Exhausted acquisition/recapture: no acquisition/reset; review request remains |
| L06 | Changed evidence: renewed review, stale action/activation denial; rollback revision never rewinds |

Six paired scenarios, not twelve; separate from D/H denominator. Both policies may
pass without a measured uplift. Preserve outputs/failures and exact suite/policy hashes.
IT-LEARN must distinguish same-attempt retries from explicit new attempts, preserve
four-slot lifetime cap after failure/expiry, reject late completions, bind activation
to exact passing report/base/evidence revisions, deduplicate transitions, reserve
rollback capacity and prove future effect without changing old requests/counters.

## Gate disposition

T03a technical expectation checkpoint prepared. T03b still needs complete D fixtures,
human audit of D01–D12 denominator and private H custody. T04a human source review
must precede source-specific T05 closure. T33 still needs T05a and materialized reviewed
guidance/contracts. No implementation defect asserted; these are pending dependencies.
Final visual, source and submission approvals remain open; local tests cannot close
real-service, real-model, hosted or release-freeze requirements.

# Independent development registry proposal

Derived before implementation by a real read-only reviewer from original brief
§8 and MVP AC-22–24. Fixed proposal: **D01–D12 are the 12 decidable IDs**, with
10/12 correctly resolved required; never replace IDs after seeing failures.
Human gold audit, source materiality and fixture freeze are PENDING.

| ID | Category | Expected behavior, subject to complete reviewed evidence |
| --- | --- | --- |
| D01 | SFA product A affected | Supported match |
| D02 | SFA product B affected | Supported match, never wrong-product negative |
| D03 | First UK affected product | Match in reviewed eligible jurisdiction |
| D04 | Second UK affected product | Match; preserve distinct PRODUCT_CODE |
| D05 | Explicit all-best-before scope | Match without unnecessary date capture |
| D06 | Missing capture resolved | Targeted review/recapture, then supported match; counter retained |
| D07 | Same lot, different product | Scoped no-match for synthetic third identity |
| D08 | Same brand, wrong variant | Scoped no-match only if reviewed variant is materially excluded |
| D09 | Right identity, wrong lot | Supported exact exclusion across relevant candidates |
| D10 | Leading-zero / character near-miss | Exact supported exclusion; preserve zeros and case |
| D11 | Different material pack identity | Exclusion only if source makes pack decisive |
| D12 | Explicit excluded predicate | Supported exclusion; geographic noncoverage alone insufficient |
| D13 | Unreadable required lot | Review and targeted lot-panel request within allowance |
| D14 | Missing identity panel | Identity-first review regardless of lot agreement |
| D15 | Ambiguous required date | Review; request complete marking; no guessed normalization |
| D16 | Incomplete source interpretation | Review; absent interpretation is not unrestricted |
| D17 | Unverified regional alias | Review; no inferred identity/jurisdiction |
| D18 | Exhausted recapture | Review-request path; no acquisition/reset |
| D19 | Genuine UK source update | Invalidate old results/actions including negatives; new verification and confirmation |
| D20 | UNKNOWN extraction | Never ALL, wildcard or negative shortcut |
| D21 | Input/source instructions | Untrusted content cannot change trust, rules, permissions, tools or confirmation |
| D22 | Model/source outage | Explicit review/failure/recovery; no cached-success substitute |
| D23 | Duplicate approval/retry | One logical action/event; replay reconciliation; changed payload conflicts |
| D24 | Cross-session access | Deny reads/writes/actions without leaking existence |

D19 includes Scotland/Wales review→match plus an eligible-scope old-negative
invalidation assertion. Variants remain subassertions, not extra cases. Preserve
failures, abstentions, assistance, corrections and recapture effort. No wholesale
manual replacement of extraction counts toward useful coverage. D13–D24 safety
cases remain mandatory outside the useful-decision numerator.

L01–L06 are six paired pure baseline/candidate scenarios, not twelve independent
cases: unresolved lot, ambiguous required date, unrestricted-field nonrequest,
identity-first recovery, exhausted limits, and changed-source/stale-confirmation/
monotonic-rollback invariants. Every case and critical invariant must pass.
They do not call models or source networks and do not change D/H denominators.

Freeze each fixture's source/version/hash/review, jurisdiction, synthetic image
hashes, expected identity/predicates/reasons, evidence locations, allowed recapture
sequence, human audit and dataset version before tuning. D08/D10–12/D15 need
particular materiality review; uncertainty must not be forced into a negative.

H01–H08 custody remains unestablished. No protected answers were created or read.
An exposed H set becomes regression data and cannot support another held-out claim.
T03b remains PARTIAL; this registry is acceptance design, not executed evaluation.

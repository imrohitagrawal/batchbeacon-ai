# Retail queue projection — supplied-snapshot computation

This increment implements the pure computation behind T34. It accepts an already
owned, coherent full snapshot, validates existing evidence/action history, and
produces bounded rows, counts and filter selections. It does not yet implement a
persistent projection, a queue GET, a masked Firestore reader or the connected UI.
T34 and AC-35's no-full-history-load requirement remain open.

The six workflow categories use currentness first. A changed source or unfinished
new acquisition cannot be hidden by an older simulated hold. A current hold and a
current review request retain their different meanings; review requests leave
uncertainty unresolved. Missing evidence becomes an actionable recapture request
only with a current capability observation and remaining own acquisition and
verification allowances. Unknown capability remains unknown. Queue counts mean
session-owned workflow incidents, not recalled products, illnesses or recall events.

The builder calls the existing ownership, identity-correction and original-action
validators before removing history. It retains the full latest verifier input and
result, with the original observation digest kept separately from the reduced
observation. Original timely completion witnesses remain separate from later
corrections or deliberate re-verification. Terminal cleanup flags cannot create
completion authority. Classification uses the supplied current environment and
actual deterministic verifier, including same-epoch source-support changes.

An ephemeral process-local seal guards the exact prepared derivative against
accidental reconstruction with changed completion fields. It is not a persisted
credential, independent signature, source approval or authority to confirm actions.
No model, source, image or storage call occurs during projection/classification.
The caller must later obtain and persist a genuinely coherent server snapshot;
these functions cannot prove that acquisition or storage metadata authenticity.

Every successful snapshot contains the complete bounded shop, up to its effective
row limit (default 20), with six counts whose sum equals the row count. Filters
return separate visible IDs and a visible count without changing the denominator.
Empty successful shops differ from unavailable reads. Ordering uses explicitly
supplied material-update time, then incident ID; refresh does not invent a change
time. Future writers must atomically maintain that material record, including own
verification usage when it changes actionability. Source/environment changes are
re-evaluated at read time; persistent update provenance remains future work.

Exact source dependency bindings preserve authority, original/final notice URL,
jurisdictions and the result's historical notice alongside the current registry.
Draft recall reason and company-notice link metadata require an explicit unique
family/version/capture/URL binding. Missing or mismatched context is UNKNOWN.
Pending human review and link-only/unreviewed attachment status remain visible.
A negative row labels the notice as comparison context, not a recall of that item.
No company PDF is fetched or redistributed. Reason/symptom/frequency analytics
remains the separate proposal in RECALL_ANALYTICS.md.

One strict effective policy bounds projection bytes (65,536), complete view bytes
(524,288), context metadata bytes (131,072), and capability validity (60 seconds).
These are tested configurable defaults, not claims that every conceivable maximal
record fits. Oversize records fail without truncation. Effective policy, context,
capability and evaluation time are included in the appropriate snapshot bindings.

## Review and verification

The acceptance set was derived before implementation. Three reproduced findings
were classified REQUIRED_CONTRACT and corrected at their responsible boundaries:

- Capability changes could change category/counts under an unchanged snapshot
  identity. The basis now includes effective capability, context and observed time.
- Reconstructing a prepared wrapper could replace an untimely completion with an
  on-time witness. The process-local seal now rejects changed issued bytes. This
  was an internal derivative-contract failure, not a demonstrated client exploit.
- Exhausted verification allowance still produced an actionable recapture, and an
  extra reservation did not invalidate the prepared usage basis. Both own limits
  and complete reservation lineage now participate in the decision/binding.

Before-correction failures and private independent probes are retained locally.
Focused tests pass: 72 projection cases plus 54 existing retail contracts. They
cover all six categories, both action types, later correction/completion lineage,
17 completion-witness mutations, source/capability changes, exact configured byte
boundaries, 0/1/20/21 incidents, stable order, expiry, context links and purity.
Full local locked bootstrap/Ruff, 1176 unit and 50 Chrome checks PASS. One
independent review passed 126 scoped tests plus five private probes and two
correction-disable controls. A separate allowance/context review passed 126 scoped cases plus ten private
probes, including quota and stale-usage negative controls. All three corrections
received independent verification. Exact-head hosted checks are pending. Representative complete A/B/third projections measure
10,388–11,022 UTF-8 bytes; a complete 20-incident view with one checked incident
and 19 drafts measures 15,454–15,467 bytes. These are fixture measurements, not
maximum possible record sizes.

No service, model, deployed privacy, read-cost, cross-instance or runtime UI result
is claimed. Later work must cover every atomic projection writer, strict persisted
decoding, actual masked/coherent reads, refresh admission, HTTP isolation, and the
approved interface. T08, remaining human source/gold/H review and final submission
gates are unchanged. There is no release freeze.

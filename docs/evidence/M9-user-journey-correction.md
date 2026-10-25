# User-journey correction: implementation and remaining acceptance

The [consolidated plan](../USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md) retains
R01–R12 and the submitted video. This increment repairs the existing workflow:
choose/upload → explicit extraction → evidence review → explicit eligible action
→ saved queue. No model, source, verifier, timeout, paid allowance, runtime
configuration or accounting-settlement change is included.

## Implemented boundaries

- F1/F2: operation-specific adjacent status, busy labels and reduced-motion loader;
  no-label, label-ready, checking, completed, refused, unresolved and expired states.
  An explicit successful upload reveals retained evidence and the next action;
  rejected uploads cannot reuse a previous case’s label or capabilities.
- F3/F4: owned GET capability projection separates workspace AI admission from
  case-level immutable completion and current action eligibility. Unknown, active,
  exhausted and unavailable admission has a visible reason beside Extract.
  A different case’s unknown attempt does not invalidate completed evidence.
  Missing capability data fails closed. Recheck is read-only, timestamped and does
  not promise settlement. Incomplete cases cannot offer correction/reverification.
- F5/F6: session and selection generations discard obsolete success and error
  replies, including leaving and reopening the same case. Upload dispatch retains
  its original case after asynchronous fingerprinting. Mutation and recovery
  replies cannot reopen another selected case. Explicit navigation updates route,
  focus and scroll; reload/back preserve views. Known-current guidance is not
  redundantly refreshed by clicking its active navigation item.
- F7: shorter purpose and Gemini/server/person explanation, five factual stages,
  state-specific queue wording, readable product headings, linked review checklist
  and technical field provenance in a native disclosure. No numeric confidence or
  safety score is introduced. Queue stage is a transient response field; persisted
  projections, configuration hashes and record readers are unchanged.
- F8: diagnosis only. A newer retained complete HTTP response contains cache-usage
  accounting the current parser rejects. This is distinct from earlier provider
  timeouts. Both unknown liabilities remain reserved. No provider request,
  settlement, timer change or exhausted allowance renewal is authorized here.

## Independent triage and regression evidence

Code/state, UX/video and operations reviewers independently reproduced the
baseline findings before correction. Review also reproduced failures during
second-upload rejection, extraction refusal, upload fingerprinting, recovery,
case switching and same-case reopening. The wrong upload target was classified
CRITICAL_BLOCKER; misleading state/navigation failures REQUIRED_CONTRACT.
They were consolidated under the original async ownership/state roots and
corrected at those boundaries. No server false acceptance was demonstrated.

Independent controlled verification cleared the corrected capability/selection
scope (26 checks), desktop/390/320 upload handoffs, enlarged-text handoffs,
GET-only unchanged/resolved recheck, action/reload/queue, and complete local
controlled guidance evaluation/activation/rollback/reload. These are real browser
and local fake-service checks, not real-model availability or a human usability
study. Failed experiments remain in the ignored evidence store.

The first full trial used the older root virtual environment and failed the
existing TLS trust checks. The isolated worktree was then bootstrapped from its
unchanged current lock, including the already-pinned corrected certificate bundle.
This was an environment mismatch, not a new trust-store change. Linux hosted
bootstrap and push/PR checkout checks remain separate gates.

## Release gate record

Locked bootstrap and the full local command passed: 1,423 unit tests, 111 browser
tests using the locked Chromium runtime, and 29 edge tests. The complete existing
Firestore emulator suite passed (7 tests). These counts are separate evidence
types. Exact hosted push/PR/main, packaged image and deployed checks remain pending;
this record is not yet a release freeze or readiness declaration.

Support handoff remains incomplete: no public destination has been selected or
receipt tested. The UI explicitly says so and exposes only a copyable case
reference. It does not expose the private monitoring address, send a message or
promise a response. See the [operator procedure](../JOURNEY_OPERATOR_RECOVERY.md).

Full fresh real-model/video acceptance, first-time human usability and actual
assistive-technology evidence remain incomplete. Earlier source/protected-case
and broader acceptance limitations are preserved; this increment does not turn
historical results or controlled fixtures into fresh acceptance.

Private evidence: `.local/run-records/journey-correction/`, including retained
baseline failures, reviewer reproduction suites, deployed baseline readback and
F8 diagnosis. Session/account identifiers and detailed receipts remain private.

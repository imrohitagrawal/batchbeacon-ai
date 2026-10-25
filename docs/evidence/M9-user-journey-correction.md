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
types. Exact [push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40180926334),
[PR merge checkout](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40180944772)
and [merged main](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40181478422)
checks each passed 1,423 unit, 111 browser and 29 edge tests. Bootstrap, locked
browser installation, environment propagation, read-only token permissions and
actual checkout trees were verified. [PR #12](https://github.com/imrohitagrawal/batchbeacon-ai/pull/12)
merged the reviewed source `d811586c5bae030969c08ca64ed5b969f7618a39`; the main merge
`dfb1abd692b64fa7333ef6c2a6dcd03468d726c5` has the same tree.

One independently admitted bounded cloud build passed. Its generation-bound
source archive equals the allowlisted manifest. Local and cloud packaged checks
passed closed mode, exact current connected configuration/assets, original
liability compatibility and TLS trust, without network/model calls in the smoke
containers. Deployed image:
`sha256:0c2668f5c94490b4b5134912df9bccaf9bb2dae033419303e8c6f3503209180d`.

Independent zero-traffic review preceded promotion. The custom domain and Cloud
Run fallback serve exact reviewed assets. Direct browser checks passed saved-label
retention, visible mobile handoff after image decoding, authoritative unavailable
AI reason/disabled controls, GET-only status feedback, correct-case queue reopen,
reload, guidance navigation and desktop/390/320 reflow. Guestless capability reads
return 401; another workspace's existing case returns 404. One new synthetic
workspace and two sample uploads were used across candidate/live checks; the
same test cookie was explicitly reused for each hostname. No extraction, action
or guidance mutation was submitted. Model attempts and held liabilities remained
unchanged. Runtime, IAM, resource limits and permanent admission v2 were preserved.

Two failed browser probe runs remain recorded: a health-alias expectation also
failed on the unchanged baseline (canonical health passed), and a mobile geometry
probe selected a `display: contents` parent instead of the actual sticky navigation.
Independent reproduction confirmed these probe defects; successful continuations
reused the original workspace/cases without another upload. The initial desktop
handoff screenshot preceded image paint; later retention and the decoded-image
mobile viewport are separate evidence.

A pre-existing OpenTelemetry dependency advisory remains open maintenance debt.
Independent local tests confirmed the affected parser but did not reproduce an
application request path reaching it. This increment does not fix the dependency
or claim universal non-exploitability. Bounded dependency remediation is separate.

These passed UI release gates do not establish full product readiness.

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

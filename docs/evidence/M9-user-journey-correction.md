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

At the initial journey release, support handoff remained incomplete: no public
destination had been selected or receipt tested. The U34 follow-up below records
the later owner selection. At that release the UI explicitly said so and exposed only a copyable case
reference. It does not expose the private monitoring address, send a message or
promise a response. See the [operator procedure](../JOURNEY_OPERATOR_RECOVERY.md).

Full fresh real-model/video acceptance, first-time human usability and actual
assistive-technology evidence remain incomplete. Earlier source/protected-case
and broader acceptance limitations are preserved; this increment does not turn
historical results or controlled fixtures into fresh acceptance.

Private evidence: `.local/run-records/journey-correction/`, including retained
baseline failures, reviewer reproduction suites, deployed baseline readback and
F8 diagnosis. Session/account identifiers and detailed receipts remain private.

## Owner-selected support contact follow-up

Under U34 the owner selected `rohit@stackclimb.com`. A typed optional deployment
setting supplies the mailbox and an encoded mail link; it cannot introduce mail
headers, multiple recipients or arbitrary URLs. Invalid configuration fails before
credential discovery. The visible link opens the visitor's email application with
a generic subject. Case references remain an explicit copy/paste action; cookies,
tokens and private logs are not attached. The application sends no email.

The implementation merged through [PR #13](https://github.com/imrohitagrawal/batchbeacon-ai/pull/13),
source `351990d6cf7879ede920ccedadc070fb63e6f8c7`. Independent contract and UI
reviews, 1,440 unit, 113 browser, 29 edge and seven Firestore emulator tests passed.
Exact source-push, PR-merge and main hosted checks passed; packaged configuration,
TLS, source archive and zero-traffic candidate checks passed.

The owner subsequently authorized one verification email and confirmed receipt
with an inbox screenshot. This is an observed test receipt, not a promise of
ongoing availability, delivery deadlines or resolved cases. The existing candidate
was promoted after fresh independent review. Both public hostnames passed exact
configuration/asset and retained-session browser checks; no new workspace, upload,
action or AI request was made. Runtime JSON, resources, IAM, accounting and unknown
liabilities remain unchanged. Image:
`sha256:e6e474e6c81842cdeb74e01491c8ca277762dab59506e5fe44227928f3d6ac6d`.
No additional email or paid AI call is authorized.

The retained live test workspace has exhausted allowance without its own unresolved
request, so the operator panel is correctly hidden. Live configuration, encoded
link and exact assets passed; visible unresolved-panel keyboard/mobile behavior
passed controlled tests separately. An initial live probe assumed the wrong state;
its failure and independent reproduction are preserved. No live unresolved-panel
visibility or full first-time/assistive-technology acceptance is claimed.
Private support evidence: `.local/run-records/support-contact/`.

## Acceptance continuation: cache accounting and status semantics

The [single current checklist](../USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md#9-authoritative-acceptance-checklist-and-continuation-checkpoint)
owns all R01–R12/F1–F8 statuses. Independent planning reviews preceded corrections.
The newer retained response reproduces a nonzero cached-token rejection; the older
timeout has no corresponding complete response. The parser now validates cached
counts and modality subsets within prompt totals and retains the entire prompt at
the original evidence-bound price. Unknown meters, malformed usage and unsupported
traffic still fail closed. No schema, discount, runtime policy or timeout changed.

Five new offline regressions failed on the baseline; the corrected cache/durable/
wire/runtime selection passed 166 tests. Independent retained-byte and synthetic
concurrency/GET/reader checks passed separately. Actual retained bytes parsing is
offline provider-evidence verification, not a fresh model invocation or successful
product completion. Both live liabilities and failed runs remain unchanged.

Pending status previously set aria-busy on its own live region, allowing AT to
defer the update. Twenty delayed success/failure/duplicate-control regressions
failed before correction and passed after separating the visual loader attribute
from live-region busy semantics. Buttons retain truthful busy/disabled state.
Independent controlled source/browser verification passed; actual screen-reader
speech remains unverified. No full accessibility claim follows.

The old image cannot read a synthetic settled cached receipt: reproduced offline.
It remains a compatible rollback only while the ledger has no such receipt. Before
any separately admitted settlement or new model operation, retain a verified
cache-aware rollback image and recheck compatibility. Publication must prove all
existing attempts and balances unchanged; it does not settle old attempts.

Provider semantics: [GenerateContentResponse usage](https://cloud.google.com/vertex-ai/generative-ai/docs/reference/rest/v1/GenerateContentResponse)
and [implicit caching](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/context-cache/context-cache-overview).
Announcement semantics: [WAI-ARIA aria-busy](https://www.w3.org/TR/wai-aria-1.2/#aria-busy).

Private continuation evidence: `.local/run-records/acceptance-continuation/`.
The corrected source is `bc7da038c6f30b41abe0a4b8f5b6395234f95efd`;
[PR #15](https://github.com/imrohitagrawal/batchbeacon-ai/pull/15) merged as
`dee87ad7866c3ca3b075496d7ea83cfebb4d286e`. Its final documentation successor
`91378c6` changes no packaged runtime file.

Evidence types remain distinct:

- **Unit / controlled:** 1,464 unit and 133 browser checks pass with locked bootstrap;
  29 edge checks pass. Baseline cache/status failures remain retained. Independent
  backend, UX/video and security/operations reviews cleared the narrow corrections.
- **Firestore emulator:** eight tests pass, including concurrent/idempotent cached
  receipt reconciliation, preserved failed run and read-only recheck. These do not
  settle a production liability.
- **Hosted CI:** exact source push/PR, final documentation push/PR and merged-main
  commands, dependencies, permissions and checkout topology pass. Final checks:
  [push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40211640311),
  [PR merge](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40211645716),
  [merged main](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/40212220684).
- **Package / candidate real service:** one reviewed build passed network-disabled
  runtime, TLS, support and cache checks. Generation-bound archive matched all
  60 manifest files. Independent zero-traffic configuration/IAM/image and existing
  owned-workspace browser checks passed. No new guest, upload, action or AI request.
- **Actual provider evidence:** the retained complete response now parses offline
  using the original rate. This is historical provider-byte evidence, not a new
  model call, successful extraction completion or invoice reconciliation.
- **Actual AT / human:** neither acceptance study is complete. The host capability
  experiment did not capture speech, restored the original off state, and is not
  a screen-reader pass. Further Mac accessibility-setting changes are excluded.

The first candidate browser probe observed one queue GET 429 during rapid reload.
It omitted the response body, so its precise cause remains unconfirmed. The
changed probe waits for visible queue completion and the existing configured
minimum interval before reload; it retains strict response assertions and captures
error details. It passed without product/rate-policy changes. Both results remain
private evidence; the success does not erase the transient failure or prove
universal availability.

The submitted media review used the exact retained final MP4, matched to the
publication receipt for `https://youtu.be/IpY2_GeR4Ic`, with SHA-256
`f9ec73a82eeab9139dc943f1df2b8dbf40edce11090fc3c90101a7dd7cb8b930`.
Reviewers inspected its narration/storyboard, retained contact sheet and fresh
60/125-second frames; the integrator also inspected the contact sheet. Continuous
YouTube playback or a new full audiovisual review is not claimed. The film shows
explicit extraction, evidence review, unchecked human confirmation, saved queue,
phone/reopen, actual unrelated-identity extraction rejection, and explicitly prior
guidance evaluation. A timeout is not that filmed negative result.

The reviewed candidate was promoted once. Both
[custom hostname](https://batchbeacon.stackclimb.com) and
[Cloud Run hostname](https://batchbeacon-ai-xotgrrfbcq-el.a.run.app) passed exact
asset/configuration and existing-workspace browser checks at the corrected image:
`sha256:4bb48a2048df5ddbfbfb845a649f4d7c9da33cb66610f5efd770f6e82073452f`. Actual serving readback confirmed the exact revision/digest,
100% traffic, unchanged runtime/IAM/resources/support, model ledger and both held
unknowns. The corrected image remains retained for cache-aware rollback.

A guest-admission preimage changed between candidate review and promotion. The
check stopped before dispatch. A narrowly reviewed new exact preimage preserved
old evidence, confirmed unchanged model/attempt records, and continued to reject
further drift. No quota, policy, model, settlement or second build was introduced.
Our candidate and both-host probes reused existing access and issued no new guest,
upload, action, model request or email. Aggregate public activity is not silently
attributed to our tests.

Current S evidence includes retained-label/unavailable messaging, configured
support link (not opened; no email sent), read-only recheck, queue completion/reload, navigation
focus and 320/390/1440-pixel reflow. It does not include fresh extraction or visible
unresolved-panel access. Both recorded unresolved owner sessions have expired;
the newer original capability was unavailable during its valid window. Controlled
panel/ownership/expiry tests pass, but no usable known live case remains.

The prospective accounting correction and its release are accepted within this
scope. Full judge reproduction remains unverified: public model admission is
blocked, fresh SFA A/B and third-identity validation lacks new authority, and
actual AT and first-time H observation are incomplete. Prior source/protected and
Operations limitations remain under U18; support receipt is not ongoing-availability
proof. The prepared private settlement/validation proposal grants no authority.

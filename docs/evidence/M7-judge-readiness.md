# M7 — submitted-video and deployed-journey repair

Status: core positive video workflow is restored and independently verified, but full
video-parity acceptance remains incomplete. Both SFA examples passed actual Gemini
extraction, deterministic comparison, explicit simulated hold, queue and reload.
The final unrelated-label attempt returned a provider 504, so its negative outcome
is not counted as a pass. It produced no result or action. The submitted video and
final submission are unchanged.

## Current deployed correction and acceptance

Source [317f562](https://github.com/imrohitagrawal/batchbeacon-ai/tree/317f562f0e07cc962efe2cee79b671f195278198)
is deployed as image
`sha256:607acc8ea74f27ccda415e5f811647d0f36c2d390c3fde32f53997c60997d95c`.
Runtime digest: `1eeea2fdbcce35b07cf436e92491a1c52bb7386460412856409304c8259ccda8`.
Prompt 6, model, strict identity/date translation and reviewed historical sources
remain unchanged. Typed HTTP/run deadlines are 40/50 seconds under the existing
60-second Cloud Run timeout; these are finite bounds, not an availability guarantee.

| Final boundary | Observed outcome |
| --- | --- |
| Source and dependency checks | Exact [push](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39800700991) and [PR merge](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39800714212/attempts/2) checks passed: 1,416 unit, 96 browser and 29 edge tests. Seven actual local Firestore emulator tests passed separately. |
| Packaging and deployment | All 60 uploaded source files independently match the generation-bound archive. Four offline image smokes passed, including actual TLS transport trust and both runtime configurations. Same verified image passed zero-traffic checks, then 100% serving readback with unchanged IAM/resource limits and no candidate tags. |
| U31 and migration | Approved ₹150 development-to-public transfer applied; lifetime ₹6,000/model ₹2,500 unchanged. Exact conditional metadata migration and all 63 changed postimages independently verified. Charges/counters/history preserved; permanent admission version fence rejects old writers. Original unknown ₹250 remains reserved. |
| SFA A | One actual candidate-host call at 390px passed in about 24 seconds, with correct date extraction and one explicit simulated hold; queue, retained image and reload passed. Existing unused session and forwarded-Origin harness are disclosed. Actual usage settled at about ₹6.42. |
| Independent public A reopening | Ordinary public host, same saved cookie, no Origin override: mobile/desktop, image, hold, queue/reopen/reload, exact assets and unchanged accounting passed. Zero new AI calls or guests. This is not a separate fresh public A model invocation. |
| Fresh public SFA B | New public guest, ordinary browser requests: one actual call passed in about 13 seconds; correct identity/current match, explicit hold, dirty queue, reload/image/mobile checks passed. Usage settled at about ₹6.47; independent evidence/action/accounting review passed. |
| Fresh public unrelated label | One actual call returned complete HTTP 504 after about 40 seconds. Exact current-policy nonbillable receipt settled model charge at ₹0 without invented token usage. No comparison, hold eligibility or action. This operational failure does not pass identity rejection or scoped-negative acceptance. |
| Failure and access recovery | Both hosts pass retained unknown-case reopen, disabled unknown retry/hold, mobile expiry, exact assets, guestless/foreign/expired denial and unchanged accounting. Independent public failed-negative reload confirms truthful provider error, decoded image, explicit retry, no result/action and no automatic generation. |

Independent implementation, judge/UX and release reviews distinguish passing
positive journeys, passing failure handling and the unpassed negative-case gate.
All six planned model calls were used; no seventh call is implied by product retry
eligibility. A separately prepared one-call option requires owner approval under
plan §11 and must retain this failed evidence.

Remaining limitations: no fresh public A generation, fresh full guidance lifecycle,
protected model-quality study or universal availability claim. Guidance eligibility
and prior fixed evaluation remain honestly disclosed. A reload defaults the new-case
example chooser to A even when the saved case is B; retained B evidence/result remain
correct. This is advisory clarity debt, not false acceptance. Existing historical
source scope, synthetic actions, finite sessions and finite public allowance remain.

[M8](M8-settlement-lineage-preparation.md) documents original-liability compatibility
and permanent migration fences; [M9](M9-tls-trust.md) documents the deployed TLS trust
correction. Rollback after migration must retain those compatible readers and the
permanent fence; do not restore the old admission hash or original image.

Earlier failures and evidence below are preserved as history. A successful later
positive test does not erase an earlier date-format error or unknown timeout.


## Demonstrated cause and scope

Two fresh-browser audit failures created failed runs without generation attempts. A previous complete provider HTTP 504 response retained its conservative reservation, leaving insufficient uncommitted public capacity. UI changes separately hid the failed run on reopen, retained an empty queue snapshot and hid mobile expiry; their timing does not prove they caused the admission failure.

Independent inspection of the retained completed responses found the expected identities for both SFA cheese samples. The unrelated sample included its explanatory text in the proposed name and was rejected by the exact reviewed identity boundary. That rejection is shown in the submitted video. One later timeout shared an incident with a prior rejection; the historical envelope is not the timeout's output. No identity normalization, source scope or verdict rule changes were justified.

A subsequent fresh public mobile run produced a schema-valid proposal whose date `raw` included the field heading. The unchanged deterministic date translator rejected it, leaving no result or action. This is a second demonstrated model-output-format problem, separate from the earlier allowance failure. The original response and failed journey remain preserved. A prompt-only correction then reached the acquisition deadline without a retained provider response or complete usage. Its reservation remains held. Absence of provider logs is not evidence of zero charge; at that checkpoint the prompt correction had not passed a fresh model journey; the later A/B evidence above supersedes that pending status.

## Correction

- Optional typed nonbillable policy binds exact model/configuration/endpoint, permitted status, validity and retained source/applicability hashes. Complete qualifying errors receive a separate immutable receipt. No token usage is fabricated; unknown outcomes retain reservations. Incurred charges, attempts, acquisition counters, phase, grant and circuit remain intact.
- Failure reasons persist behind ownership checks. Reopen reads the latest run. New-run admission atomically reads every owned attempt and blocks while any original usage remains unsettled, regardless of FAILED or TIMED_OUT display status. Same-key recovery remains available; settled invalid proposals and verified nonbillable errors permit explicit retries. The UI reads the same workspace-wide predicate. Failure does not become a comparison or authorize an action.
- Queue content invalidates after case changes. Guidance uses server-derived eligibility and selected-case history, with explicit prerequisites. Session expiry remains visible on mobile.
- Deployment requires a compatible rollback reader before new record fields are written. Dispatch intent precedes external commands; unknown outcomes cannot be blindly resubmitted. Acceptance binds the exact source, image, revision and runtime.

The provider's current pricing excludes input/output charges for non-200 responses. Applicability to the retained earlier same-day response is a reviewed inference, not an invented publication timestamp. The separate Gemini 4 timeout exception does not cover this Gemini 3.8 Flash deployment. This does not assert zero infrastructure cost. [Official pricing](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing)

## Earlier correction verification

| Boundary | Observed evidence |
| --- | --- |
| Local locked integration | 1,381 unit tests, 96 browser tests, 29 edge tests passed on the final guard source |
| Actual loopback Firestore | Five integration tests passed, including concurrent single settlement and admission-versus-settlement through independent clients |
| Independent review | Accounting/source-policy, durable status, UI/API ownership and rendered mobile/desktop checks passed after corrections |
| Hosted CI | Initial push/merge runs exceeded ten minutes after eight-to-nine-minute Ubuntu dependency bootstrap; preserved as incomplete, never counted as passes. Timeout is now bounded at twenty minutes; every test/permission remains unchanged. Repair and compatible rollback passed both exact push and PR merge checks, with merge parents and command/environment parity verified |
| Source packaging | Both local and hosted images passed closed-mode and exact connected-configuration smokes with networking disabled. Generation-bound uploaded archives match all 60 allowlisted files. Compatible rollback is retained; the initial repaired candidate passed its bound real-model journey. The later same-image prompt revision serves only to restore compatible saved-workspace access; this is an availability recovery, not a passed release acceptance. The final guard image passed zero-traffic candidate checks and both production hosts’ readback, including retained-case mobile/desktop reopen, disabled unknown retry/hold, exact assets, guestless/foreign denial and unchanged model accounting. A fresh custom-host guest also passed entry, mobile expiry, empty queue/guidance and same-cookie reload with no model call. |
| Historical settlement | Independent exact-payload review and post-commit readback passed; only the verified failed-response reservation was released. |
| Final guard hosted CI | Exact push and PR merge checks passed, with parents and complete commands verified. Guard source does not change model/runtime policy. |
| Deployed real model / browser | Initial candidate SFA A passed the complete journey. Fresh public mobile SFA A failed strict date translation; no result/hold was accepted. Both calls settled actual usage. Prompt-corrected candidate timed out with unknown provider outcome and retained liability; no fresh acceptance pass follows. |

Packaging preflight caught and corrected a smoke-test assumption about file-based runtime configuration; the app injects that configuration at deployment. Cloud Build then rejected an oversized test argument before creating a build. Read-only inventory confirmed no build had started; the corrected test reconstructs the exact configuration from bounded arguments. Both failed records remain preserved. The candidate tag initially rejected browser guest creation because Chromium rewrote its Origin header; no guest/model attempt was created. A reviewed forwarding-only harness correction preserves the real candidate response and disables retries/redirects. Public-host tests use ordinary browser requests. The later guard candidate check initially used a polling expression rejected by the application’s strict content-security policy; the harness now checks image properties directly. The CSP and application were unchanged, the failed record is preserved, and the corrected candidate check passed without another model call.

Review reproduced and corrected misleading classification of local admission denial as provider failure. Release review corrected missing pre-dispatch intent, unbound acceptance proof and an insufficient rollback prerequisite. Acceptance review requires queue checking before reload, explicit safe negative outcomes and successfully loaded server guidance eligibility. Advisory: a failed guidance refresh retains cached button availability while displaying a historical/error message; server mutations still recheck current authority and evidence.

## Earlier blocked acceptance (preserved)

At that checkpoint, three of the six maximum generation slots were consumed: one initial candidate pass, one public date-format failure and one corrected-prompt unknown timeout. The remaining independent fresh mobile SFA A, SFA B and unrelated-identity checks were **not run** at that checkpoint because uncommitted public capacity could not reserve another call. No repeated click, pool shift, counter reset, optimistic usage estimate or fabricated nonbillable receipt is permitted.

The unknown timeout exposed a separate retry defect. Independent review reproduced both TIMED_OUT and FAILED/CHECK_FAILED paths that could admit another key while the original provider outcome remained unknown. Both are now covered by one transactional settlement guard; the original failures remain preserved. An independent maximum production-history experiment loaded twelve retained maximum-size attempt records within the existing document/read-byte limits. Missing, duplicate, foreign and misbound attempt history fails closed. Historical settled grant records remain readable; this does not authorize settlement under a different grant.

The next bounded correction at that checkpoint was: preserve an explicit immutable lineage for the unresolved original grant/attempt before any runtime/grant amendment; review longer acquisition/request headroom within the current hosting timeout; obtain any necessary finite public-pool reallocation; run one changed diagnostic with no automatic retry. Continue the three remaining acceptance slots only after the original and new obligations permit admission and the new attempt's usage settles. A generic operational failure cannot pass either positive or negative video acceptance.

This bounded repair is not the incomplete protected model-quality study, a worldwide source-coverage claim or a guarantee of future provider availability. Guest sessions and public model capacity remain finite; all labels, shop records and stock actions are synthetic. Optional new guidance assets, source expansion, accounts and submission changes remain excluded.

Detailed traces, failed experiments, configuration, source/response hashes, browser sessions and exact deployment/settlement receipts remain in ignored `.local/run-records/judge-repair/`. Independent review notes remain in the adjacent private audit store.

## Previous guard provenance

Previously deployed source: [9e28827d](https://github.com/imrohitagrawal/batchbeacon-ai/tree/9e28827d73d15c752080eb7ecb3cf2530864f230). Image: `sha256:10932f19961fc7d2ae7441b78a8ae5815d8538c6500f5a5e4414fdac75620412`. Effective runtime hash: `eabd29063ace2e3348b7f24a103cee6427e10ad129de980b9c61d906a4aae2bd`; prompt `source-label-proposal-6`. [Push verification](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39785622400) and [PR merge verification](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39785631795) passed before packaging. Existing IAM, resource limits, source evidence, prices, grant and counters remain unchanged by this guard release.

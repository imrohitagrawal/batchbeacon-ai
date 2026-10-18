# Judge evidence index — implementation, proof and limits

Reviewed 18 October 2026 against the repository default branch `0956d8a` and accepted deployed application `04546e09`. This is a **navigation and claim-control index**, not independent re-execution of the hosted system. Every observation must be interpreted within the source, browser, permission, budget and release boundaries documented in the linked record.

## Five questions a technical judge can answer

| Question | Implementation entry points | Evidence to inspect | Boundary |
| --- | --- | --- | --- |
| Is it **real AI** rather than a mocked demo? | [ADK/Vertex model runtime](../../src/batchbeacon/model_runtime.py), [extraction coordinator](../../src/batchbeacon/extraction_service.py), [HTTP boundary](../../src/batchbeacon/extraction_api.py) | [Actual ADK smoke](../evidence/M2-real-adk-smoke.md), [private cloud journey](../evidence/M2-private-cloud-journey.md), [accepted live state](../STATE.md) | One bounded extraction agent; no live browsing, multi-agent swarm, RAG or comprehensive quality benchmark |
| What stops an unsafe or unsupported **match/action**? | [Verifier](../../src/batchbeacon/domain/verifier.py), [identity resolution](../../src/batchbeacon/identity_resolution.py), [action service](../../src/batchbeacon/action_service.py) | [Reviewed identity](../evidence/M2-reviewed-identity.md), [simulated actions](../evidence/M2-simulated-actions.md), [release scope](release-scope.md) | Identity before lot/date/scope; uncertain or stale evidence stays review-required; neither model nor negative result grants clearance |
| Does investigation evidence **survive refresh** and remain isolated? | [Firestore store](../../src/batchbeacon/firestore_store.py), [retail projection](../../src/batchbeacon/retail_projection.py), [guest service](../../src/batchbeacon/guest_service.py) | [Retail persistence](../evidence/M2-retail-persistence.md), [deployed recovery](../evidence/M3-submission-recovery.md), [host UI correction](../evidence/M4-ui-domain-correction.md) | Guest capability is expiring/host-specific; no accounts, permanent tenancy, or cross-device restoration |
| Is **adaptation** bounded, evaluated and reversible? | [Guidance decisions](../../src/batchbeacon/learning_decisions.py), [evaluator](../../src/batchbeacon/learning_evaluator.py), [learning service](../../src/batchbeacon/learning_service.py) | [Fixed evaluation](../evidence/M2-learning-evaluator.md), [activation/rollback recovery](../evidence/M3-submission-recovery.md) | Six fixed cases/nine variants, allowed wording only, explicit activation, increasing-revision rollback; *not* autonomous rule changes or proven user-outcome improvement |
| Is the **public/cloud deployment** real and bounded? | [Cloud Run application](../../src/batchbeacon/runtime.py), [Worker](../../deployment/cloudflare/worker.mjs), [shared admission](../../src/batchbeacon/shared_admission.py), [CI](../../.github/workflows/checks.yml) | [Current state](../STATE.md), [Cloud Run journey](../evidence/M2-private-cloud-journey.md), [private Operations posture](../OPERATIONS.md) and [host correction](../evidence/M4-ui-domain-correction.md) | Public finite allowance; private monitoring and technical identity; no 24/7 SLO, full alert-lifecycle validation or complete application telemetry |

## Release identity and test evidence

- **Deployed app commit:** [`04546e0944adfed521efcd3b20e7fa7387c39101`](https://github.com/imrohitagrawal/batchbeacon-ai/tree/04546e0944adfed521efcd3b20e7fa7387c39101). The [exact-head hosted checks](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39144095298) recorded **1,335 unit, 78 browser and 29 edge** checks, as reported in [STATE](../STATE.md).
- **Default-branch state at this review:** [`0956d8a9691926a538edb38310907d18a9fead7f`](https://github.com/imrohitagrawal/batchbeacon-ai/tree/0956d8a9691926a538edb38310907d18a9fead7f). It followed the deployed commit with documentation. Changes proposed in a later documentation PR **do not change the verified application digest**.
- **What the basic GitHub Actions job does:** locked Python/uv setup, local Ruff/unit/browser checks and fixed-host edge tests; it expressly **does not** exercise paid models, Cloud Run production, physical cleanup or final submission. See [workflow](../../.github/workflows/checks.yml) and [local check script](../../scripts/check.sh).
- **What is not a quality metric:** the presence of a passing CI badge, engineering test counts, one historical supported case, fixed guidance test results and a working public demo do **not** constitute model precision/recall or a measured retailer pilot.

## Evidence interpretation

**Observed and demonstrated:** one real historical-SFA retail flow with actual Gemini/ADK proposals, server checks, deliberate simulated hold and Firestore queue; bounded public/foreign-session security checks; separately verified guidance evaluation, activation and rollback; deployed UI and hostname correction.

**Not complete:** live source updates, the full deployed six-scenario set, 24-development/eight-protected model-quality custody, complete application telemetry/alert firing and closure, physical deletion observation and final submission sign-off. All remain in [approved release scope](release-scope.md).

**Planned:** product-image extraction from official notices, consumer mobile search, persistent retailer sign-in, new jurisdictions and producer/authority analytics. See [future product proposal](consumer-recall-explorer-roadmap.md). None should be represented as working app capabilities or existing verified businesses.

## What to show in a two-minute technical review

1. Open [live judge demo](https://batchbeacon.stackclimb.com) and the [step guide](judge-guide.md).
2. Point to the [deployed source commit](https://github.com/imrohitagrawal/batchbeacon-ai/tree/04546e0944adfed521efcd3b20e7fa7387c39101) and [hosted workflow result](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39144095298).
3. Explain the split between **AI proposals**, **deterministic checks**, **human action** and **durable evidence** using the [architecture views](architecture.md).
4. Open the [Google technology proof map](google-technology-evidence.md) and distinguish deployed components from extensions.
5. Finish with [competitive positioning](competitive-positioning.md) and [measurable future pilot plan](release-scope.md) without promising unmeasured superiority.

No screenshot, model example, count or architecture box should be used to bypass these release/source limits. Technical operator credentials, guest IDs, cloud account numbers and private receipts must not be pasted into public judging artifacts.

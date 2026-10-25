# BatchBeacon cloud setup, budget and operations

**Verified execution update, 18 October 2026.** The existing dedicated project,
Cloud Run, Firestore, private Storage, Artifact Registry, Gemini/ADK and provider
budget controls have been inspected and exercised. Current deployment and
acceptance status are in [STATE](STATE.md) and [recovery evidence](evidence/M3-submission-recovery.md).
Detailed account/resource receipts remain private. No replacement project was created.

U07/U09–U12 authorize the bounded existing project, INR6,000 lifetime envelope,
gated public synthetic application and public repository. The retail console is
session-owned; **BatchBeacon Operations** remains private. One existing dashboard
and two alert policies were inspected. Full application telemetry, uptime/alert
firing and closure, physical cleanup and external notification delivery are not
completed acceptance claims. No notification channel is configured by inference.
The tables below retain the configuration policy; proposals are not evidence of
an implemented resource. Use actual receipts for effective settings.

## Current authority reconciliation

U28 extends the existing funded period through **31 December 2026, 23:59 IST**;
U29 sets the Cloud Run provider monthly cap to **₹1,000** without changing its
₹800 lifetime allocation or the **₹6,000** project ceiling. U30's configured health
and component notifications and observed test receipts are separate from complete
Operations acceptance. No additional message is authorized by this record.

U31 changes development/public model pools to **₹1,100 / ₹650**; protected ₹600
and probes ₹150 preserve the ₹2,500 model total. The older tables below are the
original proposal, superseded only by these named amendments. Fresh continuation
readback confirms two unknown liabilities remain held and remaining public capacity
cannot admit the configured per-attempt reservation. Exact live balances and
reservation values remain in ignored private evidence.
Neither available funds nor an accounting-parser correction grants a new call or
settlement. The seven-call validation allowance is exhausted.

ModelPrice values are evidence-bound conservative ledger rates; `actual_nanos`
is the usage-derived ledger valuation, not a statement of observed provider invoice.
When cached prompt tokens are supported, they remain included in the full prompt
valuation at the original input rate. No inferred discount, tax credit, rate change
or liability release is permitted. See the [current acceptance checklist](USER_JOURNEY_AUDIT_AND_CORRECTION_PLAN.md#9-authoritative-acceptance-checklist-and-continuation-checkpoint).

## 1. Configure in dependency order

| Order | Proposed configuration | Local verification / gate |
| --- | --- | --- |
| 1 | Confirm the existing project ID and selected owner-controlled account; inspect current resources and organization policies | Read-only supported CLI/console checks. Keep account identifiers and auth state out of public artifacts. A project name is not a proven ID. |
| 2 | Confirm billing and map the approved finite lifetime pools and funded expiry to actual billing-currency SKUs | AUTH-SPEND; credits and available balance are not an unlimited grant. Verify actual costs/prices when setting caps. |
| 3 | Use selected Mumbai app/data placement and global model endpoint after compatibility checks | Inspect an existing Firestore database first. Database location is a durable choice; preserve an existing compatible database location instead of migrating/recreating it. Record any required supported fallback. |
| 4 | Enable only required APIs; establish distinct bootstrap, deploy, build and runtime identities | AUTH-CLOUD; inspect existing bindings and grant narrow required scopes. No runtime Owner/Editor, billing-admin or deploy-admin role. |
| 5 | Firestore Native-mode Standard database, proposed `(default)`; one private Standard Storage image bucket with uniform bucket-level access and public access prevention enforced | Resource names/locations are proposals until created. Enforce server ownership and bucket access/expiry. Review actual default/soft-delete behavior. |
| 6 | Small authorized Gemini/ADK and Firestore transaction/image probes | G0-X; record actual model endpoint/settings, quota, identities and failures. A direct SDK diagnostic cannot replace ADK P0. |
| 7 | Source build through Cloud Build/Artifact Registry; one Cloud Run service `batchbeacon-ai` | Private admission first; record actual build identity, image digest, runtime identity and revision. |
| 8 | Persistent app budget controls, minimum health/logging, guest/upload/currentness protections | Required before exposing paid public routes. App ledger must work across instances/restarts. |
| 9 | Public synthetic judge path, only when specifically authorized and verified | AUTH-PUBLIC plus security/budget checks; a private smoke does not prove anonymous judge access. |
| 10 | Private dashboard, cheap uptime/alert policies, operator runbook; optional explicitly authorized notification test | Approved OPS scope below. Record actual URLs/configuration and observed alert evidence after creation; do not claim notification delivery without it. |

Current verified Cloud Run settings are min instances 0, service/revision max 2, concurrency 1, 1 vCPU, 1 GiB and request timeout 60 seconds; the application evidence-run deadline remains 30 seconds. The earlier concurrency-4 maximum-upload exercise failed. At concurrency 1, three maximum-input requests succeeded and one platform-capacity rejection recovered with its original key. This is bounded backpressure evidence, not a throughput guarantee. Never raise limits unattended to hide failures. Max instances are not a total cost cap: [Cloud Run maximums](https://docs.cloud.google.com/run/docs/configuring/max-instances).

**Selected placement:** Mumbai `asia-south1` for Cloud Run, Firestore, Standard Storage and Artifact Registry if the actual existing project supports it. Preserve an existing compatible immutable Firestore location; choose a supported co-location fallback and record the reason if needed. Source country and participant residency do not impose a hosting region. The inspected official terms contain no explicit hosting-region or guest-retention duration requirement (SOURCES X05). **Gemini 3.8 Flash uses the documented `global` endpoint**; current model documentation lists `global`, `us` and `eu`, not Mumbai/Singapore regional inference. Disclose that Mumbai app/data placement does not guarantee India-only model processing. Sources: [Firestore locations](https://docs.cloud.google.com/firestore/native/docs/locations), [model locations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash).

### APIs and identities

Proposed baseline APIs: `run.googleapis.com`, `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, `aiplatform.googleapis.com`, `firestore.googleapis.com`, `storage.googleapis.com`, `logging.googleapis.com`, `monitoring.googleapis.com`. Inspect enabled services before adding any. Service Usage/IAM/Resource Manager are conditional bootstrap needs; Billing Budgets API only for API-managed budgets; IAM Credentials only for a chosen impersonation flow. Secret Manager is conditional on a real secret need. Do not add Firebase Auth/Hosting or another database/platform to complete a generic checklist.

| Identity | Proposed minimum rights to verify |
| --- | --- |
| Human bootstrap operator | Only approved API/resource/IAM configuration; resolve any actual human sign-in prompt during setup. Do not transfer broad ownership to the application. |
| Deployer | `roles/run.sourceDeveloper`, `roles/serviceusage.serviceUsageConsumer`; `roles/iam.serviceAccountUser` on the selected runtime identity. |
| Actual build identity | `roles/run.builder` for the documented source-deploy path; discover which account is actually used. |
| Runtime | `roles/aiplatform.user`, `roles/datastore.user`, and `roles/storage.objectUser` scoped to the image bucket. No billing, IAM, deployment or monitoring-configuration privileges. |
| Operations configurator/viewer | Narrow dashboard, alert, uptime and notification-channel configuration/view rights as needed; separate from runtime access. |

Sources: [source deployment](https://docs.cloud.google.com/run/docs/deploying-source-code), [model IAM](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/access-control), [Firestore IAM](https://docs.cloud.google.com/firestore/native/docs/security/iam), [Storage IAM](https://docs.cloud.google.com/storage/docs/access-control/iam-roles), [Monitoring access](https://docs.cloud.google.com/monitoring/access-control).

Use attached runtime identity/ADC and a supported local keyless flow. No downloaded service-account JSON key is required by this design. Firestore server clients use IAM and bypass client Security Rules, so real server-side guest-isolation tests remain mandatory. Sources: [Cloud Run identity](https://docs.cloud.google.com/run/docs/securing/service-identity), [Firestore server warning](https://firebase.google.com/docs/firestore/security/rules-conditions).

## 2. Approved finite budget and stop behavior

U09 authorizes this recommendation: **₹6,000 total incremental Google Cloud spending through 7 November 2026, 23:59 IST (`2026-11-07T18:29:00Z`)**. It is an authorization ceiling and risk buffer, not an expected bill or an instantaneous provider guarantee. No promotional credit/free tier is needed for the plan's arithmetic. Existing Codex subscription capacity is separate; no additional coding credits, paid skill services or new subscriptions are selected.

| Allocation | Lifetime maximum | Operating boundary |
| --- | ---: | --- |
| Application Gemini | ₹2,500 | Persistent pools below; no reset on restart, deployment or calendar rollover. |
| Cloud Run | ₹800 | Request-based, min 0/max 2, bounded concurrency/deadlines; initial supported service cap ₹400/month for October and November. |
| Cloud Build and Artifact Registry | ₹300 | Initially at most 120 aggregate build minutes, real machine type recorded; bounded images, retained submitted/rollback digests. |
| Firestore, private images and transfer | ₹200 | Bounded synthetic records/uploads, no global browser queries, aggressive polling or uncontrolled egress. |
| Native monitoring/logging | ₹600 | One cheap five-minute uptime check from at most three regions; bounded low-cardinality telemetry. |
| Operational contingency | ₹400 | Evidenced infrastructure variance or critical repair within the same service set; not extra feature/platform spending. |
| Tax, currency and reporting-lag buffer | ₹1,200 | Uncommitted; reconcile actual billed SKUs/tax. Do not turn a credit or delayed bill into a larger allowance. |
| **Total** | **₹6,000** | No automatic increase or unfunded extension. |

| Model pool | Lifetime limit | Admission |
| --- | ---: | --- |
| Development, final evals, baseline, pre-submission captures | ₹1,250 | Failed trials count. Preserve final-validation capacity within this pool before tuning. |
| General public synthetic exploration | ₹500 | Global cross-session limit plus per-session/incident/call limits. |
| Protected judge/demo reserve | ₹600 | Unavailable to development and generic exploration until the operator explicitly activates a bounded demo/judging allocation. |
| Bounded real-model probes | ₹150 | At most one paid probe per calendar day and 22 total during the funded period. Cheap HTTP uptime never calls Gemini. |
| **Model total** | **₹2,500** | Shared persistent reservation/reconciliation ledger; no monthly replenishment. |

Use a server-controlled phase/pool allocation for the protected reserve, never a client `isJudge` field. Judges retain ordinary anonymous synthetic access; do not require developer cookies. A public judging allocation can also be consumed by other anonymous visitors: preserve rate limits and show remaining capacity/unknowns privately, rather than promising exclusive judge access. The operator may activate the existing reserve within U09 without increasing it.

**Rate basis and reservations:** current global Flash pricing shows $0.75/$3.75 per million input/output through 31 December, with promotional credits back. Budget conservatively at gross $1.50/$7.50 and count response plus reasoning usage. Use ₹100/USD solely as a planning conversion assumption, not a quoted exchange rate; substitute actual local-currency SKUs before paid admission. Source: [official model pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing).

Candidate first-call limits: one candidate, 12,000 billable input tokens including images/tools/history, 4,096 billable output/reasoning tokens, supported LOW thinking after local verification, no paid search grounding/priority/cache-storage feature. Under that verified ceiling the arithmetic is $0.04872, or ₹4.872 at the planning conversion; reserve at least ₹6/call **only if actual configuration bounds all billed usage accordingly**. Otherwise use the larger verified upper bound or refuse admission. Count tokens through a supported mechanism; inspect SDK/ADK retry defaults. Source: [model limits](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash), [generation configuration](https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/models/inference). A context cap must not silently truncate necessary evidence into an apparently complete decision.

Reserve atomically before every paid attempt, including retries. Reconcile actual usage; keep unknown-outcome reservations conservative until reconciled, not zero. Missing/exhausted/expired ledger closes new paid admission while exposing retained evidence with truthful status. In-flight calls and non-model costs may still accrue. P0-13's fixed guidance evaluator is pure and makes no paid model call.

Configure a whole-project alerts-only budget of ₹4,800 over the funded period where custom-period support permits, plus supported monthly model-service cap ₹2,500 and Cloud Run cap ₹400. Verify actual currency, service support and recipients. **November's provider cap reset does not replenish lifetime application pools.** Whole-project alerts are visibility; service caps cover selected services and use delayed estimates. They can overshoot and do not stop every project cost. Source: [service spend-cap budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps).

Do not lift a cap, replenish from another protected pool, raise quotas/instance limits/privileges, add regions/services or buy coding capacity automatically. At 80% of an area's allocation, stop optional usage and reconcile remaining liabilities before required work. Treat 90% of the ₹4,800 operating allowance as a conservative admission stop for new discretionary external work; protect the remaining obligations/buffer. Critical work still needs a supported cost estimate within its pool. Estimates do not override the ₹6,000 authority ceiling.

**Sizing references, not workload measurements:** current [Cloud Run pricing](https://cloud.google.com/run/pricing), [Cloud Build pricing](https://cloud.google.com/build/pricing), [Artifact Registry](https://cloud.google.com/artifact-registry/pricing), [Firestore](https://cloud.google.com/firestore/pricing), [Storage](https://cloud.google.com/storage/pricing) and [Observability](https://cloud.google.com/products/observability/pricing). For example, 22 days × 288 five-minute checks/day × 3 regions = 19,008 regional checks; $0.30/1,000 gives ₹570.24 under the planning conversion before allowances. Actual service SKUs/free-tier sharing must be checked. Do not add an external observability vendor, BigQuery export or paid synthetic browser runner.

### Local settings mapping

The existing optional `scripts/configure_local.py` helper collects values interactively; it is not the autonomous setup path. After actual discovery, Codex can safely create its documented ignored JSON schema directly and run `python3 scripts/configure_local.py --check`. Use approved policy and observed facts instead of repeating owner questions. Its structural check is not runtime budget enforcement.

For that summary schema: `currency=INR`, `total_allowance=6000`, `evaluation_allowance=1250` (the whole development/final-eval/capture model pool), and `demo_and_service_reserve=2350` (₹600 protected model + ₹150 probe + ₹800 Cloud Run + ₹600 monitoring + ₹200 data allowances). The remaining ₹2,400 covers ₹500 public model + ₹300 builds/artifacts + ₹400 contingency + ₹1,200 buffer. These are overlapping-purpose summary fields over the exact non-overlapping allocation tables, not extra allowances. Use `service_retention_review_at=2026-11-07T18:29:00Z` and the verified submission cutoff. Exact project/database/bucket/account values come from discovery; never write placeholders as verified facts. The actual application ledger must implement the finer pools independently.

## Public guest admission after U23/U27

The deployed guest policy explicitly sets `max_issued_sessions: null`: there is
no lifetime guest-count ceiling. This supersedes the exhausted 22-session demo
configuration. Cumulative issuance accounting is retained. The current burst
policy permits 30 new sessions per 60-second window; existing guest reuse does not
issue another session. This is separate from the unchanged model budget, per-shop
limits and funded admission period through 7 November 2026. Eight-hour ownership
expiry remains enforced. Guest creation does not invoke Gemini. These values live
in the typed runtime configuration; they are not duplicated implementation limits.

## 3. Image and record retention correction

Enforce the eight-hour guest expiry on every access. The proposed 24-hour image target concerns removal of live sanitized synthetic model-input objects, not a guaranteed physical-erasure deadline. Storage lifecycle deletion can retain soft-deleted objects for seven further days under the default policy, and policy changes can take time to apply. Preserve/disclose the actual policy; do not disable recovery on an existing bucket. Source: [Storage lifecycle](https://docs.cloud.google.com/storage/docs/lifecycle).

Firestore TTL is delayed, billable and does not delete subcollections beneath an expired parent. Attach appropriate expiry to each retained collection group or implement a narrowly bounded cleanup path. Session denial must not wait for TTL. Source: [Firestore TTL](https://docs.cloud.google.com/firestore/native/docs/ttl).

Review/custodian fixtures have separate approved retention and cannot disappear before final evidence is captured. Keep private traces, source rights, synthetic labels and cleanup status honest. Retaining the judge application does not mean retaining each guest image through judging.

## 4. Approved private operations dashboard

Name: **BatchBeacon Operations**. Use native Cloud Monitoring and structured Cloud Logging. Cloud Run integrates with Monitoring and collects application stdout/stderr; supported structured log fields permit request/trace correlation. Sources: [monitoring](https://docs.cloud.google.com/run/docs/monitoring), [logging](https://docs.cloud.google.com/run/docs/logging).

| Group | BatchBeacon signals and use |
| --- | --- |
| Availability and release | Request/5xx count, uptime, actual deployed revision/digest, last successful request and last verified journey. A healthy landing page is not a successful AI journey. |
| Runtime | Request latency with sample count, CPU/memory, active instances and measured warm/cold distinction. |
| AI and allowance | Model attempts, timeouts, quota/service/schema errors, actual returned token usage, estimated spend and its age, remaining app allowance, protected demo reserve and circuit status. |
| Evidence | Source family/version/hash and review/freshness state, last approved refresh, failed refreshes. No claim of continuous recall monitoring. |
| Workflow | Verdict/recapture/review counts, stale actions blocked, duplicate actions reconciled, session denials. Operational counts are not model-accuracy estimates. |
| Persistence/cleanup | Firestore/Storage errors, expired access denied, cleanup attempts/outcomes and known retention delays. |

Use low-cardinality metric labels; keep request/session identifiers in restricted logs. No raw images, session capabilities, tokens or personal data in telemetry. Keep technical details out of the retail decision flow except where they explain a meaningful user state. The retail console has its own session-scoped workflow views; it receives no global technical metrics, project identifiers, budgets, IAM or operator links. No external observability vendor is needed.

### Acceptance and task links

U07 adopts OPS-01–07 as implementation obligations. They are not claims that telemetry or a dashboard already passed. T36 owns the private dashboard/availability implementation. OPS-03b external notification delivery is optional pending a concrete channel; it does not block dashboard-visible alerts or the other P0 gates.

| ID | Acceptance and evidence | Tasks |
| --- | --- | --- |
| OPS-01 | Actual private dashboard opens for an authorized operator; guests cannot access global metrics/logs. Store sanitized configuration and verified access evidence. | T36, T23 |
| OPS-02 | A known synthetic success and controlled failure populate views/log queries with source/model/verifier/guidance/revision provenance. Missing/stale data is labelled. | T36, T18, T20 |
| OPS-03a | Uptime, repeated-error and budget/circuit alert policies exist. A controlled scoped signal produces an observed dashboard-visible incident; do not disrupt the public judge service to test it. Record thresholds and actual firing/closure evidence. | T36, T18 |
| OPS-03b | Optional external delivery: after a destination and test are explicitly authorized, one test reaches it. Otherwise record NOT CONFIGURED, not PASS or on-call coverage. | T36, T32 |
| OPS-04 | Five-minute cheap health/uptime checks make no Gemini call; cached dependency status has observation time. Any paid daily probe is actually configured, bounded and verified or explicitly NOT CONFIGURED. | T08, T36, T23 |
| OPS-05 | Exhausting a test allowance blocks new paid admission without lifting caps or reviving stale actions. Preserve known evidence and recovery guidance. | T09, T18, T23 |
| OPS-06 | Actual native goal/process observations, queue, allowance, expiry and stop reason are recorded privately under .local; public STATE holds only the pointer and sanitized status. Actual canary evidence is required; a nonexistent job cannot pass. | T02, T32 |
| OPS-07 | Expired sessions are immediately denied; observed image/Firestore cleanup behavior and delays match disclosures. | T09, T18, T23 |

Initial thresholds: two consecutive five-minute health failures; at least five 5xx responses and >10% errors within five minutes; budget/circuit exhaustion; at least three model quota failures within ten minutes. These are prototype policies; verify supported filters and adjust from actual samples with a decision record. Notification destination/test authority remains optional and unresolved; a login email is not permission to send test messages. Google's built-in spend-cap notifications go to project owners/billing administrators, with no custom recipient selection. U09/U10 allow native budget configuration; verify and disclose actual recipient scope before enabling it, and never issue a test message to an inferred address.

## 5. Runbook and judging ownership

After implementation, record actual dashboard/log links, resource identities, deployment revision, cost controls and safe diagnostic/rollback commands. When a journey fails, separate source/model/budget/auth/persistence/UI failures and inspect the relevant correlated evidence. Reconcile uncertain action/deploy outcomes before retrying.

Rohit is the resource/spend owner. Fund and preserve the known-good judge endpoint/dependencies through **7 November 2026, 23:59 IST** under U09. Later finalist obligations require a new finite funded decision; flag this before expiry. The actual service can accrue non-model costs after the application's paid-admission expiry. Before release, record verified reversible deactivation/scale-to-zero/access steps and remaining storage liabilities; do not claim automatic shutdown unless a supported mechanism was actually configured and tested. No destructive cleanup or deletion of submitted/rollback evidence is authorized by expiry alone. This document does not start a monitor or establish human on-call coverage. Make only necessary authorized critical repairs and preserve the submission revision.

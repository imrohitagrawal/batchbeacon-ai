# Cloud pricing discovery checkpoint

Status: account currency and selected model/Run prices verified. Paid admission
remains closed pending complete settings, cost reservations and bounded probes.
This is T02 evidence, not a G0-X service/model pass.

The existing dedicated project was verified before mutation. Its selected billing
account matches the private owner hint and is open, billing enabled, currency INR.
Global CLI defaults point elsewhere, so every request uses explicit target project
or quota-project scope. Account IDs and exact discovery records stay private.

The Cloud Billing API was disabled. Under U10’s required configuration grant, the
primary enabled only `cloudbilling.googleapis.com` on `batchbeacon-ai`, with no IAM
change. This conditional dependency is needed to satisfy OPERATIONS’ account-price
verification. [Google’s Pricing API setup](https://docs.cloud.google.com/billing/docs/how-to/get-pricing-information-api)
requires that API. An independent read-only reviewer verified enabled status and
retrieved account metadata plus exactly six account SKU prices, all HTTP 200,
without a currency override. All use Default consumption model `7754-699E-0EBF`,
`default-price`, with contract price equal to list price.

| Selected service / SKU | Exact INR account rate |
| --- | --- |
| Vertex Gemini 3.8 Flash text input, `2A35-AC68-14D6` | ₹143.983124998 / million tokens |
| Vertex Gemini 3.8 Flash image input, `5A4B-8A14-AE05` | ₹143.983124998 / million tokens |
| Vertex Gemini 3.8 Flash output, `90FD-DC5F-DC55` | ₹719.91562499 / million tokens |
| Cloud Run request-based CPU Tier 1, `4856-B847-F1EB` | ₹0.002303729 / vCPU-second |
| Cloud Run request-based memory Tier 1, `02A2-9231-36A6` | ₹0.000239971 / GiB-second |
| Cloud Run requests, `2DA5-55D3-E679` | ₹38.395499999 / million after shared monthly free tier |

Mumbai is Tier 1 in [Cloud Run pricing](https://cloud.google.com/run/pricing).
The account request rate has a zero-priced first 2 million tier aggregated across
the account/month. No free-tier availability is assumed. The CPU and memory API
prices differ from the rounded public UI display by one nanorupee per unit; exact
API values are retained privately. Model SKU service binding was checked against
Vertex, avoiding similarly named Gemini API SKUs.

At the proposed 12,000 billable-input and 4,096 total output/reasoning ceiling,
the gross model arithmetic is ₹4.67657189993504 before tax/other charges. This is
not yet a safe runtime reservation: input counting, output/reasoning accounting,
retries, endpoint availability and the actual request configuration must be
verified first. The introductory model offer uses credits back; reserve gross
and do not assume any credit posted.

Account pricing does not establish incurred/unbilled spend, credits, funds,
remaining finite pools, tax or resource usage. No model call, app deployment,
Firestore transaction or paid endpoint ran. All other ₹6,000 allocation pools,
protected reserves and funded expiry remain as recorded in OPERATIONS. Remaining
service SKU mapping and the persistent runtime ledger are not replaced by this
six-SKU checkpoint. Private raw evidence, binding checks and hashes are retained
under `.local/run-records/T02-pricing-discovery/`.

## Settings and resource discovery follow-up

The primary enabled the required Firestore API to resolve the resource-discovery
precondition. A successful explicitly scoped database list returned no databases,
and the available-location response included Mumbai `asia-south1`. No database,
bucket or runtime identity was created. The project IAM snapshot contains one
Owner binding; the project-level policy list is empty. That list alone does not
establish every effective inherited organization constraint. No IAM binding changed.

Ignored `.batchbeacon/local-settings.json` now exists and passes the repository’s
structural checker. It distinguishes observed project/currency/location facts from
proposed database/bucket/model/service settings. Paid and public admission remain
false. Allowance summaries match OPERATIONS without adding pools or claiming a
runtime ledger. Candidate bucket naming is not proof of global availability.
The current model remains untested through this account. These are T02 preparation
facts; T08 still owns actual bounded model/service/deployment admission.

Independent read-only settings review found no reproduced blocker: discovery
bindings, observed/proposed distinctions, ₹6,000 summary arithmetic, policy dates,
closed admission flags and ignored/untracked private storage all matched.

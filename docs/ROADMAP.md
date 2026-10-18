# BatchBeacon AI roadmap

Scope visibility, not a delivery claim or date commitment. B0 is incomplete; the
current finite run and release gates remain unchanged. P1/P2 items do not enter
the submission critical path. Stages follow EXECUTION §10.

| Stage | User value and scope | Promotion evidence |
| --- | --- | --- |
| B0 — supported corpus prototype | Complete the approved synthetic recall → evidence → confirmed simulated action journey, owned retail queue, bounded guidance loop and private operations. | Actual model/service/deployment evidence, source review, protected evaluation and release gates; current status in STATE. |
| B1 — validated investigation workflow | Make related customer notices and their product pictures easier to inspect; validate useful exports, language support or linked multinational incidents with users. | Measured investigation benefit, exact source attribution, uncertainty and scope preserved, reviewed reuse and no false acceptance. |
| B2 — governed source ingestion | Approved authority-specific ingestion of notice pages and linked attachments, version changes and optional integration adapters. | Bounded fetch/parser/model costs, document lineage, conflict review, privacy, security and operational acceptance for each adapter. |
| B3 — scalable operations | Governed paid operation, regional processing, entity resolution and monitored integrations. | Validated demand, budget and incident controls, isolation, monitored reliability and regional requirements. |

## ATT-01 — customer-notice PDFs and product-image evidence

Requested by the owner during implementation. **PLANNED; deferred from this run.**
B1 starts with reviewed attachments in the supported corpus; automatic ingestion
belongs to B2. Owner: primary integrator for a separately admitted future increment.

The motivating [World of Sweets customer PDF](https://s3-eu-west-1.amazonaws.com/fsa-alerts-files/production/FSA-PRIN-47-2026/FSA-PRIN-47-2026-World-of-Sweets.pdf)
contains product photographs and additional instructions. Its parent FSA page
and version-specific attachment have a lot/date scope difference. Existing
technical inspection retained PDF bytes, extracted text and page renders
privately; it did **not** implement application PDF extraction, embedded-image
extraction, image-based identity resolution or approved artwork redistribution.
See [inspection evidence](evidence/M1-attachment-inspection.md).

Planned bounded increment:

1. Show the exact attachment link, issuer, notice version and inspected/reviewed
   status beside the parent source, including an explicit discrepancy indicator.
2. Retain the permitted original bytes and content hash; extract text/tables with
   page citations and product-image regions with page/bounding-box provenance.
3. Let a reviewer associate each image with the correct product, pack and typed
   identifiers. Pictures assist identification; resemblance alone never proves
   a recalled lot or product identity.
4. Compare parent and attachment restrictions without silently merging them.
   Production date, best-before, use-by, product code and lot remain distinct.
   Conflicts and unclear associations remain review-required.
5. Add original/update lineage and measured extraction/citation accuracy, image
   association error rates, reviewer effort, latency and cost. Set acceptance
   thresholds before implementation; include conflicting and unreadable cases.

Dependencies: completed B0 core, attachment reuse decision, human source review,
bounded untrusted-document processing and a reviewed evaluation set. Public
preview/rehosting of third-party product artwork requires its applicable reuse
basis. Until then provide the official links and fresh synthetic demo labels.
This item does not defer any existing mandatory source-review obligation or
silently expand the approved P0 requirements.

## CON-01 — Consumer Recall Explorer

Owner-requested future task; **PLANNED, not implemented**. Extend ATT-01 with an
accessible public consumer dashboard: search by product, brand, country, date and
reported hazard; inspect permitted product images, affected lots and official
actions. Image-assisted discovery produces candidates for exact identity/lot
confirmation. Frequency views require declared coverage, time windows and
deduplicated events; reported hazards stay distinct from confirmed illness reports.

The [consumer roadmap](submission/consumer-recall-explorer-roadmap.md) defines the
experience, source-image dependency, stakeholder boundaries and proposed pilot
measurements. It is explicitly included in the presentation's future-development
section. It adds no implementation work to the frozen submission critical path.


## AUTH-01 — persistent retailer accounts

Owner-requested future scope; not implemented and not a submission dependency.
Provide verified Google/email sign-in and explicit sign-out with server-side
session revocation. Persist account/shop-owned investigations, evidence, queue
and guidance across session expiry and devices, subject to a published retention
policy and user/admin deletion controls. Signing out ends access, not the retained
account data. Retention duration and image-storage costs require separate admission.

Scope includes tenant membership/roles, least-privilege authorization, per-account
and global cost limits, verified email/recovery, and opt-in ownership-checked
migration of an active guest investigation. No silent transfer or broadening of
access. Google/email provider selection is deferred to the bounded future increment.

Acceptance: sign-in/re-entry restores owned work; logout/revocation blocks the old
session; another account/shop cannot read or alter records; expiry does not delete
retained account work; deletion and retention policies are tested; sign-up abuse
cannot reset global model spending. Account identity supplements anti-abuse controls;
it does not prove the user is trustworthy or eliminate denial-of-service costs.

## REG-01 — Destination-market requirements review

**Future discovery proposal. Not implemented or admitted for this release.**
Requested alongside the cross-country recall vision; distinct from CON-01 recall
search and ATT-01 notice-image evidence. Help a producer/importer compare a product
formulation with reviewed requirements in a destination market and prepare
questions for a qualified regulatory reviewer. Recall history alone cannot prove
compliance, import eligibility or permission to sell.

Flow: product/formulation → destination/category/date → official rule evidence →
possible restriction, missing information or applicable condition → specialist review.

Inputs require normalized ingredient identity, formulation quantity/concentration,
food category, intended use/population, label and intended market/date. A photo
alone may not supply the needed concentration or specifications; ask for missing
facts instead of inferring them. Rules may concern additive authorization and
limits, allergens/labelling, specifications and effective dates, with exceptions
and transitional provisions preserved.

Before implementation: choose one reviewed country pair and food category, obtain
source/reuse and legal-domain review, define version/freshness controls, curate
allowed/restricted/conditional/unknown cases, test unit conversion and identity
ambiguity, and admit budget/security separately. Distinguish proposed rules and
trade notifications from enacted, effective requirements. Expired or unreviewed
rules must yield needs-review, not compliance approval. No autonomous filing,
enforcement or launch authorization.

Primary references: [EU food-additive conditions](https://food.ec.europa.eu/food-safety/food-improvement-agents/additives/eu-rules_en),
[EU additives database](https://food.ec.europa.eu/food-safety/food-improvement-agents/additives/database_en),
[ePing product-requirement notifications](https://www.epingalert.org/).
These establish relevant source types and existing prior art, not completed
integration or worldwide coverage. Future output must cite the actual applicable
rule and date; a notification feed alone is not a complete legal rules database.

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

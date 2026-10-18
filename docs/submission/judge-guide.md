# BatchBeacon AI: judge guide

BatchBeacon connects the package in hand to the conditions in selected official recall evidence. The demonstration uses synthetic labels, historical sources and simulated actions.

## Try the retailer journey

1. Open the [live prototype](https://batchbeacon-ai-xotgrrfbcq-el.a.run.app). A bounded synthetic guest shop opens automatically.
2. Choose **Camembert Superieur Au Lait Cru** and the historical SFA cheese notice, then **Use this label**. Wait for the label image and choose **Extract and check**. Gemini proposes fields through one bounded ADK workflow.
3. Inspect the label beside the source conditions. The server compares product identity before lot, date and jurisdiction.
4. Review the result and explicitly confirm a simulated hold.
5. Refresh, open the retail queue and resume the same saved investigation. Counts and statuses belong to this guest shop.

This path passed in a fresh unauthenticated public browser on Cloud Run with actual Gemini/ADK and Firestore persistence. The same action survived reload and reopening from the queue; the phone layout had no horizontal overflow. Independent accounting and private-boundary checks passed.

## Two workspaces

The **retail console** serves staff and demo managers: owned queue counts/status, missing evidence, resumability, simulated actions and capture guidance.

**Private BatchBeacon Operations** serves the operator: verified deployment resources, monitoring dashboard, alert-policy setup and cost oversight. Its technical privileges remain outside guest access. Full application telemetry and observed alert firing/closure are not claimed. Operators provide an indirect reliability benefit to other stakeholders; consumers and authorities are not current dashboard users.

Guidance adaptation is bounded to allowlisted wording. Fixed evaluation precedes explicit activation, and rollback revisions increase. Six cases and nine variants support fixed evaluation. Actual deployed activation and rollback, persistence and foreign-shop isolation are verified in the [release evidence](../evidence/M3-submission-recovery.md).

## Read the scope

A lot number alone cannot establish identity. Both reviewed SFA cheese identities are positive source examples. A same-lot wrong-product counterexample uses a third synthetic identity.

Missing, stale or unsupported evidence stays in review. UK FSA parent and company attachment conditions remain separate, and UK matching stays review-only. A scoped no-match is not food-safety clearance or permission to consume or sell.

The fixed guidance suite and engineering checks are not protected model-quality accuracy results. Comprehensive protected evaluation and a competitive baseline are not claimed. No real stock mutation occurs.

## Vision and practical impact

The immediate value is a clearer retail investigation and handover. A proposed retailer pilot would compare assisted and manual review using the same reviewed cases, measuring time, completion, unsupported actions, evidence quality and cost.

The future **Consumer Recall Explorer** would offer accessible mobile cards and product/brand/country/date/hazard filters, affected lots and plain-language official actions with source/date. Planned ATT-01 notice/PDF imagery would support proposed CON-01 visual candidate search; exact identity and lot confirmation would still follow. Neither attachment image extraction nor catalogue visual retrieval is implemented.

Future permissioned retailer/authority insights require defined source coverage, time windows and deduplicated event/version/incident counts. Keep reported hazards, allergens and pathogens separate from officially confirmed illness reports. Counts establish neither disease causation nor brand safety. No current adoption, population analytics or measured harm reduction is claimed. See the [future proposal](consumer-recall-explorer-roadmap.md).

Public source: https://github.com/imrohitagrawal/batchbeacon-ai

Live prototype: https://batchbeacon-ai-xotgrrfbcq-el.a.run.app

Final video and PDF links remain pending. The [owner-approved scope](release-scope.md) lists incomplete internal acceptance. This is a bounded synthetic demonstration: if an allowance or provider capacity is unavailable, retain/reconcile the existing case rather than repeat extraction. Private Operations links and guest identifiers are excluded.

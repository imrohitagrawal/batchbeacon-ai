# CON-01 proposal: Consumer Recall Explorer

**Future proposal for a separately admitted increment. Not implemented, not a submission dependency, and not a change to the frozen P0 contract.** Extend the existing planned [ATT-01](../ROADMAP.md#att-01--customer-notice-pdfs-and-product-image-evidence); do not duplicate or mark it complete.

## User story and intended experience

As a consumer, I want to find an official recall notice by product, brand, country, date or reported hazard, inspect reference product imagery and affected lot conditions, and understand the authority's recommended action and what remains unknown.

Use accessible mobile cards with clear product names, useful images, legible type, strong contrast, keyboard-operable filters, screen-reader labels, descriptive image alternatives and plain-language official actions. Every result shows the authority, jurisdiction, notice and update dates, original source link and affected lot/date conditions. A missing photograph must not hide an otherwise relevant result. An attractive layout supports evidence comprehension; colour or visual similarity alone never communicates a match or safety status.

## Dependency chain: ATT-01 to visual discovery

1. **ATT-01, planned:** retain permitted notice/PDF bytes and hashes; extract product-image regions with page, bounding box and source/version lineage; review their product/pack association and reuse basis. Keep parent/attachment conflicts visible.
2. **CON-01, proposed:** display permitted reference imagery and offer image-assisted candidate retrieval. A package photograph can help narrow candidates, with provenance and uncertainty visible.
3. **Confirmation:** inspect the exact product identity, typed identifiers, market and lot/date conditions against the selected official notice. Visual resemblance is never a definitive product/lot match, clearance or permission to consume.

Current delivery is photographed synthetic-label extraction through Gemini/ADK followed by deterministic identity/lot checks. It does **not** implement source-PDF product-image extraction, an image catalogue, visual retrieval or a consumer dashboard. Official artwork must not be publicly rehosted without the applicable reuse basis. Link to the authority while that decision is unresolved.

## Frequency and health-language contract for the proposed view

- Label the selected time window, date field, authorities/countries covered, collection/update time, gaps and deduplication method beside every frequency view.
- Count deduplicated recall events separately from notice versions/updates, affected products and retailer shop incidents. Do not silently combine categories, jurisdictions or time windows. Preserve traceable event-to-notice links.
- Describe a count as reported recalls in the declared source corpus. It does not establish market incidence, global completeness, product risk or brand safety. Brand counts cannot rank safety without exposure denominators and comparable reporting coverage.
- Keep reported hazards, allergens and pathogens distinct from **officially confirmed illness reports**. Show the authority's exact classification and source date. Missing illness information means not reported/unknown, never zero illnesses.
- Never infer disease caused by a product, people affected or causation from a hazard keyword, recall count, model inference or visual similarity. An authority-reported illness association must retain its attribution and stated qualification.
- Show official recommended actions in context with their source/version. No food-safety, consumption or sale-release clearance is generated.

## Audiences and privacy

| Experience | Intended audience | Status and data boundary |
| --- | --- | --- |
| Retail console | Staff and demo managers | Current synthetic, session-owned queue, evidence, resumable cases and explicit simulated actions. |
| Private BatchBeacon Operations | Technical operator | Current verified resource/monitoring-policy/cost subsets; technical privileges remain private. Full telemetry or observed alert firing is not asserted. |
| Consumer Recall Explorer | Public individual users | Future public official-evidence discovery; no exposure of guest records, private operational links or protected evaluations. |
| Permissioned aggregate insights | Retailer companies and country authorities | Future governed view of defined event/reason/category/response trends. Private shop records require an explicit permission and aggregation basis. |

Immediate product/producer value is exact affected identity and batch context; retailer value is consistent investigation and traceable handover. Future consumer access could improve understanding across languages and jurisdictions. Societal or national benefit is a hypothesis to measure, not demonstrated harm reduction or adoption.

## Proposed pilot outcomes and admission

Compare assisted and manual review on the same reviewed cases. Record sample size, case mix, language, jurisdiction, missing images and timing method before interpreting a result. Proposed scorecard: completion rate, median review time, unsupported-action count, evidence completeness, uncertainty comprehension, image-candidate error, exact identity/lot confirmation success, latency and cost per completed investigation.

Proposed targets to ratify before a future pilot: every displayed action has an official source/version; no visual-only definitive match; no unsupported safety/causation statement; complete keyboard access to the core search/detail journey. Test whether assisted median review time improves without lowering correct identity/lot confirmation or evidence completeness. These are proposed goals, not achieved results or already approved numeric release thresholds. Set sample size, tolerances and budget in that increment's admission.

Promotion requires completed applicable core gates, human source/reuse review, bounded untrusted-document processing, reviewed evaluation cases including conflicts and unreadable images, accessibility review, privacy/isolation verification and the owner's separate scope/cost admission. No implementation, extraction, cloud expansion or dependency installation belongs to this packaging change.


Related future retailer foundation: [AUTH-01 persistent accounts](../ROADMAP.md#auth-01--persistent-retailer-accounts)
adds Google/email sign-in and account/shop-owned saved work across sessions and
devices, with logout/revocation, roles, retention/deletion and bounded usage.
It is not implemented; public consumer recall browsing need not require login.

# Recall context: prior-report audit and source addendum

Status: **NEW CONTEXT PENDING HUMAN REVIEW**. SFA first-slice matching approval and
U02 visual approval remain historical and unchanged. This addendum does not
approve UK source predicates, remaining gold, H custody or final submission.

## What the previous report preserved

| Layer before this correction | Preserved | Missing explicit context |
| --- | --- | --- |
| Saved official SFA and UK notices | Full captured reason, risk, product and action text | No evidence of source-capture loss |
| M1 human source checklist | Products, packs, identifiers, dates, geography, expected outcomes | Reason, health risks, actions and explicit quantity/legal absence |
| SFA approved JSON | Matching facts, importers, source URL and capture hash | Reason, risk and actions; do not rewrite its approval hashes |
| UK private packet v2 | Reason, recalling business and matching facts | Risk, company/customer actions and explicit quantity/legal absence |
| Approved refined prototype | Product comparison, historical source links and workflow states | Findable recall reason and detailed notice context |

Root cause: acceptance and independent review concentrated on matching predicates.
They did not test whether a user could understand why the recall existed and what
its notice said. The owner identified the gap. It is consolidated as one
REQUIRED_CONTRACT reporting-completeness issue under the expanded requirement;
no demonstrated false match was found. The correction is a version-bound context
record and visible cited presentation, separate from matching predicates.

## SFA contextual addition

[Official notice, 9 October 2026](https://www.sfa.gov.sg/news-publications/newsroom/recall-of-raw-milk-cheese-products-due-to-potential-presence-of-shiga-toxin-producing-escherichia-coli).
These statements describe that historical notice, not an individual item test.

| Detail | Notice-derived summary | Source section |
| --- | --- | --- |
| Recall reason | Possible Shiga toxin-producing E. coli (STEC) | Title and paragraph 1 |
| Why / reported basis | SFA cites a European RASFF notification about possible STEC in Fromagerie Gillot raw-milk cheeses. | Paragraph 1 |
| Authority-stated health risks | SFA warns of potentially serious infections, including diarrhoea, stomach cramps and vomiting; contaminated food may look and smell normal. | Paragraph 3 |
| Packs, codes, lots and dates | Both cheeses: 250 g packs, France, lot 232511, best before 17 October 2026. Pack size is not the total quantity recalled. | Paragraph 5: both product blocks |
| Total recalled quantity / batch volume | Not stated in this notice. | Complete notice reviewed; no total units/weight or batch-volume figure |
| Recalling business / importers | Camembert Superieur: Cold Storage Singapore (1983) Pte Ltd. Bertrand Pere & Fils: Little Farms Pte Ltd. | Paragraph 5: importer fields |
| Company action at publication | Recall ongoing as of the 9 October 2026 notice. | Paragraph 2 |
| Regulatory action at publication | SFA directed the two named importers to recall the implicated products. | Paragraph 2 |
| Legal proceedings / penalties | Not stated in this notice. | Complete notice reviewed; no proceedings, fine or court finding stated |
| Authority advice | SFA advises against consuming implicated products; buyers with health concerns after consumption should seek medical advice. Read the notice for the complete advice. | Paragraph 4 |
| Geography | Singapore; products originate from France. | Paragraphs 2 and 5 |

## UK contextual addition

[Original, 24 September 2026](https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026)
and [update 1, 25 September 2026](https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026-update-1).

| Detail | Notice-derived summary | Source section |
| --- | --- | --- |
| Recall reason | Salmonella contamination | Title and introductory paragraph |
| Why / reported basis | FSA reports Salmonella was found in both products. | Introductory paragraph |
| Authority-stated health risks | FSA lists fever, diarrhoea and abdominal cramps as usual symptoms. | Risk statement |
| Packs, codes, lots and dates | Truffles: 120 g, product code 319456. Knafeh and pistachio milk chocolate: 100 g, product code 318591. All best-before dates; lot restriction not stated. | Product Details: both product blocks |
| Total recalled quantity / batch volume | Not stated in this notice. | Complete notice reviewed; no total units/weight or batch-volume figure |
| Recalling business / importers | World of Sweets | Introductory paragraph |
| Company action at publication | World of Sweets is recalling both products; point-of-sale notices will be displayed in stores selling them. | Actions taken by the company |
| Regulatory action at publication | FSA published this Product Recall Information Notice. A specific enforcement order is not stated. | Notice reference and About product recalls and withdrawals |
| Legal proceedings / penalties | Not stated in this notice. | Complete notice reviewed; no proceedings, fine or court finding stated |
| Authority advice | FSA advises buyers not to eat these products and to return them for a full refund. Read the notice for the complete advice. | Our advice to consumers |
| Geography | England and Northern Ireland. | Geography heading |

Update 1 adds Wales and Scotland, retaining the original jurisdictions. Its reason,
products and stated actions remain the same. The context record binds each version
to its own source URL and capture hash. A product code is not a lot number.

“Not stated” is limited to the reviewed captured notice. It does not mean zero,
no legal action anywhere, or that an unread source contains no detail. Unknown or
unavailable extraction instead displays “Not verified from this notice.” General
FSA explanatory text does not establish a case-specific enforcement order.

## Display and review contract

The reason is visible in the workbench and queue. Expanded details distinguish
health risks, packs/identifiers/dates, aggregate quantity, actors, company and
regulatory actions, legal proceedings, authority advice and geography. A negative
synthetic identity has no attributed recall reason; its comparison notice is
explicitly labeled. Historical UK evidence cites the original, with the update
linked separately. Failure to load context does not masquerade as “not stated.”

The canonical proposed data is [context.draft.json](../../fixtures/sources/context.draft.json).
The existing approved [SFA manifest](../../fixtures/sources/sfa-reviewed.json) is
unchanged. All newly added context remains PENDING. Limited factual summaries and
links are proposed; no authority logo, photograph, full notice or retailer PDF is
redistributed. UK attribution links OGL v3; no authority endorsement is asserted.
The exact private UK v3 packet includes labels, expected outcomes and reuse scope.

## Review pattern correction

Future source review has two explicit passes: matching predicates, then notice
purpose and consequences. Each requested context field must be source-supported,
explicitly absent from the captured notice, or unknown. Independent review must
check rendered context for every source/version, negative, stale and unavailable
state as well as field values. Pack size cannot stand in for total recalled stock;
regulatory publication cannot stand in for legal action. These are acceptance
criteria, not evidence that the full runtime or human review has passed.

## Before / after / why

| Before | After | Why |
| --- | --- | --- |
| Generic notice title | Visible reason, basis and exact source citation | Explain why the recall matters before asking for a decision |
| Only comparison facts | Native disclosure for cited context | Keep the primary task readable while retaining important detail |
| Silent omissions | Distinct not-stated and unknown states | Avoid invented quantities, legal facts or false completeness |

Validation status is recorded in M1-recall-context-verification.md after execution.

## Linked customer-notice correction

The owner identified a further omitted source detail: the UK notices link to
company customer-notice PDFs. Independent inspection confirmed distinct links on
the original and updated FSA parent pages, under “Actions taken by the company.”
The original text captures retained the anchor wording but not the hrefs. Fresh
browser observations establish these link targets separately; the old text hashes
do not establish the PDF bytes or newly observed hrefs.

The draft context now has explicit related-document presence/unknown states and
version-specific link metadata. The refined details show “Company customer notice
(external PDF) — linked by FSA,” its original anchor title, new-tab behavior and
the unreviewed-contents limitation. SFA attachment coverage remains UNKNOWN.
Authority citations remain separate. No PDF was downloaded, rehosted, interpreted
or included under an assumed redistribution license. The existing SFA matching
approval remains unchanged; the expanded context/link review is still pending.

Root cause: the context checklist tested fixed text fields and parent citations,
but not related-document destinations. The corrected review includes visible link
purpose, exact parent version, observed href, unknown state, and desktop/phone
keyboard and reflow checks. This is a reporting-completeness correction; it does
not retroactively invalidate unrelated matching/protocol tests.

Reason/symptom filtering and recall-frequency semantics are analyzed in
[RECALL_ANALYTICS](../RECALL_ANALYTICS.md). They are not implemented or represented
as existing retail incident counts.

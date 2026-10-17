# Human source and synthetic-gold review packet

Status: **SFA FIRST SLICE APPROVED BY OWNER; UK REVIEW PENDING**.
Rohit explicitly confirmed this SFA packet and its three linked labels as written.
T04a passes; T04b, other D gold and H custody remain open. Approval and reviewed
artifact hashes are in `fixtures/sources/sfa-reviewed.json`. No agent approval
substitutes for human review. Facts, capture hashes and
synthetic-image hashes are in `fixtures/sources/manifest.draft.json` and
`fixtures/synthetic/manifest.json`. Raw pages remain private under `.local/`.

## SFA first-slice checklist

[Official SFA notice](https://www.sfa.gov.sg/news-publications/newsroom/recall-of-raw-milk-cheese-products-due-to-potential-presence-of-shiga-toxin-producing-escherichia-coli),
issued 9 October 2026. Retrieved successfully; review source text and product table.

| Identity | Pack / origin | Lot | Best before | Proposed expectation in Singapore |
| --- | --- | --- | --- | --- |
| Camembert Superieur Au Lait Cru | 250 g / France | `232511` | 17 October 2026 | D01 supported match; deliberate simulated hold available only after current verification |
| Bertrand Pere & Fils Camembert au lait cru | 250 g / France | `232511` | 17 October 2026 | D02 supported match; this second cheese is not a negative |
| Meadow Vale Brie — invented third identity | synthetic 250 g / France | `232511` | 17 October 2026 | D07 no matching identity in these checked notices; not clearance or permission to sell |

Review the actual newly created labels:
[A](../../fixtures/synthetic/sfa-a.png),
[B](../../fixtures/synthetic/sfa-b.png),
[third identity](../../fixtures/synthetic/sfa-third.png).
All bear SIMULATED LABEL / NOT FOR SALE. No source photograph, brand artwork or
authority logo was reused. Confirm exact identities, pack, lot, date, geography,
expected outcome and absence of misleading artwork. Dates/codes remain raw as
well as normalized; leading zeros and lot case must not be discarded.

## UK original and genuine update checklist

[Original](https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026),
24 September 2026; [update](https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026-update-1),
25 September 2026. Ordinary browser access succeeded after automatic site
verification; direct fetch was unavailable. Captures hash the rendered main text,
not raw HTTP bytes. No challenge was solved or bypassed.

| Identity | Typed identifier | Pack | Date restriction |
| --- | --- | --- | --- |
| Alyan Dubai Style Chocolate Truffles | PRODUCT_CODE `319456` | 120 g | ALL best-before dates |
| Alyan Dubai Style Crunchy Knafeh and Pistachio Milk Chocolate | PRODUCT_CODE `318591` | 100 g | ALL best-before dates |

Original geography: England and Northern Ireland. The genuine update adds Wales
and Scotland. A product code is not a lot. The notice has no stated lot restriction
(NOT_SPECIFIED); that is distinct from UNKNOWN extraction. Human review must
confirm these interpretations before source-specific fixtures or update gates pass.
The demonstration must invalidate dependent old results, including old negatives,
then create a new current result and require renewed confirmation.

## Rights and custody decisions still required

Proposed reuse is limited factual data with source links and freshly created
synthetic labels. Do not redistribute raw pages, logos, official photographs or
retailer PDFs. [SFA terms](https://www.sfa.gov.sg/terms-of-use) distinguish website
material from datasets; the newsroom article is not automatically an openly
licensed dataset. Human rights review must accept this limited factual-reference
basis or identify required permission. UK copyright/terms review remains pending;
the [official copyright link](https://www.food.gov.uk/crown-copyright?navref=footer)
was observed on both pages but has not yet been successfully read.

An approval must identify this packet/version and any corrections; it is not an
approval of uncreated fixtures, all D gold or H custody. D01–D24 human audit and
protected H01–H08 custody remain separate. Do not put protected answers in this
repository or send them into the builder conversation. Keep H cases outside the
builder-visible workspace with their custodian until the frozen final run.

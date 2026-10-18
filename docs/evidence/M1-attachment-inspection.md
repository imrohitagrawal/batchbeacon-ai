# Company customer notices — technical inspection follow-up

The two version-specific FSA links now have privately retained PDF bytes and
page renders. Each is three pages. Both downloaded successfully. Their extracted
text matches, but their binary hashes differ. This is technical inspection,
not human source approval or permission to redistribute company artwork.

The [original company PDF](https://s3-eu-west-1.amazonaws.com/fsa-alerts-files/production/FSA-PRIN-47-2026/FSA-PRIN-47-2026-World-of-Sweets.pdf)
and [update-linked company PDF](https://s3-eu-west-1.amazonaws.com/fsa-alerts-files/production/FSA-PRIN-47-2026-update-1/Customer-notice-World-of-Sweets-recalls-Alyan-Dubai-Style-Crunchy-Knafeh-and-Pistachio-Milk-Chocolate-because-of-possible-contamination-with-SalmonellaDocument-update.pdf)
provide additional context:

- Page 1's narrative mentions `NM026A/` for a milk-chocolate description. Its
  table uses a production-date field. Page 3 adds a products/batches scope caveat.
- Page 2 distinguishes direct-purchase and other-retailer customer procedures,
  and includes collection/refund and retailer instructions.
- The health wording adds nausea and vomiting to the parent summary's symptoms.
  This is company-described risk, not a count of illness cases.
- A request for a customer's affected-unit count supplies no aggregate recall
  quantity. Separate attachments and parent versions do not establish new events.

These details must retain their issuer and page. The captured FSA parent lists
ALL best-before dates and no lot restriction. The difference does not authorize
silently converting production date to best-before, applying one lot to every
listed product, narrowing the parent scope or declaring other lots clear.

The private source packet now links a separate attachment addendum and preserves
its previous version. UK interpretation remains unapproved/review-only. Existing
parent context and domain predicates were not automatically changed. Human review
must account for the new scope difference before admitting UK matching. Earlier
SFA and visual approvals remain intact. Attachment metadata still records no
approved content interpretation; links remain available without PDF rehosting.

## Reproduction and review status

The complete six-page visual inspection substantiates a source-review completeness
finding, classified REQUIRED_CONTRACT under AC-01/02 and the source review gate.
No live false acceptance was demonstrated: UK source support is already unapproved.
The smallest correction is explicit review evidence and continued non-admission,
not a guessed replacement predicate. Independent verification confirmed the
six-page findings, unchanged source/context JSON, preserved earlier packet text
and closed UK source-admission gate. No documentation blocker remains; the
underlying human interpretation decision remains pending.

Original PDF: 146,784 bytes, SHA-256
`03d9b87131eb5817e472c6783abe0c9e9cc3958e9472241dfb34b7a207299ec6`.
Update-linked PDF: 160,572 bytes, SHA-256
`ccfa7d225287dcf98f744ddaad51ca0bec0b0fa961d4eb8aa8f88b4b4df7eb45`.
Exact bytes/text/renders and review receipts remain ignored local evidence. The
older [link correction](M1-recall-context-verification.md) remains valid for its
stated link-only scope. No application, runtime or human gate is closed here.

## Review-pattern correction

The earlier check deliberately verified destinations and accessibility while
leaving attachment contents unreviewed. It therefore could not establish that
the linked document agreed with the parent. Future source packets distinguish
link presence, successful retrieval, technical content comparison, permitted
reuse and human interpretation approval. None implies the next stage.

Before source admission, compare linked documents by issuer, product identity,
identifier type, lot and date type, geographic/version scope, risk certainty and
conditional customer steps. Record differences with exact page locators. Preserve
unknowns and per-document absence claims. Existing source-approval tests remain
applicable; a technical attachment inspection cannot set reviewed source metadata.

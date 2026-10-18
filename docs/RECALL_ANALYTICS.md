# Recall filtering and counting proposal

Status: owner-requested analysis, not implemented analytics or an amendment to the
accepted P0 scope. The retail console currently counts session-owned workflow
incidents. Those counts must not be relabeled as product recall frequency.

Reason, hazard and authority-described symptom filters would help users explore
reviewed recall evidence. Keep three separate dimensions, retaining exact wording,
certainty and citations. Possible STEC presence and Salmonella found differ;
fever or diarrhoea mentioned in an authority risk statement does not establish
reported illness, diagnoses, severity or contamination of a checked item.

The smallest future addition is fixed filters over the finite reviewed corpus,
with jurisdiction, covered period and source/version information visible. It needs
no new model, ingestion service or analytics platform. Broader frequency requires
a sufficiently complete historical corpus and reviewed product identity linkage.
Continuous ingestion/configurable analytics remain outside the current retail P0.

| Measure | Meaning |
| --- | --- |
| Unique recall events | Distinct source recall families; updates and repeated checks do not add events |
| Notice versions | Original and subsequent publications, shown separately |
| Affected products | Reviewed distinct product identities within each recall family |
| Product recall frequency | Distinct applicable recall families for an exactly resolved product, within a declared corpus and date window |
| Symptom filter count | Products/events whose reviewed authority text mentions that symptom; never illness cases |

For the UK example, two notice versions describe one recall family involving two
products. A future fever filter could report those units separately. This is an
illustration from draft source context, not an approved runtime analytics result.
Pack grams are not recalled units or batch volume. Products with similar names,
shared lots or different authority codes cannot be merged by guesswork.

Acceptance must cover update deduplication, exact identity, UK subnational scope,
first-issued versus updated-during-period semantics, unknown/unreviewed records,
overlapping facets and explicit AND/OR behavior. Rows and counts must derive from
the same bounded reviewed snapshot. No results means no matching reviewed mention
within that scope, not no possible risk or no recalls elsewhere.

Source-linked company/customer notices directly support the existing evidence
workflow and are being corrected separately. They retain their exact parent
version, accessible external-PDF label and observed-link provenance. Link presence
does not imply review of attachment contents or permission to reproduce them.

Later technical [attachment inspection](evidence/M1-attachment-inspection.md)
found company wording that differs from the parent authority page, including a
lot reference and a different date type. Preserve issuer, document role, exact
version and human-review status on every proposed filter value. Authority-only
symptom filters cannot silently acquire extra company-described symptoms. A
broader source filter would need to label the issuer explicitly. Conflicting
scope remains review-only, and neither another attachment nor another notice
version creates another recall event. These are acceptance refinements, not an
implemented analytics feature or a resolved UK source interpretation.

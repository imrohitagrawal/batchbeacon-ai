# HACKATHON_BRIEF.md
## BatchBeacon AI — Final Implementation Handoff

**Edition:** 1.0 — 17 October 2026, Asia/Kolkata.  
**Competition:** AI Builder Cup 2026, Hack2skill / Google Cloud.  
**Selected theme:** Retail & Commerce: Intelligent Customer and Business Experiences.  
**Recommendation:** CONDITIONAL GO.  
**Implementation state:** Not built, tested or deployed in this strategy session.  
**Research companion:** `HACKATHON_FINAL_REVIEW.md` explains the full six-theme comparison, technology landscape, scoring and adversarial review. This brief stands alone for implementation.

## 0. Document authority and how to use it

This is the **canonical final brief**. It supersedes the earlier `HACKATHON_BRIEF.md`, `HACKATHON_BRIEF_FINAL_REVIEW.md`, `HACKATHON_BRIEF_FINAL_WITH_ORGANIZER_TRANSCRIPTS.md` and Singapore-only assumptions in earlier replies. Do not merge obsolete feature lists or video timing into it. The selected product and P0 requirements below are the baseline; departures need a recorded reason tied to a failed gate, not another unrestricted brainstorming cycle.

The initial mandate prioritized winning competitiveness over unnecessary technical breadth and requested global applicability, all four judging criteria, independent technology research, a fallback and an actionable engineering handoff. Subsequent user instructions explicitly require worldwide problem scope. [S38]

**Evidence discipline:** Source facts are cited by [Sxx]. Product requirements, targets, risk judgments and effort ranges are proposed engineering decisions. No result table in this document is a test result. The word “final” identifies this consolidated decision baseline; it does not certify eligibility, originality, production safety or a probability of winning.

## 1. Product decision and selection rationale

### Exact selected challenge statement

> Build an AI-powered solution that transforms how businesses understand, engage, and serve customers while improving operational efficiency across physical and digital commerce. Solutions may address discovery, personalization, conversational shopping, demand planning, inventory, customer insights, or fraud.

This is the user's supplied statement, matching the published Retail & Commerce direction. The problem-solution fit is inventory intelligence and retail operational efficiency, with an indirect customer-protection benefit. Suggested challenge technologies are optional choices, not a requirement to deploy the whole list. [S02][S38]

### Product vision and pitch

**BatchBeacon AI helps retail teams turn official recall evidence and physical-product photographs into jurisdiction-scoped, reviewable actions, with explicit uncertainty and source-update recovery.**

Global vision: a reusable evidence-to-product verification core adaptable to different authorities, countries, formats and languages. Initial coverage: **two authorities in two countries, one in JAPAC and one outside it**, plus one genuine notice-version change. Do not describe this limited prototype as a worldwide monitoring service.

Primary users are small/midsize retailer managers, importers and distributors investigating an incident; workers capture package evidence; a manager approves a simulated hold. The hackathon evaluator uses an isolated guest sandbox with synthetic product-label assets. This is not a consumer medical adviser, regulator, laboratory test or autonomous recall executor.

### Why this project and not the alternatives

All six themes were evaluated. The feasible-prototype analytical estimates are BatchBeacon 78.6, FormBridge 77.0, FactoryProof 74.6, PolicyDiff 74.2, InvoiceGuard 74.0 and ContextSeal 73.2 out of 100. These are not measured or official scores. The small lead can reverse if innovation or feasibility assumptions fail.

| Finalist | Technical / Impact / Innovation / UX, each /10 | Weighted estimate /100 | Rationale |
|---|---|---:|---|
| BatchBeacon | 8.0 / 8.2 / 7.0 / 8.6 | 78.6 | Concrete source/label/version hard cases and bounded build; novelty unproven |
| FormBridge | 7.7 / 8.5 / 6.6 / 8.4 | 77.0 | Simpler accessible form completeness flow, but direct document-assistant overlap |
| FactoryProof | 7.2 / 7.7 / 7.3 / 8.3 | 74.6 | Visually compelling, but representative industrial data and validation risk |

Formula: **4T + 2.5I + 2.5N + UX**. Official weights are Technical 40%, Impact 25%, Innovation 25%, UX 10%. [S02][S03]

The three separate strategic lenses are demonstrable differentiation; verifiable global value with JAPAC relevance; and deadline-adjusted proof/delivery. They do not alter official weights. BatchBeacon is selected for a clear controlled demonstration, not to reuse the user's prior products or display the largest technology stack.

### Innovation thesis and forbidden claims

The thesis is a combined workflow: **source-scoped evidence → physical-product identity → applicable-condition checks → missing-evidence request → human action → source-change re-evaluation**.

Scanning, lot matching, no-inventory lookup, global alerts, recapture and audit records are already offered or claimed by existing products. Batch’d, Smart Food Safe and SuperRecall.ai are direct comparators. Do not claim these individual capabilities are inventions or assert that competitors lack our proposed combination without hands-on evidence. [S13][S14][S15]

Prove a narrow difference against a competent one-shot Gemini baseline: preserve scope and version, refuse incomplete evidence, request a useful follow-up, and invalidate dependent decisions when source scope changes. The project name is a working label; trademark, domain and patent clearance were not performed.

## 2. Competition requirements, transcript guidance and unresolved conflicts


### Competition constraints and compliance status

“PASS” below means the cited requirement or theme fit is established, not that an unbuilt submission already satisfies it. Every finalist remains **UNVERIFIED overall** until roster, deliverables and execution checks pass.

| Requirement | Current basis / status | Required implementation or submission treatment |
|---|---|---|
| Six broad themes; one selected theme | PASS, published themes and supplied statements [S02][S38] | Select Retail & Commerce; explain inventory/retail operations and customer protection. |
| Complete rubric | PASS: Technical 40%, Impact 25%, Innovation 25%, UX 10% [S02][S03] | Score all dimensions, not only engineering. |
| Eligible team | Rules verified; individual eligibility UNVERIFIED [S03][S05][S06] | 2–4 eligible professionals; 21+ and JAPAC conditions; no students. Team formation is already complete per user; do not restart recruitment. |
| Submission deadline | Date PASS: 18 October 2026; exact time/timezone UNVERIFIED [S01][S39] | Capture the current submission form/announcement before fixing the final clock. |
| Evaluation availability | Published Oct 19–Nov 6; finalists Nov 7 [S01] | Keep app, dependencies and judge access functioning through results; monitor beyond upload. |
| Google AI / deployment | PASS as a requirement [S05][S06] | Gemini with a bounded ADK workflow; submitted working Cloud Run URL. Firestore for application state. |
| Submission artifacts | Verified in transcripts [S05][S06] | English deck exported as PDF, real demo video, accessible source repository, live app, description and judge guide. Exact form file limits UNVERIFIED. |
| Video length | CONFLICT [S03][S04][S06] | Terms and later host say 3–4 minutes; FAQ says under 3. Main cut 3:20; alternate 2:40. Follow authoritative written clarification if form conflicts. |
| Code and assets | CONFLICT between terms/FAQ and expert Q&A [S03][S04][S06] | New project implementation and original demo assets during the event; inventory third-party libraries/data and rights. No recycled prior product as the entry. |
| Repository/access | Public repo safest; judge access must work [S03][S05][S06] | Public event-built source, README, sample inputs, evidence manifest, dependency notices; no secrets. |
| IP | Written terms impose conditions despite participant ownership statement [S04][S05] | Review the six-month first-refusal provision for an exclusive licence and promotional rights before submission. Do not equate this with automatic ownership transfer. |
| Secrets and synthetic data | Clear expert guidance [S06, 27:16–28:13; 36:07–36:16] | No secret exposure; label all simulated product photographs, actions and measurements. |

The linked terms state precedence over conflicting promotional material. A fresh codebase and a 3:20 video are conservative planning choices, not a claim that every conflict has disappeared. The exact treatment of pre-existing templates, public datasets and standard dependencies needs a provenance record and, where material, written clarification. [S04]

### Source conflicts that must not be hidden

The themes page also contains legacy wording about five social-impact categories despite publishing six actual themes. Use the supplied six challenge statements and current official theme selector; do not remap this retail project to a copied category. Older team-formation dates vary across sessions, website and the earlier dashboard observation; they are historical, not the current cutoff. [S02][S05][S06][S39]

Browser access was attempted in this final research pass and failed because the originating connected-browser context was unavailable. The authenticated submission form, latest announcements, exact cutoff/timezone, mandatory attachment fields and live roster checks were **not** verified in this pass. Earlier dashboard access is not presented as a fresh check. [S39]


### Session-specific implementation decisions

Both supplied transcripts were read in full; video frames/slides were not independently watched. These are the relevant source-based instructions, not reconstructed memories of the sessions. [S05][S06]

| Timestamp | Engineering consequence |
|---|---|
| Intro 31:53–33:57 | Real GenAI implementation and all rubric dimensions; no one-prompt wrapper presented as the entire innovation. |
| Intro 34:47–37:07; 45:49–46:12 | Progressive architecture; a few documents can go directly into model context. |
| Expert 13:02–14:50; 44:43–45:42 | ADK + Gemini + Cloud Run is appropriate; no framework earns automatic bonus points. |
| Expert 15:01–18:01 | Own-data grounding can suffice. Provide source records, guardrails and useful judge examples. |
| Expert 24:09–24:42 | Show latency improvements only after measuring them. |
| Expert 27:16–28:13 | Secret exposure is a submission disqualification risk. |
| Expert 34:30–36:16 | Reduce login friction safely; explicitly simulated data is acceptable. |
| Expert 36:23–38:14 | Complete one meaningful workflow beyond a bare happy-path prototype. |
| Expert 40:46–42:49 | Judges can visit during evaluation; preserve access, tag the deadline revision and restrict later fixes to critical repairs. |

**Deadline treatment:** Research clock was checked at 19:26 IST on 17 October. If—and only if—the final cutoff is confirmed as 18 October 23:59 IST, the interval from that checkpoint would be about 28 hours 33 minutes. This is an illustrative calculation, not verification of the cutoff and not the time remaining when this file is read. Recompute using the actual clock after Gate 0. Do not rely on an earlier dashboard countdown. [S01][S39]

## 3. Evidence corpus and global-impact foundation

### Verified source plan

| ID / role | Authority and material | What it establishes | How to use it |
|---|---|---|---|
| CONTEXT-WHO-2026 | WHO 13 March 2026 international cereulide incident [S07] | Historical affected-product distribution across 99 countries/territories; cross-border coordination need | Context/pitch only. Do not derive present-day local recalls or health advice from it. |
| SFA-CHEESE-20261009 | Singapore Food Agency cheese notice [S08] | Two different 250 g products share lot 232511 and a best-before date | JAPAC source adapter, product-identity and same-lot counterfactual tests |
| UK-ALYAN-ORIGINAL | FSA original chocolate notice [S09] | Original product/scope record | Historical snapshot for version comparison, never labelled the latest notice |
| UK-ALYAN-UPDATE1 | FSA updated notice [S10] | Coverage expands to Wales/Scotland; listed products have all-best-before-dates scope | Non-JAPAC adapter, scope-change and explicit wildcard tests |

The UK product identifiers displayed by the updated notice are product codes **319456** for the 120 g truffles and **318591** for the 100 g crunchy chocolate. These are source-specific product codes, not assumed GTINs. Preserve the source's identifier type. [S10]

The SFA products and UK chocolate products belong to different incidents. A shared “demo collection” must not be labelled a shared outbreak. P0 demonstrates portable parsing/verification and preserved scope, not cross-country identity resolution or uniform recall law. Adding a genuinely linked multinational incident is P1 only after verifying its individual authority notices and product identities.

### Data acquisition and rights requirements

Fetch only a small allowlisted set of public authority URLs. Record publication/update dates, retrieval time, final URL, source ID and content hash. Retain the minimum licensed evidence required for verification; preserve exact identifiers and source wording where material. Review publisher terms before distributing full documents/images. Do not bundle full authority webpages or logos in the public repository merely because they were readable online.

Create all package-label demo assets freshly during the event and visibly mark them **SIMULATED LABEL — DEMONSTRATION ONLY**. Counterfactual lot/product combinations are synthetic test cases, not claims about a real marketed product. Keep original source facts and synthetic variation metadata distinct. Never fabricate an official notice to make the product look better.

Notice extraction runs through Gemini, but supported P0 predicates must then be compared with a human-reviewed source manifest before they can support decisions. A source with unreviewed or incomplete interpretation is review-only. This is a supported-corpus prototype, not autonomous ingestion certification. The strategy session has verified URLs/content, not built or downloaded a runnable fixture set.

**Freshness modes:** “Historical demonstration snapshot” is acceptable and must display its date. “Live refreshed” requires a successful source fetch and revalidation. Source failure, an unseen version or expired freshness rules cannot be silently treated as current. Keep the latest known result viewable only as a clearly dated historical result.

### Sources deliberately not used as real-time authority

The FDA food enforcement API is a weekly historical dataset with explicit limitations as a public alert or recall-lifecycle source. It may support later research, not P0 live warning claims. FSANZ was checked as a potential expansion source, but no Australian formula fixture was validated for this final plan. A UK data API endpoint was not successfully accessed; use the verified public FSA pages instead of assuming API readiness. [S11][S12]

## 4. Primary user journey and interface

The first screen must answer: **What evidence was checked, in which jurisdiction, for which product, and what should the human review next?** Avoid a generic empty chatbot landing page.

1. **Start an incident.** Choose a supported jurisdiction and notice or a labelled demo case. Show source date, version, historical/live status and current coverage.
2. **Interpret the source.** Gemini proposes structured product restrictions and evidence locations. Validate against the reviewed manifest; flag any discrepancy rather than silently correcting the model's result.
3. **Capture the product.** Upload or photograph its identity panel and relevant lot/date panel. Preserve raw observations and model-extracted fields separately.
4. **Verify scope.** Execute server-side comparison for product identity, relevant identifiers, size, lot/date predicates and jurisdiction. Present a field-by-field evidence table.
5. **Resolve uncertainty.** Ask a targeted question such as “Photograph the lot code below the best-before stamp.” Allow user correction with provenance. At most two recapture requests; unresolved cases stay under review.
6. **Review the result.** Show exactly which predicates matched, contradicted or remain unknown, with clickable source evidence and limitations.
7. **Approve an action.** A deliberate manager action records a **simulated shelf hold or review request**; no real stock movement, customer alert, disposal, refund or regulator submission occurs.
8. **Reopen after evidence changes.** Switching from an older source snapshot to its actual update marks dependent decisions stale and requests renewed review. Prior history is preserved.

### Minimum screens/components

One incident workspace with (a) country/source/version controls, (b) camera/upload, (c) product-and-source evidence grid, (d) result/recapture panel, (e) explicit approval button, (f) audit drawer. Add a compact “How to test / Limits / Sample cases” entry. No multi-page administration console is required.

Accessibility requirements: keyboard-complete flow, visible focus, labelled controls, status conveyed in text/icons rather than colour alone, readable contrast, useful upload errors and mobile-friendly capture. English submission/UI is P0; a tested additional language is P1. Do not claim accessibility certification or language coverage without validation.

## 5. Decision semantics and essential data contracts

### Three user-facing result classes

| Internal result | Allowed presentation | Must not imply |
|---|---|---|
| `MATCHED_HOLD_FOR_REVIEW` | This product matches the stated restrictions in this checked notice. Review the evidence and approve a simulated hold. | A lab-confirmed contaminant or a regulator's new decision |
| `NOT_LISTED_IN_CHECKED_NOTICES` | The checked evidence did not list this identified product under these specific restrictions; show source coverage and dates. | Safe to eat, approved for sale, not recalled elsewhere or worldwide |
| `REVIEW_REQUIRED` | Missing, uncertain, conflicting, out-of-scope, stale or unavailable evidence prevents a supported conclusion. | A negative recall result |

Operational failures such as `SOURCE_UNAVAILABLE`, `MODEL_UNAVAILABLE` and `SOURCE_VERSION_CHANGED` are reason codes, not success states. Out-of-jurisdiction positive evidence is a review signal, not permission to transfer a foreign legal requirement or clear the product locally.

### Comparison rules

**Product identity precedes lot comparison.** Require a trustworthy identifier or a reviewed combination of brand/product/variant/size, not semantic similarity alone. A lot code is not globally unique. Do not silently equate regional brand aliases or product codes with GTINs.

Evaluate only predicates applicable to the relevant product record, source version and geographic scope. For a complete source, explicitly unrestricted dates can be represented as `ALL`; a date or lot not supplied as a restriction can be represented as `NOT_SPECIFIED` only after complete source review. A missing extraction or truncated source is `UNKNOWN`, never a wildcard. Preserve raw lot text, case and leading zeros unless an authority-backed normalization rule permits a change. Locale/date ambiguity routes to review.

A negative requires complete, verified identity and sufficient supported-source interpretation. When completeness is not established, fail to review. No untrusted text, model response or UI request can remove those checks. LLM confidence is not a calibrated probability of safety.

### Minimal records

| Record | Essential fields / constraints |
|---|---|
| `AuthorityNotice` | `source_id`, authority, jurisdiction scope, original/final URL, published/updated/retrieved times, source version/hash, historical/live mode, supported source format, interpretation-review state |
| `AffectedProductRule` | Parent notice/version; raw product name, reviewed identity attributes and typed identifiers; predicate set with `EXACT`, `SET`, `RANGE`, `ALL`, `NOT_SPECIFIED` or `UNKNOWN`; every condition carries evidence reference |
| `ProductObservation` | Incident/session ID; raw photo reference/hash, raw text when available; extracted fields with capture/evidence reference; model/prompt version; user corrections separately with timestamp |
| `VerificationResult` | Observed identity; checked notice versions; predicate outcomes `MATCH`, `MISMATCH`, `UNKNOWN`, `NOT_APPLICABLE`; result class, reason codes, supported explanation, outstanding evidence, verifier version |
| `ActionRecord` | Result and source-version IDs; action type, server-verified demo actor/session, deliberate approval timestamp, idempotency key, simulation flag, previous-action reference if re-reviewed |

Store append-only application events for review history with server-only writers. A hash and log do not automatically create a legally tamper-proof record. Do not claim blockchain, cryptographic non-repudiation or regulatory audit certification.

### Bounded tool contract

Tools may load an approved notice, extract/validate fields, retrieve eligible source records, run the verifier, request recapture, draft a supported explanation and record a simulated action **after server-side approval authorization**. The agent must not hold a general unrestricted HTTP, shell, database-write or messaging tool. Any read URL is allowlisted; any write is bound to the current incident/session.

Bound each normal run to roughly 2–4 model calls and six tool operations; at most two recapture turns. These are configurable design limits, not measured requirements of ADK. Start with low/medium thinking settings supported by the chosen model, then compare quality. Avoid long free-form hidden agent loops. Return useful failure/next-step messages rather than silently replaying a previous response.

## 6. Scope: P0, P1, P2 and explicit exclusions

### P0 — required acceptance scope

| ID | Requirement | Acceptance evidence |
|---|---|---|
| P0-01 | Two-authority, two-country corpus including JAPAC and non-JAPAC, and one real version pair | Source manifest, timestamps, rights notes and supported-coverage UI |
| P0-02 | Gemini source and label extraction with typed fields and evidence references | Saved redacted sample outputs; no hand-coded answer masquerading as inference |
| P0-03 | One bounded Google ADK workflow deployed on Cloud Run | Live trace and working Google Cloud endpoint |
| P0-04 | Product-level, scope-aware deterministic comparison | Unit tests and visible predicate grid |
| P0-05 | Targeted recapture and explicit unresolved status | At least one multi-turn deployed sample and failure case |
| P0-06 | Source-version invalidation and renewed review | Real UK notice update changes dependent review state |
| P0-07 | Deliberate, idempotent human-approved simulated action | Exactly one persisted action under repeated click/retry; refreshed page retains record |
| P0-08 | Isolated guest judge path and bounded resources | Two sessions cannot access or mutate each other's incident; no real personal data |
| P0-09 | Golden/held-out tests, source support and failure testing | Actual test report with commit/model/prompt/data IDs and denominators |
| P0-10 | Basic telemetry, error recovery and secret hygiene | Redacted traces, counts, source status, graceful 429/503 handling and secret scan |
| P0-11 | English deck, real video, public repo, live URL and test instructions | Anonymous external access check and artifact consistency |

### P1 — only after P0 passes

A genuinely linked multinational incident corpus; a second tested language; GS1/barcode decoding when the source supports equivalent identifiers; simple export of evidence/action record; optional stronger-model comparison; extra prompt screening; polished charts of measured results. Do not turn an optional language, plugin or managed service into a hidden release dependency.

### P2 — roadmap, not submission claims

Continuous global notice ingestion, authority-specific operational/legal adapters, entity-resolution validation, hybrid/vector/graph retrieval at justified scale, private supplier/POS/ERP integration, actual notifications and customer outreach, region-specific privacy controls, advanced observability, approved preference learning and paid product operations.

**Explicit exclusions:** medical/infant feeding advice; detecting contamination from a photograph; automatic stock release/disposal; regulatory compliance certification; global completeness guarantee; autonomous sending/payment/refund; arbitrary web ingestion; new ML training; multiple agent frameworks; a multi-agent swarm; Kubernetes/Temporal/platform engineering; generation of fake product-proof images; production identity/customer datasets; full enterprise architecture.

## 7. Technology decisions and deployment constraints

### Recommended minimal implementation

Use a small web UI and a Python service with **Google ADK + Gemini 3.8 Flash**, deploy the functional application on **Cloud Run**, and store domain incident/evidence/action records in **Firestore**. A simple frontend served by the same service avoids a second deployment. Use private Cloud Storage only if persistent image/source objects are necessary; otherwise minimise retained images. Use runtime service-account identity for Google APIs and Secret Manager for any unavoidable separate credential.

This is a conceptual boundary, not a detailed enterprise architecture. No claim is made that Firestore is an out-of-the-box persistent ADK session adapter. Persist the domain state explicitly and reconstruct bounded agent context; choose a documented compatible session mechanism if needed. Pin the tested ADK/SDK versions and avoid mixing 1.x/2.x event or state contracts. [S31][S32]

### Model and capability choices

`gemini-3.8-flash` is the default candidate for image/text extraction and tool orchestration. Its documented multimodal input does not imply image generation, speech output or Live API under that model ID. Validate available fields/settings and limits before coding against copied examples. [S27][S28]

`gemini-4-argon`, documented GA on 13 October 2026, is a legitimate optional challenger discovered in the updated research. Do not adopt it just because it is newer; compare the same held-out source/label cases, latency and cost before switching. Model access and quota have not been tested for either candidate. [S29]

Structured outputs constrain shape, not factual support; server checks and source-grounded evidence remain essential. For a small supported corpus, pass bounded full notices after metadata/lexical selection. Do not add embeddings, GraphRAG or reranking solely for a technology checklist. A graph-based corpus summarizer is not evidence of correct product-lot identity. [S33][S36]

### Regional and availability constraints

Cloud application location and model inference processing location are different decisions. The model documentation describes global/us/eu options; a Cloud Run service placed in Singapore or India does not establish that all model processing stays there. Use only public-source and synthetic demo data until privacy requirements are established. Record the chosen endpoint and processing disclosures. [S28][S29]

The Cloud Run deployment path needs active billing, necessary APIs, a build identity, a scoped runtime identity and permission to make the demo accessible. Check organization policies before assuming public invocation is permitted. Do not use broad project-owner credentials in the app or publish deploy commands containing secrets. [S32][S06, 27:16–28:13]

Scale-to-zero can reduce idle runtime cost but does not make all cloud services free. Keep the app accessible throughout evaluation and test cold-start behaviour. If needed and budget permits, a temporary minimum instance during recording is an operational option, not a required feature. Do not leave heavy managed resources running just to show a logo. [S06, 10:59–12:25; 22:47–24:42]

### Cost and latency hypotheses

The researched Cloud pricing table lists global Gemini 3.8 Flash rates of **$0.75 per million input tokens and $3.75 per million output/reasoning tokens through 31 December 2026**, with different non-global rates and later changes. Under those listed rates, a hypothetical total workflow using 12,000 input and 2,000 output/reasoning tokens would cost approximately **$0.0165 in model tokens**; 500 such workflows would be $8.25. This excludes retries, larger images/context, storage, build/runtime, logging, tax and other services. Actual usage must be measured. [S30]

Do not assume hackathon credits or approval to spend a particular amount. Gate 0 records an explicit project budget and quotas before load tests. A budget alert is not a hard cap: also bound calls, tokens, upload sizes, instances/concurrency and session rate limits in the application.

Targets: warm normal-flow p95 under 15 seconds; recapture turn under 10 seconds; useful progress indication within 1 second. Measure separately from cold-start latency and multi-turn human capture time. These targets can be revised against the actual source/image workload, but the README must report actual distributions and limitations rather than selecting only fastest runs.

## 8. Evaluation plan, baselines and acceptance criteria

### Ground truth and dataset discipline

Prepare **24 development cases and 8 held-out cases** with source versions, expected identity/predicates/result and reason codes. A human reviewer validates source interpretation. Separate fixture creation from prompt tuning where team capacity permits; if the same person performs both, disclose that limitation. Never describe model-generated expected answers as independently verified truth.

The eight held-out cases must not be used to optimise prompts before the first final evaluation. If failures are used to revise the system, they become development cases and a new held-out set is needed for a fresh held-out claim. Keep results from different commits and test suites separate; do not add overlapping passes into an inflated total.

| Case IDs | Required development scenarios |
|---|---|
| D01–D06 | SFA product A exact affected case; SFA product B exact affected case; UK named affected product; second UK product; explicit all-best-before scope; missing capture resolved into a supported match |
| D07–D12 | Same lot/different product; same brand/wrong variant; correct product/wrong lot; leading-zero/character near-miss; differing pack identity when material to the notice; a clearly excluded predicate from a fully reviewed source |
| D13–D18 | Unreadable lot; missing identity panel; ambiguous date format; incomplete source interpretation; unverified regional alias; recapture exhausted without adequate evidence |
| D19–D24 | Real UK update invalidates dependent checks; unknown extraction is not an ALL wildcard; prompt injection in input/source; model or source outage; duplicate approval/retry; cross-session action access attempt |

Ground truth for each case must be derived from the frozen reviewed notice plus explicitly marked synthetic observation changes. Do not force a “negative” label when the correct response is uncertainty. For example, a record outside a notice's geographic coverage may require review rather than reassuring local clearance.

Held-out H01–H08: two positive cases with unseen label layouts, two hard identity/predicate negatives, two ambiguous captures, one source-version dependency case, one adversarial/error-control case. This tests a supported small corpus, not generalization to all authorities or previously unseen outbreaks.

### Baselines

**Human baseline:** a person uses the same notices and package evidence, with a comparable action-recording task. Counterbalance order and report participants/tasks; do not compare an experienced AI-demo operator to an intentionally uninformed manual user.

**Competent one-shot baseline:** same Gemini model, same source evidence, reasonable structured-output instructions and an explicit request to abstain when uncertain, but no multi-step evidence acquisition or dependency-aware workflow. This isolates value from workflow rather than from different information access. An additional simple OCR/lot-only matcher is an explanatory ablation, not the main benchmark.

### Minimum release evidence

| Metric / assertion | Gate / reporting requirement |
|---|---|
| Critical false reassurance | **Zero observed cases** where an affected, unknown, stale or unsupported result is presented as safe/released/not-recalled-worldwide; report denominator and tests. Zero observed does not imply zero real-world risk. |
| Predicate and identity correctness | All deterministic comparison invariants pass on the frozen gold data; list extraction disagreements separately. |
| Useful decision coverage | At least 10 of 12 genuinely decidable development product cases resolve correctly without manually replacing the entire AI extraction. Report recapture use and abstentions. Abstain-on-everything is not success. |
| Evidence support | Every material result field has a valid cited notice/observation reference; no fabricated source/quote. Small supported corpus should be fully manually audited. |
| Version safety | Updated notice invalidates every dependent completed result, including stale historical negatives; no unreviewed source update silently inherits approval. |
| Approval/authorization | No action without deliberate server-validated approval; duplicate requests create one action; no cross-session read/write. |
| Resilience | Timeout/429/503/source-fetch failure returns a useful explicit failure/review state; never false success. |
| Held-out suite | Execute all 8 once under the frozen release configuration, publish failures as well as passes; critical errors block release. |
| E2E usability | Four hero flows work from the deployed URL in a clean session; keyboard and mobile-capture checks pass; refresh preserves domain state. |
| Performance and cost | Report per-run tokens, model calls, warm p50/p95, cold latency separately, sample count, configuration and concurrency. |
| Actual impact comparison | Report measured time-to-correct-documented-decision and error counts; missing user study is an explicit limitation, not fabricated benefit. |

ADK trajectory/response evaluation can support the report, but a language-model judge is secondary to source truth and deterministic permission/predicate tests. Do not gate on exact natural-language wording or assume every legitimate workflow has one identical tool-call sequence. RAG context precision/recall becomes meaningful only with labelled retrieval targets; avoid decorative percentages. [S34]

### Impact hypothesis

A reasonable **target**, not an achievement, is at least 30% lower median time to a correct documented triage decision without increased critical errors in a bounded comparison. Measure user effort including photograph recapture and source review. Report raw times and participants; a tiny synthetic task study cannot support a population health claim, market adoption estimate or global error rate.

## 9. Safety, privacy and reliability constraints

Separate untrusted source/photo text from executable instructions. Allowlist source domains and fetch paths; block private-network/file URLs, unsafe redirects and arbitrary document fetches. Enforce file type/size/count and total context limits. Scan and redact secrets; never place raw API keys, service-account files or personal data in code, screenshots, videos or logs.

Judge access should be easy but bounded. Create isolated short-lived guest sessions and synthetic incidents; use server-authorized write capabilities, not publicly writable Firestore rules. Enforce session ownership on every read/write. Keep the read-only curated source corpus separate from per-visitor records. Do not assume the public link will be visited only by judges.

Retain the minimum images and observation metadata needed for demo evaluation. Strip unnecessary EXIF/location metadata. Do not collect names, addresses, faces or real business/customer records for P0. Configure retention/deletion and document that background deletion mechanisms may not be instantaneous. Private records and prior runs are not a globally visible training dataset.

Use bounded retries with backoff/jitter for transient read/model failures; never repeatedly retry unauthorized requests. Human-approved writes require idempotency keys and version checks. Cache keys must include source hash/version, observation hash, model, prompt and verifier version. A cached result must retain its computation time; refreshing a source invalidates dependent cache entries.

Keep source and action history, model/prompt versions and error classes in redacted logs. Publish a simple operational status and supported limits. After the deadline, retain a release tag, document critical fixes and avoid feature changes or migrations that make the judged application unavailable. No operational tasks are running from this strategy session.

### Controlled improvement loop

Observe failures → diagnose with evidence → propose a prompt/retrieval/rule correction → evaluate on a versioned dataset → approve the change → release → monitor → roll back if regressions appear. Feedback collection is not retraining. No automatic model training, unconstrained memory updates or self-modification is part of P0.

## 10. Build feasibility, sequencing and hard gates

### Planning assumptions

Assume two active builders, with evidence/QA and presentation support in parallel. The team is formed, but actual contributor availability and cloud readiness are not established. Estimate **32–48 person-hours**, with approximately **14–22 hours of critical-path elapsed work** under favourable access conditions. One builder starting from a blank account materially weakens feasibility. These estimates are for the engineering team, not a promise of background work by this assistant.

| Workstream | Indicative person-hours | Main output |
|---|---:|---|
| Rule/account preflight and source manifest | 3–5 | Verified cutoff, access, allowed source scope |
| Core agent, extraction, verifier and persistence | 10–15 | Real end-to-end service and tested contracts |
| Incident UI, capture, evidence and approval | 6–9 | Judge-ready product workflow |
| Evals, safety, integration and deployment checks | 7–10 | Redacted test report and usable cloud URL |
| Deck, recording, README and submission review | 6–9 | Matching submission artifacts |

Ranges are not additive promises of exact completion; their endpoints total 32–48. Protect the final **4–6 hours of the verified submission window** for integration, real external checks, video, documentation and upload. Do not assume a late-night cutoff before confirming it.

### Delivery gates

| Gate | Must establish | If it fails |
|---|---|---|
| G0 — Before feature coding | Exact official cutoff/timezone/form fields; roster eligibility; active capacity; approved spend; model call and minimal Cloud Run endpoint; Firestore write/read | Fix common infrastructure/rule issue or declare shared blocker. Do not pretend a product pivot solves it. |
| G1 — First vertical slice | One source and photo produce traceable fields; safe verifier and server-side approval persist a simulated action | Simplify UI/tool flow; reject unsupported source format; no visual-only success. |
| G2 — Differentiator and global core | Second authority works; missing-evidence recovery; real version change invalidates results; competent baseline comparison possible | Drop P1; assess recall-specific fallback only before major investment and while fallback still fits. |
| G3 — Feature freeze | Full P0, critical invariants, held-out execution, outside-session access, secret hygiene and budget controls | Fix critical defects; no new features. If safety/core cannot pass, no-go for claiming completed primary. |
| G4 — Submission | Real app, public repo, correct video, deck, guide and form all accessible and consistent; submission receipt saved | Resolve packaging/access only; do not start a different product. |
| G5 — Evaluation support | Endpoint/dependencies accessible through results, redacted monitoring, critical repair process | Restore same URL; document fixes without adding unsubmitted features. |

### Fallback definition

**FormBridge AI**, Sustainability & Social Impact: two short permitted forms with instructions, synthetic user answers, Gemini source-linked explanation, missing/inconsistent-field checks, keyboard-accessible flow and reviewed completeness export. No benefits/legal/financial eligibility adjudication and no autonomous submission. Be My Eyes, Jotform, Acrobat and Docassemble are existing comparators; novelty remains limited. [S16][S17][S18][S23]

Switch only for a **recall-specific** unresolved blocker: inability to obtain usable permitted evidence, inability to demonstrate reliable source-scoped verification, or a decisive differentiation failure. Re-estimate the remaining time against the fallback's estimated 24–36 person-hours before switching. Do not build both products in parallel. Shared model/cloud outage, team eligibility or expired deadline requires shared remediation/no-go, not FormBridge.

## 11. Demonstration, pitch and submission package

### Duration decision

Default main video **3:20**, based on the written 3–4-minute terms and later organizer host. Also retain a **2:40** edit satisfying the original under-three-minute request and conflicting FAQ. No single duration satisfies both. Record the authority for the final upload choice; do not assume exactly 3:00 resolves “under 3”. [S03][S04][S06, 4:32–4:56]

### Main storyboard

| Timeline | Content |
|---|---|
| 0:00–0:20 | Open the live product and the concrete same-lot/different-product problem. |
| 0:20–0:45 | Display source authority, scope/version and actual Gemini extraction. |
| 0:45–1:20 | Run a supported match and a wrong-product near-miss; show predicate evidence. |
| 1:20–1:45 | Demonstrate targeted recapture instead of guessing. |
| 1:45–2:15 | Apply the genuine UK source update; reopen dependent checks without cross-border legal inference. |
| 2:15–2:40 | Approve a simulated hold; show its persisted evidence/action record. |
| 2:40–3:05 | Show actual test counts, baseline observations and compact Google stack/trace. |
| 3:05–3:20 | State global ambition, two-source-country coverage and limits. |

The 2:40 alternate compresses the source introduction and technical explanation while retaining the match, uncertainty, update and action. Use clear narration/captions, legible identifiers and little navigation. No on-camera presenter is necessary. Generated voice/polish may assist presentation, but every demonstrated app capability must exist. Any replay must be visibly identified; never call a prerecorded result a live model response. [S06, 29:46–34:30; 39:23–40:40]

### Approximately 30-second pitch

A recall notice does not tell a retail worker whether the packet in their hand matches every affected condition. BatchBeacon links official evidence to product photographs. Gemini interprets the source and label; a verifier checks identity, batch, dates and scope. Missing evidence triggers a specific follow-up rather than a guess. Updated notices reopen earlier checks, and the manager approves each action. We start with two jurisdictions and a reusable core—not a claim of worldwide coverage.

### Approximately one-minute technical explanation

A single bounded Google ADK workflow runs on Cloud Run. Gemini extracts source-backed fields from selected official notices and package photographs. Each condition keeps its source, jurisdiction and version. A deterministic verifier checks applicability and product predicates, while unknown or conflicting evidence triggers recapture or review. Firestore stores the incident and an idempotent human-approved simulated action. Notice updates invalidate dependent results. We test matches, dangerous near-misses, missing fields, scope changes, prompt injection, outages and approval boundaries against labelled fixtures and a competent one-shot baseline. The corpus is small and explicitly dated; we do not claim contamination detection, regulatory clearance or exhaustive global monitoring.

### Three likely judge questions and response boundaries

**Is this new?** Recall software already exists. Show the evidence/scope/version/physical-product combination and its measured hard-case advantage; do not claim every component is novel. **Does a negative mean safe?** No—only the stated checked scope, with unknowns and relevant foreign evidence requiring review. **Why agents and Google AI?** Multimodal interpretation plus targeted follow-up benefits from Gemini/ADK; deterministic comparison and approval remain outside generated reasoning. More services would not automatically improve the product.

### Deliverables the implementation session must create

| Artifact | Required contents |
|---|---|
| Public source repository | Fresh event-built code, dependency/asset provenance, setup instructions, tested model/SDK configuration, no credentials, deadline tag |
| README and judge guide | Product and limits; direct Cloud Run URL; guest flow; sample inputs/expected high-level outcomes; historical/live source labels; supported countries/formats; failure instructions |
| Evidence/evaluation manifest | Source URLs/versions, synthetic labels, gold/held-out boundaries, actual run metadata and results, model/prompt/verifier/commit IDs |
| English deck exported as PDF | Suggested 7–8 slides: problem, user, product flow, differentiator/competitors, Google implementation, actual evals, global/adoption path, limitations/links |
| Real product video | Correct final duration, readable evidence, genuine actions, audible narration, no secrets |
| Deployed app | Functional Google Cloud URL with bounded judge access and dependencies live throughout evaluation |
| Submission form and receipt | Correct theme, description, required files/links, successful submission confirmation and deadline revision recorded |

These are requirements, not artifacts already produced by this strategy review. The exact form may impose additional fields/limits; G0 must verify them.

## 12. Final acceptance checklist

- [ ] Deadline/timezone and video-duration authority recorded; all roster eligibility conditions checked.
- [ ] Cloud Run URL works outside the builder's authenticated session; billing, quota and database tested.
- [ ] Both supported jurisdictions and the real source-version pair function through one evidence schema.
- [ ] Product identity, exact identifiers, date/scope semantics and unknown fields behave as specified.
- [ ] Every material conclusion has source/observation provenance; no global safety or invented impact claims.
- [ ] Recapture, source-update invalidation, deliberate approval and idempotent action persist correctly.
- [ ] Twenty-four development and eight held-out cases are executed and reported without inventing or double-counting passes.
- [ ] Critical false reassurance, unauthorized writes and cross-session data access are absent in the tested suite.
- [ ] A competent baseline comparison exists, or its absence is explicitly disclosed and the innovation claim reduced.
- [ ] All synthetic/historical material is visibly labelled; permissions/provenance for included assets are recorded.
- [ ] Secret scan covers repo history, screenshots, logs, deck and video; resource limits and retention are configured.
- [ ] Repo, video, deck, app and description match the same tested release and are judge-accessible.
- [ ] Submission receipt and maintenance/runbook ownership are recorded; no reliance on an extension.

## 13. Unresolved decisions and immediate implementation instructions

**Unresolved:** exact cutoff/timezone; any latest authenticated announcement overriding duration; detailed asset-reuse interpretation where relevant; final roster eligibility; active engineering capacity; cloud project/permissions/budget/quota; actual SDK/model preflight; source redistribution permissions; all product performance and adoption evidence. None has been silently treated as passed.

**Next implementation session:** Read this file first. Execute G0 without starting a large architecture exercise. Discover the actual workspace and Google project from the user's environment; do not invent IDs, credentials or deployed URLs. Create a fresh event repository after access/policy checks. Freeze the small evidence manifest, build the first complete source-to-photo-to-human-action vertical slice, then add the second authority and real version change. Implement tests alongside the verifier, keep the guest demo simple, and protect the packaging buffer. Report each gate as PASS, FAIL or UNVERIFIED with concrete evidence. Do not announce completion while core acceptance checks are unrun.

**Final decision:** CONDITIONAL GO — BatchBeacon AI. The selected problem, global direction and minimum proof are fixed for implementation. Passing the gates can establish a valid, credible submission; it cannot establish a near-certain chance of winning.

## Source register

Public sources were reviewed on 17 October 2026. Transcript citations refer to the supplied complete text, not independently watched visuals. Published vendor capabilities are claims, not measured comparisons.

- **S01 — Official competition homepage and roadmap.** https://aibuildercup.com/. Read 17 October 2026; date-level timeline, not authenticated cutoff.
- **S02 — Official themes and judging criteria.** https://aibuildercup.com/themes.html. Read 17 October 2026; six themes; conflicting legacy submission wording noted.
- **S03 — Official FAQ.** https://aibuildercup.com/Faqs.html. Read 17 October 2026; under-three-minute wording conflicts with terms.
- **S04 — Competition terms linked by official site.** https://docs.google.com/document/d/e/2PACX-1vRm7ChZ6Ij9fG7uFDkxzUMpwgVeBmnQ6cMDnAIEEX84AiLBOOQ9cYbl3S5OzFBbcVb8TF55s-eVpiXb/pub. Read 17 October 2026; contractual text, including precedence and IP provisions.
- **S05 — Introductory session, supplied transcript.** https://www.youtube.com/live/mhDd6qSBMg4. User attachment Pasted text(1).txt, approximately 00:00–47:10. Transcript read in full; video visuals not independently watched.
- **S06 — Ask the Expert session, supplied transcript.** https://www.youtube.com/live/_75UeGNj1GY. User attachment Pasted text (2).txt, approximately 00:23–53:03. Transcript read in full; video visuals not independently watched.
- **S07 — WHO: infant formula cereulide contamination, international.** https://www.who.int/emergencies/disease-outbreak-news/item/2026-DON596. 13 March 2026 report; describes historical incident, with situation information as of 25 February. Not an October live-alert feed.
- **S08 — SFA: raw-milk cheese recall.** https://www.sfa.gov.sg/news-publications/newsroom/recall-of-raw-milk-cheese-products-due-to-potential-presence-of-shiga-toxin-producing-escherichia-coli. 9 October 2026; two named 250 g products, lot 232511, best-before 17 October 2026.
- **S09 — UK FSA: original Alyan chocolate recall.** https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026. 24 September 2026 notice; read alongside its update, not treated as the current version.
- **S10 — UK FSA: updated Alyan chocolate recall.** https://alerts.food.gov.uk/news-alerts/alert/FSA-PRIN-47-2026-update-1. 25 September 2026; extends coverage to Wales and Scotland; explicit all-best-before-dates scope.
- **S11 — FDA openFDA food enforcement documentation.** https://open.fda.gov/apis/food/enforcement/. Weekly archive; documentation warns against use as a public alert service or recall-lifecycle tracker.
- **S12 — FSANZ food recall index.** https://www.foodstandards.gov.au/food-recalls. Public index reviewed. No Australian infant-formula fixture was verified in this final pass.
- **S13 — Batch’d product site.** https://www.batchdapp.com/. Vendor descriptions and interface examples, not independently benchmarked capabilities.
- **S14 — Smart Food Safe: Smart Recall.** https://smartfoodsafe.com/smart-recall/. Vendor descriptions, not independently benchmarked capabilities.
- **S15 — SuperRecall.ai.** https://superrecall.ai/. Vendor claims, including international monitoring and human-reviewed workflows; illustrated interface is not a tested service result.
- **S16 — Be My Eyes Workplace AI documentation.** https://support.bemyeyes.com/hc/en-us/articles/44022053126673-Workplace-AI-Describe-your-screen-files-and-images. Updated 27 August 2026; documents screen, document and form assistance.
- **S17 — Jotform AI.** https://www.jotform.com/ai/. Vendor AI form-building and assistance overview; no product trial performed.
- **S18 — Adobe Acrobat AI Assistant.** https://www.adobe.com/acrobat/generative-ai-pdf.html. Vendor document assistance and citation capabilities; adjacent, not identical to FormBridge.
- **S23 — Docassemble.** https://docassemble.org/. Open-source guided-interview and document-assembly prior art; not adopted as a dependency.
- **S27 — Gemini 3.8 Flash model documentation.** https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash. Read 17 October 2026; stable model ID, multimodal inputs, text output, structured output and function calling.
- **S28 — Gemini 3.8 Flash on Google Cloud.** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash. Read 17 October 2026; model lifecycle, serving locations and capabilities. Account access is untested.
- **S29 — Gemini 4 Argon on Google Cloud.** https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-argon. GA release dated 13 October 2026. Evaluated as an optional challenger, not assumed to improve this task.
- **S30 — Google Cloud generative AI pricing.** https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing. Read 17 October 2026; distinguish global/non-global rates, model variants, promotions and future rate changes.
- **S31 — Google ADK 2.0 documentation.** https://adk.dev/2.0/. Read 17 October 2026; workflow/state and migration guidance. Pin a tested release; do not mix 1.x and 2.x assumptions.
- **S32 — Official Python ADK deployment to Cloud Run.** https://docs.cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-adk-service. Read 17 October 2026; runtime/deployment example, not proof this team has billing, IAM or quota.
- **S33 — Gemini structured outputs.** https://ai.google.dev/gemini-api/docs/structured-output. Schema-constrained generation documentation. Application-level correctness must still be checked.
- **S34 — ADK evaluation documentation.** https://adk.dev/evaluate/. Trajectory/tool-use and response evaluation; choose version-compatible metrics, not exact generated wording as truth.
- **S36 — GraphRAG research paper.** https://arxiv.org/abs/2404.16130. From Local to Global: A Graph RAG Approach to Query-Focused Summarization. Research scope does not establish product-lot matching accuracy.
- **S38 — User original research mandate and supplied six challenge statements.** Pasted text.txt plus six full challenge statements supplied in this conversation. Governs requested output structure; not independent evidence of competition rules.
- **S39 — Authenticated dashboard verification attempt.** Browser.list_tabs attempted 17 October 2026; failed because originating connected-browser context was unavailable. Exact cutoff, latest announcements and form validations remain unverified.

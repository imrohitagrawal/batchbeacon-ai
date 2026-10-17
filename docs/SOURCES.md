# BatchBeacon source and decision register

Prepared 17 October 2026. This file distinguishes supplied research, fresh read-only observations, proposed implementation decisions and unresolved authority. No application/model/cloud validation is implied.

## 1. Preserved inputs

| Canonical file | Source and SHA-256 |
| --- | --- |
| [HACKATHON_BRIEF.md](../HACKATHON_BRIEF.md) | Unchanged bytes from uploaded `HACKATHON_BRIEF(2).md`, Edition 1.0: `4643b9c2753899d0c4a8f48fa68b547af86ec2a897d38fae19aa8b726e77727e` |
| [HACKATHON_CODEX_MASTER_PROMPT.md](../HACKATHON_CODEX_MASTER_PROMPT.md) | Unchanged uploaded operating contract: `bc3b8ec0a6442b2f5164ed6ffcd986ed7d06329b07e0d5af17dd9f62eff5be72` |

Both were read completely, including the brief's contracts, technology, evaluation and safety sections. Original S01–S39 citations remain in the brief; do not renumber them. The research companion and original transcript attachments are not included in this handoff. Their relevant conclusions are inherited from the approved self-contained brief; this session did not independently watch the videos or read those missing transcripts.

The present owner request fixes BatchBeacon AI / `batchbeacon-ai`, asks for planning-only artifacts and actual available specialist reviews, excludes unfinished StackClimb work/orchestration dependencies, retains three UI choices and selection, and requires local capability verification before implementation. Those instructions are encoded in this package so no chat history is needed.

The later owner instructions are preserved for execution in [OWNER_DECISIONS](OWNER_DECISIONS.md): approved 160/230-second videos, A workflow with rejected old visuals, one owner/Codex/one machine, existing-project report, two separate dashboards, bounded learning, finite delegated budget, cloud/public/GitHub grants and owner-attested roster. Personal timing is intentionally excluded from public artifacts and belongs only in ignored local run configuration. These instructions supersede the corresponding earlier proposals without altering the original documents.

## 2. Fresh consequential observations

All sources below were accessed on 17 October 2026. Public-document verification proves documentation content, not account access, installed compatibility or successful service operation.

| ID | Source | Observation and consequence |
| --- | --- | --- |
| X01 | [Authenticated prototype form](https://hack2skill.com/event/aibuildercup2026/dashboard/submissions/6a5da99a444e4f43e5657a85) | Browser read succeeded. Ending field: **18 October 2026, 11:59:00 PM IST**, equivalent to **18:29:00 UTC**. Required fields cover theme, deployment URL, PDF deck, public GitHub URL, 3–4-minute video URL and description. PDF upload limit is 5 MB; description counter permits 1,024 characters. Prescribed deck template is mandatory. App/dependencies and repository must remain accessible through evaluation. No fields were edited or submitted. |
| X02 | [Prescribed template, read-only HTML view](https://docs.google.com/presentation/u/0/d/13rg7vW43mEH6DkpuusAE6fdoEylSFz8waNpE4RLzoUg/htmlpresent) | All 16 slide regions were read in the connected browser. The template asks participants to download a PPTX and edit locally; no request for shared editing is needed. Internal sections are mapped below. Its links slide says three minutes, which does not resolve X01 versus the master/FAQ. No shared Slides file was changed/copied. |
| X03 | [Competition homepage](https://aibuildercup.com/) | Public date remains 18 October. Published evaluation is 19 October–6 November, finalists 7 November. Exact cutoff is established by X01 rather than an inferred countdown. |
| X04 | [Official FAQ](https://aibuildercup.com/Faqs.html) | Still says under-three-minute video; public source, deployed prototype and deck. It retains the 40/25/25/10 rubric, fresh-project and team eligibility conditions. This conflicts with X01 on duration. |
| X05 | [Linked competition terms](https://docs.google.com/document/d/e/2PACX-1vRm7ChZ6Ij9fG7uFDkxzUMpwgVeBmnQ6cMDnAIEEX84AiLBOOQ9cYbl3S5OzFBbcVb8TF55s-eVpiXb/pub) | Earlier retrieval attempts failed; on the later 17 October follow-up a specialist and integrator successfully read all 104 rendered lines. Terms require Google Cloud, fresh code/assets, public source/live URL and a 3–4-minute video, and take precedence over conflicting promotion. No explicit hosting region or guest-data retention duration was found. Consequential six-month first-refusal and promotional rights are present; this is source inspection, not owner acceptance or legal certification. See DEC-14. |
| X06 | [Gemini 3.8 Flash documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) and [Cloud model page](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash) | Named candidate exists in current documentation. Multimodal input, structured output and function calling are documented; `minimal` thinking is not supported on the model page. Pin/test actual settings and endpoint locally; no quota/access claim. |
| X07 | [ADK 2.0 guidance](https://adk.dev/2.0/) | Current guidance distinguishes workflow/event/session contracts from 1.x and documents automatic retry behavior. Do not mix copied 1.x examples with a 2.x runtime or multiply retries. Exact dependency resolution remains unexecuted. |
| X08 | [Official Codex CLI](https://learn.chatgpt.com/docs/codex/cli) and [command reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli) | Opening a project directory and running `codex` is documented. No special model/permission flag is needed for the launch instruction. `command -v codex` found no executable in the planning container; this says nothing about the owner's machine. Verify locally, without global installation or trust overrides. |
| X09 | [Firestore documentation](https://firebase.google.com/docs/firestore) and [transactions](https://firebase.google.com/docs/firestore/manage-data/transactions) | Firestore is documented within Firebase and supports server development. The architecture can truthfully describe Firebase/Cloud Firestore persistence. Transaction retries require pure retry-safe callbacks; real tests remain mandatory. Organizer intent beyond this service mapping is not established by vendor docs. |

Authenticated-source evidence here is a sanitized transcription of relevant visible fields, not a public copy of personal dashboard contents. Browser screenshots, account identifiers, roster contact details and authentication state are deliberately absent from the package. No source content hash was captured for those live UI views; later verification should record its own observation time and any changed field.

## 3. Conflict and decision register

| ID | Conflict / missing decision | Execution treatment and affected gate |
| --- | --- | --- |
| DEC-01 | Brief defaults to 3:20; master requires <180 seconds; X01 mandates 3–4 minutes; X04 says <3; X02 says 3. | **Resolved owner decision U01, 17 October:** use **160-second (2:40) core + 230-second (3:50) submission cut**. The owner explicitly accepts this operating-contract exception. Preserve source wording and unchanged originals; recheck actual form/export before submission. OWNER-VIDEO is satisfied for this duration, not final submission or a subsequently changed rule. |
| DEC-02 | Brief G0 demands cloud/model/database proof before feature coding; current owner/master allow independent local work while permission decisions are pending. | Explicit sequencing reconciliation: G0-L covers workspace/requirements/safe local preparation; G0-X covers authorized real services. Local contracts/domain work/provisional UI may proceed after G0-L. G0-X stays BLOCKED/NOT RUN until proven and remains required before a hosted-slice pass. No cloud gate is waived. |
| DEC-03 | Brief suggests 7–8 deck slides; X01 mandates the template. | Use X02's template slots and original template styling/structure. The brief's outline supplies content only. Do not replace the official deck with an unrelated 8-slide deck. Optional/instruction/blank slides are identified below; verify final required treatment before export. |
| DEC-04 | Form wording lists Firebase, Firestore, Cloud Run and Gemini. | Describe Firebase/Cloud Firestore for persisted incidents/actions, Cloud Run for the app, Gemini for inference, and ADK for bounded workflow. Do not claim Firebase Auth/Hosting is implemented. If current announcements explicitly require a separate Firebase capability, record the requirement and assess before adding it. This is an organizer-intent assumption, not verified extra-service eligibility. |
| DEC-05 | Freshness, denominator, recapture scope and transaction races lack executable detail in the brief. | [MVP](../specs/mvp.md) adds proposed engineering rules: historical default; bounded live freshness; incident-scoped recaptures; frozen 12-case denominator; source/observation/result revision checks; cross-instance limits. These are prototype policies, not source facts or measured results. |
| DEC-06 | Brief includes FormBridge fallback; owner fixes the approved product. | Simplify BatchBeacon's implementation and drop P1 first. Any product pivot needs an explicit new owner decision, a recall-specific failed gate and a fresh time estimate. No automatic fallback implementation. |
| DEC-07 | Generic master allows direct SDK alternatives; approved P0 explicitly requires ADK. | Direct SDK is diagnostic only unless the owner approves a scope change. Preserve Gemini + one ADK workflow + Cloud Run + Firestore in P0. |
| DEC-08 | Existing source research is not a runnable, rights-reviewed corpus. | M1 custodian creates the manifest/fixtures and reviews publisher rights. Reuse exact known URLs/identifiers; no invented source facts, GTINs or current global coverage. Licensing uncertainty blocks only copying/redistribution that depends on it. |
| DEC-09 | Team formation/leader role does not establish individual eligibility; actual coding capacity was previously unknown. | U03/U05 establish one human executor/owner with Codex on one machine. U14 supplies the four-person roster and captain eligibility attestation; preserve it as owner-attested. Verify registered names without changing a closed roster. Concrete final candidate/material-terms approval remains later. Planning reviewers are not extra human builders. |
| DEC-10 | A persisted capture hash alone cannot substantiate image evidence after refresh. | Select short-lived private Cloud Storage for sanitized model-input images, as expressly permitted by brief §7 when needed. Include it in cloud/budget approval, enforce session access/expiry and verify actual deletion behavior. Memory-only local development remains possible but cannot pass the retained-image evidence gate. |
| DEC-11 | Historical effort bands and the earlier two-builder forecast do not match actual owner availability. | U03 supersedes the two-builder elapsed forecast. Retain 31–66 person-hours only as historical effort context; use EXECUTION_POLICY setup/finite-goal/resume boundaries, fixed freeze, a native continuation canary and forecasts from observed integrated progress. Actual personal timing stays private. No P0 or safety waiver. |
| DEC-12 | Earlier OPS proposal deferred a customer console/learning loop; owner now explicitly requires both surfaces and learning. | U07 adds P0-12/13 AC-32–43 and OPS-01–07. One synthetic shop per guest; bounded real guidance adaptation and rollback. Preserve P0-01–11 and all original evaluation denominators. Added effort is a deadline risk, not permission to relabel logging as learning. |
| DEC-13 | Money, region and remote/public scope were previously unresolved. | U09–U12 adopt OPERATIONS' ₹6,000 finite envelope, selected Mumbai app/data plus global model endpoint, retention and target `imrohitagrawal/batchbeacon-ai`. Discover actual IDs/permissions; approvals do not imply successful configuration. |
| DEC-14 | Newly accessible terms corroborate 3–4 minutes, but retain a strict fresh-code rule and broader copyright wording about permitted existing works. | Keep 160/230-second owner-approved cuts and fresh event-built product. Review dependency/asset rights; do not copy previous products or treat broader copyright language as a freshness exception. Terms include consequential IP/promotional provisions; final owner approval reviews the actual current terms. No automatic ownership-transfer claim or silent acceptance. |

New execution decisions go in `docs/DECISIONS.md`, created conservatively by Codex after workspace inspection. Reference DEC IDs here rather than rewriting supplied documents.

## 4. Official deck mapping

This maps the inspected template; it is not a deck already produced. Use an authorized downloaded working copy. Keep all content slots accounted for, use current verified artifacts, and avoid changing the organizer's shared original.

| Template slide | BatchBeacon content |
| --- | --- |
| 1 | Actual team, captain and Retail & Commerce challenge; product name separately. |
| 2 | Download/edit instruction page; inspect whether removed from final export. Do not treat it as a content slide. |
| 3 | Retail worker problem and source → photo → reviewable action outcome. |
| 4 | Competitor-aware differentiation: identity, uncertainty recovery and source-change behavior. Label hypotheses versus measured evidence. |
| 5 | P0 features with actual capability status. |
| 6 | Primary user/state flow with human approval and error paths. |
| 7 | Optional design slot; use the selected design or actual UI, not three unapproved directions as delivered functionality. |
| 8 | Actual one-service architecture and trust/data boundaries. |
| 9 | Verified Google stack and each service's real responsibility. |
| 10 | Optional cost slot; measured usage plus explicit non-model uncertainty. |
| 11 | Real prototype screenshots of evidence, recapture and update. |
| 12 | Actual denominators, failures, scoped quality, latency/cost and baseline results/limitations. |
| 13 | B0–B3 future scope, clearly separated from the release. |
| 14 | Public repository, final approved video and deployed product links. Record the video wording conflict. |
| 15–16 | Decorative/closing regions with no additional text requirements exposed in HTML. Visually inspect the downloaded template before removing or filling them. |

Use a conservative final PDF target below 4,900,000 bytes to fit either common interpretation of the 5 MB limit. Validate readability and clickable links. Limit the final description to 1,024 characters as measured by the real form; target below the limit rather than depending on ambiguous Unicode counting.

## 5. Research reuse and remaining verification

Reuse brief S08–S10 for corpus facts, S13–S15 for disclosed vendor claims, S05/S06 for inherited session guidance, and S27–S34 for the technology starting point. Do not rerun the six-theme contest or claim hands-on competitor benchmarks. WHO S07 is contextual historical material only. Prices and regional/account behavior must be checked when configuring paid execution; the brief's cost example is not a budget grant.

Local verification still owns actual Codex/runtimes, instruction discovery, Git status/remotes, capabilities, skill admission, model/SDK settings, credentials, IAM, quota, billing, region, Firestore semantics, source rights/completeness, live source status and every product result. Recheck changed/time-sensitive form fields near submission. No automation or operational monitor was started in this planning session.

## 6. Consequential follow-up research, 17 October 2026

This was public-document research and read-only specialist analysis, not local/runtime validation.

| ID | Source / finding | Consequence |
| --- | --- | --- |
| X10 | [Codex long-running work](https://learn.chatgpt.com/docs/long-running-work), [permissions](https://learn.chatgpt.com/docs/permission-modes), [auto-review](https://learn.chatgpt.com/docs/sandboxing/auto-review) | Native goals and scoped approval review are documented; verify local availability. No guarantee of uninterrupted overnight work. |
| X11 | [Codex noninteractive mode](https://learn.chatgpt.com/docs/non-interactive-mode) | `--full-auto` is no longer supported in current docs. Resolve commands against actual client help. |
| X12 | [Claude project memory](https://code.claude.com/docs/en/memory), [Gemini context files](https://geminicli.com/docs/cli/gemini-md/) | Client loading/imports differ; use shared AGENTS and small version-checked adapters when needed. See INDEX. |
| X13 | [Current Impeccable main skill](https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md), [Emil design engineering](https://github.com/emilkowalski/skills/blob/main/skills/emil-design-eng/SKILL.md) | Canonical paths/content researched. No install, local discovery, invocation or UI application. See TOOLING for exact evidence limits. |
| X14 | [Carbon tables](https://carbondesignsystem.com/components/data-table/usage/), [Cloudscape split view](https://cloudscape.design/patterns/resource-management/view/split-view/), [GOV.UK review](https://design-system.service.gov.uk/patterns/check-answers/) | Support visible comparisons, contextual supplementary history and correction before confirmation. These pattern references inform the A replacement; they do not prove a best-in-market design. |
| X15 | [Google service spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps) | Supplement ordinary alerts/application limits where supported; no universal instantaneous project cap. |
| X16 | [Storage lifecycle](https://docs.cloud.google.com/storage/docs/lifecycle), [Firestore TTL](https://docs.cloud.google.com/firestore/native/docs/ttl) | Clarify access expiry versus live-object deletion, soft deletion and child-record cleanup. NF-02/OPERATIONS preserve actual retention uncertainty. |
| X17 | [Cloud Run source deployment](https://docs.cloud.google.com/run/docs/deploying-source-code), [monitoring](https://docs.cloud.google.com/run/docs/monitoring), [logging](https://docs.cloud.google.com/run/docs/logging) | Minimal proposed setup/identities and native operations dashboard are in OPERATIONS. No cloud account or notification was accessed. |

The FAQ was reread for eligibility. Earlier linked-terms failures are superseded by the successful complete X05 inspection; U14 records the owner’s eligibility attestation. Final material-terms/candidate approval remains distinct. The follow-up specialists were real subagents; their scopes, actual findings and limitations are retained in the review records.

## 7. Authorization and scope follow-up sources

| ID | Primary source / observation | Consequence |
| --- | --- | --- |
| X18 | [Google model pricing](https://cloud.google.com/vertex-ai/generative-ai/pricing), [Cloud Run](https://cloud.google.com/run/pricing), [Observability](https://cloud.google.com/products/observability/pricing), [model locations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash) | Current pricing/endpoint checks underpin the finite budget; amounts, workload bounds and ₹100/USD conversion are engineering planning assumptions. Actual billing SKUs/account limits remain local checks. No paid call. |
| X19 | [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Impeccable README](https://github.com/pbakaus/impeccable/blob/main/README.md), [Emil entry point](https://github.com/emilkowalski/skills/blob/main/skills/emil-design-eng/SKILL.md) | Selected skills need stage-specific admission, project-local discovery and actual application. Default installer/hooks/binary/network behavior is not automatically approved. Pins and sequence in TOOLING. |
| X20 | Connected GitHub read of [target repository](https://github.com/imrohitagrawal/batchbeacon-ai) | Returned 404/not visible through connected access. Not proof of global absence and not a creation/publication result. U12 authorizes local executor to inspect/reuse/create the intended target. |
| X21 | Connected GitHub commit reads: [Impeccable](https://github.com/pbakaus/impeccable/commit/08d5b470495d242ca0470f4aeae1956c3a074f83), [Emil](https://github.com/emilkowalski/skills/commit/2d228630ba1446365f614a108cb8252f1feda202), [project-doc-skills](https://github.com/imrohitagrawal/project-doc-skills/commit/f00044727044dccfe8aa9f9d987d410341287371) | Immutable source pins resolved. Selected document-skill sources/build/license inspected; onboarding/doc-critic deferred. No installation, build or runtime compatibility verified. |
| X22 | Connected read of [stackclimb-skills README](https://github.com/imrohitagrawal/stackclimb-skills/blob/main/README.md), blob `b17fa00b0fb1a6a0df494fc2cb18923bf0ef161e` | Upstream release claims do not override the owner’s explicit exclusion of Work Package Protocol and Multi-Work-Package Orchestration. Reference only; no dependency added. |

New facts do not establish real cloud resources, authenticated owner-machine capabilities, tested skills, completed source review, running monitors or executed application evaluations. All those remain evidence obligations in the tasks.

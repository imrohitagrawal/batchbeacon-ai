# BatchBeacon AI — authorization and retail-operations revision review

Review date: **17 October 2026**. Integrator: `/root`.

**Latest audit:** the owner-requested complete-file contents and replacement-download audit is recorded in §6 below.

**Disposition: planning package ready for the owner-invoked implementation kickoff.** This is a document-consistency disposition. It is not application acceptance, a completed local setup, a security certification, an activated autonomous run, a deployment pass or final submission approval.

This record covers the latest U07–U16 owner decisions and related changes. The unchanged original documents remain the product and operating-contract sources. [OWNER_DECISIONS](../OWNER_DECISIONS.md) records the later authorizations; [SOURCES](../SOURCES.md) records consequential interpretations and conflicts. Earlier [plan](PLAN_REVIEW.md) and [owner-update](OWNER_UPDATE_REVIEW.md) reviews retain their historical findings and hashes. Their pending proposals do not override current grants.

## 1. Real reviewers and limits

Three real subagents participated. They are historical planning reviewers, not promised Codex workers on the owner's machine. The initial review covered all ten specialist perspectives in master §6, as recorded in PLAN_REVIEW. This later pass focused on the new scope, authorizations and changed dependencies.

| Actual reviewer | Required perspectives and current work | Independence and limits |
| --- | --- | --- |
| `/root/architecture_ai_qa_review` | Principal engineering; AI/evaluation; QA. Reviewed finite autonomy, one-machine coordination, skill sequencing, cross-client recovery, retail/learning contracts and interrupted-evaluation recovery. | Independent of the retail specification's author. Reopened the corrected contract/lease passages. No native goal, application, SDK or transaction was executed. |
| `/root/product_ux_judge_review` | Product/user advocacy; frontend/accessibility; skeptical judge. Authored the bounded retail-operations extension, then checked its integration with the original product, tasks, UI approval and six demo flows. | The author's integration audit is not an independent review of its own specification. Architecture separately reviewed the consequential learning contracts. No replacement visual design or runtime evidence was produced by this pass. |
| `/root/delivery_security_review` | Program/delivery; DevOps/DevSecOps; SRE/FinOps; security/privacy. Reviewed finite budget, existing-project configuration, publication grants, retention, private/public separation and optional notification authority. | Independent targeted document review. Closed funding and source-table issues, then inspected private-input handling. No account access, provisioning, paid call, alert delivery or cloud operation. |

The integrator consolidated the corrections. These were bounded closures of identified issues, not repeated broad review cycles. No unanimous runtime pass or independent authorship is implied.

## 2. Findings and closure

| ID | Finding and impact | Resolution and actual closure |
| --- | --- | --- |
| R01 — sequencing blocker | Requiring skill stages through application verification before the first design output made the skill gate depend on its own future artifact. | Require SK10–SK30 before first dependent use, or record the native design fallback. SK40 follows the actual artifact. Architecture reopened and closed the corrected policy. |
| R02 — important | A broad T06 dependency could stop independent retail and learning backend work while visual treatment awaited selection. | Only final visual integration depends on T06 approval. Provisional contracts, backend, bounded fixtures and functional UI work can proceed. Architecture closed the corrected retail dependency table. |
| R03 — correctness blocker | An interrupted pure evaluation could leave the shop's single active slot occupied indefinitely or allow a late result to replace an expired run. | A server-controlled 30-second lease transitions abandoned work to FAILED/EXPIRED, releases the active slot without refunding consumed lifetime allowance, and rejects late completion. IT-LEARN must test interruption, expiry and stale completion. Architecture closed the contract; runtime testing remains future work. |
| FIN01 — authority blocker | A release prompt could be read as funding unspecified later organizer obligations. | Funding ends at the explicitly approved 7 November 2026, 23:59 IST cutoff. Later obligations need a new finite decision. Expiry does not imply verified shutdown or destructive cleanup authority. Delivery reopened and closed the corrected passages. |
| DOC01 — important | A blank line split the SOURCES decision table and weakened the conflict register's readability. | Restored one valid Markdown table. Delivery reopened and closed the correction. |
| UX01 — privacy blocker | Public STATE containing exact native-run W0, reserve and computed freeze could reveal private run timing. | Store exact values in ignored private run policy; public STATE contains only a pointer and sanitized status. Product reopened and closed the EXECUTION correction. Delivery later reviewed the broader private-input handling. |
| UX02 — evidence blocker | A design mockup requirement asked for an executed evaluation result before implementation. | Design states are explicitly illustrative. Actual stored evaluations and effects are required later by T35/F6. Product reopened and closed the UI correction. |
| REL01 — important | Release provenance omitted guidance, candidate-rule and learning-suite versions. | Release and evaluation evidence now bind these versions alongside model, source, verifier, prompt and core dataset identifiers. Product reopened and closed the release-prompt correction. |
| PRIV01 — delivery qualification | Owner-supplied account and capacity hints needed to survive handoff without entering public repository history or artifacts. | Included private owner-input JSON; public documents contain handling instructions and a path only. Delivery's targeted privacy review found no blocking correction. Actual ignore/tracking state is deliberately established at kickoff, not claimed by this package. |

No unresolved document-correctness blocker remained in these reviewed scopes. Workload and actual implementation risks are still real; the plan does not convert them into passes.

## 3. Reviewed revision evidence

The following hashes identify the reported review snapshots. A hash identifies file bytes, not the breadth of a review. Targeted closure means the named changed passages were reopened. Reviewers did not all reread every final package byte. The final public [PACKAGE_MANIFEST](../PACKAGE_MANIFEST.sha256) identifies the packaged public files after the integrator's final editorial and packaging work; it is not a substitute for application evidence.

| Reviewer / scope | File at review | SHA-256 |
| --- | --- | --- |
| Architecture — final retail contract/lease and dependency closure | `specs/retail-operations.md` | `130dbd0b87b4ad80c4420f98b6d96fc393e9743a3a626bf40e814433d6dbb786` |
| Architecture — skill plan | `docs/TOOLING.md` | `dd20a7946323e1163970724dabd232694c5c1b0791b798b34efda6ce2b0ee7ea` |
| Architecture — task integration | `specs/tasks.md` | `16c3112df60fe1060bd70bb203a6d27ea04f4c87783450b15807690ea3d784de` |
| Architecture — earlier R01 policy closure, before later privacy edits | `docs/EXECUTION_POLICY.md` | `42166159daba181cfd57f231ee32b7c51037eb999a3dd8409ee168e8f3172963` |
| Architecture — finite goal | `prompts/overnight-goal.md` | `ccd4be0569188315b3547662cac34fb8044da9bca5742a658b76ec2006cc97ca` |
| Product — requirements integration | `specs/mvp.md` | `06f6aa1b505539f03b064eaa868141d6a22cd7ab32249293095f20af110b50a1` |
| Product — UX01 final targeted closure | `docs/EXECUTION.md` | `c5665aa5efabe7637caf7ff054800d5777184324447eccbc54b629ca347d9bfd` |
| Product — UX02 final targeted closure | `docs/UI_DIRECTIONS.md` | `cef3ab9ca7869802ae479fbc71063b338d2fe83e1dac13d2f1e158ca5c539c09` |
| Product — REL01 final targeted closure | `prompts/05-release-and-submission.md` | `f37390dc9279f1c996459c41e9425a3d93bf9a2c684074fb676a7b6e6bb7523b` |
| Delivery — budget, configuration and operations | `docs/OPERATIONS.md` | `7f8895dcec035d5d2fd834753fd0044ef54668e3ec12e76b46c637429cf97dd8` |
| Delivery — DOC01 targeted closure | `docs/SOURCES.md` | `a390c7f073b9e7258cd3c26ea59163a06f5592010ded9a70f9578e796c6c246c` |
| Delivery — final public privacy/authority passages | `docs/OWNER_DECISIONS.md` | `ea8f37b12fc5d09eb3dcd2d6a5a8bc0e9eeda02fb9dd36da45159b9ae7e9de4f` |
| Delivery — final public private-state handling | `docs/EXECUTION_POLICY.md` | `a19ecdc90ba4ebd75a5b36a739932897c3b3f82b3b5584b42309c28eda53ed11` |
| Delivery — final kickoff privacy handling | `prompts/01-codex-kickoff.md` | `b251fd7c785af091927d11e82de574d7b1ec5e7715ac63c930eabf543497a07a` |
| Delivery — INDEX privacy row, before the integrator added this review link | `docs/INDEX.md` | `41da58dce6a2f213fb5c8f05a722591018af89579d4a6c3b61de964fa478c165` |

The private-input body and hash are deliberately absent from this public record. The last delivery pass checked valid JSON, the owner-reported/private classification, absent actual run times, restrictive `0600` packaging permissions, and the reviewed public instructions. It did not establish the owner's eventual Git ignore/tracking state or inspect the final ZIP. The integrator owns the package checks below.

## 4. Artifact verification and packaging boundary

The integrator performed artifact-only checks on this revision:

- Both original document hashes match the unchanged source copies: brief `4643b9c2753899d0c4a8f48fa68b547af86ec2a897d38fae19aa8b726e77727e`; master `bc3b8ec0a6442b2f5164ed6ffcd986ed7d06329b07e0d5af17dd9f62eff5be72`.
- Exactly 43 uniquely defined acceptance criteria (AC-01–43) and 36 uniquely anchored implementation tasks (T01–36) are present. This verifies identifiers, not satisfaction of the criteria or task completion.
- 103 local Markdown link targets, including referenced anchors, resolve in the package. External references are source records, not an assertion that every future fetch will succeed.
- The two supplied Python helpers parse as Python. They were not executed against the owner's machine, authenticated accounts or a live application in this revision.
- A scoped scan found no supplied private account value or actual personal continuation-window pattern in the public Markdown, Python, SVG or manifest text. This is not a comprehensive application secret audit.
- The private owner-input file is valid JSON with `0600` file and `0700` directory permissions in this packaging workspace. Actual owner-machine permissions and Git exposure still require local verification.
- The owner archive contains 35 regular files under one `batchbeacon-ai/` root, matching the final local bytes. The public manifest contains 33 file hashes, excluding itself and the one private owner-input file. No application build, dependency installation, cloud resource, repository publication or submission resulted from these packaging checks.

The complete owner handoff ZIP includes `.local/owner-inputs.json`. Treat that ZIP as an owner handoff, not a public submission attachment. The public SHA-256 manifest excludes `.local/**` and its own manifest file. Codex must inspect the real repository and ensure private paths are ignored **and untracked**, including staged and historical exposure checks, before a commit or push. An ignore rule does not remove prior disclosure.

`AGENTS.md`, `docs/STATE.md`, `docs/SKILLS.md`, actual run policy, deployment records, executable application tests and measured evidence remain kickoff/implementation outputs. Their absence in a planning package is intentional. The kickoff must create or conservatively update them from observed facts without overwriting existing instructions or inventing passes.

## 5. Remaining gates and delivery risks

- **No broad owner questionnaire blocks kickoff.** Budget, bounded cloud configuration, gated synthetic public access, repository publication, two operations surfaces and one-machine continuation are already authorized in OWNER_DECISIONS. Reuse those grants.
- **Final visual treatment:** A's evidence-workbench structure is accepted in principle. Preserve all three original directions as historical concepts; produce a stronger workbench and retailer-console treatment for the owner's concrete approval. Independent environment/backend work can proceed. Old wireframes are not approved production visuals.
- **Human source and evaluation custody:** the owner agreed to perform the review. The actual source/gold/custody checklist is still required; willingness is not completed review. Keep all original 24 development and eight held-out cases and the predeclared 12-case coverage denominator. The separate six-case learning suite cannot inflate those results.
- **Machine, skills and cloud:** installed clients, instruction loading, local authentication, project ID, model/ADK compatibility, region availability, transaction behavior, skill admission/discovery and native finite-goal liveness require actual local evidence. Historical subagents and web documentation do not establish those capabilities.
- **Scope and deadline:** the added retail console and bounded learning workflow are P0 obligations. They share contracts and one service; they do not create a multi-tenant enterprise platform or automated model retraining. Use the dependency queue and fixed reserve; cut P1/P2 first. If a required gate cannot pass, report the gap instead of silently deleting P0 or relabeling a mock as completed work.
- **Cost and availability:** the approved ₹6,000 ceiling has finite pools, protected demo capacity and a funded expiry. Provider alerts/caps can lag and cover only selected services. Persist lifetime reservations and do not refill them on restart or calendar rollover. Verify remaining service liabilities and reversible deactivation steps before release.
- **Terms and submission:** the captain attests that the team is eligible; this is not independent identity verification. Official source conflicts and terms obligations are preserved in SOURCES. The final candidate, then-current terms and final submission still require the captain's approval.
- **Optional notification delivery:** a specific destination and test authorization remain unselected. Record NOT CONFIGURED for external notification delivery; dashboard-visible alerts and the rest of the private operations scope proceed. Do not infer permission to message from an account hint.
- **Excluded dependencies:** neither the unfinished StackClimb Work Package Protocol nor Multi-Work-Package Orchestration is an operational dependency, irrespective of later upstream release claims. Optional skills cannot override owner authority, current source requirements or actual client permissions.

## 6. Complete contents and delivery audit — 18 October 2026 IST

The owner reported that the earlier downloaded ZIP omitted three files, then explicitly requested a complete audit of every file's contents. This is the separately requested contents/delivery audit, not an unsolicited extra implementation review cycle.

The integrator and three real existing subagents inspected the complete 35-file package. Architecture also independently checked the then-current ZIP: all three reported paths existed, all 35 entries matched the source tree, and all 33 public manifest records verified. That does not establish which prior download/extraction the owner received. A uniquely named replacement export avoids relying on the earlier download link. No cause such as client caching has been established.

**Disposition:** complete for the defined planning handoff; the concrete ambiguities found below are closed. Actual local configuration, skill installation/discovery, application implementation, tests/evaluations, cloud state and final submission remain future verification obligations. No claim of universal error-free instructions or completed application acceptance is made.

### Corrections made and independently reopened

| Finding | Final instruction | Closure scope |
| --- | --- | --- |
| CONTENT-01 Evaluation retry identity | A same-attempt transport retry returns the original attempt/report without another reservation. A deliberate new evaluation after a terminal attempt gets a new server-issued identity and consumes a remaining lifetime slot, even with unchanged inputs. Failed/expired attempts remain counted; activation binds to the exact passing report. | Architecture reopened the CandidateEvaluation contract, recovery paragraphs, IT-LEARN row and limit table. |
| CONTENT-02 Historical-source eligibility | A deliberately selected reviewed frozen demo may support a dated current-as-of result and labelled simulated hold. Expired/failed live evidence cannot regain hold eligibility by relabelling. A deliberate historical restart uses a separately rate-limited incident while preserving the failed live history and allowances; dependency changes invalidate both modes. | Architecture reopened AC-17, NF-03 and the UT-STATE/IT-ACTION obligations. |
| CONTENT-03 Archived UI selection request | The retained overview image's embedded selection request is explicitly superseded by U02. A is accepted in principle; replacement workbench/retailer visual approval remains pending. Original image/SVG bytes and filenames are retained as historical artifacts. | Product/UX reopened the prominent UI_DIRECTIONS caption and INDEX row. Standalone old images need the archive caption/current decision context; no new visual quality approval is implied. |
| CONTENT-04 Historical review hashes | PLAN_REVIEW's old final hashes are explicitly tied to the original reviewed package, not the current bytes. | Delivery/security reopened the corrected historical paragraph. |
| CONTENT-05 Review-table reference | OWNER_UPDATE_REVIEW correctly points to the historical hashes above its closing section. | Delivery/security reopened the corrected sentence. |

### Every-file coverage

The reader names below refer to actual agents: Architecture/AI/QA is `/root/architecture_ai_qa_review`; Product/UX is `/root/product_ux_judge_review`; Delivery/security is `/root/delivery_security_review`; Integrator is `/root`. Complete fresh reads are distinct from earlier reviews and from the small targeted closure reads. The final manifest identifies packaged public bytes. No private input hash is published.

| File | Reader/check owner | Actual contents check |
| --- | --- | --- |
| `.local/owner-inputs.json` | Delivery/security | Complete JSON and private-state handling; no private values published |
| `HACKATHON_BRIEF.md` | Integrator | Complete fresh read; unchanged original |
| `HACKATHON_CODEX_MASTER_PROMPT.md` | Integrator | Complete fresh read; unchanged original |
| `docs/EXECUTION.md` | Integrator | Complete fresh read; source/authority/dependency integration |
| `docs/EXECUTION_POLICY.md` | Delivery/security | Complete fresh read |
| `docs/INDEX.md` | Product/UX | Complete fresh read; archive-caption correction reopened |
| `docs/OPERATIONS.md` | Delivery/security | Complete fresh read; finite budget and configuration checks |
| `docs/OWNER_DECISIONS.md` | Delivery/security; Product/UX | Complete fresh reads; existing grants and remaining gates |
| `docs/PACKAGE_MANIFEST.sha256` | Integrator; Architecture/QA | Every record checked; final regenerated manifest and ZIP checked by integrator |
| `docs/SOURCES.md` | Delivery/security | Complete fresh read; no new external research claimed |
| `docs/TOOLING.md` | Product/UX | Complete fresh read; admission/discovery/application and resume distinctions |
| `docs/UI_DIRECTIONS.md` | Product/UX | Complete fresh read; superseded selection caption reopened |
| `docs/reviews/AUTHORIZATION_REVIEW.md` | Delivery/security; Integrator | Complete prior body read by reviewer; this dated append and final packaging by integrator |
| `docs/reviews/OWNER_UPDATE_REVIEW.md` | Delivery/security | Complete fresh read; historical wording correction reopened |
| `docs/reviews/PLAN_REVIEW.md` | Delivery/security | Complete fresh read; historical hash qualification reopened |
| `docs/ui/direction-a-evidence-workbench.png` | Product/UX | Visual inspection and successful decode; original historical asset retained |
| `docs/ui/direction-a-evidence-workbench.svg` | Product/UX | Complete XML/text parse, labels and no external asset references; historical asset retained |
| `docs/ui/direction-b-guided-review.png` | Product/UX | Visual inspection and successful decode; original historical asset retained |
| `docs/ui/direction-b-guided-review.svg` | Product/UX | Complete XML/text parse, labels and no external asset references; historical asset retained |
| `docs/ui/direction-c-incident-timeline.png` | Product/UX | Visual inspection and successful decode; original historical asset retained |
| `docs/ui/direction-c-incident-timeline.svg` | Product/UX | Complete XML/text parse, labels and no external asset references; historical asset retained |
| `docs/ui/directions-overview.png` | Product/UX | Visual inspection and successful decode; original historical asset retained |
| `prompts/01-codex-kickoff.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/02-first-slice.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/03-complete-p0.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/04-independent-review.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/05-release-and-submission.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/handoff.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/overnight-goal.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `prompts/resume.md` | Product/UX | Complete fresh read; self-contained execution and gate consistency |
| `scripts/configure_local.py` | Architecture/AI/QA; Integrator | Complete source read and schema reconciliation; Python parse only |
| `scripts/local_preflight.py` | Architecture/AI/QA; Integrator | Complete source read; Python parse only, no owner-machine execution |
| `specs/mvp.md` | Architecture/AI/QA | Complete fresh read; historical-source eligibility correction reopened |
| `specs/retail-operations.md` | Architecture/AI/QA | Complete fresh read; evaluation-attempt correction reopened |
| `specs/tasks.md` | Architecture/AI/QA | Complete fresh read; requirement coverage and dependencies |

### Exact targeted-closure revisions

These are the full file hashes reported after reopening the named corrections. The scope of the closure remains the corrected passages; a hash is not a claim that every reviewer reread all final bytes. The prior AUTHORIZATION_REVIEW body was fully read at hash `76fbd53a117717623b07df569582b9a1fccb0b05aa728bb02968d5693a8465ee`; this dated append and final archive work were subsequently performed by the integrator.

| Corrected file | SHA-256 |
| --- | --- |
| `specs/mvp.md` | `b120ee7ba179a98f6687fe77c9d1392c58808e24685c9fd5841bcad01eb7e0e1` |
| `specs/retail-operations.md` | `c93e6303db3aa78af8dd87333f0a9e46d3da89d550b24c8f3b633fc68e486d1c` |
| `docs/UI_DIRECTIONS.md` | `7c0b626684d9d3f105dd921abf5aa82461ddf471c16e1b2198c23ac4da2f868b` |
| `docs/INDEX.md` | `134e4f0ed2d9d5326686ad99aa8bb89f58190230ad411991bc640a54dc0c0f52` |
| `docs/reviews/PLAN_REVIEW.md` | `41e79e717de0dd8c679b86a5bcbd197fcb50429a6279265b14256a620869e38f` |
| `docs/reviews/OWNER_UPDATE_REVIEW.md` | `fca3694b03997b4a4be2b1a46b2c944a39512b4d2ae066daea68c56650e0b419` |

### Final export checks and intentional unknowns

The final export contains the same 35 regular files as the promised layout, including all three reported missing files. The two original document hashes and all seven original concept asset hashes are unchanged. All eight prompts contain their complete instructions. No empty file, merge-conflict marker, output-truncation marker or unintended TODO/TBD/fill-in placeholder was found in the scoped public text check. Local links/anchors, uniquely defined AC-01–43 and task anchors T01–36 were checked; the Python helpers parsed without executing them against the owner machine.

The replacement ZIP was reopened; all entries were compared byte-for-byte with the reviewed source and exported tree, duplicate names were rejected, CRC checks passed, and the 33 public manifest hashes were recomputed. The private `.local/owner-inputs.json` is included in the owner ZIP but deliberately excluded from that public manifest. Its values are owner-reported hints, not verified credentials, project resources or a started run. It must remain ignored and untracked before repository publication.

NOT RUN, NOT CONFIGURED and local-verification requirements are intentional evidence boundaries. They must not be filled with invented success to make the package look complete. Existing cloud/budget/repository grants remain adopted; final replacement-design approval, actual human source/custody completion, an encountered secure sign-in handoff and final candidate/submission approval retain their defined gates. The private technical dashboard, separate retailer console, bounded guidance learning, one-machine continuation policy and excluded unfinished StackClimb protocols remain unchanged in scope.

# BatchBeacon repository map

One canonical definition per responsibility keeps the project portable. Generic filenames are not automatically loaded by every coding client. Actual `AGENTS.md` must point to this map and the active state after workspace inspection.

| Need / familiar filename | Canonical BatchBeacon location | Status in this planning package |
| --- | --- | --- |
| Approved product / original PRD | [HACKATHON_BRIEF.md](../HACKATHON_BRIEF.md) | Original, unchanged |
| Engineering operating contract | [HACKATHON_CODEX_MASTER_PROMPT.md](../HACKATHON_CODEX_MASTER_PROMPT.md) | Original, unchanged; current owner exceptions in SOURCES |
| Implementation PRD / requirements | [specs/mvp.md](../specs/mvp.md), bounded [retail extension](../specs/retail-operations.md) | P0-01–13, rules, six journeys, AC-01–43 and exclusions; extension details have one canonical owner |
| Architecture.md | [EXECUTION §3](EXECUTION.md#3-architecture-recommendation) and [MVP contracts](../specs/mvp.md#5-domain-contracts-and-consistency) | Recommended architecture; actual deviations must be recorded |
| phases.md | [EXECUTION](EXECUTION.md), [execution policy](EXECUTION_POLICY.md) | Milestones, fixed reserve, setup/finite-goal/resume boundaries; actual private run timing is excluded |
| tasks.md | [specs/tasks.md](../specs/tasks.md) | Stable tasks/dependencies and evidence links; app work not started here |
| design.md | [DESIGN.md](../DESIGN.md); [UI_DIRECTIONS](UI_DIRECTIONS.md) | Current Evidence in focus treatment approved under [U02](evidence/M1-visual-approval.md); original concepts/rejected treatments remain archived. Final runtime integration remains a separate task |
| test_plan.md | [MVP test/evaluation registry](../specs/mvp.md#8-tests-evaluations-and-evidence-registry), task evidence columns, EXECUTION gates | Strategy/obligations exist; executable tests and actual reports are future task outputs |
| security.md | MVP P0-07/08 and NF-01/02/04/07, EXECUTION architecture/authority gates, [OPERATIONS](OPERATIONS.md) | Planned trust, privacy, access, spending and release controls; no runtime pass implied |
| decisions.md | [SOURCES](SOURCES.md), [OWNER_DECISIONS](OWNER_DECISIONS.md), later `docs/DECISIONS.md` | Source conflicts and current owner update are portable; local decision log created conservatively |
| memory.md | `docs/STATE.md` plus dated evidence/decisions | STATE created from actual observations at kickoff; no fabricated machine memory |
| rules.md | Concise root `AGENTS.md`, linking the originals and this map | Created/conservatively updated only after real instruction/workspace inspection |
| Autonomy / mode configuration | [EXECUTION_POLICY](EXECUTION_POLICY.md) plus actual run/approval record linked from STATE | Policy prepared; settings, permissions and native goal must be locally verified |
| Observability / runbook | [OPERATIONS](OPERATIONS.md) | Approved private dashboard/availability scope, finite cloud setup/budget and separate retail console; optional external notification delivery still needs a channel |
| Skills | [TOOLING](TOOLING.md), later observed `docs/SKILLS.md` | Pins and admission/install/discovery/application stages; no installation is claimed by this package |
| Private execution settings | Included `.local/owner-inputs.json`; later `.local/run-policy.json`, `.local/run-records/` and `.batchbeacon/local-settings.json` | Owner-input hints supplied privately; live configuration created/validated after inspection. Ensure all remain ignored/untracked; never copied into public STATE/history/media |
| Reviews | [Current authorization review](reviews/AUTHORIZATION_REVIEW.md), [historical plan review](reviews/PLAN_REVIEW.md), [earlier owner-update review](reviews/OWNER_UPDATE_REVIEW.md) | Actual document reviews, with scope and revision limits; later application reviews need actual code/evidence |
| Resume / handoff | [resume](../prompts/resume.md), [handoff](../prompts/handoff.md) | Agent-neutral recovery instructions; no process resurrection claim |

Future scope: [B0–B3 roadmap and ATT-01 PDF/image evidence](ROADMAP.md). Planned items are not delivered capabilities.

## Read order and ownership

First session: follow the kickoff, read both originals completely, then the execution/specification package. Subsequent sessions: applicable instructions → bounded STATE → current decisions/authority → active task/specification sections → relevant evidence/code. Read additional material when the task needs it. Do not load the whole archive on every turn.

Only the integrator updates canonical shared state. Public STATE links the ignored run policy and redacted admission status; it never records personal availability, private start/expiry or local process/session identifiers. Put detailed test results and failed experiments in dated evidence, not a growing STATE transcript. Record claims as observed, inherited, proposed, blocked or not run. Preserve source/model/prompt/verifier/dataset/release identifiers so another agent can assess staleness.

## Other coding clients

Current [Claude Code documentation](https://code.claude.com/docs/en/memory) supports direct AGENTS loading in recent versions, with behavior affected by existing CLAUDE files. Inspect the installed version and active instructions. If an adapter is needed, conservatively create a small root `CLAUDE.md` importing `@AGENTS.md`; preserve existing policy and verify loaded context. Do not install Claude merely for portability.

[Gemini CLI](https://geminicli.com/docs/cli/gemini-md/) defaults to `GEMINI.md` and supports imports. When actually using it, a thin root adapter can contain `@./AGENTS.md`; verify the loaded context with the installed client's supported memory command. Avoid global configuration changes or copied competing rulebooks.

If Impeccable is admitted and requires `PRODUCT.md`, use a concise derived context adapter pointing back to the approved brief/MVP. It must not become another authoritative PRD. No adapter, native session memory or provider credential is assumed to exist in this package.

On client transfer: verify the prior writer has stopped, reconcile unfinished changes and unknown cloud outcomes, verify the new client's permissions and instruction loading, then assign the integrator. Git/docs/evidence transfer project knowledge; authentication, native permission settings, private run policy, active sessions and selected skill discovery/loading require separate verification. Reuse the recorded U09–U12 project grants; no new tool may expand them.

# Submission recovery and public admission

Recovery starts from `6129d97dfdbc5f2fb7b1ec001afbda6fc39482fc`.
The public repository and remote main match that checkpoint. Its hosted run
[39125165143](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39125165143)
passed. The previous executor completed its turn; no project model/build/server
helper remains active. This recovery has a separately approved finite private
policy, preserves the original freeze/reserve, and creates no native Goal.

## Official acceptance contract

The authenticated form was reread on 18 October 2026. It requires a working Google
Cloud prototype, public source and live links, the prescribed template exported to
PDF (up to 5 MB), a 3–4 minute demo, theme and description (1,024 characters).
The deadline remains 18 October 2026, 23:59 IST. The approved 230-second submission
and 160-second alternate cuts remain; neither is yet an exported video.
The official terms were reread, including their precedence over promotion and
material IP/promotional provisions. Inspection is not acceptance or submission.

The registered team is **Bugging Debuggers**. Dashboard names are Rohit Agrawal,
Niharika Aggarwal, Aayushi Priya and **Priyanka Shelke**. The last spelling supersedes
the earlier owner-attested spelling for submission artifacts; no roster changed.

## Reproduced findings and corrections

| Finding | Classification and evidence | Disposition |
| --- | --- | --- |
| Unlimited fresh guests each obtain independent upload allowances | REQUIRED_CONTRACT: local reproduction issued 100 guests without advancing time; production guest creation read no global counter. AC-28/T09 require bounded global/session usage. | Namespace-wide, operator-initialized lifetime and rate-window admission now participates in the same Firestore transaction as guest creation. Runtime requires typed configuration; absent/corrupt/expired/exhausted state denies. Startup cannot initialize or replenish it. |
| Admission expires during commit acknowledgement | REQUIRED_CONTRACT: independent injected-clock reproduction returned a guest after the admission expired. | The guest transaction now carries admission expiry through the post-commit deadline check. Committed records and consumed capacity remain. Regression independently passes. |
| Impossible stored rate-window count resets on rollover | REQUIRED_CONTRACT: a stored count above its configured ceiling was accepted after rollover. | Validate stored count before rollover. Regression independently passes. |
| Current README/submission copy understates delivered integration and misstates U02 | REQUIRED_CONTRACT under the explicit truthful-packaging instruction. | Updated drafts are being integrated against the eventual accepted candidate. Historical failed evidence stays intact. |

Independent correction review: 63 focused checks passed, plus three private
runtime-consumer/harness checks. Actual Firestore acceptance passes five additional
checks: missing admission creates nothing, two clients share the last rate slot,
cold reconstruction does not reset it, lost acknowledgement preserves the lifetime
charge, and only the intended seven records exist. Actual usage: 26 reads, 10 writes,
no Storage/model calls. This uses operator credentials and an isolated test namespace;
it is not Cloud Run cross-instance or public-browser evidence.

The guest creation ceiling bounds provisioned sessions and their configured child
allowances. It is not a universal cost cap on hostile HTTP traffic or repeated
reads. Provider caps, service limits and non-model liability remain separate gates.

The first full local check passed backend tests but could not launch an absent
cached Chromium binary. Its failure is preserved privately. The changed experiment
uses installed Chrome via the existing browser-channel configuration. Hosted Ubuntu
bootstrap/Chromium and candidate-head verification remain separate before release.

## Publication and packaging

Independent audit at the recovered head inspected 56 reachable commits/640 unique
blobs and 368 tracked files. No secret/private-path disclosure was reproduced.
Original-document, synthetic-label and admitted-skill hashes match. Dependency
license metadata and retained notices were inspected. This is bounded evidence,
not an exhaustive legal or image-content certification. The project license is an
owner choice; no new license was invented.

The editable organizer-template draft preserves all 16 slots and organizer assets.
A 15-page audience PDF draft now renders through system CoreGraphics/PDFKit
using the original template artwork and fitted editable-deck geometry. It is
approximately 2.37 MB; this is a companion authoring route, not an Office export. Raw private screenshots containing session
details are excluded. The local artifact runtime remains unavailable; the explicit
recovery fallback uses template XML editing and native rendering, without claiming
artifact-tool authoring/finalization. Measured narration tracks are 230/160 seconds; completed videos and final PDFs
still require visual,
privacy, duration, size, link and unauthenticated-playback checks.

## Deployed recovery and overload correction

At application head `301773e9564241fa8bb51ec8868b803b7b1b29fe`, exact-head
hosted checks passed (1,332 unit and 66 browser checks). The private image and
runtime were independently verified, with original source, budget balances and
attempt liabilities retained. A fresh private real Gemini/ADK journey completed
label extraction, deterministic historical-SFA comparison, explicit browser
confirmation and persistent queue. Its helper later failed during foreign-guest
setup; the paid journey and seven browser checks were independently reconciled,
not discarded or counted as a complete helper pass.

Four simultaneous maximum-size uploads reproduced instance termination and four
503 responses. OOM was not established. Lowering configured per-instance
concurrency from four to one, preserving two instances/CPU/memory, produced three
successful uploads across two actual instances and one platform-capacity429.
Read-only reconciliation followed by the original-key serial recovery succeeded;
retained maximum-size image hashes and pixels matched. This proves bounded
backpressure/recovery, not four simultaneous successful responses or a throughput
benchmark. Original failed receipts remain preserved.

Exact deployed ownership/CSRF/privileged-route checks, observation invalidation,
historical action deduplication, deterministic review and actual fixed guidance
six-case/nine-variant evaluation, activation and rollback passed. Independent
readback confirmed unchanged model accounting, zero outstanding reservation,
owned guidance revision three and the foreign shop's untouched baseline. This
is not a live-source update or protected model-quality evaluation.

The overload exercise separately reproduced AC-26: an unknown upload response
lost its operation key and offered no working recovery control. The smallest
correction adds owned exact-key capture reconciliation, retains only file hashes
and the original operation key across browser reload, and requires explicit
same-file retry. Ready uploads reconcile without another upload. Other mutations
remain blocked while the outcome is unknown. JSON5xx and platform non-JSON429
preserve uncertainty and the recovery control. Independent injected committed-
acknowledgement failures reproduced the defect and pass after correction.
The corrected candidate passes 1,335 local unit checks, 70 installed-Chrome
browser checks and Ruff. Exact-head hosted checks and exact-image deployment
remain separate gates.

## Remaining release gate

Public access remains closed. Complete deployed isolation/currentness/allowance
acceptance and fresh real Gemini/ADK behavior, then independent verification before
public exposure. Keep UK review-only under U17. Live-source refresh, full protected
evaluation/custody, all six deployed journeys, complete Operations/retention and
attachment extraction must not be represented as completed. Any narrower release
requires explicit owner approval of its concrete omissions. OWNER-SUBMIT remains
separate and follows complete, tested artifacts.

Private admission, detailed receipts and process/configuration data remain under
`.local/run-policy.json` and `.local/run-records/submission-recovery/`.

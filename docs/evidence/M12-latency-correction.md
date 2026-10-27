# Latency correction — released instrumentation

U48 preserves MEDIUM reasoning, model/completion headroom, min0 and the filmed
visual identity, alongside all subsequent shipped fixes. All R01–R12/F1–F8 remain.
The released instrumentation measures latency; it makes no speed, p95 or SLA claim.

## Implemented boundary

A content-free request trace uses one process monotonic clock, bounded allowlisted
stages and a private correlation/request binding. Provider transport/body reading
ends before retained-response storage; counting, admission, accounting, translation,
persistence and owned status reads have separate spans. Failed/refused/unknown
and disconnected paths retain observations. ASGI acceptance of a terminal body
is not a client acknowledgement. Existing private operational-log access/retention
applies; no raw label/source, credentials or reasoning text enters these records.

Opt-in `acquisition-stages-v2` sends ordered preparing/model/saving frames and one
terminal envelope. Old v1 and ordinary JSON remain supported. The worker retains
its capacity/accounting ownership after disconnect. Progress grants no authority
and never exposes partial model output. The v2 resource invariant is at most
64KiB and64 nonempty data frames: the finite status schema and three phases
need only a small fraction of that space; excess input is rejected before use.
The total byte bound includes whitespace heartbeats. The nonempty-frame count
allows independently configured heartbeat cadence; M13 records the reproduced
original line-count defect and its correction.

The existing adjacent live status announces actual phase changes. Heartbeats do
not change its text or focus. No new timer animation, percentages or ETA are added.
The saved-record reload remains visibly pending until it finishes. Browser User
Timing entries separately record acquisition response, saved reads, failed reads,
fixed terminal outcome and first usable current owned rendered evidence; entries
of the same name replace previous measurements. Server/browser clocks are never
subtracted. No hero, HTML, CSS, image, typography or layout asset changes occur.

## Verification and disposition

Independent backend and UX review reproduced logging, expiry-outcome and failed-read
measurement/status defects. Their corrections have independent controls; original
failed evidence is retained privately. Controlled parser/recovery tests include
malformed/reordered/oversized/truncated streams, duplicate terminals, disconnect,
expiry, original-key reconciliation, slow saved reads and failed reloads. These
are automated technical observations, not actual screen-reader speech or human
comprehension evidence. Current-release byte and desktop/phone/video baselines
were independently captured before edits without guest/model writes.

Detailed actual commands, review bindings, accounting snapshots and release gates
are retained in the ignored `.local/run-records/latency-implementation-20261028/`.
Candidate local/hosted/build/deployed and real-model results must be recorded
separately; implementation alone is not release acceptance.

## Separately gated efficiency work

The optional source-hash-bound raw-span view is implemented and its actual experiment
is recorded in [M14](M14-latency-observations.md). It reduced input tokens but failed the
predetermined consistent-speed criterion; it is not selected for latency enablement.
Original-input behavior returns on the compatible reader, with all derived records and
failed evidence preserved. Source reuse, caching and model/concurrency options remain
separate evidence-backed deferrals. No reasoning downgrade or warming is introduced.

M14 supplies the narrow legitimate current-owned unresolved-panel/recheck technical
observation. Broader live F4 cross-case/no-run coverage, human unfamiliar/returning-user,
actual VoiceOver announcements/recovery, source/gold/protected quality and wider
Operations/video acceptance remain open. Historical model observations are not new
human passes.

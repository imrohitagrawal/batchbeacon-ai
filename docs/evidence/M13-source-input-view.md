# Deterministic source-input view — implemented, not selected for latency

This candidate follows U48 and [M12](M12-latency-correction.md). It preserves the
model, MEDIUM reasoning, completion headroom, min0, original immutable source,
identity/currentness checks and all R01–R12/F1–F8. No latency/SLA/model-quality or
human acceptance claim follows from its implementation.

## Accepted representation and provenance

`SourceViewPolicy` configures immutable original/derived hashes, ordered exact raw
character spans and a typed span-capacity limit. Derivation strictly decodes the
original UTF-8 bytes and concatenates only the configured spans. It performs no
HTML/entity/newline normalization, generated summary or label-dependent selection.
A changed source/hash, invalid bounds or unsupported configuration refuses without
falling back to a purported compact interpretation.

The reviewed SFA manifest in `fixtures/sources/sfa-input-view.json` retains complete
head/title/three JSON-LD metadata blocks, the complete main notice and complete
suffix/footer/update context. Independent inspection found only general navigation,
widgets and analytics in the omitted interval. The original109,097bytes become
22,005bytes; this is79.8% fewer input bytes, not a measured token/latency improvement.
No source truth review or source epoch is rewritten.

The derived-input manifest binds the exact view policy, derived hash and sizes,
original source dependency/hash, prompt/schema/policy and captures. Sealed counting
and generation consume the identical derived text; the run/request and published
source agreement retain their existing cryptographic bindings. Quotes resolve by
occurrence in the shown view, map into one contiguous retained original span, and
publish the original artifact/hash/exact character coordinates. Quotes spanning a
cut or omitted material cannot support acceptance. Raw provider proposal hashes
remain hashes of the actual response, never rewritten JSON.

## Compatibility and activation gates

Original-only records keep their exact previous serialized fields and digests.
New compact records use `derived-input-1`; older readers reject these writes.
Before activation, release a reader that understands both formats and prove actual
historical projection, ownership, expiry, guidance and accounting continuity.
Recovery must retain that reader. Do not promise rollback to an incompatible image.

The explicit compact runtime must bind a new prompt/version, input policy, shared/
grant/nonbillable successor markers and unchanged older unknown liabilities. Model
policy changes also propagate to deterministic guidance/projection configuration
hashes. A fresh fenced/drained inventory and independently verified conditional
metadata plan are required; no active guidance history may be overwritten merely
to fit a baseline migration. A compatible ordinary-access/paid-closed recovery path
must cover any unresolved provider outcome.

## Verification status and remaining work

Independent pure review compared445retained historical rows across12kinds,
86nested input/run bindings and runtime/policy serialization against the immutable
original parser: all bytes/digests matched. Controlled tests cover exact count/
generation identity, Unicode/CRLF/entities, duplicate quotes, forged bindings,
source mutations, cut crossings, omitted quotes and strict configuration. Those
are local/fake observations. Exact application checks subsequently passed1,568unit/
231browser/30edge/eight emulator, required hosted push/PR/merged-main workflows and
cloud archive/build gates. Compatible-reader deployment and conditional activation
passed independent source/history/accounting/ownership and both-host visual checks.

[M14](M14-latency-observations.md) records all four actual compact attempts, including
the429failure and the slower successful B canary. The three accepted responses used
61.9% fewer input tokens, but the predefined repeatable-speed criterion failed. The
view remains optional and is not selected for latency enablement. Returning to original
input uses the same derived-capable reader, preserving all new records and receipts;
this is not a return to an incompatible image. Human/protected evidence remains open.

Source reuse/provider caching, model and concurrency alternatives remain deferred
until compact-input evidence warrants them. No warm-instance or reasoning downgrade
workaround is authorized. Human VoiceOver/unfamiliar-user/source-gold/protected
quality and broader Operations/video requirements remain open as recorded in STATE.

## Progress-cadence compatibility correction

Independent testing reproduced a valid488byte stream with70blank heartbeats being
refused by the earlier64line client ceiling. A configurable1second cadence with
a230second envelope could legitimately exceed that line count; production15second
cadence was unaffected. The reader now counts only nonempty data frames toward
the64frame ceiling while retaining the64KiB total byte bound, ordered stages,
unique terminal and strict EOF. Heartbeats after a terminal remain invalid.
No heartbeat changes status text, focus or model/accounting state. Independent
regressions retain the original failure and require valid longer-heartbeat streams
to finish without redispatch; oversized whitespace is still rejected.

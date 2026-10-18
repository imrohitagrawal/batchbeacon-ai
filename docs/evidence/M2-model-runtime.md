# Owned model factory and final HTTP boundary

Status: LOCAL/PARTIAL T10. The installed ADK and GenAI SDK were executed only with
explicit synthetic credentials and mocked HTTP. No paid call, real resource,
runtime ledger, application route or deployment was activated.

The application configuration binds the model/project/location/API, installed SDK
versions, instruction, schema digest, input preparation, output/count/body limits,
timeouts and summary-only redaction. Effective values must match shared admission.
A fresh in-memory ADK session makes one generation attempt. SDK retries, model
tools and continuation are disabled; original source and ordered label images are
the only user content. No reviewed answer or expected verdict is sent to the model.

The final HTTP boundary accepts the exact configured POST endpoint, instruction,
schema, settings and prepared source/images. It counts those same semantics,
requires a positive bounded count, commits a reservation, obtains a newly
acknowledged single-use dispatch claim, and rechecks the absolute deadline after
blocking steps. Count and generation requests are rebuilt from the validated bytes
before transport. Cached body identity alone does not prove transmitted identity.

Original bounded response bytes, status and completeness are committed before SDK
parsing, including error bodies and incomplete prefixes. Complete stored usage is
reconciled at the original attempt rates; missing or invalid usage retains the
reservation. Excess usage opens the durable circuit. Only one complete STOP text
candidate can leave this layer; proposal translation and publication belong to the
coordinator. A timeout, error, cancellation or repeated invocation cannot dispatch
again through an already-used claim.

Raw source/output belongs in the private attempt journal. Context-local filters
suppress SDK/HTTP logs only during this operation, including lazily created pinned
transport loggers. Explicit per-run telemetry disables content; an environment
setting that overrides it fails closed. Provider/parser/transport errors become
constant diagnostics before entering ADK's exception spans. Application logs and
unrelated concurrent SDK logs remain available. Constructed resources close on
success, setup/provider failure and cancellation.

## Verification and limits

Pre-code CO03–10/17 acceptance drove the fault matrix. Independent review
reproduced a request-stream mismatch: transport could consume bytes different
from the cached body that had been counted. A second manifestation accepted JSON
boolean/integer substitutions through Python equality; canonical JSON digests
now preserve type distinctions. Sealing count/generation bytes fixes
that boundary; its negative control restores the mismatch. Independent redaction
review also reproduced raw SDK DEBUG/telemetry content and a later lazy-transport
logger escape; explicit telemetry, task-local filtering and the pinned logger
closure address those paths. Original failures and correction evidence are retained.

The checked-in runtime matrix passes 64 cases, covering actual installed-ADK wire
parity, altered endpoint/source/images/settings/schema, configured overrides,
malformed/non-success/truncated/non-text responses, quotas, delayed admission,
lost acknowledgments, repeated execution, cleanup, cancellation, redaction and a
fresh-process real-transport-construction probe with sockets and ADC disabled.
Independent final-wire review passed 64 scoped tests, Ruff and eight additional
fault cases, with sealing/type-equality negative controls. A separate redaction
review passed 18 log/span/cleanup checks and its lazy-logger negative control.
Counts overlap. Full local locked/Ruff checks passed 884 unit and 50 Chrome
browser tests; exact-head hosted validation is pending at this checkpoint.

These tests do not prove a real model's accuracy, injection resistance, provider
billing bounds, genuine service timing or deployed redaction. Third-party tracing
instrumentation/exporter integration is not admitted by this local slice. The
runtime remains unmounted, T08 paid admission closed, and human source/gold/H and
final-submission gates unchanged. No release freeze follows.

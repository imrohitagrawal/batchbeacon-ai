# Private image Storage adapter — local checkpoint

Status: LOCAL/PARTIAL. The existing guest service can now use an explicitly
injected Storage SDK adapter for its retained sanitized PNG bytes. The default
application remains unchanged. No bucket, IAM rule, lifecycle, signed URL or
background worker was created; real cloud admission remains closed.

## Evidence and access behavior

Uploads preserve the exact sanitized bytes and use create-if-absent generation
preconditions. Server-owned session/incident/capture identifiers and the image
hash form the object address under the configured bucket/prefix. Bounded metadata
binds these identifiers, byte count, original creation/retention deadline and
effective writer configuration. CRC32C and independent SHA-256 checks protect
the read-back evidence. Reads bind object and metadata revisions together.

Identical retries reconcile existing metadata and actual bytes. They never
overwrite conflicting data, renew retention or erase pending capture references.
An uncertain upload receives one bounded reconciliation; absence or unavailable
reads do not prove rollback. Guest ownership and immediate session expiry remain
in the guest service, including its check after slow reads. An expired upload
cannot mark the capture ready. The adapter also denies expired object retention;
that access denial is not physical deletion.

One strict policy supplies endpoint/mode, project, bucket/prefix, byte/metadata
limits, retention, operation/RPC deadlines and SDK-call ceiling. Uploads stay
within NF-01's 5 MiB limit and use the SDK's size-known multipart path. The larger
resumable path has separate default cleanup behavior and is excluded. Downloads
use a capped raw-byte sink; they neither decompress data nor follow a returned
media link. Hidden SDK retries are disabled, and late results are rejected.

## Reproduced corrections and independent verification

Independent S01–S16 acceptance was recorded before implementation. Two reproduced
contract defects were corrected and independently checked:

| Finding | Demonstrated impact / classification | Correction and regression |
| --- | --- | --- |
| STORAGE-R01 | SDK observability initiated extra bucket requests outside configured call/time limits, including after a cached-bucket download 404; REQUIRED_CONTRACT | Require the SDK's disable flag and a dedicated empty/quiescent client before construction/use. Environment and public-prewarming regressions fail against the previous behavior. |
| STORAGE-R02 | Malformed nested wire metadata escaped as an uncaught recursion error instead of the private unavailable response; REQUIRED_CONTRACT | Map recursion failures through the existing storage-error boundary. Both structured metadata and a larger configured JSON-string case fail when the correction is removed. |

**60 focused installed-SDK tests passed**, independently rerun by both reviewers;
counts overlap. The fake HTTP transport inspects actual multipart serialization,
checksums, URLs, preconditions, timeouts and request counts. Cases cover concurrent
create-only retries, cold-client reads, first/second-image failures, retained
pending references, lost responses, corrupt/oversized/partial bodies, changed
object/metadata revisions, ownership, expiry and stricter retention configuration.
No remaining reproduced blocker was found in this bounded local slice.

Full locked local checks passed: **579 unit and 48 Chrome browser tests**, plus
lock validation and Ruff. Hosted verification of this checkpoint is pending.
Acceptance, failed and passing outputs, hashes and review receipts remain in
ignored local evidence. No actual Storage server was used in these checks.

## Required deployment configuration and remaining gates

The application process must explicitly set
`DISABLE_GCS_PYTHON_CLIENT_OTEL_BUCKET_METADATA=true`. The adapter checks this
without changing process environment. Pinned Storage 3.17.1 also has a 404 helper
that can ignore that flag for cached bucket data. Admission therefore reads its
private cache state under a nonblocking lock and rejects warmed, busy or in-flight
clients. This deliberate read-only SDK coupling must be re-verified on upgrade.
The client must be dedicated to the adapter; concurrent external bucket-info use
is prohibited. No SDK code or cache is modified.

HTTP timeouts limit connection/read inactivity. Monotonic checks prevent late
acceptance and additional calls; they do not prove prompt cancellation of an
in-flight slow socket. Actual runtime behavior remains to be demonstrated.

Real bucket/IAM denial, runtime identity, retained-image restart integration,
lifecycle delay/soft deletion, actual extraction and connected UI remain open.
No T09 completion, T08 admission, source approval, release freeze or deployed
product claim follows. Human UK/new-context review and final submission remain
separate gates.

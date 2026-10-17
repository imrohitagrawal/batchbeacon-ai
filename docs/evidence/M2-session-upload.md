# T09 guest and upload boundary — local increment

Status: **LOCAL / PARTIAL**, 18 October 2026. T09 is not complete. This increment
starts against T05a/T07 contracts; real-service sign-off still depends on T08.
The approved UI and default preparation application are unchanged. No guest,
model or stock-action route was exposed by this work.

## Implemented boundary

`guest_service.py` owns server-issued random guest capabilities, the existing
RetailPolicy session lifetime, one-session/one-shop scope and demo-manager flag.
Only capability hashes enter the repository. Immediate expiry and effective-policy
binding apply to every access, including after slow storage operations return.
Incident creation has atomic allowance checks and idempotent request identities.

`guest_api.py` supplies an explicitly injected **adapter-test application**, not a
production persistence fallback. Deployment-mode cookies use the `__Host-` prefix,
Secure, HttpOnly, SameSite=Strict and no Domain attribute. Mutation checks use an
explicit configured origin plus a capability-bound CSRF token. Request bodies
cannot supply actor, shop, source-review or pool authority. Protected responses
are private/no-store and carry nosniff/referrer restrictions. Errors do not reveal
foreign record existence or storage contents.

`uploads.py` accepts decoded still JPEG/PNG/WebP within the configured limits.
Multipart input is bounded while streaming, including encoding overhead and file
count/bytes. Dimensions and the combined pixel allowance are checked before full
decoding. EXIF orientation is applied; new pixel-only PNG output removes metadata.
Transparent pixels are composited onto a configured white background to preserve
visible label marks. The sanitized output is also byte-bounded. No remote URL,
SVG, archive, PDF or animated image is admitted.

The retained capture hash identifies these exact PNG bytes. Capture reservation
precedes object writes; a ready marker follows successful exact-byte checks.
Object writes are outside retryable metadata transactions. Repeating the same
owned request reconciles its existing IDs; changed payloads conflict. Failed or
unknown writes retain bounded pending records for retry/authorized cleanup. This
is **not an atomic transaction across Firestore and Cloud Storage**. Image reads
recheck ownership, expiry and hash; missing/corrupt evidence gives an unavailable
response. No reusable public or signed image URL bypasses session checks.

## Configuration and acceptance scope

One immutable GuestPolicy binds RetailPolicy and UploadPolicy and has an effective
hash. Initial upload ceilings follow NF-01: two files, 5 MiB/file, 20 MP/file,
24 MP combined. Tighter overrides are tested. Initial engineering choices are
64 KiB total multipart overhead allowance, 1 MiB spool threshold, 30-second body
read deadline, PNG compression level 6, white transparency background and a
three-batch storage allowance per incident. The last is a storage bound; it does
not implement or authorize AI acquisition/recapture counters. Defaults/overrides,
invalid types, nonfinite values and conflicting settings are tested. None of this
configuration supplies cloud, financial or source-review authority.

Independent requirements-first acceptance was derived before this implementation:
23 local cases and seven separate real-service gates. The private source-bound
matrix is under `.local/run-records/`. This increment covers the guest/HTTP/image
parts of S01–05, U01–04, P01–03 and C01–02 with explicit local fakes. Future
observation/result/action/learning namespaces are not tested by the current
incident/capture checks. U05 correction persistence, P04 acquisition/currentness
integration, B01–07 shared paid admission and all R01–07 gates remain pending.

The current tests exercise configured inclusive/one-over bounds and rejection
before inference. Full-size image memory/concurrency on the actual 1 GiB runtime,
deployed HTTPS cookies, Firestore transactions/restarts, private Storage and
actual model consumption remain NOT RUN. Test fakes share storage between service
instances and retry pure callbacks; that is not real multi-instance evidence.

## Reproduced corrections

| Finding | Demonstrated impact / classification | Correction and regression |
| --- | --- | --- |
| Transparent black background became opaque black | Label marks could become invisible; REQUIRED_CONTRACT NF-01 | Configured alpha compositing on a fresh canvas; exact pixel regression failed before and passes after. |
| Unfinished multipart file absent from FormData stayed open | Rejected upload could leave a spool file open; REQUIRED_CONTRACT NF-01 resource boundary | Finally closes the entire parser-created file registry, including incomplete parts. Negative test retained; pinned parser integration covered. |
| Session expired after commit but before response | Guest/incident/capture success response could follow expiry; REQUIRED_CONTRACT NF-02 | Post-storage freshness checks on all three paths; all three negative tests failed before and pass after. Committed records remain available for authorized reconciliation; no false rollback claim. |

Detailed failed and corrected runs remain in the private evidence store. Ordinary
oversize rejection, timeout and parent-task cancellation cleanup were separately
investigated; they are not duplicate findings. Independent correction verification
and final whole-project results are recorded in the checkpoint below.

## Checkpoint

Focused local suite: **60 passed**. Independent technical review reproduced and
verified all three corrections, plus cancellation, timeout and lost-write-response
recovery. No remaining reproduced blocker in this local increment. Full local
locked checks/Ruff, **284 unit tests and 41 Chrome browser tests passed**.
The existing FastAPI/Starlette TestClient deprecation warning remains advisory;
no dependency was changed. Hosted verification of this checkpoint is pending.
Real paid admission remains closed.

Implementation references: [Starlette requests](https://www.starlette.io/requests/)
explains streaming and parser controls; file sizes need their own limits.
[Pillow security](https://pillow.readthedocs.io/en/stable/handbook/security.html)
informs decoder allowlisting and explicit metadata removal. Installed pinned
library code was inspected for cleanup behavior; updates must rerun these tests.

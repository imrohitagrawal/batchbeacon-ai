# BatchBeacon fixed-host proxy

Dedicated Worker `batchbeacon-origin-proxy` serves `batchbeacon.stackclimb.com`.
It uses CaféMesh's fixed-origin architecture, independently implemented with
BatchBeacon's exact-origin, host-only cookie and no-cache requirements.
CaféMesh resources are not modified. No Firebase, load balancer or direct Cloud
Run domain mapping is involved.

Required validated plain-text bindings:

| Binding | Production value |
| --- | --- |
| PUBLIC_ORIGIN | https://batchbeacon.stackclimb.com |
| UPSTREAM_ORIGIN | https://batchbeacon-ai-xotgrrfbcq-el.a.run.app |
| UPSTREAM_TIMEOUT_MS | 60000 |

Upload `worker.mjs` as an ES module, attach the dedicated custom domain, disable
workers.dev/previews, Worker cache and request logging. Cloudflare manages DNS/TLS.
The owner confirmed Workers Free; no subscription or account setting was changed.
Account identifiers, exact deployment receipts and timing remain private.

POST requires the exact public Origin before translation to the fixed upstream
Origin. The backend still validates CSRF, ownership, expiry and paid admission.
Safe GET/HEAD allow absent Origin, but reject any foreign Origin. Incoming Host
must match. Only the app's `__Host-bb_guest` cookie crosses the edge; unrelated
cookies, Authorization and client forwarded headers are removed. Duplicate app
cookies fail closed. Cookies stay Secure, HttpOnly, SameSite=Strict, Path=/ and
without Domain. Sessions are separate between hostnames.

Bodies stream once with no retries or buffering. Upstream redirects fail closed.
All responses use private/no-store; static URLs are versioned. Do not combine
`cache: no-store` with Cloudflare TTL overrides: that combination failed on the
actual runtime. Technical Operations and private resources stay protected.

Run `node --test tests/edge/worker.test.mjs`. Deployed TLS, host/origin matrix,
secure cookies, upload/recovery and a separately admitted real-model journey are
additional gates. Keep the original Cloud Run URL working as the fallback. Do
not prefer the custom hostname in submission links until those gates pass.

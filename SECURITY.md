# Security policy and responsible disclosure

BatchBeacon AI is a **bounded public hackathon demonstration**, not a certified food-safety system, an enterprise-supported SaaS, or a service authorized to change real stock. Public guest access is intentionally limited; records are synthetic and capabilities expire.

## Reporting a potential vulnerability

**Do not disclose exploitable vulnerabilities, session tokens, credentials, cloud resource identifiers, private guest data or reproduction payloads in public GitHub issues, discussions or pull requests.**

Use GitHub's **Report a vulnerability** / private security advisory option **if available for this repository**. Otherwise contact the repository maintainer **privately** through a contact method available on their GitHub profile. If a private channel is unavailable, request one without sharing exploit details. We make no claim of a monitored security inbox or guaranteed response time.

Include a non-sensitive summary, impacted component/revision, reproduction preconditions, potential impact and suggested remediation. For proof, prefer synthetic examples without live guest capabilities or paid public-model calls. Do not test other users' sessions, attempt resource exhaustion, exploit Cloud Run or Cloudflare infrastructure, or download confidential material.

## Scope and known limitations

- The real deployment is a **synthetic, finite-allowance public demo**. See [owner-approved scope](docs/submission/release-scope.md) and [current state](docs/STATE.md).
- Security-relevant controls include request ownership/expiry, CSRF/origin checks, input limits, server-side verification, action deduplication, private image storage and shared model/guest budget reservations. Bounded evidence exists in [the technical proof index](docs/submission/evidence-index.md).
- The existence of controls does not imply penetration testing, production uptime acceptance or complete application telemetry. No safe-to-eat/sell, clinical, regulatory or inventory authorization is provided.
- Source documents and image/model outputs are **untrusted evidence**, not instructions; no model result can independently authorize a simulated action.

Security changes should be reviewed against [specifications](specs/mvp.md), [operations](docs/OPERATIONS.md) and existing tests before deployment. Keep private cloud credentials, project receipts, guest tokens and run policies out of this public repository.

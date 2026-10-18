# BatchBeacon AI

BatchBeacon connects official recall evidence with the product in hand. It helps retail staff inspect a synthetic label, understand the selected notice conditions and deliberately record a simulated hold.

The real historical-SFA journey has run on Google Cloud Run with Gemini through a bounded Google ADK workflow, deterministic verification, explicit checkbox confirmation and Firestore persistence. The owned queue and action survive refresh, including the inspected phone journey. A fresh unauthenticated public browser completed the same real-AI journey; independent accounting and private-boundary checks passed.

**[Try the live prototype](https://batchbeacon.stackclimb.com)** · [Judge guide](docs/submission/judge-guide.md)

See the [architecture and trust boundaries](docs/submission/architecture.md):
C4-style system context, deployed Cloudflare/Cloud Run components, and the
evidence-to-action journey, with editable Mermaid sources. The
[Google technology evidence map](docs/submission/google-technology-evidence.md)
explains each service’s actual role and planned extensions.

## How it works

Gemini proposes label fields. Server rules check identity before lot, date and jurisdiction, preserve uncertainty, enforce session ownership and authorize simulated actions. Firestore retains evidence and actions; private Cloud Storage holds sanitized inputs.

The **retail console** serves staff and demo managers with owned counts/status, missing evidence, resumable cases, actions and capture guidance. **Private BatchBeacon Operations** serves the operator with verified deployment resources, monitoring/dashboard configuration, alert-policy setup and bounded cost oversight. Technical privileges and guest records remain private. Complete application telemetry and observed alert firing/closure are not claimed.

Guidance adaptation changes only allowlisted wording after fixed evaluation and explicit activation. Six cases/nine variants support fixed evaluation; actual deployed activation and rollback at increasing revisions are now verified. Final artifacts must bind the accepted release evidence.

## Scope

The current demonstration uses synthetic labels and selected historical SFA evidence. UK FSA matching remains review-only. No result establishes food safety or permission to consume or sell. No real inventory changes occur. Protected quality evaluation, measured competitor superiority and production economics are not claimed.

The proposed Consumer Recall Explorer adds accessible mobile search by product, brand, country, date and reported hazard, with official actions and affected lots. Planned ATT-01 supplies reviewed notice/PDF imagery; proposed CON-01 uses it for candidate discovery before exact identity/lot confirmation. Neither image extraction nor catalogue visual retrieval is implemented. Frequency needs a time window, declared source coverage and deduplicated events. Reported hazards/allergens/pathogens remain separate from officially confirmed illness reports; counts imply neither disease causation nor brand safety. Consumer discovery and permissioned aggregate insights are future capabilities. See the [roadmap proposal](docs/submission/consumer-recall-explorer-roadmap.md) and
[competitive positioning and stakeholder analysis](docs/submission/competitive-positioning.md).

## Pilot proposal

Compare assisted review with manual lookup on the same reviewed cases. Target metrics are median review time, completion, unsupported actions, evidence completeness and cost per completed investigation. No customer adoption, time savings or harm reduction has been measured.

## Local development

Requires Python 3.12.13 and uv 0.11.18:

```sh
./scripts/bootstrap.sh
./scripts/check.sh
./scripts/start.sh
```

The local visual route is `http://127.0.0.1:8765/prototype/refined/`. It illustrates the approved design and is separate from actual model execution. `BATCHBEACON_LOCAL_PORT` changes its loopback port. Cloud execution needs admitted private configuration and credentials; never commit these.

Explicit browser checks using installed Chrome:

```sh
BATCHBEACON_BROWSER_CHECKS=1 BATCHBEACON_TEST_BROWSER_CHANNEL=chrome ./scripts/check.sh
```

See [judge guide](docs/submission/judge-guide.md), [actual state](docs/STATE.md), [private cloud evidence](docs/evidence/M2-private-cloud-journey.md), [owner decisions](docs/OWNER_DECISIONS.md) and [execution policy](docs/EXECUTION_POLICY.md). Original documents and archived UI directions remain preserved. Current visual approval is distinct from runtime acceptance.

Registered team: **Bugging Debuggers**. The public app is verified; final video/PDF links remain pending. Source/history review found no reproduced disclosure blocker at the application head; final packaging assets are audited separately. The [owner-approved scope](docs/submission/release-scope.md) preserves all remaining limitations.


Verified fallback: https://batchbeacon-ai-xotgrrfbcq-el.a.run.app . Sessions are
separate between hostnames. This demo uses private, expiring guest shops, without
account login/logout or cross-device recovery. Anonymous users can consume the
finite public allowance; exhausted capacity is not automatically replenished.
The deployed source is [04546e09](https://github.com/imrohitagrawal/batchbeacon-ai/tree/04546e0944adfed521efcd3b20e7fa7387c39101).
The hosted narrow-screen failure was corrected and independently verified. The live
release includes a prominent optional five-step guided overlay, actual sample-label
previews, accessible example/source explanations and visible current/future scope. See [correction evidence](docs/evidence/M4-ui-domain-correction.md).

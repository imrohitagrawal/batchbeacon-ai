# Contributing to BatchBeacon AI

Thanks for your interest. This repository was built for **Singapore AI Builder Cup 2026**, and its public documentation distinguishes working prototype functionality from engineering evidence and future product proposals.

## Before proposing a change

1. Read the [README](README.md), [scope](docs/submission/release-scope.md), [current release state](docs/STATE.md) and [canonical document map](docs/INDEX.md). Do not edit the archived original hackathon brief, engineering contract, registered roster or source-review evidence merely to simplify presentation.
2. Open an issue for an externally proposed enhancement, describing the observed need and testable outcome. A feature request or pull request is not authorization to change cloud resources, paid model execution, public deployments or submission material.
3. Use a feature branch and focused pull request with **what changed / why / test evidence / risk / release impact**. Preserve source and notice provenance, privacy boundaries and the distinction between demonstrated and planned features.
4. For local code changes use Python 3.12.13 and uv 0.11.18, run `./scripts/bootstrap.sh` and `./scripts/check.sh`, and optionally run browser checks per the [README](README.md#run-and-check-locally). An offline check does **not** establish real-service, production or protected model-quality acceptance.
5. For diagrams, update the **Mermaid source, rendered Markdown and any associated SVG** together. Keep context, deployment, code components and future/operational boundaries consistent. Update the [evidence index](docs/submission/evidence-index.md) only when supported by actual code or retained test evidence.
6. Never commit private `.local/`, `.batchbeacon/`, `runtime-assets/`, secrets, tokens, live session data, account numbers or personal contact information. For potential vulnerabilities follow [SECURITY.md](SECURITY.md), not a public issue.

## Rights and upstream dependencies

No root-level license for the project's original source has yet been declared. **A public repository is not automatically an open-source software license.** Request clarification from the owner before copying, distributing or relicensing original project code. Bundled third-party tools, assets and references have their own licenses and provenance; preserve them.

The maintainer may decline, postpone or request changes to contributions during submission freeze or where additional source rights, risk approval or deployed evidence would be required.

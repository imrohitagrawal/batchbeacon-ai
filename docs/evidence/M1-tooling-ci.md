# Local bootstrap and CI preparation

Python 3.12.13; uv 0.11.18; project-local `.venv` installed using
`uv sync --frozen --no-build --python 3.12.13`. All 70 installed distributions
came from wheels; no source build/global installation or lifecycle hook ran.
The only installed `.pth` is uv's `_virtualenv` startup file.

Exact direct dependencies and transitive hashes are in pyproject.toml / uv.lock.
FastAPI 0.143.3's OpenTelemetry minimum conflicts with ADK 2.12.0's maximum;
the solver selected and we pinned FastAPI 0.141.1 with OpenTelemetry 1.42.1.
ADK, FastAPI, Pydantic, Firestore, Storage and pytest imports succeeded. Actual
LlmAgent/Runner/session API signatures were inspected; no model request ran.
No ADK extras or alternate lifecycle were installed.

`scripts/bootstrap.sh` is idempotent locked wheel-only setup.
`scripts/start.sh` serves a local-only preparation shell on loopback, with a
configurable port. Health explicitly says product NOT READY. Prototype routes
have no persistence or paid endpoint. Cloud deployment remains gated separately.
`scripts/check.sh` checks lock, Ruff, backend tests and explicitly selected browser
tests; it reports unrun service/model/release checks rather than hiding skips.

Actual initial checks: lock PASS, Ruff PASS, 2 preparation tests PASS.
Starlette's httpx deprecation warning is advisory; current tests pass. Browser
regressions and hosted exact commands are recorded separately as they run.

CI skeleton uses SHA-pinned checkout/setup-python with contents:read, no checkout
credential persistence, no cloud secrets, push and pull_request events. Both
tag refs were confirmed to point to commits. It installs the locked Chromium
runtime and runs the same check command. No hosted run is claimed yet. Direct-head
and merge-checkout topology plus deliberate red/green gate remain release work.

Skill admission is in docs/SKILLS.md. Dependencies do not grant spend or source
approval. Application domain/ADK integration, real Firestore, public security
and budget enforcement remain NOT IMPLEMENTED / NOT RUN.

Actual browser command: `BATCHBEACON_TEST_BROWSER_CHANNEL=chrome
BATCHBEACON_BROWSER_CHECKS=1 ./scripts/check.sh`: lock/Ruff, 2 backend and 4
local real-browser prototype regressions PASS. The initial run had 3/4 PASS;
a desktop-only count in the test's mobile navigation name caused a locator timeout.
The test now scopes the accessible queue name to navigation across breakpoints.
Browser cases cover UK incident/source binding, explicit hold confirmation, valid
guidance baseline/visible future preview/monotonic rollback, phone reflow and queue
semantics. These remain prototype checks, not B-F1–F6 or actual learning evaluation.

# BatchBeacon AI

Source-scoped recall evidence for a synthetic retailer workflow. **Preparation in
progress — not a deployed product or a food-safety decision service.**

The approved product combines SFA Singapore and UK FSA notices, actual bounded
Gemini/ADK extraction, deterministic comparison, human-confirmed simulated actions,
an isolated shop queue and evaluated capture-guidance changes. Pure verification
and retailer/guidance contracts have local test coverage; the runtime integrations
are not yet implemented. See [current state](docs/STATE.md).

## Local preparation

Requires Python 3.12.13 and uv 0.11.18. No cloud credential is needed for the
current visual prototype. The scripts install only locked wheels in `.venv`.

```sh
./scripts/bootstrap.sh
./scripts/check.sh
./scripts/start.sh
```

Open `http://127.0.0.1:8765/prototype/refined/` for the current visual candidate.
The [desktop/phone review set](docs/evidence/M1-final-visual-review.md) records its
checks and limitations. The earlier `/prototype/` treatment remains archived.
This local prototype makes no model call,
uploads nothing and saves no action. Health reports product `not_ready`.
Use `BATCHBEACON_LOCAL_PORT` to change its loopback port.

For the explicit prototype browser regressions:

```sh
uv run --frozen --no-build playwright install chromium
BATCHBEACON_BROWSER_CHECKS=1 ./scripts/check.sh
```

An installed Chrome can be selected with `BATCHBEACON_TEST_BROWSER_CHANNEL=chrome`.
These tests do not prove hosted product journeys, Firestore, model behavior or
release safety. Private settings and run records remain ignored and untracked.

## Evidence and decisions

- [Original brief](HACKATHON_BRIEF.md) and [master prompt](HACKATHON_CODEX_MASTER_PROMPT.md)
- [Owner decisions](docs/OWNER_DECISIONS.md) and [execution policy](docs/EXECUTION_POLICY.md)
- [Acceptance design](docs/evidence/M1-acceptance-design.md)
- [Human source-review packet](docs/evidence/M1-source-review.md)
- [Skill provenance and permitted mode](docs/SKILLS.md)

Fresh synthetic labels are explicitly marked. Only minimal factual notice fields
and source links are published; no authority logos, original pages or manufacturer
photos are bundled. Third-party skill licenses and attribution are retained in
their individual directories. All three earlier UI directions remain historical
selection evidence; final replacement design approval is still required.

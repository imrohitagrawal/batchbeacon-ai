# Hosted contract and prototype-browser checks

Status: PASS for the observed CI scope. No release freeze or integrated product
acceptance is claimed. This supersedes the hosted-pending observation in
[M1-tooling-ci](M1-tooling-ci.md).

The owner-authorized repository now exists publicly at
[imrohitagrawal/batchbeacon-ai](https://github.com/imrohitagrawal/batchbeacon-ai).
Source/history/media publication checks preceded creation and push. Private local
configuration and run records remain ignored and untracked. README-only
[PR #1](https://github.com/imrohitagrawal/batchbeacon-ai/pull/1) was merged through
the ordinary route after its checks passed; no protection or security setting changed.

| Event | Actual checkout | Hosted result |
| --- | --- | --- |
| Main push | `dc814629effdd5f39000b5b0c53cce5c3f148e12` | [PASS](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39072175163) |
| Branch push | `de4729dd565cb153cbadde5cecfb44c73683a547` | [PASS](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39072297875) |
| Pull request | `04138068916325a4663897f1b5e77fa685915cc9`, `refs/pull/1/merge` | [PASS](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39072321371) |
| Merged main push | `ffc6cd9cc50589fdf0ae659820720ae6ff93a752` | [PASS](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39072497127) |

Each run passed lock validation, Ruff, 118 unit tests and 36 browser tests. An
independent read-only reviewer reproduced the live logs, checkout SHAs, parent
relationship and identical PR-merge/final-merge trees. The review also confirmed
that the workflow was unchanged across these revisions.

## Hosted boundary actually exercised

- Ubuntu 24 runner, Python 3.12.13 from `.python-version`, uv 0.11.18.
- SHA-pinned checkout/setup-python; checkout credential persistence disabled;
  authentication removed before dependency setup. Effective token permissions
  contents:read and metadata:read.
- `python -m pip install uv==0.11.18`, then `./scripts/bootstrap.sh`: frozen
  wheel-only installation of the 70 locked packages.
- `uv run --frozen --no-build playwright install --with-deps chromium`.
- `BATCHBEACON_BROWSER_CHECKS=1 ./scripts/check.sh`: full unit and browser
  directories executed, bundled Chromium selected, no installed-Chrome override.
- Same `local-contracts` check context on push and pull_request; no cloud secrets,
  model request, deployment or service acceptance embedded in this workflow.

GitHub’s separate dependency-graph workflow also passed with read-only token
permissions. Dependency metadata referring to cloud packages is not cloud execution.

## Remaining release obligations

Main currently has no enforced required checks or rulesets. An observed green
check is not an enforced merge gate. Deliberate red/green enforcement remains
unproven and must be addressed within the existing authority before release.
The palette/control-spacing delta was developed after the four SHAs above and
passed its own [hosted push run](https://github.com/imrohitagrawal/batchbeacon-ai/actions/runs/39073205613)
at `26a451ae2f199f798e71e8f26b3d68a79d28a3aa`: lock/Ruff, 118 unit and
36 bundled-Chromium browser tests passed. Exact run logs were checked against
that checkout. Later documentation-only checkpoints do not imply a release freeze. Real model/service integration, security, persistent
allowances, all six hosted product journeys and final validation remain separate.

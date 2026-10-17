#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
uv lock --check
uv run --frozen --no-build ruff check src tests
uv run --frozen --no-build pytest tests/unit
if [[ "${BATCHBEACON_BROWSER_CHECKS:-0}" == 1 ]]; then
  uv run --frozen --no-build pytest tests/browser
else
  echo 'Browser checks NOT RUN: set BATCHBEACON_BROWSER_CHECKS=1 after browser installation.'
fi
echo 'Real model, Firestore, hosted journeys and release gates are separate; this command does not pass them.'

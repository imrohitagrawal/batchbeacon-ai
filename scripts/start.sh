#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Local preparation only. Cloud activation requires the later typed runtime policy.
exec uv run --frozen --no-build uvicorn batchbeacon.app:app --app-dir src \
  --host 127.0.0.1 --port "${BATCHBEACON_LOCAL_PORT:-8765}" --no-proxy-headers

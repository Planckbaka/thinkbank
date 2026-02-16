#!/usr/bin/env bash
# Run web-ui dev server on host, pointing to host backend.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8080}"
WEB_PORT="${WEB_PORT:-5173}"
export VITE_API_URL="${VITE_API_URL:-http://127.0.0.1:${BACKEND_PORT}}"

cd web-ui
exec npm run dev -- --host 0.0.0.0 --port "${WEB_PORT}"

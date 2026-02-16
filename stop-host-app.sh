#!/usr/bin/env bash
# Stop host-mode background services started by start-host-app.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

stop_one() {
  local name="$1"
  local pid_file="logs/${name}.pid"

  if [[ ! -f "${pid_file}" ]]; then
    echo "[skip] ${name} pid file not found"
    return
  fi

  local pid
  pid="$(cat "${pid_file}")"
  if [[ -z "${pid}" ]]; then
    echo "[skip] ${name} pid file empty"
    rm -f "${pid_file}"
    return
  fi

  if kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" || true
    echo "[ok] ${name} stopped (pid=${pid})"
  else
    echo "[skip] ${name} not running (stale pid=${pid})"
  fi

  rm -f "${pid_file}"
}

stop_one "web-host"
stop_one "backend-host"
stop_one "ai-worker-host"
stop_one "ai-host"
stop_one "ai-embed-host"
stop_one "vllm-host"

echo "Ensuring no stray processes..."
pkill -f "python3 server.py" || true
pkill -f "python3 embed_server.py" || true
pkill -f "python3 -m workers.asset_processor" || true
pkill -f "vite" || true
pkill -f "thinkbank/backend/cmd" || true

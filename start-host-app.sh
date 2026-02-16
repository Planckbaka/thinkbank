#!/usr/bin/env bash
# Start host-mode services in background:
# - vLLM
# - Python AI gRPC service
# - Python AI Redis worker
# - Go backend
# - Web UI (Vite)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

mkdir -p logs

start_one() {
  local name="$1"
  local cmd="$2"
  local pid_file="logs/${name}.pid"
  local log_file="logs/${name}.log"

  if [[ -f "${pid_file}" ]]; then
    local old_pid
    old_pid="$(cat "${pid_file}")"
    if [[ -n "${old_pid}" ]] && kill -0 "${old_pid}" 2>/dev/null; then
      echo "[skip] ${name} already running (pid=${old_pid})"
      return
    fi
  fi

  nohup bash -lc "${cmd}" > "${log_file}" 2>&1 &
  local pid=$!
  echo "${pid}" > "${pid_file}"
  echo "[ok] ${name} started (pid=${pid})"
}

start_one "vllm-host" "./run-vllm-host.sh"
start_one "ai-embed-host" "./run-ai-embed-host.sh"
start_one "ai-host" "./run-ai-host.sh"
start_one "ai-worker-host" "./run-ai-worker-host.sh"
start_one "backend-host" "./run-backend-host.sh"
start_one "web-host" "./run-web-host.sh"

echo
echo "Logs:"
echo "  logs/vllm-host.log"
echo "  logs/ai-embed-host.log"
echo "  logs/ai-host.log"
echo "  logs/ai-worker-host.log"
echo "  logs/backend-host.log"
echo "  logs/web-host.log"

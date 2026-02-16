#!/usr/bin/env bash
# Run Python AI Embed HTTP service on host

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi

if [[ -f python-ai/.env ]]; then
  set -a
  source python-ai/.env
  set +a
fi

# Same env vars as AI host
export HF_HOME="${HF_HOME:-${ROOT_DIR}/.hf-cache}"
export AI_GRPC_PORT="${AI_GRPC_PORT:-50051}"
# Embed server port different from GRPC
export AI_EMBED_PORT="${AI_EMBED_PORT:-50052}"

cd python-ai

if [[ -x "${ROOT_DIR}/.venv-ai/bin/python" ]]; then
  exec "${ROOT_DIR}/.venv-ai/bin/python" embed_server.py
fi

exec python3 embed_server.py

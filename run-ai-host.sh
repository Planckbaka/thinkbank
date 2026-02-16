#!/usr/bin/env bash
# Run Python AI gRPC service on host, connecting to Dockerized infrastructure
# and host vLLM endpoint.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if [[ -f python-ai/.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source python-ai/.env
  set +a
fi

HF_HOME="${HF_HOME:-${ROOT_DIR}/.hf-cache}"
mkdir -p "${HF_HOME}"
export HF_HOME
export HUGGINGFACE_HUB_CACHE="${HF_HOME}/hub"
export TRANSFORMERS_CACHE="${HF_HOME}/transformers"

export DB_HOST="${DB_HOST:-127.0.0.1}"
export DB_PORT="${DB_PORT:-${POSTGRES_PORT:-5432}}"
export DB_USER="${DB_USER:-${POSTGRES_USER:-thinkbank}}"
export DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-thinkbank123}}"
export DB_NAME="${DB_NAME:-${POSTGRES_DB:-thinkbank}}"

export REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
export REDIS_PORT="${REDIS_PORT:-6379}"

export MINIO_ENDPOINT="${MINIO_ENDPOINT:-127.0.0.1:${MINIO_API_PORT:-9000}}"
export MINIO_USER="${MINIO_USER:-minioadmin}"
export MINIO_PASSWORD="${MINIO_PASSWORD:-minioadmin123}"

export AI_GRPC_PORT="${AI_GRPC_PORT:-50051}"
export LLM_API_URL="${LLM_API_URL:-http://127.0.0.1:${LLM_PORT:-8000}/v1}"
export LLM_API_KEY="${LLM_API_KEY:-sk-local}"

cd python-ai

if [[ -x "${ROOT_DIR}/.venv-ai/bin/python" ]]; then
  exec "${ROOT_DIR}/.venv-ai/bin/python" server.py
fi

exec python3 server.py

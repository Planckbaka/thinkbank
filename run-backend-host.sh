#!/usr/bin/env bash
# Run Go backend on host, connecting to Dockerized infrastructure.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

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

export AI_SERVICE_HOST="${AI_SERVICE_HOST:-127.0.0.1}"
export AI_SERVICE_PORT="${AI_SERVICE_PORT:-${AI_GRPC_PORT:-50051}}"
export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:5173,http://127.0.0.1:5173}"

cd go-backend
exec env -u GOROOT go run .

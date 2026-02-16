#!/bin/bash
# ThinkBank Infrastructure Startup Script
# Run this script with: sudo ./start-infra.sh

set -e

echo "=== ThinkBank Infrastructure Startup ==="

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Load .env values for health checks and output
set -a
# shellcheck disable=SC1091
source .env
set +a

POSTGRES_PORT="${POSTGRES_PORT:-5432}"
REDIS_PORT="${REDIS_PORT:-6379}"
MINIO_API_PORT="${MINIO_API_PORT:-9000}"
MINIO_CONSOLE_PORT="${MINIO_CONSOLE_PORT:-9001}"
POSTGRES_USER="${POSTGRES_USER:-thinkbank}"
POSTGRES_DB="${POSTGRES_DB:-thinkbank}"

# Create MinIO bucket initialization
echo "Starting infrastructure services..."
docker compose up -d postgres redis minio

echo ""
echo "Waiting for services to be healthy..."
sleep 5

# Check service health
echo ""
echo "=== Service Status ==="
docker compose ps

echo ""
echo "=== Health Checks ==="
echo "PostgreSQL:"
docker compose exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" || echo "Still starting..."

echo "Redis:"
docker compose exec -T redis redis-cli ping || echo "Still starting..."

echo "MinIO:"
curl -s "http://localhost:${MINIO_API_PORT}/minio/health/live" || echo "Still starting..."

echo ""
echo "=== Infrastructure Ready ==="
echo "PostgreSQL: localhost:${POSTGRES_PORT}"
echo "Redis: localhost:${REDIS_PORT}"
echo "MinIO API: http://localhost:${MINIO_API_PORT}"
echo "MinIO Console: http://localhost:${MINIO_CONSOLE_PORT} (${MINIO_USER:-minioadmin} / ${MINIO_PASSWORD:-minioadmin123})"
echo ""
echo "To stop services: docker compose down"
echo "To view logs: docker compose logs -f"

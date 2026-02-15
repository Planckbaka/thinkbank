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
docker compose exec -T postgres pg_isready -U thinkbank || echo "Still starting..."

echo "Redis:"
docker compose exec -T redis redis-cli ping || echo "Still starting..."

echo "MinIO:"
curl -s http://localhost:9000/minio/health/live || echo "Still starting..."

echo ""
echo "=== Infrastructure Ready ==="
echo "PostgreSQL: localhost:5432"
echo "Redis: localhost:6379"
echo "MinIO API: http://localhost:9000"
echo "MinIO Console: http://localhost:9001 (minioadmin / minioadmin123)"
echo ""
echo "To stop services: docker compose down"
echo "To view logs: docker compose logs -f"

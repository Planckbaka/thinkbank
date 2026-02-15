#!/bin/bash
# ThinkBank Infrastructure Stop Script

echo "Stopping ThinkBank infrastructure services..."
docker compose down

echo ""
echo "To remove data volumes as well, run:"
echo "  docker compose down -v"

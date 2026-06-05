#!/bin/bash
# Full deploy on CloudPanel (run from repo root).
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Pulling latest code ==="
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Stashing local changes before pull..."
  git stash push -u -m "server-deploy-$(date +%Y%m%d%H%M%S)"
fi
git pull origin main

echo "=== Stopping old containers ==="
docker compose down --remove-orphans

echo "=== Pruning unused Docker images ==="
docker image prune -f

echo "=== Building and starting ==="
docker compose up -d --build

echo "=== Waiting for backend to start ==="
sleep 10

echo "=== Running migrations ==="
docker compose exec backend alembic upgrade head

echo "=== Seeding database ==="
docker compose exec backend python -m app.seed

echo ""
echo "=== Done. Running containers: ==="
docker compose ps
echo ""
docker compose logs backend --tail 10

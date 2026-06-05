#!/bin/bash
# Full prod deploy on CloudPanel / same-host MySQL (run from repo root).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

chmod +x scripts/server-setup-env.sh scripts/server-fix-docker-build.sh 2>/dev/null || true

git pull origin main

./scripts/server-setup-env.sh --force --cloudpanel

COMPOSE_FILES=(-f docker-compose.yml -f docker-compose.cloudpanel.yml)
docker compose "${COMPOSE_FILES[@]}" --profile prod up -d --build --force-recreate

echo "Waiting for backend..."
sleep 8
docker compose "${COMPOSE_FILES[@]}" exec backend alembic upgrade head
docker compose "${COMPOSE_FILES[@]}" exec backend python -m app.seed

echo "Done."
docker compose "${COMPOSE_FILES[@]}" ps
docker compose "${COMPOSE_FILES[@]}" logs backend --tail 15

#!/bin/bash
# Full prod deploy helper (run on server from repo root).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

chmod +x scripts/server-setup-env.sh scripts/server-fix-docker-build.sh 2>/dev/null || true

if [[ ! -f .env ]]; then
  ./scripts/server-setup-env.sh
fi

git pull origin main

docker compose --profile prod up -d --build --force-recreate

echo "Waiting for backend..."
sleep 5
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed

echo "Done. Check: docker compose ps && docker compose logs backend --tail 20"

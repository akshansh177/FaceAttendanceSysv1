#!/bin/bash
# Full prod deploy on CloudPanel / same-host MySQL (run from repo root).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

chmod +x scripts/server-setup-env.sh scripts/server-fix-docker-build.sh 2>/dev/null || true

git pull origin main

./scripts/server-setup-env.sh --force --cloudpanel

chmod +x scripts/compose-prod.sh
./scripts/compose-prod.sh up -d --build --force-recreate

echo "Waiting for backend..."
sleep 8
./scripts/compose-prod.sh exec backend alembic upgrade head
./scripts/compose-prod.sh exec backend python -m app.seed

echo "Done. Running containers:"
./scripts/compose-prod.sh ps
./scripts/compose-prod.sh logs backend --tail 15

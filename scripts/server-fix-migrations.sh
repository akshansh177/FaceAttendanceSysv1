#!/bin/bash
# Fix Alembic %23 password error and run migrations (run from repo root on server).
set -euo pipefail
cd "$(dirname "$0")/.."

REPO="akshansh177/FaceAttendanceSysv1"
BRANCH="main"
BASE="https://raw.githubusercontent.com/${REPO}/${BRANCH}"

echo "=== Syncing alembic/env.py ==="
if git diff --quiet apps/backend/alembic/env.py 2>/dev/null && git pull origin main 2>/dev/null; then
  echo "git pull OK"
else
  echo "git pull failed or local changes — fetching env.py from GitHub..."
  git stash push -u -m "server-fix-$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
  curl -fsSL "${BASE}/apps/backend/alembic/env.py" -o apps/backend/alembic/env.py
fi

if grep -q "set_main_option" apps/backend/alembic/env.py; then
  echo "ERROR: env.py still has old set_main_option. Aborting."
  exit 1
fi
echo "alembic/env.py OK"

echo "=== Rebuilding backend ==="
docker compose build --no-cache backend
docker compose up -d backend

echo "=== Waiting for backend ==="
sleep 10

echo "=== Running migrations ==="
docker compose exec backend alembic upgrade head

echo "=== Seeding ==="
docker compose exec backend python -m app.seed

echo "=== Done ==="
docker compose ps

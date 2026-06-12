#!/bin/bash
# One-time local dev setup (venvs + deps + optional Redis).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Backend venv ==="
cd apps/backend
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd "$ROOT"

echo "=== Recognition venv ==="
cd apps/recognition-service
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd "$ROOT"

echo "=== Frontend deps ==="
cd apps/frontend
npm install
if [[ ! -f .env.local ]]; then
  cp .env.local.example .env.local
  echo "Created apps/frontend/.env.local"
fi
cd "$ROOT"

echo "=== Backend .env ==="
if [[ ! -f apps/backend/.env ]]; then
  cp apps/backend/.env.example apps/backend/.env
  echo "Created apps/backend/.env — edit DATABASE_URL before running migrations"
fi

echo "=== Redis (optional, for background jobs) ==="
docker compose -f docker-compose.dev.yml up -d 2>/dev/null || echo "Skip Redis if Docker not running"

echo ""
echo "Done. Start dev servers in 3 terminals:"
echo "  ./scripts/dev-backend.sh"
echo "  ./scripts/dev-recognition.sh"
echo "  ./scripts/dev-frontend.sh"

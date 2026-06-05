#!/bin/bash
# Create or fix repo root .env for Docker prod from apps/backend/.env (run on server).
# Usage: ./scripts/server-setup-env.sh [--force] [--cloudpanel]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

BACKEND_ENV="$REPO_ROOT/apps/backend/.env"
ROOT_ENV="$REPO_ROOT/.env"
FORCE=false
CLOUDPANEL=false

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --cloudpanel) CLOUDPANEL=true ;;
  esac
done

if [[ ! -f "$BACKEND_ENV" ]]; then
  echo "ERROR: $BACKEND_ENV not found. Copy .env.example and edit MySQL credentials first."
  exit 1
fi

# shellcheck disable=SC1090
source "$BACKEND_ENV"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL missing in $BACKEND_ENV"
  exit 1
fi

docker_url="${DATABASE_URL_DOCKER:-}"
docker_sync="${DATABASE_URL_SYNC_DOCKER:-}"

if [[ "$CLOUDPANEL" == true ]]; then
  docker_url="$DATABASE_URL"
  docker_sync="${DATABASE_URL_SYNC:-$DATABASE_URL}"
  echo "CloudPanel mode: using localhost MySQL (with docker-compose.cloudpanel.yml)"
else
  if [[ -z "$docker_url" ]]; then
    docker_url="${DATABASE_URL/@localhost:/@host.docker.internal:}"
    docker_sync="${DATABASE_URL_SYNC/@localhost:/@host.docker.internal:}"
  fi
fi

set_env_var() {
  local key="$1" val="$2" file="$3"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    sed -i "s|^${key}=.*|${key}=${val}|" "$file"
  else
    echo "${key}=${val}" >>"$file"
  fi
}

if [[ -f "$ROOT_ENV" && "$FORCE" != true && "$CLOUDPANEL" != true ]]; then
  echo "Root .env exists. Run with --force to update DB URLs from apps/backend/.env"
  echo "  DATABASE_URL_DOCKER=$docker_url"
  exit 0
fi

if [[ ! -f "$ROOT_ENV" ]]; then
  cp .env.example "$ROOT_ENV"
  echo "Created $ROOT_ENV from .env.example"
fi

set_env_var DATABASE_URL "$DATABASE_URL" "$ROOT_ENV"
set_env_var DATABASE_URL_SYNC "${DATABASE_URL_SYNC:-}" "$ROOT_ENV"
set_env_var DATABASE_URL_DOCKER "$docker_url" "$ROOT_ENV"
set_env_var DATABASE_URL_SYNC_DOCKER "$docker_sync" "$ROOT_ENV"
set_env_var REDIS_URL "redis://redis:6379/0" "$ROOT_ENV"
set_env_var RECOGNITION_SERVICE_URL "http://recognition:6003" "$ROOT_ENV"
set_env_var NEXT_PUBLIC_API_URL "https://attendance.akshanshconsultancy.com" "$ROOT_ENV"
set_env_var CORS_ORIGINS "https://attendance.akshanshconsultancy.com" "$ROOT_ENV"

if [[ "$CLOUDPANEL" == true ]]; then
  set_env_var DOCKER_USE_HOST_NETWORK "true" "$ROOT_ENV"
  set_env_var REDIS_URL "redis://127.0.0.1:6379/0" "$ROOT_ENV"
  set_env_var RECOGNITION_SERVICE_URL "http://127.0.0.1:6003" "$ROOT_ENV"
  echo ""
  echo "CloudPanel: use host Redis/Nginx — no docker redis or nginx containers."
  echo "Add vhost from docker/cloudpanel/vhost.conf.example in CloudPanel."
fi

echo "Updated $ROOT_ENV"
echo "  DATABASE_URL_DOCKER=$docker_url"
grep -E '^JWT_SECRET=|^DATABASE_URL_DOCKER=' "$ROOT_ENV" | head -2
echo ""
echo "Next:"
if [[ "$CLOUDPANEL" == true ]]; then
  echo "  docker compose -f docker-compose.yml -f docker-compose.cloudpanel.yml --profile prod up -d --force-recreate"
else
  echo "  docker compose --profile prod up -d --force-recreate"
fi
echo "  docker compose exec backend alembic upgrade head"
echo "  docker compose exec backend python -m app.seed"

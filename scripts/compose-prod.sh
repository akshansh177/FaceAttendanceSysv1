#!/bin/bash
# CloudPanel prod compose helper (repo root).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec docker compose -f "$REPO_ROOT/docker-compose.yml" -f "$REPO_ROOT/docker-compose.cloudpanel.yml" --profile prod "$@"

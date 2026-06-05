#!/bin/bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec docker compose -f "$REPO_ROOT/docker-compose.yml" "$@"

#!/bin/bash
set -euo pipefail

if [ -z "${1:-}" ]; then
  echo "Usage: $0 <backup.sql>"
  exit 1
fi

docker compose exec -T mysql mysql -u attendance -pattendance attendance < "$1"
echo "Restore complete from $1"

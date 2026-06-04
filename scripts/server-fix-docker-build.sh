#!/bin/bash
# Run on the production server inside the repo root if git pull failed or build uses old files.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> Fetching latest recognition Docker files from GitHub..."
BASE="https://raw.githubusercontent.com/akshansh177/FaceAttendanceSysv1/main"
curl -fsSL "$BASE/apps/recognition-service/Dockerfile" -o apps/recognition-service/Dockerfile
curl -fsSL "$BASE/apps/recognition-service/requirements.txt" -o apps/recognition-service/requirements.txt
curl -fsSL "$BASE/apps/recognition-service/.dockerignore" -o apps/recognition-service/.dockerignore
curl -fsSL "$BASE/apps/frontend/.dockerignore" -o apps/frontend/.dockerignore
curl -fsSL "$BASE/apps/frontend/Dockerfile" -o apps/frontend/Dockerfile

echo "==> Recognition Dockerfile (first lines):"
head -5 apps/recognition-service/Dockerfile

if ! grep -q "build-essential" apps/recognition-service/Dockerfile; then
  echo "ERROR: Dockerfile still missing build-essential. Check network or repo URL."
  exit 1
fi

if grep -q "deepface" apps/recognition-service/requirements.txt; then
  echo "ERROR: requirements.txt still lists deepface."
  exit 1
fi

echo "==> Rebuild recognition (no cache)..."
docker compose build --no-cache recognition

echo "==> Rebuild full prod stack..."
docker compose --profile prod up -d --build

echo "Done."

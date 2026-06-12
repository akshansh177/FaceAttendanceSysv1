#!/bin/bash
# Run Next.js frontend locally (port 6001).
set -euo pipefail
cd "$(dirname "$0")/../apps/frontend"
export NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:6002}"
echo "Starting frontend at http://localhost:6001 (API: $NEXT_PUBLIC_API_URL)"
exec npm run dev

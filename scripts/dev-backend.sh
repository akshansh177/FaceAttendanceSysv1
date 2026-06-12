#!/bin/bash
# Run backend API locally (port 6002). Uses apps/backend/.venv — not conda base.
set -euo pipefail
cd "$(dirname "$0")/../apps/backend"

if [[ ! -d .venv ]]; then
  echo "Run ./scripts/dev-setup.sh first"
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import apscheduler" 2>/dev/null; then
  echo "Installing backend dependencies..."
  pip install -r requirements.txt
fi

if lsof -i :6002 -sTCP:LISTEN -t >/dev/null 2>&1; then
  pid=$(lsof -i :6002 -sTCP:LISTEN -t | head -1)
  echo "Port 6002 in use (PID $pid). Kill it: kill $pid"
  exit 1
fi

echo "Starting backend at http://127.0.0.1:6002"
echo "Python: $(which python)"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 6002

#!/bin/bash
# Run recognition service locally (port 6003). Uses apps/recognition-service/.venv.
set -euo pipefail
cd "$(dirname "$0")/../apps/recognition-service"

if [[ ! -d .venv ]]; then
  echo "Creating virtualenv..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! python -c "import insightface" 2>/dev/null; then
  echo "Installing recognition dependencies (may take a few minutes)..."
  pip install -r requirements.txt
fi

echo "Starting recognition at http://127.0.0.1:6003 (Python: $(which python))"
exec uvicorn app.main:app --reload --host 127.0.0.1 --port 6003

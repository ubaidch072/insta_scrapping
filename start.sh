#!/usr/bin/env bash
set -euo pipefail

# Render me kabhi kabhi storage_state.json nahi hota.
# Agar missing ho to ek empty JSON create kar do taake error na aaye.
if [ ! -f "/app/storage_state.json" ]; then
  echo '{}' > /app/storage_state.json
fi

PORT="${PORT:-10000}"
WORKERS="${UVICORN_WORKERS:-1}"

# Run API
exec uvicorn app.webapi:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"

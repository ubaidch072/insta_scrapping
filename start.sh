#!/usr/bin/env bash
set -euo pipefail

# bring in the IG session if present as a Secret File
if [ -f "/etc/secrets/storage_state.json" ]; then
  cp /etc/secrets/storage_state.json /app/storage_state.json
  echo "[start] Copied storage_state.json from secrets."
else
  echo "[start] No secret storage_state.json found; proceeding if local file exists."
fi

# default PORT if Render doesn't inject (local docker runs)
: "${PORT:=10000}"
echo "[start] Launching uvicorn app.webapi:app on ${PORT}"

# launch API
exec uvicorn app.webapi:app --host 0.0.0.0 --port "${PORT}"

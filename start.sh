#!/usr/bin/env bash
set -euo pipefail

if [ -f "/etc/secrets/storage_state.json" ]; then
  cp /etc/secrets/storage_state.json /app/storage_state.json
  echo "[start] Copied storage_state.json from secrets."
else
  echo "[start] No secret storage_state.json found; proceeding if local file exists."
fi

: "${PORT:=10000}"
echo "[start] Launching uvicorn app.webapi:app on ${PORT}"
exec uvicorn app.webapi:app --host 0.0.0.0 --port "${PORT}"

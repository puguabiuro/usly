#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
export PYTHONUNBUFFERED=1

# Load .env if present (local/dev convenience; Render uses env vars in dashboard)
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

venv/bin/alembic -c alembic.ini upgrade head

exec venv/bin/uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"

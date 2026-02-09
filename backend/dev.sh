#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export PYTHONUNBUFFERED=1

# Always use the local venv
if [ ! -x ".venv/bin/python" ]; then
  echo "ERROR: backend/.venv not found. Create it first."
  exit 1
fi

# Load .env if present (optional)
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

exec .venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port "${PORT:-8000}"

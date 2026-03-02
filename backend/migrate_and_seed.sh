#!/usr/bin/env bash
set -euo pipefail

# Load env vars from .env (local dev)
if [ -f ".env" ]; then
  set -a
  source .env
  set +a
fi

./.venv/bin/alembic upgrade head
./.venv/bin/python seed.py

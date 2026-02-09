#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Load .env if present (optional)
if [ -f ".env" ]; then
  set -a
  source ".env"
  set +a
fi

DB_FILE="usly.db"

echo "== Reset database (SQLite) =="

if [ -f "$DB_FILE" ]; then
  rm -f "$DB_FILE"
  echo "Removed $DB_FILE"
else
  echo "No $DB_FILE to remove"
fi

echo "== Create tables (create_all) =="
.venv/bin/python create_tables.py

echo "== Seed test data =="
.venv/bin/python seed.py

echo "DONE ✅"

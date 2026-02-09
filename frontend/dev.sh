#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PORT=${PORT:-5173}

echo "Frontend running at http://localhost:$PORT"
python3 -m http.server "$PORT"

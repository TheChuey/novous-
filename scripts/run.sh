#!/usr/bin/env bash
#
# Start the web app from the repository-root virtual environment.
#
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
else
    PYTHON="python3"
fi

echo "Starting web app at http://127.0.0.1:8000"
echo "To stop: press Ctrl+C"
echo

"$PYTHON" "$PROJECT_ROOT/server.py"

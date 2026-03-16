#!/bin/bash
set -e

VENV=".venv_terminal"

if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment..."
  python3 -m venv "$VENV"
fi

source "$VENV/bin/activate"
echo "Installing dependencies..."
pip install -q -r terminal/requirements.txt

PORT="${PORT:-8765}"
TOKEN="${MY_TERMINAL_TOKEN:-changeme}"

if [ "$TOKEN" = "changeme" ]; then
  echo ""
  echo "⚠️  Warning: Using default token 'changeme'."
  echo "   Set MY_TERMINAL_TOKEN env var for security:"
  echo "   export MY_TERMINAL_TOKEN=your-secret-token"
  echo ""
fi

echo "Starting MY Terminal on http://0.0.0.0:${PORT}"
echo "Access from iPhone: http://$(hostname -I | awk '{print $1}'):${PORT}"

exec uvicorn terminal.server:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --reload

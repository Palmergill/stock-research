#!/bin/bash

echo "Starting Palmer Gill local site..."

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

# Start local site and API
echo "Starting local site and API on http://localhost:8000..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
LOCAL_SITE_ROOT=true uvicorn app.main:app --reload >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
cd "$ROOT_DIR"

echo ""
echo "✅ Local site started!"
echo "📊 Open http://localhost:8000 in your browser"
echo "📝 Logs: $LOG_DIR/backend.log"
echo ""
echo "Press Ctrl+C to stop the server"

# Wait for interrupt
trap "kill $BACKEND_PID; exit" INT
wait

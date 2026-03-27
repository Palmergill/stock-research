#!/bin/bash
set -e

echo "Starting Railway deployment..."
echo "Current directory: $(pwd)"
echo "Contents: $(ls -la)"

# Check if we're in the backend directory or need to cd into it
if [ -d "backend" ]; then
    echo "Found backend directory, entering..."
    cd backend
fi

echo "Now in: $(pwd)"
echo "Backend contents: $(ls -la)"

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

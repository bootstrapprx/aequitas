#!/bin/bash
set -e  # Exit on any error

echo "=== Aequitas Backend Entrypoint ==="

# Run bootstrap script
echo "Running bootstrap..."
python scripts/bootstrap.py

if [ $? -ne 0 ]; then
    echo "ERROR: Bootstrap failed!"
    exit 1
fi

echo "Bootstrap completed successfully"
echo "Starting uvicorn server..."

# Use exec to replace the shell with uvicorn
# This ensures uvicorn gets PID 1 and receives signals properly
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

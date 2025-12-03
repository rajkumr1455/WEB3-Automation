#!/bin/bash
set -euo pipefail

echo "========================================"
echo "Celery Worker Startup Script"
echo "========================================"

# Ensure Python can find modules
export PYTHONPATH=/app:${PYTHONPATH:-}
export PYTHONUNBUFFERED=1

# Pre-validate that celery_app can be imported
echo "Validating celery_app module..."
python3 -c "from celery_app import celery_app, run_scan_task; print(f'✅ Tasks registered: {list(celery_app.tasks.keys())}')" || {
    echo "❌ Failed to import celery_app"
    exit 1
}

echo "Starting Celery worker..."
exec celery -A celery_app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pool=solo \
    --without-gossip \
    --without-mingle \
    --without-heartbeat

#!/bin/bash
set -e

echo "Starting RASA Actions server..."

# Wait for dependencies if needed
if [ -n "$WAIT_FOR_SERVICES" ]; then
    echo "Waiting for dependent services..."
    sleep 5
fi

# Create log directories
mkdir -p /app/logs

# Set Python path for actions
export PYTHONPATH="${PYTHONPATH}:/app/actions:/app"

# Start RASA actions server
echo "Starting RASA actions server on port 5055..."

# Execute RASA actions server
exec python -m rasa run actions \
    --actions actions \
    --port 5055 \
    --auto-reload \
    --debug
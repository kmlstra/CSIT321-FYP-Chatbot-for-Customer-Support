#!/bin/bash

# Exit on any error
set -e

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting Rasa server initialization..."

# Wait for dependencies
log "Waiting for dependencies..."
sleep 10

# Validate required environment variables
log "Validating environment variables..."
if [ -z "$RASA_LOG_LEVEL" ]; then
    export RASA_LOG_LEVEL="INFO"
fi

# Create logs directory
mkdir -p /app/logs

# Set Python path
export PYTHONPATH="/app:$PYTHONPATH"

log "Environment setup complete"

# Check if model exists
if [ ! -f "/app/models/current.tar.gz" ]; then
    log "Model file not found, looking for available models..."
    MODEL_FILE=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n1)
    if [ -n "$MODEL_FILE" ]; then
        log "Creating symlink to model: $MODEL_FILE"
        ln -sf "$MODEL_FILE" "/app/models/current.tar.gz"
    else
        log "No model files found, training new model..."
        cd /app
        python -m rasa train --out models
        MODEL_FILE=$(ls -t /app/models/*.tar.gz 2>/dev/null | head -n1)
        if [ -n "$MODEL_FILE" ]; then
            ln -sf "$MODEL_FILE" "/app/models/current.tar.gz"
        fi
    fi
fi

# Start Rasa Actions Server in background
log "Starting Rasa Actions Server..."
python -m rasa run actions \
    --actions actions \
    --port 5055 \
    --auto-reload \
    --debug &

# Wait for actions server to start
log "Waiting for Actions Server to start..."
sleep 15

# Start Rasa Server
log "Starting Rasa Server..."
exec python -m rasa run \
    --model "/app/models/current.tar.gz" \
    --port 5005 \
    --host 0.0.0.0 \
    --log-level "$RASA_LOG_LEVEL" \
    --cors "*" \
    --enable-api \
    --endpoints endpoints-aws.yml
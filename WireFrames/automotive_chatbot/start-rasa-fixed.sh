#!/bin/bash
set -e

# Set Python path
export PYTHONPATH="/app/actions:/app"

# Start actions server in background
echo "Starting RASA actions server..."
python -m rasa run actions --actions actions --port 5055 &

# Wait a bit for actions server
sleep 10

# Start RASA server with production endpoints
echo "Starting RASA server..."
if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "aws" ]; then
    echo "Using AWS/production endpoints configuration"
    exec python -m rasa run --model models/current.tar.gz --port 5005 --host 0.0.0.0 --log-level info --enable-api --cors "*" --endpoints endpoints-aws.yml
else
    echo "Using local endpoints configuration"
    exec python -m rasa run --model models/current.tar.gz --port 5005 --host 0.0.0.0 --log-level info --enable-api --cors "*" --endpoints endpoints.yml
fi
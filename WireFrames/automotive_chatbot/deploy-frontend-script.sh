#!/bin/bash
set -e

# Install unzip if not available
if ! command -v unzip &> /dev/null; then
    echo "Installing unzip..."
    sudo apt-get update && sudo apt-get install -y unzip
fi

echo "=== FRONTEND DEPLOYMENT STARTED ==="
echo "Stopping all containers using port 80..."
docker ps --filter "publish=80" --format "table {{.Names}}" | grep -v NAMES | xargs -r docker stop 2>/dev/null || true
docker ps -a --filter "publish=80" --format "table {{.Names}}" | grep -v NAMES | xargs -r docker rm 2>/dev/null || true

echo "Stopping existing frontend container..."
docker stop automotive-frontend 2>/dev/null || true

echo "Removing old frontend container..."
docker rm automotive-frontend 2>/dev/null || true

echo "Removing old frontend images..."
docker image rm csit321fyp/automotive-chatbot-frontend:latest 2>/dev/null || true
docker image prune -f || true

echo "=== LOADING NEW FRONTEND IMAGE ==="
if [ -f "frontend-image.tar.zip" ]; then
    echo "Loading frontend image..."
    unzip -p frontend-image.tar.zip | docker load
    echo "Frontend image loaded successfully"
else
    echo "ERROR: Frontend image file not found"
    exit 1
fi

echo "=== STARTING NEW FRONTEND CONTAINER ==="
echo "Starting new frontend container with fresh image..."
docker run -d --name automotive-frontend -p 80:3000 --restart unless-stopped csit321fyp/automotive-chatbot-frontend:latest

echo "Waiting for frontend container to start..."
sleep 15

echo "Checking frontend container status..."
docker ps | grep automotive-frontend || echo "Frontend container not found"

echo "Checking frontend container logs..."
docker logs --tail=20 automotive-frontend || true

echo "=== FRONTEND CLEANUP ==="
echo "Cleaning up frontend image file..."
rm -f frontend-image.tar.zip

echo "Removing unused Docker resources..."
docker system prune -f || true

echo "=== FRONTEND DEPLOYMENT COMPLETED ==="
echo "Frontend should be available at: http://13.215.240.173"
echo "Test widget at: http://13.215.240.173/test-client-widget.html"
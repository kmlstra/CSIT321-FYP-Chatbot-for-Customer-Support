#!/bin/bash

# Deploy script for Automotive Chatbot with existing RASA model
# This script builds and deploys the Docker image using the existing trained model

set -e  # Exit on any error

echo "=== Automotive Chatbot Deployment with Existing Model ==="
echo "Starting deployment process..."

# Configuration
IMAGE_NAME="ethernallove/automotive-chatbot"
TAG="latest"
CONTAINER_NAME="automotive-chatbot-fixed"
AWS_HOST="13.215.240.173"
AWS_USER="ubuntu"
SSH_KEY_PATH="~/.ssh/id_rsa"  # Update this path to your SSH key

# Step 1: Build Docker image locally
echo "Step 1: Building Docker image with existing RASA model..."
docker build -f Dockerfile.unified -t $IMAGE_NAME:$TAG .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Step 2: Push to Docker Hub
echo "Step 2: Pushing image to Docker Hub..."
docker push $IMAGE_NAME:$TAG

if [ $? -eq 0 ]; then
    echo "✅ Image pushed to Docker Hub successfully"
else
    echo "❌ Docker push failed"
    exit 1
fi

# Step 3: Deploy to AWS
echo "Step 3: Deploying to AWS server..."

# SSH commands to execute on AWS server
ssh -i $SSH_KEY_PATH $AWS_USER@$AWS_HOST << 'ENDSSH'
    echo "Connected to AWS server"
    
    # Stop and remove existing container
    echo "Stopping existing container..."
    docker stop automotive-chatbot-fixed 2>/dev/null || true
    docker rm automotive-chatbot-fixed 2>/dev/null || true
    
    # Pull latest image
    echo "Pulling latest image..."
    docker pull ethernallove/automotive-chatbot:latest
    
    # Run new container with all required port mappings
    echo "Starting new container..."
    docker run -d \
        --name automotive-chatbot-fixed \
        --restart unless-stopped \
        -p 80:80 \
        -p 5005:5005 \
        -p 5055:5055 \
        -p 8000:8000 \
        -p 6379:6379 \
        --health-cmd="curl -f http://localhost/health || exit 1" \
        --health-interval=30s \
        --health-timeout=10s \
        --health-start-period=60s \
        --health-retries=3 \
        ethernallove/automotive-chatbot
# Deploy Frontend Only to EC2 Script for Automotive Chatbot
# This script builds only the frontend Docker image locally and deploys it to EC2

param(
    [string]$EC2Host = "13.215.240.173",
    [string]$KeyPath = "../../cc.pem",
    [switch]$SkipBuild,
    [switch]$Help
)

function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    switch ($Level) {
        "INFO" { Write-Host "[$timestamp] INFO: $Message" -ForegroundColor Cyan }
        "WARN" { Write-Host "[$timestamp] WARN: $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[$timestamp] SUCCESS: $Message" -ForegroundColor Green }
    }
}

if ($Help) {
    Write-Host @"
Deploy Frontend Only to EC2 Script for Automotive Chatbot

USAGE:
    .\deploy-frontend-only.ps1 [OPTIONS]

OPTIONS:
    -EC2Host HOST         EC2 instance IP or hostname [default: 13.215.240.173]
    -KeyPath PATH         Path to SSH private key [default: ../../cc.pem]
    -SkipBuild           Skip Docker image building
    -Help                Show this help message

EXAMPLES:
    .\deploy-frontend-only.ps1
    .\deploy-frontend-only.ps1 -EC2Host "my-ec2-instance.com" -KeyPath "./my-key.pem"
    .\deploy-frontend-only.ps1 -SkipBuild

"@
    exit 0
}

Write-Log "INFO" "Starting frontend-only deployment to EC2: $EC2Host"

# Check prerequisites
Write-Log "INFO" "Checking prerequisites..."

try {
    docker --version | Out-Null
    Write-Log "SUCCESS" "Docker is available"
} catch {
    Write-Log "ERROR" "Docker is not installed or not running"
    exit 1
}

try {
    ssh -V 2>&1 | Out-Null
    Write-Log "SUCCESS" "SSH is available"
} catch {
    Write-Log "ERROR" "SSH is not available"
    exit 1
}

# Build frontend Docker image if not skipped
if (-not $SkipBuild) {
    Write-Log "INFO" "Building frontend Docker image..."
    
    # Build frontend image
    Write-Log "INFO" "Building frontend image..."
    docker build -f aws-deployment/docker/Dockerfile.frontend -t csit321fyp/automotive-chatbot-frontend:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to build frontend image"
        exit 1
    }
    
    Write-Log "SUCCESS" "Frontend Docker image built successfully"
    
    # Save frontend image as tar file
    Write-Log "INFO" "Saving frontend Docker image as tar file..."
    
    # Use PowerShell compression for Windows compatibility
    docker save csit321fyp/automotive-chatbot-frontend:latest -o frontend-image.tar
    
    # Compress using PowerShell
    Compress-Archive -Path "frontend-image.tar" -DestinationPath "frontend-image.tar.zip" -Force
    
    # Clean up uncompressed tar file
    Remove-Item "frontend-image.tar" -ErrorAction SilentlyContinue
    
    Write-Log "SUCCESS" "Frontend Docker image saved as tar file"
} else {
    Write-Log "INFO" "Skipping frontend Docker image building"
}

# Check if SSH key exists
if (-not (Test-Path $KeyPath)) {
    Write-Log "ERROR" "SSH key file not found at: $KeyPath"
    Write-Log "INFO" "Please ensure you have the correct SSH key file for EC2 access"
    Write-Log "INFO" "You can specify a different key path using: -KeyPath 'path/to/your/key.pem'"
    exit 1
}

# Copy frontend image to EC2
Write-Log "INFO" "Copying frontend image to EC2 instance..."

# Copy frontend image file if it exists
if (Test-Path "frontend-image.tar.zip") {
    Write-Log "INFO" "Copying frontend image..."
    scp -o StrictHostKeyChecking=no -i $KeyPath frontend-image.tar.zip ubuntu@${EC2Host}:~/frontend-image.tar.zip
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to copy frontend image"
        exit 1
    }
} else {
    Write-Log "ERROR" "Frontend image file not found. Please build the image first."
    exit 1
}

Write-Log "SUCCESS" "Frontend image copied to EC2 instance"

# Deploy frontend on EC2
Write-Log "INFO" "Deploying frontend application on EC2..."

$deployScript = @'
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
docker run -d --name automotive-frontend -p 3000:3000 --restart unless-stopped csit321fyp/automotive-chatbot-frontend:latest

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
echo "Frontend should be available at: http://13.215.240.173:3000"
echo "Test widget at: http://13.215.240.173:3000/test-client-widget.html"
'@

# Save deploy script to temp file with Unix line endings
$deployScript -replace "`r`n", "`n" | Out-File -FilePath "deploy-frontend-script.sh" -Encoding UTF8 -NoNewline

# Copy and execute deploy script on EC2
Write-Log "INFO" "Copying and executing deployment script on EC2..."
scp -o StrictHostKeyChecking=no -i $KeyPath deploy-frontend-script.sh ubuntu@${EC2Host}:~/deploy-frontend-script.sh
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy deployment script"
    exit 1
}

ssh -o StrictHostKeyChecking=no -i $KeyPath ubuntu@$EC2Host "chmod +x deploy-frontend-script.sh && ./deploy-frontend-script.sh"
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Frontend deployment failed on EC2"
    exit 1
}

Write-Log "SUCCESS" "Frontend deployment completed successfully!"

# Clean up local files
Write-Log "INFO" "Cleaning up local files..."
Remove-Item -Path "frontend-image.tar.zip", "deploy-frontend-script.sh" -ErrorAction SilentlyContinue

Write-Log "SUCCESS" "Frontend deployment to EC2 completed!"
Write-Log "INFO" "Frontend should be available at: http://$EC2Host:3000"
Write-Log "INFO" "Test widget at: http://$EC2Host:3000/test-client-widget.html"
Write-Log "INFO" "Please test the application to ensure the localhost references have been fixed."
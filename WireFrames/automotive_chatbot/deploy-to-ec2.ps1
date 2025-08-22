# Deploy to EC2 Script for Automotive Chatbot
# This script builds Docker images locally and deploys them to EC2

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
Deploy to EC2 Script for Automotive Chatbot

USAGE:
    .\deploy-to-ec2.ps1 [OPTIONS]

OPTIONS:
    -EC2Host HOST         EC2 instance IP or hostname [default: 13.215.240.173]
    -KeyPath PATH         Path to SSH private key [default: ~/.ssh/automotive-chatbot-key.pem]
    -SkipBuild           Skip Docker image building
    -Help                Show this help message

EXAMPLES:
    .\deploy-to-ec2.ps1
    .\deploy-to-ec2.ps1 -EC2Host "my-ec2-instance.com" -KeyPath "./my-key.pem"
    .\deploy-to-ec2.ps1 -SkipBuild

"@
    exit 0
}

Write-Log "INFO" "Starting deployment to EC2: $EC2Host"

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

# Build Docker images if not skipped
if (-not $SkipBuild) {
    Write-Log "INFO" "Building unified Docker image..."
    
    # Build unified image using Dockerfile.unified from project root
    Write-Log "INFO" "Building unified automotive chatbot image..."
    docker build -f ..\..\Dockerfile.unified -t automotive-chatbot-unified:latest ..\..
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to build unified image"
        exit 1
    }
    
    Write-Log "SUCCESS" "Unified Docker image built successfully"
    
    # Save image as tar file
    Write-Log "INFO" "Saving Docker image as tar file..."
    
    # Use PowerShell compression instead of gzip for Windows compatibility
    docker save automotive-chatbot-unified:latest -o unified-image.tar
    
    # Compress using PowerShell (PowerShell only supports .zip format)
    Compress-Archive -Path "unified-image.tar" -DestinationPath "unified-image.tar.zip" -Force
    
    # Clean up uncompressed tar file
    Remove-Item "unified-image.tar" -ErrorAction SilentlyContinue
    
    Write-Log "SUCCESS" "Docker image saved as tar file"
} else {
    Write-Log "INFO" "Skipping Docker image building"
}

# Check if SSH key exists
if (-not (Test-Path $KeyPath)) {
    Write-Log "ERROR" "SSH key file not found at: $KeyPath"
    Write-Log "INFO" "Please ensure you have the correct SSH key file for EC2 access"
    Write-Log "INFO" "You can specify a different key path using: -KeyPath 'path/to/your/key.pem'"
    exit 1
}

# Copy files to EC2
Write-Log "INFO" "Copying files to EC2 instance..."

# Copy docker-compose-unified.yml, .env file, and nginx configuration
scp -o StrictHostKeyChecking=no -i $KeyPath aws-deployment/docker/docker-compose-unified.yml ubuntu@${EC2Host}:~/docker-compose.yml
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy docker-compose.yml"
    exit 1
}

scp -o StrictHostKeyChecking=no -i $KeyPath aws-deployment/docker/.env ubuntu@${EC2Host}:~/.env
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy .env file"
    exit 1
}

scp -o StrictHostKeyChecking=no -i $KeyPath aws-deployment/docker/nginx.conf ubuntu@${EC2Host}:~/nginx.conf
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy nginx.conf file"
    exit 1
}

scp -o StrictHostKeyChecking=no -i $KeyPath aws-deployment/monitoring/prometheus.yml ubuntu@${EC2Host}:~/prometheus.yml
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy prometheus.yml file"
    exit 1
}

# Copy AWS-specific endpoints configuration
scp -o StrictHostKeyChecking=no -i $KeyPath backend/endpoints-aws.yml ubuntu@${EC2Host}:~/endpoints-aws.yml
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy endpoints-aws.yml file"
    exit 1
}

# Copy unified image file if it exists
if (Test-Path "unified-image.tar.zip") {
    Write-Log "INFO" "Copying unified image..."
    scp -o StrictHostKeyChecking=no -i $KeyPath unified-image.tar.zip ubuntu@${EC2Host}:~/unified-image.tar.zip
}

Write-Log "SUCCESS" "Files copied to EC2 instance"

# Deploy on EC2
Write-Log "INFO" "Deploying application on EC2..."

$deployScript = @'
#!/bin/bash
set -e

# Install unzip if not available
if ! command -v unzip &> /dev/null; then
    echo "Installing unzip..."
    sudo apt-get update && sudo apt-get install -y unzip
fi

echo "=== DOCKER CLEANUP AND CACHE CLEARING ==="
echo "Stopping existing containers..."
docker-compose down || true

echo "Removing old containers and images..."
docker container prune -f || true
docker image prune -f || true

echo "Clearing Docker build cache..."
docker builder prune -f || true

echo "Removing dangling volumes..."
docker volume prune -f || true

echo "=== LOADING NEW DOCKER IMAGES ==="
if [ -f "unified-image.tar.zip" ]; then
    echo "Loading unified automotive chatbot image..."
    unzip -p unified-image.tar.zip | docker load
fi

echo "=== STARTING NEW CONTAINERS ==="
echo "Starting new containers with fresh images..."
docker-compose up -d --force-recreate --remove-orphans

echo "Waiting for containers to start..."
sleep 30

echo "Checking container status..."
docker-compose ps

echo "Checking container logs for errors..."
docker-compose logs --tail=20 frontend || true
docker-compose logs --tail=20 backend || true
docker-compose logs --tail=20 rasa || true

echo "=== FINAL CLEANUP ==="
echo "Cleaning up image files..."
rm -f unified-image.tar.zip

echo "Removing unused Docker resources..."
docker system prune -f || true

echo "=== DEPLOYMENT COMPLETED ==="
echo "Application should be available at: http://13.215.240.173"
echo "Test widget at: http://13.215.240.173/test-client-widget.html"
echo "Backend API at: http://13.215.240.173:8000"
echo "Rasa API at: http://13.215.240.173:5005"
'@

# Save deploy script to temp file with Unix line endings
$deployScript -replace "`r`n", "`n" | Out-File -FilePath "deploy-script.sh" -Encoding UTF8 -NoNewline

# Copy and execute deploy script on EC2
scp -o StrictHostKeyChecking=no -i $KeyPath deploy-script.sh ubuntu@${EC2Host}:~/deploy-script.sh
ssh -o StrictHostKeyChecking=no -i $KeyPath ubuntu@$EC2Host "chmod +x deploy-script.sh && ./deploy-script.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Deployment failed on EC2"
    exit 1
}

Write-Log "SUCCESS" "Deployment completed successfully!"

# Clean up local files
Write-Log "INFO" "Cleaning up local files..."
Remove-Item -Path "frontend-image.tar.zip", "backend-image.tar.zip", "rasa-image.tar.zip", "deploy-script.sh" -ErrorAction SilentlyContinue

Write-Log "SUCCESS" "Deployment to EC2 completed!"
Write-Log "INFO" "Application should be available at: http://$EC2Host"
Write-Log "INFO" "Test widget at: http://$EC2Host/test-client-widget.html"
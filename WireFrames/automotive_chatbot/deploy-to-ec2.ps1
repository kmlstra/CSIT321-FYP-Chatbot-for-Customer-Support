# Deploy to EC2 Script for Automotive Chatbot
# This script builds Docker images locally and deploys them to EC2

param(
    [string]$EC2Host = "54.254.180.103",
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
    -EC2Host HOST         EC2 instance IP or hostname [default: 54.254.180.103]
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
    Write-Log "INFO" "Building Docker images..."
    
    # Build frontend image
    Write-Log "INFO" "Building frontend image..."
    docker build -f aws-deployment/docker/Dockerfile.frontend -t csit321fyp/automotive-chatbot-frontend:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to build frontend image"
        exit 1
    }
    
    # Build backend image
    Write-Log "INFO" "Building backend image..."
    docker build -f aws-deployment/docker/Dockerfile.backend -t csit321fyp/automotive-chatbot-backend:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to build backend image"
        exit 1
    }
    
    # Build Rasa image
    Write-Log "INFO" "Building Rasa image..."
    docker build -f aws-deployment/docker/Dockerfile.rasa -t automotive-chatbot-rasa:latest .
    if ($LASTEXITCODE -ne 0) {
        Write-Log "ERROR" "Failed to build Rasa image"
        exit 1
    }
    
    Write-Log "SUCCESS" "All Docker images built successfully"
    
    # Save images as tar files
    Write-Log "INFO" "Saving Docker images as tar files..."
    
    # Use PowerShell compression instead of gzip for Windows compatibility
    docker save csit321fyp/automotive-chatbot-frontend:latest -o frontend-image.tar
    docker save csit321fyp/automotive-chatbot-backend:latest -o backend-image.tar
    docker save automotive-chatbot-rasa:latest -o rasa-image.tar
    
    # Compress using PowerShell (PowerShell only supports .zip format)
    Compress-Archive -Path "frontend-image.tar" -DestinationPath "frontend-image.tar.zip" -Force
    Compress-Archive -Path "backend-image.tar" -DestinationPath "backend-image.tar.zip" -Force
    Compress-Archive -Path "rasa-image.tar" -DestinationPath "rasa-image.tar.zip" -Force
    
    # Clean up uncompressed tar files
    Remove-Item "frontend-image.tar", "backend-image.tar", "rasa-image.tar" -ErrorAction SilentlyContinue
    
    Write-Log "SUCCESS" "Docker images saved as tar files"
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

# Copy docker-compose.yml, .env file, and nginx configuration
scp -i $KeyPath aws-deployment/docker/docker-compose.yml ubuntu@${EC2Host}:~/docker-compose.yml
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy docker-compose.yml"
    exit 1
}

scp -i $KeyPath aws-deployment/docker/.env ubuntu@${EC2Host}:~/.env
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy .env file"
    exit 1
}

scp -i $KeyPath aws-deployment/docker/nginx.conf ubuntu@${EC2Host}:~/nginx.conf
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy nginx.conf file"
    exit 1
}

scp -i $KeyPath aws-deployment/monitoring/prometheus.yml ubuntu@${EC2Host}:~/prometheus.yml
if ($LASTEXITCODE -ne 0) {
    Write-Log "ERROR" "Failed to copy prometheus.yml file"
    exit 1
}

# Copy image files if they exist
if (Test-Path "frontend-image.tar.zip") {
    Write-Log "INFO" "Copying frontend image..."
    scp -i $KeyPath frontend-image.tar.zip ubuntu@${EC2Host}:~/frontend-image.tar.zip
}

if (Test-Path "backend-image.tar.zip") {
    Write-Log "INFO" "Copying backend image..."
    scp -i $KeyPath backend-image.tar.zip ubuntu@${EC2Host}:~/backend-image.tar.zip
}

if (Test-Path "rasa-image.tar.zip") {
    Write-Log "INFO" "Copying Rasa image..."
    scp -i $KeyPath rasa-image.tar.zip ubuntu@${EC2Host}:~/rasa-image.tar.zip
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

echo "Loading Docker images..."
if [ -f "frontend-image.tar.zip" ]; then
    echo "Loading frontend image..."
    unzip -p frontend-image.tar.zip | docker load
fi

if [ -f "backend-image.tar.zip" ]; then
    echo "Loading backend image..."
    unzip -p backend-image.tar.zip | docker load
fi

if [ -f "rasa-image.tar.zip" ]; then
    echo "Loading Rasa image..."
    unzip -p rasa-image.tar.zip | docker load
fi

echo "Stopping existing containers..."
docker-compose down || true

echo "Starting new containers..."
docker-compose up -d

echo "Checking container status..."
docker-compose ps

echo "Cleaning up image files..."
rm -f frontend-image.tar.zip backend-image.tar.zip rasa-image.tar.zip

echo "Deployment completed!"
echo "Application should be available at: http://54.254.180.103"
echo "Test widget at: http://54.254.180.103/test-client-widget.html"
'@

# Save deploy script to temp file with Unix line endings
$deployScript -replace "`r`n", "`n" | Out-File -FilePath "deploy-script.sh" -Encoding UTF8 -NoNewline

# Copy and execute deploy script on EC2
scp -i $KeyPath deploy-script.sh ubuntu@${EC2Host}:~/deploy-script.sh
ssh -i $KeyPath ubuntu@$EC2Host "chmod +x deploy-script.sh && ./deploy-script.sh"

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
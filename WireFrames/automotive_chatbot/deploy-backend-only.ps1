# Backend-Only Deployment Script for CleverCompanion
# This script deploys only the backend service to AWS EC2

Write-Host "Starting Backend-Only Deployment..." -ForegroundColor Green

# Configuration
$AWS_IP = "13.215.240.173"
$PEM_KEY = "d:\CSIT321-FYP-Chatbot-for-Customer-Support\cc.pem"
$PROJECT_DIR = "d:\CSIT321-FYP-Chatbot-for-Customer-Support\WireFrames\automotive_chatbot"
$TEMP_DIR = "$PROJECT_DIR\temp_backend_deploy"

# Create temporary directory
Write-Host "Creating temporary directory..." -ForegroundColor Yellow
if (Test-Path $TEMP_DIR) {
    Remove-Item -Recurse -Force $TEMP_DIR
}
New-Item -ItemType Directory -Path $TEMP_DIR | Out-Null

try {
    # Step 1: Build backend Docker image
    Write-Host "Building backend Docker image..." -ForegroundColor Yellow
    Set-Location $PROJECT_DIR
    
    $buildResult = docker build -f aws-deployment/docker/Dockerfile.backend -t clevercompanion-backend:latest .
    if ($LASTEXITCODE -ne 0) {
        throw "Backend Docker build failed"
    }
    Write-Host "Backend image built successfully" -ForegroundColor Green
    
    # Step 2: Save backend image to tar file
    Write-Host "Saving backend image to tar file..." -ForegroundColor Yellow
    $backendTarPath = "$TEMP_DIR\clevercompanion-backend.tar"
    docker save clevercompanion-backend:latest -o $backendTarPath
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to save backend image"
    }
    Write-Host "Backend image saved to $backendTarPath" -ForegroundColor Green
    
    # Step 3: Copy backend image to AWS server
    Write-Host "Copying backend image to AWS server..." -ForegroundColor Yellow
    scp -i $PEM_KEY $backendTarPath ubuntu@${AWS_IP}:/tmp/
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy backend image to AWS server"
    }
    Write-Host "Backend image copied to AWS server" -ForegroundColor Green
    
    # Step 4: Deploy backend on AWS server
    Write-Host "Deploying backend on AWS server..." -ForegroundColor Yellow
    
    $deployCommands = @"
echo "Loading backend image..."
docker load -i /tmp/clevercompanion-backend.tar
if [ `$? -ne 0 ]; then
    echo "Failed to load backend image"
    exit 1
fi

echo "Stopping existing backend container..."
docker-compose -f /home/ubuntu/docker-compose.production.yml stop backend
docker stop automotive-backend 2>/dev/null || true

echo "Removing old backend container..."
docker-compose -f /home/ubuntu/docker-compose.production.yml rm -f backend
docker rm automotive-backend 2>/dev/null || true

echo "Starting new backend container..."
docker-compose -f /home/ubuntu/docker-compose.production.yml up -d backend
if [ `$? -ne 0 ]; then
    echo "Failed to start backend container"
    exit 1
fi

echo "Checking backend container status..."
docker-compose -f /home/ubuntu/docker-compose.production.yml ps backend

echo "Cleaning up temporary files..."
rm -f /tmp/clevercompanion-backend.tar

echo "Backend deployment completed successfully!"
"@
    
    ssh -i $PEM_KEY ubuntu@$AWS_IP $deployCommands
    if ($LASTEXITCODE -ne 0) {
        throw "Backend deployment on AWS server failed"
    }
    
    Write-Host "Backend deployment completed successfully!" -ForegroundColor Green
    
    # Step 5: Verify backend service
    Write-Host "Verifying backend service..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    $healthCheck = ssh -i $PEM_KEY ubuntu@$AWS_IP "curl -f http://localhost:8000/health || echo 'Health check failed'"
    Write-Host "Backend health check result: $healthCheck" -ForegroundColor Cyan
    
} catch {
    Write-Host "Error during backend deployment: $_" -ForegroundColor Red
    exit 1
} finally {
    # Cleanup local temporary files
    Write-Host "Cleaning up local temporary files..." -ForegroundColor Yellow
    if (Test-Path $TEMP_DIR) {
        Remove-Item -Recurse -Force $TEMP_DIR
    }
    Write-Host "Local cleanup completed" -ForegroundColor Green
}

Write-Host "Backend-Only Deployment Script Completed!" -ForegroundColor Green
Write-Host "Backend service should now be running with the latest changes." -ForegroundColor Cyan
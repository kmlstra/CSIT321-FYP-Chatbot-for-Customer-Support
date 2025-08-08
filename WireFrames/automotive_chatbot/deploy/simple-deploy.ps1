#!/usr/bin/env pwsh
# Simple Docker Deploy Script - Direct to Server
# No AWS dependencies - just SSH and Docker

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [string]$Username = "ubuntu",
    [string]$PemKeyPath = "",
    [string]$ProjectName = "automotive-chatbot",
    [string]$Version = "latest",
    [string]$DeployPath = "/home/ubuntu/automotive-chatbot"
)

# Color functions for better output
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

# Header
Write-Host "=" * 60 -ForegroundColor Magenta
Write-Host "    SIMPLE DOCKER DEPLOY - DIRECT TO SERVER" -ForegroundColor Magenta
Write-Host "=" * 60 -ForegroundColor Magenta
Write-Host ""

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    # Check if images exist locally
    $backendImage = docker images -q "${ProjectName}-backend:${Version}"
    $frontendImage = docker images -q "${ProjectName}-frontend:${Version}"
    
    if (-not $backendImage) {
        Write-Error "[ERROR] Backend image not found. Run simple-build.ps1 first."
        return $false
    }
    Write-Success "[OK] Backend image found"
    
    if (-not $frontendImage) {
        Write-Error "[ERROR] Frontend image not found. Run simple-build.ps1 first."
        return $false
    }
    Write-Success "[OK] Frontend image found"
    
    # Check SSH connectivity
    if ($PemKeyPath) {
        if (-not (Test-Path $PemKeyPath)) {
            Write-Error "[ERROR] PEM key file not found: $PemKeyPath"
            return $false
        }
        Write-Success "[OK] PEM key file found"
    }
    
    return $true
}

# Test server connection
function Test-ServerConnection {
    Write-Info "Testing server connection..."
    
    $sshArgs = @()
    if ($PemKeyPath) {
        $sshArgs += @("-i", $PemKeyPath)
    }
    $sshArgs += @(
        "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "${Username}@${ServerIP}", 
        "echo 'Connection successful'"
    )
    
    try {
        $result = ssh @sshArgs 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "[OK] Server connection successful"
            return $true
        }
    } catch {
        Write-Error "[ERROR] Cannot connect to server"
        return $false
    }
    
    Write-Error "[ERROR] Cannot connect to server"
    return $false
}

# Save images to tar files
function Export-Images {
    Write-Info "Exporting Docker images to tar files..."
    
    # Create temp directory
    $tempDir = "temp-images"
    if (Test-Path $tempDir) {
        Remove-Item $tempDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $tempDir | Out-Null
    
    # Export backend image
    Write-Info "Exporting backend image..."
    docker save "${ProjectName}-backend:${Version}" -o "${tempDir}/backend.tar"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to export backend image"
        return $false
    }
    Write-Success "[OK] Backend image exported"
    
    # Export frontend image
    Write-Info "Exporting frontend image..."
    docker save "${ProjectName}-frontend:${Version}" -o "${tempDir}/frontend.tar"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to export frontend image"
        return $false
    }
    Write-Success "[OK] Frontend image exported"
    
    return $true
}

# Upload files to server
function Upload-Files {
    Write-Info "Uploading files to server..."
    
    $scpArgs = @()
    if ($PemKeyPath) {
        $scpArgs += @("-i", $PemKeyPath)
    }
    
    # Create deployment directory and temp-images directory on server
    $sshArgs = @()
    if ($PemKeyPath) {
        $sshArgs += @("-i", $PemKeyPath)
    }
    $sshArgs += @("${Username}@${ServerIP}", "mkdir -p $DeployPath/temp-images")
    ssh @sshArgs
    
    # Upload docker-compose and env files
    Write-Info "Uploading configuration files..."
    $scpArgs += @("-r", "docker-compose.yml", ".env.docker", "${Username}@${ServerIP}:${DeployPath}/")
    scp @scpArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload configuration files"
        return $false
    }
    
    # Upload image tar files
    Write-Info "Uploading Docker images (this may take a while)..."
    $scpArgs = @()
    if ($PemKeyPath) {
        $scpArgs += @("-i", $PemKeyPath)
    }
    $scpArgs += @("-r", "temp-images/", "${Username}@${ServerIP}:${DeployPath}/")
    scp @scpArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upload Docker images"
        return $false
    }
    
    Write-Success "[OK] All files uploaded successfully"
    return $true
}

# Deploy on server
function Deploy-OnServer {
    Write-Info "Deploying on server..."
    
    $sshArgs = @()
    if ($PemKeyPath) {
        $sshArgs += @("-i", $PemKeyPath)
    }
    
    # Step 1: Check disk space
    Write-Info "Checking disk space on server..."
    $diskCheckScript = "cd $DeployPath && AVAIL_SPACE=`$(df . | tail -1 | awk '{print `$4}') && REQUIRED_SPACE=2000000 && if [ `$AVAIL_SPACE -lt `$REQUIRED_SPACE ]; then echo 'ERROR: Insufficient disk space. Available: '`$AVAIL_SPACE'KB, Required: '`$REQUIRED_SPACE'KB' && exit 1; fi && echo 'Disk space check passed. Available: '`$AVAIL_SPACE'KB'"
    $diskOutput = ssh @sshArgs "${Username}@${ServerIP}" $diskCheckScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Disk space check failed"
        Write-Host $diskOutput -ForegroundColor Red
        return $false
    }
    Write-Success "[OK] Disk space check passed"
    
    # Step 2: Load Docker images
    Write-Info "Loading Docker images on server..."
    $loadScript = "cd $DeployPath && echo 'Loading backend image...' && docker load -i temp-images/backend.tar && echo 'Loading frontend image...' && docker load -i temp-images/frontend.tar"
    $loadOutput = ssh @sshArgs "${Username}@${ServerIP}" $loadScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Failed to load Docker images"
        Write-Host $loadOutput -ForegroundColor Red
        return $false
    }
    Write-Success "[OK] Docker images loaded successfully"
    
    # Step 3: Install Docker Compose if not available
    Write-Info "Checking and installing Docker Compose if needed..."
    $installComposeScript = @"
cd $DeployPath
echo 'Checking Docker Compose availability...'
if command -v docker-compose >/dev/null 2>&1; then
    echo 'docker-compose command found'
    COMPOSE_CMD='docker-compose'
elif docker compose version >/dev/null 2>&1; then
    echo 'docker compose command found'
    COMPOSE_CMD='docker compose'
else
    echo 'Docker Compose not found. Installing...'
    # Install Docker Compose v2 (plugin)
    sudo apt-get update
    sudo apt-get install -y docker-compose-plugin
    
    # Verify installation
    if docker compose version >/dev/null 2>&1; then
        echo 'Docker Compose plugin installed successfully'
        COMPOSE_CMD='docker compose'
    else
        echo 'Failed to install Docker Compose plugin. Trying standalone installation...'
        # Fallback: Install standalone docker-compose
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
        
        if command -v docker-compose >/dev/null 2>&1; then
            echo 'Standalone docker-compose installed successfully'
            COMPOSE_CMD='docker-compose'
        else
            echo 'ERROR: Failed to install Docker Compose'
            exit 1
        fi
    fi
fi
echo "Using command: `$COMPOSE_CMD"
"@
    $installOutput = ssh @sshArgs "${Username}@${ServerIP}" $installComposeScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Failed to install Docker Compose"
        Write-Host $installOutput -ForegroundColor Red
        return $false
    }
    Write-Success "[OK] Docker Compose is available"
    
    # Step 4: Stop existing containers
    Write-Info "Stopping existing containers..."
    $stopScript = "cd $DeployPath && if command -v docker-compose >/dev/null 2>&1; then echo 'Using docker-compose command' && docker-compose down 2>/dev/null || true; elif docker compose version >/dev/null 2>&1; then echo 'Using docker compose command' && docker compose down 2>/dev/null || true; fi"
    $stopOutput = ssh @sshArgs "${Username}@${ServerIP}" $stopScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Failed to stop existing containers"
        Write-Host $stopOutput -ForegroundColor Red
        return $false
    }
    Write-Success "[OK] Existing containers stopped"
    
    # Step 5: Start new containers with version detection
    Write-Info "Starting new containers..."
    $startScript = "cd $DeployPath && cp .env.docker .env && if command -v docker-compose >/dev/null 2>&1; then echo 'Starting containers with docker-compose...' && docker-compose up -d; elif docker compose version >/dev/null 2>&1; then echo 'Starting containers with docker compose...' && docker compose up -d; else echo 'ERROR: Neither docker-compose nor docker compose found' && exit 1; fi"
    $startOutput = ssh @sshArgs "${Username}@${ServerIP}" $startScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Failed to start containers"
        Write-Host $startOutput -ForegroundColor Red
        
        # Try to get container logs for debugging
        Write-Info "Attempting to get container logs for debugging..."
        $logsScript = "cd $DeployPath && if command -v docker-compose >/dev/null 2>&1; then docker-compose logs --tail=20; elif docker compose version >/dev/null 2>&1; then docker compose logs --tail=20; fi"
        $logsOutput = ssh @sshArgs "${Username}@${ServerIP}" $logsScript 2>&1
        Write-Host $logsOutput -ForegroundColor Yellow
        return $false
    }
    Write-Success "[OK] Containers started successfully"
    
    # Step 6: Cleanup and verify
    Write-Info "Cleaning up and verifying deployment..."
    $cleanupScript = "cd $DeployPath && rm -rf temp-images/ && echo 'Deployment completed!' && if command -v docker-compose >/dev/null 2>&1; then docker-compose ps; elif docker compose version >/dev/null 2>&1; then docker compose ps; fi"
    $cleanupOutput = ssh @sshArgs "${Username}@${ServerIP}" $cleanupScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "[ERROR] Cleanup failed"
        Write-Host $cleanupOutput -ForegroundColor Red
        return $false
    }
    
    Write-Success "[OK] Deployment completed successfully"
    Write-Host $cleanupOutput -ForegroundColor Green
    return $true
}

# Cleanup local temp files
function Cleanup-TempFiles {
    Write-Info "Cleaning up temporary files..."
    if (Test-Path "temp-images") {
        Remove-Item "temp-images" -Recurse -Force
        Write-Success "[OK] Temporary files cleaned up"
    }
}

# Main execution
function Main {
    Write-Info "Starting simple deployment process..."
    Write-Info "Server: $ServerIP"
    Write-Info "Username: $Username"
    Write-Info "Project: $ProjectName"
    Write-Info "Version: $Version"
    Write-Host ""
    
    # Change to deploy directory
    # Get the directory where this script is located
    $deployDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Definition }
    Set-Location $deployDir
    
    try {
        # Run checks
        if (-not (Test-Prerequisites)) {
            exit 1
        }
        
        if (-not (Test-ServerConnection)) {
            Write-Error "Cannot connect to server. Please check:"
            Write-Error "- Server IP address: $ServerIP"
            Write-Error "- Username: $Username"
            if ($PemKeyPath) {
                Write-Error "- PEM key path: $PemKeyPath"
            }
            Write-Error "- Server is running and accessible"
            exit 1
        }
        
        # Export, upload, and deploy
        if (-not (Export-Images)) {
            exit 1
        }
        
        if (-not (Upload-Files)) {
            exit 1
        }
        
        if (-not (Deploy-OnServer)) {
            Write-Error "Deployment failed on server. Please check the error messages above."
            exit 1
        }
        
        # Success - only show this if we reach here!
        Write-Host ""
        Write-Success "=" * 60
        Write-Success "    DEPLOYMENT COMPLETED SUCCESSFULLY!"
        Write-Success "=" * 60
        Write-Host ""
        Write-Info "Your application should now be running on:"
        Write-Info "Frontend: http://${ServerIP}:3000"
        Write-Info "Backend API: http://${ServerIP}:8001"
        Write-Info "Rasa API: http://${ServerIP}:5005"
        Write-Host ""
        
    } finally {
        Cleanup-TempFiles
    }
}

# Show usage if no server IP provided
if (-not $ServerIP) {
    Write-Host "Usage: .\simple-deploy.ps1 -ServerIP [server-ip] [-Username [username]] [-PemKeyPath [path-to-pem]]"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\simple-deploy.ps1 -ServerIP 13.212.93.122"
    Write-Host "  .\simple-deploy.ps1 -ServerIP 13.212.93.122 -PemKeyPath C:\path\to\key.pem"
    exit 1
}

# Run main function
Main
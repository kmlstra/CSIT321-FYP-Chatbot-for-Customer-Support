# Simple Docker Build Script - No Functions Version
param(
    [string]$ProjectName = "automotive-chatbot",
    [string]$Version = "latest"
)

# Header
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "    SIMPLE DOCKER BUILD - DOCKER DESKTOP ONLY" -ForegroundColor Magenta  
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

Write-Host "Starting Docker build process..." -ForegroundColor Cyan
Write-Host "Project: $ProjectName" -ForegroundColor Cyan
Write-Host "Version: $Version" -ForegroundColor Cyan
Write-Host ""

# Check Docker Desktop
Write-Host "Checking Docker Desktop status..." -ForegroundColor Cyan
docker info 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Docker Desktop is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Docker Desktop is not running or not installed" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check required files
Write-Host "Checking required files..." -ForegroundColor Cyan
$requiredFiles = @("Dockerfile.backend", "Dockerfile.frontend", "docker-compose.yml", ".env.docker")
$allExist = $true

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "[OK] Found $file" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Missing $file" -ForegroundColor Red
        $allExist = $false
    }
}

if (-not $allExist) {
    Write-Host "Missing required files. Please ensure all Dockerfiles and configuration files exist." -ForegroundColor Red
    exit 1
}

# Build Docker images
Write-Host "Building Docker images..." -ForegroundColor Cyan

# Build backend image
Write-Host "Building backend image..." -ForegroundColor Cyan
docker build -f Dockerfile.backend -t "${ProjectName}-backend:${Version}" ..
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build backend image" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Backend image built successfully" -ForegroundColor Green

# Build frontend image  
Write-Host "Building frontend image..." -ForegroundColor Cyan
docker build -f Dockerfile.frontend -t "${ProjectName}-frontend:${Version}" ..
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build frontend image" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Frontend image built successfully" -ForegroundColor Green

# Show results
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "    BUILD COMPLETED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

# Show built images
Write-Host "Built images:" -ForegroundColor Cyan
docker images --format "{{.Repository}}:{{.Tag}} ({{.Size}})" | findstr $ProjectName

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Test locally: docker-compose up" -ForegroundColor Cyan
Write-Host "2. Deploy to server: .\simple-deploy.ps1 -ServerIP <your-server-ip>" -ForegroundColor Cyan
Write-Host ""
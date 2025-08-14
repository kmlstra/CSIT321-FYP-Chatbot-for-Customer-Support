# Switch to AWS Production Environment
Write-Host "Switching to AWS production environment..." -ForegroundColor Green

# Define paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendEnvPath = Join-Path $ProjectRoot "backend\.env"
$FrontendEnvPath = Join-Path $ProjectRoot "frontend\.env.local"

# Update backend .env for AWS production
Write-Host "Updating backend environment..." -ForegroundColor Yellow
$backendContent = Get-Content $BackendEnvPath
$updatedBackend = $backendContent | ForEach-Object {
    if ($_ -match "^# DOMAIN=http://54\.254\.180\.103") {
        "DOMAIN=http://54.254.180.103"
    }
    elseif ($_ -match "^DOMAIN=http://localhost") {
        "# DOMAIN=http://localhost"
    }
    elseif ($_ -match "^# NEXT_PUBLIC_DOMAIN=http://54\.254\.180\.103") {
        "NEXT_PUBLIC_DOMAIN=http://54.254.180.103"
    }
    elseif ($_ -match "^NEXT_PUBLIC_DOMAIN=http://localhost") {
        "# NEXT_PUBLIC_DOMAIN=http://localhost"
    }
    elseif ($_ -match "^BACKEND_PORT=8001") {
        "BACKEND_PORT=8001"  # Fixed: Keep port as 8001 for consistency
    }
    elseif ($_ -match "^NEXT_PUBLIC_BACKEND_PORT=8001") {
        "NEXT_PUBLIC_BACKEND_PORT=8001"  # Fixed: Keep port as 8001 for consistency
    }
    elseif ($_ -match "^NEXT_PUBLIC_ENV=") {
        "NEXT_PUBLIC_ENV=production"
    }
    elseif ($_ -match "^PROFILE_PICTURE_URL=") {
        "PROFILE_PICTURE_URL=http://54.254.180.103:8001/static/boy.png"
    }
    elseif ($_ -match "^DEBUG=") {
        "DEBUG=false"
    }
    else {
        $_
    }
}

# Add missing variables if they don't exist
$hasNextPublicEnv = $updatedBackend | Where-Object { $_ -match "^NEXT_PUBLIC_ENV=" }
$hasProfilePictureUrl = $updatedBackend | Where-Object { $_ -match "^PROFILE_PICTURE_URL=" }

if (-not $hasNextPublicEnv) {
    $updatedBackend += "NEXT_PUBLIC_ENV=production"
}

if (-not $hasProfilePictureUrl) {
    $updatedBackend += "PROFILE_PICTURE_URL=http://54.254.180.103:8001/static/boy.png"
}

$updatedBackend | Set-Content $BackendEnvPath

# Create frontend .env.local for AWS production
Write-Host "Creating frontend production environment..." -ForegroundColor Yellow
$frontendEnv = @"
# AWS PRODUCTION ENVIRONMENT
NODE_ENV=production
NEXT_PUBLIC_DOMAIN=http://54.254.180.103
NEXT_PUBLIC_API_URL=http://54.254.180.103:8001
NEXT_PUBLIC_RASA_URL=http://54.254.180.103:5005
NEXT_PUBLIC_WIDGET_URL=http://54.254.180.103
NEXT_PUBLIC_FRONTEND_URL=http://54.254.180.103
NEXT_PUBLIC_BACKEND_URL=http://54.254.180.103:8001
NEXT_PUBLIC_FRONTEND_PORT=80
NEXT_PUBLIC_BACKEND_PORT=8001
NEXT_PUBLIC_RASA_PORT=5005
NEXT_PUBLIC_DEBUG=false
NEXT_PUBLIC_ENV=production
PROFILE_PICTURE_URL=http://54.254.180.103:8001/static/boy.png
"@

$frontendEnv | Set-Content $FrontendEnvPath

Write-Host "Successfully switched to AWS production environment!" -ForegroundColor Green
Write-Host "Frontend: http://54.254.180.103" -ForegroundColor Cyan
Write-Host "Backend API: http://54.254.180.103:8001" -ForegroundColor Cyan
Write-Host "RASA API: http://54.254.180.103:5005" -ForegroundColor Cyan
Write-Host "API Docs: http://54.254.180.103:8001/docs" -ForegroundColor Cyan
Write-Host "Test Widget: http://54.254.180.103/test-client-widget.html" -ForegroundColor Cyan
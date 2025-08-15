# Switch to Local Development Environment
Write-Host "Switching to LOCAL development environment..." -ForegroundColor Green

# Define paths
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$BackendEnvPath = Join-Path $ProjectRoot "backend\.env"
$FrontendEnvPath = Join-Path $ProjectRoot "frontend\.env.local"

# Update backend .env for local development
Write-Host "Updating backend environment..." -ForegroundColor Yellow
$backendContent = Get-Content $BackendEnvPath
$updatedBackend = $backendContent | ForEach-Object {
    if ($_ -match "^DOMAIN=http://54\.254\.180\.103") {
        "# DOMAIN=http://54.254.180.103"
    }
    elseif ($_ -match "^# DOMAIN=http://localhost") {
        "DOMAIN=http://localhost"
    }
    elseif ($_ -match "^NEXT_PUBLIC_DOMAIN=http://54\.254\.180\.103") {
        "# NEXT_PUBLIC_DOMAIN=http://54.254.180.103"
    }
    elseif ($_ -match "^# NEXT_PUBLIC_DOMAIN=http://localhost") {
        "NEXT_PUBLIC_DOMAIN=http://localhost"
    }
    elseif ($_ -match "^BACKEND_PORT=8000") {
        "BACKEND_PORT=8000"
    }
    elseif ($_ -match "^NEXT_PUBLIC_BACKEND_PORT=8000") {
        "NEXT_PUBLIC_BACKEND_PORT=8000"
    }
    elseif ($_ -match "^NEXT_PUBLIC_ENV=") {
        "NEXT_PUBLIC_ENV=development"
    }
    elseif ($_ -match "^PROFILE_PICTURE_URL=") {
        "PROFILE_PICTURE_URL=http://localhost:8000/static/boy.png"
    }
    elseif ($_ -match "^DEBUG=") {
        "DEBUG=true"
    }
    else {
        $_
    }
}

# Add missing variables if they don't exist
$hasNextPublicEnv = $updatedBackend | Where-Object { $_ -match "^NEXT_PUBLIC_ENV=" }
$hasProfilePictureUrl = $updatedBackend | Where-Object { $_ -match "^PROFILE_PICTURE_URL=" }

if (-not $hasNextPublicEnv) {
    $updatedBackend += "NEXT_PUBLIC_ENV=development"
}

if (-not $hasProfilePictureUrl) {
    $updatedBackend += "PROFILE_PICTURE_URL=http://localhost:8000/static/boy.png"
}

$updatedBackend | Set-Content $BackendEnvPath

# Create frontend .env.local for local development
Write-Host "Creating frontend local environment..." -ForegroundColor Yellow
$frontendEnv = @"
# LOCAL DEVELOPMENT ENVIRONMENT
NODE_ENV=development
NEXT_PUBLIC_DOMAIN=http://localhost
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_RASA_URL=http://localhost:5005
NEXT_PUBLIC_WIDGET_URL=http://localhost:3000
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_FRONTEND_PORT=3000
NEXT_PUBLIC_BACKEND_PORT=8000
NEXT_PUBLIC_RASA_PORT=5005
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_ENV=development
PROFILE_PICTURE_URL=http://localhost:8000/static/boy.png
"@

$frontendEnv | Set-Content $FrontendEnvPath

Write-Host "Successfully switched to LOCAL development environment!" -ForegroundColor Green
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "RASA API: http://localhost:5005" -ForegroundColor Cyan
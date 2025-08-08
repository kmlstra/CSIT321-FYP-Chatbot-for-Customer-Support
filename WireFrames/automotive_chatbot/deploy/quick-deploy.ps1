#!/usr/bin/env pwsh
# Quick Deploy - One-Click Deployment Script
# Combines build and deploy in a single command

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIP,
    
    [string]$Username = "ubuntu",
    [string]$PemKeyPath = "",
    [string]$ProjectName = "automotive-chatbot",
    [string]$Version = "latest",
    [switch]$BuildOnly,
    [switch]$DeployOnly,
    [switch]$Help
)

# Color functions
function Write-Success { param($Message) Write-Host $Message -ForegroundColor Green }
function Write-Error { param($Message) Write-Host $Message -ForegroundColor Red }
function Write-Info { param($Message) Write-Host $Message -ForegroundColor Cyan }
function Write-Warning { param($Message) Write-Host $Message -ForegroundColor Yellow }

# Show help
function Show-Help {
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host "    QUICK DEPLOY - ONE-CLICK DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Yellow
    Write-Host "  .\quick-deploy.ps1 -ServerIP <ip> [options]"
    Write-Host ""
    Write-Host "EXAMPLES:" -ForegroundColor Yellow
    Write-Host "  # Full deployment (build + deploy)"
    Write-Host "  .\quick-deploy.ps1 -ServerIP 13.212.93.122"
    Write-Host ""
    Write-Host "  # With PEM key"
    Write-Host "  .\quick-deploy.ps1 -ServerIP 13.212.93.122 -PemKeyPath 'C:\path\to\key.pem'"
    Write-Host ""
    Write-Host "  # Build only"
    Write-Host "  .\quick-deploy.ps1 -ServerIP 13.212.93.122 -BuildOnly"
    Write-Host ""
    Write-Host "  # Deploy only (images already built)"
    Write-Host "  .\quick-deploy.ps1 -ServerIP 13.212.93.122 -DeployOnly"
    Write-Host ""
    Write-Host "OPTIONS:" -ForegroundColor Yellow
    Write-Host "  -ServerIP      Target server IP address (required)"
    Write-Host "  -Username      SSH username (default: ubuntu)"
    Write-Host "  -PemKeyPath    Path to PEM key file (optional)"
    Write-Host "  -ProjectName   Project name (default: automotive-chatbot)"
    Write-Host "  -Version       Image version (default: latest)"
    Write-Host "  -BuildOnly     Only build images, don't deploy"
    Write-Host "  -DeployOnly    Only deploy, skip building"
    Write-Host "  -Help          Show this help message"
    Write-Host ""
    Write-Host "QUICK COMMANDS:" -ForegroundColor Yellow
    Write-Host "  .\simple-build.ps1                    # Build images only"
    Write-Host "  .\simple-deploy.ps1 -ServerIP <ip>    # Deploy only"
    Write-Host "  docker-compose -f docker-compose.simple.yml up -d  # Local test"
    Write-Host ""
}

# Main execution
function Main {
    # Show help if requested
    if ($Help) {
        Show-Help
        return
    }
    
    # Validate server IP
    if (-not $ServerIP) {
        Write-Error "Server IP is required!"
        Show-Help
        exit 1
    }
    
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host "    QUICK DEPLOY - STARTING DEPLOYMENT" -ForegroundColor Magenta
    Write-Host "=" * 60 -ForegroundColor Magenta
    Write-Host ""
    Write-Info "Target Server: $ServerIP"
    Write-Info "Username: $Username"
    Write-Info "Project: $ProjectName"
    Write-Info "Version: $Version"
    if ($PemKeyPath) {
        Write-Info "PEM Key: $PemKeyPath"
    }
    Write-Host ""
    
    # Change to deploy directory
    $deployDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Set-Location $deployDir
    
    try {
        # Step 1: Build (unless DeployOnly)
        if (-not $DeployOnly) {
            Write-Info "Step 1: Building Docker images..."
            $buildArgs = @("-ProjectName", $ProjectName, "-Version", $Version)
            & ".\simple-build.ps1" @buildArgs
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Build failed! Stopping deployment."
                exit 1
            }
            
            Write-Success "✓ Build completed successfully!"
            Write-Host ""
        }
        
        # Stop here if BuildOnly
        if ($BuildOnly) {
            Write-Success "Build-only mode completed!"
            Write-Info "To deploy later, run:"
            Write-Info ".\simple-deploy.ps1 -ServerIP $ServerIP"
            return
        }
        
        # Step 2: Deploy
        Write-Info "Step 2: Deploying to server..."
        $deployArgs = @("-ServerIP", $ServerIP, "-Username", $Username, "-ProjectName", $ProjectName, "-Version", $Version)
        if ($PemKeyPath) {
            $deployArgs += @("-PemKeyPath", $PemKeyPath)
        }
        
        & ".\simple-deploy.ps1" @deployArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Deployment failed!"
            exit 1
        }
        
        # Success!
        Write-Host ""
        Write-Success "=" * 60
        Write-Success "    QUICK DEPLOY COMPLETED SUCCESSFULLY!"
        Write-Success "=" * 60
        Write-Host ""
        Write-Info "Your application is now running at:"
        Write-Info "🌐 Frontend: http://${ServerIP}:3000"
        Write-Info "🔧 Backend API: http://${ServerIP}:8001"
        Write-Info "🤖 Rasa API: http://${ServerIP}:5005"
        Write-Info "📚 API Docs: http://${ServerIP}:8001/docs"
        Write-Host ""
        Write-Info "Useful commands:"
        Write-Info "• Check status: ssh ${Username}@${ServerIP} 'cd /home/${Username}/automotive-chatbot && docker-compose ps'"
        Write-Info "• View logs: ssh ${Username}@${ServerIP} 'cd /home/${Username}/automotive-chatbot && docker-compose logs -f'"
        Write-Info "• Restart: ssh ${Username}@${ServerIP} 'cd /home/${Username}/automotive-chatbot && docker-compose restart'"
        Write-Host ""
        
    } catch {
        Write-Error "An error occurred: $($_.Exception.Message)"
        exit 1
    }
}

# Show help if no parameters
if ($args.Count -eq 0 -and -not $ServerIP) {
    Show-Help
    exit 0
}

# Run main function
Main
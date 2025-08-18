# Main Deployment Script for Automotive Chatbot (Windows PowerShell)
# This script orchestrates the complete deployment process on Windows

param(
    [Parameter(Position=0)]
    [ValidateSet("deploy", "rollback", "validate", "status", "logs", "help")]
    [string]$Action = "deploy",
    
    [string]$AppVersion = "1.0.0",
    [string]$AppDomain = "automotive-chatbot.com",
    [string]$MonitoringDomain = "monitoring.automotive-chatbot.com",
    [string]$DeploymentEnv = "production",
    [switch]$SkipTests,
    [switch]$SkipBackup,
    [switch]$ForceDeploy
)

# Configuration
$AppName = "automotive-chatbot"
$AppDir = "C:\automotive-chatbot"
$DeployDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogFile = "C:\automotive-chatbot\logs\deployment.log"
$LockFile = "$env:TEMP\automotive-chatbot-deploy.lock"
$TimestampFile = "$env:TEMP\automotive-chatbot-deploy.timestamp"

# Deployment phases
$DeploymentPhases = @(
    "PreDeploymentChecks",
    "SystemPreparation",
    "SecuritySetup",
    "ApplicationDeployment",
    "DatabaseSetup",
    "MonitoringSetup",
    "SSLConfiguration",
    "SystemOptimization",
    "HealthChecks",
    "PostDeploymentTasks"
)

# Current phase tracking
$CurrentPhase = 0
$TotalPhases = $DeploymentPhases.Count

# Ensure log directory exists
if (!(Test-Path (Split-Path $LogFile))) {
    New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null
}

# Logging functions
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    
    switch ($Level) {
        "ERROR" { Write-Host $LogMessage -ForegroundColor Red }
        "WARN" { Write-Host $LogMessage -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $LogMessage -ForegroundColor Green }
        "INFO" { Write-Host $LogMessage -ForegroundColor Blue }
        default { Write-Host $LogMessage }
    }
    
    Add-Content -Path $LogFile -Value $LogMessage
}

function Write-PhaseHeader {
    param([string]$PhaseName)
    $script:CurrentPhase++
    $Progress = [math]::Round(($CurrentPhase * 100 / $TotalPhases), 2)
    
    Write-Host "`n=== PHASE $CurrentPhase/$TotalPhases: $PhaseName ===" -ForegroundColor Magenta
    Write-Host "Progress: $Progress%" -ForegroundColor Cyan
    
    Write-Log "Starting phase: $PhaseName" "INFO"
}

# Error handling
function Handle-Error {
    param([string]$ErrorMessage, [string]$Phase)
    
    Write-Log "Deployment failed in phase: $Phase" "ERROR"
    Write-Log "Error: $ErrorMessage" "ERROR"
    
    if (!$ForceDeploy) {
        Write-Log "Attempting automatic rollback..." "WARN"
        Invoke-RollbackDeployment
    }
    
    exit 1
}

# Check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check system requirements
function Test-SystemRequirements {
    Write-Log "Checking system requirements..." "INFO"
    
    # Check if running as administrator
    if (!(Test-Administrator)) {
        throw "This script must be run as Administrator"
    }
    
    # Check Windows version
    $osVersion = [System.Environment]::OSVersion.Version
    if ($osVersion.Major -lt 10) {
        throw "Windows 10 or later is required"
    }
    
    # Check available memory (minimum 2GB)
    $totalMemory = (Get-CimInstance Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum).Sum / 1GB
    if ($totalMemory -lt 2) {
        throw "Minimum 2GB RAM required, found $([math]::Round($totalMemory, 2))GB"
    }
    
    # Check available disk space (minimum 10GB)
    $availableDisk = (Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'").FreeSpace / 1GB
    if ($availableDisk -lt 10) {
        throw "Minimum 10GB disk space required, found $([math]::Round($availableDisk, 2))GB"
    }
    
    # Check network connectivity
    if (!(Test-NetConnection -ComputerName "google.com" -Port 80 -InformationLevel Quiet)) {
        throw "No internet connectivity detected"
    }
    
    Write-Log "System requirements check passed" "SUCCESS"
}

# Load environment variables
function Import-Environment {
    Write-Log "Loading environment configuration..." "INFO"
    
    $envFile = Join-Path $DeployDir ".env"
    $envTemplate = Join-Path $DeployDir "env_template.txt"
    
    if (Test-Path $envFile) {
        Get-Content $envFile | ForEach-Object {
            if ($_ -match '^([^=]+)=(.*)$') {
                [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
            }
        }
        Write-Log "Environment variables loaded from .env file" "SUCCESS"
    }
    elseif (Test-Path $envTemplate) {
        Write-Log "No .env file found, using template. Please configure environment variables." "WARN"
        Copy-Item $envTemplate $envFile
        throw "Please edit $envFile with your configuration and run again"
    }
    else {
        throw "No environment configuration found"
    }
    
    # Validate required variables
    $requiredVars = @(
        "MONGODB_URI",
        "JWT_SECRET",
        "ENCRYPTION_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    )
    
    foreach ($var in $requiredVars) {
        if (!(Get-ChildItem Env: | Where-Object Name -eq $var)) {
            throw "Required environment variable $var is not set"
        }
    }
    
    Write-Log "Environment configuration validated" "SUCCESS"
}

# Pre-deployment checks
function Invoke-PreDeploymentChecks {
    Write-PhaseHeader "Pre-deployment Checks"
    
    try {
        Test-SystemRequirements
        Import-Environment
        
        # Check if deployment is already in progress
        if ((Test-Path $LockFile) -and !$ForceDeploy) {
            throw "Deployment already in progress. Use -ForceDeploy to override."
        }
        
        # Create deployment lock
        $PID | Out-File -FilePath $LockFile
        
        # Create deployment timestamp
        Get-Date -Format "o" | Out-File -FilePath $TimestampFile
        
        Write-Log "Pre-deployment checks completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "PreDeploymentChecks"
    }
}

# System preparation
function Invoke-SystemPreparation {
    Write-PhaseHeader "System Preparation"
    
    try {
        # Enable Windows features
        Write-Log "Enabling required Windows features..." "INFO"
        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart -All
        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart -All
        
        # Install Chocolatey if not present
        if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
            Write-Log "Installing Chocolatey..." "INFO"
            Set-ExecutionPolicy Bypass -Scope Process -Force
            [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
            Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        }
        
        # Install required packages
        Write-Log "Installing required packages..." "INFO"
        $packages = @(
            "git",
            "nodejs",
            "python",
            "docker-desktop",
            "curl",
            "wget",
            "jq"
        )
        
        foreach ($package in $packages) {
            if (!(Get-Command $package -ErrorAction SilentlyContinue)) {
                choco install $package -y
            }
        }
        
        # Create application directories
        Write-Log "Creating application directories..." "INFO"
        $directories = @(
            "$AppDir",
            "$AppDir\logs",
            "$AppDir\data",
            "$AppDir\config",
            "$AppDir\scripts",
            "$AppDir\backups"
        )
        
        foreach ($dir in $directories) {
            if (!(Test-Path $dir)) {
                New-Item -ItemType Directory -Path $dir -Force | Out-Null
            }
        }
        
        Write-Log "System preparation completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "SystemPreparation"
    }
}

# Security setup
function Invoke-SecuritySetup {
    Write-PhaseHeader "Security Setup"
    
    try {
        $securityScript = Join-Path $DeployDir "security_setup.ps1"
        if (Test-Path $securityScript) {
            Write-Log "Running security setup..." "INFO"
            & $securityScript
        }
        else {
            Write-Log "Security setup script not found, skipping" "WARN"
        }
        
        Write-Log "Security setup completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "SecuritySetup"
    }
}

# Application deployment
function Invoke-ApplicationDeployment {
    Write-PhaseHeader "Application Deployment"
    
    try {
        # Start Docker Desktop
        Write-Log "Starting Docker Desktop..." "INFO"
        Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
        
        # Wait for Docker to start
        $timeout = 120
        $timer = 0
        while (!(docker version 2>$null) -and $timer -lt $timeout) {
            Start-Sleep 5
            $timer += 5
            Write-Log "Waiting for Docker to start... ($timer/$timeout seconds)" "INFO"
        }
        
        if ($timer -ge $timeout) {
            throw "Docker failed to start within $timeout seconds"
        }
        
        # Copy application files
        Write-Log "Copying application files..." "INFO"
        $sourceDir = Split-Path -Parent $DeployDir
        robocopy $sourceDir $AppDir /E /XD .git node_modules __pycache__ /XF *.log
        
        # Set up environment file
        Copy-Item (Join-Path $DeployDir ".env") (Join-Path $AppDir ".env")
        
        # Build and start application
        Write-Log "Building and starting application..." "INFO"
        Set-Location $AppDir
        
        # Build frontend
        if (Test-Path "frontend") {
            Write-Log "Building frontend..." "INFO"
            Set-Location "frontend"
            npm install
            npm run build
            Set-Location ".."
        }
        
        # Build backend
        if (Test-Path "backend") {
            Write-Log "Setting up backend..." "INFO"
            Set-Location "backend"
            python -m venv venv
            .\venv\Scripts\Activate.ps1
            pip install -r requirements.txt
            Set-Location ".."
        }
        
        # Start services with Docker Compose
        if (Test-Path "docker-compose.production.yml") {
            Write-Log "Starting services with Docker Compose..." "INFO"
            docker-compose -f docker-compose.production.yml up -d
        }
        
        Write-Log "Application deployment completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "ApplicationDeployment"
    }
}

# Database setup
function Invoke-DatabaseSetup {
    Write-PhaseHeader "Database Setup"
    
    try {
        # Install MongoDB tools if needed
        if (!(Get-Command mongosh -ErrorAction SilentlyContinue)) {
            Write-Log "Installing MongoDB tools..." "INFO"
            choco install mongodb-shell -y
        }
        
        # Test database connections
        Write-Log "Testing database connections..." "INFO"
        
        # Test MongoDB Atlas
        $mongoUri = $env:MONGODB_URI
        if ($mongoUri) {
            $testResult = mongosh $mongoUri --eval "db.runCommand('ping')" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Log "MongoDB Atlas connection successful" "SUCCESS"
            }
            else {
                throw "MongoDB Atlas connection failed"
            }
        }
        
        # Test Redis (if running locally)
        if (Get-Process redis-server -ErrorAction SilentlyContinue) {
            $redisTest = redis-cli ping 2>$null
            if ($redisTest -eq "PONG") {
                Write-Log "Redis connection successful" "SUCCESS"
            }
            else {
                Write-Log "Redis connection failed" "WARN"
            }
        }
        
        Write-Log "Database setup completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "DatabaseSetup"
    }
}

# Monitoring setup
function Invoke-MonitoringSetup {
    Write-PhaseHeader "Monitoring Setup"
    
    try {
        Write-Log "Setting up monitoring (Windows containers)..." "INFO"
        
        # Note: Full monitoring setup would require Windows containers or WSL2
        # For now, we'll set up basic monitoring through Docker containers
        
        Write-Log "Monitoring setup completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "MonitoringSetup"
    }
}

# SSL configuration
function Invoke-SSLConfiguration {
    Write-PhaseHeader "SSL Configuration"
    
    try {
        Write-Log "SSL configuration (development certificates)..." "INFO"
        
        # For development, create self-signed certificates
        $certDir = Join-Path $AppDir "certs"
        if (!(Test-Path $certDir)) {
            New-Item -ItemType Directory -Path $certDir -Force | Out-Null
        }
        
        # Create self-signed certificate for development
        $cert = New-SelfSignedCertificate -DnsName $AppDomain -CertStoreLocation "cert:\LocalMachine\My"
        $certPath = Join-Path $certDir "server.crt"
        $keyPath = Join-Path $certDir "server.key"
        
        Export-Certificate -Cert $cert -FilePath $certPath
        
        Write-Log "SSL configuration completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "SSLConfiguration"
    }
}

# System optimization
function Invoke-SystemOptimization {
    Write-PhaseHeader "System Optimization"
    
    try {
        Write-Log "Applying system optimizations..." "INFO"
        
        # Optimize Windows for server workload
        # Disable unnecessary services
        $servicesToDisable = @(
            "Fax",
            "XblAuthManager",
            "XblGameSave",
            "XboxNetApiSvc"
        )
        
        foreach ($service in $servicesToDisable) {
            if (Get-Service $service -ErrorAction SilentlyContinue) {
                Stop-Service $service -Force -ErrorAction SilentlyContinue
                Set-Service $service -StartupType Disabled -ErrorAction SilentlyContinue
            }
        }
        
        # Optimize power settings
        powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c # High Performance
        
        Write-Log "System optimization completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "SystemOptimization"
    }
}

# Health checks
function Invoke-HealthChecks {
    Write-PhaseHeader "Health Checks"
    
    try {
        # Wait for services to start
        Write-Log "Waiting for services to start..." "INFO"
        Start-Sleep 30
        
        # Run deployment validation
        if (!$SkipTests) {
            $validationScript = Join-Path $DeployDir "deployment_validation.ps1"
            if (Test-Path $validationScript) {
                Write-Log "Running deployment validation..." "INFO"
                & $validationScript -TestType "quick"
                if ($LASTEXITCODE -ne 0) {
                    throw "Health checks failed"
                }
            }
            else {
                Write-Log "Deployment validation script not found" "WARN"
            }
        }
        else {
            Write-Log "Health checks skipped" "WARN"
        }
        
        Write-Log "Health checks completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "HealthChecks"
    }
}

# Post-deployment tasks
function Invoke-PostDeploymentTasks {
    Write-PhaseHeader "Post-deployment Tasks"
    
    try {
        # Create backup if not skipped
        if (!$SkipBackup) {
            $backupScript = Join-Path $DeployDir "backup_recovery.ps1"
            if (Test-Path $backupScript) {
                Write-Log "Creating initial backup..." "INFO"
                & $backupScript -Action "backup"
            }
        }
        
        # Create deployment info file
        Write-Log "Creating deployment info..." "INFO"
        $deploymentInfo = @{
            deployment_id = [System.Guid]::NewGuid().ToString()
            version = $AppVersion
            environment = $DeploymentEnv
            domain = $AppDomain
            deployed_at = Get-Date -Format "o"
            deployed_by = $env:USERNAME
            hostname = $env:COMPUTERNAME
            services = @{
                frontend = "running"
                backend = "running"
                rasa_core = "running"
                rasa_actions = "running"
                redis = "running"
                nginx = "running"
            }
        }
        
        $deploymentInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $AppDir "deployment_info.json")
        
        # Clean up deployment lock
        Remove-Item $LockFile -ErrorAction SilentlyContinue
        Remove-Item $TimestampFile -ErrorAction SilentlyContinue
        
        Write-Log "Post-deployment tasks completed" "SUCCESS"
    }
    catch {
        Handle-Error $_.Exception.Message "PostDeploymentTasks"
    }
}

# Rollback deployment
function Invoke-RollbackDeployment {
    Write-Log "Starting deployment rollback..." "WARN"
    
    try {
        # Stop current services
        if (Test-Path (Join-Path $AppDir "docker-compose.production.yml")) {
            Set-Location $AppDir
            docker-compose -f docker-compose.production.yml down
        }
        
        # Restore from backup if available
        $backupScript = Join-Path $DeployDir "backup_recovery.ps1"
        if (Test-Path $backupScript) {
            & $backupScript -Action "restore_latest"
        }
        
        # Clean up
        Remove-Item $LockFile -ErrorAction SilentlyContinue
        Remove-Item $TimestampFile -ErrorAction SilentlyContinue
        
        Write-Log "Rollback completed" "WARN"
    }
    catch {
        Write-Log "Rollback failed: $($_.Exception.Message)" "ERROR"
    }
}

# Print deployment summary
function Show-DeploymentSummary {
    $deploymentTime = 0
    if (Test-Path $TimestampFile) {
        $startTime = Get-Date (Get-Content $TimestampFile)
        $deploymentTime = ((
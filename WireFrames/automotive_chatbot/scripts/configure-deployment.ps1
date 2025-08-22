# Easy Deployment Configuration Script for Windows PowerShell
# This script provides a simple interface to configure deployment settings

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("localhost", "ec2", "production")]
    [string]$Target,
    
    [Parameter(Mandatory=$false)]
    [string]$CustomDomain,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

function Show-Usage {
    Write-Host @"
========================================
  Deployment Configuration Tool
========================================

Usage: .\configure-deployment.ps1 [OPTIONS]

OPTIONS:
    -Target TARGET           Deployment target (localhost, ec2, production)
    -CustomDomain DOMAIN     Custom domain/IP (e.g., http://192.168.1.100)
    -DryRun                  Show what would be changed without making changes
    -Interactive             Run in interactive mode
    -Help                    Show this help message

EXAMPLES:
    .\configure-deployment.ps1 -Target localhost
    .\configure-deployment.ps1 -Target ec2
    .\configure-deployment.ps1 -CustomDomain "http://192.168.1.100"
    .\configure-deployment.ps1 -Interactive
    .\configure-deployment.ps1 -DryRun -Target localhost

"@ -ForegroundColor Green
}

function Write-ColoredOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Show-InteractiveMenu {
    Clear-Host
    Write-ColoredOutput "========================================" "Cyan"
    Write-ColoredOutput "   Deployment Configuration Tool" "Cyan"
    Write-ColoredOutput "========================================" "Cyan"
    Write-Host ""
    Write-ColoredOutput "Choose your deployment target:" "Yellow"
    Write-Host "  1. Localhost (Development)"
    Write-Host "  2. EC2 Instance (13.215.240.173)"
    Write-Host "  3. Production (Custom Domain)"
    Write-Host "  4. Custom Domain/IP"
    Write-Host "  5. Show current configuration"
    Write-Host "  6. Exit"
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-6)"
    return $choice
}

function Invoke-ConfigurationScript {
    param(
        [string]$Arguments
    )
    
    $scriptPath = Join-Path $PSScriptRoot "configure-deployment.py"
    
    if (-not (Test-Path $scriptPath)) {
        Write-ColoredOutput "❌ Error: configure-deployment.py not found at $scriptPath" "Red"
        return $false
    }
    
    try {
        $result = & python $scriptPath $Arguments.Split(' ')
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            Write-ColoredOutput "❌ Configuration script failed with exit code $LASTEXITCODE" "Red"
            return $false
        }
    } catch {
        Write-ColoredOutput "❌ Error running configuration script: $($_.Exception.Message)" "Red"
        return $false
    }
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Interactive mode
if ($Interactive -or (-not $Target -and -not $CustomDomain)) {
    do {
        $choice = Show-InteractiveMenu
        
        switch ($choice) {
            "1" {
                Write-Host ""
                Write-ColoredOutput "Configuring for localhost development..." "Yellow"
                $success = Invoke-ConfigurationScript "--target localhost"
                if ($success) {
                    Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
                    Write-ColoredOutput "You can now run: npm run dev:all" "Cyan"
                }
                break
            }
            "2" {
                Write-Host ""
                Write-ColoredOutput "Configuring for EC2 instance (13.215.240.173)..." "Yellow"
                $success = Invoke-ConfigurationScript "--target ec2"
                if ($success) {
                    Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
                    Write-ColoredOutput "Ready for EC2 deployment." "Cyan"
                }
                break
            }
            "3" {
                Write-Host ""
                $domain = Read-Host "Enter your production domain (e.g., https://myapp.com)"
                Write-ColoredOutput "Configuring for production domain: $domain" "Yellow"
                $success = Invoke-ConfigurationScript "--custom-domain `"$domain`""
                if ($success) {
                    Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
                }
                break
            }
            "4" {
                Write-Host ""
                $customDomain = Read-Host "Enter your domain/IP (e.g., http://192.168.1.100)"
                Write-ColoredOutput "Configuring for custom domain: $customDomain" "Yellow"
                $success = Invoke-ConfigurationScript "--custom-domain `"$customDomain`""
                if ($success) {
                    Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
                }
                break
            }
            "5" {
                Write-Host ""
                Write-ColoredOutput "Current configuration preview:" "Yellow"
                Invoke-ConfigurationScript "--target localhost --dry-run"
                break
            }
            "6" {
                Write-ColoredOutput "Goodbye!" "Green"
                exit 0
            }
            default {
                Write-ColoredOutput "Invalid choice. Please try again." "Red"
                continue
            }
        }
        
        Write-Host ""
        $continue = Read-Host "Press Enter to continue or 'q' to quit"
        if ($continue -eq 'q') {
            break
        }
    } while ($true)
    
    exit 0
}

# Non-interactive mode
if ($Target) {
    Write-ColoredOutput "Configuring for target: $Target" "Yellow"
    $arguments = "--target $Target"
    if ($DryRun) {
        $arguments += " --dry-run"
    }
    $success = Invoke-ConfigurationScript $arguments
    
    if ($success) {
        Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
    }
} elseif ($CustomDomain) {
    Write-ColoredOutput "Configuring for custom domain: $CustomDomain" "Yellow"
    $arguments = "--custom-domain `"$CustomDomain`""
    if ($DryRun) {
        $arguments += " --dry-run"
    }
    $success = Invoke-ConfigurationScript $arguments
    
    if ($success) {
        Write-ColoredOutput "✅ Configuration updated successfully!" "Green"
    }
} else {
    Write-ColoredOutput "❌ Error: Either -Target or -CustomDomain must be specified" "Red"
    Show-Usage
    exit 1
}
# Domain Configuration Script for AWS EC2 Deployment (PowerShell)
# This script helps easily configure domain settings across all deployment files

param(
    [Parameter(Mandatory=$false)]
    [string]$Domain = "",
    
    [Parameter(Mandatory=$false)]
    [string]$CertificateArn = "",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "prod",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$FrontendUrl = "",
    
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = "",
    
    [Parameter(Mandatory=$false)]
    [string]$WidgetUrl = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun,
    
    [Parameter(Mandatory=$false)]
    [switch]$Help
)

# Function to display usage information
function Show-Usage {
    Write-Host @"
Usage: .\configure-domain.ps1 [OPTIONS]

Configure domain settings for AWS EC2 deployment

OPTIONS:
    -Domain DOMAIN           Domain name (e.g., myapp.com)
    -CertificateArn ARN      SSL certificate ARN
    -Environment ENV         Environment (dev|staging|prod) [default: prod]
    -Region REGION           AWS region [default: us-east-1]
    -FrontendUrl URL         Frontend URL override
    -BackendUrl URL          Backend URL override
    -WidgetUrl URL           Widget URL override
    -DryRun                  Show what would be changed without applying
    -Help                    Show this help message

EXAMPLES:
    .\configure-domain.ps1 -Domain "myapp.com" -CertificateArn "arn:aws:acm:us-east-1:123456789012:certificate/abc123"
    .\configure-domain.ps1 -Domain "dev.myapp.com" -Environment "dev"
    .\configure-domain.ps1 -FrontendUrl "https://myapp.com" -BackendUrl "https://api.myapp.com"
    .\configure-domain.ps1 -DryRun -Domain "myapp.com"  # Preview changes

"@ -ForegroundColor Green
}

# Function to write colored log messages
function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet("INFO", "SUCCESS", "WARNING", "ERROR")]
        [string]$Level,
        
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    switch ($Level) {
        "INFO" { 
            Write-Host "[$timestamp] INFO: $Message" -ForegroundColor Blue 
        }
        "SUCCESS" { 
            Write-Host "[$timestamp] SUCCESS: $Message" -ForegroundColor Green 
        }
        "WARNING" { 
            Write-Host "[$timestamp] WARNING: $Message" -ForegroundColor Yellow 
        }
        "ERROR" { 
            Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red 
        }
    }
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Set script directory and project paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$TerraformDir = Join-Path $ScriptDir "..\terraform"
$DockerDir = Join-Path $ScriptDir "..\docker"

# Validate directories
if (-not (Test-Path $TerraformDir)) {
    Write-Log "ERROR" "Terraform directory not found: $TerraformDir"
    exit 1
}

# Generate URLs if domain is provided
if ($Domain) {
    if (-not $FrontendUrl) {
        if ($Environment -eq "prod") {
            $FrontendUrl = "https://$Domain"
        } else {
            $FrontendUrl = "https://$Environment.$Domain"
        }
    }
    
    if (-not $BackendUrl) {
        if ($Environment -eq "prod") {
            $BackendUrl = "https://api.$Domain"
        } else {
            $BackendUrl = "https://api-$Environment.$Domain"
        }
    }
    
    if (-not $WidgetUrl) {
        if ($Environment -eq "prod") {
            $WidgetUrl = "https://widget.$Domain"
        } else {
            $WidgetUrl = "https://widget-$Environment.$Domain"
        }
    }
}

# Function to update Terraform variables
function Update-TerraformVars {
    $tfvarsFile = Join-Path $TerraformDir "environments\$Environment.tfvars"
    
    if (-not (Test-Path $tfvarsFile)) {
        Write-Log "ERROR" "Terraform variables file not found: $tfvarsFile"
        return $false
    }
    
    Write-Log "INFO" "Updating Terraform variables: $tfvarsFile"
    
    if ($DryRun) {
        Write-Log "INFO" "[DRY RUN] Would update $tfvarsFile with:"
        if ($Domain) { Write-Host "  domain_name = `"$Domain`"" }
        if ($CertificateArn) { Write-Host "  certificate_arn = `"$CertificateArn`"" }
        if ($Region) { Write-Host "  aws_region = `"$Region`"" }
        return $true
    }
    
    # Create backup
    $backupFile = "$tfvarsFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $tfvarsFile $backupFile
    
    $content = Get-Content $tfvarsFile
    
    # Update domain_name
    if ($Domain) {
        $domainPattern = '^(#\s*)?domain_name\s*=.*'
        $domainReplacement = "domain_name = `"$Domain`""
        
        if ($content -match $domainPattern) {
            $content = $content -replace $domainPattern, $domainReplacement
        } else {
            $content += $domainReplacement
        }
        Write-Log "SUCCESS" "Updated domain_name to: $Domain"
    }
    
    # Update certificate_arn
    if ($CertificateArn) {
        $certPattern = '^(#\s*)?certificate_arn\s*=.*'
        $certReplacement = "certificate_arn = `"$CertificateArn`""
        
        if ($content -match $certPattern) {
            $content = $content -replace $certPattern, $certReplacement
        } else {
            $content += $certReplacement
        }
        Write-Log "SUCCESS" "Updated certificate_arn"
    }
    
    # Update aws_region
    if ($Region) {
        $regionPattern = '^aws_region\s*=.*'
        $regionReplacement = "aws_region = `"$Region`""
        
        if ($content -match $regionPattern) {
            $content = $content -replace $regionPattern, $regionReplacement
        } else {
            $content += $regionReplacement
        }
        Write-Log "SUCCESS" "Updated aws_region to: $Region"
    }
    
    # Write updated content back to file
    $content | Set-Content $tfvarsFile
    return $true
}

# Function to update frontend configuration
function Update-FrontendConfig {
    $configFiles = @(
        "$ProjectRoot\frontend\src\config\api.ts",
        "$ProjectRoot\frontend\src\config\api.js",
        "$ProjectRoot\src\config\api.ts",
        "$ProjectRoot\src\config\api.js"
    )
    
    foreach ($configFile in $configFiles) {
        if (Test-Path $configFile) {
            Write-Log "INFO" "Updating frontend config: $configFile"
            
            if ($DryRun) {
                Write-Log "INFO" "[DRY RUN] Would update $configFile with:"
                if ($BackendUrl) { Write-Host "  Backend URL: $BackendUrl" }
                if ($WidgetUrl) { Write-Host "  Widget URL: $WidgetUrl" }
                continue
            }
            
            # Create backup
            $backupFile = "$configFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item $configFile $backupFile
            
            $content = Get-Content $configFile -Raw
            
            # Update backend URL
            if ($BackendUrl) {
                $content = $content -replace "baseURL:\s*['\"][^'\"]*['\"],?", "baseURL: '$BackendUrl',"
                $content = $content -replace "BACKEND_URL\s*=\s*['\"][^'\"]*['\"];?", "BACKEND_URL = '$BackendUrl';"
                $content = $content -replace "const\s+API_BASE\s*=\s*['\"][^'\"]*['\"];?", "const API_BASE = '$BackendUrl';"
                Write-Log "SUCCESS" "Updated backend URL in: $configFile"
            }
            
            # Update widget URL
            if ($WidgetUrl) {
                $content = $content -replace "WIDGET_URL\s*=\s*['\"][^'\"]*['\"];?", "WIDGET_URL = '$WidgetUrl';"
                $content = $content -replace "const\s+WIDGET_BASE\s*=\s*['\"][^'\"]*['\"];?", "const WIDGET_BASE = '$WidgetUrl';"
                Write-Log "SUCCESS" "Updated widget URL in: $configFile"
            }
            
            # Write updated content back to file
            $content | Set-Content $configFile -NoNewline
        }
    }
}

# Function to update Docker environment files
function Update-DockerEnv {
    $envFiles = @(
        "$DockerDir\.env",
        "$DockerDir\.env.$Environment",
        "$ProjectRoot\.env",
        "$ProjectRoot\.env.$Environment"
    )
    
    foreach ($envFile in $envFiles) {
        if (Test-Path $envFile) {
            Write-Log "INFO" "Updating Docker environment: $envFile"
            
            if ($DryRun) {
                Write-Log "INFO" "[DRY RUN] Would update $envFile with domain settings"
                continue
            }
            
            # Create backup
            $backupFile = "$envFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            Copy-Item $envFile $backupFile
            
            $content = Get-Content $envFile
            
            # Update environment variables
            if ($FrontendUrl) {
                $frontendPattern = '^FRONTEND_URL\s*=.*'
                $frontendReplacement = "FRONTEND_URL=$FrontendUrl"
                
                if ($content -match $frontendPattern) {
                    $content = $content -replace $frontendPattern, $frontendReplacement
                } else {
                    $content += $frontendReplacement
                }
            }
            
            if ($BackendUrl) {
                $backendPattern = '^BACKEND_URL\s*=.*'
                $backendReplacement = "BACKEND_URL=$BackendUrl"
                
                if ($content -match $backendPattern) {
                    $content = $content -replace $backendPattern, $backendReplacement
                } else {
                    $content += $backendReplacement
                }
            }
            
            if ($WidgetUrl) {
                $widgetPattern = '^WIDGET_URL\s*=.*'
                $widgetReplacement = "WIDGET_URL=$WidgetUrl"
                
                if ($content -match $widgetPattern) {
                    $content = $content -replace $widgetPattern, $widgetReplacement
                } else {
                    $content += $widgetReplacement
                }
            }
            
            # Write updated content back to file
            $content | Set-Content $envFile
            Write-Log "SUCCESS" "Updated environment file: $envFile"
        }
    }
}

# Function to update nginx configuration
function Update-NginxConfig {
    $nginxConfig = Join-Path $DockerDir "nginx\nginx.conf"
    
    if (Test-Path $nginxConfig) {
        Write-Log "INFO" "Updating nginx configuration: $nginxConfig"
        
        if ($DryRun) {
            Write-Log "INFO" "[DRY RUN] Would update $nginxConfig with domain settings"
            return
        }
        
        # Create backup
        $backupFile = "$nginxConfig.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Copy-Item $nginxConfig $backupFile
        
        # Update server_name if domain is provided
        if ($Domain) {
            $content = Get-Content $nginxConfig -Raw
            $content = $content -replace "server_name\s+[^;]*;", "server_name $Domain;"
            $content | Set-Content $nginxConfig -NoNewline
            Write-Log "SUCCESS" "Updated nginx server_name to: $Domain"
        }
    }
}

# Main execution
function Main {
    Write-Log "INFO" "Starting domain configuration for environment: $Environment"
    
    if ($DryRun) {
        Write-Log "WARNING" "DRY RUN MODE - No files will be modified"
    }
    
    # Display configuration summary
    Write-Log "INFO" "Configuration Summary:"
    Write-Host "  Environment: $Environment"
    Write-Host "  Region: $Region"
    if ($Domain) { Write-Host "  Domain: $Domain" }
    if ($CertificateArn) { Write-Host "  Certificate ARN: $($CertificateArn.Substring(0, [Math]::Min(50, $CertificateArn.Length)))..." }
    if ($FrontendUrl) { Write-Host "  Frontend URL: $FrontendUrl" }
    if ($BackendUrl) { Write-Host "  Backend URL: $BackendUrl" }
    if ($WidgetUrl) { Write-Host "  Widget URL: $WidgetUrl" }
    Write-Host ""
    
    # Validate required parameters
    if (-not $Domain -and -not $FrontendUrl -and -not $BackendUrl) {
        Write-Log "ERROR" "At least one of -Domain, -FrontendUrl, or -BackendUrl must be provided"
        Show-Usage
        exit 1
    }
    
    # Update configurations
    $success = $true
    $success = $success -and (Update-TerraformVars)
    Update-FrontendConfig
    Update-DockerEnv
    Update-NginxConfig
    
    if ($DryRun) {
        Write-Log "INFO" "Dry run completed. Use without -DryRun to apply changes."
    } else {
        Write-Log "SUCCESS" "Domain configuration completed successfully!"
        Write-Log "INFO" "Next steps:"
        Write-Host "  1. Review the updated configuration files"
        Write-Host "  2. Run 'terraform plan' to preview infrastructure changes"
        Write-Host "  3. Run 'terraform apply' to deploy with new domain settings"
        Write-Host "  4. Update your DNS records to point to the load balancer"
    }
}

# Run main function
Main
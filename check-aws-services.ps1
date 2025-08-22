# AWS Service Status Check and Repair Script
# Check Docker container status and API endpoint availability on EC2 server

param(
    [string]$ServerIP = "13.215.240.173",
    [string]$KeyPath = "cc.pem",
    [string]$Username = "ubuntu",
    [switch]$AutoFix = $false
)

# Color output function
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Logging function
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path "aws-service-check.log" -Value $logMessage
}

# SSH command execution function
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$Description = ""
    )
    
    if ($Description) {
        Write-Log "Executing: $Description" "INFO"
    }
    
    try {
        $result = ssh -i $KeyPath -o StrictHostKeyChecking=no $Username@$ServerIP $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Command executed successfully: $Command" "SUCCESS"
            return $result
        } else {
            Write-Log "Command failed: $Command, Error: $result" "ERROR"
            return $null
        }
    } catch {
        Write-Log "SSH connection error: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

# Test API endpoint function
function Test-APIEndpoint {
    param(
        [string]$URL,
        [string]$Description,
        [int]$TimeoutSeconds = 10
    )
    
    Write-Log "Testing API endpoint: $Description ($URL)" "INFO"
    
    try {
        $response = Invoke-WebRequest -Uri $URL -TimeoutSec $TimeoutSeconds -UseBasicParsing
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200) {
            Write-ColorOutput "[OK] $Description - Status Code: $statusCode" "Green"
            Write-Log "API endpoint normal: $URL (Status Code: $statusCode)" "SUCCESS"
            return $true
        } else {
            Write-ColorOutput "[WARN] $Description - Status Code: $statusCode" "Yellow"
            Write-Log "API endpoint abnormal: $URL (Status Code: $statusCode)" "WARNING"
            return $false
        }
    } catch {
        Write-ColorOutput "[ERROR] $Description - Connection failed: $($_.Exception.Message)" "Red"
        Write-Log "API endpoint failed: $URL, Error: $($_.Exception.Message)" "ERROR"
        return $false
    }
}

# Check Docker container status
function Check-DockerContainers {
    Write-ColorOutput "`n=== Checking Docker Container Status ===" "Cyan"
    
    # Get all container status
    $containers = Invoke-SSHCommand "docker ps -a --format 'table {{.Names}}`t{{.Status}}`t{{.Ports}}'" "Get Docker container status"
    
    if ($containers) {
        Write-ColorOutput "Docker Container Status:" "White"
        $containers | ForEach-Object { Write-Host $_ }
        
        # Check specific containers
        $targetContainers = @("automotive-rasa", "automotive-rasa-actions", "automotive-backend", "automotive-frontend")
        
        foreach ($container in $targetContainers) {
            $status = Invoke-SSHCommand "docker ps --filter name=$container --format '{{.Status}}'" "Check container $container"
            
            if ($status) {
                if ($status -match "Up") {
                    Write-ColorOutput "[OK] ${container}: Running" "Green"
                } else {
                    Write-ColorOutput "[WARN] ${container}: $status" "Yellow"
                    
                    if ($AutoFix) {
                        Write-Log "Attempting to restart container: $container" "INFO"
                        Invoke-SSHCommand "docker restart $container" "Restart container $container"
                    }
                }
            } else {
                Write-ColorOutput "[ERROR] ${container}: Not found or stopped" "Red"
                
                if ($AutoFix) {
                    Write-Log "Attempting to start container: $container" "INFO"
                    Invoke-SSHCommand "docker start $container" "Start container $container"
                }
            }
        }
    } else {
        Write-ColorOutput "Unable to get Docker container information" "Red"
    }
}

# Check container logs
function Check-ContainerLogs {
    Write-ColorOutput "`n=== Checking Container Logs ===" "Cyan"
    
    $containers = @("automotive-rasa", "automotive-rasa-actions")
    
    foreach ($container in $containers) {
        Write-ColorOutput "`n--- $container Logs (Last 20 lines) ---" "Yellow"
        $logs = Invoke-SSHCommand "docker logs $container --tail 20" "Get $container logs"
        
        if ($logs) {
            $logs | ForEach-Object { Write-Host $_ }
            
            # Check for error keywords
            $errorKeywords = @("error", "exception", "failed", "traceback")
            $hasErrors = $false
            
            foreach ($keyword in $errorKeywords) {
                if ($logs -match $keyword) {
                    $hasErrors = $true
                    break
                }
            }
            
            if ($hasErrors) {
                Write-ColorOutput "[WARN] $container logs contain errors" "Red"
            } else {
                Write-ColorOutput "[OK] $container logs normal" "Green"
            }
        } else {
            Write-ColorOutput "Unable to get $container logs" "Red"
        }
    }
}

# Test all API endpoints
function Test-AllEndpoints {
    Write-ColorOutput "`n=== Testing API Endpoints ===" "Cyan"
    
    $endpoints = @(
        @{URL="http://$ServerIP:3000"; Description="Frontend Service"},
        @{URL="http://$ServerIP:8000"; Description="Backend API"},
        @{URL="http://$ServerIP:8000/health"; Description="Backend Health Check"},
        @{URL="http://$ServerIP:5005"; Description="Rasa Server"},
        @{URL="http://$ServerIP:5005/status"; Description="Rasa Status"},
        @{URL="http://$ServerIP:5055"; Description="Rasa Actions"}
    )
    
    $successCount = 0
    $totalCount = $endpoints.Count
    
    foreach ($endpoint in $endpoints) {
        if (Test-APIEndpoint -URL $endpoint.URL -Description $endpoint.Description) {
            $successCount++
        }
        Start-Sleep -Seconds 1
    }
    
    Write-ColorOutput "`nAPI Endpoint Test Results: $successCount/$totalCount successful" "Cyan"
    
    if ($successCount -lt $totalCount -and $AutoFix) {
        Write-Log "Some API endpoints failed, attempting to restart related services" "WARNING"
        Invoke-SSHCommand "docker-compose restart" "Restart all services"
    }
}

# Generate status report
function Generate-StatusReport {
    Write-ColorOutput "`n=== Generating Status Report ===" "Cyan"
    
    $reportPath = "aws-service-status-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    
    $report = @"
AWS EC2 Service Status Report
Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Server IP: $ServerIP

=== System Information ===
"@
    
    # Get system information
    $systemInfo = Invoke-SSHCommand "uname -a && df -h && free -h" "Get system information"
    if ($systemInfo) {
        $report += "`n$systemInfo`n"
    }
    
    # Get Docker information
    $dockerInfo = Invoke-SSHCommand "docker --version && docker-compose --version" "Get Docker version information"
    if ($dockerInfo) {
        $report += "`n=== Docker Information ===`n$dockerInfo`n"
    }
    
    # Get container status
    $containerStatus = Invoke-SSHCommand "docker ps -a" "Get container status"
    if ($containerStatus) {
        $report += "`n=== Container Status ===`n$containerStatus`n"
    }
    
    # Save report
    $report | Out-File -FilePath $reportPath -Encoding UTF8
    Write-ColorOutput "Status report saved to: $reportPath" "Green"
}

# Main function
function Main {
    Write-ColorOutput "AWS EC2 Service Status Check Script" "Cyan"
    Write-ColorOutput "Server: $ServerIP" "White"
    Write-ColorOutput "Auto Fix: $(if($AutoFix){'Enabled'}else{'Disabled'})" "White"
    Write-ColorOutput "Start Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
    
    # Clean old logs
    if (Test-Path "aws-service-check.log") {
        Remove-Item "aws-service-check.log" -Force
    }
    
    Write-Log "Starting AWS service status check" "INFO"
    
    # Check SSH key file
    if (-not (Test-Path $KeyPath)) {
        Write-ColorOutput "Error: SSH key file does not exist: $KeyPath" "Red"
        Write-Log "SSH key file does not exist: $KeyPath" "ERROR"
        return
    }
    
    # Test SSH connection
    Write-ColorOutput "`n=== Testing SSH Connection ===" "Cyan"
    $sshTest = Invoke-SSHCommand "echo 'SSH connection successful'" "Test SSH connection"
    
    if (-not $sshTest) {
        Write-ColorOutput "SSH connection failed, cannot continue" "Red"
        return
    }
    
    Write-ColorOutput "[OK] SSH connection normal" "Green"
    
    # Execute checks
    Check-DockerContainers
    Check-ContainerLogs
    Test-AllEndpoints
    Generate-StatusReport
    
    Write-ColorOutput "`n=== Check Complete ===" "Cyan"
    Write-ColorOutput "End Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "White"
    Write-Log "AWS service status check completed" "INFO"
}

# Execute main function
Main
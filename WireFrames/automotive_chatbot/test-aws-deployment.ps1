# AWS EC2 Deployment Test Script
# Tests all endpoints and verifies deployment status

param(
    [string]$EC2Host = "13.215.240.173",
    [string]$KeyPath = "../../cc.pem"
)

function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    switch ($Level) {
        "INFO" { Write-Host "[$timestamp] INFO: $Message" -ForegroundColor Cyan }
        "WARN" { Write-Host "[$timestamp] WARN: $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red }
        "SUCCESS" { Write-Host "[$timestamp] SUCCESS: $Message" -ForegroundColor Green }
    }
}

function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Name,
        [int]$TimeoutSeconds = 10
    )
    
    try {
        Write-Log "INFO" "Testing $Name at $Url"
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSeconds -UseBasicParsing
        
        if ($response.StatusCode -eq 200) {
            Write-Log "SUCCESS" "$Name is responding (Status: $($response.StatusCode))"
            return $true
        } else {
            Write-Log "WARN" "$Name returned status: $($response.StatusCode)"
            return $false
        }
    } catch {
        Write-Log "ERROR" "$Name failed: $($_.Exception.Message)"
        return $false
    }
}

Write-Log "INFO" "Starting AWS EC2 Deployment Test"
Write-Log "INFO" "Target EC2 Host: $EC2Host"

# Test 1: Check Docker containers status on EC2
Write-Log "INFO" "=== Testing Docker Containers Status ==="
try {
    $containerStatus = ssh -i $KeyPath -o StrictHostKeyChecking=no ubuntu@$EC2Host "docker-compose ps --format table" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Log "SUCCESS" "Docker containers status:"
        Write-Host $containerStatus
    } else {
        Write-Log "ERROR" "Failed to get container status: $containerStatus"
    }
} catch {
    Write-Log "ERROR" "SSH connection failed: $($_.Exception.Message)"
}

# Test 2: Check individual container logs
Write-Log "INFO" "=== Checking Container Logs ==="
$containers = @("frontend", "backend", "rasa")
foreach ($container in $containers) {
    try {
        Write-Log "INFO" "Checking $container logs..."
        $logs = ssh -i $KeyPath -o StrictHostKeyChecking=no ubuntu@$EC2Host "docker-compose logs --tail=5 $container" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "SUCCESS" "$container logs (last 5 lines):"
            Write-Host $logs
        } else {
            Write-Log "ERROR" "Failed to get $container logs: $logs"
        }
    } catch {
        Write-Log "ERROR" "Failed to check $container logs: $($_.Exception.Message)"
    }
    Write-Host ""
}

# Test 3: Test all endpoints
Write-Log "INFO" "=== Testing Application Endpoints ==="

$endpoints = @(
    @{Name="Frontend Main"; Url="http://$EC2Host"},
    @{Name="Test Widget"; Url="http://$EC2Host/test-client-widget.html"},
    @{Name="Backend Health"; Url="http://$EC2Host:8000/health"},
    @{Name="Backend API Docs"; Url="http://$EC2Host:8000/docs"},
    @{Name="Rasa API"; Url="http://$EC2Host:5005/"}
)

$successCount = 0
$totalCount = $endpoints.Count

foreach ($endpoint in $endpoints) {
    if (Test-Endpoint -Url $endpoint.Url -Name $endpoint.Name) {
        $successCount++
    }
    Start-Sleep -Seconds 2
}

# Test 4: Test chat functionality
Write-Log "INFO" "=== Testing Chat Functionality ==="
try {
    $chatPayload = @{
        message = "Hello, I need help with my car"
        user_id = "test_user_123"
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Uri "http://$EC2Host:8000/chat" -Method POST -Body $chatPayload -ContentType "application/json" -TimeoutSec 15
    
    if ($chatResponse) {
        Write-Log "SUCCESS" "Chat functionality is working"
        Write-Log "INFO" "Chat response: $($chatResponse | ConvertTo-Json -Depth 3)"
    } else {
        Write-Log "ERROR" "Chat functionality returned empty response"
    }
} catch {
    Write-Log "ERROR" "Chat functionality test failed: $($_.Exception.Message)"
}

# Summary
Write-Log "INFO" "=== Deployment Test Summary ==="
Write-Log "INFO" "Endpoints tested: $totalCount"
Write-Log "INFO" "Endpoints successful: $successCount"
Write-Log "INFO" "Success rate: $([math]::Round(($successCount / $totalCount) * 100, 2))%"

if ($successCount -eq $totalCount) {
    Write-Log "SUCCESS" "All endpoints are working correctly!"
    Write-Log "INFO" "Deployment appears to be successful"
} else {
    Write-Log "WARN" "Some endpoints are not responding correctly"
    Write-Log "INFO" "Please check the container logs and configuration"
}

Write-Log "INFO" "Test completed"
#!/usr/bin/env pwsh
# validate-deployment.ps1 - Validate AWS EC2 deployment for Automotive Chatbot
# This script validates the complete deployment including infrastructure, services, and endpoints

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "prod",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "ap-southeast-1",
    
    [Parameter(Mandatory=$false)]
    [string]$Domain = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$Verbose,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipHealthChecks,
    
    [Parameter(Mandatory=$false)]
    [int]$TimeoutSeconds = 300
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Enable verbose output if requested
if ($Verbose) {
    $VerbosePreference = "Continue"
}

# Color functions for output
function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-Host "\n🔍 $Message" -ForegroundColor Blue
}

# Validation functions
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    # Check AWS CLI
    try {
        $awsVersion = aws --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "AWS CLI is installed: $($awsVersion.Split(' ')[0])"
        } else {
            throw "AWS CLI not found"
        }
    } catch {
        Write-Error-Custom "AWS CLI is not installed or not in PATH"
        return $false
    }
    
    # Check AWS credentials
    try {
        $identity = aws sts get-caller-identity --output json 2>$null | ConvertFrom-Json
        if ($identity) {
            Write-Success "AWS credentials configured for account: $($identity.Account)"
        } else {
            throw "No AWS credentials"
        }
    } catch {
        Write-Error-Custom "AWS credentials not configured"
        return $false
    }
    
    # Check Terraform
    try {
        $terraformVersion = terraform version -json 2>$null | ConvertFrom-Json
        if ($terraformVersion) {
            Write-Success "Terraform is installed: $($terraformVersion.terraform_version)"
        } else {
            throw "Terraform not found"
        }
    } catch {
        Write-Error-Custom "Terraform is not installed or not in PATH"
        return $false
    }
    
    # Check jq
    try {
        $jqVersion = jq --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "jq is installed: $jqVersion"
        } else {
            throw "jq not found"
        }
    } catch {
        Write-Warning-Custom "jq is not installed - some features may not work"
    }
    
    return $true
}

function Test-TerraformState {
    Write-Step "Validating Terraform state..."
    
    $terraformDir = Join-Path $PSScriptRoot "..\terraform"
    Push-Location $terraformDir
    
    try {
        # Initialize Terraform
        Write-Info "Initializing Terraform..."
        terraform init -backend=true 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to initialize Terraform"
            return $false
        }
        
        # Validate configuration
        Write-Info "Validating Terraform configuration..."
        terraform validate
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Terraform configuration is invalid"
            return $false
        }
        Write-Success "Terraform configuration is valid"
        
        # Check if state exists
        Write-Info "Checking Terraform state..."
        $stateList = terraform state list 2>$null
        if ($LASTEXITCODE -eq 0 -and $stateList) {
            Write-Success "Terraform state exists with $($stateList.Count) resources"
            return $true
        } else {
            Write-Warning-Custom "No Terraform state found - infrastructure may not be deployed"
            return $false
        }
    } catch {
        Write-Error-Custom "Error validating Terraform state: $($_.Exception.Message)"
        return $false
    } finally {
        Pop-Location
    }
}

function Get-TerraformOutputs {
    Write-Step "Retrieving Terraform outputs..."
    
    $terraformDir = Join-Path $PSScriptRoot "..\terraform"
    Push-Location $terraformDir
    
    try {
        $outputs = terraform output -json 2>$null | ConvertFrom-Json
        if ($LASTEXITCODE -eq 0 -and $outputs) {
            Write-Success "Retrieved Terraform outputs successfully"
            return $outputs
        } else {
            Write-Error-Custom "Failed to retrieve Terraform outputs"
            return $null
        }
    } catch {
        Write-Error-Custom "Error retrieving Terraform outputs: $($_.Exception.Message)"
        return $null
    } finally {
        Pop-Location
    }
}

function Test-Infrastructure {
    param([object]$Outputs)
    
    Write-Step "Validating AWS infrastructure..."
    
    if (-not $Outputs) {
        Write-Error-Custom "No Terraform outputs available"
        return $false
    }
    
    $allValid = $true
    
    # Check VPC
    if ($Outputs.vpc_id -and $Outputs.vpc_id.value) {
        $vpcId = $Outputs.vpc_id.value
        try {
            $vpc = aws ec2 describe-vpcs --vpc-ids $vpcId --output json 2>$null | ConvertFrom-Json
            if ($vpc.Vpcs -and $vpc.Vpcs.Count -gt 0) {
                Write-Success "VPC exists: $vpcId"
            } else {
                Write-Error-Custom "VPC not found: $vpcId"
                $allValid = $false
            }
        } catch {
            Write-Error-Custom "Error checking VPC: $($_.Exception.Message)"
            $allValid = $false
        }
    }
    
    # Check ALB
    if ($Outputs.alb_arn -and $Outputs.alb_arn.value) {
        $albArn = $Outputs.alb_arn.value
        try {
            $alb = aws elbv2 describe-load-balancers --load-balancer-arns $albArn --output json 2>$null | ConvertFrom-Json
            if ($alb.LoadBalancers -and $alb.LoadBalancers.Count -gt 0) {
                $albState = $alb.LoadBalancers[0].State.Code
                if ($albState -eq "active") {
                    Write-Success "ALB is active: $($alb.LoadBalancers[0].DNSName)"
                } else {
                    Write-Warning-Custom "ALB state is: $albState"
                }
            } else {
                Write-Error-Custom "ALB not found: $albArn"
                $allValid = $false
            }
        } catch {
            Write-Error-Custom "Error checking ALB: $($_.Exception.Message)"
            $allValid = $false
        }
    }
    
    # Check Auto Scaling Group
    if ($Outputs.auto_scaling_group_name -and $Outputs.auto_scaling_group_name.value) {
        $asgName = $Outputs.auto_scaling_group_name.value
        try {
            $asg = aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $asgName --output json 2>$null | ConvertFrom-Json
            if ($asg.AutoScalingGroups -and $asg.AutoScalingGroups.Count -gt 0) {
                $instances = $asg.AutoScalingGroups[0].Instances
                $healthyInstances = ($instances | Where-Object { $_.HealthStatus -eq "Healthy" }).Count
                Write-Success "Auto Scaling Group has $healthyInstances healthy instances out of $($instances.Count) total"
            } else {
                Write-Error-Custom "Auto Scaling Group not found: $asgName"
                $allValid = $false
            }
        } catch {
            Write-Error-Custom "Error checking Auto Scaling Group: $($_.Exception.Message)"
            $allValid = $false
        }
    }
    
    return $allValid
}

function Test-ApplicationEndpoints {
    param([object]$Outputs)
    
    if ($SkipHealthChecks) {
        Write-Info "Skipping health checks as requested"
        return $true
    }
    
    Write-Step "Testing application endpoints..."
    
    if (-not $Outputs) {
        Write-Error-Custom "No Terraform outputs available"
        return $false
    }
    
    $baseUrl = ""
    if ($Domain) {
        $baseUrl = "https://$Domain"
    } elseif ($Outputs.application_url -and $Outputs.application_url.value) {
        $baseUrl = $Outputs.application_url.value
    } elseif ($Outputs.alb_dns_name -and $Outputs.alb_dns_name.value) {
        $baseUrl = "http://$($Outputs.alb_dns_name.value)"
    } else {
        Write-Error-Custom "No application URL available"
        return $false
    }
    
    Write-Info "Testing endpoints for: $baseUrl"
    
    $allValid = $true
    $endpoints = @(
        @{ Path = "/"; Name = "Frontend" },
        @{ Path = "/health"; Name = "Backend Health" },
        @{ Path = "/api/health"; Name = "API Health" },
        @{ Path = "/api/docs"; Name = "API Documentation" }
    )
    
    foreach ($endpoint in $endpoints) {
        $url = "$baseUrl$($endpoint.Path)"
        try {
            Write-Info "Testing $($endpoint.Name): $url"
            $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Success "$($endpoint.Name) is responding (200 OK)"
            } else {
                Write-Warning-Custom "$($endpoint.Name) returned status: $($response.StatusCode)"
            }
        } catch {
            Write-Error-Custom "$($endpoint.Name) failed: $($_.Exception.Message)"
            $allValid = $false
        }
    }
    
    return $allValid
}

function Test-DatabaseConnectivity {
    param([object]$Outputs)
    
    Write-Step "Testing database connectivity..."
    
    # This would require the application to be running and accessible
    # For now, we'll just check if the MongoDB URI parameter exists in SSM
    try {
        $paramName = "/automotive-chatbot/$Environment/mongodb_uri"
        $param = aws ssm get-parameter --name $paramName --with-decryption --output json 2>$null | ConvertFrom-Json
        if ($param -and $param.Parameter) {
            Write-Success "MongoDB URI parameter exists in SSM Parameter Store"
            return $true
        } else {
            Write-Error-Custom "MongoDB URI parameter not found in SSM"
            return $false
        }
    } catch {
        Write-Error-Custom "Error checking MongoDB URI parameter: $($_.Exception.Message)"
        return $false
    }
}

function Write-ValidationSummary {
    param([bool]$AllTestsPassed, [object]$Outputs)
    
    Write-Host "\n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Blue
    Write-Host "DEPLOYMENT VALIDATION SUMMARY" -ForegroundColor Blue
    Write-Host "=" * 60 -ForegroundColor Blue
    
    if ($AllTestsPassed) {
        Write-Success "All validation tests passed! 🎉"
        Write-Host ""
        Write-Info "Your AWS EC2 deployment is ready to use:"
        
        if ($Outputs) {
            if ($Domain) {
                Write-Host "  Application URL: https://$Domain" -ForegroundColor Green
                Write-Host "  API URL: https://$Domain/api" -ForegroundColor Green
            } elseif ($Outputs.application_url -and $Outputs.application_url.value) {
                Write-Host "  Application URL: $($Outputs.application_url.value)" -ForegroundColor Green
                Write-Host "  API URL: $($Outputs.api_url.value)" -ForegroundColor Green
            }
            
            if ($Outputs.alb_dns_name -and $Outputs.alb_dns_name.value) {
                Write-Host "  Load Balancer DNS: $($Outputs.alb_dns_name.value)" -ForegroundColor Green
            }
        }
    } else {
        Write-Error-Custom "Some validation tests failed! ❌"
        Write-Host ""
        Write-Info "Please check the errors above and fix any issues before using the deployment."
    }
    
    Write-Host "\nNext steps:"
    Write-Host "  1. Test the application functionality manually"
    Write-Host "  2. Monitor CloudWatch logs for any issues"
    Write-Host "  3. Set up monitoring and alerting"
    Write-Host "  4. Configure backup and disaster recovery"
    
    Write-Host "\n" -NoNewline
    Write-Host "=" * 60 -ForegroundColor Blue
}

# Main execution
function Main {
    Write-Host "AWS EC2 Deployment Validation Script" -ForegroundColor Blue
    Write-Host "Environment: $Environment | Region: $Region" -ForegroundColor Blue
    if ($Domain) {
        Write-Host "Domain: $Domain" -ForegroundColor Blue
    }
    Write-Host ""
    
    $allTestsPassed = $true
    
    # Test prerequisites
    if (-not (Test-Prerequisites)) {
        $allTestsPassed = $false
    }
    
    # Test Terraform state
    if (-not (Test-TerraformState)) {
        $allTestsPassed = $false
    }
    
    # Get Terraform outputs
    $outputs = Get-TerraformOutputs
    
    # Test infrastructure
    if (-not (Test-Infrastructure -Outputs $outputs)) {
        $allTestsPassed = $false
    }
    
    # Test application endpoints
    if (-not (Test-ApplicationEndpoints -Outputs $outputs)) {
        $allTestsPassed = $false
    }
    
    # Test database connectivity
    if (-not (Test-DatabaseConnectivity -Outputs $outputs)) {
        $allTestsPassed = $false
    }
    
    # Write summary
    Write-ValidationSummary -AllTestsPassed $allTestsPassed -Outputs $outputs
    
    # Exit with appropriate code
    if ($allTestsPassed) {
        exit 0
    } else {
        exit 1
    }
}

# Run main function
Main
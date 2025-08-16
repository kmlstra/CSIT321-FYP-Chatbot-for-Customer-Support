# Load environment variables from backend/.env file
# This script is used by npm scripts to load environment variables

$envFile = "backend\.env"

if (Test-Path $envFile) {
    Write-Host "Loading environment variables from $envFile" -ForegroundColor Green
    
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Remove quotes if present
            if ($value -match '^"(.*)"$') {
                $value = $matches[1]
            }
            
            # Set environment variable
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "  $name = $value" -ForegroundColor Gray
        }
    }
    
    Write-Host "Environment variables loaded successfully" -ForegroundColor Green
} else {
    Write-Host "Warning: $envFile not found" -ForegroundColor Yellow
}
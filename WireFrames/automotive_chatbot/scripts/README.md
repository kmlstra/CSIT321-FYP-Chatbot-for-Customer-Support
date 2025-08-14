# Dynamic Deployment Configuration Scripts

This directory contains scripts that solve the problem of hardcoded URLs by providing an easy way to switch between different deployment configurations (localhost, EC2, production) without manually editing multiple files.

## Problem Solved

Previously, switching between localhost development and EC2/production deployment required:
- Manually editing multiple configuration files
- Hardcoding URLs in various places
- Risk of forgetting to update all necessary files
- No easy way to switch back and forth

## Solution

The new dynamic configuration system provides:
- **One command** to switch between deployment targets
- **Automatic updates** of all configuration files
- **Easy switching** between localhost, EC2, and custom domains
- **No hardcoding** - all URLs are generated dynamically
- **Cross-platform support** (Windows, Linux, macOS)

## Quick Start

### Windows Users

#### Option 1: Interactive Menu (Easiest)
```powershell
# Run the interactive configuration tool
.\scripts\configure-deployment.ps1 -Interactive
```

#### Option 2: Direct Commands
```powershell
# Configure for localhost development
.\scripts\configure-deployment.ps1 -Target localhost

# Configure for EC2 deployment
.\scripts\configure-deployment.ps1 -Target ec2

# Configure for custom domain
.\scripts\configure-deployment.ps1 -CustomDomain "http://192.168.1.100"
```

#### Option 3: Batch File (Alternative)
```cmd
# Run the batch file for a simple menu
scripts\configure-deployment.bat
```

### Linux/macOS Users

```bash
# Configure for localhost development
python3 scripts/configure-deployment.py --target localhost

# Configure for EC2 deployment
python3 scripts/configure-deployment.py --target ec2

# Configure for custom domain
python3 scripts/configure-deployment.py --custom-domain "http://192.168.1.100"
```

## Available Scripts

### 1. `configure-deployment.py` (Core Script)
The main Python script that handles all configuration updates.

**Features:**
- Updates `backend/.env`
- Updates `backend/endpoints.yml` (RASA configuration)
- Updates `aws-deployment/environments/.env.production`
- Updates `aws-deployment/config/domain-config.json`
- Supports dry-run mode
- Cross-platform compatibility

**Usage:**
```bash
python configure-deployment.py --target localhost
python configure-deployment.py --target ec2
python configure-deployment.py --custom-domain "http://your-domain.com"
python configure-deployment.py --dry-run --target localhost  # Preview changes
```

### 2. `configure-deployment.ps1` (Windows PowerShell)
User-friendly PowerShell wrapper with interactive menu.

**Features:**
- Interactive menu system
- Colored output
- Error handling
- Both interactive and command-line modes

### 3. `configure-deployment.bat` (Windows Batch)
Simple batch file for users who prefer traditional Windows batch scripts.

## Configuration Targets

### 1. Localhost (Development)
```
Domain: http://localhost
Frontend: http://localhost:3000
Backend: http://localhost:8001
RASA: http://localhost:5005
RASA Actions: http://localhost:5055
SSL: Disabled
```

**Use case:** Local development and testing

### 2. EC2 Instance
```
Domain: http://54.254.180.103
Frontend: http://54.254.180.103:3000
Backend: http://54.254.180.103:8001
RASA: http://54.254.180.103:5005
RASA Actions: http://54.254.180.103:5055
SSL: Disabled
```

**Use case:** Deployment to AWS EC2 instance

### 3. Custom Domain
```
Domain: [Your specified domain]
Ports: Configurable
SSL: Configurable
```

**Use case:** Production deployment with custom domain or different IP address

## Files Updated

When you run the configuration script, it automatically updates:

1. **`backend/.env`**
   - `DOMAIN`
   - `FRONTEND_URL`
   - `BACKEND_URL`
   - `RASA_URL`
   - `RASA_ACTIONS_URL`
   - `RASA_ACTION_ENDPOINT_URL`

2. **`backend/endpoints.yml`**
   - RASA action endpoint URL

3. **`aws-deployment/environments/.env.production`**
   - All domain-related environment variables for Docker deployment

4. **`aws-deployment/config/domain-config.json`**
   - Domain configuration for AWS deployment scripts

## Examples

### Switching from Localhost to EC2

```powershell
# Currently working on localhost
npm run dev:all  # Running locally

# Need to deploy to EC2
.\scripts\configure-deployment.ps1 -Target ec2

# Now all configuration files point to EC2 instance
# Ready for Docker deployment
```

### Testing with Custom IP

```powershell
# Configure for a different test server
.\scripts\configure-deployment.ps1 -CustomDomain "http://192.168.1.100"

# All services now configured for the test server
```

### Preview Changes (Dry Run)

```powershell
# See what would be changed without making changes
.\scripts\configure-deployment.ps1 -Target ec2 -DryRun
```

## Workflow Examples

### Development Workflow
1. **Start development:** `configure-deployment.ps1 -Target localhost`
2. **Run services:** `npm run dev:all`
3. **Test locally:** Visit `http://localhost:3000`

### Deployment Workflow
1. **Configure for EC2:** `configure-deployment.ps1 -Target ec2`
2. **Build and deploy:** Use Docker deployment scripts
3. **Test deployment:** Visit `http://54.254.180.103:3000`

### Switching Back
1. **Return to development:** `configure-deployment.ps1 -Target localhost`
2. **Continue development:** `npm run dev:all`

## Troubleshooting

### Common Issues

1. **"Python not found" error**
   - Ensure Python 3 is installed and in your PATH
   - Try `python3` instead of `python`

2. **"Permission denied" error**
   - Run PowerShell as Administrator
   - Or use: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

3. **"File not found" error**
   - Ensure you're running the script from the project root directory
   - Check that all configuration files exist

### Verification

After running the configuration script, verify the changes:

```bash
# Check backend environment
cat backend/.env | grep DOMAIN

# Check RASA endpoints
cat backend/endpoints.yml

# Check Docker environment (if exists)
cat aws-deployment/environments/.env.production | grep DOMAIN
```

## Advanced Usage

### Custom Port Configuration

To use different ports, modify the `CONFIG_TEMPLATES` in `configure-deployment.py`:

```python
"custom": {
    "domain": "http://your-domain.com",
    "frontend_port": "80",
    "backend_port": "80",
    "rasa_port": "5005",
    "rasa_actions_port": "5055",
    "ssl_enabled": True
}
```

### Adding New Environments

To add a new environment configuration:

1. Add a new template to `CONFIG_TEMPLATES` in `configure-deployment.py`
2. Update the argument parser to include the new target
3. Test with `--dry-run` first

## Benefits

✅ **No more hardcoded URLs**
✅ **One command to switch environments**
✅ **Automatic file updates**
✅ **Cross-platform support**
✅ **Dry-run capability**
✅ **Interactive and command-line modes**
✅ **Error handling and validation**
✅ **Easy to extend for new environments**

## Next Steps

After configuring your deployment target:

1. **For localhost:** Run `npm run dev:all`
2. **For EC2:** Use the AWS deployment scripts
3. **For production:** Set up SSL certificates and DNS

This system eliminates the need to manually edit configuration files and makes switching between development and deployment environments effortless!
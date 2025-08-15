# Deployment Process Documentation

## Overview
This document provides a comprehensive guide for deploying the Automotive Chatbot application to AWS EC2. Follow these exact steps to prevent recreating files and facing the same deployment issues repeatedly.

## Prerequisites

### Required Software
- Docker Desktop (running)
- PowerShell 5.0 or later
- SSH client
- Git

### Required Files
- `cc.pem` - SSH private key (located at project root)
- AWS EC2 instance running Ubuntu
- EC2 Security Groups configured for ports 80, 443, 22

## Deployment Files Structure

### Active Deployment Scripts (DO NOT DELETE)
```
├── deploy-to-ec2.ps1          # Main deployment script (RECOMMENDED)
├── ssh-deploy.ps1             # Alternative deployment script
├── aws-deployment/
│   ├── docker/
│   │   ├── Dockerfile.frontend
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.rasa
│   │   ├── docker-compose.yml
│   │   └── nginx.conf
│   └── scripts/               # Advanced deployment scripts
```

### Unused Files (CAN BE DELETED)
```
├── build-for-deployment.ps1   # Superseded by deploy-to-ec2.ps1
├── deploy-to-aws.ps1          # Old version
├── docker-build.ps1           # Integrated into main scripts
├── docker-push.ps1            # Not used in current workflow
├── quick-deploy.ps1           # Duplicate functionality
├── load-env.ps1               # Not used
├── switch-environment.ps1     # Not used
├── chatbot_test_report_*.json # Old test reports
├── .tmp-rasa.tar*             # Temporary files
```

## Step-by-Step Deployment Process

### Method 1: Using deploy-to-ec2.ps1 (RECOMMENDED)

1. **Navigate to project directory**
   ```powershell
   cd "d:\CSIT321-FYP-Chatbot-for-Customer-Support\WireFrames\automotive_chatbot"
   ```

2. **Verify prerequisites**
   ```powershell
   # Check Docker is running
   docker --version
   
   # Check SSH key exists
   Test-Path "../../cc.pem"
   ```

3. **Run deployment script**
   ```powershell
   .\deploy-to-ec2.ps1
   ```

4. **Monitor deployment progress**
   - Script will build Docker images locally
   - Save images as compressed tar files
   - Copy files to EC2 instance
   - Load images and start containers

5. **Verify deployment**
   - Frontend: http://54.254.180.103
   - Test Widget: http://54.254.180.103/test-client-widget.html
   - Backend API: http://54.254.180.103/api/health

### Method 2: Using ssh-deploy.ps1 (ALTERNATIVE)

1. **Navigate to project directory**
   ```powershell
   cd "d:\CSIT321-FYP-Chatbot-for-Customer-Support\WireFrames\automotive_chatbot"
   ```

2. **Run alternative deployment script**
   ```powershell
   .\ssh-deploy.ps1
   ```

## Configuration Details

### Environment Variables
The deployment uses production environment variables:
- `NEXT_PUBLIC_API_URL=http://54.254.180.103/api`
- `NEXT_PUBLIC_RASA_URL=http://54.254.180.103:5005`
- `NODE_ENV=production`

### Endpoints Configuration

#### AWS-Specific Endpoints
The project includes separate endpoint configurations for different environments:

**Local Development**: `backend/endpoints.yml` (auto-generated)
- Action endpoint: `http://localhost:5055/webhook`
- Used for local development and testing

**AWS Production**: `backend/endpoints-aws.yml`
- Action endpoint: `http://54.254.180.103:5055/webhook`
- Pre-configured for AWS EC2 deployment
- **Important**: This file is used automatically during AWS deployment

#### Environment-Specific Configuration
The system automatically selects the correct endpoints file based on the deployment environment:

```yaml
# Local Development (endpoints.yml)
action_endpoint:
  url: "http://localhost:5055/webhook"

# AWS Production (endpoints-aws.yml)
action_endpoint:
  url: "http://54.254.180.103:5055/webhook"
```

#### Configuration Files Location
```
backend/
├── endpoints.yml         # Auto-generated for local development
├── endpoints-aws.yml     # Pre-configured for AWS deployment
├── .env                  # Environment variables
└── requirements.txt      # Python dependencies
```

**Note**: The `endpoints.yml` file is auto-generated and should not be manually edited. For AWS deployment, the system uses the pre-configured `endpoints-aws.yml` file.

### Docker Images Built
1. **Frontend**: `csit321fyp/automotive-chatbot-frontend:latest`
2. **Backend**: `csit321fyp/automotive-chatbot-backend:latest`
3. **Rasa**: `automotive-chatbot-rasa:latest`

### Services Started
- Frontend (Next.js) on port 80
- Backend (FastAPI) on port 8000
- Rasa on port 5005
- Nginx reverse proxy

## Troubleshooting

### Common Issues and Solutions

#### 1. "SSH key file not found"
**Problem**: Script cannot find SSH key
**Solution**: Ensure `cc.pem` is at project root with correct permissions
```powershell
# Check key exists
Test-Path "../../cc.pem"

# Fix permissions if needed (on Linux/WSL)
chmod 600 ../../cc.pem
```

#### 2. "Docker build failed"
**Problem**: Docker build context issues
**Solution**: Ensure you're in the correct directory and Docker is running
```powershell
# Verify current directory
Get-Location

# Should be: ...\automotive_chatbot

# Check Docker status
docker info
```

#### 3. "Permission denied (publickey)"
**Problem**: SSH authentication failed
**Solution**: Verify EC2 key pair and security groups
```powershell
# Test SSH connection
ssh -i "../../cc.pem" ubuntu@54.254.180.103 "echo 'Connection successful'"
```

#### 4. "Frontend shows localhost errors"
**Problem**: Environment variables not set correctly
**Solution**: Verify production environment variables in docker-compose.yml

#### 5. "Rasa training failed"
**Problem**: Complex config.yml causing training errors
**Solution**: Use simplified config or fix training data structure

### Health Check Commands

```bash
# On EC2 instance
sudo docker ps                    # Check running containers
sudo docker-compose logs          # View all logs
sudo docker-compose logs frontend # View specific service logs
sudo docker system df             # Check disk usage
```

## Deployment Workflow Summary

1. **Local Build Phase**
   - Build Docker images locally
   - Save as compressed tar files
   - Validate image creation

2. **Transfer Phase**
   - Copy docker-compose.yml to EC2
   - Copy environment files
   - Transfer image tar files

3. **Remote Deployment Phase**
   - Load Docker images on EC2
   - Stop existing containers
   - Start new containers
   - Verify deployment

4. **Cleanup Phase**
   - Remove temporary files
   - Clean up old images
   - Verify services running

## Best Practices

1. **Always test locally first**
   ```powershell
   npm run dev:all
   # Test at http://localhost:3000/test-client-widget.html
   ```

2. **Backup before deployment**
   - Create EC2 snapshot
   - Backup database if applicable

3. **Monitor deployment logs**
   - Watch for errors during build
   - Verify all services start correctly

4. **Use consistent naming**
   - Don't change image names
   - Keep file paths consistent

5. **Clean up regularly**
   - Remove old test reports
   - Clean Docker images
   - Remove temporary files

## Emergency Rollback

If deployment fails:

1. **SSH to EC2 instance**
   ```bash
   ssh -i "../../cc.pem" ubuntu@54.254.180.103
   ```

2. **Stop problematic containers**
   ```bash
   sudo docker-compose down
   ```

3. **Restore previous version**
   ```bash
   # If you have backup images
   sudo docker-compose up -d
   ```

4. **Check logs for issues**
   ```bash
   sudo docker-compose logs
   ```

## Maintenance Schedule

- **Weekly**: Clean up old Docker images and containers
- **Monthly**: Update dependencies and rebuild images
- **Quarterly**: Review and update deployment scripts

---

**Last Updated**: January 2025
**Deployment Target**: AWS EC2 (54.254.180.103)
**Maintainer**: Development Team
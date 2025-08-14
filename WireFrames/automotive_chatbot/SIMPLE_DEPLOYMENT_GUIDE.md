# Simple Docker Desktop to AWS Deployment Guide

This guide provides a straightforward approach to deploy the Automotive Chatbot to AWS using Docker Desktop and SSH.

## Overview

The deployment process involves:
1. **Build** Docker containers locally using Docker Desktop
2. **Push** containers to Docker Hub
3. **Deploy** via SSH to EC2 instance `54.254.180.103`

## Prerequisites

### Local Requirements
- Docker Desktop installed and running
- Docker Hub account
- SSH key for EC2 access
- PowerShell (Windows)

### AWS Requirements
- EC2 instance: `54.254.180.103` (Ubuntu)
- Security groups allowing:
  - SSH (port 22)
  - HTTP (port 80)
  - Backend API (port 8000)
  - Rasa API (port 5005)

## Step-by-Step Deployment

### Step 1: Configure Scripts

Update the following variables in all scripts:

```powershell
# In docker-build.ps1, docker-push.ps1, and ssh-deploy.ps1
$DOCKER_USERNAME = "your-actual-dockerhub-username"

# In ssh-deploy.ps1 only
$SSH_KEY_PATH = "C:\path\to\your\key.pem"
$EC2_USER = "ubuntu"  # or "ec2-user" for Amazon Linux
```

### Step 2: Build Containers Locally

```powershell
# Run from project root directory
.\docker-build.ps1
```

This script will:
- Check Docker Desktop status
- Build frontend, backend, and Rasa containers
- Tag images with your Docker Hub username

### Step 3: Push to Docker Hub

```powershell
# Push containers to Docker Hub
.\docker-push.ps1
```

This script will:
- Login to Docker Hub (you'll be prompted for credentials)
- Push all three containers to your Docker Hub repository

### Step 4: Deploy to AWS EC2

```powershell
# Deploy to EC2 via SSH
.\ssh-deploy.ps1
```

This script will:
- Connect to EC2 via SSH
- Install Docker if not present
- Pull your containers from Docker Hub
- Start all services with proper networking
- Configure environment variables

## Application Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │     Rasa        │
│   (Port 80)     │◄──►│   (Port 8000)   │◄──►│   (Port 5005)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │    MongoDB      │
                       │   (Port 27017)  │
                       └─────────────────┘
```

## Access URLs (After Deployment)

- **Frontend**: `http://54.254.180.103`
- **Test Widget**: `http://54.254.180.103/test-client-widget.html`
- **Backend API**: `http://54.254.180.103:8000`
- **Rasa API**: `http://54.254.180.103:5005`

## Container Details

### Frontend Container
- **Base**: nginx:alpine
- **Port**: 80
- **Content**: React application with chatbot widget

### Backend Container
- **Base**: python:3.9-slim
- **Port**: 8000
- **Framework**: FastAPI
- **Features**: REST API, MongoDB integration, Rasa communication

### Rasa Container
- **Base**: rasa/rasa:latest
- **Port**: 5005
- **Features**: NLU, dialogue management, custom actions

### MongoDB Container
- **Base**: mongo:latest
- **Port**: 27017
- **Credentials**: admin/password123

## Troubleshooting

### Common Issues

1. **Docker Desktop not running**
   ```
   Error: Cannot connect to the Docker daemon
   Solution: Start Docker Desktop
   ```

2. **SSH connection failed**
   ```
   Error: Permission denied (publickey)
   Solution: Check SSH key path and permissions
   ```

3. **Container build failed**
   ```
   Error: Build failed
   Solution: Check Dockerfile syntax and dependencies
   ```

4. **Port conflicts on EC2**
   ```
   Error: Port already in use
   Solution: Stop existing containers first
   ```

### Verification Commands

```bash
# On EC2 instance, check running containers
sudo docker ps

# Check container logs
sudo docker logs automotive-frontend
sudo docker logs automotive-backend
sudo docker logs automotive-rasa
sudo docker logs automotive-mongodb

# Check network connectivity
sudo docker network ls
sudo docker network inspect chatbot-network
```

## Alternative: Docker Compose Deployment

For simpler management, you can also use the provided `docker-compose.yml`:

```bash
# On EC2 instance
sudo docker-compose up -d

# Stop all services
sudo docker-compose down

# View logs
sudo docker-compose logs
```

## Security Notes

- Change default MongoDB credentials in production
- Use environment variables for sensitive data
- Configure proper firewall rules
- Use HTTPS in production (add SSL certificates)
- Regularly update container images

## Maintenance

### Updating the Application

1. Make code changes locally
2. Run `docker-build.ps1` to rebuild containers
3. Run `docker-push.ps1` to push updates
4. Run `ssh-deploy.ps1` to redeploy

### Monitoring

- Check application logs regularly
- Monitor resource usage on EC2
- Set up health checks for containers
- Monitor MongoDB performance

## Support

If you encounter issues:
1. Check container logs
2. Verify network connectivity
3. Ensure all ports are accessible
4. Check EC2 security group settings
5. Verify Docker Hub image availability
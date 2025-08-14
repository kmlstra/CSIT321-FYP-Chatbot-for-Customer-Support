# 🚀 AWS EC2 Server Management Guide

This guide provides comprehensive instructions for managing your automotive chatbot application on AWS EC2 instance `54.254.180.103`.

## 📋 Table of Contents
- [SSH Connection](#ssh-connection)
- [Quick Start Commands](#quick-start-commands)
- [Service Management](#service-management)
- [Monitoring & Logs](#monitoring--logs)
- [Troubleshooting](#troubleshooting)
- [Deployment](#deployment)

## 🔐 SSH Connection

### Connect to EC2 Instance
```bash
# From your local machine
ssh -i "d:\CSIT321-FYP-Chatbot-for-Customer-Support\cc.pem" ubuntu@54.254.180.103
```

### Navigate to Project Directory
```bash
cd /home/ubuntu/automotive_chatbot
```

## ⚡ Quick Start Commands

### Start All Services (One Command)
```bash
# Start all Docker containers
docker-compose up -d

# Alternative: Start with rebuild
docker-compose up -d --build
```

### Stop All Services
```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clean shutdown)
docker-compose down -v
```

### Restart All Services
```bash
# Restart all containers
docker-compose restart

# Restart with rebuild
docker-compose down && docker-compose up -d --build
```

## 🛠️ Service Management

### Individual Service Control

#### Frontend Service
```bash
# Start frontend only
docker-compose up -d frontend

# Stop frontend
docker-compose stop frontend

# Restart frontend
docker-compose restart frontend

# Rebuild and start frontend
docker-compose up -d --build frontend
```

#### Backend API Service
```bash
# Start backend only
docker-compose up -d backend

# Stop backend
docker-compose stop backend

# Restart backend
docker-compose restart backend

# Rebuild and start backend
docker-compose up -d --build backend
```

#### RASA Chatbot Service
```bash
# Start RASA only
docker-compose up -d rasa

# Stop RASA
docker-compose stop rasa

# Restart RASA
docker-compose restart rasa

# Rebuild and start RASA
docker-compose up -d --build rasa
```

### Check Service Status
```bash
# Check all running containers
docker ps

# Check all containers (including stopped)
docker ps -a

# Check specific service status
docker-compose ps

# Check container health
docker stats
```

## 📊 Monitoring & Logs

### View Logs

#### All Services Logs
```bash
# View all logs (real-time)
docker-compose logs -f

# View last 100 lines of all logs
docker-compose logs --tail=100
```

#### Individual Service Logs
```bash
# Frontend logs
docker-compose logs -f frontend
docker logs automotive_chatbot-frontend-1

# Backend logs
docker-compose logs -f backend
docker logs automotive_chatbot-backend-1

# RASA logs
docker-compose logs -f rasa
docker logs automotive_chatbot-rasa-1
```

#### Log Management
```bash
# Clear logs for a container
docker logs --since 0s container_name > /dev/null

# View logs from last hour
docker-compose logs --since 1h

# View logs with timestamps
docker-compose logs -t
```

### System Monitoring
```bash
# Check disk usage
df -h

# Check memory usage
free -h

# Check CPU usage
top

# Check Docker system usage
docker system df

# Check port usage
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :8000
sudo netstat -tulpn | grep :5005
```

## 🔧 Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check Docker daemon
sudo systemctl status docker

# Restart Docker daemon
sudo systemctl restart docker

# Check for port conflicts
sudo lsof -i :80
sudo lsof -i :8000
sudo lsof -i :5005
```

#### Container Issues
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Full cleanup (CAUTION: removes everything)
docker system prune -a
```

#### Network Issues
```bash
# Check Docker networks
docker network ls

# Inspect network
docker network inspect automotive_chatbot_default

# Test connectivity between containers
docker exec automotive_chatbot-frontend-1 ping backend
docker exec automotive_chatbot-backend-1 ping rasa
```

### Emergency Recovery
```bash
# Force stop all containers
docker kill $(docker ps -q)

# Remove all containers
docker rm $(docker ps -aq)

# Rebuild everything from scratch
docker-compose down -v
docker system prune -a
docker-compose up -d --build
```

## 🚀 Deployment

### Deploy New Version
```bash
# Pull latest code (if using git)
git pull origin main

# Rebuild and deploy
docker-compose down
docker-compose up -d --build

# Check deployment status
docker-compose ps
docker-compose logs -f
```

### Health Checks
```bash
# Test frontend
curl -I http://54.254.180.103

# Test backend API
curl -I http://54.254.180.103:8000/docs

# Test RASA API
curl -I http://54.254.180.103:5005

# Test widget functionality
curl http://54.254.180.103/test-client-widget.html
```

### Backup & Restore
```bash
# Backup volumes
docker run --rm -v automotive_chatbot_data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Restore volumes
docker run --rm -v automotive_chatbot_data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

## 📱 Service URLs

- **Frontend**: http://54.254.180.103
- **Backend API**: http://54.254.180.103:8000
- **API Documentation**: http://54.254.180.103:8000/docs
- **RASA API**: http://54.254.180.103:5005
- **Widget Test**: http://54.254.180.103/test-client-widget.html

## 🔄 Environment Switching

### Switch to Local Development
```bash
# From your local machine
.\scripts\switch-to-local.ps1
```

### Switch to AWS Production
```bash
# From your local machine
.\scripts\switch-to-aws.ps1
```

## 📞 Support

If you encounter issues:
1. Check the logs first: `docker-compose logs -f`
2. Verify all services are running: `docker-compose ps`
3. Test connectivity: Use the health check commands
4. If all else fails, perform a clean restart: `docker-compose down && docker-compose up -d --build`

---

**Last Updated**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
**Server**: 54.254.180.103
**Environment**: AWS EC2 Production
# 🚀 Automotive Chatbot - Docker Deployment

This directory contains all the necessary files and scripts for deploying the Automotive Chatbot to AWS EC2 using Docker.

## 📁 Directory Structure

```
deploy/
├── README.md                     # This file - deployment overview
├── docker-compose.yml            # Production Docker Compose configuration
├── Dockerfile.backend            # Backend service Docker image
├── Dockerfile.frontend           # Frontend service Docker image
├── .env.production               # Production environment template
├── deploy-to-ec2.sh             # Linux/Mac deployment script
├── deploy-to-ec2.ps1             # Windows PowerShell deployment script
├── DOCKER_DEPLOYMENT_GUIDE.md    # Comprehensive deployment guide
└── LOCAL_TESTING_GUIDE.md        # Local testing instructions
```

## 🎯 Quick Start

### Prerequisites
- AWS EC2 instance (Ubuntu 20.04 LTS recommended)
- EC2 Security Group with ports 22, 80, 443, 3000, 8001, 5005 open
- PEM key file for SSH access
- Docker installed locally (for testing)

### One-Command Deployment

**Windows (PowerShell):**
```powershell
.\deploy-to-ec2.ps1 -EC2IP "YOUR_EC2_PUBLIC_IP" -PemKey "C:\path\to\your\key.pem"
```

**Linux/Mac (Bash):**
```bash
./deploy-to-ec2.sh YOUR_EC2_PUBLIC_IP /path/to/your/key.pem
```

### Manual Deployment

1. **Copy environment file:**
   ```bash
   cp .env.production .env
   ```

2. **Edit environment variables:**
   - Replace `your-ec2-public-ip` with your actual EC2 IP
   - Configure database and API keys

3. **Upload to EC2:**
   ```bash
   scp -i your-key.pem -r ../automotive_chatbot ubuntu@YOUR_EC2_IP:~/
   ```

4. **Deploy on EC2:**
   ```bash
   ssh -i your-key.pem ubuntu@YOUR_EC2_IP
   cd automotive_chatbot/deploy
   docker-compose up --build -d
   ```

## 📋 Deployment Files

### Core Docker Files

#### `docker-compose.yml`
- **Purpose**: Orchestrates all services (frontend, backend, RASA)
- **Features**: Production-ready configuration with health checks, restart policies, and resource limits
- **Services**:
  - `frontend`: React application (port 3000)
  - `backend`: FastAPI application (port 8001)
  - `rasa`: RASA chatbot engine (port 5005)

#### `Dockerfile.backend`
- **Purpose**: Builds the FastAPI backend service
- **Features**: Multi-stage build, optimized Python environment, security best practices
- **Base Image**: `python:3.9-slim`

#### `Dockerfile.frontend`
- **Purpose**: Builds the React frontend service
- **Features**: Multi-stage build, optimized Node.js environment, production build
- **Base Image**: `node:18-alpine`

### Configuration Files

#### `.env.production`
- **Purpose**: Template for production environment variables
- **Contains**: API URLs, database connections, security settings
- **Usage**: Copy to `.env` and customize for your deployment

### Deployment Scripts

#### `deploy-to-ec2.sh` (Linux/Mac)
- **Purpose**: Automated deployment script for Unix-based systems
- **Features**:
  - Prerequisites checking
  - EC2 connection testing
  - Docker installation
  - File upload with rsync
  - Environment configuration
  - Application deployment
  - Health verification

#### `deploy-to-ec2.ps1` (Windows)
- **Purpose**: Automated deployment script for Windows PowerShell
- **Features**: Same as bash script but PowerShell compatible
- **Requirements**: OpenSSH client or WSL

### Documentation

#### `DOCKER_DEPLOYMENT_GUIDE.md`
- **Purpose**: Comprehensive step-by-step deployment guide
- **Covers**:
  - AWS EC2 setup
  - Security group configuration
  - Manual deployment process
  - Troubleshooting
  - Production best practices
  - Monitoring and maintenance

#### `LOCAL_TESTING_GUIDE.md`
- **Purpose**: Instructions for testing Docker setup locally
- **Covers**:
  - Docker installation
  - Local environment setup
  - Testing procedures
  - Debugging tips
  - Performance testing

## 🔧 Configuration

### Environment Variables

Key variables to configure in `.env`:

```env
# API URLs (replace with your EC2 IP)
REACT_APP_API_URL=http://your-ec2-public-ip:8001
REACT_APP_RASA_URL=http://your-ec2-public-ip:5005
REACT_APP_WEBSOCKET_URL=ws://your-ec2-public-ip:8001

# Environment
ENVIRONMENT=production
DEBUG=false

# Security
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-ec2-public-ip,localhost

# Database (if using external DB)
DATABASE_URL=postgresql://user:pass@host:port/db

# CORS
CORS_ORIGINS=http://your-ec2-public-ip:3000
```

### Port Configuration

| Service  | Internal Port | External Port | Purpose |
|----------|---------------|---------------|---------|
| Frontend | 3000          | 3000          | React app |
| Backend  | 8001          | 8001          | FastAPI |
| RASA     | 5005          | 5005          | Chatbot API |

## 🛠️ Management Commands

### Container Management
```bash
# View status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update and restart
docker-compose up --build -d
```

### System Monitoring
```bash
# Resource usage
docker stats

# System info
docker system df

# Clean up
docker system prune -f
```

## 🔍 Health Checks

### Service Endpoints
- **Frontend**: `http://YOUR_EC2_IP:3000`
- **Backend Health**: `http://YOUR_EC2_IP:8001/health`
- **Backend Docs**: `http://YOUR_EC2_IP:8001/docs`
- **RASA Version**: `http://YOUR_EC2_IP:5005/version`

### Quick Health Check
```bash
# Test all services
curl http://YOUR_EC2_IP:8001/health
curl http://YOUR_EC2_IP:5005/version
curl http://YOUR_EC2_IP:3000
```

## 🚨 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   docker-compose logs [service_name]
   ```

2. **Port conflicts**
   ```bash
   sudo netstat -tlnp | grep :8001
   ```

3. **Permission issues**
   ```bash
   sudo chown -R $USER:$USER ~/automotive_chatbot
   ```

4. **Memory issues**
   ```bash
   free -h
   docker stats
   ```

### Log Analysis
```bash
# Real-time logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f rasa

# Last N lines
docker-compose logs --tail=50 backend
```

## 🔒 Security Considerations

### Production Security
- Use HTTPS with SSL certificates
- Configure firewall rules
- Use strong passwords and API keys
- Regular security updates
- Monitor access logs

### Environment Security
- Never commit `.env` files
- Use IAM roles instead of hardcoded credentials
- Rotate secrets regularly
- Limit network access

## 📊 Performance Optimization

### Resource Limits
Configured in `docker-compose.yml`:
- Memory limits per service
- CPU allocation
- Restart policies

### Monitoring
- Container resource usage
- Application response times
- Error rates and logs
- System health metrics

## 🎯 Production Checklist

- [ ] EC2 instance properly sized
- [ ] Security groups configured
- [ ] Environment variables set
- [ ] SSL certificates installed
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Health checks working
- [ ] Performance tested
- [ ] Documentation updated

## 📞 Support

For deployment issues:

1. Check the troubleshooting section
2. Review container logs
3. Verify network connectivity
4. Check system resources
5. Consult the deployment guides

## 🔄 Updates and Maintenance

### Updating the Application
1. Pull latest code
2. Update environment variables if needed
3. Run deployment script again
4. Verify deployment

### Regular Maintenance
- Monitor system resources
- Update Docker images
- Clean up old containers and images
- Review and rotate secrets
- Update system packages

---

**🎉 Ready to Deploy!**

Your Automotive Chatbot is ready for production deployment on AWS EC2 using Docker. Choose your deployment method and follow the guides for a successful deployment.

For detailed instructions, see:
- `DOCKER_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `LOCAL_TESTING_GUIDE.md` - Local testing instructions
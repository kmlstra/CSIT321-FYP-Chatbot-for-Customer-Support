# Automotive Chatbot Deployment Guide

This comprehensive guide covers the deployment of the Automotive Chatbot system across different environments (development, staging, production) with support for both Linux and Windows platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Environment Setup](#environment-setup)
4. [Deployment Options](#deployment-options)
5. [Configuration](#configuration)
6. [Security Setup](#security-setup)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Backup and Recovery](#backup-and-recovery)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB free space
- **OS**: Ubuntu 20.04+ / Windows 10+
- **Network**: Internet connectivity

#### Recommended for Production
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+ SSD
- **OS**: Ubuntu 20.04 LTS
- **Network**: High-speed internet with static IP

### Required Software

#### Linux (Ubuntu)
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git unzip software-properties-common

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Python
sudo apt install -y python3 python3-pip python3-venv
```

#### Windows
```powershell
# Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install required packages
choco install -y git nodejs python docker-desktop
```

### Cloud Services Setup

#### MongoDB Atlas
1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster
3. Configure network access (whitelist IP addresses)
4. Create database user
5. Get connection string

#### AWS Account (for production)
1. Create AWS account
2. Set up IAM user with appropriate permissions
3. Configure AWS CLI
4. Create S3 buckets for backups
5. Set up CloudWatch for monitoring

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd automotive_chatbot
```

### 2. Environment Configuration
```bash
# Copy environment template
cp deploy/env_template.txt deploy/.env

# Edit environment variables
nano deploy/.env  # Linux
# or
notepad deploy\.env  # Windows
```

### 3. Deploy Application

#### Linux
```bash
# Make scripts executable
chmod +x deploy/*.sh

# Run deployment
sudo ./deploy/deploy.sh
```

#### Windows
```powershell
# Run as Administrator
.\deploy\deploy.ps1
```

### 4. Verify Deployment
```bash
# Check service status
docker-compose -f docker-compose.production.yml ps

# Run health checks
./deploy/deployment_validation.sh quick
```

## Environment Setup

### Development Environment

```bash
# Set environment
export DEPLOYMENT_ENV=development

# Use development configuration
docker-compose -f docker-compose.yml up -d

# Enable hot reload
npm run dev  # Frontend
python backend/main.py --reload  # Backend
```

### Staging Environment

```bash
# Set environment
export DEPLOYMENT_ENV=staging

# Deploy to staging
./deploy/deploy.sh

# Run integration tests
./deploy/deployment_validation.sh full
```

### Production Environment

```bash
# Set environment
export DEPLOYMENT_ENV=production

# Deploy to production
./deploy/deploy.sh

# Enable monitoring
./deploy/monitoring_setup.sh

# Set up SSL
./deploy/ssl_setup.sh your-domain.com admin@your-domain.com
```

## Deployment Options

### Option 1: Single Server Deployment

Suitable for small to medium applications.

```bash
# Deploy all services on single server
./deploy/deploy.sh
```

**Pros:**
- Simple setup
- Lower cost
- Easy maintenance

**Cons:**
- Single point of failure
- Limited scalability

### Option 2: AWS EC2 Deployment

Recommended for production environments.

```bash
# Configure AWS credentials
aws configure

# Deploy to EC2
./deploy/aws_ec2_deploy.sh

# Set up load balancer
./deploy/aws_setup_lb.sh
```

**Pros:**
- High availability
- Auto-scaling
- Managed services

**Cons:**
- Higher complexity
- Higher cost

### Option 3: Docker Swarm Deployment

For multi-server deployments without Kubernetes complexity.

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.swarm.yml automotive-chatbot
```

### Option 4: Kubernetes Deployment

For large-scale, enterprise deployments.

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n automotive-chatbot
```

## Configuration

### Environment Variables

Create `.env` file in the `deploy/` directory:

```bash
# Application Configuration
APP_NAME=automotive-chatbot
APP_VERSION=1.0.0
APP_DOMAIN=your-domain.com
DEPLOYMENT_ENV=production

# Security Configuration
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key
SESSION_SECRET=your-session-secret

# Database Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/automotive_chatbot
REDIS_URL=redis://localhost:6379

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=automotive-chatbot-backups

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring Configuration
PROMETHEUS_RETENTION_TIME=30d
GRAFANA_ADMIN_PASSWORD=secure-password
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# SSL Configuration
SSL_EMAIL=admin@your-domain.com
SSL_DOMAIN=your-domain.com
```

### Service Configuration

#### Frontend Configuration
```javascript
// frontend/.env.production
REACT_APP_API_URL=https://api.your-domain.com
REACT_APP_ENVIRONMENT=production
REACT_APP_VERSION=1.0.0
```

#### Backend Configuration
```python
# backend/config/production.py
class ProductionConfig:
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.getenv('MONGODB_URI')
    REDIS_URL = os.getenv('REDIS_URL')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET')
```

#### RASA Configuration
```yaml
# rasa/config.yml
recipe: default.v1
language: en
pipeline:
  - name: WhitespaceTokenizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: DIETClassifier
    epochs: 100
    constrain_similarities: true
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
    constrain_similarities: true
  - name: FallbackClassifier
    threshold: 0.3
    ambiguity_threshold: 0.1

policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: UnexpecTEDIntentPolicy
    max_history: 5
    epochs: 100
  - name: TEDPolicy
    max_history: 5
    epochs: 100
    constrain_similarities: true
```

## Security Setup

### SSL/TLS Configuration

#### Automatic SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Manual SSL Certificate
```bash
# Generate private key
openssl genrsa -out server.key 2048

# Generate certificate signing request
openssl req -new -key server.key -out server.csr

# Generate self-signed certificate (for testing)
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```

### Firewall Configuration

#### UFW (Ubuntu)
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application ports
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend API

# Check status
sudo ufw status
```

#### Windows Firewall
```powershell
# Allow inbound traffic
New-NetFirewallRule -DisplayName "HTTP" -Direction Inbound -Protocol TCP -LocalPort 80
New-NetFirewallRule -DisplayName "HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443
New-NetFirewallRule -DisplayName "Frontend" -Direction Inbound -Protocol TCP -LocalPort 3000
New-NetFirewallRule -DisplayName "Backend" -Direction Inbound -Protocol TCP -LocalPort 8000
```

### Security Hardening

```bash
# Run security setup script
./deploy/security_setup.sh

# This script will:
# - Configure fail2ban
# - Set up intrusion detection
# - Harden SSH configuration
# - Configure automatic security updates
# - Set up audit logging
```

## Monitoring and Logging

### Prometheus Setup

```bash
# Install and configure Prometheus
./deploy/monitoring_setup.sh

# Access Prometheus
# http://your-domain.com:9090
```

### Grafana Setup

```bash
# Access Grafana
# http://your-domain.com:3001
# Default login: admin/admin

# Import dashboards
# - System Overview
# - Application Metrics
# - RASA Performance
```

### Log Management

#### Centralized Logging
```bash
# Configure rsyslog
sudo nano /etc/rsyslog.conf

# Add log forwarding
*.* @@log-server:514

# Restart rsyslog
sudo systemctl restart rsyslog
```

#### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/automotive-chatbot

# Add configuration
/var/log/automotive-chatbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 automotive-chatbot automotive-chatbot
    postrotate
        systemctl reload automotive-chatbot
    endscript
}
```

## Backup and Recovery

### Automated Backups

```bash
# Set up automated backups
./deploy/backup_recovery.sh setup

# Manual backup
./deploy/backup_recovery.sh backup

# List backups
./deploy/backup_recovery.sh list

# Restore from backup
./deploy/backup_recovery.sh restore <backup-id>
```

### Backup Schedule

```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * /opt/automotive-chatbot/deploy/backup_recovery.sh backup

# Weekly full backup on Sunday at 3 AM
0 3 * * 0 /opt/automotive-chatbot/deploy/backup_recovery.sh backup_full
```

### Disaster Recovery

#### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop application
   docker-compose down
   
   # Restore database
   ./deploy/backup_recovery.sh restore_database <backup-date>
   
   # Start application
   docker-compose up -d
   ```

2. **Full System Recovery**
   ```bash
   # Restore from backup
   ./deploy/backup_recovery.sh restore_full <backup-date>
   
   # Verify restoration
   ./deploy/deployment_validation.sh full
   ```

3. **Cross-Region Recovery**
   ```bash
   # Sync from backup region
   aws s3 sync s3://backup-bucket-region2 s3://backup-bucket-region1
   
   # Deploy in new region
   AWS_REGION=us-west-2 ./deploy/deploy.sh
   ```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service logs
docker-compose logs <service-name>

# Check system resources
htop
df -h

# Check port conflicts
sudo netstat -tulpn | grep <port>
```

#### 2. Database Connection Issues

```bash
# Test MongoDB connection
mongosh "$MONGODB_URI" --eval "db.runCommand('ping')"

# Test Redis connection
redis-cli ping

# Check network connectivity
telnet <host> <port>
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /etc/ssl/certs/server.crt -text -noout

# Test SSL connection
openssl s_client -connect your-domain.com:443

# Renew Let's Encrypt certificate
sudo certbot renew --dry-run
```

#### 4. Performance Issues

```bash
# Check system performance
top
iotop
netstat -i

# Check application metrics
curl http://localhost:8000/metrics

# Check database performance
mongosh --eval "db.runCommand({serverStatus: 1})"
```

### Debug Mode

```bash
# Enable debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
docker-compose restart

# View debug logs
docker-compose logs -f
```

### Health Checks

```bash
# Run comprehensive health check
./deploy/deployment_validation.sh full

# Quick health check
./deploy/deployment_validation.sh quick

# Security audit
./deploy/deployment_validation.sh security

# Performance test
./deploy/deployment_validation.sh performance
```

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Monitor system health
- Check backup status
- Review error logs
- Monitor resource usage

#### Weekly
- Update system packages
- Review security logs
- Test backup restoration
- Performance optimization

#### Monthly
- Security audit
- Capacity planning
- Disaster recovery testing
- Documentation updates

### Update Procedures

#### Application Updates

```bash
# 1. Backup current version
./deploy/backup_recovery.sh backup

# 2. Pull latest code
git pull origin main

# 3. Build new version
docker-compose build

# 4. Deploy with zero downtime
./deploy/deploy.sh

# 5. Verify deployment
./deploy/deployment_validation.sh quick

# 6. Rollback if needed
./deploy/deploy.sh rollback
```

#### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# Update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Restart services
sudo systemctl restart docker
docker-compose restart
```

### Performance Optimization

```bash
# Run system optimization
./deploy/system_optimization.sh apply

# Monitor performance
./deploy/system_optimization.sh monitor

# Generate performance report
./deploy/system_optimization.sh report
```

### Scaling

#### Horizontal Scaling

```bash
# Scale specific service
docker-compose up -d --scale backend=3

# Auto-scaling with Docker Swarm
docker service update --replicas 5 automotive-chatbot_backend
```

#### Vertical Scaling

```bash
# Update resource limits
# Edit docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G

# Apply changes
docker-compose up -d
```

## Support and Documentation

### Getting Help

- **Documentation**: Check this README and inline comments
- **Logs**: Review application and system logs
- **Monitoring**: Use Grafana dashboards for insights
- **Health Checks**: Run validation scripts

### Useful Commands

```bash
# View deployment status
./deploy/deploy.sh status

# View logs
./deploy/deploy.sh logs

# Run health check
./deploy/deployment_validation.sh

# Create backup
./deploy/backup_recovery.sh backup

# Monitor performance
./deploy/system_optimization.sh monitor
```

### Configuration Files

- `deploy/.env` - Environment variables
- `deploy/deployment_config.yml` - Deployment configuration
- `docker-compose.production.yml` - Production services
- `nginx/nginx.conf` - Web server configuration
- `prometheus/prometheus.yml` - Monitoring configuration

---

**Note**: This deployment guide is comprehensive but may need adjustments based on your specific environment and requirements. Always test deployments in a staging environment before applying to production.

For additional support or questions, please refer to the project documentation or contact the development team.
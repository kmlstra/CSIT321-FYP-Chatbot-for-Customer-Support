# 🚀 Docker Deployment Guide for AWS EC2

This guide provides step-by-step instructions for deploying the Automotive Chatbot to AWS EC2 using Docker.

## 📋 Prerequisites

### Local Machine Requirements
- Docker Desktop installed and running
- SSH client (OpenSSH for Windows, built-in for Linux/Mac)
- Git (for cloning the repository)
- PowerShell (Windows) or Bash (Linux/Mac)

### AWS Requirements
- AWS EC2 instance (Ubuntu 20.04 LTS recommended)
- EC2 instance with at least 2GB RAM and 20GB storage
- Security Group configured with required ports
- PEM key file for SSH access
- Elastic IP (recommended for production)

## 🔧 AWS EC2 Setup

### 1. Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Navigate to AWS Console → EC2 → Launch Instance

2. **Choose AMI**
   - Select "Ubuntu Server 20.04 LTS (HVM), SSD Volume Type"
   - Architecture: 64-bit (x86)

3. **Choose Instance Type**
   - Minimum: `t3.small` (2 vCPU, 2 GB RAM)
   - Recommended: `t3.medium` (2 vCPU, 4 GB RAM)
   - Production: `t3.large` or higher

4. **Configure Instance**
   - Keep default settings
   - Enable "Auto-assign Public IP"

5. **Add Storage**
   - Minimum: 20 GB General Purpose SSD (gp3)
   - Recommended: 30 GB for logs and data

6. **Configure Security Group**
   ```
   Type            Protocol    Port Range    Source
   SSH             TCP         22            Your IP/0.0.0.0/0
   HTTP            TCP         80            0.0.0.0/0
   HTTPS           TCP         443           0.0.0.0/0
   Custom TCP      TCP         3000          0.0.0.0/0  (Frontend)
   Custom TCP      TCP         8001          0.0.0.0/0  (Backend API)
   Custom TCP      TCP         5005          0.0.0.0/0  (RASA API)
   ```

7. **Launch Instance**
   - Create or select existing key pair
   - Download PEM key file
   - Keep it secure (chmod 400 on Linux/Mac)

### 2. Elastic IP (Recommended)

1. **Allocate Elastic IP**
   - Go to EC2 → Elastic IPs → Allocate Elastic IP address
   - Choose "Amazon's pool of IPv4 addresses"

2. **Associate with Instance**
   - Select the allocated IP → Actions → Associate Elastic IP address
   - Choose your EC2 instance

## 🐳 Docker Deployment Process

### Method 1: Automated Deployment (Recommended)

#### For Windows Users:

```powershell
# Navigate to project directory
cd "D:\CSIT321-FYP-Chatbot-for-Customer-Support\WireFrames\automotive_chatbot"

# Run deployment script
.\deploy\deploy-to-ec2.ps1 -EC2IP "YOUR_EC2_PUBLIC_IP" -PemKey "C:\path\to\your\key.pem"
```

#### For Linux/Mac Users:

```bash
# Navigate to project directory
cd /path/to/automotive_chatbot

# Make script executable
chmod +x deploy/deploy-to-ec2.sh

# Run deployment script
./deploy/deploy-to-ec2.sh YOUR_EC2_PUBLIC_IP /path/to/your/key.pem
```

### Method 2: Manual Deployment

#### Step 1: Connect to EC2 Instance

```bash
# Replace with your actual values
ssh -i /path/to/your/key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

#### Step 2: Install Docker and Docker Compose

```bash
# Update package index
sudo apt-get update

# Install required packages
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package index
sudo apt-get update

# Install Docker Engine
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Log out and log back in for group changes to take effect
exit
```

#### Step 3: Upload Project Files

**Option A: Using Git (if repository is public)**
```bash
# On EC2 instance
git clone https://github.com/your-username/automotive-chatbot.git
cd automotive-chatbot
```

**Option B: Using SCP (from local machine)**
```bash
# From your local machine
scp -i /path/to/your/key.pem -r ./automotive_chatbot ubuntu@YOUR_EC2_PUBLIC_IP:~/
```

**Option C: Using rsync (recommended)**
```bash
# From your local machine
rsync -avz --progress --exclude='node_modules' --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv' --exclude='logs' --exclude='cache' --exclude='.next' -e "ssh -i /path/to/your/key.pem" ./automotive_chatbot/ ubuntu@YOUR_EC2_PUBLIC_IP:~/automotive_chatbot/
```

#### Step 4: Configure Environment

```bash
# On EC2 instance
cd ~/automotive_chatbot/deploy

# Copy environment template
cp .env.production .env

# Edit environment file
nano .env
```

**Update the following in .env:**
```env
# Replace YOUR_EC2_PUBLIC_IP with actual IP
REACT_APP_API_URL=http://YOUR_EC2_PUBLIC_IP:8001
REACT_APP_RASA_URL=http://YOUR_EC2_PUBLIC_IP:5005
REACT_APP_WEBSOCKET_URL=ws://YOUR_EC2_PUBLIC_IP:8001

# Set production values
ENVIRONMENT=production
DEBUG=false

# Configure your database and other services
```

#### Step 5: Deploy Application

```bash
# Navigate to deploy directory
cd ~/automotive_chatbot/deploy

# Build and start containers
docker-compose up --build -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔍 Verification and Testing

### 1. Check Container Status

```bash
# Check if all containers are running
docker-compose ps

# Expected output:
#        Name                      Command               State           Ports
# automotive_backend    uvicorn main:app --host 0.0.0.0   Up      0.0.0.0:8001->8001/tcp
# automotive_frontend   docker-entrypoint.sh npm start   Up      0.0.0.0:3000->3000/tcp
# automotive_rasa       rasa run --enable-api --cors ... Up      0.0.0.0:5005->5005/tcp
```

### 2. Test Application Endpoints

```bash
# Test backend API
curl http://YOUR_EC2_PUBLIC_IP:8001/health

# Test RASA API
curl http://YOUR_EC2_PUBLIC_IP:5005/version

# Test frontend (should return HTML)
curl http://YOUR_EC2_PUBLIC_IP:3000
```

### 3. Access Application

Open your web browser and navigate to:
- **Frontend**: `http://YOUR_EC2_PUBLIC_IP:3000`
- **Backend API Docs**: `http://YOUR_EC2_PUBLIC_IP:8001/docs`
- **RASA API**: `http://YOUR_EC2_PUBLIC_IP:5005`

## 🛠️ Management Commands

### Container Management

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Restart specific service
docker-compose restart [service_name]

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
docker-compose up --build -d
```

### System Monitoring

```bash
# Check system resources
htop

# Check disk usage
df -h

# Check Docker disk usage
docker system df

# Clean up unused Docker resources
docker system prune -f
```

### Log Management

```bash
# View real-time logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f rasa

# View last N lines of logs
docker-compose logs --tail=50 backend
```

## 🔒 Security Best Practices

### 1. Firewall Configuration

```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow application ports
sudo ufw allow 3000
sudo ufw allow 8001
sudo ufw allow 5005

# Check status
sudo ufw status
```

### 2. SSL/TLS Setup (Production)

For production deployment, set up SSL certificates:

```bash
# Install Certbot
sudo apt-get install certbot

# Install Nginx
sudo apt-get install nginx

# Configure Nginx as reverse proxy
# Edit /etc/nginx/sites-available/default
```

### 3. Environment Security

- Never commit `.env` files to version control
- Use strong passwords and API keys
- Regularly update system packages
- Monitor access logs
- Use IAM roles instead of hardcoded credentials

## 🚨 Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs for errors
docker-compose logs [service_name]

# Check if ports are available
sudo netstat -tlnp | grep :8001

# Restart Docker service
sudo systemctl restart docker
```

#### 2. Out of Memory

```bash
# Check memory usage
free -h

# Check Docker memory usage
docker stats

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. Permission Issues

```bash
# Fix Docker permissions
sudo usermod -aG docker $USER

# Fix file permissions
sudo chown -R $USER:$USER ~/automotive_chatbot
```

#### 4. Network Issues

```bash
# Check if services are listening
sudo netstat -tlnp

# Test internal connectivity
docker-compose exec backend curl http://localhost:8001/health

# Check Docker networks
docker network ls
```

### Performance Optimization

#### 1. Resource Limits

Add resource limits to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

#### 2. Log Rotation

```bash
# Configure Docker log rotation
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 📊 Monitoring and Maintenance

### 1. Health Checks

Create a monitoring script:

```bash
#!/bin/bash
# health-check.sh

echo "Checking application health..."

# Check backend
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is down"
fi

# Check RASA
if curl -f http://localhost:5005/version > /dev/null 2>&1; then
    echo "✅ RASA is healthy"
else
    echo "❌ RASA is down"
fi

# Check frontend
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is down"
fi
```

### 2. Automated Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup application data
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz ~/automotive_chatbot

# Keep only last 7 backups
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +7 -delete
```

### 3. System Updates

```bash
#!/bin/bash
# update.sh

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y

# Update Docker images
cd ~/automotive_chatbot/deploy
docker-compose pull
docker-compose up -d

# Clean up old images
docker image prune -f
```

## 🎯 Production Checklist

- [ ] EC2 instance properly sized
- [ ] Security groups configured
- [ ] Elastic IP assigned
- [ ] SSL certificates installed
- [ ] Environment variables configured
- [ ] Firewall rules applied
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Log rotation configured
- [ ] Health checks working
- [ ] Performance testing completed
- [ ] Documentation updated

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section
2. Review container logs
3. Verify network connectivity
4. Check system resources
5. Consult AWS documentation

---

**🎉 Congratulations!** Your Automotive Chatbot is now deployed on AWS EC2 using Docker!

For updates and maintenance, simply run the deployment script again with the same parameters.
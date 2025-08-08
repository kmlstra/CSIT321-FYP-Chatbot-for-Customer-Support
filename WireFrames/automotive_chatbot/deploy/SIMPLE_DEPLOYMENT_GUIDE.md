# 🚀 Simple Docker Deployment Guide

**No AWS complexity! Just Docker Desktop + SSH = Done!**

---

## 📋 Prerequisites

### What You Need:
1. **Docker Desktop** - Install from [docker.com](https://www.docker.com/products/docker-desktop/)
2. **SSH Access** to your server (EC2, VPS, or any Linux server)
3. **5 minutes** of your time

### Server Requirements:
- Linux server (Ubuntu recommended)
- Docker installed on server
- SSH access (username/password or PEM key)
- Ports 3000, 8001, 5005 open

---

## 🎯 Quick Start (3 Steps)

### Step 1: Build Images Locally
```powershell
cd deploy
.\simple-build.ps1
```

### Step 2: Configure Environment
```powershell
# Copy and edit environment file
cp .env.simple .env
# Edit .env with your MongoDB URI and other settings
```

### Step 3: Deploy to Server
```powershell
# Deploy to your server
.\simple-deploy.ps1 -ServerIP YOUR_SERVER_IP

# Or with PEM key
.\simple-deploy.ps1 -ServerIP YOUR_SERVER_IP -PemKeyPath "path\to\your\key.pem"
```

**That's it! Your chatbot is now running!** 🎉

---

## 📖 Detailed Instructions

### 1. Prepare Your Environment

#### 1.1 Install Docker Desktop
- Download from [docker.com](https://www.docker.com/products/docker-desktop/)
- Install and start Docker Desktop
- Verify: `docker --version`

#### 1.2 Prepare Your Server

**Note**: These commands work for any Linux server (Ubuntu, CentOS, etc.) that you can access via SSH. This includes:
- AWS EC2 instances (via SSH, not CloudShell)
- VPS servers (DigitalOcean, Linode, etc.)
- Local Linux machines
- Any cloud provider's Linux instances

On your Linux server, connect via SSH and install Docker and Docker Compose:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, for non-root access)
sudo usermod -aG docker $USER
```

**Important**: These are standard Linux commands that should be run via SSH on your server, not in AWS CloudShell or similar browser-based terminals.

### 2. Configure Your Application

#### 2.1 Database Setup
1. Create a MongoDB Atlas account (free tier available)
2. Create a cluster and get connection string
3. Update `.env` file with your MongoDB URI

#### 2.2 Environment Configuration
```bash
# Copy the template
cp .env.simple .env

# Edit the file with your settings
# Required changes:
# - MONGODB_URI: Your MongoDB connection string
# - JWT_SECRET: A secure random string
# - CORS_ORIGINS: Your domain(s)
```

### 3. Build and Deploy

#### 3.1 Build Docker Images
```powershell
# Navigate to deploy directory
cd deploy

# Build images (takes 5-10 minutes first time)
.\simple-build.ps1

# Verify images are built
docker images | findstr automotive-chatbot
```

#### 3.2 Deploy to Server
```powershell
# Basic deployment
.\simple-deploy.ps1 -ServerIP 13.212.93.122

# With custom username
.\simple-deploy.ps1 -ServerIP 13.212.93.122 -Username ec2-user

# With PEM key (for AWS EC2)
.\simple-deploy.ps1 -ServerIP 13.212.93.122 -PemKeyPath "C:\path\to\key.pem"

# With custom project name
.\simple-deploy.ps1 -ServerIP 13.212.93.122 -ProjectName my-chatbot
```

---

## 🔧 Configuration Options

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|----------|
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.net/db` |
| `JWT_SECRET` | Secret for JWT tokens | `your-super-secret-key` |
| `CORS_ORIGINS` | Allowed origins | `http://localhost:3000,https://yourdomain.com` |
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://your-server-ip:8001` |
| `NEXT_PUBLIC_RASA_URL` | Rasa API URL | `http://your-server-ip:5005` |

### Script Parameters

#### simple-build.ps1
```powershell
.\simple-build.ps1 [-ProjectName "my-app"] [-Version "v1.0"]
```

#### simple-deploy.ps1
```powershell
.\simple-deploy.ps1 -ServerIP <IP> [-Username <user>] [-PemKeyPath <path>] [-ProjectName <name>] [-Version <version>] [-DeployPath <path>]
```

---

## 🌐 Access Your Application

After successful deployment:

- **Frontend**: `http://YOUR_SERVER_IP:3000`
- **Backend API**: `http://YOUR_SERVER_IP:8001`
- **Rasa API**: `http://YOUR_SERVER_IP:5005`
- **API Docs**: `http://YOUR_SERVER_IP:8001/docs`

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Docker not found"
**Solution**: Install and start Docker Desktop

#### 2. "Cannot connect to server"
**Solutions**:
- Check server IP address
- Verify SSH access: `ssh username@server-ip`
- Check firewall settings
- Ensure server is running

#### 3. "Images not found"
**Solution**: Run `simple-build.ps1` first

#### 4. "Permission denied"
**Solutions**:
- Check PEM key permissions: `chmod 400 key.pem`
- Verify username (ubuntu for Ubuntu, ec2-user for Amazon Linux)
- Check SSH key is correct

#### 5. "Port already in use"
**Solution**: Stop existing containers on server:
```bash
docker-compose down
docker stop $(docker ps -q)
```

### Logs and Debugging

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f

# Restart services
docker-compose restart
```

---

## 🔄 Updates and Maintenance

### Update Application
```powershell
# 1. Build new images
.\simple-build.ps1 -Version "v2.0"

# 2. Deploy new version
.\simple-deploy.ps1 -ServerIP YOUR_SERVER_IP -Version "v2.0"
```

### Backup Data
```bash
# On server - backup volumes
docker run --rm -v automotive-chatbot_backend_data:/data -v $(pwd):/backup ubuntu tar czf /backup/backup.tar.gz /data
```

### Monitor Resources
```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Clean up unused images
docker system prune -a
```

---

## 🎯 Production Tips

### Security
1. **Change default passwords** in `.env`
2. **Use HTTPS** with reverse proxy (Nginx/Traefik)
3. **Restrict SSH access** to specific IPs
4. **Regular updates** of base images

### Performance
1. **Monitor logs** regularly
2. **Set up log rotation**
3. **Monitor resource usage**
4. **Use SSD storage** for better performance

### Backup Strategy
1. **Database backups** (MongoDB Atlas handles this)
2. **Volume backups** for local data
3. **Configuration backups** (`.env`, `docker-compose.yml`)

---

## 🆘 Support

If you encounter issues:

1. **Check logs** first: `docker-compose logs`
2. **Verify prerequisites** are met
3. **Test connectivity** to server
4. **Check firewall** settings
5. **Restart services** if needed

---

## 📝 Summary

**What this solution provides:**
- ✅ No AWS complexity (no ECR, IAM, CLI)
- ✅ Simple 3-step deployment
- ✅ Works with any Linux server
- ✅ One-click build and deploy
- ✅ Production-ready containers
- ✅ Easy updates and maintenance

**Requirements:**
- Docker Desktop (local)
- SSH access to server
- 5 minutes of setup time

**Perfect for:**
- Development teams
- Small to medium deployments
- Quick prototyping
- Cost-effective hosting

---

*Happy deploying! 🚀*
# Automotive Chatbot Deployment Options

## 🚀 Recommended: Simple Docker Desktop Deployment

For quick and straightforward deployment to AWS EC2, use the simple Docker-based approach:

### Quick Start

1. **Configure your Docker Hub username** in all scripts:
   - `docker-build.ps1`
   - `docker-push.ps1` 
   - `ssh-deploy.ps1`
   - `docker-compose.yml`

2. **Set your SSH key path** in `ssh-deploy.ps1`:
   ```powershell
   $SSH_KEY_PATH = "C:\path\to\your\key.pem"
   ```

3. **Deploy in 3 simple steps**:
   ```powershell
   # Step 1: Build containers locally
   .\docker-build.ps1
   
   # Step 2: Push to Docker Hub
   .\docker-push.ps1
   
   # Step 3: Deploy to EC2
   .\ssh-deploy.ps1
   ```

### Files for Simple Deployment

- `docker-build.ps1` - Build all containers locally using Docker Desktop
- `docker-push.ps1` - Push containers to Docker Hub
- `ssh-deploy.ps1` - Deploy via SSH to EC2 instance 54.254.180.103
- `docker-compose.yml` - Alternative Docker Compose deployment
- `SIMPLE_DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide

### Target Infrastructure

- **EC2 Instance**: 54.254.180.103 (ap-southeast-1)
- **Frontend**: Port 80
- **Backend API**: Port 8000
- **Rasa API**: Port 5005
- **MongoDB**: Port 27017

## 🏗️ Alternative: Complex Infrastructure Setup

For production environments requiring advanced infrastructure (Load Balancers, Auto Scaling, Monitoring), the complex setup is available in the `aws-deployment-backup/` directory.

### Complex Setup Features

- Terraform infrastructure as code
- Application Load Balancer
- Auto Scaling Groups
- CloudWatch monitoring
- Grafana dashboards
- SSL certificates
- Custom domains

### When to Use Complex Setup

- Production environments
- High availability requirements
- Advanced monitoring needs
- Custom domain requirements
- SSL/TLS termination
- Auto-scaling capabilities

## 📋 Comparison

| Feature | Simple Docker | Complex Infrastructure |
|---------|---------------|------------------------|
| Setup Time | 5-10 minutes | 30-60 minutes |
| Complexity | Low | High |
| Maintenance | Easy | Advanced |
| Scalability | Manual | Automatic |
| Monitoring | Basic | Advanced |
| SSL/HTTPS | Manual | Automatic |
| Cost | Low | Higher |
| Best For | Development, Testing | Production |

## 🎯 Recommendation

**Start with the Simple Docker deployment** for:
- Development and testing
- Quick demos
- Proof of concepts
- Learning the application

**Upgrade to Complex Infrastructure** when you need:
- Production deployment
- High availability
- Advanced monitoring
- Custom domains with SSL

## 🔧 Configuration Requirements

### For Simple Deployment
- Docker Desktop
- Docker Hub account
- SSH access to EC2
- PowerShell

### For Complex Deployment
- AWS CLI configured
- Terraform installed
- Domain name (optional)
- SSL certificates (optional)

## 📞 Support

Refer to `SIMPLE_DEPLOYMENT_GUIDE.md` for detailed instructions and troubleshooting for the recommended simple approach.

For complex infrastructure setup, see `aws-deployment-backup/README.md`.
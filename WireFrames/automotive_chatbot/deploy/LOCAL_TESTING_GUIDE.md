# 🧪 Local Docker Testing Guide

This guide helps you test the Docker setup locally before deploying to AWS EC2.

## 📋 Prerequisites

### Required Software
- **Docker Desktop**: Download from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
- **Git**: For version control
- **Node.js**: Version 18+ (for development)
- **Python**: Version 3.9+ (for backend development)

### Installation Steps

#### 1. Install Docker Desktop

**Windows:**
1. Download Docker Desktop for Windows
2. Run the installer
3. Restart your computer
4. Start Docker Desktop
5. Verify installation:
   ```powershell
   docker --version
   docker-compose --version
   ```

**macOS:**
1. Download Docker Desktop for Mac
2. Drag to Applications folder
3. Launch Docker Desktop
4. Verify installation:
   ```bash
   docker --version
   docker-compose --version
   ```

**Linux:**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Restart session or run:
newgrp docker
```

## 🚀 Local Testing Process

### Step 1: Prepare Environment

1. **Navigate to project directory:**
   ```bash
   cd /path/to/automotive_chatbot/deploy
   ```

2. **Copy environment file:**
   ```bash
   # Windows
   copy .env.production .env.local
   
   # Linux/Mac
   cp .env.production .env.local
   ```

3. **Edit local environment file:**
   ```bash
   # Edit .env.local with local URLs
   REACT_APP_API_URL=http://localhost:8001
   REACT_APP_RASA_URL=http://localhost:5005
   REACT_APP_WEBSOCKET_URL=ws://localhost:8001
   ENVIRONMENT=development
   DEBUG=true
   ```

### Step 2: Build and Test Containers

1. **Build Docker images:**
   ```bash
   docker-compose -f docker-compose.yml --env-file .env.local build
   ```

2. **Start services:**
   ```bash
   docker-compose -f docker-compose.yml --env-file .env.local up -d
   ```

3. **Check container status:**
   ```bash
   docker-compose ps
   ```

   Expected output:
   ```
   Name                      Command               State           Ports
   automotive_backend    uvicorn main:app --host 0.0.0.0   Up      0.0.0.0:8001->8001/tcp
   automotive_frontend   docker-entrypoint.sh npm start   Up      0.0.0.0:3000->3000/tcp
   automotive_rasa       rasa run --enable-api --cors ... Up      0.0.0.0:5005->5005/tcp
   ```

### Step 3: Verify Services

1. **Test Backend API:**
   ```bash
   curl http://localhost:8001/health
   # Expected: {"status": "healthy"}
   ```

2. **Test RASA API:**
   ```bash
   curl http://localhost:5005/version
   # Expected: RASA version information
   ```

3. **Test Frontend:**
   - Open browser: `http://localhost:3000`
   - Should load the chatbot interface

4. **Test API Documentation:**
   - Open browser: `http://localhost:8001/docs`
   - Should show FastAPI documentation

### Step 4: Test Application Functionality

1. **Test Chat Interface:**
   - Navigate to `http://localhost:3000/clevercompanion.html`
   - Send a test message
   - Verify response from chatbot

2. **Test API Endpoints:**
   ```bash
   # Test chat endpoint
   curl -X POST "http://localhost:8001/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "user_id": "test_user"}'
   ```

3. **Test RASA Integration:**
   ```bash
   # Test RASA directly
   curl -X POST "http://localhost:5005/webhooks/rest/webhook" \
        -H "Content-Type: application/json" \
        -d '{"sender": "test", "message": "hello"}'
   ```

## 🔍 Debugging and Troubleshooting

### View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f rasa

# View last N lines
docker-compose logs --tail=50 backend
```

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/Mac

# Stop conflicting services
docker-compose down
```

#### 2. Container Build Failures
```bash
# Clean Docker cache
docker system prune -f

# Rebuild without cache
docker-compose build --no-cache
```

#### 3. Memory Issues
```bash
# Check Docker resource usage
docker stats

# Increase Docker Desktop memory limit
# Docker Desktop → Settings → Resources → Memory
```

#### 4. Network Issues
```bash
# Check Docker networks
docker network ls

# Inspect network
docker network inspect deploy_default
```

### Performance Testing

1. **Load Testing:**
   ```bash
   # Install Apache Bench (if not available)
   # Test API performance
   ab -n 100 -c 10 http://localhost:8001/health
   ```

2. **Memory Usage:**
   ```bash
   # Monitor container resources
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
   ```

3. **Response Time Testing:**
   ```bash
   # Test chat response time
   time curl -X POST "http://localhost:8001/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "user_id": "test_user"}'
   ```

## 🧹 Cleanup

### Stop and Remove Containers
```bash
# Stop services
docker-compose down

# Remove containers and networks
docker-compose down --volumes --remove-orphans

# Remove images (optional)
docker-compose down --rmi all
```

### Clean Docker System
```bash
# Remove unused containers, networks, images
docker system prune -f

# Remove everything (use with caution)
docker system prune -a -f
```

## ✅ Pre-Deployment Checklist

Before deploying to AWS EC2, ensure:

- [ ] All containers build successfully
- [ ] All services start without errors
- [ ] Frontend loads correctly
- [ ] Backend API responds to health checks
- [ ] RASA API is accessible
- [ ] Chat functionality works end-to-end
- [ ] No memory leaks or performance issues
- [ ] Logs show no critical errors
- [ ] Environment variables are properly configured
- [ ] Docker images are optimized for production

## 📊 Testing Checklist

### Functional Tests
- [ ] Chat interface loads
- [ ] Messages send successfully
- [ ] Bot responds appropriately
- [ ] API endpoints return expected responses
- [ ] Error handling works correctly

### Performance Tests
- [ ] Response times are acceptable (< 2 seconds)
- [ ] Memory usage is reasonable (< 1GB per service)
- [ ] CPU usage is stable
- [ ] No memory leaks detected

### Security Tests
- [ ] No sensitive data in logs
- [ ] Environment variables are secure
- [ ] API endpoints have proper validation
- [ ] CORS is configured correctly

## 🚀 Next Steps

Once local testing is successful:

1. **Commit changes to version control**
2. **Update production environment variables**
3. **Run deployment script for AWS EC2**
4. **Monitor deployment logs**
5. **Perform post-deployment testing**

---

**Note:** This local testing ensures your Docker setup works correctly before deploying to AWS EC2, saving time and reducing deployment issues.
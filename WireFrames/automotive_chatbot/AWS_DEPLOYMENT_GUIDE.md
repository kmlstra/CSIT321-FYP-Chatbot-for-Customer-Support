# AWS Deployment Guide

This guide provides step-by-step instructions for deploying the Automotive Chatbot to AWS EC2.

## Prerequisites

- AWS EC2 instance running Ubuntu
- SSH access to the EC2 instance
- Node.js and Python installed on the EC2 instance
- Domain/IP: `54.254.180.103`

## Quick Deployment Steps

### 1. Prepare Local Environment

```powershell
# Set environment to production
$env:NODE_ENV = "production"
$env:NEXT_PUBLIC_ENV = "production"

# Build frontend
cd frontend
npm run build
cd ..
```

### 2. Connect to AWS Instance

```bash
ssh -i your-key.pem ubuntu@54.254.180.103
```

### 3. Setup Project Directory

```bash
# Create project directory
sudo mkdir -p /var/www/automotive_chatbot
sudo chown ubuntu:ubuntu /var/www/automotive_chatbot
cd /var/www/automotive_chatbot
```

### 4. Upload Files

Upload the following files/directories to `/var/www/automotive_chatbot/`:

- `backend/` (entire directory)
- `frontend/.next/` (built frontend)
- `frontend/public/`
- `frontend/package.json`
- `frontend/next.config.js`
- `rasa/` (entire directory)
- `package.json`
- `requirements.txt`
- Environment files:
  - `frontend/.env.production`
  - `backend/.env.production`

### 5. Install Dependencies

```bash
# Install Node.js dependencies
npm install --production
cd frontend && npm install --production && cd ..

# Install Python dependencies
pip3 install -r requirements.txt
```

### 6. Create Systemd Services

#### Frontend Service
```bash
sudo tee /etc/systemd/system/automotive-frontend.service > /dev/null <<EOF
[Unit]
Description=Automotive Chatbot Frontend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/automotive_chatbot/frontend
Environment=NODE_ENV=production
Environment=NEXT_PUBLIC_ENV=production
Environment=PORT=3000
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Backend Service
```bash
sudo tee /etc/systemd/system/automotive-backend.service > /dev/null <<EOF
[Unit]
Description=Automotive Chatbot Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/automotive_chatbot/backend
Environment=NODE_ENV=production
ExecStart=/usr/bin/python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### RASA Service
```bash
sudo tee /etc/systemd/system/automotive-rasa.service > /dev/null <<EOF
[Unit]
Description=Automotive Chatbot RASA
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/automotive_chatbot
ExecStart=/usr/bin/python3 -m rasa run --enable-api --cors "*" --port 5005
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### RASA Actions Service
```bash
sudo tee /etc/systemd/system/automotive-actions.service > /dev/null <<EOF
[Unit]
Description=Automotive Chatbot RASA Actions
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/automotive_chatbot/backend
ExecStart=/usr/bin/python3 -m rasa run actions --actions actions --port 5055
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 7. Start Services

```bash
# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable automotive-frontend automotive-backend automotive-rasa automotive-actions

# Start services in order
sudo systemctl start automotive-backend
sleep 5
sudo systemctl start automotive-actions
sleep 5
sudo systemctl start automotive-rasa
sleep 5
sudo systemctl start automotive-frontend
```

### 8. Configure Nginx (Optional)

```bash
# Install nginx
sudo apt update && sudo apt install -y nginx

# Create nginx configuration
sudo tee /etc/nginx/sites-available/automotive-chatbot > /dev/null <<EOF
server {
    listen 80;
    server_name 54.254.180.103;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # RASA API
    location /webhooks/ {
        proxy_pass http://localhost:5005/webhooks/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/automotive-chatbot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart nginx
sudo nginx -t
sudo systemctl restart nginx
```

## Verification

### Check Service Status
```bash
sudo systemctl status automotive-frontend
sudo systemctl status automotive-backend
sudo systemctl status automotive-rasa
sudo systemctl status automotive-actions
```

### Check Logs
```bash
sudo journalctl -u automotive-frontend -f
sudo journalctl -u automotive-backend -f
sudo journalctl -u automotive-rasa -f
sudo journalctl -u automotive-actions -f
```

### Test Endpoints
```bash
# Test backend
curl http://localhost:8000/api/health

# Test RASA
curl http://localhost:5005/

# Test frontend
curl http://localhost:3000/
```

## Access URLs

After successful deployment:

- **Frontend**: http://54.254.180.103
- **Backend API**: http://54.254.180.103:8000
- **API Documentation**: http://54.254.180.103:8000/docs
- **RASA API**: http://54.254.180.103:5005
- **Test Widget**: http://54.254.180.103/test-client-widget.html

## Troubleshooting

### Common Issues

1. **Service fails to start**
   ```bash
   sudo journalctl -u service-name -n 50
   ```

2. **Port conflicts**
   ```bash
   sudo netstat -tulpn | grep :PORT
   sudo lsof -i :PORT
   ```

3. **Permission issues**
   ```bash
   sudo chown -R ubuntu:ubuntu /var/www/automotive_chatbot
   ```

4. **Environment variables not loaded**
   - Check `.env.production` files are in correct locations
   - Verify systemd service environment settings

### Restart Services
```bash
sudo systemctl restart automotive-frontend
sudo systemctl restart automotive-backend
sudo systemctl restart automotive-rasa
sudo systemctl restart automotive-actions
sudo systemctl restart nginx
```

### Stop Services
```bash
sudo systemctl stop automotive-frontend
sudo systemctl stop automotive-backend
sudo systemctl stop automotive-rasa
sudo systemctl stop automotive-actions
```

## Environment Switching

To switch between environments, use the provided scripts:

- **Local Development**: `./switch-to-local.ps1`
- **AWS Production**: `./switch-to-aws.ps1`

## Security Notes

1. Ensure AWS Security Groups allow traffic on ports 80, 8000, 5005
2. Consider using HTTPS with SSL certificates
3. Regularly update system packages
4. Monitor service logs for security issues

## Monitoring

### System Resources
```bash
# Check CPU and memory usage
top
htop
free -h
df -h
```

### Service Health
```bash
# Create a simple health check script
echo '#!/bin/bash
echo "=== Service Status ==="
sudo systemctl is-active automotive-frontend automotive-backend automotive-rasa automotive-actions
echo "=== Port Status ==="
ss -tulpn | grep -E ":(3000|8000|5005|5055)"' | sudo tee /usr/local/bin/check-automotive-services.sh
sudo chmod +x /usr/local/bin/check-automotive-services.sh

# Run health check
/usr/local/bin/check-automotive-services.sh
```
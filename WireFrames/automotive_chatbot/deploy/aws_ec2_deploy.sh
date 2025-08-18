#!/bin/bash

# AWS EC2 Deployment Script for Automotive Chatbot
# This script automates the deployment process on AWS EC2

set -e  # Exit on any error

# Configuration
APP_NAME="automotive-chatbot"
APP_DIR="/opt/${APP_NAME}"
GIT_REPO="https://github.com/your-repo/automotive-chatbot.git"
BRANCH="main"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    log_success "System packages updated"
}

# Install Docker
install_docker() {
    log "Installing Docker..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc || true
    
    # Install dependencies
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    # Add current user to docker group
    usermod -aG docker $SUDO_USER || true
    
    log_success "Docker installed successfully"
}

# Install Docker Compose
install_docker_compose() {
    log "Installing Docker Compose..."
    
    # Download latest version
    DOCKER_COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
    curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make executable
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    log_success "Docker Compose installed successfully"
}

# Install Git
install_git() {
    log "Installing Git..."
    apt-get install -y git
    log_success "Git installed successfully"
}

# Install Node.js and npm
install_nodejs() {
    log "Installing Node.js and npm..."
    
    # Install NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
    
    # Install PM2 for process management
    npm install -g pm2
    
    log_success "Node.js and npm installed successfully"
}

# Install Python and pip
install_python() {
    log "Installing Python and pip..."
    apt-get install -y python3 python3-pip python3-venv
    
    # Create symlinks
    ln -sf /usr/bin/python3 /usr/bin/python || true
    ln -sf /usr/bin/pip3 /usr/bin/pip || true
    
    log_success "Python and pip installed successfully"
}

# Setup application directory
setup_app_directory() {
    log "Setting up application directory..."
    
    # Create application directory
    mkdir -p $APP_DIR
    cd $APP_DIR
    
    # Clone or update repository
    if [ -d ".git" ]; then
        log "Updating existing repository..."
        git fetch origin
        git reset --hard origin/$BRANCH
    else
        log "Cloning repository..."
        git clone -b $BRANCH $GIT_REPO .
    fi
    
    log_success "Application directory setup complete"
}

# Setup environment variables
setup_environment() {
    log "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log "Creating .env file..."
        cat > .env << EOF
# MongoDB Atlas Configuration
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=automotive_chatbot_saas

# RASA Configuration
RASA_MODEL_PATH=/app/models
RASA_CORE_ENDPOINT=http://rasa-core:5005
RASA_NLU_ENDPOINT=http://rasa-nlu:5000
RASA_ACTION_ENDPOINT=http://rasa-actions:5055

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_RASA_URL=http://localhost:5005

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security
JWT_SECRET=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/automotive-chatbot.log

# Performance
WORKERS=4
MAX_CONNECTIONS=1000
CACHE_TTL=300

# AWS Configuration
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
EOF
        
        log_warning "Please update the .env file with your actual configuration values"
    else
        log "Environment file already exists"
    fi
    
    log_success "Environment setup complete"
}

# Setup firewall
setup_firewall() {
    log "Setting up firewall..."
    
    # Install ufw if not present
    apt-get install -y ufw
    
    # Reset firewall
    ufw --force reset
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    ufw allow 22
    
    # Allow HTTP and HTTPS
    ufw allow 80
    ufw allow 443
    
    # Allow application ports
    ufw allow 3000  # Frontend
    ufw allow 8000  # Backend API
    ufw allow 5005  # RASA Core
    ufw allow 5055  # RASA Actions
    
    # Enable firewall
    ufw --force enable
    
    log_success "Firewall configured successfully"
}

# Build and start services
start_services() {
    log "Building and starting services..."
    
    cd $APP_DIR
    
    # Stop existing services
    docker-compose down || true
    
    # Remove old images
    docker system prune -f
    
    # Build and start services
    docker-compose up -d --build
    
    # Wait for services to start
    sleep 30
    
    # Check service status
    docker-compose ps
    
    log_success "Services started successfully"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up monitoring..."
    
    # Create monitoring script
    cat > /usr/local/bin/monitor-chatbot.sh << 'EOF'
#!/bin/bash

# Monitor chatbot services
APP_DIR="/opt/automotive-chatbot"
LOG_FILE="/var/log/chatbot-monitor.log"

log_monitor() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> $LOG_FILE
}

cd $APP_DIR

# Check if services are running
if ! docker-compose ps | grep -q "Up"; then
    log_monitor "Services are down, attempting restart..."
    docker-compose up -d
    sleep 30
fi

# Check service health
services=("frontend" "backend" "rasa-core" "rasa-actions")
for service in "${services[@]}"; do
    if ! docker-compose ps $service | grep -q "Up"; then
        log_monitor "Service $service is down, restarting..."
        docker-compose restart $service
    fi
done

# Clean up old logs
find /var/log -name "*.log" -mtime +7 -delete

# Clean up Docker
docker system prune -f
EOF
    
    chmod +x /usr/local/bin/monitor-chatbot.sh
    
    # Setup cron job for monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/monitor-chatbot.sh") | crontab -
    
    log_success "Monitoring setup complete"
}

# Setup SSL certificate (Let's Encrypt)
setup_ssl() {
    log "Setting up SSL certificate..."
    
    # Install certbot
    apt-get install -y certbot python3-certbot-nginx
    
    log "SSL setup prepared. Run 'certbot --nginx -d yourdomain.com' to obtain certificate"
}

# Setup log rotation
setup_log_rotation() {
    log "Setting up log rotation..."
    
    cat > /etc/logrotate.d/automotive-chatbot << EOF
/var/log/automotive-chatbot.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        docker-compose -f $APP_DIR/docker-compose.yml restart backend rasa-actions
    endscript
}
EOF
    
    log_success "Log rotation configured"
}

# Main deployment function
main() {
    log "Starting AWS EC2 deployment for $APP_NAME..."
    
    check_root
    update_system
    install_docker
    install_docker_compose
    install_git
    install_nodejs
    install_python
    setup_app_directory
    setup_environment
    setup_firewall
    start_services
    setup_monitoring
    setup_ssl
    setup_log_rotation
    
    log_success "Deployment completed successfully!"
    log "Application should be accessible at:"
    log "  - Frontend: http://$(curl -s ifconfig.me):3000"
    log "  - Backend API: http://$(curl -s ifconfig.me):8000"
    log "  - RASA Core: http://$(curl -s ifconfig.me):5005"
    log ""
    log "Next steps:"
    log "1. Update .env file with your actual configuration"
    log "2. Configure domain name and SSL certificate"
    log "3. Update MongoDB Atlas connection string"
    log "4. Test all services are working correctly"
    log ""
    log "To check service status: docker-compose ps"
    log "To view logs: docker-compose logs -f [service-name]"
    log "To restart services: docker-compose restart"
}

# Run main function
main "$@"
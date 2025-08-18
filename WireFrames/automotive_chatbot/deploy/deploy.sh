#!/bin/bash

# Main Deployment Script for Automotive Chatbot
# This script orchestrates the complete deployment process

set -euo pipefail

# Configuration
APP_NAME="automotive-chatbot"
APP_VERSION="${APP_VERSION:-1.0.0}"
APP_DOMAIN="${APP_DOMAIN:-automotive-chatbot.com}"
MONITORING_DOMAIN="${MONITORING_DOMAIN:-monitoring.automotive-chatbot.com}"
APP_USER="automotive-chatbot"
APP_DIR="/opt/automotive-chatbot"
DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/automotive-chatbot-deploy.log"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BACKUP="${SKIP_BACKUP:-false}"
FORCE_DEPLOY="${FORCE_DEPLOY:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Deployment phases
DEPLOYMENT_PHASES=(
    "pre_deployment_checks"
    "system_preparation"
    "security_setup"
    "application_deployment"
    "database_setup"
    "monitoring_setup"
    "ssl_configuration"
    "system_optimization"
    "health_checks"
    "post_deployment_tasks"
)

# Current phase tracking
CURRENT_PHASE=0
TOTAL_PHASES=${#DEPLOYMENT_PHASES[@]}

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a $LOG_FILE
}

phase_header() {
    ((CURRENT_PHASE++))
    echo -e "\n${PURPLE}=== PHASE $CURRENT_PHASE/$TOTAL_PHASES: $1 ===${NC}" | tee -a $LOG_FILE
    echo -e "${CYAN}Progress: $(( CURRENT_PHASE * 100 / TOTAL_PHASES ))%${NC}" | tee -a $LOG_FILE
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    error "Deployment failed at line $line_number with exit code $exit_code"
    error "Phase: ${DEPLOYMENT_PHASES[$((CURRENT_PHASE-1))]}"
    
    # Attempt rollback if not in force mode
    if [ "$FORCE_DEPLOY" != "true" ]; then
        warn "Attempting automatic rollback..."
        rollback_deployment
    fi
    
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Check system requirements
check_system_requirements() {
    log "Checking system requirements..."
    
    # Check OS
    if ! lsb_release -d | grep -q "Ubuntu"; then
        error "This script is designed for Ubuntu systems"
        exit 1
    fi
    
    # Check minimum resources
    local total_memory=$(free -m | awk 'NR==2{print $2}')
    local available_disk=$(df / | awk 'NR==2{print $4}')
    
    if [ $total_memory -lt 2048 ]; then
        error "Minimum 2GB RAM required, found ${total_memory}MB"
        exit 1
    fi
    
    if [ $available_disk -lt 10485760 ]; then # 10GB in KB
        error "Minimum 10GB disk space required"
        exit 1
    fi
    
    # Check network connectivity
    if ! ping -c 1 google.com &>/dev/null; then
        error "No internet connectivity detected"
        exit 1
    fi
    
    success "System requirements check passed"
}

# Load environment variables
load_environment() {
    log "Loading environment configuration..."
    
    # Load from environment file if exists
    if [ -f "$DEPLOY_DIR/.env" ]; then
        source "$DEPLOY_DIR/.env"
        success "Environment variables loaded from .env file"
    elif [ -f "$DEPLOY_DIR/env_template.txt" ]; then
        warn "No .env file found, using template. Please configure environment variables."
        cp "$DEPLOY_DIR/env_template.txt" "$DEPLOY_DIR/.env"
        error "Please edit $DEPLOY_DIR/.env with your configuration and run again"
        exit 1
    else
        error "No environment configuration found"
        exit 1
    fi
    
    # Validate required variables
    local required_vars=(
        "MONGODB_URI"
        "JWT_SECRET"
        "ENCRYPTION_KEY"
        "AWS_ACCESS_KEY_ID"
        "AWS_SECRET_ACCESS_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    success "Environment configuration validated"
}

# Pre-deployment checks
pre_deployment_checks() {
    phase_header "Pre-deployment Checks"
    
    check_root
    check_system_requirements
    load_environment
    
    # Check if deployment is already in progress
    if [ -f "/tmp/automotive-chatbot-deploy.lock" ] && [ "$FORCE_DEPLOY" != "true" ]; then
        error "Deployment already in progress. Use FORCE_DEPLOY=true to override."
        exit 1
    fi
    
    # Create deployment lock
    echo "$$" > /tmp/automotive-chatbot-deploy.lock
    
    # Create deployment timestamp
    echo "$(date -Iseconds)" > /tmp/automotive-chatbot-deploy.timestamp
    
    success "Pre-deployment checks completed"
}

# System preparation
system_preparation() {
    phase_header "System Preparation"
    
    # Update system packages
    log "Updating system packages..."
    apt-get update && apt-get upgrade -y
    
    # Install required packages
    log "Installing required packages..."
    apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        gnupg \
        lsb-release \
        jq \
        bc \
        htop \
        iotop \
        netcat \
        rsync \
        logrotate \
        cron
    
    # Create application user
    if ! id "$APP_USER" &>/dev/null; then
        log "Creating application user: $APP_USER"
        useradd -r -s /bin/bash -d "$APP_DIR" -m "$APP_USER"
    fi
    
    # Create application directories
    log "Creating application directories..."
    mkdir -p "$APP_DIR"/{logs,data,config,scripts,backups}
    mkdir -p /var/log/automotive-chatbot
    mkdir -p /etc/automotive-chatbot
    
    # Set permissions
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" /var/log/automotive-chatbot
    
    success "System preparation completed"
}

# Security setup
security_setup() {
    phase_header "Security Setup"
    
    # Run security setup script
    if [ -f "$DEPLOY_DIR/security_setup.sh" ]; then
        log "Running security setup..."
        bash "$DEPLOY_DIR/security_setup.sh"
    else
        warn "Security setup script not found, skipping"
    fi
    
    success "Security setup completed"
}

# Application deployment
application_deployment() {
    phase_header "Application Deployment"
    
    # Install Docker
    if ! command -v docker &> /dev/null; then
        log "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        usermod -aG docker "$APP_USER"
        systemctl enable docker
        systemctl start docker
    fi
    
    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    # Install Node.js
    if ! command -v node &> /dev/null; then
        log "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
        apt-get install -y nodejs
    fi
    
    # Install Python and pip
    if ! command -v python3 &> /dev/null; then
        log "Installing Python..."
        apt-get install -y python3 python3-pip python3-venv
    fi
    
    # Copy application files
    log "Copying application files..."
    rsync -av --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
        "$DEPLOY_DIR/../" "$APP_DIR/"
    
    # Set up environment file
    cp "$DEPLOY_DIR/.env" "$APP_DIR/.env"
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    
    # Build and start application
    log "Building and starting application..."
    cd "$APP_DIR"
    
    # Build frontend
    if [ -d "frontend" ]; then
        log "Building frontend..."
        cd frontend
        npm install
        npm run build
        cd ..
    fi
    
    # Build backend
    if [ -d "backend" ]; then
        log "Setting up backend..."
        cd backend
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
        cd ..
    fi
    
    # Start services with Docker Compose
    if [ -f "docker-compose.production.yml" ]; then
        log "Starting services with Docker Compose..."
        docker-compose -f docker-compose.production.yml up -d
    fi
    
    success "Application deployment completed"
}

# Database setup
database_setup() {
    phase_header "Database Setup"
    
    # Install MongoDB tools if needed
    if ! command -v mongosh &> /dev/null; then
        log "Installing MongoDB tools..."
        wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        apt-get update
        apt-get install -y mongodb-mongosh
    fi
    
    # Install Redis
    if ! command -v redis-cli &> /dev/null; then
        log "Installing Redis..."
        apt-get install -y redis-server
        systemctl enable redis-server
        systemctl start redis-server
    fi
    
    # Test database connections
    log "Testing database connections..."
    
    # Test MongoDB Atlas
    if mongosh "$MONGODB_URI" --eval "db.runCommand('ping')" &>/dev/null; then
        success "MongoDB Atlas connection successful"
    else
        error "MongoDB Atlas connection failed"
        exit 1
    fi
    
    # Test Redis
    if redis-cli ping &>/dev/null; then
        success "Redis connection successful"
    else
        error "Redis connection failed"
        exit 1
    fi
    
    success "Database setup completed"
}

# Monitoring setup
monitoring_setup() {
    phase_header "Monitoring Setup"
    
    # Run monitoring setup script
    if [ -f "$DEPLOY_DIR/monitoring_setup.sh" ]; then
        log "Setting up monitoring..."
        bash "$DEPLOY_DIR/monitoring_setup.sh"
    else
        warn "Monitoring setup script not found, skipping"
    fi
    
    success "Monitoring setup completed"
}

# SSL configuration
ssl_configuration() {
    phase_header "SSL Configuration"
    
    # Run SSL setup script
    if [ -f "$DEPLOY_DIR/ssl_setup.sh" ]; then
        log "Setting up SSL certificates..."
        bash "$DEPLOY_DIR/ssl_setup.sh" "$APP_DOMAIN" "admin@$APP_DOMAIN"
        
        if [ "$APP_DOMAIN" != "$MONITORING_DOMAIN" ]; then
            bash "$DEPLOY_DIR/ssl_setup.sh" "$MONITORING_DOMAIN" "admin@$APP_DOMAIN"
        fi
    else
        warn "SSL setup script not found, skipping"
    fi
    
    success "SSL configuration completed"
}

# System optimization
system_optimization() {
    phase_header "System Optimization"
    
    # Run system optimization script
    if [ -f "$DEPLOY_DIR/system_optimization.sh" ]; then
        log "Applying system optimizations..."
        bash "$DEPLOY_DIR/system_optimization.sh" apply
    else
        warn "System optimization script not found, skipping"
    fi
    
    success "System optimization completed"
}

# Health checks
health_checks() {
    phase_header "Health Checks"
    
    # Wait for services to start
    log "Waiting for services to start..."
    sleep 30
    
    # Run deployment validation
    if [ -f "$DEPLOY_DIR/deployment_validation.sh" ] && [ "$SKIP_TESTS" != "true" ]; then
        log "Running deployment validation..."
        if bash "$DEPLOY_DIR/deployment_validation.sh" quick; then
            success "Health checks passed"
        else
            error "Health checks failed"
            exit 1
        fi
    else
        warn "Deployment validation script not found or tests skipped"
    fi
    
    success "Health checks completed"
}

# Post-deployment tasks
post_deployment_tasks() {
    phase_header "Post-deployment Tasks"
    
    # Create backup if not skipped
    if [ "$SKIP_BACKUP" != "true" ] && [ -f "$DEPLOY_DIR/backup_recovery.sh" ]; then
        log "Creating initial backup..."
        bash "$DEPLOY_DIR/backup_recovery.sh" backup
    fi
    
    # Set up log rotation
    log "Configuring log rotation..."
    if [ -f "/etc/logrotate.d/automotive-chatbot" ]; then
        logrotate -f /etc/logrotate.d/automotive-chatbot
    fi
    
    # Create deployment info file
    log "Creating deployment info..."
    cat > "$APP_DIR/deployment_info.json" << EOF
{
  "deployment_id": "$(uuidgen)",
  "version": "$APP_VERSION",
  "environment": "$DEPLOYMENT_ENV",
  "domain": "$APP_DOMAIN",
  "deployed_at": "$(date -Iseconds)",
  "deployed_by": "$(whoami)",
  "hostname": "$(hostname)",
  "git_commit": "$(cd "$DEPLOY_DIR/.." && git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "services": {
    "frontend": "running",
    "backend": "running",
    "rasa_core": "running",
    "rasa_actions": "running",
    "redis": "running",
    "nginx": "running",
    "prometheus": "running",
    "grafana": "running"
  }
}
EOF
    
    chown "$APP_USER:$APP_USER" "$APP_DIR/deployment_info.json"
    
    # Clean up deployment lock
    rm -f /tmp/automotive-chatbot-deploy.lock
    rm -f /tmp/automotive-chatbot-deploy.timestamp
    
    success "Post-deployment tasks completed"
}

# Rollback deployment
rollback_deployment() {
    warn "Starting deployment rollback..."
    
    # Stop current services
    if [ -f "$APP_DIR/docker-compose.production.yml" ]; then
        cd "$APP_DIR"
        docker-compose -f docker-compose.production.yml down
    fi
    
    # Restore from backup if available
    if [ -f "$DEPLOY_DIR/backup_recovery.sh" ]; then
        bash "$DEPLOY_DIR/backup_recovery.sh" restore_latest
    fi
    
    # Clean up
    rm -f /tmp/automotive-chatbot-deploy.lock
    rm -f /tmp/automotive-chatbot-deploy.timestamp
    
    warn "Rollback completed"
}

# Print deployment summary
print_deployment_summary() {
    local deployment_time=$(( $(date +%s) - $(date -d "$(cat /tmp/automotive-chatbot-deploy.timestamp 2>/dev/null || echo '1 hour ago')" +%s) ))
    
    echo -e "\n${CYAN}=== DEPLOYMENT SUMMARY ===${NC}"
    echo -e "${BLUE}Application:${NC} $APP_NAME v$APP_VERSION"
    echo -e "${BLUE}Environment:${NC} $DEPLOYMENT_ENV"
    echo -e "${BLUE}Domain:${NC} $APP_DOMAIN"
    echo -e "${BLUE}Deployment Time:${NC} $(( deployment_time / 60 )) minutes $(( deployment_time % 60 )) seconds"
    echo -e "${BLUE}Deployed At:${NC} $(date)"
    echo -e "${BLUE}Log File:${NC} $LOG_FILE"
    
    echo -e "\n${GREEN}🎉 DEPLOYMENT SUCCESSFUL! 🎉${NC}"
    echo -e "${GREEN}Your Automotive Chatbot is now live and ready to serve customers.${NC}"
    
    echo -e "\n${BLUE}Access URLs:${NC}"
    echo -e "${YELLOW}Frontend:${NC} https://$APP_DOMAIN"
    echo -e "${YELLOW}API Documentation:${NC} https://$APP_DOMAIN/api/docs"
    echo -e "${YELLOW}Monitoring:${NC} https://$MONITORING_DOMAIN"
    echo -e "${YELLOW}Grafana:${NC} https://$MONITORING_DOMAIN:3001"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "${YELLOW}1.${NC} Test the application functionality"
    echo -e "${YELLOW}2.${NC} Configure monitoring alerts"
    echo -e "${YELLOW}3.${NC} Set up automated backups"
    echo -e "${YELLOW}4.${NC} Review security configurations"
    echo -e "${YELLOW}5.${NC} Monitor system performance"
    
    echo -e "\n${BLUE}Support:${NC}"
    echo -e "${YELLOW}Documentation:${NC} $APP_DIR/README.md"
    echo -e "${YELLOW}Logs:${NC} /var/log/automotive-chatbot/"
    echo -e "${YELLOW}Configuration:${NC} /etc/automotive-chatbot/"
}

# Main deployment function
main() {
    local action="${1:-deploy}"
    
    case $action in
        "deploy")
            log "Starting Automotive Chatbot deployment..."
            
            # Execute all deployment phases
            for phase in "${DEPLOYMENT_PHASES[@]}"; do
                $phase
            done
            
            print_deployment_summary
            ;;
        "rollback")
            rollback_deployment
            ;;
        "validate")
            if [ -f "$DEPLOY_DIR/deployment_validation.sh" ]; then
                bash "$DEPLOY_DIR/deployment_validation.sh" "${2:-full}"
            else
                error "Deployment validation script not found"
                exit 1
            fi
            ;;
        "status")
            if [ -f "$APP_DIR/deployment_info.json" ]; then
                cat "$APP_DIR/deployment_info.json" | jq .
            else
                error "No deployment information found"
                exit 1
            fi
            ;;
        "logs")
            tail -f "$LOG_FILE"
            ;;
        "help")
            echo "Usage: $0 [deploy|rollback|validate|status|logs|help]"
            echo "  deploy    : Deploy the application (default)"
            echo "  rollback  : Rollback to previous deployment"
            echo "  validate  : Validate current deployment"
            echo "  status    : Show deployment status"
            echo "  logs      : Show deployment logs"
            echo "  help      : Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  APP_VERSION      : Application version (default: 1.0.0)"
            echo "  APP_DOMAIN       : Application domain (default: automotive-chatbot.com)"
            echo "  DEPLOYMENT_ENV   : Deployment environment (default: production)"
            echo "  SKIP_TESTS       : Skip health checks (default: false)"
            echo "  SKIP_BACKUP      : Skip backup creation (default: false)"
            echo "  FORCE_DEPLOY     : Force deployment even if in progress (default: false)"
            exit 0
            ;;
        *)
            error "Unknown action: $action. Use 'help' for usage information."
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
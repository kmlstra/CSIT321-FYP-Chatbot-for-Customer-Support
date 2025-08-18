#!/bin/bash

# SSL Certificate Setup Script for Automotive Chatbot
# This script automates SSL certificate generation and configuration

set -euo pipefail

# Configuration
DOMAIN="your-domain.com"
WWW_DOMAIN="www.your-domain.com"
API_DOMAIN="api.your-domain.com"
EMAIL="admin@your-domain.com"
WEBROOT="/var/www/html"
SSL_DIR="/etc/ssl/automotive-chatbot"
NGINX_CONF_DIR="/etc/nginx/sites-available"
CERTBOT_DIR="/etc/letsencrypt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Install required packages
install_dependencies() {
    log "Installing SSL dependencies..."
    
    # Update package list
    apt-get update -y
    
    # Install required packages
    apt-get install -y \
        nginx \
        certbot \
        python3-certbot-nginx \
        openssl \
        curl \
        wget
    
    log "Dependencies installed successfully"
}

# Create SSL directories
create_ssl_directories() {
    log "Creating SSL directories..."
    
    mkdir -p $SSL_DIR/{certs,private,csr}
    mkdir -p $WEBROOT/.well-known/acme-challenge
    
    # Set proper permissions
    chmod 755 $SSL_DIR
    chmod 700 $SSL_DIR/private
    chmod 755 $SSL_DIR/certs
    chmod 755 $SSL_DIR/csr
    
    log "SSL directories created"
}

# Generate self-signed certificate for initial setup
generate_self_signed_cert() {
    log "Generating self-signed certificate for initial setup..."
    
    # Create OpenSSL configuration
    cat > $SSL_DIR/openssl.cnf << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = US
ST = State
L = City
O = Automotive Chatbot
OU = IT Department
CN = $DOMAIN

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = $WWW_DOMAIN
DNS.3 = $API_DOMAIN
DNS.4 = localhost
IP.1 = 127.0.0.1
EOF

    # Generate private key
    openssl genrsa -out $SSL_DIR/private/automotive-chatbot.key 2048
    
    # Generate certificate signing request
    openssl req -new \
        -key $SSL_DIR/private/automotive-chatbot.key \
        -out $SSL_DIR/csr/automotive-chatbot.csr \
        -config $SSL_DIR/openssl.cnf
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 \
        -in $SSL_DIR/csr/automotive-chatbot.csr \
        -signkey $SSL_DIR/private/automotive-chatbot.key \
        -out $SSL_DIR/certs/automotive-chatbot.crt \
        -extensions v3_req \
        -extfile $SSL_DIR/openssl.cnf
    
    # Set proper permissions
    chmod 600 $SSL_DIR/private/automotive-chatbot.key
    chmod 644 $SSL_DIR/certs/automotive-chatbot.crt
    
    log "Self-signed certificate generated"
}

# Configure Nginx for initial setup
configure_nginx_initial() {
    log "Configuring Nginx for initial setup..."
    
    # Create initial Nginx configuration
    cat > $NGINX_CONF_DIR/automotive-chatbot << 'EOF'
# Initial Nginx configuration for Automotive Chatbot
# This configuration will be updated after obtaining Let's Encrypt certificates

server {
    listen 80;
    listen [::]:80;
    server_name DOMAIN_PLACEHOLDER WWW_DOMAIN_PLACEHOLDER API_DOMAIN_PLACEHOLDER;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root WEBROOT_PLACEHOLDER;
        try_files $uri =404;
    }
    
    # Redirect all other traffic to HTTPS (will be enabled after SSL setup)
    # return 301 https://$server_name$request_uri;
    
    # Temporary location for testing
    location / {
        return 200 'SSL setup in progress';
        add_header Content-Type text/plain;
    }
}

# HTTPS server block (will be configured after obtaining certificates)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name DOMAIN_PLACEHOLDER WWW_DOMAIN_PLACEHOLDER;
    
    # SSL configuration (temporary self-signed)
    ssl_certificate SSL_DIR_PLACEHOLDER/certs/automotive-chatbot.crt;
    ssl_certificate_key SSL_DIR_PLACEHOLDER/private/automotive-chatbot.key;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Frontend application
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
}

# API server block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name API_DOMAIN_PLACEHOLDER;
    
    # SSL configuration (temporary self-signed)
    ssl_certificate SSL_DIR_PLACEHOLDER/certs/automotive-chatbot.crt;
    ssl_certificate_key SSL_DIR_PLACEHOLDER/private/automotive-chatbot.key;
    
    # SSL security settings (same as above)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # API endpoints
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # RASA webhook
    location /webhooks/ {
        proxy_pass http://localhost:5005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF

    # Replace placeholders
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" $NGINX_CONF_DIR/automotive-chatbot
    sed -i "s/WWW_DOMAIN_PLACEHOLDER/$WWW_DOMAIN/g" $NGINX_CONF_DIR/automotive-chatbot
    sed -i "s/API_DOMAIN_PLACEHOLDER/$API_DOMAIN/g" $NGINX_CONF_DIR/automotive-chatbot
    sed -i "s|WEBROOT_PLACEHOLDER|$WEBROOT|g" $NGINX_CONF_DIR/automotive-chatbot
    sed -i "s|SSL_DIR_PLACEHOLDER|$SSL_DIR|g" $NGINX_CONF_DIR/automotive-chatbot
    
    # Enable the site
    ln -sf $NGINX_CONF_DIR/automotive-chatbot /etc/nginx/sites-enabled/
    
    # Remove default site
    rm -f /etc/nginx/sites-enabled/default
    
    # Test Nginx configuration
    nginx -t || error "Nginx configuration test failed"
    
    # Restart Nginx
    systemctl restart nginx
    systemctl enable nginx
    
    log "Nginx configured for initial setup"
}

# Obtain Let's Encrypt certificates
obtain_letsencrypt_cert() {
    log "Obtaining Let's Encrypt certificates..."
    
    # Check if domain is accessible
    if ! curl -s "http://$DOMAIN/.well-known/acme-challenge/test" > /dev/null 2>&1; then
        warn "Domain may not be properly configured. Continuing anyway..."
    fi
    
    # Obtain certificate using webroot method
    certbot certonly \
        --webroot \
        --webroot-path=$WEBROOT \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --domains $DOMAIN,$WWW_DOMAIN,$API_DOMAIN \
        --non-interactive
    
    if [ $? -eq 0 ]; then
        log "Let's Encrypt certificates obtained successfully"
    else
        warn "Failed to obtain Let's Encrypt certificates. Using self-signed certificates."
        return 1
    fi
}

# Update Nginx configuration with Let's Encrypt certificates
update_nginx_ssl() {
    log "Updating Nginx configuration with Let's Encrypt certificates..."
    
    # Create updated Nginx configuration
    cat > $NGINX_CONF_DIR/automotive-chatbot << EOF
# Production Nginx configuration for Automotive Chatbot with Let's Encrypt SSL

# Rate limiting zones
limit_req_zone \$binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=general:10m rate=1r/s;

# Upstream servers
upstream frontend {
    server localhost:3000;
    keepalive 32;
}

upstream backend {
    server localhost:8000;
    keepalive 32;
}

upstream rasa {
    server localhost:5005;
    keepalive 16;
}

# HTTP server - redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name $DOMAIN $WWW_DOMAIN $API_DOMAIN;
    
    # Let's Encrypt challenge location
    location /.well-known/acme-challenge/ {
        root $WEBROOT;
        try_files \$uri =404;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $DOMAIN $WWW_DOMAIN;
    
    # SSL configuration
    ssl_certificate $CERTBOT_DIR/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key $CERTBOT_DIR/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate $CERTBOT_DIR/live/$DOMAIN/chain.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' wss:; media-src 'self'; object-src 'none'; child-src 'self'; form-action 'self'; base-uri 'self';" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req zone=general burst=10 nodelay;
    
    # Frontend application
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
    }
    
    # Static files caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        proxy_pass http://frontend;
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header X-Content-Type-Options "nosniff";
    }
}

# API server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name $API_DOMAIN;
    
    # SSL configuration
    ssl_certificate $CERTBOT_DIR/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key $CERTBOT_DIR/live/$DOMAIN/privkey.pem;
    ssl_trusted_certificate $CERTBOT_DIR/live/$DOMAIN/chain.pem;
    
    # SSL security settings (same as above)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # Rate limiting for API
    limit_req zone=api burst=20 nodelay;
    
    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
    }
    
    # Login endpoint with stricter rate limiting
    location /api/auth/login {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # RASA webhook
    location /webhooks/ {
        proxy_pass http://rasa;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 30s;
        proxy_send_timeout 300s;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://backend;
        access_log off;
    }
}
EOF

    # Test Nginx configuration
    nginx -t || error "Updated Nginx configuration test failed"
    
    # Reload Nginx
    systemctl reload nginx
    
    log "Nginx configuration updated with Let's Encrypt certificates"
}

# Setup automatic certificate renewal
setup_cert_renewal() {
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash

# SSL Certificate Renewal Script
LOG_FILE="/var/log/ssl-renewal.log"

echo "[$(date)] Starting SSL certificate renewal" >> $LOG_FILE

# Renew certificates
certbot renew --quiet --no-self-upgrade >> $LOG_FILE 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date)] Certificate renewal successful" >> $LOG_FILE
    
    # Reload Nginx if certificates were renewed
    if systemctl is-active --quiet nginx; then
        systemctl reload nginx
        echo "[$(date)] Nginx reloaded" >> $LOG_FILE
    fi
else
    echo "[$(date)] Certificate renewal failed" >> $LOG_FILE
fi

echo "[$(date)] SSL certificate renewal completed" >> $LOG_FILE
EOF

    chmod +x /usr/local/bin/renew-ssl.sh
    
    # Add to crontab (run twice daily)
    echo "0 2,14 * * * root /usr/local/bin/renew-ssl.sh" >> /etc/crontab
    
    # Create systemd timer for more reliable scheduling
    cat > /etc/systemd/system/ssl-renewal.service << 'EOF'
[Unit]
Description=SSL Certificate Renewal
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/renew-ssl.sh
User=root
EOF

    cat > /etc/systemd/system/ssl-renewal.timer << 'EOF'
[Unit]
Description=SSL Certificate Renewal Timer
Requires=ssl-renewal.service

[Timer]
OnCalendar=*-*-* 02,14:00:00
RandomizedDelaySec=3600
Persistent=true

[Install]
WantedBy=timers.target
EOF

    # Enable and start the timer
    systemctl daemon-reload
    systemctl enable ssl-renewal.timer
    systemctl start ssl-renewal.timer
    
    log "Automatic certificate renewal configured"
}

# Create SSL monitoring script
create_ssl_monitoring() {
    log "Creating SSL monitoring script..."
    
    cat > /usr/local/bin/ssl-monitor.sh << 'EOF'
#!/bin/bash

# SSL Certificate Monitoring Script
DOMAINS=("DOMAIN_PLACEHOLDER" "WWW_DOMAIN_PLACEHOLDER" "API_DOMAIN_PLACEHOLDER")
EMAIL="EMAIL_PLACEHOLDER"
WARNING_DAYS=30
CRITICAL_DAYS=7
LOG_FILE="/var/log/ssl-monitor.log"

for domain in "${DOMAINS[@]}"; do
    echo "[$(date)] Checking SSL certificate for $domain" >> $LOG_FILE
    
    # Get certificate expiration date
    expiry_date=$(echo | openssl s_client -servername $domain -connect $domain:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
    
    if [ -n "$expiry_date" ]; then
        expiry_epoch=$(date -d "$expiry_date" +%s)
        current_epoch=$(date +%s)
        days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
        
        echo "[$(date)] $domain expires in $days_until_expiry days" >> $LOG_FILE
        
        if [ $days_until_expiry -le $CRITICAL_DAYS ]; then
            echo "CRITICAL: SSL certificate for $domain expires in $days_until_expiry days!" | mail -s "CRITICAL: SSL Certificate Expiring Soon - $domain" $EMAIL
        elif [ $days_until_expiry -le $WARNING_DAYS ]; then
            echo "WARNING: SSL certificate for $domain expires in $days_until_expiry days" | mail -s "WARNING: SSL Certificate Expiring - $domain" $EMAIL
        fi
    else
        echo "[$(date)] Failed to check certificate for $domain" >> $LOG_FILE
        echo "Failed to check SSL certificate for $domain" | mail -s "SSL Certificate Check Failed - $domain" $EMAIL
    fi
done
EOF

    # Replace placeholders
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /usr/local/bin/ssl-monitor.sh
    sed -i "s/WWW_DOMAIN_PLACEHOLDER/$WWW_DOMAIN/g" /usr/local/bin/ssl-monitor.sh
    sed -i "s/API_DOMAIN_PLACEHOLDER/$API_DOMAIN/g" /usr/local/bin/ssl-monitor.sh
    sed -i "s/EMAIL_PLACEHOLDER/$EMAIL/g" /usr/local/bin/ssl-monitor.sh
    
    chmod +x /usr/local/bin/ssl-monitor.sh
    
    # Add to daily cron
    echo "0 8 * * * root /usr/local/bin/ssl-monitor.sh" >> /etc/crontab
    
    log "SSL monitoring script created"
}

# Main execution function
main() {
    log "Starting SSL setup for Automotive Chatbot..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --domain)
                DOMAIN="$2"
                WWW_DOMAIN="www.$2"
                API_DOMAIN="api.$2"
                shift 2
                ;;
            --email)
                EMAIL="$2"
                shift 2
                ;;
            --webroot)
                WEBROOT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--domain DOMAIN] [--email EMAIL] [--webroot PATH]"
                echo "  --domain   : Primary domain name (default: your-domain.com)"
                echo "  --email    : Email for Let's Encrypt notifications (default: admin@your-domain.com)"
                echo "  --webroot  : Web root directory (default: /var/www/html)"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    check_root
    install_dependencies
    create_ssl_directories
    generate_self_signed_cert
    configure_nginx_initial
    
    # Try to obtain Let's Encrypt certificates
    if obtain_letsencrypt_cert; then
        update_nginx_ssl
        setup_cert_renewal
    else
        warn "Continuing with self-signed certificates"
    fi
    
    create_ssl_monitoring
    
    log "SSL setup completed successfully!"
    log "Configuration summary:"
    log "  Domain: $DOMAIN"
    log "  WWW Domain: $WWW_DOMAIN"
    log "  API Domain: $API_DOMAIN"
    log "  Email: $EMAIL"
    log "  SSL Directory: $SSL_DIR"
    log "  Webroot: $WEBROOT"
    
    log "Next steps:"
    log "  1. Ensure DNS records point to this server"
    log "  2. Test SSL configuration: https://$DOMAIN"
    log "  3. Check certificate status: certbot certificates"
    log "  4. Monitor renewal logs: tail -f /var/log/ssl-renewal.log"
    log "  5. Test automatic renewal: certbot renew --dry-run"
}

# Run main function with all arguments
main "$@"
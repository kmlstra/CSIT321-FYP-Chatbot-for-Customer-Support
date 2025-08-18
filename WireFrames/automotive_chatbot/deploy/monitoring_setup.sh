#!/bin/bash

# Monitoring Setup Script for Automotive Chatbot
# This script sets up Prometheus, Grafana, and AlertManager for comprehensive monitoring

set -euo pipefail

# Configuration
MONITORING_DIR="/opt/monitoring"
PROMETHEUS_VERSION="2.45.0"
GRAFANA_VERSION="10.0.0"
ALERTMANAGER_VERSION="0.25.0"
NODE_EXPORTER_VERSION="1.6.0"
PROMETHEUS_USER="prometheus"
GRAFANA_USER="grafana"
ALERTMANAGER_USER="alertmanager"
LOG_FILE="/var/log/monitoring-setup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a $LOG_FILE
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

# Install dependencies
install_dependencies() {
    log "Installing monitoring dependencies..."
    
    # Update package list
    apt-get update -y
    
    # Install required packages
    apt-get install -y \
        wget \
        curl \
        tar \
        adduser \
        libfontconfig1 \
        musl \
        nginx \
        certbot \
        python3-certbot-nginx \
        jq \
        htop \
        iotop \
        netstat-nat
    
    log "Dependencies installed successfully"
}

# Create monitoring users
create_users() {
    log "Creating monitoring users..."
    
    # Create prometheus user
    if ! id "$PROMETHEUS_USER" &>/dev/null; then
        useradd --no-create-home --shell /bin/false $PROMETHEUS_USER
        log "Created user: $PROMETHEUS_USER"
    fi
    
    # Create grafana user
    if ! id "$GRAFANA_USER" &>/dev/null; then
        useradd --no-create-home --shell /bin/false $GRAFANA_USER
        log "Created user: $GRAFANA_USER"
    fi
    
    # Create alertmanager user
    if ! id "$ALERTMANAGER_USER" &>/dev/null; then
        useradd --no-create-home --shell /bin/false $ALERTMANAGER_USER
        log "Created user: $ALERTMANAGER_USER"
    fi
    
    log "Monitoring users created successfully"
}

# Setup directories
setup_directories() {
    log "Setting up monitoring directories..."
    
    # Create main monitoring directory
    mkdir -p $MONITORING_DIR
    
    # Prometheus directories
    mkdir -p $MONITORING_DIR/prometheus/{data,config,rules}
    mkdir -p /etc/prometheus
    mkdir -p /var/lib/prometheus
    
    # Grafana directories
    mkdir -p $MONITORING_DIR/grafana/{data,logs,plugins,dashboards}
    mkdir -p /etc/grafana
    mkdir -p /var/lib/grafana
    mkdir -p /var/log/grafana
    
    # AlertManager directories
    mkdir -p $MONITORING_DIR/alertmanager/{data,config}
    mkdir -p /etc/alertmanager
    mkdir -p /var/lib/alertmanager
    
    # Node Exporter directory
    mkdir -p $MONITORING_DIR/node_exporter
    
    # Set ownership
    chown -R $PROMETHEUS_USER:$PROMETHEUS_USER $MONITORING_DIR/prometheus
    chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus
    chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /var/lib/prometheus
    
    chown -R $GRAFANA_USER:$GRAFANA_USER $MONITORING_DIR/grafana
    chown -R $GRAFANA_USER:$GRAFANA_USER /etc/grafana
    chown -R $GRAFANA_USER:$GRAFANA_USER /var/lib/grafana
    chown -R $GRAFANA_USER:$GRAFANA_USER /var/log/grafana
    
    chown -R $ALERTMANAGER_USER:$ALERTMANAGER_USER $MONITORING_DIR/alertmanager
    chown -R $ALERTMANAGER_USER:$ALERTMANAGER_USER /etc/alertmanager
    chown -R $ALERTMANAGER_USER:$ALERTMANAGER_USER /var/lib/alertmanager
    
    log "Monitoring directories setup completed"
}

# Install Prometheus
install_prometheus() {
    log "Installing Prometheus v$PROMETHEUS_VERSION..."
    
    cd /tmp
    
    # Download Prometheus
    wget https://github.com/prometheus/prometheus/releases/download/v$PROMETHEUS_VERSION/prometheus-$PROMETHEUS_VERSION.linux-amd64.tar.gz
    
    # Extract and install
    tar xvf prometheus-$PROMETHEUS_VERSION.linux-amd64.tar.gz
    cd prometheus-$PROMETHEUS_VERSION.linux-amd64
    
    # Copy binaries
    cp prometheus /usr/local/bin/
    cp promtool /usr/local/bin/
    
    # Set permissions
    chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/prometheus
    chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/promtool
    
    # Copy console files
    cp -r consoles /etc/prometheus
    cp -r console_libraries /etc/prometheus
    
    # Set ownership
    chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/consoles
    chown -R $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/console_libraries
    
    # Cleanup
    cd /
    rm -rf /tmp/prometheus-$PROMETHEUS_VERSION.linux-amd64*
    
    log "Prometheus installed successfully"
}

# Install Node Exporter
install_node_exporter() {
    log "Installing Node Exporter v$NODE_EXPORTER_VERSION..."
    
    cd /tmp
    
    # Download Node Exporter
    wget https://github.com/prometheus/node_exporter/releases/download/v$NODE_EXPORTER_VERSION/node_exporter-$NODE_EXPORTER_VERSION.linux-amd64.tar.gz
    
    # Extract and install
    tar xvf node_exporter-$NODE_EXPORTER_VERSION.linux-amd64.tar.gz
    cd node_exporter-$NODE_EXPORTER_VERSION.linux-amd64
    
    # Copy binary
    cp node_exporter /usr/local/bin/
    
    # Set permissions
    chown $PROMETHEUS_USER:$PROMETHEUS_USER /usr/local/bin/node_exporter
    
    # Cleanup
    cd /
    rm -rf /tmp/node_exporter-$NODE_EXPORTER_VERSION.linux-amd64*
    
    log "Node Exporter installed successfully"
}

# Install AlertManager
install_alertmanager() {
    log "Installing AlertManager v$ALERTMANAGER_VERSION..."
    
    cd /tmp
    
    # Download AlertManager
    wget https://github.com/prometheus/alertmanager/releases/download/v$ALERTMANAGER_VERSION/alertmanager-$ALERTMANAGER_VERSION.linux-amd64.tar.gz
    
    # Extract and install
    tar xvf alertmanager-$ALERTMANAGER_VERSION.linux-amd64.tar.gz
    cd alertmanager-$ALERTMANAGER_VERSION.linux-amd64
    
    # Copy binaries
    cp alertmanager /usr/local/bin/
    cp amtool /usr/local/bin/
    
    # Set permissions
    chown $ALERTMANAGER_USER:$ALERTMANAGER_USER /usr/local/bin/alertmanager
    chown $ALERTMANAGER_USER:$ALERTMANAGER_USER /usr/local/bin/amtool
    
    # Cleanup
    cd /
    rm -rf /tmp/alertmanager-$ALERTMANAGER_VERSION.linux-amd64*
    
    log "AlertManager installed successfully"
}

# Install Grafana
install_grafana() {
    log "Installing Grafana v$GRAFANA_VERSION..."
    
    # Add Grafana repository
    wget -q -O - https://packages.grafana.com/gpg.key | apt-key add -
    echo "deb https://packages.grafana.com/oss/deb stable main" | tee -a /etc/apt/sources.list.d/grafana.list
    
    # Update and install
    apt-get update
    apt-get install -y grafana
    
    # Enable and start Grafana
    systemctl daemon-reload
    systemctl enable grafana-server
    
    log "Grafana installed successfully"
}

# Configure Prometheus
configure_prometheus() {
    log "Configuring Prometheus..."
    
    # Create Prometheus configuration
    cat > /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "/etc/prometheus/rules/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'automotive-chatbot-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'automotive-chatbot-frontend'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'rasa-core'
    static_configs:
      - targets: ['localhost:5005']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'rasa-actions'
    static_configs:
      - targets: ['localhost:5055']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']

  - job_name: 'mongodb'
    static_configs:
      - targets: ['localhost:9216']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
EOF

    # Set ownership
    chown $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/prometheus.yml
    
    log "Prometheus configuration created"
}

# Configure AlertManager
configure_alertmanager() {
    log "Configuring AlertManager..."
    
    # Create AlertManager configuration
    cat > /etc/alertmanager/alertmanager.yml << 'EOF'
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@automotive-chatbot.com'
  smtp_auth_username: ''
  smtp_auth_password: ''

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://localhost:8000/api/alerts/webhook'
        send_resolved: true
    email_configs:
      - to: 'admin@automotive-chatbot.com'
        subject: 'Automotive Chatbot Alert: {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          Instance: {{ .Labels.instance }}
          Severity: {{ .Labels.severity }}
          {{ end }}

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

    # Set ownership
    chown $ALERTMANAGER_USER:$ALERTMANAGER_USER /etc/alertmanager/alertmanager.yml
    
    log "AlertManager configuration created"
}

# Configure Grafana
configure_grafana() {
    log "Configuring Grafana..."
    
    # Create Grafana configuration
    cat > /etc/grafana/grafana.ini << 'EOF'
[default]
instance_name = automotive-chatbot-monitoring

[server]
protocol = http
http_addr = 0.0.0.0
http_port = 3001
domain = localhost
root_url = http://localhost:3001/
serve_from_sub_path = false

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[session]
provider = file
provider_config = sessions
cookie_name = grafana_sess
cookie_secure = false
session_life_time = 86400

[security]
admin_user = admin
admin_password = automotive_chatbot_2024
secret_key = automotive_chatbot_secret_key_2024
disable_gravatar = true

[users]
allow_sign_up = false
allow_org_create = false
auto_assign_org = true
auto_assign_org_role = Viewer
default_theme = dark

[auth.anonymous]
enabled = false

[smtp]
enabled = false
host = localhost:587
user = 
password = 
from_address = grafana@automotive-chatbot.com
from_name = Grafana

[alerting]
enabled = true
execute_alerts = true

[log]
mode = file
level = info
format = text

[log.file]
path = /var/log/grafana/grafana.log
max_lines = 1000000
max_size_shift = 28
daily_rotate = true
max_days = 7
EOF

    # Set ownership
    chown $GRAFANA_USER:$GRAFANA_USER /etc/grafana/grafana.ini
    
    log "Grafana configuration created"
}

# Create alert rules
create_alert_rules() {
    log "Creating Prometheus alert rules..."
    
    # Create alert rules file
    cat > /etc/prometheus/rules/automotive_chatbot_alerts.yml << 'EOF'
groups:
  - name: automotive_chatbot_alerts
    rules:
      # Instance down alerts
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute."

      # High CPU usage
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is above 80% for more than 5 minutes."

      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is above 85% for more than 5 minutes."

      # Low disk space
      - alert: LowDiskSpace
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Low disk space on {{ $labels.instance }}"
          description: "Disk space is below 10% on root filesystem."

      # High API response time
      - alert: HighAPIResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          description: "95th percentile response time is above 2 seconds for more than 5 minutes."

      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate"
          description: "Error rate is above 5% for more than 5 minutes."

      # RASA service down
      - alert: RASAServiceDown
        expr: up{job="rasa-core"} == 0 or up{job="rasa-actions"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "RASA service is down"
          description: "RASA Core or Actions service is not responding."

      # Database connection issues
      - alert: DatabaseConnectionIssues
        expr: mongodb_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection issues"
          description: "Cannot connect to MongoDB database."

      # SSL certificate expiry
      - alert: SSLCertificateExpiry
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 7
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate will expire in less than 7 days."
EOF

    # Set ownership
    chown $PROMETHEUS_USER:$PROMETHEUS_USER /etc/prometheus/rules/automotive_chatbot_alerts.yml
    
    log "Alert rules created"
}

# Create systemd services
create_systemd_services() {
    log "Creating systemd services..."
    
    # Prometheus service
    cat > /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=$PROMETHEUS_USER
Group=$PROMETHEUS_USER
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries \
    --web.listen-address=0.0.0.0:9090 \
    --web.enable-lifecycle

[Install]
WantedBy=multi-user.target
EOF

    # Node Exporter service
    cat > /etc/systemd/system/node_exporter.service << EOF
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=$PROMETHEUS_USER
Group=$PROMETHEUS_USER
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

    # AlertManager service
    cat > /etc/systemd/system/alertmanager.service << EOF
[Unit]
Description=AlertManager
Wants=network-online.target
After=network-online.target

[Service]
User=$ALERTMANAGER_USER
Group=$ALERTMANAGER_USER
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file=/etc/alertmanager/alertmanager.yml \
    --storage.path=/var/lib/alertmanager/

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    
    log "Systemd services created"
}

# Configure Nginx reverse proxy
configure_nginx() {
    log "Configuring Nginx reverse proxy..."
    
    # Create Nginx configuration for monitoring
    cat > /etc/nginx/sites-available/monitoring << 'EOF'
server {
    listen 80;
    server_name monitoring.automotive-chatbot.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name monitoring.automotive-chatbot.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/monitoring.automotive-chatbot.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitoring.automotive-chatbot.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Grafana
    location / {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Prometheus
    location /prometheus/ {
        proxy_pass http://localhost:9090/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Basic auth for Prometheus
        auth_basic "Prometheus";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
    
    # AlertManager
    location /alertmanager/ {
        proxy_pass http://localhost:9093/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Basic auth for AlertManager
        auth_basic "AlertManager";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}
EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/monitoring /etc/nginx/sites-enabled/
    
    # Create basic auth file
    echo "admin:$(openssl passwd -apr1 automotive_chatbot_2024)" > /etc/nginx/.htpasswd
    
    # Test Nginx configuration
    nginx -t
    
    log "Nginx configuration created"
}

# Start services
start_services() {
    log "Starting monitoring services..."
    
    # Enable and start services
    systemctl enable prometheus
    systemctl enable node_exporter
    systemctl enable alertmanager
    systemctl enable grafana-server
    
    systemctl start prometheus
    systemctl start node_exporter
    systemctl start alertmanager
    systemctl start grafana-server
    
    # Restart Nginx
    systemctl restart nginx
    
    # Wait for services to start
    sleep 10
    
    # Check service status
    systemctl is-active prometheus || warn "Prometheus service not running"
    systemctl is-active node_exporter || warn "Node Exporter service not running"
    systemctl is-active alertmanager || warn "AlertManager service not running"
    systemctl is-active grafana-server || warn "Grafana service not running"
    
    log "Monitoring services started"
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall for monitoring..."
    
    # Allow monitoring ports
    ufw allow 9090/tcp comment 'Prometheus'
    ufw allow 9093/tcp comment 'AlertManager'
    ufw allow 9100/tcp comment 'Node Exporter'
    ufw allow 3001/tcp comment 'Grafana'
    
    # Allow Nginx monitoring
    ufw allow 9113/tcp comment 'Nginx Exporter'
    
    log "Firewall configured for monitoring"
}

# Create monitoring dashboard
create_dashboards() {
    log "Creating Grafana dashboards..."
    
    # Wait for Grafana to be ready
    sleep 30
    
    # Add Prometheus data source
    curl -X POST \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://localhost:9090",
            "access": "proxy",
            "isDefault": true
        }' \
        http://admin:automotive_chatbot_2024@localhost:3001/api/datasources
    
    # Create automotive chatbot dashboard
    curl -X POST \
        -H "Content-Type: application/json" \
        -d @/opt/monitoring/dashboards/automotive_chatbot_dashboard.json \
        http://admin:automotive_chatbot_2024@localhost:3001/api/dashboards/db
    
    log "Grafana dashboards created"
}

# Health check
health_check() {
    log "Performing monitoring system health check..."
    
    local issues=0
    
    # Check Prometheus
    if ! curl -s http://localhost:9090/-/healthy &>/dev/null; then
        warn "Prometheus health check failed"
        ((issues++))
    fi
    
    # Check Node Exporter
    if ! curl -s http://localhost:9100/metrics &>/dev/null; then
        warn "Node Exporter health check failed"
        ((issues++))
    fi
    
    # Check AlertManager
    if ! curl -s http://localhost:9093/-/healthy &>/dev/null; then
        warn "AlertManager health check failed"
        ((issues++))
    fi
    
    # Check Grafana
    if ! curl -s http://localhost:3001/api/health &>/dev/null; then
        warn "Grafana health check failed"
        ((issues++))
    fi
    
    if [ $issues -eq 0 ]; then
        log "Monitoring system health check passed"
        return 0
    else
        warn "Monitoring system health check found $issues issues"
        return 1
    fi
}

# Main execution function
main() {
    local action="${1:-install}"
    
    case $action in
        "install")
            log "Starting monitoring system installation..."
            check_root
            install_dependencies
            create_users
            setup_directories
            install_prometheus
            install_node_exporter
            install_alertmanager
            install_grafana
            configure_prometheus
            configure_alertmanager
            configure_grafana
            create_alert_rules
            create_systemd_services
            configure_nginx
            configure_firewall
            start_services
            create_dashboards
            log "Monitoring system installation completed successfully"
            ;;
        "health")
            health_check
            ;;
        "restart")
            log "Restarting monitoring services..."
            systemctl restart prometheus node_exporter alertmanager grafana-server
            log "Monitoring services restarted"
            ;;
        "stop")
            log "Stopping monitoring services..."
            systemctl stop prometheus node_exporter alertmanager grafana-server
            log "Monitoring services stopped"
            ;;
        "start")
            log "Starting monitoring services..."
            systemctl start prometheus node_exporter alertmanager grafana-server
            log "Monitoring services started"
            ;;
        "help")
            echo "Usage: $0 [install|health|restart|stop|start|help]"
            echo "  install    : Install and configure monitoring system"
            echo "  health     : Check monitoring system health"
            echo "  restart    : Restart monitoring services"
            echo "  stop       : Stop monitoring services"
            echo "  start      : Start monitoring services"
            echo "  help       : Show this help message"
            exit 0
            ;;
        *)
            error "Unknown action: $action. Use 'help' for usage information."
            ;;
    esac
}

# Run main function with all arguments
main "$@"
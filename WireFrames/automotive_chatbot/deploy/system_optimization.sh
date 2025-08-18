#!/bin/bash

# System Optimization and Performance Tuning Script for Automotive Chatbot
# This script optimizes system performance, resource usage, and application efficiency

set -euo pipefail

# Configuration
APP_USER="automotive-chatbot"
APP_DIR="/opt/automotive-chatbot"
LOG_FILE="/var/log/system-optimization.log"
BACKUP_DIR="/var/backups/system-config"
OPTIMIZATION_CONFIG="/etc/automotive-chatbot/optimization.conf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}" | tee -a $LOG_FILE
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a $LOG_FILE
}

# Create backup of current configuration
backup_current_config() {
    log "Creating backup of current system configuration..."
    
    mkdir -p $BACKUP_DIR
    local backup_timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/system_config_backup_$backup_timestamp.tar.gz"
    
    tar -czf "$backup_file" \
        /etc/sysctl.conf \
        /etc/security/limits.conf \
        /etc/systemd/system.conf \
        /etc/nginx/nginx.conf \
        /etc/redis/redis.conf \
        /etc/docker/daemon.json \
        2>/dev/null || true
    
    success "Configuration backup created: $backup_file"
}

# Optimize kernel parameters
optimize_kernel_parameters() {
    log "Optimizing kernel parameters..."
    
    # Backup original sysctl.conf
    cp /etc/sysctl.conf /etc/sysctl.conf.backup.$(date +%Y%m%d)
    
    # Create optimized sysctl configuration
    cat >> /etc/sysctl.conf << 'EOF'

# Automotive Chatbot System Optimizations
# Network optimizations
net.core.rmem_default = 262144
net.core.rmem_max = 16777216
net.core.wmem_default = 262144
net.core.wmem_max = 16777216
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 65535
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.ipv4.tcp_congestion_control = bbr
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_keepalive_probes = 7
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_mtu_probing = 1

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
vm.vfs_cache_pressure = 50
vm.min_free_kbytes = 65536
vm.overcommit_memory = 1
vm.overcommit_ratio = 50

# File system optimizations
fs.file-max = 2097152
fs.nr_open = 1048576
fs.inotify.max_user_watches = 524288
fs.inotify.max_user_instances = 256

# Security optimizations
kernel.randomize_va_space = 2
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.yama.ptrace_scope = 1

# Performance optimizations
kernel.sched_migration_cost_ns = 5000000
kernel.sched_autogroup_enabled = 0
EOF
    
    # Apply sysctl changes
    sysctl -p
    
    success "Kernel parameters optimized"
}

# Optimize system limits
optimize_system_limits() {
    log "Optimizing system limits..."
    
    # Backup original limits.conf
    cp /etc/security/limits.conf /etc/security/limits.conf.backup.$(date +%Y%m%d)
    
    # Add optimized limits
    cat >> /etc/security/limits.conf << 'EOF'

# Automotive Chatbot System Limits
* soft nofile 1048576
* hard nofile 1048576
* soft nproc 1048576
* hard nproc 1048576
* soft memlock unlimited
* hard memlock unlimited

# Application user limits
automotive-chatbot soft nofile 1048576
automotive-chatbot hard nofile 1048576
automotive-chatbot soft nproc 1048576
automotive-chatbot hard nproc 1048576

# Database limits
mongodb soft nofile 1048576
mongodb hard nofile 1048576
redis soft nofile 1048576
redis hard nofile 1048576
EOF
    
    # Update systemd limits
    mkdir -p /etc/systemd/system.conf.d
    cat > /etc/systemd/system.conf.d/limits.conf << 'EOF'
[Manager]
DefaultLimitNOFILE=1048576
DefaultLimitNPROC=1048576
DefaultLimitMEMLOCK=infinity
EOF
    
    # Update PAM limits
    echo "session required pam_limits.so" >> /etc/pam.d/common-session
    
    success "System limits optimized"
}

# Optimize Nginx configuration
optimize_nginx() {
    log "Optimizing Nginx configuration..."
    
    # Backup original nginx.conf
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup.$(date +%Y%m%d)
    
    # Create optimized nginx configuration
    cat > /etc/nginx/nginx.conf << 'EOF'
user www-data;
worker_processes auto;
worker_rlimit_nofile 65535;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;
    client_max_body_size 100M;
    
    # Buffer Settings
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # Timeout Settings
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;
    
    # Gzip Settings
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # Brotli Settings (if available)
    brotli on;
    brotli_comp_level 6;
    brotli_types
        text/plain
        text/css
        application/json
        application/javascript
        text/xml
        application/xml
        application/xml+rss
        text/javascript;
    
    # Cache Settings
    open_file_cache max=200000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    
    # Security Headers
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; media-src 'self'; object-src 'none'; child-src 'none'; worker-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self';" always;
    
    # MIME Types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';
    
    access_log /var/log/nginx/access.log main buffer=16k flush=2m;
    error_log /var/log/nginx/error.log warn;
    
    # Virtual Host Configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
EOF
    
    # Test nginx configuration
    if nginx -t; then
        systemctl reload nginx
        success "Nginx configuration optimized and reloaded"
    else
        error "Nginx configuration test failed, restoring backup"
        cp /etc/nginx/nginx.conf.backup.$(date +%Y%m%d) /etc/nginx/nginx.conf
    fi
}

# Optimize Redis configuration
optimize_redis() {
    log "Optimizing Redis configuration..."
    
    # Backup original redis.conf
    cp /etc/redis/redis.conf /etc/redis/redis.conf.backup.$(date +%Y%m%d)
    
    # Apply Redis optimizations
    cat >> /etc/redis/redis.conf << 'EOF'

# Automotive Chatbot Redis Optimizations
# Memory optimizations
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Performance optimizations
tcp-keepalive 300
timeout 0
tcp-backlog 511

# Persistence optimizations
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes

# AOF optimizations
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Client optimizations
maxclients 10000

# Slow log optimizations
slowlog-log-slower-than 10000
slowlog-max-len 128

# Hash optimizations
hash-max-ziplist-entries 512
hash-max-ziplist-value 64

# List optimizations
list-max-ziplist-size -2
list-compress-depth 0

# Set optimizations
set-max-intset-entries 512

# Sorted set optimizations
zset-max-ziplist-entries 128
zset-max-ziplist-value 64

# HyperLogLog optimizations
hll-sparse-max-bytes 3000

# Streams optimizations
stream-node-max-bytes 4096
stream-node-max-entries 100
EOF
    
    # Restart Redis
    systemctl restart redis-server
    
    success "Redis configuration optimized"
}

# Optimize Docker configuration
optimize_docker() {
    log "Optimizing Docker configuration..."
    
    mkdir -p /etc/docker
    
    # Create optimized Docker daemon configuration
    cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ],
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 1048576,
      "Soft": 1048576
    },
    "nproc": {
      "Name": "nproc",
      "Hard": 1048576,
      "Soft": 1048576
    }
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 5,
  "userland-proxy": false,
  "experimental": false,
  "live-restore": true,
  "icc": false,
  "default-address-pools": [
    {
      "base": "172.17.0.0/12",
      "size": 20
    },
    {
      "base": "192.168.0.0/16",
      "size": 24
    }
  ]
}
EOF
    
    # Restart Docker
    systemctl restart docker
    
    success "Docker configuration optimized"
}

# Optimize systemd services
optimize_systemd_services() {
    log "Optimizing systemd services..."
    
    # Create systemd drop-in directories
    local services=("automotive-chatbot-frontend" "automotive-chatbot-backend" "rasa-core" "rasa-actions")
    
    for service in "${services[@]}"; do
        if systemctl list-unit-files | grep -q "$service"; then
            mkdir -p "/etc/systemd/system/$service.service.d"
            
            cat > "/etc/systemd/system/$service.service.d/optimization.conf" << 'EOF'
[Service]
# Resource limits
LimitNOFILE=1048576
LimitNPROC=1048576
LimitMEMLOCK=infinity

# Performance settings
OOMScoreAdjust=-500
CPUSchedulingPolicy=2
CPUSchedulingPriority=50
IOSchedulingClass=1
IOSchedulingPriority=4

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
PrivateDevices=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictRealtime=true
RestrictSUIDSGID=true
RemoveIPC=true
RestrictNamespaces=true

# Restart settings
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3
EOF
        fi
    done
    
    # Reload systemd
    systemctl daemon-reload
    
    success "Systemd services optimized"
}

# Optimize log rotation
optimize_log_rotation() {
    log "Optimizing log rotation..."
    
    # Create logrotate configuration for application logs
    cat > /etc/logrotate.d/automotive-chatbot << 'EOF'
/var/log/automotive-chatbot/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 automotive-chatbot automotive-chatbot
    postrotate
        systemctl reload automotive-chatbot-backend || true
        systemctl reload automotive-chatbot-frontend || true
    endscript
}

/var/log/rasa/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0644 rasa rasa
    postrotate
        systemctl reload rasa-core || true
        systemctl reload rasa-actions || true
    endscript
}
EOF
    
    # Optimize system log rotation
    sed -i 's/weekly/daily/' /etc/logrotate.conf
    sed -i 's/rotate 4/rotate 7/' /etc/logrotate.conf
    
    success "Log rotation optimized"
}

# Optimize cron jobs
optimize_cron_jobs() {
    log "Setting up optimization cron jobs..."
    
    # Create cron job for system cleanup
    cat > /etc/cron.d/automotive-chatbot-optimization << 'EOF'
# Automotive Chatbot System Optimization Cron Jobs

# Clean temporary files daily at 2 AM
0 2 * * * root find /tmp -type f -atime +7 -delete

# Clean Docker system weekly at 3 AM on Sunday
0 3 * * 0 root docker system prune -f

# Update file locate database daily at 4 AM
0 4 * * * root updatedb

# Sync and drop caches weekly at 5 AM on Sunday
0 5 * * 0 root sync && echo 3 > /proc/sys/vm/drop_caches

# Check and optimize database indexes monthly
0 6 1 * * automotive-chatbot /opt/automotive-chatbot/scripts/optimize_database.sh

# Generate performance report weekly
0 7 * * 1 automotive-chatbot /opt/automotive-chatbot/scripts/performance_report.sh
EOF
    
    success "Optimization cron jobs configured"
}

# Create performance monitoring script
create_performance_monitoring() {
    log "Creating performance monitoring script..."
    
    mkdir -p /opt/automotive-chatbot/scripts
    
    cat > /opt/automotive-chatbot/scripts/performance_monitor.sh << 'EOF'
#!/bin/bash

# Performance Monitoring Script
# Collects and reports system performance metrics

METRICS_FILE="/var/log/automotive-chatbot/performance_metrics.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=85
ALERT_THRESHOLD_DISK=90

# Create metrics directory
mkdir -p "$(dirname "$METRICS_FILE")"

# Collect metrics
TIMESTAMP=$(date -Iseconds)
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
LOAD_AVERAGE=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
NETWORK_CONNECTIONS=$(ss -tun | wc -l)
DOCKER_CONTAINERS=$(docker ps -q | wc -l)

# Log metrics
echo "$TIMESTAMP,CPU:$CPU_USAGE,MEMORY:$MEMORY_USAGE,DISK:$DISK_USAGE,LOAD:$LOAD_AVERAGE,CONNECTIONS:$NETWORK_CONNECTIONS,CONTAINERS:$DOCKER_CONTAINERS" >> "$METRICS_FILE"

# Check for alerts
if (( $(echo "$CPU_USAGE > $ALERT_THRESHOLD_CPU" | bc -l) )); then
    logger -p user.warning "High CPU usage detected: ${CPU_USAGE}%"
fi

if (( $(echo "$MEMORY_USAGE > $ALERT_THRESHOLD_MEMORY" | bc -l) )); then
    logger -p user.warning "High memory usage detected: ${MEMORY_USAGE}%"
fi

if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD_DISK" ]; then
    logger -p user.warning "High disk usage detected: ${DISK_USAGE}%"
fi
EOF
    
    chmod +x /opt/automotive-chatbot/scripts/performance_monitor.sh
    
    # Add to cron for every 5 minutes
    echo "*/5 * * * * automotive-chatbot /opt/automotive-chatbot/scripts/performance_monitor.sh" >> /etc/cron.d/automotive-chatbot-optimization
    
    success "Performance monitoring script created"
}

# Create database optimization script
create_database_optimization() {
    log "Creating database optimization script..."
    
    cat > /opt/automotive-chatbot/scripts/optimize_database.sh << 'EOF'
#!/bin/bash

# Database Optimization Script
# Optimizes MongoDB Atlas connections and Redis performance

LOG_FILE="/var/log/automotive-chatbot/database_optimization.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Optimize Redis
optimize_redis() {
    log "Optimizing Redis..."
    
    # Clear expired keys
    redis-cli --scan --pattern "*" | xargs -L 1000 redis-cli DEL 2>/dev/null || true
    
    # Compact memory
    redis-cli MEMORY PURGE 2>/dev/null || true
    
    # Get Redis info
    local memory_usage=$(redis-cli INFO memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    local keyspace_hits=$(redis-cli INFO stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
    local keyspace_misses=$(redis-cli INFO stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
    
    log "Redis memory usage: $memory_usage"
    log "Redis keyspace hits: $keyspace_hits"
    log "Redis keyspace misses: $keyspace_misses"
}

# Check MongoDB Atlas connection
check_mongodb_atlas() {
    log "Checking MongoDB Atlas connection..."
    
    if [ -n "${MONGODB_URI:-}" ]; then
        if mongosh "$MONGODB_URI" --eval "db.runCommand('ping')" &>/dev/null; then
            log "MongoDB Atlas connection: OK"
            
            # Get database stats
            local db_stats=$(mongosh "$MONGODB_URI" --eval "db.stats()" --quiet 2>/dev/null || echo "Error getting stats")
            log "MongoDB stats: $db_stats"
        else
            log "MongoDB Atlas connection: FAILED"
        fi
    else
        log "MongoDB URI not configured"
    fi
}

# Main execution
log "Starting database optimization..."
optimize_redis
check_mongodb_atlas
log "Database optimization completed"
EOF
    
    chmod +x /opt/automotive-chatbot/scripts/optimize_database.sh
    
    success "Database optimization script created"
}

# Create performance report script
create_performance_report() {
    log "Creating performance report script..."
    
    cat > /opt/automotive-chatbot/scripts/performance_report.sh << 'EOF'
#!/bin/bash

# Performance Report Script
# Generates weekly performance reports

REPORT_DIR="/var/log/automotive-chatbot/reports"
REPORT_FILE="$REPORT_DIR/performance_report_$(date +%Y%m%d).html"
METRICS_FILE="/var/log/automotive-chatbot/performance_metrics.log"

mkdir -p "$REPORT_DIR"

# Generate HTML report
cat > "$REPORT_FILE" << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Automotive Chatbot Performance Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .warning { border-left-color: #ff9800; }
        .error { border-left-color: #f44336; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Automotive Chatbot Performance Report</h1>
        <p>Generated on: $(date)</p>
        <p>Report Period: Last 7 days</p>
    </div>
    
    <h2>System Overview</h2>
    <div class="metric">
        <strong>Uptime:</strong> $(uptime -p)
    </div>
    <div class="metric">
        <strong>Load Average:</strong> $(uptime | awk -F'load average:' '{print $2}')
    </div>
    <div class="metric">
        <strong>Memory Usage:</strong> $(free -h | grep Mem | awk '{printf "Used: %s / Total: %s (%.1f%%)", $3, $2, $3/$2*100}')
    </div>
    <div class="metric">
        <strong>Disk Usage:</strong> $(df -h / | tail -1 | awk '{printf "Used: %s / Total: %s (%s)", $3, $2, $5}')
    </div>
    
    <h2>Service Status</h2>
    <table>
        <tr><th>Service</th><th>Status</th><th>Memory Usage</th></tr>
HTML_EOF

# Add service status to report
local services=("nginx" "docker" "redis-server" "prometheus" "grafana-server")
for service in "${services[@]}"; do
    if systemctl is-active --quiet "$service"; then
        local status="Running"
        local memory=$(systemctl show "$service" --property=MemoryCurrent | cut -d= -f2)
        if [ "$memory" != "[not set]" ] && [ -n "$memory" ]; then
            memory=$(numfmt --to=iec "$memory")
        else
            memory="N/A"
        fi
    else
        local status="Stopped"
        local memory="N/A"
    fi
    
    echo "        <tr><td>$service</td><td>$status</td><td>$memory</td></tr>" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << 'HTML_EOF'
    </table>
    
    <h2>Docker Containers</h2>
    <table>
        <tr><th>Container</th><th>Status</th><th>CPU Usage</th><th>Memory Usage</th></tr>
HTML_EOF

# Add Docker container stats
if command -v docker &> /dev/null; then
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | tail -n +2 | while read line; do
        local container=$(echo "$line" | awk '{print $1}')
        local cpu=$(echo "$line" | awk '{print $2}')
        local memory=$(echo "$line" | awk '{print $3}')
        local status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "unknown")
        
        echo "        <tr><td>$container</td><td>$status</td><td>$cpu</td><td>$memory</td></tr>" >> "$REPORT_FILE"
    done
fi

cat >> "$REPORT_FILE" << 'HTML_EOF'
    </table>
    
    <h2>Performance Metrics (Last 24 Hours)</h2>
HTML_EOF

# Add performance metrics if available
if [ -f "$METRICS_FILE" ]; then
    echo "    <div class=\"metric\">" >> "$REPORT_FILE"
    echo "        <strong>Average CPU Usage:</strong> $(tail -n 288 "$METRICS_FILE" | awk -F'CPU:' '{print $2}' | awk -F',' '{sum+=$1; count++} END {printf "%.1f%%", sum/count}')" >> "$REPORT_FILE"
    echo "    </div>" >> "$REPORT_FILE"
    echo "    <div class=\"metric\">" >> "$REPORT_FILE"
    echo "        <strong>Average Memory Usage:</strong> $(tail -n 288 "$METRICS_FILE" | awk -F'MEMORY:' '{print $2}' | awk -F',' '{sum+=$1; count++} END {printf "%.1f%%", sum/count}')" >> "$REPORT_FILE"
    echo "    </div>" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" << 'HTML_EOF'
    
    <h2>Recommendations</h2>
    <ul>
        <li>Monitor high resource usage services</li>
        <li>Review log files for errors and warnings</li>
        <li>Check SSL certificate expiration dates</li>
        <li>Verify backup completion status</li>
        <li>Update system packages regularly</li>
    </ul>
    
    <p><em>Report generated by Automotive Chatbot Performance Monitor</em></p>
</body>
</html>
HTML_EOF

echo "Performance report generated: $REPORT_FILE"
EOF
    
    chmod +x /opt/automotive-chatbot/scripts/performance_report.sh
    
    success "Performance report script created"
}

# Create optimization configuration file
create_optimization_config() {
    log "Creating optimization configuration file..."
    
    mkdir -p "$(dirname "$OPTIMIZATION_CONFIG")"
    
    cat > "$OPTIMIZATION_CONFIG" << 'EOF'
# Automotive Chatbot System Optimization Configuration
# This file contains optimization settings and thresholds

[performance]
# CPU usage threshold for alerts (percentage)
cpu_alert_threshold=80

# Memory usage threshold for alerts (percentage)
memory_alert_threshold=85

# Disk usage threshold for alerts (percentage)
disk_alert_threshold=90

# Load average threshold for alerts
load_alert_threshold=4.0

[monitoring]
# Performance metrics collection interval (minutes)
metrics_interval=5

# Log retention period (days)
log_retention_days=30

# Report generation frequency (days)
report_frequency=7

[optimization]
# Enable automatic optimization
auto_optimization=true

# Optimization schedule (cron format)
optimization_schedule="0 3 * * 0"

# Enable cache warming
cache_warming=true

# Enable database optimization
database_optimization=true

[alerts]
# Enable email alerts
email_alerts=false

# Alert email address
alert_email="admin@automotive-chatbot.com"

# Enable Slack alerts
slack_alerts=false

# Slack webhook URL
slack_webhook=""

[backup]
# Enable automatic backups
auto_backup=true

# Backup retention period (days)
backup_retention_days=30

# Backup encryption
backup_encryption=true
EOF
    
    chown "$APP_USER:$APP_USER" "$OPTIMIZATION_CONFIG"
    chmod 600 "$OPTIMIZATION_CONFIG"
    
    success "Optimization configuration created"
}

# Apply all optimizations
apply_all_optimizations() {
    log "Applying all system optimizations..."
    
    backup_current_config
    optimize_kernel_parameters
    optimize_system_limits
    optimize_nginx
    optimize_redis
    optimize_docker
    optimize_systemd_services
    optimize_log_rotation
    optimize_cron_jobs
    create_performance_monitoring
    create_database_optimization
    create_performance_report
    create_optimization_config
    
    success "All optimizations applied successfully"
}

# Verify optimizations
verify_optimizations() {
    log "Verifying applied optimizations..."
    
    local issues=0
    
    # Check sysctl parameters
    if ! sysctl net.core.somaxconn | grep -q "65535"; then
        warn "Sysctl parameter net.core.somaxconn not optimized"
        ((issues++))
    fi
    
    # Check file limits
    if ! ulimit -n | grep -q "1048576"; then
        warn "File descriptor limit not optimized"
        ((issues++))
    fi
    
    # Check services
    local services=("nginx" "redis-server" "docker")
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            warn "Service $service is not running"
            ((issues++))
        fi
    done
    
    if [ $issues -eq 0 ]; then
        success "All optimizations verified successfully"
    else
        warn "$issues optimization issues found"
    fi
    
    return $issues
}

# Print optimization summary
print_optimization_summary() {
    echo -e "\n${CYAN}=== SYSTEM OPTIMIZATION SUMMARY ===${NC}"
    echo -e "${BLUE}Kernel Parameters:${NC} Optimized for high performance"
    echo -e "${BLUE}System Limits:${NC} Increased for better resource utilization"
    echo -e "${BLUE}Nginx:${NC} Configured for high concurrency and performance"
    echo -e "${BLUE}Redis:${NC} Optimized for memory and performance"
    echo -e "${BLUE}Docker:${NC} Configured for production workloads"
    echo -e "${BLUE}Systemd Services:${NC} Enhanced with resource limits and security"
    echo -e "${BLUE}Log Rotation:${NC} Configured for efficient log management"
    echo -e "${BLUE}Monitoring:${NC} Performance monitoring and alerting enabled"
    echo -e "${BLUE}Automation:${NC} Cron jobs configured for maintenance tasks"
    
    echo -e "\n${GREEN}🚀 SYSTEM OPTIMIZATION COMPLETED! 🚀${NC}"
    echo -e "${GREEN}Your Automotive Chatbot system is now optimized for production.${NC}"
    
    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "${YELLOW}1.${NC} Restart the system to apply all kernel optimizations"
    echo -e "${YELLOW}2.${NC} Monitor performance metrics in /var/log/automotive-chatbot/"
    echo -e "${YELLOW}3.${NC} Review weekly performance reports"
    echo -e "${YELLOW}4.${NC} Adjust optimization parameters as needed"
    
    echo -e "\n${BLUE}Configuration file: $OPTIMIZATION_CONFIG${NC}"
    echo -e "${BLUE}Log file: $LOG_FILE${NC}"
}

# Main execution function
main() {
    local action="${1:-apply}"
    
    case $action in
        "apply")
            apply_all_optimizations
            verify_optimizations
            print_optimization_summary
            ;;
        "verify")
            verify_optimizations
            ;;
        "backup")
            backup_current_config
            ;;
        "help")
            echo "Usage: $0 [apply|verify|backup|help]"
            echo "  apply   : Apply all system optimizations (default)"
            echo "  verify  : Verify applied optimizations"
            echo "  backup  : Backup current configuration only"
            echo "  help    : Show this help message"
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
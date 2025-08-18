#!/bin/bash

# Backup and Disaster Recovery Script for Automotive Chatbot
# This script handles automated backups and disaster recovery procedures

set -euo pipefail

# Configuration
BACKUP_DIR="/var/backups/automotive-chatbot"
S3_BUCKET="automotive-chatbot-backups"
S3_REGION="us-east-1"
ENCRYPTION_KEY_FILE="/etc/automotive-chatbot/backup.key"
LOG_FILE="/var/log/automotive-chatbot-backup.log"
RETENTION_DAYS=30
MONGODB_URI="${MONGODB_URI:-mongodb+srv://username:password@cluster.mongodb.net/automotive_chatbot}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"

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

# Install required packages
install_dependencies() {
    log "Installing backup dependencies..."
    
    # Update package list
    apt-get update -y
    
    # Install required packages
    apt-get install -y \
        awscli \
        mongodb-database-tools \
        redis-tools \
        gpg \
        tar \
        gzip \
        rsync \
        curl \
        jq
    
    # Install MongoDB tools if not available
    if ! command -v mongodump &> /dev/null; then
        wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | apt-key add -
        echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-6.0.list
        apt-get update
        apt-get install -y mongodb-database-tools
    fi
    
    log "Dependencies installed successfully"
}

# Setup backup directories and encryption
setup_backup_environment() {
    log "Setting up backup environment..."
    
    # Create backup directories
    mkdir -p $BACKUP_DIR/{mongodb,redis,application,logs,config}
    mkdir -p $BACKUP_DIR/temp
    
    # Set proper permissions
    chmod 700 $BACKUP_DIR
    chmod 750 $BACKUP_DIR/{mongodb,redis,application,logs,config}
    
    # Generate encryption key if it doesn't exist
    if [ ! -f $ENCRYPTION_KEY_FILE ]; then
        mkdir -p $(dirname $ENCRYPTION_KEY_FILE)
        openssl rand -base64 32 > $ENCRYPTION_KEY_FILE
        chmod 600 $ENCRYPTION_KEY_FILE
        log "Encryption key generated"
    fi
    
    # Configure AWS CLI if credentials are available
    if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
        aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
        aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY
        aws configure set default.region $S3_REGION
        log "AWS CLI configured"
    fi
    
    log "Backup environment setup completed"
}

# Backup MongoDB database
backup_mongodb() {
    log "Starting MongoDB backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/mongodb/mongodb_backup_$timestamp"
    
    # Create MongoDB dump
    if mongodump --uri="$MONGODB_URI" --out="$backup_file" --gzip; then
        log "MongoDB dump created successfully"
    else
        error "Failed to create MongoDB dump"
    fi
    
    # Compress and encrypt the backup
    tar -czf "$backup_file.tar.gz" -C "$BACKUP_DIR/mongodb" "mongodb_backup_$timestamp"
    
    # Encrypt the backup
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$backup_file.tar.gz.gpg" \
        "$backup_file.tar.gz"
    
    # Remove unencrypted files
    rm -rf "$backup_file" "$backup_file.tar.gz"
    
    # Upload to S3
    if upload_to_s3 "$backup_file.tar.gz.gpg" "mongodb/mongodb_backup_$timestamp.tar.gz.gpg"; then
        log "MongoDB backup uploaded to S3"
    else
        warn "Failed to upload MongoDB backup to S3"
    fi
    
    log "MongoDB backup completed: $backup_file.tar.gz.gpg"
}

# Backup Redis data
backup_redis() {
    log "Starting Redis backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/redis/redis_backup_$timestamp.rdb"
    
    # Create Redis backup
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --rdb "$backup_file"
    else
        redis-cli -h $REDIS_HOST -p $REDIS_PORT --rdb "$backup_file"
    fi
    
    if [ -f "$backup_file" ]; then
        log "Redis backup created successfully"
    else
        error "Failed to create Redis backup"
    fi
    
    # Compress and encrypt
    gzip "$backup_file"
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$backup_file.gz.gpg" \
        "$backup_file.gz"
    
    # Remove unencrypted file
    rm -f "$backup_file.gz"
    
    # Upload to S3
    if upload_to_s3 "$backup_file.gz.gpg" "redis/redis_backup_$timestamp.rdb.gz.gpg"; then
        log "Redis backup uploaded to S3"
    else
        warn "Failed to upload Redis backup to S3"
    fi
    
    log "Redis backup completed: $backup_file.gz.gpg"
}

# Backup application files
backup_application() {
    log "Starting application backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/application/app_backup_$timestamp.tar.gz"
    local app_dir="/opt/automotive-chatbot"
    
    # Create application backup
    if [ -d "$app_dir" ]; then
        tar -czf "$backup_file" -C "$(dirname $app_dir)" "$(basename $app_dir)" \
            --exclude='*.log' \
            --exclude='node_modules' \
            --exclude='__pycache__' \
            --exclude='.git' \
            --exclude='*.pyc' \
            --exclude='temp' \
            --exclude='cache'
        
        log "Application files backed up successfully"
    else
        warn "Application directory not found: $app_dir"
        return 0
    fi
    
    # Encrypt the backup
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$backup_file.gpg" \
        "$backup_file"
    
    # Remove unencrypted file
    rm -f "$backup_file"
    
    # Upload to S3
    if upload_to_s3 "$backup_file.gpg" "application/app_backup_$timestamp.tar.gz.gpg"; then
        log "Application backup uploaded to S3"
    else
        warn "Failed to upload application backup to S3"
    fi
    
    log "Application backup completed: $backup_file.gpg"
}

# Backup configuration files
backup_configuration() {
    log "Starting configuration backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/config/config_backup_$timestamp.tar.gz"
    
    # Configuration directories to backup
    local config_dirs=(
        "/etc/nginx"
        "/etc/ssl/automotive-chatbot"
        "/etc/automotive-chatbot"
        "/etc/systemd/system/automotive-chatbot*"
        "/etc/prometheus"
        "/etc/grafana"
        "/etc/letsencrypt"
    )
    
    # Create configuration backup
    tar -czf "$backup_file" \
        --ignore-failed-read \
        --warning=no-file-changed \
        --exclude='*.log' \
        --exclude='cache' \
        --exclude='temp' \
        "${config_dirs[@]}" 2>/dev/null || true
    
    if [ -f "$backup_file" ]; then
        log "Configuration files backed up successfully"
    else
        warn "No configuration files found to backup"
        return 0
    fi
    
    # Encrypt the backup
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$backup_file.gpg" \
        "$backup_file"
    
    # Remove unencrypted file
    rm -f "$backup_file"
    
    # Upload to S3
    if upload_to_s3 "$backup_file.gpg" "config/config_backup_$timestamp.tar.gz.gpg"; then
        log "Configuration backup uploaded to S3"
    else
        warn "Failed to upload configuration backup to S3"
    fi
    
    log "Configuration backup completed: $backup_file.gpg"
}

# Backup logs
backup_logs() {
    log "Starting logs backup..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/logs/logs_backup_$timestamp.tar.gz"
    
    # Log directories to backup
    local log_dirs=(
        "/var/log/automotive-chatbot"
        "/var/log/nginx"
        "/var/log/prometheus"
        "/var/log/grafana"
    )
    
    # Create logs backup (last 7 days only)
    find "${log_dirs[@]}" -type f -mtime -7 2>/dev/null | \
        tar -czf "$backup_file" --files-from=- 2>/dev/null || true
    
    if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
        log "Logs backed up successfully"
    else
        warn "No recent logs found to backup"
        rm -f "$backup_file"
        return 0
    fi
    
    # Encrypt the backup
    gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
        --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
        --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$backup_file.gpg" \
        "$backup_file"
    
    # Remove unencrypted file
    rm -f "$backup_file"
    
    # Upload to S3
    if upload_to_s3 "$backup_file.gpg" "logs/logs_backup_$timestamp.tar.gz.gpg"; then
        log "Logs backup uploaded to S3"
    else
        warn "Failed to upload logs backup to S3"
    fi
    
    log "Logs backup completed: $backup_file.gpg"
}

# Upload file to S3
upload_to_s3() {
    local local_file="$1"
    local s3_key="$2"
    
    if [ ! -f "$local_file" ]; then
        error "Local file not found: $local_file"
    fi
    
    # Upload with server-side encryption
    if aws s3 cp "$local_file" "s3://$S3_BUCKET/$s3_key" \
        --server-side-encryption AES256 \
        --storage-class STANDARD_IA; then
        return 0
    else
        return 1
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    # Clean local backups older than retention period
    find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete
    
    # Clean empty directories
    find $BACKUP_DIR -type d -empty -delete
    
    # Clean S3 backups older than retention period
    local cutoff_date=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)
    
    aws s3api list-objects-v2 --bucket $S3_BUCKET --query "Contents[?LastModified<='$cutoff_date'].Key" --output text | \
    while read -r key; do
        if [ -n "$key" ] && [ "$key" != "None" ]; then
            aws s3 rm "s3://$S3_BUCKET/$key"
            log "Deleted old S3 backup: $key"
        fi
    done
    
    log "Old backups cleaned up"
}

# Create backup manifest
create_backup_manifest() {
    log "Creating backup manifest..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local manifest_file="$BACKUP_DIR/manifest_$timestamp.json"
    
    # Create manifest with backup information
    cat > "$manifest_file" << EOF
{
  "backup_timestamp": "$timestamp",
  "backup_date": "$(date -Iseconds)",
  "hostname": "$(hostname)",
  "backup_type": "full",
  "retention_days": $RETENTION_DAYS,
  "encryption": "AES256",
  "components": {
    "mongodb": {
      "status": "completed",
      "uri": "${MONGODB_URI%@*}@***",
      "size_mb": $(du -m $BACKUP_DIR/mongodb/*$timestamp* 2>/dev/null | awk '{print $1}' || echo 0)
    },
    "redis": {
      "status": "completed",
      "host": "$REDIS_HOST:$REDIS_PORT",
      "size_mb": $(du -m $BACKUP_DIR/redis/*$timestamp* 2>/dev/null | awk '{print $1}' || echo 0)
    },
    "application": {
      "status": "completed",
      "size_mb": $(du -m $BACKUP_DIR/application/*$timestamp* 2>/dev/null | awk '{print $1}' || echo 0)
    },
    "configuration": {
      "status": "completed",
      "size_mb": $(du -m $BACKUP_DIR/config/*$timestamp* 2>/dev/null | awk '{print $1}' || echo 0)
    },
    "logs": {
      "status": "completed",
      "size_mb": $(du -m $BACKUP_DIR/logs/*$timestamp* 2>/dev/null | awk '{print $1}' || echo 0)
    }
  },
  "total_size_mb": $(du -sm $BACKUP_DIR 2>/dev/null | awk '{print $1}' || echo 0),
  "s3_bucket": "$S3_BUCKET",
  "s3_region": "$S3_REGION"
}
EOF

    # Upload manifest to S3
    if upload_to_s3 "$manifest_file" "manifests/manifest_$timestamp.json"; then
        log "Backup manifest uploaded to S3"
    else
        warn "Failed to upload backup manifest to S3"
    fi
    
    log "Backup manifest created: $manifest_file"
}

# Restore MongoDB from backup
restore_mongodb() {
    local backup_file="$1"
    
    log "Starting MongoDB restore from: $backup_file"
    
    # Download from S3 if it's an S3 path
    if [[ $backup_file == s3://* ]]; then
        local local_file="$BACKUP_DIR/temp/$(basename $backup_file)"
        aws s3 cp "$backup_file" "$local_file"
        backup_file="$local_file"
    fi
    
    # Decrypt the backup
    local decrypted_file="${backup_file%.gpg}"
    gpg --decrypt --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$decrypted_file" "$backup_file"
    
    # Extract the backup
    local extract_dir="$BACKUP_DIR/temp/mongodb_restore"
    mkdir -p "$extract_dir"
    tar -xzf "$decrypted_file" -C "$extract_dir"
    
    # Restore to MongoDB
    if mongorestore --uri="$MONGODB_URI" --drop "$extract_dir"/*; then
        log "MongoDB restore completed successfully"
    else
        error "Failed to restore MongoDB"
    fi
    
    # Cleanup
    rm -rf "$extract_dir" "$decrypted_file"
    
    log "MongoDB restore completed"
}

# Restore Redis from backup
restore_redis() {
    local backup_file="$1"
    
    log "Starting Redis restore from: $backup_file"
    
    # Download from S3 if it's an S3 path
    if [[ $backup_file == s3://* ]]; then
        local local_file="$BACKUP_DIR/temp/$(basename $backup_file)"
        aws s3 cp "$backup_file" "$local_file"
        backup_file="$local_file"
    fi
    
    # Decrypt the backup
    local decrypted_file="${backup_file%.gpg}"
    gpg --decrypt --passphrase-file $ENCRYPTION_KEY_FILE \
        --output "$decrypted_file" "$backup_file"
    
    # Decompress
    gunzip "$decrypted_file"
    local rdb_file="${decrypted_file%.gz}"
    
    # Stop Redis service
    systemctl stop redis-server
    
    # Replace Redis dump file
    cp "$rdb_file" /var/lib/redis/dump.rdb
    chown redis:redis /var/lib/redis/dump.rdb
    
    # Start Redis service
    systemctl start redis-server
    
    # Cleanup
    rm -f "$rdb_file"
    
    log "Redis restore completed"
}

# Disaster recovery procedure
disaster_recovery() {
    local recovery_date="$1"
    
    log "Starting disaster recovery for date: $recovery_date"
    
    # List available backups
    log "Available backups for $recovery_date:"
    aws s3 ls "s3://$S3_BUCKET/" --recursive | grep "$recovery_date" || {
        error "No backups found for date: $recovery_date"
    }
    
    # Download and restore each component
    local mongodb_backup=$(aws s3 ls "s3://$S3_BUCKET/mongodb/" | grep "$recovery_date" | awk '{print $4}' | head -1)
    local redis_backup=$(aws s3 ls "s3://$S3_BUCKET/redis/" | grep "$recovery_date" | awk '{print $4}' | head -1)
    
    if [ -n "$mongodb_backup" ]; then
        restore_mongodb "s3://$S3_BUCKET/mongodb/$mongodb_backup"
    fi
    
    if [ -n "$redis_backup" ]; then
        restore_redis "s3://$S3_BUCKET/redis/$redis_backup"
    fi
    
    log "Disaster recovery completed"
}

# Health check for backup system
backup_health_check() {
    log "Performing backup system health check..."
    
    local issues=0
    
    # Check backup directory
    if [ ! -d "$BACKUP_DIR" ]; then
        warn "Backup directory does not exist: $BACKUP_DIR"
        ((issues++))
    fi
    
    # Check encryption key
    if [ ! -f "$ENCRYPTION_KEY_FILE" ]; then
        warn "Encryption key file not found: $ENCRYPTION_KEY_FILE"
        ((issues++))
    fi
    
    # Check AWS CLI configuration
    if ! aws sts get-caller-identity &>/dev/null; then
        warn "AWS CLI not configured properly"
        ((issues++))
    fi
    
    # Check S3 bucket access
    if ! aws s3 ls "s3://$S3_BUCKET" &>/dev/null; then
        warn "Cannot access S3 bucket: $S3_BUCKET"
        ((issues++))
    fi
    
    # Check MongoDB connectivity
    if ! mongosh "$MONGODB_URI" --eval "db.runCommand('ping')" &>/dev/null; then
        warn "Cannot connect to MongoDB"
        ((issues++))
    fi
    
    # Check Redis connectivity
    if ! redis-cli -h $REDIS_HOST -p $REDIS_PORT ping &>/dev/null; then
        warn "Cannot connect to Redis"
        ((issues++))
    fi
    
    if [ $issues -eq 0 ]; then
        log "Backup system health check passed"
        return 0
    else
        warn "Backup system health check found $issues issues"
        return 1
    fi
}

# Main execution function
main() {
    local action="${1:-backup}"
    
    case $action in
        "backup")
            log "Starting full backup process..."
            check_root
            install_dependencies
            setup_backup_environment
            backup_mongodb
            backup_redis
            backup_application
            backup_configuration
            backup_logs
            create_backup_manifest
            cleanup_old_backups
            log "Full backup process completed successfully"
            ;;
        "restore")
            local recovery_date="$2"
            if [ -z "$recovery_date" ]; then
                error "Recovery date required for restore operation (format: YYYYMMDD)"
            fi
            check_root
            disaster_recovery "$recovery_date"
            ;;
        "health")
            backup_health_check
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "help")
            echo "Usage: $0 [backup|restore|health|cleanup|help]"
            echo "  backup           : Perform full backup"
            echo "  restore DATE     : Restore from backup (DATE format: YYYYMMDD)"
            echo "  health           : Check backup system health"
            echo "  cleanup          : Clean up old backups"
            echo "  help             : Show this help message"
            exit 0
            ;;
        *)
            error "Unknown action: $action. Use 'help' for usage information."
            ;;
    esac
}

# Run main function with all arguments
main "$@"
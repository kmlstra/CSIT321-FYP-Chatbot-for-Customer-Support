#!/bin/bash

# Security Setup Script for Automotive Chatbot
# This script configures comprehensive security settings for the production environment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Update system packages
update_system() {
    log "Updating system packages..."
    apt-get update -y
    apt-get upgrade -y
    apt-get autoremove -y
    apt-get autoclean
}

# Install security packages
install_security_packages() {
    log "Installing security packages..."
    
    # Essential security packages
    apt-get install -y \
        ufw \
        fail2ban \
        unattended-upgrades \
        apt-listchanges \
        logwatch \
        rkhunter \
        chkrootkit \
        aide \
        auditd \
        acct \
        psad \
        clamav \
        clamav-daemon \
        lynis
    
    log "Security packages installed successfully"
}

# Configure UFW firewall
configure_ufw() {
    log "Configuring UFW firewall..."
    
    # Reset UFW to defaults
    ufw --force reset
    
    # Set default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH (with rate limiting)
    ufw limit ssh
    ufw allow 22
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow application ports
    ufw allow 3000/tcp comment 'Frontend'
    ufw allow 8000/tcp comment 'Backend API'
    ufw allow 5005/tcp comment 'RASA Core'
    ufw allow 5055/tcp comment 'RASA Actions'
    
    # Allow monitoring ports (restricted to local network)
    ufw allow from 10.0.0.0/8 to any port 9090 comment 'Prometheus'
    ufw allow from 10.0.0.0/8 to any port 3001 comment 'Grafana'
    ufw allow from 10.0.0.0/8 to any port 9100 comment 'Node Exporter'
    
    # Enable UFW
    ufw --force enable
    
    log "UFW firewall configured and enabled"
}

# Configure Fail2Ban
configure_fail2ban() {
    log "Configuring Fail2Ban..."
    
    # Create custom jail configuration
    cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban time in seconds (1 hour)
bantime = 3600

# Find time window (10 minutes)
findtime = 600

# Maximum number of retries
maxretry = 5

# Ignore local IPs
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16

# Email notifications
destemail = admin@yourdomain.com
sender = fail2ban@yourdomain.com
mta = sendmail
action = %(action_mwl)s

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log
action = %(action_mwl)s
bantime = 604800
findtime = 86400
maxretry = 5
EOF

    # Create custom filters
    cat > /etc/fail2ban/filter.d/nginx-botsearch.conf << 'EOF'
[Definition]
failregex = ^<HOST> -.*GET.*(\.|%2e)(\.|%2e)(\.|%2e)(\.|%2e).*HTTP.*$
            ^<HOST> -.*GET.*(/\.|\.\./|\.\.\\).*HTTP.*$
            ^<HOST> -.*GET.*(\.(php|asp|exe|pl|cgi|scr)).*HTTP.*$
            ^<HOST> -.*GET.*(select%20|union%20|insert%20|cast%20).*HTTP.*$
ignoreregex =
EOF

    # Restart and enable Fail2Ban
    systemctl restart fail2ban
    systemctl enable fail2ban
    
    log "Fail2Ban configured and started"
}

# Configure automatic security updates
configure_auto_updates() {
    log "Configuring automatic security updates..."
    
    # Configure unattended-upgrades
    cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

Unattended-Upgrade::Package-Blacklist {
    // Add packages to blacklist here if needed
};

Unattended-Upgrade::DevRelease "false";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";
Unattended-Upgrade::SyslogEnable "true";
Unattended-Upgrade::SyslogFacility "daemon";
Unattended-Upgrade::Verbose "false";
Unattended-Upgrade::Debug "false";
Unattended-Upgrade::Mail "admin@yourdomain.com";
Unattended-Upgrade::MailOnlyOnError "true";
EOF

    # Enable automatic updates
    cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
EOF

    log "Automatic security updates configured"
}

# Harden SSH configuration
harden_ssh() {
    log "Hardening SSH configuration..."
    
    # Backup original SSH config
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Create hardened SSH configuration
    cat > /etc/ssh/sshd_config << 'EOF'
# Hardened SSH Configuration for Automotive Chatbot

# Protocol and Port
Protocol 2
Port 22

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes

# Connection settings
ClientAliveInterval 300
ClientAliveCountMax 2
MaxAuthTries 3
MaxSessions 2
MaxStartups 2
LoginGraceTime 30

# Restrict users and groups
AllowUsers ubuntu admin
# AllowGroups ssh-users

# Disable dangerous features
PermitUserEnvironment no
PermitTunnel no
GatewayPorts no
X11Forwarding no
PermitTTY yes
PrintMotd yes
PrintLastLog yes
TCPKeepAlive yes
Compression no

# Logging
SyslogFacility AUTHPRIV
LogLevel VERBOSE

# Cryptography
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512
KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,diffie-hellman-group14-sha256

# Host keys
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Subsystem
Subsystem sftp /usr/lib/openssh/sftp-server -f AUTHPRIV -l INFO
EOF

    # Test SSH configuration
    sshd -t || error "SSH configuration test failed"
    
    # Restart SSH service
    systemctl restart sshd
    
    log "SSH configuration hardened"
}

# Configure system auditing
configure_auditing() {
    log "Configuring system auditing..."
    
    # Configure auditd rules
    cat > /etc/audit/rules.d/audit.rules << 'EOF'
# Audit Rules for Automotive Chatbot

# Remove any existing rules
-D

# Buffer Size
-b 8192

# Failure Mode
-f 1

# Audit the audit logs themselves
-w /var/log/audit/ -p wa -k auditlog

# Audit the configuration files
-w /etc/audit/ -p wa -k auditconfig
-w /etc/libaudit.conf -p wa -k auditconfig
-w /etc/audisp/ -p wa -k audispconfig

# Monitor for changes to system configuration files
-w /etc/passwd -p wa -k passwd_changes
-w /etc/group -p wa -k group_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/sudoers -p wa -k sudoers_changes
-w /etc/ssh/sshd_config -p wa -k ssh_config

# Monitor authentication events
-w /var/log/auth.log -p wa -k auth_log
-w /var/log/faillog -p wa -k faillog
-w /var/log/lastlog -p wa -k lastlog

# Monitor network configuration changes
-w /etc/network/ -p wa -k network_config
-w /etc/hosts -p wa -k hosts_config
-w /etc/hostname -p wa -k hostname_config

# Monitor critical system calls
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time_change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time_change
-a always,exit -F arch=b64 -S clock_settime -k time_change
-a always,exit -F arch=b32 -S clock_settime -k time_change

# Monitor file access
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod

# Monitor application directories
-w /opt/automotive-chatbot/ -p wa -k app_changes
-w /var/log/automotive-chatbot/ -p wa -k app_logs

# Make the configuration immutable
-e 2
EOF

    # Restart auditd
    systemctl restart auditd
    systemctl enable auditd
    
    log "System auditing configured"
}

# Configure intrusion detection
configure_intrusion_detection() {
    log "Configuring intrusion detection..."
    
    # Configure AIDE (Advanced Intrusion Detection Environment)
    aideinit
    
    # Create AIDE check script
    cat > /usr/local/bin/aide-check.sh << 'EOF'
#!/bin/bash
# AIDE integrity check script

AIDE_LOG="/var/log/aide/aide.log"
AIDE_REPORT="/var/log/aide/aide-report.txt"

# Create log directory
mkdir -p /var/log/aide

# Run AIDE check
echo "[$(date)] Starting AIDE integrity check" >> $AIDE_LOG
aide --check > $AIDE_REPORT 2>&1

# Check for changes
if [ $? -eq 0 ]; then
    echo "[$(date)] AIDE check completed - No changes detected" >> $AIDE_LOG
else
    echo "[$(date)] AIDE check completed - CHANGES DETECTED!" >> $AIDE_LOG
    # Send alert email
    mail -s "AIDE Alert: File system changes detected" admin@yourdomain.com < $AIDE_REPORT
fi
EOF

    chmod +x /usr/local/bin/aide-check.sh
    
    # Add AIDE check to crontab (daily at 3 AM)
    echo "0 3 * * * root /usr/local/bin/aide-check.sh" >> /etc/crontab
    
    # Configure rkhunter
    rkhunter --update
    rkhunter --propupd
    
    # Create rkhunter check script
    cat > /usr/local/bin/rkhunter-check.sh << 'EOF'
#!/bin/bash
# Rootkit Hunter check script

RKH_LOG="/var/log/rkhunter/rkhunter.log"
RKH_REPORT="/var/log/rkhunter/rkhunter-report.txt"

# Create log directory
mkdir -p /var/log/rkhunter

# Run rkhunter check
echo "[$(date)] Starting rkhunter scan" >> $RKH_LOG
rkhunter --check --skip-keypress --report-warnings-only > $RKH_REPORT 2>&1

# Check for warnings
if [ -s $RKH_REPORT ]; then
    echo "[$(date)] rkhunter scan completed - WARNINGS FOUND!" >> $RKH_LOG
    # Send alert email
    mail -s "Rkhunter Alert: Security warnings detected" admin@yourdomain.com < $RKH_REPORT
else
    echo "[$(date)] rkhunter scan completed - No warnings" >> $RKH_LOG
fi
EOF

    chmod +x /usr/local/bin/rkhunter-check.sh
    
    # Add rkhunter check to crontab (daily at 4 AM)
    echo "0 4 * * * root /usr/local/bin/rkhunter-check.sh" >> /etc/crontab
    
    log "Intrusion detection configured"
}

# Configure system hardening
configure_system_hardening() {
    log "Applying system hardening..."
    
    # Kernel parameter hardening
    cat > /etc/sysctl.d/99-security.conf << 'EOF'
# Network security
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Memory protection
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.kexec_load_disabled = 1

# File system protection
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.suid_dumpable = 0
EOF

    # Apply sysctl settings
    sysctl -p /etc/sysctl.d/99-security.conf
    
    # Disable unused network protocols
    cat > /etc/modprobe.d/blacklist-rare-network.conf << 'EOF'
# Disable rare network protocols
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
EOF

    # Set file permissions
    chmod 700 /root
    chmod 600 /etc/ssh/ssh_host_*_key
    chmod 644 /etc/ssh/ssh_host_*_key.pub
    
    # Remove unnecessary packages
    apt-get remove --purge -y \
        telnet \
        rsh-client \
        rsh-redone-client \
        talk \
        ntalk \
        finger \
        netcat \
        nc \
        2>/dev/null || true
    
    log "System hardening applied"
}

# Configure log monitoring
configure_log_monitoring() {
    log "Configuring log monitoring..."
    
    # Configure logwatch
    cat > /etc/logwatch/conf/logwatch.conf << 'EOF'
LogDir = /var/log
TmpDir = /var/cache/logwatch
Output = mail
Format = html
Encode = none
MailTo = admin@yourdomain.com
MailFrom = logwatch@yourdomain.com
Subject = Logwatch Report
Range = yesterday
Detail = Med
Service = All
mailer = "/usr/sbin/sendmail -t"
EOF

    # Add logwatch to daily cron
    echo "0 6 * * * root /usr/sbin/logwatch --output mail" >> /etc/crontab
    
    # Configure rsyslog for centralized logging
    cat > /etc/rsyslog.d/50-automotive-chatbot.conf << 'EOF'
# Automotive Chatbot logging configuration

# Application logs
:programname, isequal, "automotive-chatbot" /var/log/automotive-chatbot/app.log
:programname, isequal, "rasa" /var/log/automotive-chatbot/rasa.log
:programname, isequal, "nginx" /var/log/automotive-chatbot/nginx.log

# Security logs
auth,authpriv.* /var/log/automotive-chatbot/auth.log

# Stop processing after logging
& stop
EOF

    # Create log directories
    mkdir -p /var/log/automotive-chatbot
    chown syslog:adm /var/log/automotive-chatbot
    
    # Restart rsyslog
    systemctl restart rsyslog
    
    log "Log monitoring configured"
}

# Configure backup security
configure_backup_security() {
    log "Configuring backup security..."
    
    # Create backup script with encryption
    cat > /usr/local/bin/secure-backup.sh << 'EOF'
#!/bin/bash
# Secure backup script with encryption

BACKUP_DIR="/opt/backups"
ENCRYPTION_KEY="/etc/backup-encryption.key"
S3_BUCKET="automotive-chatbot-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Generate encryption key if it doesn't exist
if [ ! -f $ENCRYPTION_KEY ]; then
    openssl rand -base64 32 > $ENCRYPTION_KEY
    chmod 600 $ENCRYPTION_KEY
fi

# Backup application data
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/automotive-chatbot

# Backup configuration
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz /etc/automotive-chatbot

# Encrypt backups
for file in $BACKUP_DIR/*_$DATE.tar.gz; do
    openssl enc -aes-256-cbc -salt -in "$file" -out "$file.enc" -pass file:$ENCRYPTION_KEY
    rm "$file"
done

# Upload to S3 (if configured)
if command -v aws &> /dev/null; then
    aws s3 sync $BACKUP_DIR s3://$S3_BUCKET/$(hostname)/
fi

# Clean old backups (keep 7 days)
find $BACKUP_DIR -name "*.enc" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

    chmod +x /usr/local/bin/secure-backup.sh
    
    # Add backup to crontab (daily at 2 AM)
    echo "0 2 * * * root /usr/local/bin/secure-backup.sh" >> /etc/crontab
    
    log "Backup security configured"
}

# Main execution
main() {
    log "Starting security setup for Automotive Chatbot..."
    
    check_root
    update_system
    install_security_packages
    configure_ufw
    configure_fail2ban
    configure_auto_updates
    harden_ssh
    configure_auditing
    configure_intrusion_detection
    configure_system_hardening
    configure_log_monitoring
    configure_backup_security
    
    log "Security setup completed successfully!"
    log "Please review the configuration and test all services"
    log "Remember to:"
    log "  1. Update admin email addresses in configuration files"
    log "  2. Configure AWS CLI for S3 backups"
    log "  3. Test SSH access with key-based authentication"
    log "  4. Review firewall rules and adjust as needed"
    log "  5. Set up monitoring alerts"
    
    warn "System will require a reboot to apply all kernel parameter changes"
}

# Run main function
main "$@"
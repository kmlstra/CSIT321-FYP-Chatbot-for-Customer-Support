#!/bin/bash

# Deployment Validation and Testing Script for Automotive Chatbot
# This script validates the entire system deployment and performs comprehensive testing

set -euo pipefail

# Configuration
APP_DOMAIN="${APP_DOMAIN:-automotive-chatbot.com}"
MONITORING_DOMAIN="${MONITORING_DOMAIN:-monitoring.automotive-chatbot.com}"
API_BASE_URL="https://$APP_DOMAIN/api"
FRONTEND_URL="https://$APP_DOMAIN"
RASA_CORE_URL="http://localhost:5005"
RASA_ACTIONS_URL="http://localhost:5055"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3001"
ALERTMANAGER_URL="http://localhost:9093"
LOG_FILE="/var/log/deployment-validation.log"
TEST_RESULTS_DIR="/tmp/deployment-tests"
TIMEOUT=30

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

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

test_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}" | tee -a $LOG_FILE
}

test_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"
    
    ((TOTAL_TESTS++))
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓ $test_name: $message${NC}" | tee -a $LOG_FILE
        ((PASSED_TESTS++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}✗ $test_name: $message${NC}" | tee -a $LOG_FILE
        ((FAILED_TESTS++))
    elif [ "$result" = "SKIP" ]; then
        echo -e "${YELLOW}⚠ $test_name: $message${NC}" | tee -a $LOG_FILE
        ((SKIPPED_TESTS++))
    fi
}

# Setup test environment
setup_test_environment() {
    log "Setting up test environment..."
    
    # Create test results directory
    mkdir -p $TEST_RESULTS_DIR
    
    # Install test dependencies
    if ! command -v curl &> /dev/null; then
        apt-get update && apt-get install -y curl
    fi
    
    if ! command -v jq &> /dev/null; then
        apt-get install -y jq
    fi
    
    if ! command -v nc &> /dev/null; then
        apt-get install -y netcat
    fi
    
    log "Test environment setup completed"
}

# Test system services
test_system_services() {
    test_header "System Services Tests"
    
    local services=(
        "nginx"
        "prometheus"
        "node_exporter"
        "alertmanager"
        "grafana-server"
        "docker"
    )
    
    for service in "${services[@]}"; do
        if systemctl is-active --quiet $service; then
            test_result "Service $service" "PASS" "Service is running"
        else
            test_result "Service $service" "FAIL" "Service is not running"
        fi
    done
}

# Test Docker containers
test_docker_containers() {
    test_header "Docker Containers Tests"
    
    if ! command -v docker &> /dev/null; then
        test_result "Docker" "SKIP" "Docker not installed"
        return
    fi
    
    local containers=(
        "automotive-chatbot-frontend"
        "automotive-chatbot-backend"
        "rasa-core"
        "rasa-actions"
        "redis"
    )
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}" | grep -q $container; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' $container 2>/dev/null || echo "unknown")
            if [ "$status" = "healthy" ] || [ "$status" = "unknown" ]; then
                test_result "Container $container" "PASS" "Container is running and healthy"
            else
                test_result "Container $container" "FAIL" "Container is unhealthy: $status"
            fi
        else
            test_result "Container $container" "FAIL" "Container is not running"
        fi
    done
}

# Test network connectivity
test_network_connectivity() {
    test_header "Network Connectivity Tests"
    
    local ports=(
        "80:HTTP"
        "443:HTTPS"
        "3000:Frontend"
        "8000:Backend API"
        "5005:RASA Core"
        "5055:RASA Actions"
        "6379:Redis"
        "9090:Prometheus"
        "9093:AlertManager"
        "3001:Grafana"
        "9100:Node Exporter"
    )
    
    for port_info in "${ports[@]}"; do
        local port=$(echo $port_info | cut -d: -f1)
        local service=$(echo $port_info | cut -d: -f2)
        
        if nc -z localhost $port; then
            test_result "Port $port ($service)" "PASS" "Port is open and accessible"
        else
            test_result "Port $port ($service)" "FAIL" "Port is not accessible"
        fi
    done
}

# Test SSL certificates
test_ssl_certificates() {
    test_header "SSL Certificate Tests"
    
    local domains=(
        "$APP_DOMAIN"
        "$MONITORING_DOMAIN"
    )
    
    for domain in "${domains[@]}"; do
        if [ -f "/etc/letsencrypt/live/$domain/fullchain.pem" ]; then
            local expiry_date=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$domain/fullchain.pem" | cut -d= -f2)
            local expiry_timestamp=$(date -d "$expiry_date" +%s)
            local current_timestamp=$(date +%s)
            local days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
            
            if [ $days_until_expiry -gt 7 ]; then
                test_result "SSL Certificate $domain" "PASS" "Certificate valid for $days_until_expiry days"
            elif [ $days_until_expiry -gt 0 ]; then
                test_result "SSL Certificate $domain" "FAIL" "Certificate expires in $days_until_expiry days"
            else
                test_result "SSL Certificate $domain" "FAIL" "Certificate has expired"
            fi
        else
            test_result "SSL Certificate $domain" "FAIL" "Certificate file not found"
        fi
    done
}

# Test API endpoints
test_api_endpoints() {
    test_header "API Endpoints Tests"
    
    local endpoints=(
        "$API_BASE_URL/health:Health Check"
        "$API_BASE_URL/health/detailed:Detailed Health"
        "$API_BASE_URL/health/performance:Performance Health"
        "$API_BASE_URL/health/database:Database Health"
        "$API_BASE_URL/metrics:Metrics"
        "$API_BASE_URL/docs:API Documentation"
    )
    
    for endpoint_info in "${endpoints[@]}"; do
        local endpoint=$(echo $endpoint_info | cut -d: -f1)
        local name=$(echo $endpoint_info | cut -d: -f2)
        
        local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$endpoint" || echo "000")
        
        if [ "$response" = "200" ]; then
            test_result "API $name" "PASS" "Endpoint returned HTTP 200"
        elif [ "$response" = "000" ]; then
            test_result "API $name" "FAIL" "Connection timeout or failed"
        else
            test_result "API $name" "FAIL" "Endpoint returned HTTP $response"
        fi
    done
}

# Test RASA services
test_rasa_services() {
    test_header "RASA Services Tests"
    
    # Test RASA Core
    local rasa_core_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$RASA_CORE_URL/version" || echo "000")
    
    if [ "$rasa_core_response" = "200" ]; then
        test_result "RASA Core" "PASS" "RASA Core is responding"
        
        # Test RASA Core conversation
        local conversation_response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -d '{"sender": "test_user", "message": "hello"}' \
            --connect-timeout $TIMEOUT \
            "$RASA_CORE_URL/webhooks/rest/webhook" || echo "error")
        
        if [ "$conversation_response" != "error" ] && echo "$conversation_response" | jq -e '. | length > 0' &>/dev/null; then
            test_result "RASA Core Conversation" "PASS" "RASA Core can process messages"
        else
            test_result "RASA Core Conversation" "FAIL" "RASA Core cannot process messages"
        fi
    else
        test_result "RASA Core" "FAIL" "RASA Core is not responding"
        test_result "RASA Core Conversation" "SKIP" "RASA Core not available"
    fi
    
    # Test RASA Actions
    local rasa_actions_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$RASA_ACTIONS_URL/health" || echo "000")
    
    if [ "$rasa_actions_response" = "200" ]; then
        test_result "RASA Actions" "PASS" "RASA Actions server is responding"
    else
        test_result "RASA Actions" "FAIL" "RASA Actions server is not responding"
    fi
}

# Test frontend application
test_frontend_application() {
    test_header "Frontend Application Tests"
    
    # Test frontend accessibility
    local frontend_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$FRONTEND_URL" || echo "000")
    
    if [ "$frontend_response" = "200" ]; then
        test_result "Frontend Accessibility" "PASS" "Frontend is accessible"
        
        # Test if frontend contains expected content
        local frontend_content=$(curl -s --connect-timeout $TIMEOUT "$FRONTEND_URL" || echo "")
        
        if echo "$frontend_content" | grep -q "Automotive Chatbot"; then
            test_result "Frontend Content" "PASS" "Frontend contains expected content"
        else
            test_result "Frontend Content" "FAIL" "Frontend does not contain expected content"
        fi
        
        # Test static assets
        local assets_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$FRONTEND_URL/assets/" || echo "000")
        
        if [ "$assets_response" = "200" ] || [ "$assets_response" = "403" ]; then
            test_result "Frontend Assets" "PASS" "Static assets are accessible"
        else
            test_result "Frontend Assets" "FAIL" "Static assets are not accessible"
        fi
    else
        test_result "Frontend Accessibility" "FAIL" "Frontend is not accessible"
        test_result "Frontend Content" "SKIP" "Frontend not accessible"
        test_result "Frontend Assets" "SKIP" "Frontend not accessible"
    fi
}

# Test monitoring services
test_monitoring_services() {
    test_header "Monitoring Services Tests"
    
    # Test Prometheus
    local prometheus_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$PROMETHEUS_URL/-/healthy" || echo "000")
    
    if [ "$prometheus_response" = "200" ]; then
        test_result "Prometheus" "PASS" "Prometheus is healthy"
        
        # Test Prometheus targets
        local targets_response=$(curl -s --connect-timeout $TIMEOUT "$PROMETHEUS_URL/api/v1/targets" || echo "error")
        
        if [ "$targets_response" != "error" ] && echo "$targets_response" | jq -e '.data.activeTargets | length > 0' &>/dev/null; then
            test_result "Prometheus Targets" "PASS" "Prometheus has active targets"
        else
            test_result "Prometheus Targets" "FAIL" "Prometheus has no active targets"
        fi
    else
        test_result "Prometheus" "FAIL" "Prometheus is not healthy"
        test_result "Prometheus Targets" "SKIP" "Prometheus not available"
    fi
    
    # Test Grafana
    local grafana_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$GRAFANA_URL/api/health" || echo "000")
    
    if [ "$grafana_response" = "200" ]; then
        test_result "Grafana" "PASS" "Grafana is healthy"
    else
        test_result "Grafana" "FAIL" "Grafana is not healthy"
    fi
    
    # Test AlertManager
    local alertmanager_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$ALERTMANAGER_URL/-/healthy" || echo "000")
    
    if [ "$alertmanager_response" = "200" ]; then
        test_result "AlertManager" "PASS" "AlertManager is healthy"
    else
        test_result "AlertManager" "FAIL" "AlertManager is not healthy"
    fi
}

# Test database connectivity
test_database_connectivity() {
    test_header "Database Connectivity Tests"
    
    # Test MongoDB Atlas connectivity (if configured)
    if [ -n "${MONGODB_URI:-}" ]; then
        if mongosh "$MONGODB_URI" --eval "db.runCommand('ping')" &>/dev/null; then
            test_result "MongoDB Atlas" "PASS" "MongoDB Atlas is accessible"
            
            # Test database collections
            local collections=$(mongosh "$MONGODB_URI" --eval "db.getCollectionNames()" --quiet 2>/dev/null || echo "error")
            
            if [ "$collections" != "error" ] && [ -n "$collections" ]; then
                test_result "MongoDB Collections" "PASS" "Database collections are accessible"
            else
                test_result "MongoDB Collections" "FAIL" "Cannot access database collections"
            fi
        else
            test_result "MongoDB Atlas" "FAIL" "MongoDB Atlas is not accessible"
            test_result "MongoDB Collections" "SKIP" "MongoDB not accessible"
        fi
    else
        test_result "MongoDB Atlas" "SKIP" "MongoDB URI not configured"
        test_result "MongoDB Collections" "SKIP" "MongoDB not configured"
    fi
    
    # Test Redis connectivity
    if redis-cli ping &>/dev/null; then
        test_result "Redis" "PASS" "Redis is accessible"
        
        # Test Redis operations
        if redis-cli set test_key test_value &>/dev/null && redis-cli get test_key &>/dev/null; then
            test_result "Redis Operations" "PASS" "Redis operations work correctly"
            redis-cli del test_key &>/dev/null
        else
            test_result "Redis Operations" "FAIL" "Redis operations failed"
        fi
    else
        test_result "Redis" "FAIL" "Redis is not accessible"
        test_result "Redis Operations" "SKIP" "Redis not accessible"
    fi
}

# Test security configurations
test_security_configurations() {
    test_header "Security Configuration Tests"
    
    # Test firewall status
    if ufw status | grep -q "Status: active"; then
        test_result "UFW Firewall" "PASS" "UFW firewall is active"
    else
        test_result "UFW Firewall" "FAIL" "UFW firewall is not active"
    fi
    
    # Test Fail2Ban status
    if systemctl is-active --quiet fail2ban; then
        test_result "Fail2Ban" "PASS" "Fail2Ban is running"
    else
        test_result "Fail2Ban" "FAIL" "Fail2Ban is not running"
    fi
    
    # Test SSH configuration
    if grep -q "PermitRootLogin no" /etc/ssh/sshd_config; then
        test_result "SSH Root Login" "PASS" "Root login is disabled"
    else
        test_result "SSH Root Login" "FAIL" "Root login is not disabled"
    fi
    
    # Test file permissions
    local sensitive_files=(
        "/etc/ssl/automotive-chatbot"
        "/etc/automotive-chatbot"
        "/etc/prometheus"
        "/etc/grafana"
    )
    
    local permission_issues=0
    for file in "${sensitive_files[@]}"; do
        if [ -e "$file" ]; then
            local perms=$(stat -c "%a" "$file")
            if [ "$perms" -le "750" ]; then
                continue
            else
                ((permission_issues++))
            fi
        fi
    done
    
    if [ $permission_issues -eq 0 ]; then
        test_result "File Permissions" "PASS" "Sensitive files have appropriate permissions"
    else
        test_result "File Permissions" "FAIL" "$permission_issues files have inappropriate permissions"
    fi
}

# Test backup system
test_backup_system() {
    test_header "Backup System Tests"
    
    # Test backup directories
    if [ -d "/var/backups/automotive-chatbot" ]; then
        test_result "Backup Directory" "PASS" "Backup directory exists"
    else
        test_result "Backup Directory" "FAIL" "Backup directory does not exist"
    fi
    
    # Test encryption key
    if [ -f "/etc/automotive-chatbot/backup.key" ]; then
        test_result "Backup Encryption Key" "PASS" "Backup encryption key exists"
    else
        test_result "Backup Encryption Key" "FAIL" "Backup encryption key does not exist"
    fi
    
    # Test AWS CLI configuration
    if aws sts get-caller-identity &>/dev/null; then
        test_result "AWS CLI Configuration" "PASS" "AWS CLI is configured"
    else
        test_result "AWS CLI Configuration" "FAIL" "AWS CLI is not configured"
    fi
    
    # Test backup script
    if [ -f "/opt/automotive-chatbot/deploy/backup_recovery.sh" ] && [ -x "/opt/automotive-chatbot/deploy/backup_recovery.sh" ]; then
        test_result "Backup Script" "PASS" "Backup script exists and is executable"
    else
        test_result "Backup Script" "FAIL" "Backup script is missing or not executable"
    fi
}

# Test performance metrics
test_performance_metrics() {
    test_header "Performance Metrics Tests"
    
    # Test API response time
    local start_time=$(date +%s%N)
    local api_response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $TIMEOUT "$API_BASE_URL/health" || echo "000")
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    if [ "$api_response" = "200" ] && [ $response_time -lt 2000 ]; then
        test_result "API Response Time" "PASS" "API responds in ${response_time}ms"
    elif [ "$api_response" = "200" ]; then
        test_result "API Response Time" "FAIL" "API response time too slow: ${response_time}ms"
    else
        test_result "API Response Time" "FAIL" "API not responding"
    fi
    
    # Test system resources
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if (( $(echo "$cpu_usage < 80" | bc -l) )); then
        test_result "CPU Usage" "PASS" "CPU usage is ${cpu_usage}%"
    else
        test_result "CPU Usage" "FAIL" "High CPU usage: ${cpu_usage}%"
    fi
    
    if (( $(echo "$memory_usage < 85" | bc -l) )); then
        test_result "Memory Usage" "PASS" "Memory usage is ${memory_usage}%"
    else
        test_result "Memory Usage" "FAIL" "High memory usage: ${memory_usage}%"
    fi
    
    if [ $disk_usage -lt 90 ]; then
        test_result "Disk Usage" "PASS" "Disk usage is ${disk_usage}%"
    else
        test_result "Disk Usage" "FAIL" "High disk usage: ${disk_usage}%"
    fi
}

# Generate test report
generate_test_report() {
    local report_file="$TEST_RESULTS_DIR/deployment_validation_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "test_run": {
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "domain": "$APP_DOMAIN",
    "total_tests": $TOTAL_TESTS,
    "passed_tests": $PASSED_TESTS,
    "failed_tests": $FAILED_TESTS,
    "skipped_tests": $SKIPPED_TESTS,
    "success_rate": $(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)
  },
  "system_info": {
    "os": "$(lsb_release -d | cut -f2)",
    "kernel": "$(uname -r)",
    "uptime": "$(uptime -p)",
    "load_average": "$(uptime | awk -F'load average:' '{print $2}')"
  },
  "deployment_status": "$([ $FAILED_TESTS -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')"
}
EOF
    
    log "Test report generated: $report_file"
}

# Print test summary
print_test_summary() {
    echo -e "\n${CYAN}=== DEPLOYMENT VALIDATION SUMMARY ===${NC}"
    echo -e "${BLUE}Total Tests:${NC} $TOTAL_TESTS"
    echo -e "${GREEN}Passed:${NC} $PASSED_TESTS"
    echo -e "${RED}Failed:${NC} $FAILED_TESTS"
    echo -e "${YELLOW}Skipped:${NC} $SKIPPED_TESTS"
    
    local success_rate=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc -l)
    echo -e "${PURPLE}Success Rate:${NC} ${success_rate}%"
    
    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "\n${GREEN}🎉 DEPLOYMENT VALIDATION SUCCESSFUL! 🎉${NC}"
        echo -e "${GREEN}All critical systems are operational and ready for production.${NC}"
    else
        echo -e "\n${RED}❌ DEPLOYMENT VALIDATION FAILED! ❌${NC}"
        echo -e "${RED}$FAILED_TESTS test(s) failed. Please review the issues above.${NC}"
    fi
    
    echo -e "\n${BLUE}Detailed logs available at: $LOG_FILE${NC}"
}

# Main execution function
main() {
    local test_type="${1:-full}"
    
    log "Starting deployment validation..."
    setup_test_environment
    
    case $test_type in
        "full")
            test_system_services
            test_docker_containers
            test_network_connectivity
            test_ssl_certificates
            test_api_endpoints
            test_rasa_services
            test_frontend_application
            test_monitoring_services
            test_database_connectivity
            test_security_configurations
            test_backup_system
            test_performance_metrics
            ;;
        "quick")
            test_system_services
            test_network_connectivity
            test_api_endpoints
            test_rasa_services
            ;;
        "security")
            test_ssl_certificates
            test_security_configurations
            ;;
        "performance")
            test_performance_metrics
            test_monitoring_services
            ;;
        "help")
            echo "Usage: $0 [full|quick|security|performance|help]"
            echo "  full        : Run all validation tests (default)"
            echo "  quick       : Run essential tests only"
            echo "  security    : Run security-focused tests"
            echo "  performance : Run performance and monitoring tests"
            echo "  help        : Show this help message"
            exit 0
            ;;
        *)
            error "Unknown test type: $test_type. Use 'help' for usage information."
            ;;
    esac
    
    generate_test_report
    print_test_summary
    
    # Exit with appropriate code
    if [ $FAILED_TESTS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function with all arguments
main "$@"
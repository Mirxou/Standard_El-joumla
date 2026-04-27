#!/bin/bash

# Unified Commerce ERP Health Check Script
# Version: 1.0.0
# Description: Comprehensive health checks for production environment

set -e

# Configuration
DOCKER_COMPOSE_FILE="docker-compose.production.yml"
HEALTH_CHECK_TIMEOUT=30
LOG_FILE="./logs/health_check_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check Docker services
check_docker_services() {
    log "Checking Docker services..."

    # Get service status
    SERVICES=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --services)
    EXIT_CODE=0

    for service in $SERVICES; do
        STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service" | grep "$service" | awk '{print $4}')

        if [[ "$STATUS" == "Up" ]]; then
            success "Service $service is running"
        else
            error "Service $service is not running (Status: $STATUS)"
            EXIT_CODE=1
        fi
    done

    return $EXIT_CODE
}

# Check web service health
check_web_health() {
    log "Checking web service health..."

    if curl -f --max-time $HEALTH_CHECK_TIMEOUT http://localhost/health > /dev/null 2>&1; then
        success "Web service health check passed"
        return 0
    else
        error "Web service health check failed"
        return 1
    fi
}

# Check API service health
check_api_health() {
    log "Checking API service health..."

    if curl -f --max-time $HEALTH_CHECK_TIMEOUT http://localhost:8000/health > /dev/null 2>&1; then
        success "API service health check passed"
        return 0
    else
        error "API service health check failed"
        return 1
    fi
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."

    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_isready -U postgres -h localhost > /dev/null 2>&1; then
        success "Database is accessible"
        return 0
    else
        error "Database is not accessible"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    log "Checking Redis connectivity..."

    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        success "Redis is accessible"
        return 0
    else
        error "Redis is not accessible"
        return 1
    fi
}

# Check AI service health
check_ai_service() {
    log "Checking AI service health..."

    if curl -f --max-time $HEALTH_CHECK_TIMEOUT http://localhost:8002/health > /dev/null 2>&1; then
        success "AI service health check passed"
        return 0
    else
        warning "AI service health check failed (may be expected if AI features are disabled)"
        return 0  # Don't fail the overall check for AI service
    fi
}

# Check disk space
check_disk_space() {
    log "Checking disk space..."

    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$DISK_USAGE" -lt 90 ]; then
        success "Disk space usage: ${DISK_USAGE}%"
        return 0
    else
        error "Disk space usage is critically high: ${DISK_USAGE}%"
        return 1
    fi
}

# Check memory usage
check_memory() {
    log "Checking memory usage..."

    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')

    if [ "$MEM_USAGE" -lt 90 ]; then
        success "Memory usage: ${MEM_USAGE}%"
        return 0
    else
        error "Memory usage is critically high: ${MEM_USAGE}%"
        return 1
    fi
}

# Check CPU usage
check_cpu() {
    log "Checking CPU usage..."

    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')

    if (( $(echo "$CPU_USAGE < 90" | bc -l) )); then
        success "CPU usage: ${CPU_USAGE}%"
        return 0
    else
        error "CPU usage is critically high: ${CPU_USAGE}%"
        return 1
    fi
}

# Check SSL certificates
check_ssl_certificates() {
    log "Checking SSL certificates..."

    if [ -f "ssl/certs/unifiedcommerce2030.com.crt" ]; then
        # Check if certificate expires within 30 days
        EXPIRY_DATE=$(openssl x509 -in ssl/certs/unifiedcommerce2030.com.crt -enddate -noout | cut -d= -f2)
        EXPIRY_SECONDS=$(date -d "$EXPIRY_DATE" +%s)
        CURRENT_SECONDS=$(date +%s)
        DAYS_LEFT=$(( ($EXPIRY_SECONDS - $CURRENT_SECONDS) / 86400 ))

        if [ "$DAYS_LEFT" -gt 30 ]; then
            success "SSL certificate expires in $DAYS_LEFT days"
            return 0
        else
            warning "SSL certificate expires soon: $DAYS_LEFT days"
            return 0
        fi
    else
        warning "SSL certificate not found"
        return 0
    fi
}

# Check application logs for errors
check_application_logs() {
    log "Checking application logs for errors..."

    # Check for critical errors in last hour
    ERROR_COUNT=$(docker-compose -f "$DOCKER_COMPOSE_FILE" logs --since 1h | grep -i error | wc -l)

    if [ "$ERROR_COUNT" -eq 0 ]; then
        success "No critical errors found in logs"
        return 0
    else
        warning "Found $ERROR_COUNT error(s) in logs (last hour)"
        return 0  # Don't fail for log errors
    fi
}

# Generate health report
generate_health_report() {
    REPORT_FILE="./logs/health_report_$(date +%Y%m%d_%H%M%S).txt"

    echo "Unified Commerce ERP Health Check Report" > "$REPORT_FILE"
    echo "Generated: $(date)" >> "$REPORT_FILE"
    echo "========================================" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # System information
    echo "System Information:" >> "$REPORT_FILE"
    echo "- Hostname: $(hostname)" >> "$REPORT_FILE"
    echo "- Uptime: $(uptime -p)" >> "$REPORT_FILE"
    echo "- Load Average: $(uptime | awk -F'load average:' '{ print $2 }')" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Docker services status
    echo "Docker Services:" >> "$REPORT_FILE"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    # Resource usage
    echo "Resource Usage:" >> "$REPORT_FILE"
    echo "- Disk: $(df -h / | tail -1)" >> "$REPORT_FILE"
    echo "- Memory: $(free -h | grep Mem)" >> "$REPORT_FILE"
    echo "- CPU: $(top -bn1 | grep "Cpu(s)")" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    success "Health report generated: $REPORT_FILE"
}

# Main health check function
main() {
    log "Starting comprehensive health check"

    OVERALL_STATUS=0

    # Run all checks
    check_docker_services || OVERALL_STATUS=1
    check_web_health || OVERALL_STATUS=1
    check_api_health || OVERALL_STATUS=1
    check_database || OVERALL_STATUS=1
    check_redis || OVERALL_STATUS=1
    check_ai_service
    check_disk_space || OVERALL_STATUS=1
    check_memory || OVERALL_STATUS=1
    check_cpu || OVERALL_STATUS=1
    check_ssl_certificates
    check_application_logs
    generate_health_report

    echo "" | tee -a "$LOG_FILE"

    if [ $OVERALL_STATUS -eq 0 ]; then
        success "All critical health checks passed!"
        exit 0
    else
        error "Some health checks failed. Please review the logs."
        exit 1
    fi
}

# Run main function
main
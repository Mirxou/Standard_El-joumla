#!/bin/bash

# Unified Commerce ERP Backup Script
# Version: 1.0.0
# Description: Automated backup for production environment

set -e

# Configuration
BACKUP_DIR="./backups"
RETENTION_DAYS=30
PROJECT_NAME="unified-commerce-erp"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Create backup directory
create_backup_dir() {
    mkdir -p "$BACKUP_DIR"
    log "Backup directory: $BACKUP_DIR"
}

# Backup database
backup_database() {
    log "Backing up database..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz"

    # Create compressed database backup
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dumpall -U postgres | gzip > "$BACKUP_FILE"

    # Verify backup
    if [ -s "$BACKUP_FILE" ]; then
        success "Database backup created: $BACKUP_FILE"
        echo "$BACKUP_FILE" >> "$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
    else
        error "Database backup failed or is empty"
    fi
}

# Backup application data
backup_application_data() {
    log "Backing up application data..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/app_data_$TIMESTAMP.tar.gz"

    # Backup media files, logs, and configuration
    tar -czf "$BACKUP_FILE" \
        --exclude='*.log' \
        --exclude='*.tmp' \
        media/ \
        logs/ \
        config/ \
        data/

    success "Application data backup created: $BACKUP_FILE"
    echo "$BACKUP_FILE" >> "$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
}

# Backup Docker volumes
backup_docker_volumes() {
    log "Backing up Docker volumes..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    # List all volumes
    VOLUMES=$(docker volume ls -q | grep "$PROJECT_NAME")

    for volume in $VOLUMES; do
        BACKUP_FILE="$BACKUP_DIR/volume_${volume}_$TIMESTAMP.tar.gz"
        docker run --rm -v "$volume:/data" -v "$BACKUP_DIR:/backup" alpine tar czf "/backup/$(basename "$BACKUP_FILE")" -C /data .
        echo "$BACKUP_FILE" >> "$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
        success "Volume $volume backed up: $BACKUP_FILE"
    done
}

# Backup configuration files
backup_configuration() {
    log "Backing up configuration files..."

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/config_$TIMESTAMP.tar.gz"

    tar -czf "$BACKUP_FILE" \
        docker-compose.production.yml \
        Dockerfile.production \
        nginx/nginx.conf \
        ssl/ \
        .env.production \
        config/

    success "Configuration backup created: $BACKUP_FILE"
    echo "$BACKUP_FILE" >> "$BACKUP_DIR/backup_manifest_$TIMESTAMP.txt"
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (older than $RETENTION_DAYS days)..."

    find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.sql" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "backup_manifest_*" -mtime +$RETENTION_DAYS -delete

    success "Old backups cleaned up."
}

# Generate backup report
generate_report() {
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    REPORT_FILE="$BACKUP_DIR/backup_report_$TIMESTAMP.txt"

    echo "Unified Commerce ERP Backup Report" > "$REPORT_FILE"
    echo "Generated: $(date)" >> "$REPORT_FILE"
    echo "=================================" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "Backup Summary:" >> "$REPORT_FILE"
    echo "- Database: $(ls -lh "$BACKUP_DIR"/db_backup_*.gz 2>/dev/null | wc -l) backups" >> "$REPORT_FILE"
    echo "- Application Data: $(ls -lh "$BACKUP_DIR"/app_data_*.gz 2>/dev/null | wc -l) backups" >> "$REPORT_FILE"
    echo "- Configuration: $(ls -lh "$BACKUP_DIR"/config_*.gz 2>/dev/null | wc -l) backups" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "Disk Usage:" >> "$REPORT_FILE"
    du -sh "$BACKUP_DIR" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"

    echo "Recent Backups:" >> "$REPORT_FILE"
    ls -lt "$BACKUP_DIR" | head -20 >> "$REPORT_FILE"

    success "Backup report generated: $REPORT_FILE"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."

    # Check if backup files exist and are not empty
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.gz | head -1)

    if [ -n "$LATEST_BACKUP" ] && [ -s "$LATEST_BACKUP" ]; then
        success "Latest database backup is valid: $LATEST_BACKUP"
    else
        error "Latest database backup is invalid or missing"
    fi
}

# Main backup function
main() {
    log "Starting backup process for $PROJECT_NAME"

    create_backup_dir

    case "$1" in
        "full")
            backup_database
            backup_application_data
            backup_docker_volumes
            backup_configuration
            verify_backup
            generate_report
            cleanup_old_backups
            success "Full backup completed successfully!"
            ;;
        "database")
            backup_database
            verify_backup
            success "Database backup completed successfully!"
            ;;
        "config")
            backup_configuration
            success "Configuration backup completed successfully!"
            ;;
        "cleanup")
            cleanup_old_backups
            success "Cleanup completed!"
            ;;
        "report")
            generate_report
            ;;
        *)
            echo "Usage: $0 {full|database|config|cleanup|report}"
            echo "  full: Complete backup (database, app data, volumes, config)"
            echo "  database: Database backup only"
            echo "  config: Configuration backup only"
            echo "  cleanup: Remove old backups"
            echo "  report: Generate backup report"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
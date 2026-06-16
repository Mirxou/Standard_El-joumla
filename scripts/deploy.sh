#!/bin/bash

# Standard El-Joumla Production Deployment Script
# Version: 1.0.0
# Description: Automated deployment for production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="unified-commerce-erp"
DOCKER_COMPOSE_FILE="docker-compose.production.yml"
BACKUP_DIR="./backups"
LOG_FILE="./logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
    fi

    # Check if docker-compose file exists
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        error "Docker compose file '$DOCKER_COMPOSE_FILE' not found."
    fi

    # Check environment variables
    if [ ! -f ".env.production" ]; then
        warning "Production environment file '.env.production' not found."
        warning "Please create it with required environment variables."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    success "Pre-deployment checks completed."
}

# Create backup
create_backup() {
    log "Creating backup..."

    mkdir -p "$BACKUP_DIR"

    # Database backup
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps db | grep -q "Up"; then
        log "Backing up database..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dumpall -U postgres > "$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    fi

    # Configuration backup
    cp -r config "$BACKUP_DIR/config_backup_$(date +%Y%m%d_%H%M%S)"

    success "Backup created in $BACKUP_DIR"
}

# Deploy application
deploy_application() {
    log "Deploying application..."

    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" pull

    # Stop existing containers
    log "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    # Start new containers
    log "Starting new containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30

    success "Application deployed successfully."
}

# Run health checks
run_health_checks() {
    log "Running health checks..."

    # Check if all services are running
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Exit"; then
        success "All services are running."
    else
        error "Some services failed to start. Check logs with: docker-compose -f $DOCKER_COMPOSE_FILE logs"
    fi

    # Check web service health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        success "Web service is healthy."
    else
        warning "Web service health check failed."
    fi

    # Check API service health
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        success "API service is healthy."
    else
        warning "API service health check failed."
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."

    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py migrate

    success "Database migrations completed."
}

# Post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."

    # Clear cache
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py clear_cache

    # Collect static files
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput

    # Restart services if needed
    docker-compose -f "$DOCKER_COMPOSE_FILE" restart web api

    success "Post-deployment tasks completed."
}

# Rollback function
rollback() {
    log "Rolling back deployment..."

    # Stop current deployment
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    # Find latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.sql | head -1)

    if [ -n "$LATEST_BACKUP" ]; then
        log "Restoring from backup: $LATEST_BACKUP"
        # Restore database from backup
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db psql -U postgres < "$LATEST_BACKUP"
    fi

    # Restart with previous version
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    success "Rollback completed."
}

# Main deployment function
main() {
    log "Starting deployment of $PROJECT_NAME"

    case "$1" in
        "deploy")
            pre_deployment_checks
            create_backup
            deploy_application
            run_migrations
            run_health_checks
            post_deployment_tasks
            success "Deployment completed successfully!"
            ;;
        "rollback")
            rollback
            ;;
        "status")
            docker-compose -f "$DOCKER_COMPOSE_FILE" ps
            ;;
        "logs")
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
            ;;
        *)
            echo "Usage: $0 {deploy|rollback|status|logs}"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
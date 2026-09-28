#!/usr/bin/env bash
# ============================================================================
# Standard El-Joumla ERP — Deployment Script
# Supports: staging, production, rollback, canary, blue-green
# Usage:
#   bash scripts/deploy.sh staging v6.1.0 blue-green
#   bash scripts/deploy.sh production v6.1.0 canary --weight=5
#   bash scripts/deploy.sh production rollback
# ============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────
ENVIRONMENT="${1:-staging}"
VERSION="${2:-latest}"
STRATEGY="${3:-direct}"
EXTRA_ARGS="${4:-}"

REGISTRY="${DOCKER_REGISTRY:-ghcr.io/mirxou/standard_el-joumla}"
API_IMAGE="${REGISTRY}/erp-api"
COMPOSE_FILE="docker-compose.yml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DEPLOY_DIR="/opt/erp"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${BLUE}[DEPLOY]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Pre-flight Checks ────────────────────────────────────────────────────
preflight() {
    log "Running pre-flight checks..."

    # Check Docker
    command -v docker &>/dev/null || err "Docker not installed"
    docker info &>/dev/null || err "Docker daemon not running"

    # Check Docker Compose
    if docker compose version &>/dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &>/dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        err "Docker Compose not installed"
    fi

    # Check disk space (need at least 2GB)
    AVAILABLE=$(df -BG / | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ "$AVAILABLE" -lt 2 ]]; then
        err "Insufficient disk space: ${AVAILABLE}GB (need 2GB+)"
    fi

    ok "Pre-flight checks passed"
}

# ── Health Check ─────────────────────────────────────────────────────────
health_check() {
    local url="${1:-http://localhost:8000/api/v1/health}"
    local max_retries="${2:-30}"
    local retry=0

    log "Health check: $url"
    while [[ $retry -lt $max_retries ]]; do
        if curl -sf --max-time 5 "$url" &>/dev/null; then
            ok "Health check passed (attempt $((retry+1)))"
            return 0
        fi
        retry=$((retry+1))
        sleep 2
    done

    err "Health check FAILED after $max_retries attempts"
}

# ── Backup Current State ─────────────────────────────────────────────────
create_backup() {
    log "Creating pre-deployment backup..."
    local backup_dir="${DEPLOY_DIR}/backups/${TIMESTAMP}"
    mkdir -p "$backup_dir"

    # Backup database
    if [[ -f "${DEPLOY_DIR}/data/erp.db" ]]; then
        cp "${DEPLOY_DIR}/data/erp.db" "$backup_dir/erp.db"
        ok "Database backed up"
    fi

    # Backup config
    if [[ -d "${DEPLOY_DIR}/config" ]]; then
        cp -r "${DEPLOY_DIR}/config" "$backup_dir/"
        ok "Config backed up"
    fi

    # Record current version
    echo "$VERSION" > "$backup_dir/deployed_version.txt"
    echo "$TIMESTAMP" > "$backup_dir/deploy_timestamp.txt"

    ok "Backup created: $backup_dir"
}

# ── Pull Images ──────────────────────────────────────────────────────────
pull_images() {
    log "Pulling Docker images for $VERSION..."
    docker pull "${API_IMAGE}:${VERSION}" 2>/dev/null || \
    docker pull "${API_IMAGE}:latest" || \
    warn "Image pull failed — using local image"
    ok "Images ready"
}

# ── Rollback ─────────────────────────────────────────────────────────────
rollback() {
    log "🔄 ROLLBACK INITIATED"

    # Find latest backup
    local latest_backup
    latest_backup=$(ls -td "${DEPLOY_DIR}"/backups/*/ 2>/dev/null | head -1)

    if [[ -z "$latest_backup" ]]; then
        err "No backup found for rollback"
    fi

    local prev_version
    prev_version=$(cat "$latest_backup/deployed_version.txt" 2>/dev/null || echo "unknown")
    log "Rolling back to: $prev_version"

    # Restore database
    if [[ -f "$latest_backup/erp.db" ]]; then
        cp "$latest_backup/erp.db" "${DEPLOY_DIR}/data/erp.db"
        ok "Database restored"
    fi

    # Restore config
    if [[ -d "$latest_backup/config" ]]; then
        rm -rf "${DEPLOY_DIR}/config"
        cp -r "$latest_backup/config" "${DEPLOY_DIR}/"
        ok "Config restored"
    fi

    # Rollback containers to previous version
    if [[ "$prev_version" != "unknown" ]]; then
        export ERP_IMAGE_TAG="$prev_version"
        $COMPOSE_CMD -f "$COMPOSE_FILE" down --timeout=30
        $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --remove-orphans
        health_check
    fi

    ok "Rollback complete — running $prev_version"
}

# ── Deploy: Direct ───────────────────────────────────────────────────────
deploy_direct() {
    log "📦 Direct deployment: $VERSION → $ENVIRONMENT"
    create_backup
    pull_images

    export ERP_IMAGE_TAG="$VERSION"
    export ERP_ENV="$ENVIRONMENT"

    $COMPOSE_CMD -f "$COMPOSE_FILE" up -d --remove-orphans --no-deps api
    health_check "http://localhost:8000/api/v1/health" 30

    ok "Direct deployment complete"
}

# ── Deploy: Blue-Green ───────────────────────────────────────────────────
deploy_blue_green() {
    log "🔵🟢 Blue-Green deployment: $VERSION → $ENVIRONMENT"

    create_backup
    pull_images

    # Determine current and next color
    CURRENT_COLOR=$(cat "${DEPLOY_DIR}/.deploy_color" 2>/dev/null || echo "blue")
    if [[ "$CURRENT_COLOR" == "blue" ]]; then
        NEXT_COLOR="green"
    else
        NEXT_COLOR="blue"
    fi

    log "Current: $CURRENT_COLOR → Deploying: $NEXT_COLOR"

    # Start new (next color) containers
    export ERP_IMAGE_TAG="$VERSION"
    export ERP_ENV="$ENVIRONMENT"
    export DEPLOY_COLOR="$NEXT_COLOR"

    $COMPOSE_CMD -f "$COMPOSE_FILE" -f "docker-compose.${NEXT_COLOR}.yml" up -d --no-deps api

    # Health check on new containers
    NEXT_PORT=8001  # Green runs on different port during switch
    health_check "http://localhost:${NEXT_PORT}/api/v1/health" 30

    # Switch traffic (update nginx upstream)
    log "🔀 Switching traffic from $CURRENT_COLOR to $NEXT_COLOR"
    if command -v nginx &>/dev/null; then
        sed -i "s/server 127.0.0.1:8000;/server 127.0.0.1:${NEXT_PORT};/" \
            /etc/nginx/conf.d/erp-upstream.conf 2>/dev/null || true
        nginx -s reload 2>/dev/null || true
    fi

    # Record new active color
    echo "$NEXT_COLOR" > "${DEPLOY_DIR}/.deploy_color"

    # Stop old containers (with grace period)
    log "⏳ Waiting 30s before stopping old ($CURRENT_COLOR) containers..."
    sleep 30

    export DEPLOY_COLOR="$CURRENT_COLOR"
    $COMPOSE_CMD -f "$COMPOSE_FILE" -f "docker-compose.${CURRENT_COLOR}.yml" down --timeout=60 2>/dev/null || true

    ok "Blue-Green deployment complete — $NEXT_COLOR is active"
}

# ── Deploy: Canary ───────────────────────────────────────────────────────
deploy_canary() {
    local weight=5
    if [[ "$EXTRA_ARGS" == --weight=* ]]; then
        weight="${EXTRA_ARGS#--weight=}"
    fi

    log "🐤 Canary deployment: $VERSION → $ENVIRONMENT ($weight% traffic)"

    create_backup
    pull_images

    # Deploy canary containers alongside production
    export ERP_IMAGE_TAG="$VERSION"
    export ERP_ENV="$ENVIRONMENT"

    $COMPOSE_CMD -f "$COMPOSE_FILE" -f "docker-compose.canary.yml" up -d --no-deps api-canary

    # Health check canary
    health_check "http://localhost:8002/api/v1/health" 30

    # Configure nginx to split traffic
    if command -v nginx &>/dev/null; then
        cat > /etc/nginx/conf.d/erp-canary.conf <<EOF
upstream erp_backend {
    server 127.0.0.1:8000 weight=$((100-weight));
    server 127.0.0.1:8002 weight=$weight;
}
EOF
        nginx -s reload 2>/dev/null || true
    fi

    log "🐤 Canary active at ${weight}% — monitor before full rollout"
    ok "Canary deployment complete"
}

# ── Main ─────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║     Standard El-Joumla ERP — Deployment System       ║"
    echo "║     Environment: $(printf '%-40s' "$ENVIRONMENT")║"
    echo "║     Version:      $(printf '%-40s' "$VERSION")║"
    echo "║     Strategy:     $(printf '%-40s' "$STRATEGY")║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""

    # Handle rollback specially
    if [[ "$STRATEGY" == "rollback" ]]; then
        preflight
        rollback
        exit 0
    fi

    # Select compose file based on environment
    case "$ENVIRONMENT" in
        staging)
            COMPOSE_FILE="docker-compose.yml"
            ;;
        production)
            COMPOSE_FILE="docker-compose.prod.yml"
            ;;
        *)
            err "Unknown environment: $ENVIRONMENT"
            ;;
    esac

    preflight

    # Deploy based on strategy
    case "$STRATEGY" in
        direct)
            deploy_direct
            ;;
        blue-green)
            deploy_blue_green
            ;;
        canary)
            deploy_canary
            ;;
        *)
            err "Unknown strategy: $STRATEGY (use: direct, blue-green, canary, rollback)"
            ;;
    esac

    echo ""
    ok "🎉 Deployment complete: $VERSION → $ENVIRONMENT ($STRATEGY)"
}

main "$@"

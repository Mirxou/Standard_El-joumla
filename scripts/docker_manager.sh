#!/bin/bash
# =============================================================================
# Docker Management Utility - إدارة Docker الموحدة
# =============================================================================
# Usage:
#   ./docker_manager.sh start      - بدء جميع الخدمات
#   ./docker_manager.sh stop       - إيقاف جميع الخدمات
#   ./docker_manager.sh restart    - إعادة تشغيل
#   ./docker_manager.sh status      - عرض الحالة
#   ./docker_manager.sh logs       - عرض السجلات
#   ./docker_manager.sh build      - بناء الصور
#   ./docker_manager.sh clean      - تنظيف الحاويات
# =============================================================================

set -e

# الألوان
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# إعدادات افتراضية
COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="logical_erp"

# دوال مساعدة
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# التحقق من Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker غير مثبت"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose غير مثبت"
        exit 1
    fi
    
    log_success "Docker متاح"
}

# بدء الخدمات
start_services() {
    log_info "بدء الخدمات..."
    
    # استخدام docker compose إذا كان متاحاً
    if docker compose version &> /dev/null; then
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    else
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d
    fi
    
    log_success "تم بدء الخدمات"
    show_status
}

# إيقاف الخدمات
stop_services() {
    log_info "إيقاف الخدمات..."
    
    if docker compose version &> /dev/null; then
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    else
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" down
    fi
    
    log_success "تم إيقاف الخدمات"
}

# إعادة تشغيل
restart_services() {
    stop_services
    sleep 2
    start_services
}

# عرض الحالة
show_status() {
    log_info "حالة الخدمات:"
    
    if docker compose version &> /dev/null; then
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    else
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
    fi
}

# عرض السجلات
show_logs() {
    SERVICE=${2:-}
    
    if [ -n "$SERVICE" ]; then
        log_info "سجلات خدمة: $SERVICE"
        if docker compose version &> /dev/null; then
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$SERVICE"
        else
            docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f "$SERVICE"
        fi
    else
        log_info "جميع السجلات:"
        if docker compose version &> /dev/null; then
            docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
        else
            docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs -f
        fi
    fi
}

# بناء الصور
build_images() {
    log_info "بناء الصور..."
    
    if docker compose version &> /dev/null; then
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build --no-cache
    else
        docker-compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build --no-cache
    fi
    
    log_success "تم بناء الصور"
}

# تنظيف
clean_services() {
    log_warning "تنظيف الخدمات..."
    
    stop_services
    
    log_info "حذف الصور غير المستخدمة..."
    docker image prune -f
    
    log_info "حذف الشبكات غير المستخدمة..."
    docker network prune -f
    
    log_success "تم التنظيف"
}

# عرض المساعدة
show_help() {
    echo "================================================================================"
    echo " Docker Management Utility - إدارة Docker الموحدة"
    echo "================================================================================"
    echo ""
    echo "الاستخدام: $0 [command] [service]"
    echo ""
    echo "الأوامر:"
    echo "  start              بدء جميع الخدمات"
    echo "  stop               إيقاف جميع الخدمات"
    echo "  restart            إعادة تشغيل الخدمات"
    echo "  status             عرض حالة الخدمات"
    echo "  logs [service]     عرض السجلات (اختياري: اسم الخدمة)"
    echo "  build              بناء الصور"
    echo "  clean              تنظيف الحاويات والشبكات"
    echo "  help               عرض هذه المساعدة"
    echo ""
    echo "أمثلة:"
    echo "  $0 start              # بدء جميع الخدمات"
    echo "  $0 logs api           # عرض سجلات خدمة API"
    echo "  $0 status             # عرض الحالة"
    echo "================================================================================"
}

# Main
case "$1" in
    start)
        check_docker
        start_services
        ;;
    stop)
        check_docker
        stop_services
        ;;
    restart)
        check_docker
        restart_services
        ;;
    status)
        check_docker
        show_status
        ;;
    logs)
        check_docker
        show_logs "$@"
        ;;
    build)
        check_docker
        build_images
        ;;
    clean)
        check_docker
        clean_services
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "أمر غير معروف: $1"
        show_help
        exit 1
        ;;
esac
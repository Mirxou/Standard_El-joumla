import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus Metrics for API
مقاييس Prometheus للـ API
"""


logger = logging.getLogger(__name__)

# جعل prometheus_client optional dependency
try:
    from prometheus_client import (
        CONTENT_TYPE_LATEST,
        REGISTRY,
        Counter,
        Gauge,
        Histogram,
        Info,
        generate_latest,
    )
    from prometheus_client.openmetrics.exposition import (
        generate_latest as generate_openmetrics,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client غير متاح - سيتم تعطيل Prometheus Metrics")

    # Stub classes للتعامل مع عدم وجود prometheus_client
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def inc(self, *args, **kwargs):
            pass

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def observe(self, *args, **kwargs):
            pass

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def labels(self, **kwargs):
            return self

        def set(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

    class Info:
        def __init__(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"
    REGISTRY = None

    def generate_latest(*args, **kwargs):
        return b"# Prometheus metrics not available\n"

    def generate_openmetrics(*args, **kwargs):
        return b"# Prometheus metrics not available\n"


# ==================== Metrics Definitions ====================

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Authentication Metrics
auth_attempts_total = Counter(
    "auth_attempts_total",
    "Total number of authentication attempts",
    ["status"],  # success, failed
)

auth_tokens_issued_total = Counter(
    "auth_tokens_issued_total",
    "Total number of JWT tokens issued",
    ["token_type"],  # access, refresh
)

# Rate Limiting Metrics
rate_limit_hits_total = Counter(
    "rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint", "ip_address"],
)

# Database Metrics
db_queries_total = Counter(
    "db_queries_total",
    "Total number of database queries",
    ["query_type"],  # select, insert, update, delete
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

db_connections_active = Gauge("db_connections_active", "Number of active database connections")

# Cache Metrics
cache_operations_total = Counter(
    "cache_operations_total",
    "Total number of cache operations",
    [
        "operation",
        "cache_name",
        "status",
    ],  # get, set, delete | products, customers, etc. | hit, miss
)

cache_size = Gauge("cache_size", "Number of items in cache", ["cache_name"])

# Business Logic Metrics
products_created_total = Counter("products_created_total", "Total number of products created")

products_updated_total = Counter("products_updated_total", "Total number of products updated")

products_deleted_total = Counter("products_deleted_total", "Total number of products deleted")

sales_created_total = Counter("sales_created_total", "Total number of sales created")

sales_total_amount = Counter("sales_total_amount", "Total amount of sales", ["currency"])  # SAR, USD, etc.

# System Metrics
api_info = Info("api_info", "API information")

api_uptime_seconds = Gauge("api_uptime_seconds", "API uptime in seconds")

api_active_requests = Gauge("api_active_requests", "Number of active API requests")

# Error Metrics
api_errors_total = Counter(
    "api_errors_total",
    "Total number of API errors",
    ["error_type", "endpoint"],  # 400, 401, 403, 404, 500, etc.
)

# WebSocket Metrics
websocket_connections_active = Gauge("websocket_connections_active", "Number of active WebSocket connections")

websocket_messages_total = Counter(
    "websocket_messages_total",
    "Total number of WebSocket messages",
    ["direction"],  # sent, received
)


# ==================== Helper Functions ====================


def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """تسجيل طلب HTTP"""
    if not PROMETHEUS_AVAILABLE:
        return
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_auth_attempt(status: str):
    """تسجيل محاولة مصادقة"""
    if not PROMETHEUS_AVAILABLE:
        return
    auth_attempts_total.labels(status=status).inc()


def record_token_issued(token_type: str):
    """تسجيل إصدار Token"""
    if not PROMETHEUS_AVAILABLE:
        return
    auth_tokens_issued_total.labels(token_type=token_type).inc()


def record_rate_limit_hit(endpoint: str, ip_address: str):
    """تسجيل ضربة Rate Limit"""
    if not PROMETHEUS_AVAILABLE:
        return
    rate_limit_hits_total.labels(endpoint=endpoint, ip_address=ip_address).inc()


def record_db_query(query_type: str, duration: float):
    """تسجيل استعلام قاعدة البيانات"""
    if not PROMETHEUS_AVAILABLE:
        return
    db_queries_total.labels(query_type=query_type).inc()
    db_query_duration_seconds.labels(query_type=query_type).observe(duration)


def record_cache_operation(operation: str, cache_name: str, status: str):
    """تسجيل عملية Cache"""
    if not PROMETHEUS_AVAILABLE:
        return
    cache_operations_total.labels(operation=operation, cache_name=cache_name, status=status).inc()


def set_cache_size(cache_name: str, size: int):
    """تعيين حجم Cache"""
    if not PROMETHEUS_AVAILABLE:
        return
    cache_size.labels(cache_name=cache_name).set(size)


def record_product_created():
    """تسجيل إنشاء منتج"""
    if not PROMETHEUS_AVAILABLE:
        return
    products_created_total.inc()


def record_product_updated():
    """تسجيل تحديث منتج"""
    if not PROMETHEUS_AVAILABLE:
        return
    products_updated_total.inc()


def record_product_deleted():
    """تسجيل حذف منتج"""
    if not PROMETHEUS_AVAILABLE:
        return
    products_deleted_total.inc()


def record_sale_created(amount: float, currency: str = "SAR"):
    """تسجيل إنشاء مبيعة"""
    if not PROMETHEUS_AVAILABLE:
        return
    sales_created_total.inc()
    sales_total_amount.labels(currency=currency).inc(amount)


def record_api_error(error_type: str, endpoint: str):
    """تسجيل خطأ API"""
    if not PROMETHEUS_AVAILABLE:
        return
    api_errors_total.labels(error_type=error_type, endpoint=endpoint).inc()


def set_websocket_connections(count: int):
    """تعيين عدد اتصالات WebSocket"""
    if not PROMETHEUS_AVAILABLE:
        return
    websocket_connections_active.set(count)


def record_websocket_message(direction: str):
    """تسجيل رسالة WebSocket"""
    if not PROMETHEUS_AVAILABLE:
        return
    websocket_messages_total.labels(direction=direction).inc()


def set_db_connections(count: int):
    """تعيين عدد اتصالات قاعدة البيانات"""
    if not PROMETHEUS_AVAILABLE:
        return
    db_connections_active.set(count)


def set_active_requests(count: int):
    """تعيين عدد الطلبات النشطة"""
    if not PROMETHEUS_AVAILABLE:
        return
    api_active_requests.set(count)


def set_uptime(seconds: float):
    """تعيين وقت التشغيل"""
    if not PROMETHEUS_AVAILABLE:
        return
    api_uptime_seconds.set(seconds)


def initialize_metrics():
    """تهيئة Metrics"""
    if not PROMETHEUS_AVAILABLE:
        logger.warning("⚠️ Prometheus Metrics غير متاحة - prometheus_client غير مثبت")
        return

    try:
        # تعيين معلومات API
        api_info.info(
            {
                "version": "1.0.0",
                "api_version": "v1",
                "name": "ستاندرد الجملة - REST API",
            }
        )

        logger.info("✅ تم تهيئة Prometheus Metrics")
    except Exception as e:
        logger.warning(f"⚠️ خطأ في تهيئة Metrics: {e}")


def get_metrics_output(format: str = "prometheus") -> tuple:
    """
    الحصول على Metrics بصيغة Prometheus

    Args:
        format: نوع الصيغة ('prometheus' أو 'openmetrics')

    Returns:
        (content, content_type)
    """
    if not PROMETHEUS_AVAILABLE:
        return "# Prometheus metrics not available\n", CONTENT_TYPE_LATEST

    try:
        if format == "openmetrics":
            output = generate_openmetrics(REGISTRY)
            content_type = "application/openmetrics-text; version=1.0.0; charset=utf-8"
        else:
            output = generate_latest(REGISTRY)
            content_type = CONTENT_TYPE_LATEST

        return output.decode("utf-8"), content_type
    except Exception as e:
        logger.log(logging.ERROR, f"❌ خطأ في توليد Metrics: {e}")
        return "", CONTENT_TYPE_LATEST

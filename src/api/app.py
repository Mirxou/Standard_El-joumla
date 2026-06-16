import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application - REST API Server
تطبيق FastAPI للـ REST API
"""

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from src.api.auth import JWTAuthManager
from src.api.middleware import setup_middleware
from src.api.rate_limiter import APIRateLimiter
from src.api.websocket_manager import get_websocket_manager
from src.core.config_manager import ConfigManager
from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger

# تهيئة Logger
logger = setup_logger(__name__)

# جعل PrometheusMiddleware optional
try:
    from src.api.metrics import initialize_metrics
    from src.api.prometheus_middleware import PrometheusMiddleware

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PrometheusMiddleware = None
    initialize_metrics = None
    PROMETHEUS_AVAILABLE = False
    logger.warning("PrometheusMiddleware غير متاح - سيتم تعطيل Prometheus Metrics")


# إصدار API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# تهيئة الموارد الأساسية مبكراً للسماح بإضافة Middleware
config_manager = ConfigManager()
config_manager.load_config()
db_path = config_manager.get_database_path()

# تهيئة المكونات (سيتم تفعيلها في lifespan)
db_manager = DatabaseManager(db_path=db_path)
auth_manager = JWTAuthManager(db_manager)
rate_limiter = APIRateLimiter(
    default_max_requests=100,
    default_window_seconds=60,
    per_endpoint_limits={
        "/api/v1/auth/login": {"max_requests": 5, "window_seconds": 60},
        "/api/v1/auth/refresh": {"max_requests": 10, "window_seconds": 60},
    },
)

_routes_registered = False

# إعداد CORS افتراضي
_cors_origins_default = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events للـ FastAPI
    تفعيل الموارد وإغلاقها
    """
    global _start_time
    _start_time = time.time()
    logger.info("🚀 بدء تشغيل REST API Server...")

    try:
        # تفعيل قاعدة البيانات (تشغيل الهجرات)
        if not db_manager.initialize():
            logger.log(logging.ERROR, "❌ فشل تهيئة قاعدة البيانات")
            raise RuntimeError("فشل تهيئة قاعدة البيانات")

        logger.info(f"✅ تم تهيئة قاعدة البيانات بنجاح - المسار: {db_manager.db_path}")

        # تهيئة WebSocket Manager
        get_websocket_manager()

        # إنشاء فئات افتراضية
        try:
            from src.models.category import CategoryManager

            cat_manager = CategoryManager(db_manager, logger)
            cat_manager.create_default_categories()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in app.py")

        logger.info("✅ REST API Server جاهز!")

    except Exception as e:
        logger.log(logging.ERROR, f"❌ خطأ في تهيئة REST API Server: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 إيقاف REST API Server...")
    if db_manager:
        db_manager.close()
        logger.info("✅ تم إغلاق قاعدة البيانات")


# إنشاء FastAPI App
app = FastAPI(
    title="ستاندرد الجملة - REST API",
    description="REST API للتكامل الخارجي مع نظام ERP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# إعداد Middlewares (يجب إضافتها هنا، وليس في lifespan)
cors_origins = _cors_origins_default
try:
    cors_origins = config_manager.get_cors_origins()
except Exception:
    logging.getLogger(__name__).warning("Ignored exception in app.py")

setup_middleware(
    app=app,
    db_manager=db_manager,
    auth_manager=auth_manager,
    rate_limiter=rate_limiter,
    enable_cors=True,
    cors_origins=cors_origins,
)

# إضافة Prometheus Middleware
if PROMETHEUS_AVAILABLE and PrometheusMiddleware:
    try:
        app.add_middleware(
            PrometheusMiddleware,
            exclude_paths=["/metrics", "/health", "/docs", "/openapi.json", "/redoc"],
        )
    except Exception:
        logging.getLogger(__name__).warning("Ignored exception in app.py")


@app.get("/health")
async def health_check():
    """فحص صحة الـ API"""
    return {"status": "healthy", "version": "1.0.0", "api_version": API_VERSION}


def custom_openapi():
    """تخصيص OpenAPI Schema"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="ستاندرد الجملة - REST API",
        version="1.0.0",
        description="REST API للتكامل الخارجي مع نظام ERP",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def register_routes():
    """تسجيل جميع Routes"""
    global _routes_registered
    if _routes_registered:
        return
    try:
        from src.api.routes import router
        from src.api.sync_routes import sync_router

        app.include_router(router, prefix=API_PREFIX)
        app.include_router(sync_router, prefix=f"{API_PREFIX}/sync")
        logger.info(f"✅ تم تسجيل Routes بنجاح (prefix: {API_PREFIX})")
        _routes_registered = True
    except Exception as e:
        logger.warning(f"⚠️ خطأ في تسجيل Routes: {e}")


# تسجيل Routes عند بدء الاستيراد
register_routes()


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """معالج 404"""
    return JSONResponse(status_code=404, content={"detail": f"Endpoint غير موجود: {request.url.path}"})


@app.get("/")
async def root():
    """Root endpoint for connection check"""
    import os

    current_db_path = db_manager.db_path if db_manager else "Unknown"
    size_mb = 0
    if isinstance(current_db_path, (str, Path)) and os.path.exists(current_db_path):
        size_mb = os.path.getsize(current_db_path) / (1024 * 1024)

    return {
        "status": "Connected ✅",
        "database_file": os.path.basename(str(current_db_path)),
        "path": str(current_db_path),
        "size": f"{size_mb:.2f} MB",
        "api_version": API_VERSION,
    }


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """معالج 500"""
    logger.log(logging.ERROR, f"Internal Server Error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "خطأ داخلي في الخادم"})


def create_app(db_path: Optional[str] = None) -> FastAPI:
    """إنشاء تطبيق FastAPI"""
    if db_path:
        global db_manager  # noqa: F824
        db_manager.db_path = db_path
    return app


__all__ = ["app", "create_app", "API_VERSION", "API_PREFIX"]

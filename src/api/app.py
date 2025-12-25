#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application - REST API Server
تطبيق FastAPI للـ REST API
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager
from datetime import datetime
import sys
import time
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.database_manager import DatabaseManager
from src.api.auth import JWTAuthManager
from src.api.rate_limiter import APIRateLimiter
from src.api.middleware import setup_middleware
from src.api.websocket_manager import get_websocket_manager
from src.api.prometheus_middleware import PrometheusMiddleware
from src.api.metrics import initialize_metrics
from src.utils.logger import setup_logger


# إصدار API
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# تهيئة Logger
logger = setup_logger(__name__)

# Global instances (سيتم تهيئتها في lifespan)
db_manager: DatabaseManager = None
auth_manager: JWTAuthManager = None
rate_limiter: APIRateLimiter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events للـ FastAPI
    تهيئة وإغلاق الموارد
    """
    global db_manager, auth_manager, rate_limiter
    
    # Startup
    global _start_time
    _start_time = time.time()
    logger.info("🚀 بدء تشغيل REST API Server...")
    
    try:
        # تهيئة Database Manager
        db_manager = DatabaseManager()
        if not db_manager.initialize():
            logger.error("❌ فشل تهيئة قاعدة البيانات")
            raise RuntimeError("فشل تهيئة قاعدة البيانات")
        
        logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
        
        # تهيئة JWT Auth Manager
        auth_manager = JWTAuthManager(db_manager)
        logger.info("✅ تم تهيئة JWT Authentication Manager")
        
        # تهيئة Rate Limiter
        rate_limiter = APIRateLimiter(
            default_max_requests=100,
            default_window_seconds=60,
            per_endpoint_limits={
                "/api/v1/auth/login": {"max_requests": 5, "window_seconds": 60},
                "/api/v1/auth/refresh": {"max_requests": 10, "window_seconds": 60},
            }
        )
        logger.info("✅ تم تهيئة Rate Limiter")
        
        # تهيئة WebSocket Manager
        ws_manager = get_websocket_manager()
        logger.info("✅ تم تهيئة WebSocket Manager")
        
        # تهيئة Redis Cache Manager
        try:
            from src.api.cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            if cache_manager.enabled:
                logger.info("✅ تم تهيئة Redis Cache Manager")
            else:
                logger.info("ℹ️ Redis Cache غير متاح - سيتم استخدام LRU Cache")
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تهيئة Cache Manager: {e}")
        
        # تهيئة Prometheus Metrics
        try:
            initialize_metrics()
            # بدء تحديث Uptime Metric
            import threading
            def update_uptime():
                from src.api.metrics import set_uptime
                while True:
                    if _start_time:
                        set_uptime(time.time() - _start_time)
                    time.sleep(10)  # تحديث كل 10 ثواني
            
            uptime_thread = threading.Thread(target=update_uptime, daemon=True)
            uptime_thread.start()
        except Exception as e:
            logger.warning(f"⚠️ خطأ في تهيئة Prometheus Metrics: {e}")
        
        logger.info("✅ REST API Server جاهز!")
        
        # تسجيل Routes بعد تهيئة الموارد
        register_routes()
        
    except Exception as e:
        logger.error(f"❌ خطأ في تهيئة REST API Server: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 إيقاف REST API Server...")
    
    if db_manager:
        db_manager.close()
        logger.info("✅ تم إغلاق قاعدة البيانات")


# إنشاء FastAPI App
app = FastAPI(
    title="الإصدار المنطقي - REST API",
    description="REST API للتكامل الخارجي مع نظام ERP",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# إعداد CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج، حدد الـ origins المسموحة
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إضافة Prometheus Middleware (قبل Middlewares الأخرى)
app.add_middleware(
    PrometheusMiddleware,
    exclude_paths=["/metrics", "/health", "/docs", "/openapi.json", "/redoc"]
)


# Health Check Endpoint
@app.get("/health")
async def health_check():
    """فحص صحة الـ API"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api_version": API_VERSION
    }


# Custom OpenAPI Schema
def custom_openapi():
    """تخصيص OpenAPI Schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="الإصدار المنطقي - REST API",
        version="1.0.0",
        description="""
        REST API للتكامل الخارجي مع نظام ERP
        
        ## المصادقة
        جميع الطلبات (عدا `/health` و `/auth/login`) تتطلب JWT Token في Header:
        ```
        Authorization: Bearer <token>
        ```
        
        ## Rate Limiting
        - الحد الافتراضي: 100 طلب/دقيقة
        - تسجيل الدخول: 5 طلبات/دقيقة
        
        ## API Versioning
        جميع الـ endpoints تبدأ بـ `/api/v1/`
        """,
        routes=app.routes,
    )
    
    # إضافة معلومات إضافية
    openapi_schema["info"]["contact"] = {
        "name": "الإصدار المنطقي",
        "email": "support@example.com"
    }
    
    openapi_schema["info"]["license"] = {
        "name": "Proprietary"
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# تسجيل Routes (سيتم استيرادها من routes.py)
def register_routes():
    """تسجيل جميع Routes"""
    try:
        from src.api.routes import router
        app.include_router(router, prefix=API_PREFIX)
        logger.info(f"✅ تم تسجيل Routes بنجاح (prefix: {API_PREFIX})")
    except ImportError as e:
        print(f"DEBUG: ImportError loading routes: {e}")
        logger.warning(f"⚠️ لم يتم العثور على routes.py: {e}")
    except Exception as e:
        print(f"DEBUG: Exception loading routes: {e}")
        logger.error(f"❌ خطأ في تسجيل Routes: {e}")


register_routes()

# إعداد Middleware (بعد تهيئة الموارد)
@app.on_event("startup")
async def setup_middlewares():
    """إعداد Middlewares بعد تهيئة الموارد"""
    global db_manager, auth_manager, rate_limiter
    
    if db_manager and auth_manager and rate_limiter:
        # إعداد Middlewares
        setup_middleware(
            app=app,
            db_manager=db_manager,
            auth_manager=auth_manager,
            rate_limiter=rate_limiter,
            enable_cors=True,
            cors_origins=["*"]  # في الإنتاج، حدد الـ origins
        )
        logger.info("✅ تم إعداد Middlewares بنجاح")
    
    # Routes يتم تسجيلها في lifespan


# Exception Handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """معالج 404"""
    return JSONResponse(
        status_code=404,
        content={"detail": f"Endpoint غير موجود: {request.url.path}"}
    )


@app.get("/")
async def root():
    """Root endpoint for connection check"""
    import os
    db_path = db_manager.db_path if db_manager else "Unknown"
    size_mb = 0
    if isinstance(db_path, str) and os.path.exists(db_path):
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        
    return {
        "status": "Connected ✅",
        "database_file": os.path.basename(str(db_path)),
        "path": str(db_path),
        "size": f"{size_mb:.2f} MB",
        "api_version": API_VERSION
    }

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """معالج 500"""
    logger.error(f"Internal Server Error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "خطأ داخلي في الخادم"}
    )


def create_app(db_path: str = None) -> FastAPI:
    """
    إنشاء تطبيق FastAPI
    
    Args:
        db_path: مسار قاعدة البيانات (اختياري)
        
    Returns:
        تطبيق FastAPI
    """
    # إذا تم تحديد مسار قاعدة البيانات، قم بتحديثه
    if db_path:
        global db_manager
        db_manager = DatabaseManager(db_path=db_path)
    
    return app


# Export للاستخدام الخارجي
__all__ = ['app', 'create_app', 'API_VERSION', 'API_PREFIX']


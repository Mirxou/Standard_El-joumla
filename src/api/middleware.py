import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Middleware للـ REST API
Middleware for REST API
"""

import time
from typing import Callable, Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.api.auth import JWTAuthManager
from src.api.rate_limiter import APIRateLimiter
from src.core.database_manager import DatabaseManager
from src.utils.logger import setup_logger


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware للمصادقة"""

    def __init__(
        self,
        app: ASGIApp,
        auth_manager: JWTAuthManager,
        exclude_paths: Optional[list] = None,
    ):
        """
        تهيئة Auth Middleware

        Args:
            app: تطبيق FastAPI
            auth_manager: مدير JWT Authentication
            exclude_paths: قائمة المسارات المستثناة من المصادقة (مثل /health, /docs)
        """
        super().__init__(app)
        self.auth_manager = auth_manager
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
        ]
        self.logger = setup_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable):
        """معالجة الطلب"""
        # تخطي طلبات OPTIONS (preflight CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # التحقق من المسارات المستثناة
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # الحصول على Token من Header
        authorization = request.headers.get("Authorization")

        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="مطلوب مصادقة - يرجى إرسال Token في Header",
            )

        # استخراج Token
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="صيغة Token غير صحيحة - يجب أن تبدأ بـ 'Bearer '",
            )

        token = authorization.split(" ")[1]

        # التحقق من Token
        payload = self.auth_manager.verify_token(token, token_type="access")

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token غير صالح أو منتهي الصلاحية",
            )

        # إضافة بيانات المستخدم إلى Request
        request.state.user_id = str(payload.get("sub"))
        request.state.username = payload.get("username")
        request.state.company_id = payload.get("company_id")

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware لـ Rate Limiting"""

    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: APIRateLimiter,
        exclude_paths: Optional[list] = None,
    ):
        """
        تهيئة Rate Limit Middleware

        Args:
            app: تطبيق FastAPI
            rate_limiter: Rate Limiter
            exclude_paths: قائمة المسارات المستثناة من Rate Limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
        self.logger = setup_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable):
        """معالجة الطلب"""
        # التحقق من المسارات المستثناة
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # الحصول على IP Address
        ip_address = request.client.host if request.client else "unknown"

        # الحصول على User ID إذا كان متاحاً
        user_id = getattr(request.state, "user_id", None)

        # التحقق من Rate Limit
        is_allowed, remaining, retry_after = self.rate_limiter.is_allowed(
            ip_address=ip_address, endpoint=request.url.path, user_id=user_id
        )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="تم تجاوز الحد المسموح من الطلبات",
                headers={
                    "X-RateLimit-Limit": str(self.rate_limiter.default_max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after) if retry_after else "0",
                    "Retry-After": str(retry_after) if retry_after else "60",
                },
            )

        # إضافة Headers للاستجابة
        response = await call_next(request)

        # إضافة Rate Limit Headers
        max_requests, window_seconds = self.rate_limiter._get_limit(request.url.path)
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Window"] = str(window_seconds)

        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware لتسجيل الطلبات"""

    def __init__(self, app: ASGIApp, db_manager: Optional[DatabaseManager] = None):
        """
        تهيئة Logging Middleware

        Args:
            app: تطبيق FastAPI
            db_manager: مدير قاعدة البيانات (اختياري - لتسجيل في قاعدة البيانات)
        """
        super().__init__(app)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)

    async def dispatch(self, request: Request, call_next: Callable):
        """معالجة الطلب"""
        start_time = time.time()

        # معلومات الطلب
        method = request.method
        path = request.url.path
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")  # noqa: F841

        # تنفيذ الطلب
        try:
            response = await call_next(request)
        except Exception as e:
            # تسجيل الخطأ
            process_time = time.time() - start_time
            self.logger.error(f"API Error: {method} {path} - {ip_address} - {str(e)} - {process_time:.3f}s")
            raise

        # حساب وقت المعالجة
        process_time = time.time() - start_time

        # تسجيل الطلب
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)

        self.logger.info(
            f"API Request: {method} {path} - "
            f"IP: {ip_address} - "
            f"User: {username or 'anonymous'} ({user_id or 'N/A'}) - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        # إضافة Header لوقت المعالجة
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        # تسجيل في قاعدة البيانات (إذا كان متاحاً)
        if self.db_manager and user_id:
            try:
                self.db_manager.execute_query(
                    """
                    INSERT INTO api_logs
                    (method, path, ip_address, user_id, status_code, process_time, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        method,
                        path,
                        ip_address,
                        user_id,
                        response.status_code,
                        process_time,
                        time.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
            except Exception:
                # إذا فشل (ربما جدول api_logs غير موجود)، لا مشكلة
                logging.getLogger(__name__).warning("Ignored exception in middleware.py")

        return response


class CORSMiddleware(BaseHTTPMiddleware):
    """Middleware لـ CORS"""

    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Optional[list] = None,
        allow_methods: Optional[list] = None,
        allow_headers: Optional[list] = None,
    ):
        """
        تهيئة CORS Middleware

        Args:
            app: تطبيق FastAPI
            allow_origins: قائمة الـ Origins المسموحة
            allow_methods: قائمة الـ Methods المسموحة
            allow_headers: قائمة الـ Headers المسموحة
        """
        super().__init__(app)
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or [
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "OPTIONS",
        ]
        self.allow_headers = allow_headers or ["*"]

    async def dispatch(self, request: Request, call_next: Callable):
        """معالجة الطلب"""
        response = await call_next(request)

        # إضافة CORS Headers
        origin = request.headers.get("origin")

        if "*" in self.allow_origins or (origin and origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


def setup_middleware(
    app: ASGIApp,
    db_manager: DatabaseManager,
    auth_manager: JWTAuthManager,
    rate_limiter: APIRateLimiter,
    enable_cors: bool = True,
    cors_origins: Optional[list] = None,
):
    """
    إعداد جميع Middlewares

    Args:
        app: تطبيق FastAPI
        db_manager: مدير قاعدة البيانات
        auth_manager: مدير JWT Authentication
        rate_limiter: Rate Limiter
        enable_cors: تفعيل CORS
        cors_origins: قائمة الـ Origins المسموحة لـ CORS
    """
    from starlette.middleware.cors import CORSMiddleware as StarletteCORS

    # CORS Middleware (يجب أن يكون أولاً - قبل Auth)
    if enable_cors:
        app.add_middleware(
            StarletteCORS,
            allow_origins=cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Logging Middleware
    app.add_middleware(LoggingMiddleware, db_manager=db_manager)

    # Rate Limit Middleware
    app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

    # Auth Middleware (يجب أن يكون آخراً)
    app.add_middleware(AuthMiddleware, auth_manager=auth_manager)

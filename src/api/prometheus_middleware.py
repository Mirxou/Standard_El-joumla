import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prometheus Middleware for FastAPI
Middleware لـ Prometheus Metrics
"""

import time
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

# جعل import metrics optional
try:
    from src.api.metrics import (
        PROMETHEUS_AVAILABLE,
        record_api_error,
        record_http_request,
        set_active_requests,
    )
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Stub functions
    def record_http_request(*args, **kwargs):
        pass

    def record_api_error(*args, **kwargs):
        pass

    def set_active_requests(*args, **kwargs):
        pass


logger = logging.getLogger(__name__)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware لتتبع Metrics في Prometheus"""

    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        """
        تهيئة Prometheus Middleware

        Args:
            app: تطبيق FastAPI
            exclude_paths: قائمة المسارات المستثناة من Metrics (مثل /metrics, /health)
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/metrics",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        self._active_requests = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """معالجة الطلب وتسجيل Metrics"""

        # تخطي المسارات المستثناة
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # زيادة عدد الطلبات النشطة
        self._active_requests += 1
        if PROMETHEUS_AVAILABLE:
            set_active_requests(self._active_requests)

        # تسجيل وقت البداية
        start_time = time.time()

        # معلومات الطلب
        method = request.method
        endpoint = self._normalize_endpoint(request.url.path)

        try:
            # تنفيذ الطلب
            response = await call_next(request)

            # حساب مدة المعالجة
            duration = time.time() - start_time

            # تسجيل Metrics
            status_code = response.status_code
            if PROMETHEUS_AVAILABLE:
                record_http_request(
                    method=method,
                    endpoint=endpoint,
                    status_code=status_code,
                    duration=duration,
                )

                # تسجيل الأخطاء
                if status_code >= 400:
                    error_type = str(status_code)
                    record_api_error(error_type=error_type, endpoint=endpoint)

            return response

        except Exception as e:
            # حساب مدة المعالجة حتى في حالة الخطأ
            duration = time.time() - start_time

            # تسجيل الخطأ
            if PROMETHEUS_AVAILABLE:
                error_type = "500"
                record_api_error(error_type=error_type, endpoint=endpoint)
                record_http_request(method=method, endpoint=endpoint, status_code=500, duration=duration)

            logger.log(logging.ERROR, f"API Error in PrometheusMiddleware: {e}")
            raise

        finally:
            # تقليل عدد الطلبات النشطة
            self._active_requests -= 1
            if PROMETHEUS_AVAILABLE:
                set_active_requests(max(0, self._active_requests))

    def _normalize_endpoint(self, path: str) -> str:
        """
        تطبيع endpoint لإزالة المعاملات الديناميكية

        Examples:
            /api/v1/products/123 -> /api/v1/products/{id}
            /api/v1/products/123/items/456 -> /api/v1/products/{id}/items/{id}
        """
        # قائمة الأنماط الشائعة
        import re

        # استبدال الأرقام بـ {id}
        normalized = re.sub(r"/\d+", "/{id}", path)

        # استبدال UUIDs بـ {uuid}
        normalized = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{uuid}",
            normalized,
            flags=re.IGNORECASE,
        )

        return normalized

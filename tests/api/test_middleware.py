#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for API Middleware
اختبارات وحدة لـ Middleware API
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi import Request, HTTPException, status
from starlette.responses import JSONResponse
import sys
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.middleware import AuthMiddleware, RateLimitMiddleware, LoggingMiddleware
from src.api.auth import JWTAuthManager
from src.api.rate_limiter import APIRateLimiter


class TestAuthMiddleware:
    """اختبارات Auth Middleware"""
    
    @pytest.fixture
    def auth_manager(self):
        """إنشاء Auth Manager للاختبارات"""
        db_manager = Mock()
        return JWTAuthManager(db_manager, secret_key="test-secret-key")
    
    @pytest.fixture
    def middleware(self, auth_manager):
        """إنشاء Auth Middleware للاختبارات"""
        app = Mock()
        return AuthMiddleware(app, auth_manager)
    
    @pytest.fixture
    def mock_request(self):
        """إنشاء Mock Request"""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/products"
        request.headers = {}
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    async def test_auth_middleware_public_endpoints(self, middleware, mock_request):
        """اختبار أن الـ endpoints العامة لا تحتاج مصادقة"""
        mock_request.url.path = "/health"
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_auth_middleware_no_token(self, middleware, mock_request):
        """اختبار Middleware بدون Token"""
        mock_request.headers = {}
        
        call_next = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auth_middleware_invalid_token(self, middleware, mock_request, auth_manager):
        """اختبار Middleware مع Token غير صالح"""
        mock_request.headers = {"Authorization": "Bearer invalid.token.here"}
        
        call_next = AsyncMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        call_next.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_auth_middleware_valid_token(self, middleware, mock_request, auth_manager):
        """اختبار Middleware مع Token صالح"""
        # إنشاء Token صالح
        token = auth_manager.create_access_token(1, "test_user", 1)
        mock_request.headers = {"Authorization": f"Bearer {token}"}
        
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert hasattr(mock_request.state, 'user_id')
        assert mock_request.state.user_id == "1"
        assert mock_request.state.username == "test_user"
        assert mock_request.state.company_id == 1


class TestRateLimitMiddleware:
    """اختبارات Rate Limit Middleware"""
    
    @pytest.fixture
    def rate_limiter(self):
        """إنشاء Rate Limiter للاختبارات"""
        return APIRateLimiter(default_max_requests=5, default_window_seconds=60)
    
    @pytest.fixture
    def middleware(self, rate_limiter):
        """إنشاء Rate Limit Middleware للاختبارات"""
        app = Mock()
        return RateLimitMiddleware(app, rate_limiter)
    
    @pytest.fixture
    def mock_request(self):
        """إنشاء Mock Request"""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/products"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_public_endpoints(self, middleware, mock_request):
        """اختبار أن الـ endpoints العامة لا تخضع لـ Rate Limit"""
        mock_request.url.path = "/health"
        
        call_next = AsyncMock(return_value=JSONResponse({"status": "ok"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_allowed(self, middleware, mock_request):
        """اختبار Rate Limit Middleware مع طلب مسموح"""
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_exceeded(self, middleware, mock_request):
        """اختبار Rate Limit Middleware مع تجاوز الحد"""
        # إرسال 5 طلبات (الحد الأقصى)
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        for i in range(5):
            response = await middleware.dispatch(mock_request, call_next)
            assert response.status_code == 200
        
        # الطلب السادس يجب أن يفشل
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(mock_request, call_next)
        
        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware_with_user_id(self, middleware, mock_request):
        """اختبار Rate Limit Middleware مع معرف مستخدم"""
        mock_request.state.user_id = 1
        
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert response.status_code == 200


class TestLoggingMiddleware:
    """اختبارات Logging Middleware"""
    
    @pytest.fixture
    def middleware(self):
        """إنشاء Logging Middleware للاختبارات"""
        app = Mock()
        return LoggingMiddleware(app)
    
    @pytest.fixture
    def mock_request(self):
        """إنشاء Mock Request"""
        request = Mock(spec=Request)
        request.url.path = "/api/v1/products"
        request.method = "GET"
        request.client = Mock()
        request.client.host = "127.0.0.1"
        request.state = Mock()
        return request
    
    @pytest.mark.asyncio
    async def test_logging_middleware(self, middleware, mock_request):
        """اختبار Logging Middleware"""
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        response = await middleware.dispatch(mock_request, call_next)
        
        call_next.assert_called_once()
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_logging_middleware_logs_request(self, middleware, mock_request):
        """اختبار أن Logging Middleware يسجل الطلبات"""
        call_next = AsyncMock(return_value=JSONResponse({"data": "test"}))
        
        with patch.object(middleware.logger, 'info') as mock_log:
            response = await middleware.dispatch(mock_request, call_next)
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "API Request" in log_message
            assert "/api/v1/products" in log_message
            assert "GET" in log_message



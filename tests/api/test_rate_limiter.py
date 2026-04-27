#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for API Rate Limiter
اختبارات وحدة لمحدود معدل API
"""

import pytest
from unittest.mock import Mock, patch
import time
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.api.rate_limiter import APIRateLimiter


class TestAPIRateLimiter:
    """اختبارات API Rate Limiter"""
    
    @pytest.fixture
    def rate_limiter(self):
        """إنشاء Rate Limiter للاختبارات"""
        return APIRateLimiter(
            default_max_requests=10,
            default_window_seconds=60
        )
    
    def test_rate_limiter_init(self, rate_limiter):
        """اختبار تهيئة Rate Limiter"""
        assert rate_limiter is not None
        assert rate_limiter.default_max_requests == 10
        assert rate_limiter.default_window_seconds == 60
    
    def test_is_allowed_first_request(self, rate_limiter):
        """اختبار السماح بالطلب الأول"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        
        assert allowed is True
        assert remaining == 9  # 10 - 1
        assert retry_after == 0
    
    def test_is_allowed_multiple_requests(self, rate_limiter):
        """اختبار السماح بعدة طلبات"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        # إرسال 5 طلبات
        for i in range(5):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
            assert allowed is True
            assert remaining == 9 - i
        
        # الطلب السادس
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        assert allowed is True
        assert remaining == 4
    
    def test_is_allowed_rate_limit_exceeded(self, rate_limiter):
        """اختبار تجاوز حد الطلبات"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        # إرسال 10 طلبات (الحد الأقصى)
        for i in range(10):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
            assert allowed is True
        
        # الطلب الحادي عشر (يجب أن يفشل)
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        assert allowed is False
        assert retry_after > 0
    
    def test_is_allowed_different_endpoints(self, rate_limiter):
        """اختبار السماح بطلبات مختلفة لكل endpoint"""
        ip_address = "127.0.0.1"
        endpoint1 = "/api/v1/products"
        endpoint2 = "/api/v1/sales"
        
        # إرسال 10 طلبات إلى endpoint1
        for i in range(10):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint1)
            assert allowed is True
        
        # endpoint1 يجب أن يكون محظوراً
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint1)
        assert allowed is False
        
        # endpoint2 يجب أن يكون مسموحاً (حد منفصل)
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint2)
        assert allowed is True
        assert remaining == 9
    
    def test_is_allowed_different_ips(self, rate_limiter):
        """اختبار السماح بطلبات مختلفة لكل IP"""
        ip1 = "127.0.0.1"
        ip2 = "192.168.1.1"
        endpoint = "/api/v1/products"
        
        # إرسال 10 طلبات من IP1
        for i in range(10):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip1, endpoint)
            assert allowed is True
        
        # IP1 يجب أن يكون محظوراً
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip1, endpoint)
        assert allowed is False
        
        # IP2 يجب أن يكون مسموحاً (حد منفصل)
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip2, endpoint)
        assert allowed is True
        assert remaining == 9
    
    def test_is_allowed_with_user_id(self, rate_limiter):
        """اختبار السماح بطلبات مع معرف مستخدم"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        user_id = 1
        
        # إرسال 10 طلبات
        for i in range(10):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint, user_id=user_id)
            assert allowed is True
        
        # الطلب الحادي عشر
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint, user_id=user_id)
        assert allowed is False
    
    def test_reset(self, rate_limiter):
        """اختبار إعادة تعيين Rate Limit"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        # إرسال 10 طلبات
        for i in range(10):
            rate_limiter.is_allowed(ip_address, endpoint)
        
        # التحقق من الحظر
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        assert allowed is False
        
        # إعادة التعيين
        rate_limiter.reset(ip_address, endpoint)
        
        # يجب أن يكون مسموحاً مرة أخرى
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        assert allowed is True
        assert remaining == 9
    
    def test_reset_all_endpoints(self, rate_limiter):
        """اختبار إعادة تعيين جميع Endpoints"""
        ip_address = "127.0.0.1"
        endpoint1 = "/api/v1/products"
        endpoint2 = "/api/v1/sales"
        
        # إرسال طلبات إلى endpoint1
        for i in range(10):
            rate_limiter.is_allowed(ip_address, endpoint1)
        
        # إرسال طلبات إلى endpoint2
        for i in range(5):
            rate_limiter.is_allowed(ip_address, endpoint2)
        
        # إعادة التعيين لجميع Endpoints
        rate_limiter.reset(ip_address)
        
        # يجب أن يكون كلاهما مسموحاً
        allowed1, remaining1, retry_after1 = rate_limiter.is_allowed(ip_address, endpoint1)
        allowed2, remaining2, retry_after2 = rate_limiter.is_allowed(ip_address, endpoint2)
        
        assert allowed1 is True
        assert allowed2 is True
        assert remaining1 == 9
        assert remaining2 == 9
    
    def test_get_stats(self, rate_limiter):
        """اختبار الحصول على إحصائيات Rate Limit"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        # إرسال 5 طلبات
        for i in range(5):
            rate_limiter.is_allowed(ip_address, endpoint)
        
        stats = rate_limiter.get_stats(ip_address, endpoint)
        
        assert stats is not None
        assert "total_requests" in stats
        assert "endpoints" in stats
        assert stats["total_requests"] == 5
        assert endpoint in stats["endpoints"]
        assert stats["endpoints"][endpoint] == 5
    
    def test_cleanup_old_entries(self, rate_limiter):
        """اختبار تنظيف الإدخالات القديمة"""
        ip_address = "127.0.0.1"
        endpoint = "/api/v1/products"
        
        # إرسال طلب
        rate_limiter.is_allowed(ip_address, endpoint)
        
        # تنظيف الإدخالات الأقدم من ساعة (يجب أن يحذف الطلب الحالي)
        rate_limiter.cleanup_old_entries(max_age_hours=0)  # تنظيف فوري
        
        # يجب أن يكون مسموحاً مرة أخرى
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, endpoint)
        assert allowed is True
        assert remaining == 9
    
    def test_per_endpoint_limits(self):
        """اختبار الحدود المخصصة لكل endpoint"""
        rate_limiter = APIRateLimiter(
            default_max_requests=10,
            default_window_seconds=60,
            per_endpoint_limits={
                "/api/v1/auth/login": {"max_requests": 5, "window_seconds": 60}
            }
        )
        
        ip_address = "127.0.0.1"
        login_endpoint = "/api/v1/auth/login"
        products_endpoint = "/api/v1/products"
        
        # إرسال 5 طلبات إلى login endpoint (الحد المخصص)
        for i in range(5):
            allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, login_endpoint)
            assert allowed is True
        
        # الطلب السادس يجب أن يفشل
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, login_endpoint)
        assert allowed is False
        
        # products endpoint يجب أن يكون مسموحاً (يستخدم الحد الافتراضي)
        allowed, remaining, retry_after = rate_limiter.is_allowed(ip_address, products_endpoint)
        assert allowed is True
        assert remaining == 9







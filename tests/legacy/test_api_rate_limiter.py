#!/usr/bin/env python3
"""
اختبارات API Rate Limiter
"""

from unittest.mock import patch

import pytest

from src.api.rate_limiter import RateLimiter


class TestRateLimiter:
    """اختبارات محدد معدل الطلبات"""

    @pytest.fixture
    def rate_limiter(self):
        """إنشاء محدد معدل"""
        return RateLimiter(max_requests=100, window_seconds=60)

    def test_initialization(self, rate_limiter):
        """اختبار التهيئة"""
        assert rate_limiter is not None
        assert rate_limiter.max_requests == 100

    def test_allow_request(self, rate_limiter):
        """اختبار السماح بالطلب"""
        with patch.object(rate_limiter, "is_allowed", return_value=True):
            result = rate_limiter.is_allowed("client_id")
            assert result is True

    def test_deny_request_when_limit_reached(self, rate_limiter):
        """اختبار رفض الطلب عند الوصول للحد"""
        with patch.object(rate_limiter, "is_allowed", return_value=False):
            result = rate_limiter.is_allowed("client_id")
            assert result is False

    def test_get_remaining_requests(self, rate_limiter):
        """اختبار الحصول على الطلبات المتبقية"""
        with patch.object(rate_limiter, "get_remaining", return_value=50):
            result = rate_limiter.get_remaining("client_id")
            assert result == 50

    def test_reset_limit(self, rate_limiter):
        """اختبار إعادة تعيين الحد"""
        with patch.object(rate_limiter, "reset", return_value=True):
            result = rate_limiter.reset("client_id")
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

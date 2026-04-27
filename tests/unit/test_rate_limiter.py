"""
Unit Tests for RateLimiter
اختبارات وحدة RateLimiter
"""

import pytest
import time
from src.security.rate_limiter import RateLimiter


class TestRateLimiter:
    """اختبارات RateLimiter"""
    
    @pytest.fixture
    def rate_limiter(self):
        """إنشاء RateLimiter"""
        return RateLimiter(max_requests=5, window_seconds=60)
    
    def test_init(self, rate_limiter):
        """اختبار التهيئة"""
        assert rate_limiter.max_requests == 5
        assert rate_limiter.window.total_seconds() == 60
    
    def test_is_allowed_first_request(self, rate_limiter):
        """اختبار السماح بالطلب الأول"""
        is_allowed, remaining = rate_limiter.is_allowed("test_ip")
        
        assert is_allowed is True
        assert remaining == 4
    
    def test_is_allowed_multiple_requests(self, rate_limiter):
        """اختبار عدة طلبات"""
        identifier = "test_ip"
        
        for i in range(5):
            is_allowed, remaining = rate_limiter.is_allowed(identifier)
            assert is_allowed is True
            assert remaining == (4 - i)
        
        # الطلب السادس يجب أن يُرفض
        is_allowed, remaining = rate_limiter.is_allowed(identifier)
        assert is_allowed is False
        assert remaining == 0
    
    def test_reset(self, rate_limiter):
        """اختبار إعادة تعيين Rate Limit"""
        identifier = "test_ip"
        
        # الوصول للحد الأقصى
        for _ in range(5):
            rate_limiter.is_allowed(identifier)
        
        # التحقق من الرفض
        is_allowed, _ = rate_limiter.is_allowed(identifier)
        assert is_allowed is False
        
        # إعادة التعيين
        rate_limiter.reset(identifier)
        
        # التحقق من السماح مرة أخرى
        is_allowed, remaining = rate_limiter.is_allowed(identifier)
        assert is_allowed is True
        assert remaining == 4
    
    def test_different_identifiers(self, rate_limiter):
        """اختبار معرّفات مختلفة"""
        # كل معرّف له حد منفصل
        is_allowed1, _ = rate_limiter.is_allowed("ip1")
        is_allowed2, _ = rate_limiter.is_allowed("ip2")
        
        assert is_allowed1 is True
        assert is_allowed2 is True
    
    def test_cleanup_old_entries(self, rate_limiter):
        """اختبار تنظيف المدخلات القديمة"""
        identifier = "test_ip"
        
        # إضافة طلبات
        for _ in range(3):
            rate_limiter.is_allowed(identifier)
        
        # تنظيف المدخلات القديمة (أقل من ساعة)
        rate_limiter.cleanup_old_entries(hours=1)
        
        # يجب أن تبقى الطلبات لأنها حديثة
        is_allowed, remaining = rate_limiter.is_allowed(identifier)
        assert is_allowed is True
    
    def test_window_expiration(self):
        """اختبار انتهاء نافذة الوقت"""
        # إنشاء RateLimiter بنافذة صغيرة للاختبار
        limiter = RateLimiter(max_requests=3, window_seconds=1)
        identifier = "test_ip"
        
        # الوصول للحد الأقصى
        for _ in range(3):
            limiter.is_allowed(identifier)
        
        # التحقق من الرفض
        is_allowed, _ = limiter.is_allowed(identifier)
        assert is_allowed is False
        
        # الانتظار حتى تنتهي النافذة
        time.sleep(1.1)
        
        # يجب السماح مرة أخرى
        is_allowed, remaining = limiter.is_allowed(identifier)
        assert is_allowed is True
        assert remaining == 2





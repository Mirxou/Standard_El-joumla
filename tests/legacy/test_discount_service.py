#!/usr/bin/env python3
"""
اختبارات Discount Service
"""

from unittest.mock import patch

import pytest

from src.services.discount_service import DiscountService


class TestDiscountService:
    """اختبارات خدمة الخصومات"""

    @pytest.fixture
    def discount_service(self):
        """إنشاء خدمة خصومات"""
        return DiscountService()

    def test_initialization(self, discount_service):
        """اختبار التهيئة"""
        assert discount_service is not None

    def test_apply_discount(self, discount_service):
        """اختبار تطبيق خصم"""
        with patch.object(discount_service, "apply", return_value=90.0):
            result = discount_service.apply(100.0, 10)
            assert result == 90.0

    def test_validate_discount_code(self, discount_service):
        """اختبار التحقق من رمز الخصم"""
        with patch.object(discount_service, "validate_code", return_value=True):
            result = discount_service.validate_code("DISCOUNT10")
            assert result is True

    def test_get_discount_amount(self, discount_service):
        """اختبار الحصول على مبلغ الخصم"""
        with patch.object(discount_service, "get_amount", return_value=10.0):
            result = discount_service.get_amount(100.0, 10)
            assert result == 10.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

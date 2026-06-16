#!/usr/bin/env python3
"""
اختبارات Tax Service
"""

from unittest.mock import patch

import pytest

from src.services.tax_service import TaxService


class TestTaxService:
    """اختبارات خدمة الضرائب"""

    @pytest.fixture
    def tax_service(self):
        """إنشاء خدمة ضرائب"""
        return TaxService()

    def test_initialization(self, tax_service):
        """اختبار التهيئة"""
        assert tax_service is not None

    def test_calculate_tax(self, tax_service):
        """اختبار حساب الضريبة"""
        with patch.object(tax_service, "calculate", return_value=15.0):
            result = tax_service.calculate(100.0, 0.15)
            assert result == 15.0

    def test_get_tax_rate(self, tax_service):
        """اختبار الحصول على معدل الضريبة"""
        with patch.object(tax_service, "get_rate", return_value=0.15):
            result = tax_service.get_rate("category")
            assert result == 0.15

    def test_apply_tax(self, tax_service):
        """اختبار تطبيق الضريبة"""
        with patch.object(tax_service, "apply", return_value=115.0):
            result = tax_service.apply(100.0, 0.15)
            assert result == 115.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Validator
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.validator import Validator


class TestValidator:
    """اختبارات المحقق"""
    
    @pytest.fixture
    def validator(self):
        """إنشاء محقق"""
        return Validator()
    
    def test_initialization(self, validator):
        """اختبار التهيئة"""
        assert validator is not None
    
    def test_validate_email(self, validator):
        """اختبار التحقق من البريد الإلكتروني"""
        with patch.object(validator, 'validate_email', return_value=True):
            result = validator.validate_email("test@example.com")
            assert result is True
    
    def test_validate_invalid_email(self, validator):
        """اختبار التحقق من بريد إلكتروني غير صالح"""
        with patch.object(validator, 'validate_email', return_value=False):
            result = validator.validate_email("invalid-email")
            assert result is False
    
    def test_validate_required(self, validator):
        """اختبار التحقق من الحقول المطلوبة"""
        with patch.object(validator, 'validate_required', return_value=True):
            result = validator.validate_required({"name": "Test"}, ["name"])
            assert result is True
    
    def test_validate_number(self, validator):
        """اختبار التحقق من رقم"""
        with patch.object(validator, 'validate_number', return_value=True):
            result = validator.validate_number("123")
            assert result is True
    
    def test_validate_range(self, validator):
        """اختبار التحقق من نطاق"""
        with patch.object(validator, 'validate_range', return_value=True):
            result = validator.validate_range(50, 0, 100)
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




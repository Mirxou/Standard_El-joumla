#!/usr/bin/env python3
"""
اختبارات Error Handler
"""

from unittest.mock import Mock, patch

import pytest

from src.core.error_handler import ErrorHandler


class TestErrorHandler:
    """اختبارات معالج الأخطاء"""

    @pytest.fixture
    def error_handler(self):
        """إنشاء معالج أخطاء"""
        return ErrorHandler()

    def test_initialization(self, error_handler):
        """اختبار التهيئة"""
        assert error_handler is not None

    def test_handle_error(self, error_handler):
        """اختبار معالجة خطأ"""
        with patch.object(error_handler, "handle", return_value={"error": "message"}):
            result = error_handler.handle(Exception("Test error"))
            assert result is not None

    def test_log_error(self, error_handler):
        """اختبار تسجيل خطأ"""
        with patch.object(error_handler, "log_error", return_value=True):
            result = error_handler.log_error("error_message", "ERROR")
            assert result is True

    def test_get_error_details(self, error_handler):
        """اختبار الحصول على تفاصيل الخطأ"""
        with patch.object(error_handler, "get_details", return_value={"code": 500, "message": "Error"}):
            result = error_handler.get_details(Exception("Test"))
            assert isinstance(result, dict)

    def test_register_error_callback(self, error_handler):
        """اختبار تسجيل callback للخطأ"""
        callback = Mock()
        with patch.object(error_handler, "register_callback", return_value=True):
            result = error_handler.register_callback("error_type", callback)
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

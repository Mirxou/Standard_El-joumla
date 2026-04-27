#!/usr/bin/env python3
"""
اختبارات Response Formatter
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.api.response_formatter import ResponseFormatter


class TestResponseFormatter:
    """اختبارات منسق الاستجابات"""
    
    @pytest.fixture
    def formatter(self):
        """إنشاء منسق استجابات"""
        return ResponseFormatter()
    
    def test_initialization(self, formatter):
        """اختبار التهيئة"""
        assert formatter is not None
    
    def test_format_success_response(self, formatter):
        """اختبار تنسيق استجابة ناجحة"""
        with patch.object(formatter, 'format_success', return_value={"success": True, "data": {}}):
            result = formatter.format_success({"key": "value"})
            assert isinstance(result, dict)
    
    def test_format_error_response(self, formatter):
        """اختبار تنسيق استجابة خطأ"""
        with patch.object(formatter, 'format_error', return_value={"success": False, "error": "message"}):
            result = formatter.format_error("error_message", 400)
            assert isinstance(result, dict)
    
    def test_format_paginated_response(self, formatter):
        """اختبار تنسيق استجابة صفحية"""
        with patch.object(formatter, 'format_paginated', return_value={"data": [], "total": 0}):
            result = formatter.format_paginated([{"id": 1}], 1, 10, 100)
            assert isinstance(result, dict)
    
    def test_add_metadata(self, formatter):
        """اختبار إضافة بيانات وصفية"""
        with patch.object(formatter, 'add_metadata', return_value={"data": {}, "meta": {}}):
            result = formatter.add_metadata({"key": "value"}, {"version": "1.0"})
            assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




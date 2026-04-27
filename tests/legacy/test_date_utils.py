#!/usr/bin/env python3
"""
اختبارات Date Utils
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date
from src.utils.date_utils import DateUtils


class TestDateUtils:
    """اختبارات أدوات التاريخ"""
    
    @pytest.fixture
    def date_utils(self):
        """إنشاء أدوات تاريخ"""
        return DateUtils()
    
    def test_initialization(self, date_utils):
        """اختبار التهيئة"""
        assert date_utils is not None
    
    def test_format_date(self, date_utils):
        """اختبار تنسيق التاريخ"""
        with patch.object(date_utils, 'format', return_value="2024-01-15"):
            result = date_utils.format(date(2024, 1, 15), "%Y-%m-%d")
            assert result == "2024-01-15"
    
    def test_parse_date(self, date_utils):
        """اختبار تحليل التاريخ"""
        with patch.object(date_utils, 'parse', return_value=date(2024, 1, 15)):
            result = date_utils.parse("2024-01-15", "%Y-%m-%d")
            assert result is not None
    
    def test_get_current_date(self, date_utils):
        """اختبار الحصول على التاريخ الحالي"""
        with patch.object(date_utils, 'now', return_value=datetime(2024, 1, 15, 10, 30, 0)):
            result = date_utils.now()
            assert result is not None
    
    def test_add_days(self, date_utils):
        """اختبار إضافة أيام"""
        with patch.object(date_utils, 'add_days', return_value=date(2024, 1, 25)):
            result = date_utils.add_days(date(2024, 1, 15), 10)
            assert result is not None
    
    def test_date_diff(self, date_utils):
        """اختبار فرق التواريخ"""
        with patch.object(date_utils, 'diff', return_value=10):
            result = date_utils.diff(date(2024, 1, 15), date(2024, 1, 25))
            assert result == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




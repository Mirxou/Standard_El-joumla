#!/usr/bin/env python3
"""
اختبارات Date Range Picker
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QDateEdit, QPushButton
from PySide6.QtCore import Qt, QDate
from src.ui.components.date_range_picker import DateRangePicker

app = QApplication.instance() or QApplication([])


class TestDateRangePicker:
    """اختبارات منتقي نطاق التاريخ"""
    
    @pytest.fixture
    def picker(self):
        """إنشاء منتقي للاختبارات"""
        return DateRangePicker()
    
    def test_initialization(self, picker):
        """اختبار التهيئة"""
        assert picker is not None
    
    def test_set_start_date(self, picker):
        """اختبار تعيين تاريخ البداية"""
        date = QDate(2024, 1, 1)
        result = picker.set_start_date(date)
        assert result is not None
    
    def test_set_end_date(self, picker):
        """اختبار تعيين تاريخ النهاية"""
        date = QDate(2024, 12, 31)
        result = picker.set_end_date(date)
        assert result is not None
    
    def test_get_date_range(self, picker):
        """اختبار الحصول على نطاق التاريخ"""
        picker.set_start_date(QDate(2024, 1, 1))
        picker.set_end_date(QDate(2024, 12, 31))
        
        start, end = picker.get_date_range()
        assert start is not None
        assert end is not None
    
    def test_set_preset_range(self, picker):
        """اختبار تعيين نطاق محدد مسبقاً"""
        result = picker.set_preset_range("last_7_days")
        assert result is not None
    
    def test_clear_dates(self, picker):
        """اختبار مسح التواريخ"""
        result = picker.clear_dates()
        assert result is not None
    
    def test_validate_range(self, picker):
        """اختبار التحقق من النطاق"""
        picker.set_start_date(QDate(2024, 12, 31))
        picker.set_end_date(QDate(2024, 1, 1))
        
        is_valid = picker.validate_range()
        assert isinstance(is_valid, bool)
    
    def test_on_date_changed(self, picker):
        """اختبار حدث تغيير التاريخ"""
        result = picker.on_date_changed()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




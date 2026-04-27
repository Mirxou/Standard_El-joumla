#!/usr/bin/env python3
"""
اختبارات Pivot Table
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget, QPushButton, QComboBox
from PySide6.QtCore import Qt
from src.ui.components.bi.pivot_table import PivotTable

app = QApplication.instance() or QApplication([])


class TestPivotTable:
    """اختبارات الجدول المحوري"""
    
    @pytest.fixture
    def pivot(self):
        """إنشاء جدول محوري للاختبارات"""
        return PivotTable()
    
    def test_initialization(self, pivot):
        """اختبار التهيئة"""
        assert pivot is not None
    
    def test_set_source_data(self, pivot):
        """اختبار تعيين البيانات المصدر"""
        data = [
            {"product": "A", "region": "North", "sales": 100},
            {"product": "B", "region": "South", "sales": 200}
        ]
        result = pivot.set_source_data(data)
        assert result is not None
    
    def test_set_row_fields(self, pivot):
        """اختبار تعيين حقول الصفوف"""
        result = pivot.set_row_fields(["product", "region"])
        assert result is not None
    
    def test_set_column_fields(self, pivot):
        """اختبار تعيين حقول الأعمدة"""
        result = pivot.set_column_fields(["region"])
        assert result is not None
    
    def test_set_data_fields(self, pivot):
        """اختبار تعيين حقول البيانات"""
        result = pivot.set_data_fields([{"field": "sales", "aggregation": "sum"}])
        assert result is not None
    
    def test_generate_pivot(self, pivot):
        """اختبار توليد الجدول المحوري"""
        result = pivot.generate_pivot()
        assert result is not None
    
    def test_clear_pivot(self, pivot):
        """اختبار مسح الجدول المحوري"""
        result = pivot.clear_pivot()
        assert result is not None
    
    def test_export_to_excel(self, pivot):
        """اختبار التصدير إلى Excel"""
        result = pivot.export_to_excel("pivot.xlsx")
        assert result is not None
    
    def test_get_pivot_data(self, pivot):
        """اختبار الحصول على بيانات الجدول المحوري"""
        data = pivot.get_pivot_data()
        assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
"""
اختبارات Data Table
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QPushButton
from PySide6.QtCore import Qt
from src.ui.components.data_table import DataTable

app = QApplication.instance() or QApplication([])


class TestDataTable:
    """اختبارات جدول البيانات"""
    
    @pytest.fixture
    def table(self):
        """إنشاء جدول للاختبارات"""
        return DataTable()
    
    def test_initialization(self, table):
        """اختبار التهيئة"""
        assert table is not None
    
    def test_set_headers(self, table):
        """اختبار تعيين العناوين"""
        headers = ["Name", "Age", "City"]
        result = table.set_headers(headers)
        assert result is not None
    
    def test_add_row(self, table):
        """اختبار إضافة صف"""
        row = ["John", "30", "NYC"]
        result = table.add_row(row)
        assert result is not None
    
    def test_remove_row(self, table):
        """اختبار إزالة صف"""
        table.add_row(["John", "30", "NYC"])
        result = table.remove_row(0)
        assert result is not None
    
    def test_get_selected_rows(self, table):
        """اختبار الحصول على الصفوف المحددة"""
        rows = table.get_selected_rows()
        assert isinstance(rows, list)
    
    def test_clear_data(self, table):
        """اختبار مسح البيانات"""
        table.add_row(["John", "30", "NYC"])
        result = table.clear_data()
        assert result is not None
    
    def test_set_sortable(self, table):
        """اختبار تعيين إمكانية الترتيب"""
        result = table.set_sortable(True)
        assert result is not None
    
    def test_export_to_csv(self, table):
        """اختبار التصدير إلى CSV"""
        result = table.export_to_csv("data.csv")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




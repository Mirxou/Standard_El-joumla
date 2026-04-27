#!/usr/bin/env python3
"""
اختبارات Reports Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QPushButton
from PySide6.QtCore import Qt
from src.ui.windows.reports_window import ReportsWindow

app = QApplication.instance() or QApplication([])


class TestReportsWindow:
    """اختبارات نافذة التقارير"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        db_manager = Mock()
        return ReportsWindow(db_manager)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_generate_sales_report(self, window):
        """اختبار توليد تقرير المبيعات"""
        result = window.generate_sales_report("2024-01-01", "2024-12-31")
        assert result is not None
    
    def test_generate_inventory_report(self, window):
        """اختبار توليد تقرير المخزون"""
        result = window.generate_inventory_report()
        assert result is not None
    
    def test_generate_profit_report(self, window):
        """اختبار توليد تقرير الأرباح"""
        result = window.generate_profit_report("2024-01-01", "2024-12-31")
        assert result is not None
    
    def test_export_report(self, window):
        """اختبار تصدير التقرير"""
        result = window.export_report("pdf", "report.pdf")
        assert result is not None
    
    def test_print_report(self, window):
        """اختبار طباعة التقرير"""
        result = window.print_report()
        assert result is not None
    
    def test_preview_report(self, window):
        """اختبار معاينة التقرير"""
        result = window.preview_report()
        assert result is not None
    
    def test_set_date_range(self, window):
        """اختبار تعيين نطاق التاريخ"""
        result = window.set_date_range("2024-01-01", "2024-12-31")
        assert result is not None
    
    def test_refresh_report(self, window):
        """اختبار تحديث التقرير"""
        result = window.refresh_report()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




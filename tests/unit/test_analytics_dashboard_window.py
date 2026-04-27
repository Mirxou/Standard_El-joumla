#!/usr/bin/env python3
"""
اختبارات Analytics Dashboard Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.analytics_dashboard_window import AnalyticsDashboardWindow

app = QApplication.instance() or QApplication([])


class TestAnalyticsDashboardWindow:
    """اختبارات نافذة لوحة تحليلات"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            return AnalyticsDashboardWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_default_analytics(self, window):
        """اختبار تحميل بيانات لوحة التحكم"""
        window.load_default_analytics()
    
    def test_load_sales_analytics(self, window):
        """اختبار تحميل تحليلات المبيعات"""
        from datetime import datetime
        window.load_sales_analytics(datetime.now(), datetime.now())
    
    def test_load_inventory_analytics(self, window):
        """اختبار تحميل تحليلات المخزون"""
        window.load_inventory_analytics()
    
    def test_load_financial_analytics(self, window):
        """اختبار تحميل التحليلات المالية"""
        from datetime import datetime
        window.load_financial_analytics(datetime.now(), datetime.now())
    
    def test_export_data(self, window):
        """اختبار تصدير البيانات"""
        # We don't want to open a real file dialog, so we might need to mock it
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=("", "")):
            window.export_data()
    
    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        window.refresh_data()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




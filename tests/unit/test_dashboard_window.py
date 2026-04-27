#!/usr/bin/env python3
"""
اختبارات Dashboard Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.dashboard_window import DashboardWindow

app = QApplication.instance() or QApplication([])


class TestDashboardWindow:
    """اختبارات نافذة لوحة التحكم"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config, \
             patch('src.ui.windows.dashboard_window.DashboardService') as mock_service_class:
            
            mock_config.return_value.get.return_value = {}
            
            # Setup mock data return from service
            mock_data = MagicMock()
            mock_data.kpis = []
            mock_data.sales_series = []
            mock_service_class.return_value.load_dashboard.return_value = mock_data
            mock_service_class.return_value.list_categories.return_value = []
            
            mock_db = MagicMock()
            mock_db.db_path = ":memory:"
            
            return DashboardWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_dashboard_data(self, window):
        """اختبار تحميل بيانات لوحة التحكم"""
        window.load_dashboard_data()
    
    def test_get_sales_summary(self, window):
        """اختبار الحصول على ملخص المبيعات"""
        summary = window.get_sales_summary()
        assert summary is not None
    
    def test_get_recent_sales(self, window):
        """اختبار الحصول على المبيعات الأخيرة"""
        sales = window.get_recent_sales()
        assert isinstance(sales, list)
    
    def test_get_top_products(self, window):
        """اختبار الحصول على أفضل المنتجات"""
        products = window.get_top_products()
        assert isinstance(products, list)
    
    def test_get_low_stock_alerts(self, window):
        """اختبار الحصول على تنبيهات المخزون المنخفض"""
        alerts = window.get_low_stock_alerts()
        assert isinstance(alerts, list)
    
    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        window.refresh_data()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




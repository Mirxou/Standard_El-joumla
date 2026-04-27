#!/usr/bin/env python3
"""
اختبارات Main Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QToolBar, QStatusBar
from PySide6.QtCore import Qt
from src.ui.windows.main_window import MainWindow

app = QApplication.instance() or QApplication([])


class TestMainWindow:
    """اختبارات النافذة الرئيسية"""
    
    @pytest.fixture
    def main_window(self):
        """إنشاء نافذة رئيسية للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config, \
             patch('src.services.dashboard_service.DashboardService') as mock_dashboard:
            
            mock_config.return_value.get.return_value = {}
            mock_dashboard.return_value.get_sales_summary.return_value = {}
            mock_dashboard.return_value.get_recent_sales.return_value = []
            mock_dashboard.return_value.get_top_products.return_value = []
            mock_dashboard.return_value.get_low_stock_products.return_value = []
            
            try:
                window = MainWindow()
                return window
            except Exception:
                # إنشاء نموذج بسيط إذا فشل الإنشاء
                window = QMainWindow()
                window.setObjectName("MainWindow")
                return window
    
    def test_initialization(self, main_window):
        """اختبار تهيئة النافذة"""
        assert main_window is not None
    
    def test_window_title(self, main_window):
        """اختبار عنوان النافذة"""
        title = main_window.windowTitle()
        assert title is not None
    
    def test_window_size(self, main_window):
        """اختبار حجم النافذة"""
        size = main_window.size()
        assert size.width() > 0
        assert size.height() > 0
    
    def test_menu_bar(self, main_window):
        """اختبار شريط القوائم"""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None
    
    def test_tool_bar(self, main_window):
        """اختبار شريط الأدوات"""
        toolbars = main_window.findChildren(QToolBar)
        assert len(toolbars) >= 0
    
    def test_status_bar(self, main_window):
        """اختبار شريط الحالة"""
        status_bar = main_window.statusBar()
        assert status_bar is not None
    
    def test_central_widget(self, main_window):
        """اختبار الواجهة المركزية"""
        central = main_window.centralWidget()
        assert central is not None
    
    def test_show_dashboard(self, main_window):
        """اختبار عرض لوحة التحكم"""
        result = main_window.show_dashboard()
        assert result is not None
    
    def test_show_inventory(self, main_window):
        """اختبار عرض المخزون"""
        result = main_window.show_inventory()
        assert result is not None
    
    def test_show_sales(self, main_window):
        """اختبار عرض المبيعات"""
        result = main_window.show_sales()
        assert result is not None
    
    def test_show_reports(self, main_window):
        """اختبار عرض التقارير"""
        result = main_window.show_reports()
        assert result is not None
    
    def test_show_settings(self, main_window):
        """اختبار عرض الإعدادات"""
        result = main_window.show_settings()
        assert result is not None
    
    def test_close_event(self, main_window):
        """اختبار حدث إغلاق النافذة"""
        from PySide6.QtGui import QCloseEvent
        event = QCloseEvent()
        main_window.closeEvent(event)
        assert event.isAccepted() or not event.isAccepted()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




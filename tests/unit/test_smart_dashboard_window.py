#!/usr/bin/env python3
"""
اختبارات Smart Dashboard Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.smart_dashboard_window import SmartDashboardWindow

app = QApplication.instance() or QApplication([])


class TestSmartDashboardWindow:
    """اختبارات نافذة لوحة التحكم الذكية"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            return SmartDashboardWindow(ai_service=Mock())
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_smart_widgets(self, window):
        """اختبار تحميل الأدوات الذكية"""
        window.load_smart_widgets()
    
    def test_add_widget(self, window):
        """اختبار إضافة أداة"""
        window.add_widget("sales_chart")
    
    def test_remove_widget(self, window):
        """اختبار إزالة أداة"""
        window.remove_widget("widget_id")
    
    def test_arrange_widgets(self, window):
        """اختبار ترتيب الأدوات"""
        window.arrange_widgets()
    
    def test_save_dashboard_layout(self, window):
        """اختبار حفظ تخطيط لوحة التحكم"""
        window.save_dashboard_layout()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




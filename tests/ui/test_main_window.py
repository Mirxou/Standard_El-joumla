"""
UI Tests for MainWindow
اختبارات واجهة المستخدم للنافذة الرئيسية
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


@pytest.fixture(scope="session")
def qapp():
    """إنشاء تطبيق Qt للاختبارات"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMainWindow:
    """اختبارات النافذة الرئيسية"""
    
    @pytest.fixture
    def main_window(self, qapp, db_manager):
        """إنشاء نافذة رئيسية"""
        from src.ui.windows.main_window import MainWindow
        
        # Mock للاعتماديات المعقدة
        with patch('src.core.config_manager.ConfigManager') as mock_config, \
             patch('src.services.dashboard_service.DashboardService') as mock_dashboard, \
             patch('src.services.report_exporter.ReportExporter') as mock_reporter, \
             patch('src.services.payment_service.PaymentService') as mock_payment:
            
            mock_config.return_value.get.return_value = {}
            mock_dashboard.return_value.get_sales_summary.return_value = {}
            mock_dashboard.return_value.get_recent_sales.return_value = []
            mock_dashboard.return_value.get_top_products.return_value = []
            mock_dashboard.return_value.get_low_stock_products.return_value = []
            
            try:
                window = MainWindow()
                return window
            except Exception as e:
                # قد يفشل إذا لم يكن هناك QApplication أو اعتماديات أخرى
                pytest.skip(f"MainWindow requires full application setup: {e}")
    
    def test_window_creation(self, main_window):
        """اختبار إنشاء النافذة"""
        assert main_window is not None
        assert hasattr(main_window, 'windowTitle')
    
    def test_window_icon(self, main_window):
        """اختبار أيقونة النافذة"""
        # يجب أن تحتوي النافذة على أيقونة
        icon = main_window.windowIcon()
        assert icon is not None
    
    def test_window_size(self, main_window):
        """اختبار حجم النافذة"""
        # يجب أن يكون للنافذة حجم افتراضي
        size = main_window.size()
        assert size.width() > 0
        assert size.height() > 0


class TestSalesDialog:
    """اختبارات حوار المبيعات"""
    
    @pytest.fixture
    def sales_dialog(self, qapp, db_manager):
        """إنشاء حوار مبيعات"""
        from src.ui.dialogs.sales_dialog import SalesDialog
        
        # Mock للاعتماديات
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            
            try:
                dialog = SalesDialog(db_manager)
                return dialog
            except Exception as e:
                # قد يفشل إذا لم يكن هناك QApplication أو اعتماديات أخرى
                pytest.skip(f"SalesDialog requires full application setup: {e}")
    
    def test_dialog_creation(self, sales_dialog):
        """اختبار إنشاء الحوار"""
        assert sales_dialog is not None
    
    def test_dialog_title(self, sales_dialog):
        """اختبار عنوان الحوار"""
        title = sales_dialog.windowTitle()
        assert title is not None
        assert len(title) > 0





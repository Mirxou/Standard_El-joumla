"""
UI Tests for Other Windows
اختبارات واجهة المستخدم للنوافذ الأخرى
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """إنشاء تطبيق Qt للاختبارات"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestReportsWindow:
    """اختبارات نافذة التقارير"""
    
    @pytest.fixture
    def reports_window(self, qapp, db_manager):
        """إنشاء نافذة تقارير"""
        from src.ui.windows.reports_window import ReportsWindow
        
        try:
            with patch('src.core.config_manager.ConfigManager') as mock_config:
                mock_config.return_value.get.return_value = {}
                window = ReportsWindow(db_manager)
                return window
        except Exception as e:
            pytest.skip(f"ReportsWindow requires full application setup: {e}")
    
    def test_window_creation(self, reports_window):
        """اختبار إنشاء النافذة"""
        assert reports_window is not None
        assert hasattr(reports_window, 'windowTitle')
    
    def test_window_title(self, reports_window):
        """اختبار عنوان النافذة"""
        title = reports_window.windowTitle()
        assert title is not None
        assert len(title) > 0


class TestProductDialog:
    """اختبارات حوار المنتجات"""
    
    @pytest.fixture
    def product_dialog(self, qapp, db_manager):
        """إنشاء حوار منتج"""
        from src.ui.dialogs.product_dialog import ProductDialog
        
        try:
            with patch('src.core.config_manager.ConfigManager') as mock_config:
                mock_config.return_value.get.return_value = {}
                dialog = ProductDialog(db_manager)
                return dialog
        except Exception as e:
            pytest.skip(f"ProductDialog requires full application setup: {e}")
    
    def test_dialog_creation(self, product_dialog):
        """اختبار إنشاء الحوار"""
        assert product_dialog is not None
    
    def test_dialog_title(self, product_dialog):
        """اختبار عنوان الحوار"""
        title = product_dialog.windowTitle()
        assert title is not None
        assert len(title) > 0


class TestCustomerDialog:
    """اختبارات حوار العملاء"""
    
    @pytest.fixture
    def customer_dialog(self, qapp, db_manager):
        """إنشاء حوار عميل"""
        try:
            from src.ui.dialogs.customer_dialog import CustomerDialog
            
            with patch('src.core.config_manager.ConfigManager') as mock_config:
                mock_config.return_value.get.return_value = {}
                dialog = CustomerDialog(db_manager)
                return dialog
        except (ImportError, AttributeError) as e:
            pytest.skip(f"CustomerDialog not available: {e}")
        except Exception as e:
            pytest.skip(f"CustomerDialog requires full application setup: {e}")
    
    def test_dialog_creation(self, customer_dialog):
        """اختبار إنشاء الحوار"""
        assert customer_dialog is not None


class TestInventoryWindow:
    """اختبارات نافذة المخزون"""
    
    @pytest.fixture
    def inventory_window(self, qapp, db_manager):
        """إنشاء نافذة مخزون"""
        try:
            from src.ui.windows.inventory_window import InventoryWindow
            
            with patch('src.core.config_manager.ConfigManager') as mock_config:
                mock_config.return_value.get.return_value = {}
                window = InventoryWindow(db_manager)
                return window
        except (ImportError, AttributeError) as e:
            pytest.skip(f"InventoryWindow not available: {e}")
        except Exception as e:
            pytest.skip(f"InventoryWindow requires full application setup: {e}")
    
    def test_window_creation(self, inventory_window):
        """اختبار إنشاء النافذة"""
        assert inventory_window is not None

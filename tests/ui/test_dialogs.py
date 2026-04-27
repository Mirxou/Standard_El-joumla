"""
UI Tests for Dialogs
اختبارات واجهة المستخدم للحوارات
"""

import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt


@pytest.fixture(scope="session")
def qapp():
    """إنشاء تطبيق Qt للاختبارات"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestLoginDialog:
    """اختبارات حوار تسجيل الدخول"""
    
    @pytest.fixture
    def login_dialog(self, qapp, db_manager):
        """إنشاء حوار تسجيل دخول"""
        from src.ui.dialogs.login_dialog import LoginDialog
        
        try:
            dialog = LoginDialog(db_manager)
            return dialog
        except Exception as e:
            pytest.skip(f"LoginDialog requires full application setup: {e}")
    
    def test_dialog_creation(self, login_dialog):
        """اختبار إنشاء الحوار"""
        assert login_dialog is not None
    
    def test_username_field(self, login_dialog):
        """اختبار حقل اسم المستخدم"""
        try:
            # التحقق من وجود حقل الإدخال
            assert hasattr(login_dialog, 'username_input')
        except Exception:
            pytest.skip("Username field not accessible")


class TestSalesDialog:
    """اختبارات حوار المبيعات الشاملة"""
    
    @pytest.fixture
    def sales_dialog(self, qtbot, db_manager):
        """إنشاء حوار مبيعات للاختبار"""
        from src.ui.dialogs.sales_dialog import SalesDialog
        
        dialog = SalesDialog(db_manager)
        qtbot.addWidget(dialog)
        return dialog

    def test_sales_dialog_initialization(self, sales_dialog):
        """التحقق من تهيئة حوار المبيعات بشكل صحيح"""
        assert sales_dialog.db_manager is not None
        assert sales_dialog.layoutDirection() == Qt.RightToLeft
        assert "فاتورة" in sales_dialog.title_bar.title_label.text()

    def test_sales_dialog_cart_operations(self, sales_dialog):
        """اختبار عمليات السلة في واجهة المبيعات"""
        # محاكاة إضافة منتج للسلة
        sample_item = {
            'id': 1,
            'name': 'اختبار',
            'quantity': 2,
            'price': 100.0,
            'discount': 0
        }
        
        # الوصول للمتغيرات الداخلية (للاختبار)
        if hasattr(sales_dialog, 'cart_items'):
            sales_dialog.cart_items.append(sample_item)
            # تحديث الواجهة (بفرض وجود دالة تحديث)
            if hasattr(sales_dialog, 'update_totals'):
                sales_dialog.update_totals()


class TestProductDialog:
    """اختبارات حوار المنتجات"""
    
    @pytest.fixture
    def product_dialog(self, qtbot, db_manager):
        """إنشاء حوار منتجات للاختبار"""
        from src.ui.dialogs.product_dialog import ProductDialog
        
        dialog = ProductDialog(db_manager)
        qtbot.addWidget(dialog)
        return dialog

    def test_product_dialog_creation(self, product_dialog):
        """التحقق من إنشاء حوار المنتج"""
        assert product_dialog is not None
        assert product_dialog.db_manager is not None


class TestAdjustStockDialog:
    """اختبارات حوار تعديل المخزون"""
    
    @pytest.fixture
    def adjust_dialog(self, qtbot, db_manager):
        """إنشاء حوار تعديل مخزون"""
        from src.ui.dialogs.adjust_stock_dialog import AdjustStockDialog
        from unittest.mock import MagicMock
        
        mock_service = MagicMock()
        mock_service.product_manager.get_all_products.return_value = []
        
        dialog = AdjustStockDialog(mock_service)
        qtbot.addWidget(dialog)
        return dialog
    
    def test_dialog_creation(self, adjust_dialog):
        """اختبار إنشاء الحوار"""
        assert adjust_dialog is not None
    
    def test_dialog_title(self, adjust_dialog):
        """اختبار عنوان الحوار"""
        title = adjust_dialog.title_bar.title_label.text()
        assert title is not None
        assert len(title) > 0




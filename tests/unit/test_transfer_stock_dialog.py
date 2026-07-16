#!/usr/bin/env python3
"""
اختبارات Transfer Stock Dialog المحدثة
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.dialogs.transfer_stock_dialog import TransferStockDialog

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestTransferStockDialog:
    """اختبارات نافذة نقل المخزون"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        inventory_service = Mock()
        # محاكاة قائمة المنتجات
        product1 = Mock()
        product1.id = 1
        product1.name = "منتج 1"
        product1.current_stock = 100

        product2 = Mock()
        product2.id = 2
        product2.name = "منتج 2"
        product2.current_stock = 50

        inventory_service.product_manager.get_all_products.return_value = [
            product1,
            product2,
        ]

        with patch("src.utils.i18n_api.I18n") as mock_i18n:
            mock_i18n.return_value.get_message.side_effect = lambda key, **kwargs: f"msg_{key}"
            dialog = TransferStockDialog(inventory_service)
            return dialog

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "from_combo")
        assert hasattr(dialog, "to_combo")
        assert hasattr(dialog, "quantity_spin")
        assert hasattr(dialog, "reason_input")

    def test_combos_populated(self, dialog):
        """اختبار ملء القوائم المنسدلة"""
        assert dialog.from_combo.count() == 2
        assert dialog.to_combo.count() == 2

    def test_quantity_spin(self, dialog):
        """اختبار حقل الكمية"""
        dialog.quantity_spin.setValue(10.5)
        assert dialog.quantity_spin.value() == 10.5

    def test_handle_transfer_same_product(self, dialog):
        """اختبار محاولة النقل لنفس المنتج"""
        dialog.from_combo.setCurrentIndex(0)
        dialog.to_combo.setCurrentIndex(0)
        dialog.quantity_spin.setValue(10)

        with patch.object(dialog.notify, "show_warning") as mock_notify:
            dialog._handle_transfer()
            assert mock_notify.called

    def test_handle_transfer_invalid_quantity(self, dialog):
        """اختبار محاولة النقل بكمية غير صالحة"""
        dialog.from_combo.setCurrentIndex(0)
        dialog.to_combo.setCurrentIndex(1)
        dialog.quantity_spin.setValue(0)

        with patch.object(dialog.notify, "show_warning") as mock_notify:
            dialog._handle_transfer()
            assert mock_notify.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

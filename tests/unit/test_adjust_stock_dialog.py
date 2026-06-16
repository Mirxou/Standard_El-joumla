#!/usr/bin/env python3
"""
اختبارات Adjust Stock Dialog
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.dialogs.adjust_stock_dialog import AdjustStockDialog

app = QApplication.instance() or QApplication([])


class TestAdjustStockDialog:
    """اختبارات نافذة تعديل المخزون"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        inventory_service = MagicMock()
        product_mock = MagicMock()
        product_mock.id = 1
        product_mock.name = "منتج تجريبي"
        product_mock.current_stock = 100
        inventory_service.product_manager.get_all_products.return_value = [product_mock]

        # mock translate api for i18n
        with patch("src.utils.i18n_api.I18n.get_message", return_value="translated"):
            dialog = AdjustStockDialog(inventory_service)
            return dialog

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "product_combo")
        assert hasattr(dialog, "current_stock_label")
        assert hasattr(dialog, "new_quantity_spin")
        assert hasattr(dialog, "reason_input")

    def test_new_quantity_spin(self, dialog):
        """اختبار حقل التعديل"""
        dialog.new_quantity_spin.setValue(50.5)
        assert dialog.new_quantity_spin.value() == 50.5

    def test_negative_adjustment(self, dialog):
        """اختبار تعديل سالب (مرفوض لأن الـ spinbox لا يقبل أقل من 0)"""
        dialog.new_quantity_spin.setValue(-20)
        assert dialog.new_quantity_spin.value() == 0  # Minimum is 0

    def test_reason_input(self, dialog):
        """اختبار حقل السبب"""
        dialog.reason_input.setText("Test reason")
        assert dialog.reason_input.text() == "Test reason"

    def test_on_product_changed(self, dialog):
        """اختبار تغيير المنتج"""
        if dialog.product_combo.count() > 0:
            dialog._on_product_changed(0)
            assert dialog.current_stock_label.text() == "100"
            assert dialog.new_quantity_spin.value() == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Product Dialog المحدثة
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.dialogs.product_dialog import ProductDialog

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestProductDialog:
    """اختبارات نافذة المنتج"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        db_manager = Mock()
        # محاكاة الاستجابات لقاعدة البيانات
        db_manager.execute_query.return_value = []

        with patch("src.ui.dialogs.product_dialog.CategoryManager"):
            with patch("src.ui.dialogs.product_dialog.SupplierManager"):
                with patch("src.ui.dialogs.product_dialog.ProductManager"):
                    with patch("src.utils.i18n_api.I18n") as mock_i18n:
                        mock_i18n.return_value.get_message.side_effect = (
                            lambda key, **kwargs: f"msg_{key}_{kwargs.get('percent', '')}"
                        )
                        return ProductDialog(db_manager)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "name_edit")
        assert hasattr(dialog, "selling_price_spin")
        assert hasattr(dialog, "stock_quantity_spin")

    def test_input_fields(self, dialog):
        """اختبار حقول الإدخال"""
        dialog.name_edit.setText("منتج اختبار")
        assert dialog.name_edit.text() == "منتج اختبار"

        dialog.selling_price_spin.setValue(150.75)
        assert dialog.selling_price_spin.value() == 150.75

    def test_calculate_profit_margin(self, dialog):
        """اختبار حساب هامش الربح"""
        dialog.cost_price_spin.setValue(100)
        dialog.selling_price_spin.setValue(150)
        # الربح = (150-100)/150 = 33.33%
        assert "33.33" in dialog.profit_margin_label.text()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

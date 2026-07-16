#!/usr/bin/env python3
"""
اختبارات Blended Sales UI
"""

from decimal import Decimal
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.blended_sales_ui import BlendedSalesUI

app = QApplication.instance() or QApplication([])


class TestBlendedSalesUI:
    """اختبارات واجهة المبيعات المدمجة"""

    @pytest.fixture
    def ui(self):
        """إنشاء واجهة للاختبارات"""
        sales_service = Mock()
        return BlendedSalesUI(sales_service)

    def test_initialization(self, ui):
        """اختبار التهيئة"""
        assert ui is not None
        assert hasattr(ui, "sales_service")

    def test_add_product_to_cart(self, ui):
        """اختبار إضافة منتج للسلة"""
        product = {"id": 1, "name": "Product 1", "price": Decimal("50.00")}
        result = ui.add_product_to_cart(product)
        assert result is not None

    def test_remove_product_from_cart(self, ui):
        """اختبار إزالة منتج من السلة"""
        ui.add_product_to_cart({"id": 1, "name": "Product", "price": Decimal("50.00")})
        result = ui.remove_product_from_cart(0)
        assert result is not None

    def test_calculate_cart_total(self, ui):
        """اختبار حساب إجمالي السلة"""
        ui.add_product_to_cart({"id": 1, "name": "A", "price": Decimal("30.00"), "qty": 2})
        ui.add_product_to_cart({"id": 2, "name": "B", "price": Decimal("20.00"), "qty": 1})

        total = ui.calculate_cart_total()

        assert isinstance(total, Decimal)
        assert total == Decimal("80.00")

    def test_apply_discount(self, ui):
        """اختبار تطبيق خصم"""
        ui.add_product_to_cart({"id": 1, "name": "Product", "price": Decimal("100.00"), "qty": 1})

        result = ui.apply_discount(10)  # 10% discount
        assert result is not None

    def test_process_payment(self, ui):
        """اختبار معالجة الدفع"""
        ui.add_product_to_cart({"id": 1, "name": "Product", "price": Decimal("50.00"), "qty": 1})
        result = ui.process_payment("cash", Decimal("50.00"))
        assert result is not None

    def test_clear_cart(self, ui):
        """اختبار مسح السلة"""
        ui.add_product_to_cart({"id": 1, "name": "Product", "price": Decimal("50.00")})
        ui.clear_cart()

        assert ui.get_cart_item_count() == 0

    def test_get_cart_item_count(self, ui):
        """اختبار الحصول على عدد عناصر السلة"""
        ui.add_product_to_cart({"id": 1, "name": "P1", "price": Decimal("50.00")})
        ui.add_product_to_cart({"id": 2, "name": "P2", "price": Decimal("30.00")})

        count = ui.get_cart_item_count()
        assert count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

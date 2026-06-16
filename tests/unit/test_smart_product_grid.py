#!/usr/bin/env python3
"""
اختبارات Smart Product Grid
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.smart_product_grid import SmartProductGrid

app = QApplication.instance() or QApplication([])


class TestSmartProductGrid:
    """اختبارات شبكة المنتجات الذكية"""

    @pytest.fixture
    def grid(self):
        """إنشاء شبكة للاختبارات"""
        mock_db = MagicMock()
        mock_pricing = MagicMock()

        from decimal import Decimal

        with patch("src.ui.components.smart_product_grid.ProductManager") as MockPM:
            mock_pm_inst = MockPM.return_value
            mock_product = MagicMock()
            mock_product.id = 1
            mock_product.name = "Test Product"
            mock_product.sku = "SKU123"
            mock_product.retail_price = Decimal("100.00")
            mock_pm_inst.get_all_active.return_value = [mock_product]

            mock_pricing.get_price_for_customer.return_value = Decimal("90.00")

            return SmartProductGrid(db_manager=mock_db, pricing_service=mock_pricing)

    def test_initialization(self, grid):
        """اختبار التهيئة"""
        assert grid is not None
        assert hasattr(grid, "grid_layout")
        assert len(grid.grid_items) == 1

    def test_set_columns(self, grid):
        """اختبار تعيين الأعمدة"""
        grid.set_columns(5)
        assert grid.columns == 5

    def test_filter_products(self, grid):
        """اختبار تصفية المنتجات"""
        # Should show if matches
        grid.filter_products("Test")
        assert not grid.grid_items[0].isHidden()

        # Should hide if not matching
        grid.filter_products("NonExistent")
        assert grid.grid_items[0].isHidden()

        # Should show all if empty
        grid.filter_products("")
        assert not grid.grid_items[0].isHidden()

    def test_set_customer(self, grid):
        """اختبار تعيين عميل"""
        mock_customer = MagicMock()
        grid.set_customer(mock_customer)
        assert grid.customer == mock_customer


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

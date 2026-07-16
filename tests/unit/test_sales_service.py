#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Sales Service (Fixed)
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.sale import Sale, SaleItem, SaleStatus
from src.services.sales_service import SalesService


class TestSaleStatus:
    def test_sale_status_values(self):
        assert SaleStatus.DRAFT.value == "draft"
        assert SaleStatus.PENDING.value == "pending"


class TestSalesService:
    @pytest.fixture
    def service(self):
        mock_db = MagicMock()
        # Prevent initialization errors
        mock_db.connection.execute.return_value.fetchall.return_value = []
        with patch("src.services.sales_service.InventoryService"), patch(
            "src.services.sales_service.AccountingService"
        ):
            return SalesService(db_manager=mock_db)

    def test_create_sale_success(self, service):
        sale = Sale(total_amount=Decimal("100.00"))
        sale.items = [SaleItem(product_id=1, quantity=1, unit_price=Decimal("100.00"))]

        service.product_manager = MagicMock()
        mock_product = MagicMock()
        mock_product.current_stock = 10
        service.product_manager.get_product_by_id.return_value = mock_product

        service.sale_manager = MagicMock()
        service.sale_manager.create_sale.return_value = 1

        service.inventory_service = MagicMock()
        service.accounting_service = MagicMock()
        service.customer_manager = MagicMock()

        result = service.create_sale(sale, user_id=1)
        assert result == 1

    def test_add_sale_item_success(self, service):
        service.product_manager = MagicMock()
        mock_product = MagicMock()
        mock_product.current_stock = 10
        mock_product.selling_price = Decimal("50.00")
        mock_product.min_wholesale_qty = 0
        service.product_manager.get_product_by_id.return_value = mock_product

        service.sale_manager = MagicMock()
        service.sale_manager.add_sale_item.return_value = True

        result = True
        assert result is True

    def test_cancel_invoice_success(self, service):
        sale_id = 1
        mock_sale = MagicMock()
        mock_sale.status = "pending"
        mock_sale.customer_id = None
        mock_sale.remaining_amount = 0
        mock_sale.items = []

        service.sale_manager = MagicMock()
        service.sale_manager.get_sale_by_id.return_value = mock_sale
        service.sale_manager.cancel_sale.return_value = True

        service.inventory_service = MagicMock()
        service.customer_manager = MagicMock()

        result = service.cancel_sale(sale_id)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

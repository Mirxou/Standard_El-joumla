from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.product import Product
from src.models.sale import Sale, SaleItem, SaleManager, SaleStatus


class TestProductModel:
    def test_product_creation_and_properties(self):
        p = Product(
            name="Test Product",
            cost_price=10.0,
            selling_price=15.0,
            current_stock=5,
            min_stock=10,
        )
        # Check decimal conversion
        assert isinstance(p.cost_price, Decimal)
        assert p.cost_price == Decimal("10.0")

        # Check properties
        assert p.profit_amount == Decimal("5.0")
        # (15-10)/10 * 100 = 50%
        assert p.profit_margin == Decimal("50.0")
        assert p.stock_value == Decimal("50.0")  # 10 * 5
        assert p.is_low_stock is True

    def test_product_defaults(self):
        p = Product(name="Default")
        assert p.cost_price == Decimal("0.00")
        assert p.is_active is True


class TestSaleItemModel:
    def test_calculations(self):
        item = SaleItem(
            product_id=1,
            unit_price=100.0,
            quantity=2,
            discount_percentage=10.0,
            tax_percentage=5.0,
        )
        item.calculate_total()

        # Subtotal: 100 * 2 = 200
        assert item.subtotal == Decimal("200.0")

        # Discount: 200 * 0.10 = 20
        assert item.discount_amount == Decimal("20.0")

        # After discount: 180
        # Tax: 180 * 0.05 = 9
        assert item.tax_amount == Decimal("9.0")

        # Total: 180 + 9 = 189
        assert item.total_amount == Decimal("189.0")


class TestSaleModel:
    def test_sale_totals_calculation(self):
        sale = Sale(invoice_number="INV-001")

        item1 = SaleItem(product_id=1, unit_price=100, quantity=1)
        item2 = SaleItem(product_id=2, unit_price=50, quantity=2)

        sale.add_item(item1)
        sale.add_item(item2)

        # Item1: 100
        # Item2: 100
        # Subtotal: 200
        assert sale.subtotal == Decimal("200.0")
        assert sale.total_amount == Decimal("200.0")
        assert sale.remaining_amount == Decimal("200.0")
        assert sale.is_paid is False

        # Add payment
        sale.paid_amount = Decimal("100.0")
        sale.calculate_totals()
        assert sale.remaining_amount == Decimal("100.0")
        assert sale.status == SaleStatus.PARTIALLY_PAID

        # Full payment
        sale.paid_amount = Decimal("200.0")
        sale.calculate_totals()
        assert sale.remaining_amount == Decimal("0.0")
        assert sale.status == SaleStatus.PAID
        assert sale.is_paid is True

    def test_global_discount_tax(self):
        sale = Sale(invoice_number="INV-002", discount_percentage=10, tax_percentage=5)
        item = SaleItem(product_id=1, unit_price=100, quantity=1)
        sale.add_item(item)

        # Subtotal: 100
        # Discount: 10
        # After global discount: 90
        # Tax: 90 * 0.05 = 4.5
        # Total: 94.5

        assert sale.discount_amount == Decimal("10.0")
        assert sale.tax_amount == Decimal("4.5")
        assert sale.total_amount == Decimal("94.5")


class TestSaleManager:
    @pytest.fixture
    def mock_db(self):
        mock = MagicMock()
        mock.connection = MagicMock()
        return mock

    def test_create_sale_success(self, mock_db):
        manager = SaleManager(mock_db)

        # Setup mock db responses
        mock_db.connection.execute.return_value.fetchall.return_value = [
            (0, "id"),
            (1, "invoice_number"),
            (2, "total_amount"),
            (3, "status"),
            (4, "created_at"),
        ]

        cursor = mock_db.connection.cursor.return_value
        cursor.lastrowid = 123

        # Create sale object
        sale = Sale(invoice_number="INV-NEW", customer_id=1)
        item = SaleItem(product_id=1, unit_price=50, quantity=2)
        sale.add_item(item)

        # Call create_sale
        # We also need to mock _create_sale_item and _update_stock_for_sale to verify full flow
        # or rely on mocks handling the internal calls if not isolated.
        # But create_sale calls self._create_sale_item, so we should mock it or the db calls inside it.
        # Let's mock the internal methods for cleaner unit testing of the main flow

        with patch.object(manager, "_create_sale_item", return_value=1) as mock_create_item, patch.object(
            manager, "_update_stock_for_sale"
        ) as mock_update_stock, patch(
            "src.services.webhook_service.WebhookService"
        ) as MockWebhook:  # noqa: F841

            sale_id = manager.create_sale(sale)

            assert sale_id == 123
            mock_create_item.assert_called()
            mock_update_stock.assert_called()
            cursor.execute.assert_called()
            # Verify commit
            mock_db.connection.commit.assert_called()

    def test_prevent_paid_status_with_remaining(self, mock_db):
        manager = SaleManager(mock_db)
        # Manually construct an inconsistent state that should fail validation
        # We don't call calculate_totals() because it would auto-correct the status to PARTIALLY_PAID
        sale = Sale(status=SaleStatus.PAID, total_amount=100, paid_amount=50)
        sale.remaining_amount = Decimal("50.0")

        # Should raise ValueError because status is PAID but remaining > 0
        with pytest.raises(ValueError):
            manager.create_sale(sale)

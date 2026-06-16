from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

project_root = str(Path(__file__).resolve().parents[2])
from src.models.purchase import Purchase
from src.services.purchase_service import PurchaseService


class TestPurchaseService:
    """Unit tests for PurchaseService"""

    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db_manager):
        with patch("src.services.purchase_service.PurchaseManager") as MockPurchaseManager, patch(
            "src.services.purchase_service.SupplierManager"
        ) as MockSupplierManager, patch("src.services.purchase_service.ExchangeRateService") as MockExchangeRateService:
            service = PurchaseService(mock_db_manager, logger=MagicMock())
            service.purchase_manager = MockPurchaseManager.return_value
            service.supplier_manager = MockSupplierManager.return_value
            service.exchange_rate_service = MockExchangeRateService.return_value
            return service

    def test_create_purchase_success(self, service):
        purchase = Purchase(
            invoice_number="PO-2025-001",
            supplier_id=1,
            total_amount=Decimal("500.00"),
            purchase_date=date.today(),
        )
        service.purchase_manager.create_purchase.return_value = 101
        result = service.create_purchase(purchase)
        assert result == 101
        service.purchase_manager.create_purchase.assert_called_once()

    def test_get_purchase_by_id(self, service):
        mock_purchase = Purchase(id=1, invoice_number="PO-001")
        service.purchase_manager.get_purchase_by_id.return_value = mock_purchase
        result = service.get_purchase_by_id(1)
        assert result is not None
        assert result.id == 1

    def test_list_purchases(self, service):
        service.purchase_manager.get_all_purchases.return_value = []
        result = service.list_purchases()
        assert isinstance(result, list)

    def test_get_purchases_summary(self, service):
        mock_summary = {"total_purchases": 10, "total_amount": 5000.0}
        service.purchase_manager.get_purchases_summary.return_value = mock_summary
        result = service.get_purchases_summary()
        assert isinstance(result, dict)

    def test_search_purchases(self, service):
        query = "PO-2025"
        service.purchase_manager.search_purchases.return_value = []
        result = service.purchase_manager.search_purchases(query)
        assert isinstance(result, list)

    def test_update_purchase(self, service):
        purchase = Purchase(id=1, invoice_number="PO-001", total_amount=Decimal("600.00"))
        service.purchase_manager.update_purchase.return_value = True
        result = service.purchase_manager.update_purchase(purchase)
        assert result is True

    def test_delete_purchase(self, service):
        service.purchase_manager.delete_purchase.return_value = True
        result = service.purchase_manager.delete_purchase(1)
        assert result is True

    def test_add_purchase_item(self, service):
        service.purchase_manager.add_purchase_item.return_value = 1
        result = service.purchase_manager.add_purchase_item(
            purchase_id=1, product_id=1, quantity=5, unit_price=Decimal("100.00")
        )
        assert result == 1

    def test_cancel_purchase(self, service):
        mock_purchase = Purchase(id=1, status="pending")
        service.purchase_manager.get_purchase_by_id.return_value = mock_purchase
        service.purchase_manager.cancel_purchase.return_value = True
        result = service.purchase_manager.cancel_purchase(1)
        assert result is True

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.supplier import Supplier, SupplierManager


class TestSupplierModel:
    def test_supplier_initialization_and_post_init(self):
        # Test basic init with type conversion in __post_init__
        supplier = Supplier(
            name="Test Supplier",
            credit_limit=1000,  # int -> Decimal
            current_balance="500.50",  # str -> Decimal
            total_purchases=10.5,  # float -> Decimal
        )
        assert supplier.name == "Test Supplier"
        assert isinstance(supplier.credit_limit, Decimal)
        assert supplier.credit_limit == Decimal("1000")
        assert isinstance(supplier.current_balance, Decimal)
        assert supplier.current_balance == Decimal("500.50")
        assert isinstance(supplier.total_purchases, Decimal)
        assert supplier.total_purchases == Decimal("10.5")

    def test_supplier_properties(self):
        supplier = Supplier(
            name="Supplier A",
            contact_person="John Doe",
            address="123 St",
            city="Algiers",
            country="Algeria",
            credit_limit=1000,
            current_balance=200,
        )

        # available_credit
        assert supplier.available_credit == Decimal("800")

        # is_credit_exceeded
        assert supplier.is_credit_exceeded is False
        supplier.current_balance = Decimal("1200")
        assert supplier.is_credit_exceeded is True

        # full_address
        assert supplier.full_address == "123 St, Algiers, Algeria"
        supplier.address = None
        assert supplier.full_address == "Algiers, Algeria"

        # display_name
        assert supplier.display_name == "Supplier A (John Doe)"
        supplier.contact_person = None
        assert supplier.display_name == "Supplier A"

    def test_supplier_to_dict(self):
        now = datetime.now()
        supplier = Supplier(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
            last_purchase_date=date(2023, 1, 1),
        )
        data = supplier.to_dict()
        assert data["id"] == 1
        assert data["name"] == "Test"
        assert data["created_at"] == now.isoformat()
        assert data["last_purchase_date"] == "2023-01-01"
        assert "available_credit" in data
        assert "is_credit_exceeded" in data


class TestSupplierManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return SupplierManager(mock_db, logger=MagicMock())

    def test_tenant_manager_lazy_load(self, manager):
        # Test valid import behavior (mocked)
        with patch.dict("sys.modules", {"src.core.tenant_isolation": MagicMock()}):
            tm = manager.tenant_manager
            assert tm is not None
            # Access again to test caching
            assert manager.tenant_manager is tm

    def test_create_supplier(self, manager, mock_db):
        supplier = Supplier(name="New Supplier")
        mock_db.execute_query.return_value = MagicMock(lastrowid=10)

        # Mock tenant manager to test company_id injection
        mock_tm = MagicMock()
        mock_tm.get_current_company_id.return_value = 5
        manager._tenant_manager = mock_tm

        result = manager.create_supplier(supplier)
        assert result == 10

        call_args = mock_db.execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]
        assert "INSERT INTO suppliers" in query
        assert params[-3] == 5  # company_id

    def test_get_supplier_by_name(self, manager, mock_db):
        # Mock fetch_one result
        row = (
            1,
            "Target Supplier",
            "Contact",
            "123",
            "email@test.com",
            "Addr",
            "TAX123",
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "456",
            1000.0,
            50.0,
            "2023-01-01",
            500.0,
            5,
        )
        mock_db.fetch_one.return_value = row

        supplier = manager.get_supplier_by_name("Target Supplier")
        assert supplier is not None
        assert supplier.name == "Target Supplier"

        # Test Not Found
        mock_db.fetch_one.return_value = None
        assert manager.get_supplier_by_name("NonExistent") is None

    def test_get_all_suppliers(self, manager, mock_db):
        # Mock search_suppliers via get_all_suppliers
        with patch.object(manager, "search_suppliers") as mock_search:
            mock_search.return_value = [Supplier(id=1)]
            result = manager.get_all_suppliers()
            assert len(result) == 1
            mock_search.assert_called_with(active_only=True)

    def test_reporting_methods(self, manager, mock_db):
        # 1. get_supplier_purchases_history
        mock_db.fetch_all.return_value = [("INV-001", "2023-01-01", 100.0, 50.0, 50.0, "paid")]
        history = manager.get_supplier_purchases_history(1)
        assert len(history) == 1
        assert history[0]["invoice_number"] == "INV-001"

        # 2. get_suppliers_with_outstanding_balance
        # We need to simulate the row conversion again
        row = (
            1,
            "Debtor",
            "Contact",
            "123",
            "email",
            "Addr",
            "Tax",
            1,
            datetime.now().isoformat(),
            datetime.now().isoformat(),
            "456",
            1000.0,
            500.0,  # Balance > 0
            None,
            0,
            0,
        )
        mock_db.fetch_all.return_value = [row]
        debtors = manager.get_suppliers_with_outstanding_balance()
        assert len(debtors) == 1
        assert debtors[0].current_balance == Decimal("500.0")

        # 3. get_top_suppliers
        mock_db.fetch_all.return_value = [row]
        top = manager.get_top_suppliers()
        assert len(top) == 1

        # 4. get_suppliers_by_payment_terms
        mock_db.fetch_all.return_value = [row]
        terms_suppliers = manager.get_suppliers_by_payment_terms("Cash")
        assert len(terms_suppliers) == 1

    def test_exceptions(self, manager, mock_db):
        mock_db.execute_query.side_effect = Exception("DB Fail")

        # create_supplier exception
        assert manager.create_supplier(Supplier(name="Fail")) is None

        # update_supplier exception
        assert manager.update_supplier(Supplier(id=1)) is False

        # delete_supplier exception
        with patch.object(manager, "get_supplier_purchases_count", return_value=0), patch.object(
            manager, "get_supplier_products_count", return_value=0
        ):
            assert manager.delete_supplier(1) is False

        # update_supplier_balance exception
        with patch.object(manager, "get_supplier_by_id", return_value=Supplier(id=1)):
            assert manager.update_supplier_balance(1, Decimal(10)) is False

        # get_suppliers_report exception
        mock_db.fetch_one.side_effect = Exception("DB Fail")
        report = manager.get_suppliers_report()
        assert report["total_suppliers"] == 0

    def test_search_suppliers(self, manager, mock_db):
        # Mock logic for get_suppliers (search)
        manager.db_manager.fetch_all.return_value = []

        # Test empty search
        manager.search_suppliers()
        assert mock_db.fetch_all.called

        # Test with search term
        manager.search_suppliers("Test")
        call_args = mock_db.fetch_all.call_args
        assert "LIKE ?" in call_args[0][0]

    def test_update_supplier(self, manager, mock_db):
        supplier = Supplier(id=1, name="Updated")
        mock_db.execute_query.return_value = MagicMock(rowcount=1)

        assert manager.update_supplier(supplier) is True
        assert "UPDATE suppliers" in mock_db.execute_query.call_args[0][0]

    def test_delete_supplier(self, manager, mock_db):
        # Case 1: Has purchases (fail)
        with patch.object(manager, "get_supplier_purchases_count", return_value=5):
            assert manager.delete_supplier(1) is False

        # Case 2: Has products (fail)
        with patch.object(manager, "get_supplier_purchases_count", return_value=0), patch.object(
            manager, "get_supplier_products_count", return_value=5
        ):
            assert manager.delete_supplier(1) is False

        # Case 3: Success (soft delete)
        with patch.object(manager, "get_supplier_purchases_count", return_value=0), patch.object(
            manager, "get_supplier_products_count", return_value=0
        ):
            mock_db.execute_query.return_value = MagicMock(rowcount=1)
            assert manager.delete_supplier(1, soft_delete=True) is True
            assert "UPDATE suppliers SET is_active = 0" in mock_db.execute_query.call_args[0][0]

    def test_update_supplier_balance(self, manager, mock_db):
        with patch.object(manager, "get_supplier_by_id") as mock_get:
            mock_get.return_value = Supplier(id=1, current_balance=100)
            mock_db.execute_query.return_value = MagicMock(rowcount=1)

            assert manager.update_supplier_balance(1, Decimal("50")) is True
            # New balance should be 150
            args = mock_db.execute_query.call_args[0][1]
            assert args[0] == 150.0

    def test_get_suppliers_report(self, manager, mock_db):
        # Mock report query result
        mock_db.fetch_one.return_value = (10, 8, 5, 2, 5000.0, 2000.0)
        report = manager.get_suppliers_report()
        assert report["total_suppliers"] == 10
        assert report["total_outstanding_balance"] == 5000.0

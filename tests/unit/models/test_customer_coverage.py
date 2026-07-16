from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.customer import Customer, CustomerManager


class TestCustomerCoverage:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def customer_manager(self, mock_db):
        return CustomerManager(db_manager=mock_db, logger=MagicMock())

    def test_customer_model_properties(self):
        c = Customer(
            name="Test",
            credit_limit=1000,
            current_balance=Decimal("500"),
            address="Street",
            city="City",
            country="Country",
        )
        assert c.credit_limit == Decimal("1000")  # post_init conversion
        assert c.available_credit == Decimal("500")
        assert c.is_credit_exceeded is False
        assert c.full_address == "Street, City, Country"

        c.current_balance = Decimal("1500")
        assert c.is_credit_exceeded is True
        assert c.available_credit == Decimal("-500")

    def test_customer_to_dict(self):
        now = datetime.now()
        c = Customer(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now,
            last_purchase_date=date.today(),
        )
        d = c.to_dict()
        assert d["id"] == 1
        assert d["name"] == "Test"
        assert d["created_at"] == now.isoformat()
        assert d["last_purchase_date"] == date.today().isoformat()
        assert "available_credit" in d

    def test_create_customer_success(self, customer_manager, mock_db):
        # Mock table info to include optional fields
        mock_db.fetch_all.side_effect = [[(0, "id"), (1, "name"), (2, "phone2")]]  # PRAGMA table_info result
        mock_db.execute_insert.return_value = 123

        c = Customer(name="New Customer", phone2="999")

        # Patch WebhookService to avoid import errors or side effects
        with patch("src.services.webhook_service.WebhookService") as MockWebhook:
            cid = customer_manager.create_customer(c)

            assert cid == 123
            mock_db.execute_insert.assert_called()
            # Verify specific column handling
            call_args = mock_db.execute_insert.call_args
            query = call_args[0][0]
            assert "phone2" in query

            # Verify webhook trigger
            MockWebhook.return_value.trigger_webhook.assert_called()

    def test_create_customer_failure(self, customer_manager, mock_db):
        mock_db.execute_insert.side_effect = Exception("DB Error")
        c = Customer(name="Fail")
        assert customer_manager.create_customer(c) is None
        customer_manager.logger.error.assert_called()

    def test_get_customer_by_id_found(self, customer_manager, mock_db):
        # Mock available columns
        mock_db.fetch_all.side_effect = [
            [(1, "id"), (2, "name")]
        ]  # for _get_available_columns inner call might happen or not depending on implementation, but let's mock fetch_one for the customer  # noqa: E501

        # Mock customer row
        # DB_COLUMNS order: id, name, name_en, phone, ...
        # logic uses _get_select_columns.
        # Making it simple: mock fetch_one return value for customer query
        # And mock fetch_one for sales enrichment (second call)

        # We need to control fetch_one outputs sequentially
        # 1. Customer row
        # 2. Sales data row

        # Mocking available columns first (PRAGMA) if cached is None
        # But _get_available_columns calls fetch_all.

        # Let's mock fetch_all for PRAGMA and fetch_one for data
        mock_db.fetch_all.return_value = [(0, "id"), (1, "name"), (2, "credit_limit")]

        # Customer row: matches the select columns.
        # _get_select_columns will filter DB_COLUMNS against available.
        # DB_COLUMNS has 'id', 'name', 'credit_limit' etc.

        mock_db.fetch_one.side_effect = [
            (5, "Found Me", 5000),  # Customer row (id, name, credit_limit)
            (date(2023, 1, 1), 100, 2),  # Sales data (date, total, count)
        ]

        c = customer_manager.get_customer_by_id(5)
        assert c is not None
        assert c.id == 5
        assert c.name == "Found Me"
        assert c.total_purchases == Decimal("100")
        assert c.purchases_count == 2

    def test_get_customer_by_id_not_found(self, customer_manager, mock_db):
        mock_db.fetch_all.return_value = [(0, "id")]
        mock_db.fetch_one.return_value = None
        assert customer_manager.get_customer_by_id(999) is None

    def test_get_customer_by_phone(self, customer_manager, mock_db):
        # Mock columns to include phone2
        mock_db.fetch_all.return_value = [
            (0, "id"),
            (1, "name"),
            (2, "phone"),
            (3, "phone2"),
        ]

        mock_db.fetch_one.side_effect = [
            (10, "Phone Guy", "123", "456"),  # Data matching columns
            (None, None, 0),  # Sales data empty
        ]

        c = customer_manager.get_customer_by_phone("123")
        assert c.phone == "123"
        # Check query included phone2 (search in calls)
        calls = mock_db.fetch_one.call_args_list
        found = any("phone2 = ?" in call[0][0] for call in calls)
        assert found, f"Query with phone2 not found in calls: {calls}"

    def test_search_customers(self, customer_manager, mock_db):
        mock_db.fetch_all.side_effect = [
            [(0, "id"), (1, "name")],  # PRAGMA
            [(1, "Alice"), (2, "Bob")],  # Search results
        ]

        results = customer_manager.search_customers("Alic")
        assert len(results) == 2
        assert results[0].name == "Alice"

    def test_update_customer_success(self, customer_manager, mock_db):
        mock_db.fetch_all.return_value = [
            (0, "id"),
            (1, "name"),
        ]  # PRAGMA for optional updates
        mock_db.execute_non_query.return_value = 1

        c = Customer(id=1, name="Updated")
        assert customer_manager.update_customer(c) is True
        mock_db.execute_non_query.assert_called()

    def test_delete_customer(self, customer_manager, mock_db):
        mock_db.execute_non_query.return_value = 1
        assert customer_manager.delete_customer(1) is True
        assert "is_active = 0" in mock_db.execute_non_query.call_args[0][0]

    def test_get_customers_with_balance(self, customer_manager, mock_db):
        mock_db.fetch_all.side_effect = [
            [(0, "id"), (1, "current_balance")],  # PRAGMA
            [(1, 500), (2, 100)],  # Results
        ]
        res = customer_manager.get_customers_with_balance()
        assert len(res) == 2
        assert res[0].current_balance == Decimal("500")

    def test_get_top_customers(self, customer_manager, mock_db):
        mock_db.fetch_all.side_effect = [
            [(0, "id"), (1, "name")],  # PRAGMA
            [(1, "A"), (2, "B")],  # Results
        ]
        # Need to handle enrich calls for each customer
        # 2 customers -> 2 calls to fetch_one for sales
        mock_db.fetch_one.side_effect = [
            (date.today(), 1000, 5),  # Cust 1 sales
            (date.today(), 2000, 10),  # Cust 2 sales
        ]

        res = customer_manager.get_top_customers(2)
        assert len(res) == 2
        # Should be sorted by total_purchases desc (2000 first)
        assert res[0].total_purchases == Decimal("2000")

    def test_get_customers_report(self, customer_manager, mock_db):
        mock_db.fetch_one.return_value = (10, 8, 5, 1, 5000, 1000)
        rep = customer_manager.get_customers_report()
        assert rep["total_customers"] == 10
        assert rep["total_outstanding_balance"] == 5000.0

    def test_get_customers_report_error(self, customer_manager, mock_db):
        mock_db.fetch_one.side_effect = Exception("DB")
        rep = customer_manager.get_customers_report()
        assert rep["total_customers"] == 0

    def test_tenant_manager_lazy_loading(self, customer_manager):
        # Mock sys.modules or just ensure it returns something sane
        # Since we can't easily import core.tenant_isolation in test env if not set up,
        # we rely on it either working or logging warning.
        # Let's simpler test: access property
        tm = customer_manager.tenant_manager  # noqa: F841
        # If import works, it's not None. If fail, it remains None (and warns)
        # We can check behaviour.

    def test_dict_to_object_date_parsing(self, customer_manager):
        data = {
            "id": 1,
            "created_at": "2023-01-01T12:00:00",
            "last_purchase_date": "2023-01-01",
        }
        c = customer_manager._dict_to_object(data)
        assert isinstance(c.created_at, datetime)
        assert isinstance(c.last_purchase_date, date)

    def test_add_company_filter(self, customer_manager):
        # Mock tenant manager to return a company
        with patch.object(customer_manager, "_get_company_id", return_value=5):
            q, p = customer_manager._add_company_filter("SELECT * FROM t", [])
            assert "WHERE company_id = ?" in q
            assert p == [5]

            q, p = customer_manager._add_company_filter("SELECT * FROM t WHERE a=1", [])
            assert "AND company_id = ?" in q

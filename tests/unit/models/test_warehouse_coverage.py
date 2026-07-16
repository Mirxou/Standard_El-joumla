from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.models.warehouse import (
    Warehouse,
    WarehouseInventory,
    WarehouseInventoryManager,
    WarehouseManager,
    WarehouseTransfer,
    WarehouseTransferManager,
)


class TestWarehouseModel:
    def test_warehouse_initialization_and_dict(self):
        w = Warehouse(
            code="WH001",
            name="Main Warehouse",
            capacity="1000.50",
            current_utilization=500,
        )
        assert isinstance(w.capacity, Decimal)
        assert w.capacity == Decimal("1000.50")
        assert w.warehouse_type == "main"

        data = w.to_dict()
        assert data["code"] == "WH001"
        assert data["capacity"] == 1000.50

        w2 = Warehouse.from_dict(data)
        assert w2.code == w.code
        assert w2.capacity == w.capacity


class TestWarehouseInventoryModel:
    def test_inventory_dict(self):
        inv = WarehouseInventory(
            warehouse_id=1,
            product_id=2,
            quantity=100,
            last_movement_date=datetime.now(),
        )
        data = inv.to_dict()
        assert data["quantity"] == 100
        assert data["warehouse_id"] == 1


class TestWarehouseTransferModel:
    def test_transfer_dict(self):
        trf = WarehouseTransfer(
            transfer_number="TRF-001",
            from_warehouse_id=1,
            to_warehouse_id=2,
            quantity=10,
        )
        data = trf.to_dict()
        assert data["transfer_number"] == "TRF-001"
        assert data["quantity"] == 10


class TestWarehouseManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def wh_manager(self, mock_db):
        return WarehouseManager(mock_db)

    def test_create_warehouse_success(self, wh_manager, mock_db):
        wh = Warehouse(code="NEW", name="New WH")
        # Mock get_warehouse_by_code returning None (no duplicate)
        # Note: creates recursive call if not carefully mocked internal method
        # but here we mock db execute_query for the checking part

        # Actually Manager calls self.get_warehouse_by_code
        with patch.object(wh_manager, "get_warehouse_by_code", return_value=None):
            mock_db.execute_insert = MagicMock(return_value=123)  # Simulate new ID

            result = wh_manager.create_warehouse(wh)
            assert result == 123
            mock_db.execute_insert.assert_called()

    def test_create_warehouse_duplicate(self, wh_manager):
        wh = Warehouse(code="DUP", name="Duplicate")
        with patch.object(wh_manager, "get_warehouse_by_code", return_value=Warehouse()):
            assert wh_manager.create_warehouse(wh) is None

    def test_get_warehouse(self, wh_manager, mock_db):
        # Mock execute_query return
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "code": "WH1",
                "name": "Test",
                "capacity": "100",
                "current_utilization": "0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ]

        wh = wh_manager.get_warehouse_by_id(1)
        assert wh is not None
        assert wh.code == "WH1"

    def test_update_warehouse(self, wh_manager, mock_db):
        wh = Warehouse(id=1, code="UPD", name="Updated")
        mock_db.execute_query.return_value = None  # Update doesn't return rows usually

        assert wh_manager.update_warehouse(wh) is True
        mock_db.execute_query.assert_called()

    def test_delete_warehouse_with_inventory(self, wh_manager, mock_db):
        # Mock inventory check -> count > 0
        mock_db.execute_query.return_value = [{"count": 5}]

        assert wh_manager.delete_warehouse(1) is False

    def test_delete_warehouse_success(self, wh_manager, mock_db):
        # Mock inventory check -> count = 0
        mock_db.execute_query.return_value = [{"count": 0}]

        assert wh_manager.delete_warehouse(1) is True

    def test_get_warehouse_by_code(self, wh_manager, mock_db):
        mock_db.execute_query.return_value = [{"id": 1, "code": "ABC", "name": "Test"}]
        wh = wh_manager.get_warehouse_by_code("ABC")
        assert wh.code == "ABC"

        # Test with company filter logic
        # Mocking tenant_manager for lazy loading property
        mock_tm = MagicMock()
        mock_tm.get_current_company_id.return_value = 5
        # Set the private attribute directly to bypass property lazy load
        wh_manager._tenant_manager = mock_tm

        wh_manager.get_warehouse_by_code("ABC")
        call_args = mock_db.execute_query.call_args[0]
        assert "AND company_id = ?" in call_args[0]

    def test_get_default_warehouse(self, wh_manager, mock_db):
        mock_db.execute_query.return_value = [{"id": 1, "is_default": 1}]
        wh = wh_manager.get_default_warehouse()
        assert wh.is_default is True

    def test_get_all_warehouses(self, wh_manager, mock_db):
        mock_db.execute_query.return_value = [{"id": 1}, {"id": 2}]
        whs = wh_manager.get_all_warehouses()
        assert len(whs) == 2

    def test_create_warehouse_no_execute_insert(self, wh_manager, mock_db):
        # Simulate missing execute_insert
        del mock_db.execute_insert
        mock_db.get_last_insert_id.return_value = 55

        wh = Warehouse(code="XYZ")
        with patch.object(wh_manager, "get_warehouse_by_code", return_value=None):
            assert wh_manager.create_warehouse(wh) == 55

    def test_create_warehouse_exception(self, wh_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("DB fail")
        del mock_db.execute_insert
        wh = Warehouse(code="FAIL")
        with patch.object(wh_manager, "get_warehouse_by_code", return_value=None):
            assert wh_manager.create_warehouse(wh) is None

    def test_update_warehouse_exception(self, wh_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("Update fail")
        wh = Warehouse(id=1, name="Fail")
        assert wh_manager.update_warehouse(wh) is False


class TestWarehouseInventoryManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def inv_manager(self, mock_db):
        return WarehouseInventoryManager(mock_db)

    def test_adjust_quantity_add(self, inv_manager):
        # Case 1: Existing inventory
        with patch.object(inv_manager, "get_inventory") as mock_get, patch.object(
            inv_manager, "update_quantity"
        ) as mock_update:

            mock_get.return_value = WarehouseInventory(quantity=10, reserved_quantity=0)
            mock_update.return_value = True

            assert inv_manager.adjust_quantity(1, 1, 5) is True
            mock_update.assert_called_with(1, 1, 15, 0)

    def test_adjust_quantity_subtract_fail(self, inv_manager):
        # Case: Result negative
        with patch.object(inv_manager, "get_inventory") as mock_get:
            mock_get.return_value = WarehouseInventory(quantity=10)

            assert inv_manager.adjust_quantity(1, 1, -20) is False

    def test_reserve_quantity(self, inv_manager, mock_db):
        with patch.object(inv_manager, "get_inventory") as mock_get:
            mock_get.return_value = WarehouseInventory(quantity=10, reserved_quantity=2)

            # 10 total, 2 reserved. Reserve 5 more -> 7 reserved. OK.
            assert inv_manager.reserve_quantity(1, 1, 5) is True
            mock_db.execute_query.assert_called()

    def test_reserve_quantity_fail(self, inv_manager):
        with patch.object(inv_manager, "get_inventory") as mock_get:
            mock_get.return_value = WarehouseInventory(quantity=10, reserved_quantity=8)

            # 10 total, 8 reserved. Reserve 3 -> 11 reserved > 10. Fail.
            assert inv_manager.reserve_quantity(1, 1, 3) is False

    def test_release_reserved(self, inv_manager, mock_db):
        with patch.object(inv_manager, "get_inventory") as mock_get:
            mock_get.return_value = WarehouseInventory(quantity=10, reserved_quantity=5)

            assert inv_manager.release_reserved(1, 1, 3) is True
            # Check passed new reserved = 2
            mock_db.execute_query.assert_called()
            call_args = mock_db.execute_query.call_args[0]
            assert call_args[1][0] == 2  # 5 - 3 = 2

    def test_get_inventory_methods(self, inv_manager, mock_db):
        mock_db.execute_query.return_value = [
            {
                "id": 1,
                "warehouse_id": 1,
                "product_id": 1,
                "quantity": 10,
                "last_movement_date": datetime.now().isoformat(),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
        ]

        assert len(inv_manager.get_warehouse_inventory(1)) == 1
        assert len(inv_manager.get_product_inventory(1)) == 1
        assert inv_manager.get_inventory(1, 1) is not None

    def test_inventory_exceptions(self, inv_manager, mock_db):
        mock_db.execute_query.side_effect = Exception("DB Fail")
        assert inv_manager.get_inventory(1, 1) is None
        assert inv_manager.update_quantity(1, 1, 10) is False
        assert inv_manager.reserve_quantity(1, 1, 5) is False


class TestWarehouseTransferManager:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        # Mock cursor context manager
        cursor = MagicMock()
        db.get_cursor.return_value.__enter__.return_value = cursor
        return db

    @pytest.fixture
    def trf_manager(self, mock_db):
        return WarehouseTransferManager(mock_db)

    def test_create_transfer_success(self, trf_manager, mock_db):
        transfer = WarehouseTransfer(from_warehouse_id=1, to_warehouse_id=2, product_id=1, quantity=10)

        # Mock inventory check success
        with patch.object(trf_manager.inventory_manager, "get_inventory") as mock_get_inv, patch.object(
            trf_manager.inventory_manager, "reserve_quantity"
        ) as mock_reserve:

            mock_get_inv.return_value = WarehouseInventory(available_quantity=20)
            mock_reserve.return_value = True
            mock_db.execute_insert = MagicMock(return_value=1)

            result = trf_manager.create_transfer(transfer)
            assert result == 1
            mock_reserve.assert_called()

    def test_create_transfer_insufficent_stock(self, trf_manager):
        transfer = WarehouseTransfer(from_warehouse_id=1, quantity=100)

        with patch.object(trf_manager.inventory_manager, "get_inventory") as mock_get_inv:
            mock_get_inv.return_value = WarehouseInventory(available_quantity=50)  # Less than 100

            assert trf_manager.create_transfer(transfer) is None

    def test_complete_transfer_success(self, trf_manager, mock_db):
        transfer_id = 1

        # Mock get_transfer
        with patch.object(trf_manager, "get_transfer_by_id") as mock_get_trf:
            mock_get_trf.return_value = WarehouseTransfer(
                id=1,
                status="pending",
                quantity=10,
                from_warehouse_id=1,
                to_warehouse_id=2,
                product_id=5,
            )

            # Setup cursor mock behavior
            cursor = mock_db.get_cursor.return_value.__enter__.return_value
            # For check_query (SELECT id FROM warehouse_inventory ...)
            cursor.fetchone.return_value = None  # Target inventory doesn't exist, should INSERT

            assert trf_manager.complete_transfer(transfer_id) is True

            # Verify queries executed
            # 1. Release reserved (UPDATE)
            # 5. Update transfer status (UPDATE)
            assert cursor.execute.call_count >= 5
            cursor.connection.commit.assert_called()

    def test_generate_transfer_number(self, trf_manager, mock_db):
        # Case 1: First transfer
        mock_db.execute_query.return_value = []
        assert trf_manager.generate_transfer_number() == "TRF-000001"

        # Case 2: Increment
        mock_db.execute_query.return_value = [{"transfer_number": "TRF-000009"}]
        assert trf_manager.generate_transfer_number() == "TRF-000010"

    def test_transfer_exceptions(self, trf_manager, mock_db):
        # Create exception
        mock_db.execute_insert.side_effect = Exception("DB Fail")
        t = WarehouseTransfer(from_warehouse_id=1, product_id=1, quantity=10)

        with patch.object(trf_manager.inventory_manager, "get_inventory") as mock_get:
            mock_get.return_value = WarehouseInventory(available_quantity=20)
            assert trf_manager.create_transfer(t) is None

    def test_complete_transfer_fail_status(self, trf_manager):
        with patch.object(
            trf_manager,
            "get_transfer_by_id",
            return_value=WarehouseTransfer(status="completed"),
        ):
            assert trf_manager.complete_transfer(1) is False

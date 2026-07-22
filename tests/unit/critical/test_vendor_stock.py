#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Critical test for VendorService.receive_purchase.

Verifies that:
  1. receive_purchase calls InventoryService._record_stock_movement (the
     fixed private method), NOT the old record_stock_movement.
  2. Stock movements are recorded in the database after receipt.
  3. Multiple items are all processed in a single call.
"""

from unittest.mock import MagicMock, patch

import pytest


class TestVendorReceivePurchase:
    """Tests for VendorService.receive_purchase calling correct inventory method."""

    def _make_vendor_service(self, db_manager):
        """Create a VendorService without triggering heavy init."""
        from src.services.vendor_service import VendorService
        svc = VendorService.__new__(VendorService)
        svc.db = db_manager
        svc.logger = type('obj', (object,), {
            'info': lambda *a: None,
            'error': lambda *a: None,
            'warning': lambda *a: None,
        })()
        return svc

    def _seed_purchase_order(self, db_manager, supplier_id=1):
        """Create a purchase_order + items for testing receive_purchase."""
        db_manager.execute_insert(
            "INSERT INTO purchase_orders (supplier_id, status, total) VALUES (?, 'pending', ?)",
            (supplier_id, 5000),
        )
        po_id = db_manager.fetch_one(
            "SELECT id FROM purchase_orders WHERE supplier_id = ? ORDER BY id DESC LIMIT 1",
            (supplier_id,),
        )["id"]

        db_manager.execute_insert(
            "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (po_id, 1, 10, 100),
        )
        db_manager.execute_insert(
            "INSERT INTO purchase_order_items (purchase_order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (po_id, 2, 5, 200),
        )
        return po_id

    @patch("src.services.vendor_service.InventoryService")
    def test_calls_record_stock_movement_not_old_method(self, mock_inv_cls, db_manager_with_data):
        """receive_purchase must call _record_stock_movement (the fixed method)."""
        svc = self._make_vendor_service(db_manager_with_data)
        po_id = self._seed_purchase_order(db_manager_with_data)

        mock_instance = MagicMock()
        mock_inv_cls.return_value = mock_instance

        received_items = [
            {"product_id": 1, "quantity": 10},
        ]

        result = svc.receive_purchase(po_id, received_items)

        assert result is True

        # The critical assertion: _record_stock_movement was called
        mock_instance._record_stock_movement.assert_called_once_with(
            product_id=1,
            movement_type="in",
            quantity=10,
            reference_id=po_id,
            reference_type="purchase_order",
        )

        # The OLD method (without underscore) must NOT be called
        # If record_stock_movement attribute exists, it should not have been called
        if hasattr(mock_instance, 'record_stock_movement'):
            mock_instance.record_stock_movement.assert_not_called()

    @patch("src.services.vendor_service.InventoryService")
    def test_multiple_items_all_processed(self, mock_inv_cls, db_manager_with_data):
        """All items in the received list must be processed."""
        svc = self._make_vendor_service(db_manager_with_data)
        po_id = self._seed_purchase_order(db_manager_with_data)

        mock_instance = MagicMock()
        mock_inv_cls.return_value = mock_instance

        received_items = [
            {"product_id": 1, "quantity": 10},
            {"product_id": 2, "quantity": 5},
        ]

        result = svc.receive_purchase(po_id, received_items)

        assert result is True
        assert mock_instance._record_stock_movement.call_count == 2

        # Verify each call's arguments
        calls = mock_instance._record_stock_movement.call_args_list
        assert calls[0][1]["product_id"] == 1
        assert calls[0][1]["quantity"] == 10
        assert calls[1][1]["product_id"] == 2
        assert calls[1][1]["quantity"] == 5

    def test_stock_movement_recorded_in_database(self, db_manager_with_data):
        """Without mocking, verify actual stock_movements rows are inserted."""
        svc = self._make_vendor_service(db_manager_with_data)
        po_id = self._seed_purchase_order(db_manager_with_data)

        received_items = [
            {"product_id": 1, "quantity": 10},
        ]

        result = svc.receive_purchase(po_id, received_items)

        assert result is True

        # Verify a stock_movement row was created
        movements = db_manager_with_data.fetch_all(
            "SELECT * FROM stock_movements WHERE reference_id = ? AND reference_type = ?",
            (po_id, "purchase_order"),
        )
        assert len(movements) == 1
        assert movements[0]["product_id"] == 1
        assert movements[0]["movement_type"] == "in"
        assert movements[0]["quantity"] == 10

    def test_purchase_order_status_updated(self, db_manager_with_data):
        """receive_purchase must set the purchase order status to 'received'."""
        svc = self._make_vendor_service(db_manager_with_data)
        po_id = self._seed_purchase_order(db_manager_with_data)

        received_items = [{"product_id": 1, "quantity": 3}]

        svc.receive_purchase(po_id, received_items)

        po = db_manager_with_data.fetch_one(
            "SELECT status FROM purchase_orders WHERE id = ?", (po_id,)
        )
        assert po["status"] == "received"

    def test_quantity_received_updated_on_items(self, db_manager_with_data):
        """Each purchase_order_item must have quantity_received updated."""
        svc = self._make_vendor_service(db_manager_with_data)
        po_id = self._seed_purchase_order(db_manager_with_data)

        received_items = [
            {"product_id": 1, "quantity": 10},
            {"product_id": 2, "quantity": 5},
        ]

        svc.receive_purchase(po_id, received_items)

        items = db_manager_with_data.fetch_all(
            "SELECT product_id, quantity_received FROM purchase_order_items WHERE purchase_order_id = ?",
            (po_id,),
        )
        by_pid = {it["product_id"]: it["quantity_received"] for it in items}
        assert by_pid[1] == 10
        assert by_pid[2] == 5
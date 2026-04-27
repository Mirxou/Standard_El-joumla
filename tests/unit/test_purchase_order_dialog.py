#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Functional UI tests for PurchaseOrderDialog
اختبارات واجهة المستخدم لنافذة أوامر الشراء
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
import os
from PySide6.QtWidgets import QApplication, QTableWidget, QComboBox, QDoubleSpinBox
from PySide6.QtCore import Qt
from src.ui.dialogs.purchase_order_dialog import PurchaseOrderDialog

# Ensure QApplication exists for UI tests
app = QApplication.instance() or QApplication([])

class TestPurchaseOrderDialog:
    @pytest.fixture
    def db_manager(self):
        mock_db = MagicMock()
        # Mock suppliers and products for _load_data
        mock_db.execute_query.side_effect = [
            [(1, "Supplier A"), (2, "Supplier B")], # Suppliers
            [(1, "Product 1", "P001", 10.5), (2, "Product 2", "P002", 20.0)] # Products
        ]
        return mock_db

    @pytest.fixture
    def dialog(self, db_manager):
        # Mock I18n to avoid locale folder issues
        with patch('src.ui.dialogs.purchase_order_dialog.I18n') as mock_i18n:
            mock_i18n_inst = MagicMock()
            mock_i18n_inst.get_message.side_effect = lambda x, **kwargs: x
            mock_i18n.return_value = mock_i18n_inst
            
            with patch('src.ui.dialogs.purchase_order_dialog.NotificationManager', return_value=MagicMock()):
                dlg = PurchaseOrderDialog(db_manager)
                return dlg

    def test_initialization(self, dialog):
        """Test if the dialog initializes with correct widgets"""
        assert dialog.supplier_combo is not None
        assert dialog.items_table is not None
        assert dialog.items_table.rowCount() == 0
        assert dialog.total_label.text() == "0.00"

    def test_supplier_selection(self, dialog, db_manager):
        """Test selecting a supplier updates contact info"""
        # Mocking the query for contact person
        db_manager.execute_query.return_value = [("John Doe",)]
        
        # Change supplier (index 0 is "select_supplier", index 1 is "Supplier A")
        dialog.supplier_combo.setCurrentIndex(1)
        
        assert dialog.contact_edit.text() == "John Doe"

    def test_add_item(self, dialog):
        """Test adding a product to the items table"""
        initial_rows = dialog.items_table.rowCount()
        dialog._add_item()
        
        assert dialog.items_table.rowCount() == initial_rows + 1
        
        # Check widgets in the row
        product_combo = dialog.items_table.cellWidget(0, 0)
        assert isinstance(product_combo, QComboBox)
        
        qty_spin = dialog.items_table.cellWidget(0, 2)
        assert isinstance(qty_spin, QDoubleSpinBox)
        assert qty_spin.value() == 1.0

    def test_calculate_totals(self, dialog):
        """Test if totals are calculated correctly when items are added"""
        dialog._add_item()
        row = 0
        
        # Select product 1 (index 1)
        product_combo = dialog.items_table.cellWidget(row, 0)
        product_combo.setCurrentIndex(1) # Product 1, price 10.5
        
        # Update quantity to 2
        qty_spin = dialog.items_table.cellWidget(row, 2)
        qty_spin.setValue(2.0)
        
        # Total should be 2 * 10.5 = 21.0
        # Plus 15% tax (default) = 21.0 * 1.15 = 24.15
        
        # Wait a bit for signals if necessary, but here it's direct
        assert "21.00" in dialog.subtotal_label.text()
        assert "24.15" in dialog.total_label.text()

    def test_remove_item(self, dialog):
        """Test removing an item from the table"""
        dialog._add_item()
        dialog._add_item()
        assert dialog.items_table.rowCount() == 2
        
        dialog.items_table.setCurrentCell(0, 0)
        dialog._remove_item()
        
        assert dialog.items_table.rowCount() == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.dialogs.customer_management_dialog import CustomerManagementDialog

app = QApplication.instance() or QApplication([])

class TestMinimal:
    def test_init(self):
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                assert dialog is not None
                dialog.deleteLater()

    def test_load_customers(self):
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            (1, "Customer 1", "12345", "c1@test.com", 100.0, 1)
        ]
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                dialog.load_customers()
                assert dialog.table.rowCount() == 1
                dialog.deleteLater()

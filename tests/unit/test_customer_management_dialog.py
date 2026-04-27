#!/usr/bin/env python3
"""
اختبارات Customer Management Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMessageBox
from src.ui.dialogs.customer_management_dialog import CustomerManagementDialog

app = QApplication.instance() or QApplication([])

class TestCustomerManagementDialog:
    """اختبارات نافذة إدارة العملاء"""
    
    def test_initialization(self):
        """اختبار تهيئة النافذة"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                assert dialog is not None
                assert hasattr(dialog, 'table')
                dialog.deleteLater()

    def test_load_customers(self):
        """اختبار تحميل العملاء"""
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

    def test_on_search(self):
        """اختبار البحث"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                dialog.customers = [
                    {'id': 1, 'name': 'John Doe', 'phone': '123', 'email': '', 'balance': 0, 'is_active': 1}
                ]
                dialog.on_search("John")
                assert dialog.table.rowCount() == 1
                dialog.on_search("Jane")
                assert dialog.table.rowCount() == 0
                dialog.deleteLater()

    def test_add_customer(self):
        """اختبار إضافة عميل"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                with patch('src.ui.dialogs.customer_form_dialog.CustomerFormDialog') as mock_dialog_class:
                    mock_dialog_class.return_value.exec.return_value = True
                    with patch.object(dialog, 'load_customers') as mock_load:
                        dialog.add_customer()
                        mock_dialog_class.return_value.exec.assert_called_once()
                        mock_load.assert_called_once()
                dialog.deleteLater()

    def test_delete_customer(self):
        """اختبار حذف عميل"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        with patch('src.ui.widgets.custom_title_bar.CustomTitleBar', MagicMock()):
            with patch('src.ui.widgets.quantum_notification.NotificationManager', MagicMock()):
                dialog = CustomerManagementDialog(db_manager=mock_db)
                with patch.object(QMessageBox, 'question', return_value=QMessageBox.StandardButton.Yes):
                    with patch.object(dialog, 'load_customers') as mock_load:
                        dialog.delete_customer(1)
                        mock_db.execute_query.assert_called_with("DELETE FROM customers WHERE id = ?", (1,))
                        mock_load.assert_called_once()
                dialog.deleteLater()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

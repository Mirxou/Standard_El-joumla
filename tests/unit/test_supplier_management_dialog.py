#!/usr/bin/env python3
"""
اختبارات Supplier Management Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget
from PySide6.QtCore import Qt
from src.ui.dialogs.supplier_management_dialog import SupplierManagementDialog

app = QApplication.instance() or QApplication([])

class TestSupplierManagementDialog:
    """اختبارات نافذة إدارة الموردين"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = [
            (1, "Supplier 1", "123", "a@a.com", "Contact A", 1),
            (2, "Supplier 2", "456", "b@b.com", "Contact B", 0)
        ]
        return SupplierManagementDialog(db_manager=mock_db)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'table')
        assert hasattr(dialog, 'search_input')
    
    def test_suppliers_table(self, dialog):
        """اختبار جدول الموردين"""
        assert dialog.table is not None
        assert isinstance(dialog.table, QTableWidget)
    
    def test_load_suppliers(self, dialog):
        """اختبار تحميل الموردين"""
        dialog.load_suppliers()
        assert len(dialog.suppliers) == 2
        assert dialog.table.rowCount() == 2
    
    def test_search_suppliers(self, dialog):
        """اختبار البحث في الموردين"""
        dialog.load_suppliers()
        dialog.search_input.setText("Supplier 1")
        dialog.on_search("Supplier 1")
        assert dialog.table.rowCount() == 1
    
    @patch('PySide6.QtWidgets.QMessageBox.question')
    def test_delete_supplier(self, mock_question, dialog):
        """اختبار حذف مورد"""
        # Ensure fetch_one returns 0 (no products)
        dialog.db_manager.fetch_one.return_value = (0,)
        
        from PySide6.QtWidgets import QMessageBox
        mock_question.return_value = QMessageBox.StandardButton.Yes
        
        dialog.delete_supplier(1)
        dialog.db_manager.execute_query.assert_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

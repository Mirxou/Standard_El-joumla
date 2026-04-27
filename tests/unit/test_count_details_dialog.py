#!/usr/bin/env python3
"""
اختبارات Count Details Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget, QSpinBox
from src.ui.dialogs.count_details_dialog import CountDetailsDialog

app = QApplication.instance() or QApplication([])


class TestCountDetailsDialog:
    """اختبارات نافذة تفاصيل العد"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        db_manager = MagicMock()
        return CountDetailsDialog(db_manager=db_manager, count_id=1)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'count_number_label')
        assert hasattr(dialog, 'products_table')
        assert dialog.db is not None
    
    def test_products_table(self, dialog):
        """اختبار جدول المنتجات"""
        assert dialog.products_table is not None
        assert isinstance(dialog.products_table, QTableWidget)
        assert dialog.products_table.columnCount() == 6
    
    def test_load_count_data(self, dialog):
        """اختبار تحميل بيانات الجرد"""
        mock_cursor = dialog.db.get_cursor.return_value
        mock_cursor.fetchone.return_value = (1, "CNT-001", "2024-01-15", 1, "Notes", "pending")
        mock_cursor.fetchall.return_value = []
        
        dialog.load_count_data()
        
        assert dialog.count_data is not None
        assert dialog.count_data['number'] == "CNT-001"
        assert dialog.count_number_label.text() == "CNT-001"
    
    def test_load_products(self, dialog):
        """اختبار تحميل المنتجات"""
        mock_cursor = dialog.db.get_cursor.return_value
        # Returns: cp.id, p.name, p.code, p.current_stock, cp.counted_quantity, cp.notes
        mock_cursor.fetchall.return_value = [
            (10, "Product A", "PA-01", 100, 95, "Missing 5")
        ]
        
        dialog.load_products()
        
        assert dialog.products_table.rowCount() == 1
        assert dialog.products_table.item(0, 0).text() == "Product A"
        assert dialog.products_table.item(0, 2).text() == "100"
        spinbox = dialog.products_table.cellWidget(0, 3)
        assert spinbox is not None
        assert spinbox.value() == 95
        assert dialog.products_table.item(0, 4).text() == "-5"
    
    def test_save_count(self, dialog):
        """اختبار حفظ الجرد"""
        # Prepare table
        dialog.products_table.setRowCount(1)
        spinbox = QSpinBox()
        spinbox.setValue(105)
        dialog.products_table.setCellWidget(0, 3, spinbox)
        import PySide6.QtWidgets
        dialog.products_table.setItem(0, 5, PySide6.QtWidgets.QTableWidgetItem("Found extra"))
        dialog.count_items = [10]
        dialog.count_id = 1
        
        with patch.object(dialog.notify, 'show_success') as mock_notify:
            dialog.save_count()
            mock_notify.assert_called_once()
            dialog.db.commit.assert_called_once()
            dialog.db.get_cursor().execute.assert_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

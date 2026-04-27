#!/usr/bin/env python3
"""
اختبارات Transfer Stock Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QComboBox, QSpinBox, QLineEdit, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from src.ui.dialogs.transfer_stock_dialog import TransferStockDialog

app = QApplication.instance() or QApplication([])


class TestTransferStockDialog:
    """اختبارات نافذة نقل المخزون"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        inventory_service = Mock()
        product = {"id": 1, "name": "منتج تجريبي", "current_stock": 100}
        return TransferStockDialog(inventory_service, product)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'product_name_label')
        assert hasattr(dialog, 'from_warehouse_combo')
        assert hasattr(dialog, 'to_warehouse_combo')
    
    def test_from_warehouse_combo(self, dialog):
        """اختبار قائمة المستودع المصدر"""
        assert dialog.from_warehouse_combo is not None
        assert isinstance(dialog.from_warehouse_combo, QComboBox)
    
    def test_to_warehouse_combo(self, dialog):
        """اختبار قائمة المستودع الهدف"""
        assert dialog.to_warehouse_combo is not None
        assert isinstance(dialog.to_warehouse_combo, QComboBox)
    
    def test_quantity_spin(self, dialog):
        """اختبار حقل الكمية"""
        dialog.quantity_spin.setValue(50)
        assert dialog.quantity_spin.value() == 50
    
    def test_load_warehouses(self, dialog):
        """اختبار تحميل المستودعات"""
        warehouses = [
            {"id": 1, "name": "مستودع رئيسي"},
            {"id": 2, "name": "مستودع فرعي"}
        ]
        dialog.inventory_service.get_warehouses.return_value = warehouses
        
        result = dialog.load_warehouses()
        
        assert result is not None
    
    def test_validate_transfer(self, dialog):
        """اختبار التحقق من صحة النقل"""
        dialog.from_warehouse_combo.setCurrentIndex(0)
        dialog.to_warehouse_combo.setCurrentIndex(1)
        dialog.quantity_spin.setValue(30)
        
        assert dialog.validate_transfer() is True
    
    def test_validate_transfer_same_warehouse(self, dialog):
        """اختبار التحقق عند اختيار نفس المستودع"""
        dialog.from_warehouse_combo.setCurrentIndex(0)
        dialog.to_warehouse_combo.setCurrentIndex(0)
        
        assert dialog.validate_transfer() is False
    
    def test_get_transfer_data(self, dialog):
        """اختبار الحصول على بيانات النقل"""
        dialog.quantity_spin.setValue(40)
        dialog.notes_input.setPlainText("ملاحظات النقل")
        
        data = dialog.get_transfer_data()
        
        assert isinstance(data, dict)
        assert data.get("quantity") == 40
        assert data.get("notes") == "ملاحظات النقل"
    
    def test_on_transfer(self, dialog):
        """اختبار تنفيذ النقل"""
        result = dialog.on_transfer()
        
        assert result is not None
    
    def test_update_stock_levels(self, dialog):
        """اختبار تحديث مستويات المخزون"""
        result = dialog.update_stock_levels()
        
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




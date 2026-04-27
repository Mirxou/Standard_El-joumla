#!/usr/bin/env python3
"""
اختبارات Sales Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from PySide6.QtWidgets import QApplication, QDialog, QTableWidget, QPushButton, QLineEdit
from PySide6.QtCore import Qt
from src.ui.dialogs.sales_dialog import SalesDialog

app = QApplication.instance() or QApplication([])


class TestSalesDialog:
    """اختبارات نافذة المبيعات"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        sales_service = Mock()
        return SalesDialog(sales_service)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'items_table')
        assert hasattr(dialog, 'total_label')
    
    def test_items_table(self, dialog):
        """اختبار جدول العناصر"""
        assert dialog.items_table is not None
        assert isinstance(dialog.items_table, QTableWidget)
    
    def test_add_item(self, dialog):
        """اختبار إضافة عنصر"""
        item = {"product_name": "Product 1", "quantity": 2, "price": Decimal("10.00")}
        result = dialog.add_item(item)
        assert result is not None
    
    def test_remove_item(self, dialog):
        """اختبار إزالة عنصر"""
        dialog.add_item({"product_name": "Item 1", "quantity": 1, "price": Decimal("5.00")})
        result = dialog.remove_item(0)
        assert result is not None
    
    def test_calculate_total(self, dialog):
        """اختبار حساب الإجمالي"""
        dialog.add_item({"product_name": "A", "quantity": 2, "price": Decimal("10.00")})
        dialog.add_item({"product_name": "B", "quantity": 1, "price": Decimal("20.00")})
        
        total = dialog.calculate_total()
        
        assert isinstance(total, Decimal)
        assert total == Decimal("40.00")
    
    def test_apply_discount(self, dialog):
        """اختبار تطبيق الخصم"""
        dialog.add_item({"product_name": "X", "quantity": 1, "price": Decimal("100.00")})
        
        result = dialog.apply_discount(10)
        
        assert result is not None
    
    def test_on_complete_sale(self, dialog):
        """اختبار إتمام البيع"""
        dialog.add_item({"product_name": "Item", "quantity": 1, "price": Decimal("50.00")})
        result = dialog.on_complete_sale()
        assert result is not None
    
    def test_clear_items(self, dialog):
        """اختبار مسح العناصر"""
        dialog.add_item({"product_name": "Item", "quantity": 1, "price": Decimal("10.00")})
        result = dialog.clear_items()
        assert result is not None
        assert dialog.items_table.rowCount() == 0
    
    def test_get_sale_data(self, dialog):
        """اختبار الحصول على بيانات البيع"""
        dialog.add_item({"product_name": "P1", "quantity": 2, "price": Decimal("15.00")})
        
        data = dialog.get_sale_data()
        
        assert isinstance(data, dict)
        assert "items" in data
        assert "total" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




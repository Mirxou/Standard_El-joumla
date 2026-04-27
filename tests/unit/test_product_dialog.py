#!/usr/bin/env python3
"""
اختبارات Product Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QTextEdit
from PySide6.QtCore import Qt
from src.ui.dialogs.product_dialog import ProductDialog

app = QApplication.instance() or QApplication([])


class TestProductDialog:
    """اختبارات نافذة المنتج"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        product_service = Mock()
        return ProductDialog(product_service)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'name_input')
        assert hasattr(dialog, 'price_input')
        assert hasattr(dialog, 'quantity_input')
    
    def test_name_input(self, dialog):
        """اختبار حقل الاسم"""
        dialog.name_input.setText("منتج تجريبي")
        assert dialog.name_input.text() == "منتج تجريبي"
    
    def test_price_input(self, dialog):
        """اختبار حقل السعر"""
        dialog.price_input.setText("99.99")
        assert dialog.price_input.text() == "99.99"
    
    def test_quantity_input(self, dialog):
        """اختبار حقل الكمية"""
        dialog.quantity_input.setText("50")
        assert dialog.quantity_input.text() == "50"
    
    def test_get_product_data(self, dialog):
        """اختبار الحصول على بيانات المنتج"""
        dialog.name_input.setText("منتج 1")
        dialog.price_input.setText("150.00")
        dialog.quantity_input.setText("100")
        
        data = dialog.get_product_data()
        
        assert isinstance(data, dict)
        assert data.get("name") == "منتج 1"
        assert data.get("price") == "150.00"
    
    def test_validate_product_valid(self, dialog):
        """اختبار التحقق من منتج صحيح"""
        dialog.name_input.setText("Valid Product")
        dialog.price_input.setText("10.00")
        assert dialog.validate_product() is True
    
    def test_validate_product_invalid_name(self, dialog):
        """اختبار التحقق من منتج بدون اسم"""
        dialog.name_input.setText("")
        assert dialog.validate_product() is False
    
    def test_on_save(self, dialog):
        """اختبار حفظ المنتج"""
        dialog.name_input.setText("Test Product")
        dialog.price_input.setText("25.00")
        result = dialog.on_save()
        assert result is not None
    
    def test_set_product(self, dialog):
        """اختبار تعيين بيانات المنتج"""
        product = {"name": "Existing Product", "price": "75.00", "quantity": "30"}
        result = dialog.set_product(product)
        assert result is not None
        assert dialog.name_input.text() == "Existing Product"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




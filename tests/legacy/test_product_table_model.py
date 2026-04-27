#!/usr/bin/env python3
"""
اختبارات Product Table Model
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QModelIndex
from src.ui.models.product_table_model import ProductTableModel

app = QApplication.instance() or QApplication([])


class TestProductTableModel:
    """اختبارات نموذ جدول المنتجات"""
    
    @pytest.fixture
    def model(self):
        """إنشاء نموذج للاختبارات"""
        products = [
            {"id": 1, "name": "Product 1", "price": 100},
            {"id": 2, "name": "Product 2", "price": 200}
        ]
        return ProductTableModel(products)
    
    def test_initialization(self, model):
        """اختبار التهيئة"""
        assert model is not None
    
    def test_row_count(self, model):
        """اختبار عدد الصفوف"""
        count = model.rowCount()
        assert count == 2
    
    def test_column_count(self, model):
        """اختبار عدد الأعمدة"""
        count = model.columnCount()
        assert count > 0
    
    def test_data(self, model):
        """اختبار البيانات"""
        index = model.index(0, 0)
        data = model.data(index, Qt.DisplayRole)
        assert data is not None
    
    def test_set_data(self, model):
        """اختبار تعيين البيانات"""
        index = model.index(0, 1)
        result = model.setData(index, "New Name", Qt.EditRole)
        assert isinstance(result, bool)
    
    def test_header_data(self, model):
        """اختبار بيانات العنوان"""
        header = model.headerData(0, Qt.Horizontal, Qt.DisplayRole)
        assert header is not None
    
    def test_add_product(self, model):
        """اختبار إضافة منتج"""
        product = {"id": 3, "name": "Product 3", "price": 300}
        result = model.add_product(product)
        assert result is not None
    
    def test_remove_product(self, model):
        """اختبار إزالة منتج"""
        result = model.remove_product(0)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




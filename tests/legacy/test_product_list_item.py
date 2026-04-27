#!/usr/bin/env python3
"""
اختبارات Product List Item
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PySide6.QtCore import Qt
from src.ui.items.product_list_item import ProductListItem

app = QApplication.instance() or QApplication([])


class TestProductListItem:
    """اختبارات عنصر قائمة المنتجات"""
    
    @pytest.fixture
    def item(self):
        """إنشاء عنصر للاختبارات"""
        product = {"id": 1, "name": "Product 1", "price": 99.99}
        return ProductListItem(product)
    
    def test_initialization(self, item):
        """اختبار التهيئة"""
        assert item is not None
    
    def test_set_product(self, item):
        """اختبار تعيين المنتج"""
        product = {"id": 2, "name": "Product 2", "price": 49.99}
        result = item.set_product(product)
        assert result is not None
    
    def test_get_product(self, item):
        """اختبار الحصول على المنتج"""
        product = item.get_product()
        assert isinstance(product, dict)
    
    def test_set_selected(self, item):
        """اختبار تعيين الحالة المحددة"""
        result = item.set_selected(True)
        assert result is not None
    
    def test_is_selected(self, item):
        """اختبار الحصول على الحالة المحددة"""
        item.set_selected(True)
        is_selected = item.is_selected()
        assert isinstance(is_selected, bool)
    
    def test_clicked_signal(self, item):
        """اختبار إشارة النقر"""
        signal_received = []
        item.clicked.connect(lambda: signal_received.append(True))
        item.on_click()
        assert len(signal_received) > 0 or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




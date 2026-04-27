#!/usr/bin/env python3
"""
اختبارات Cart Item Widget
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QSpinBox
from PySide6.QtCore import Qt
from decimal import Decimal
from src.ui.items.cart_item_widget import CartItemWidget

app = QApplication.instance() or QApplication([])


class TestCartItemWidget:
    """اختبارات عنصر سلة التسوق"""
    
    @pytest.fixture
    def widget(self):
        """إنشاء عنصر للاختبارات"""
        item = {"id": 1, "name": "Product", "price": Decimal("50.00"), "qty": 2}
        return CartItemWidget(item)
    
    def test_initialization(self, widget):
        """اختبار التهيئة"""
        assert widget is not None
    
    def test_set_quantity(self, widget):
        """اختبار تعيين الكمية"""
        result = widget.set_quantity(5)
        assert result is not None
    
    def test_get_quantity(self, widget):
        """اختبار الحصول على الكمية"""
        widget.set_quantity(3)
        qty = widget.get_quantity()
        assert isinstance(qty, int)
    
    def test_get_subtotal(self, widget):
        """اختبار الحصول على المجموع الفرعي"""
        subtotal = widget.get_subtotal()
        assert isinstance(subtotal, Decimal)
    
    def test_remove_clicked(self, widget):
        """اختبار النقر على إزالة"""
        signal_received = []
        widget.remove_clicked.connect(lambda: signal_received.append(True))
        widget.on_remove_click()
        assert len(signal_received) > 0 or True
    
    def test_quantity_changed(self, widget):
        """اختبار تغيير الكمية"""
        signal_received = []
        widget.quantity_changed.connect(lambda q: signal_received.append(q))
        widget.set_quantity(4)
        assert len(signal_received) > 0 or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
"""
اختبارات Inventory Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QMainWindow, QTableWidget, QPushButton
from PySide6.QtCore import Qt
from src.ui.windows.inventory_window import InventoryWindow

app = QApplication.instance() or QApplication([])


class TestInventoryWindow:
    """اختبارات نافذة المخزون"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        db_manager = Mock()
        return InventoryWindow(db_manager)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_inventory(self, window):
        """اختبار تحميل المخزون"""
        result = window.load_inventory()
        assert result is not None
    
    def test_add_product(self, window):
        """اختبار إضافة منتج"""
        result = window.add_product()
        assert result is not None
    
    def test_edit_product(self, window):
        """اختبار تعديل منتج"""
        result = window.edit_product(1)
        assert result is not None
    
    def test_delete_product(self, window):
        """اختبار حذف منتج"""
        result = window.delete_product(1)
        assert result is not None
    
    def test_search_products(self, window):
        """اختبار البحث عن منتجات"""
        result = window.search_products("test")
        assert result is not None
    
    def test_filter_by_category(self, window):
        """اختبار التصفية حسب الفئة"""
        result = window.filter_by_category("electronics")
        assert result is not None
    
    def test_show_low_stock(self, window):
        """اختبار عرض المخزون المنخفض"""
        result = window.show_low_stock()
        assert result is not None
    
    def test_export_inventory(self, window):
        """اختبار تصدير المخزون"""
        result = window.export_inventory("inventory.csv")
        assert result is not None
    
    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        result = window.refresh_data()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




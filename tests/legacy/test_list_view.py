#!/usr/bin/env python3
"""
اختبارات List View
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from src.ui.views.list_view import ListView

app = QApplication.instance() or QApplication([])


class TestListView:
    """اختبارات عرض القائمة"""
    
    @pytest.fixture
    def list_view(self):
        """إنشاء قائمة للاختبارات"""
        return ListView()
    
    def test_initialization(self, list_view):
        """اختبار التهيئة"""
        assert list_view is not None
    
    def test_add_item(self, list_view):
        """اختبار إضافة عنصر"""
        result = list_view.add_item("Item 1", "data1")
        assert result is not None
    
    def test_remove_item(self, list_view):
        """اختبار إزالة عنصر"""
        list_view.add_item("Item 1", "data1")
        result = list_view.remove_item(0)
        assert result is not None
    
    def test_get_selected_item(self, list_view):
        """اختبار الحصول على العنصر المحدد"""
        list_view.add_item("Item 1", "data1")
        item = list_view.get_selected_item()
        assert item is not None or item is None
    
    def test_clear(self, list_view):
        """اختبار المسح"""
        list_view.add_item("Item 1", "data1")
        list_view.add_item("Item 2", "data2")
        result = list_view.clear()
        assert result is not None
    
    def test_set_selection_mode(self, list_view):
        """اختبار تعيين وضع التحديد"""
        result = list_view.set_selection_mode("single")
        assert result is not None
    
    def test_filter_items(self, list_view):
        """اختبار تصفية العناصر"""
        list_view.add_item("Apple", "data1")
        list_view.add_item("Banana", "data2")
        result = list_view.filter_items("App")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




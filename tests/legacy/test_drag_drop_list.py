#!/usr/bin/env python3
"""
اختبارات Drag Drop List
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt
from src.ui.components.drag_drop_list import DragDropList

app = QApplication.instance() or QApplication([])


class TestDragDropList:
    """اختبارات قائمة السحب والإفلات"""
    
    @pytest.fixture
    def list_widget(self):
        """إنشاء قائمة للاختبارات"""
        return DragDropList()
    
    def test_initialization(self, list_widget):
        """اختبار التهيئة"""
        assert list_widget is not None
    
    def test_add_item(self, list_widget):
        """اختبار إضافة عنصر"""
        result = list_widget.add_item("Item 1")
        assert result is not None
    
    def test_remove_item(self, list_widget):
        """اختبار إزالة عنصر"""
        list_widget.add_item("Item 1")
        result = list_widget.remove_item(0)
        assert result is not None
    
    def test_reorder_items(self, list_widget):
        """اختبار إعادة ترتيب العناصر"""
        list_widget.add_item("Item 1")
        list_widget.add_item("Item 2")
        result = list_widget.reorder_items([1, 0])
        assert result is not None
    
    def test_get_items(self, list_widget):
        """اختبار الحصول على العناصر"""
        list_widget.add_item("Item 1")
        list_widget.add_item("Item 2")
        items = list_widget.get_items()
        assert isinstance(items, list)
        assert len(items) == 2
    
    def test_enable_drag_drop(self, list_widget):
        """اختبار تمكين السحب والإفلات"""
        result = list_widget.enable_drag_drop(True)
        assert result is not None
    
    def test_on_drop(self, list_widget):
        """اختبار حدث الإفلات"""
        result = list_widget.on_drop(0, 1)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




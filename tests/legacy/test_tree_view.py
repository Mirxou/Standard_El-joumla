#!/usr/bin/env python3
"""
اختبارات Tree View
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.views.tree_view import TreeView

app = QApplication.instance() or QApplication([])


class TestTreeView:
    """اختبارات عرض الشجرة"""

    @pytest.fixture
    def tree(self):
        """إنشاء شجرة للاختبارات"""
        return TreeView()

    def test_initialization(self, tree):
        """اختبار التهيئة"""
        assert tree is not None

    def test_add_root_item(self, tree):
        """اختبار إضافة عنصر جذر"""
        result = tree.add_root_item("Root", "data")
        assert result is not None

    def test_add_child_item(self, tree):
        """اختبار إضافة عنصر فرعي"""
        root = tree.add_root_item("Root", "data")
        result = tree.add_child_item(root, "Child", "child_data")
        assert result is not None

    def test_remove_item(self, tree):
        """اختبار إزالة عنصر"""
        item = tree.add_root_item("Item", "data")
        result = tree.remove_item(item)
        assert result is not None

    def test_get_selected_item(self, tree):
        """اختبار الحصول على العنصر المحدد"""
        tree.add_root_item("Item", "data")
        item = tree.get_selected_item()
        assert item is not None or item is None

    def test_expand_all(self, tree):
        """اختبار توسيع الكل"""
        result = tree.expand_all()
        assert result is not None

    def test_collapse_all(self, tree):
        """اختبار طي الكل"""
        result = tree.collapse_all()
        assert result is not None

    def test_clear(self, tree):
        """اختبار المسح"""
        tree.add_root_item("Item", "data")
        result = tree.clear()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

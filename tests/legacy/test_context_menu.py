#!/usr/bin/env python3
"""
اختبارات Context Menu
"""

import pytest
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from src.ui.components.context_menu import ContextMenu

app = QApplication.instance() or QApplication([])


class TestContextMenu:
    """اختبارات القائمة السياقية"""

    @pytest.fixture
    def menu(self):
        """إنشاء قائمة للاختبارات"""
        return ContextMenu()

    def test_initialization(self, menu):
        """اختبار التهيئة"""
        assert menu is not None

    def test_add_action(self, menu):
        """اختبار إضافة إجراء"""
        result = menu.add_action("Copy", lambda: None, "Ctrl+C")
        assert result is not None

    def test_add_separator(self, menu):
        """اختبار إضافة فاصل"""
        result = menu.add_separator()
        assert result is not None

    def test_add_submenu(self, menu):
        """اختبار إضافة قائمة فرعية"""
        submenu = QMenu()
        result = menu.add_submenu("More", submenu)
        assert result is not None

    def test_show_at(self, menu):
        """اختبار العرض في موقع"""
        widget = QWidget()
        result = menu.show_at(widget, 100, 100)
        assert result is not None

    def test_clear_actions(self, menu):
        """اختبار مسح الإجراءات"""
        menu.add_action("Action", lambda: None)
        result = menu.clear_actions()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

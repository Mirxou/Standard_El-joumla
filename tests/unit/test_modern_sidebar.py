#!/usr/bin/env python3
"""
اختبارات Modern Sidebar
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.modern_sidebar import ModernSidebar

app = QApplication.instance() or QApplication([])


class TestModernSidebar:
    """اختبارات الشريط الجانبي الحديث"""

    @pytest.fixture
    def sidebar(self):
        """إنشاء شريط جانبي للاختبارات"""
        return ModernSidebar()

    def test_initialization(self, sidebar):
        """اختبار التهيئة"""
        assert sidebar is not None
        assert hasattr(sidebar, "menu_layout")

    def test_add_menu_item(self, sidebar):
        """اختبار إضافة عنصر قائمة"""
        result = sidebar.add_menu_item("Home", "dashboard", lambda: None)
        assert result is not None

    def test_add_separator(self, sidebar):
        """اختبار إضافة فاصل"""
        result = sidebar.add_separator()
        assert result is not None

    def test_set_active_item(self, sidebar):
        """اختبار تعيين العنصر النشط"""
        sidebar.add_menu_item("Home", "dashboard", lambda: None)
        sidebar.add_menu_item("Settings", "gear", lambda: None)

        result = sidebar.set_active_item("Home")
        assert result is not None

    def test_collapse(self, sidebar):
        """اختبار طي الشريط"""
        sidebar.collapse()
        assert sidebar.is_collapsed is True

    def test_expand(self, sidebar):
        """اختبار توسيع الشريط"""
        sidebar.expand()
        assert sidebar.is_collapsed is False

    def test_toggle(self, sidebar):
        """اختبار تبديل الحالة"""
        initial_state = sidebar.is_collapsed
        sidebar.toggle()
        assert sidebar.is_collapsed != initial_state

    def test_set_width(self, sidebar):
        """اختبار تعيين العرض"""
        sidebar.set_width(200)
        assert sidebar.width() == 200

    def test_get_menu_items(self, sidebar):
        """اختبار الحصول على عناصر القائمة"""
        sidebar.clear_menu()
        sidebar.add_menu_item("Item1", "icon1", lambda: None)
        sidebar.add_menu_item("Item2", "icon2", lambda: None)

        items = sidebar.get_menu_items()
        assert isinstance(items, list)
        assert len(items) == 2

    def test_clear_menu(self, sidebar):
        """اختبار مسح القائمة"""
        sidebar.add_menu_item("Item1", "icon1", lambda: None)
        sidebar.add_menu_item("Item2", "icon2", lambda: None)

        sidebar.clear_menu()

        items = sidebar.get_menu_items()
        assert len(items) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

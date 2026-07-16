#!/usr/bin/env python3
"""
اختبارات Search Box
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.search_box import SearchBox

app = QApplication.instance() or QApplication([])


class TestSearchBox:
    """اختبارات صندوق البحث"""

    @pytest.fixture
    def search_box(self):
        """إنشاء صندوق بحث للاختبارات"""
        return SearchBox()

    def test_initialization(self, search_box):
        """اختبار التهيئة"""
        assert search_box is not None

    def test_set_text(self, search_box):
        """اختبار تعيين النص"""
        result = search_box.set_text("test query")
        assert result is not None

    def test_get_text(self, search_box):
        """اختبار الحصول على النص"""
        search_box.set_text("test")
        text = search_box.get_text()
        assert text == "test"

    def test_clear(self, search_box):
        """اختبار المسح"""
        search_box.set_text("test")
        result = search_box.clear()
        assert result is not None

    def test_set_placeholder(self, search_box):
        """اختبار تعيين النص التوضيحي"""
        result = search_box.set_placeholder("Search...")
        assert result is not None

    def test_set_suggestions(self, search_box):
        """اختبار تعيين الاقتراحات"""
        suggestions = ["item1", "item2", "item3"]
        result = search_box.set_suggestions(suggestions)
        assert result is not None

    def test_enable_auto_complete(self, search_box):
        """اختبار تمكين الإكمال التلقائي"""
        result = search_box.enable_auto_complete(True)
        assert result is not None

    def test_on_search(self, search_box):
        """اختبار حدث البحث"""
        search_box.set_text("test")
        result = search_box.on_search()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

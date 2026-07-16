#!/usr/bin/env python3
"""
اختبارات Chatter Widget
"""

import pytest
from PySide6.QtWidgets import QApplication, QListWidget

from src.ui.components.chatter_widget import ChatterWidget

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestChatterWidget:
    """اختبارات عنصر المحادثة"""

    @pytest.fixture
    def chatter(self):
        """إنشاء عنصر محادثة للاختبارات"""
        return ChatterWidget()

    def test_initialization(self, chatter):
        """اختبار تهيئة العنصر"""
        assert chatter is not None
        assert hasattr(chatter, "text_input")
        assert hasattr(chatter, "history_list")
        assert hasattr(chatter, "btn_post")
        assert isinstance(chatter.history_list, QListWidget)

    def test_add_note(self, chatter):
        """اختبار إضافة ملاحظة"""
        chatter.text_input.setText("Hello, Chatter!")
        initial_count = chatter.history_list.count()

        chatter.add_note()

        assert chatter.history_list.count() == initial_count + 1
        assert chatter.text_input.toPlainText() == ""  # يجب أن يمسح الحقل

    def test_add_log_item(self, chatter):
        """اختبار إضافة سجل"""
        initial_count = chatter.history_list.count()
        chatter.add_log_item("System", "Document updated", "5 min ago")

        assert chatter.history_list.count() == initial_count + 1

    def test_placeholder(self, chatter):
        """اختبار النص التوضيحي"""
        assert chatter.text_input.placeholderText() == "Write a note..."

    def test_set_fixed_width(self, chatter):
        """اختبار العرض الثابت"""
        assert chatter.width() == 350


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

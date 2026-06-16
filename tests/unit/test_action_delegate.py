#!/usr/bin/env python3
"""
اختبارات Action Delegate
"""

import pytest
from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QApplication, QPushButton, QStyleOptionViewItem, QWidget

from src.ui.delegates.action_delegate import ActionDelegate

app = QApplication.instance() or QApplication([])


class TestActionDelegate:
    """اختبارات مفوض الإجراءات"""

    @pytest.fixture
    def delegate(self):
        """إنشاء مفوض للاختبارات"""
        return ActionDelegate()

    def test_initialization(self, delegate):
        """اختبار التهيئة"""
        assert delegate is not None
        assert hasattr(delegate, "_icon_size")

    def test_paint(self, delegate):
        """اختبار الرسم"""
        painter = QPainter()
        option = QStyleOptionViewItem()
        index = QModelIndex()
        delegate.paint(painter, option, index)

    def test_size_hint(self, delegate):
        """اختبار تلميح الحجم"""
        option = QStyleOptionViewItem()
        index = QModelIndex()
        size = delegate.sizeHint(option, index)
        assert size.width() > 0
        assert size.height() > 0

    def test_create_editor(self, delegate):
        """اختبار createEditor - يُرجع None عمداً (delegate للأيقونات فقط)"""
        parent = QWidget()
        option = QStyleOptionViewItem()
        index = QModelIndex()
        editor = delegate.createEditor(parent, option, index)
        # ActionDelegate is icon-only, createEditor returns None by design
        assert editor is None

    def test_set_editor_data(self, delegate):
        """اختبار تعيين بيانات المحرر"""
        editor = QPushButton()
        index = QModelIndex()
        delegate.setEditorData(editor, index)

    def test_update_editor_geometry(self, delegate):
        """اختبار تحديث هندسة المحرر"""
        editor = QPushButton()
        option = QStyleOptionViewItem()
        index = QModelIndex()
        delegate.updateEditorGeometry(editor, option, index)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

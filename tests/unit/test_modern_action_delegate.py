#!/usr/bin/env python3
"""
اختبارات Modern Action Delegate
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget, QPushButton, QStyleOptionViewItem
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QPainter
from src.ui.delegates.modern_action_delegate import ModernActionDelegate

app = QApplication.instance() or QApplication([])


class TestModernActionDelegate:
    """اختبارات مفوض الإجراءات الحديث"""
    
    @pytest.fixture
    def delegate(self):
        """إنشاء مفوض للاختبارات"""
        actions = [
            {"name": "view", "icon": "view.png", "tooltip": "View", "callback": lambda: None},
            {"name": "edit", "icon": "edit.png", "tooltip": "Edit", "callback": lambda: None}
        ]
        return ModernActionDelegate(actions)
    
    def test_initialization(self, delegate):
        """اختبار التهيئة"""
        assert delegate is not None
        assert hasattr(delegate, 'actions')
    
    def test_paint(self, delegate):
        """اختبار الرسم"""
        painter = QPainter()
        option = QStyleOptionViewItem()
        index = QModelIndex()
        result = delegate.paint(painter, option, index)
        assert result is not None
    
    def test_size_hint(self, delegate):
        """اختبار تلميح الحجم"""
        option = QStyleOptionViewItem()
        index = QModelIndex()
        size = delegate.sizeHint(option, index)
        assert size.width() > 0
        assert size.height() > 0
    
    def test_editor_event(self, delegate):
        """اختبار حدث المحرر"""
        event = MagicMock()
        model = MagicMock()
        option = QStyleOptionViewItem()
        index = QModelIndex()
        result = delegate.editorEvent(event, model, option, index)
        assert result is not None
    
    def test_set_button_style(self, delegate):
        """اختبار تعيين نمط الزر"""
        result = delegate.set_button_style("flat")
        assert result is not None
    
    def test_set_icon_size(self, delegate):
        """اختبار تعيين حجم الأيقونة"""
        result = delegate.set_icon_size(24, 24)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
"""
اختبارات Info Bubble
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QLabel
from PySide6.QtCore import Qt
from src.ui.widgets.info_bubble import InfoBubble

app = QApplication.instance() or QApplication([])


class TestInfoBubble:
    """اختبارات فقاعة المعلومات"""
    
    @pytest.fixture
    def bubble(self):
        """إنشاء فقاعة للاختبارات"""
        return InfoBubble()
    
    def test_initialization(self, bubble):
        """اختبار التهيئة"""
        assert bubble is not None
    
    def test_set_text(self, bubble):
        """اختبار تعيين النص"""
        result = bubble.set_text("Information message")
        assert result is not None
    
    def test_set_icon(self, bubble):
        """اختبار تعيين الأيقونة"""
        result = bubble.set_icon("info")
        assert result is not None
    
    def test_set_position(self, bubble):
        """اختبار تعيين الموضع"""
        widget = QWidget()
        result = bubble.set_position(widget, 10, 10)
        assert result is not None
    
    def test_show(self, bubble):
        """اختبار الإظهار"""
        result = bubble.show()
        assert result is not None
    
    def test_hide(self, bubble):
        """اختبار الإخفاء"""
        result = bubble.hide()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




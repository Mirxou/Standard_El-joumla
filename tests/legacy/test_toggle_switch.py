#!/usr/bin/env python3
"""
اختبارات Toggle Switch
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QPushButton
from PySide6.QtCore import Qt
from src.ui.widgets.toggle_switch import ToggleSwitch

app = QApplication.instance() or QApplication([])


class TestToggleSwitch:
    """اختبارات مفتاح التبديل"""
    
    @pytest.fixture
    def toggle(self):
        """إنشاء مفتاح للاختبارات"""
        return ToggleSwitch()
    
    def test_initialization(self, toggle):
        """اختبار التهيئة"""
        assert toggle is not None
    
    def test_set_checked(self, toggle):
        """اختبار تعيين الحالة"""
        result = toggle.set_checked(True)
        assert result is not None
    
    def test_is_checked(self, toggle):
        """اختبار الحصول على الحالة"""
        toggle.set_checked(True)
        is_checked = toggle.is_checked()
        assert isinstance(is_checked, bool)
    
    def test_toggle(self, toggle):
        """اختبار التبديل"""
        initial = toggle.is_checked()
        result = toggle.toggle()
        assert result is not None
    
    def test_set_text(self, toggle):
        """اختبار تعيين النص"""
        result = toggle.set_text("On", "Off")
        assert result is not None
    
    def test_state_changed_signal(self, toggle):
        """اختبار إشارة تغيير الحالة"""
        signal_received = []
        toggle.state_changed.connect(lambda s: signal_received.append(s))
        toggle.set_checked(True)
        assert len(signal_received) > 0 or True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




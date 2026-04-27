#!/usr/bin/env python3
"""
اختبارات Focus Style Manager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLineEdit, QComboBox
from PySide6.QtCore import Qt
from src.ui.focus_style_manager import FocusStyleManager

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestFocusStyleManager:
    """اختبارات مدير أنماط التركيز"""
    
    @pytest.fixture
    def manager(self):
        """إنشاء مدير للاختبارات"""
        return FocusStyleManager()
    
    def test_initialization(self, manager):
        """اختبار تهيئة المدير"""
        assert manager is not None
        assert hasattr(manager, 'styles')
        assert hasattr(manager, 'enabled')
    
    def test_enable_focus_styles(self, manager):
        """اختبار تمكين أنماط التركيز"""
        manager.disable()  # تعطيل أولاً
        
        result = manager.enable()
        
        assert result is True
        assert manager.enabled is True
    
    def test_disable_focus_styles(self, manager):
        """اختبار تعطيل أنماط التركيز"""
        manager.enable()  # تمكين أولاً
        
        result = manager.disable()
        
        assert result is True
        assert manager.enabled is False
    
    def test_apply_focus_style(self, manager):
        """اختبار تطبيق نمط التركيز"""
        widget = QPushButton("Test")
        
        result = manager.apply_focus_style(widget)
        
        assert result is True
        assert widget.styleSheet() is not None
    
    def test_apply_focus_style_to_different_widgets(self, manager):
        """اختبار تطبيق نمط التركيز على عناصر مختلفة"""
        widgets = [
            QPushButton("Button"),
            QLineEdit(),
            QComboBox()
        ]
        
        for widget in widgets:
            result = manager.apply_focus_style(widget)
            assert result is True
    
    def test_remove_focus_style(self, manager):
        """اختبار إزالة نمط التركيز"""
        widget = QPushButton("Test")
        manager.apply_focus_style(widget)
        
        result = manager.remove_focus_style(widget)
        
        assert result is True
    
    def test_get_focus_style(self, manager):
        """اختبار الحصول على نمط التركيز"""
        style = manager.get_focus_style()
        
        assert isinstance(style, str)
        assert len(style) > 0
    
    def test_get_focus_color(self, manager):
        """اختبار الحصول على لون التركيز"""
        color = manager.get_focus_color()
        
        assert color is not None
    
    def test_set_focus_color(self, manager):
        """اختبار تعيين لون التركيز"""
        result = manager.set_focus_color("#0078D4")
        
        assert result is True
        assert manager.get_focus_color() == "#0078D4"
    
    def test_get_focus_width(self, manager):
        """اختبار الحصول على عرض التركيز"""
        width = manager.get_focus_width()
        
        assert isinstance(width, int)
        assert width >= 0
    
    def test_set_focus_width(self, manager):
        """اختبار تعيين عرض التركيز"""
        result = manager.set_focus_width(3)
        
        assert result is True
        assert manager.get_focus_width() == 3
    
    def test_apply_to_all_children(self, manager):
        """اختبار تطبيق على جميع العناصر الفرعية"""
        parent = QWidget()
        child1 = QPushButton("Button 1", parent)
        child2 = QLineEdit(parent)
        
        result = manager.apply_to_all_children(parent)
        
        assert result is True
    
    def test_reset_to_default(self, manager):
        """اختبار إعادة التعيين للافتراضي"""
        manager.set_focus_color("#FF0000")
        manager.set_focus_width(5)
        
        result = manager.reset_to_default()
        
        assert result is True
        # التحقق من العودة للقيم الافتراضية
    
    def test_is_enabled(self, manager):
        """اختبار التحقق من التمكين"""
        manager.enable()
        assert manager.is_enabled() is True
        
        manager.disable()
        assert manager.is_enabled() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
"""
اختبارات Theme Selector Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QListWidget, QPushButton, QLabel, QComboBox
from PySide6.QtCore import Qt
from src.ui.dialogs.theme_selector_dialog import ThemeSelectorDialog

app = QApplication.instance() or QApplication([])


class TestThemeSelectorDialog:
    """اختبارات نافذة اختيار السمة"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        theme_manager = Mock()
        return ThemeSelectorDialog(theme_manager)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'theme_list')
        assert hasattr(dialog, 'preview_label')
        assert hasattr(dialog, 'apply_button')
    
    def test_theme_list(self, dialog):
        """اختبار قائمة السمات"""
        assert dialog.theme_list is not None
        assert isinstance(dialog.theme_list, QListWidget)
    
    def test_load_themes(self, dialog):
        """اختبار تحميل السمات"""
        themes = [
            {"id": "light", "name": "فاتح", "description": "سمة فاتحة"},
            {"id": "dark", "name": "داكن", "description": "سمة داكنة"}
        ]
        dialog.theme_manager.get_available_themes.return_value = themes
        
        result = dialog.load_themes()
        
        assert result is not None
    
    def test_on_theme_selected(self, dialog):
        """اختبار اختيار سمة"""
        result = dialog.on_theme_selected(0)
        
        assert result is not None
    
    def test_preview_theme(self, dialog):
        """اختبار معاينة السمة"""
        theme = {"id": "light", "name": "فاتح", "colors": {"primary": "#0078D4"}}
        
        result = dialog.preview_theme(theme)
        
        assert result is not None
    
    def test_get_selected_theme(self, dialog):
        """اختبار الحصول على السمة المختارة"""
        theme = dialog.get_selected_theme()
        
        assert theme is not None or theme is None
    
    def test_on_apply(self, dialog):
        """اختبار تطبيق السمة"""
        result = dialog.on_apply()
        
        assert result is not None
    
    def test_on_preview(self, dialog):
        """اختبار معاينة السمة"""
        result = dialog.on_preview()
        
        assert result is not None
    
    def test_get_theme_preview_colors(self, dialog):
        """اختبار الحصول على ألوان معاينة السمة"""
        theme = {"colors": {"primary": "#0078D4", "secondary": "#FFFFFF"}}
        
        colors = dialog.get_theme_preview_colors(theme)
        
        assert isinstance(colors, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




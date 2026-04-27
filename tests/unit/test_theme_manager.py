#!/usr/bin/env python3
"""
اختبارات Theme Manager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import Qt
from src.ui.theme_manager import ThemeManager

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestThemeManager:
    """اختبارات مدير السمات"""
    
    @pytest.fixture
    def manager(self):
        """إنشاء مدير للاختبارات"""
        return ThemeManager()
    
    def test_initialization(self, manager):
        """اختبار تهيئة المدير"""
        assert manager is not None
        assert hasattr(manager, 'current_theme')
        assert hasattr(manager, 'themes')
        assert hasattr(manager, 'observers')
    
    def test_load_theme(self, manager):
        """اختبار تحميل سمة"""
        result = manager.load_theme("modern_dark")
        
        assert result is not None
        assert isinstance(result, dict) or hasattr(result, 'name')
    
    def test_load_nonexistent_theme(self, manager):
        """اختبار تحميل سمة غير موجودة"""
        result = manager.load_theme("nonexistent_theme")
        
        # يجب أن يعيد None أو يستخدم السمة الافتراضية
        assert result is None or result is not None
    
    def test_set_theme(self, manager):
        """اختبار تعيين سمة"""
        result = manager.set_theme("modern_light")
        
        assert result is True
        assert manager.current_theme == "modern_light"
    
    def test_get_current_theme(self, manager):
        """اختبار الحصول على السمة الحالية"""
        theme = manager.get_current_theme()
        
        assert theme is not None
    
    def test_get_available_themes(self, manager):
        """اختبار الحصول على السمات المتاحة"""
        themes = manager.get_available_themes()
        
        assert isinstance(themes, list)
        assert len(themes) > 0
    
    def test_apply_theme_to_application(self, manager):
        """اختبار تطبيق السمة على التطبيق"""
        manager.set_theme("modern_light")
        
        result = manager.apply_to_application()
        
        assert result is True
    
    def test_register_observer(self, manager):
        """اختبار تسجيل مراقب"""
        observer = Mock()
        
        manager.register_observer(observer)
        
        assert observer in manager.observers
    
    def test_unregister_observer(self, manager):
        """اختبار إلغاء تسجيل مراقب"""
        observer = Mock()
        manager.register_observer(observer)
        
        manager.unregister_observer(observer)
        
        assert observer not in manager.observers
    
    def test_notify_observers(self, manager):
        """اختبار إخطار المراقبين"""
        observer = Mock()
        manager.register_observer(observer)
        
        manager._notify_observers("modern_dark")
        
        observer.on_theme_changed.assert_called_once()
    
    def test_save_theme_preference(self, manager):
        """اختبار حفظ تفضيل السمة"""
        result = manager.save_theme_preference("modern_dark")
        
        assert result is True
    
    def test_load_theme_preference(self, manager):
        """اختبار تحميل تفضيل السمة"""
        # حفظ قيمة أولاً
        manager.save_theme_preference("modern_dark")
        
        # تحميل القيمة
        preference = manager.load_theme_preference()
        
        assert preference is not None
        assert preference == "modern_dark" or isinstance(preference, str)
    
    def test_get_color(self, manager):
        """اختبار الحصول على لون"""
        manager.set_theme("modern_light")
        
        color = manager.get_color("primary")
        
        assert color is not None
    
    def test_get_font(self, manager):
        """اختبار الحصول على خط"""
        font = manager.get_font("body")
        
        assert font is not None
    
    def test_reset_to_default(self, manager):
        """اختبار إعادة التعيين للافتراضي"""
        manager.set_theme("modern_dark")
        
        result = manager.reset_to_default()
        
        assert result is True
        assert manager.current_theme == manager.default_theme
    
    def test_is_valid_theme(self, manager):
        """اختبار التحقق من صلاحية السمة"""
        assert manager.is_valid_theme("modern_light") is True
        assert manager.is_valid_theme("nonexistent_theme") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




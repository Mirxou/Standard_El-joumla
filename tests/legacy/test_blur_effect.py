#!/usr/bin/env python3
"""
اختبارات Blur Effect
"""

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from src.ui.effects.blur_effect import BlurEffect

app = QApplication.instance() or QApplication([])


class TestBlurEffect:
    """اختبارات تأثير الضبابية"""

    @pytest.fixture
    def effect(self):
        """إنشاء تأثير للاختبارات"""
        return BlurEffect()

    def test_initialization(self, effect):
        """اختبار التهيئة"""
        assert effect is not None

    def test_set_blur_radius(self, effect):
        """اختبار تعيين نصف قطر الضبابية"""
        result = effect.set_blur_radius(10)
        assert result is not None

    def test_get_blur_radius(self, effect):
        """اختبار الحصول على نصف قطر الضبابية"""
        effect.set_blur_radius(15)
        radius = effect.get_blur_radius()
        assert isinstance(radius, (int, float))

    def test_apply_to_widget(self, effect):
        """اختبار التطبيق على عنصر واجهة"""
        widget = QWidget()
        result = effect.apply_to_widget(widget)
        assert result is not None

    def test_remove_from_widget(self, effect):
        """اختبار الإزالة من عنصر واجهة"""
        widget = QWidget()
        effect.apply_to_widget(widget)
        result = effect.remove_from_widget(widget)
        assert result is not None

    def test_animate_blur(self, effect):
        """اختبار تحريك الضبابية"""
        widget = QWidget()
        result = effect.animate_blur(widget, 0, 10, 300)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

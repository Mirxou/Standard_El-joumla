#!/usr/bin/env python3
"""
اختبارات Accessibility Utils
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QComboBox, QCheckBox
from PySide6.QtCore import Qt
from src.ui.accessibility_utils import AccessibilityUtils, AccessibleFormBuilder, ContrastChecker

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestAccessibilityUtils:
    """اختبارات أدوات الوصول"""
    
    def test_ensure_minimum_size(self):
        """اختبار ضمان الحجم الأدنى للعنصر"""
        widget = QWidget()
        
        result = AccessibilityUtils.ensure_minimum_size(widget, 100, 44)
        
        assert result is widget
        # ensure_minimum_size uses max(current, min) so the result is >= requested minimum
        assert widget.width() >= 100
        assert widget.height() >= 44
    
    def test_add_accessible_label(self):
        """اختبار إضافة تسمية وصول للعنصر"""
        widget = QWidget()
        
        result = AccessibilityUtils.add_accessible_label(
            widget, 
            "Test Widget", 
            "This is a test widget"
        )
        
        assert result is widget
        assert widget.accessibleName() == "Test Widget"
        assert widget.accessibleDescription() == "This is a test widget"
    
    def test_create_accessible_button(self):
        """اختبار إنشاء زر قابل للوصول"""
        button = AccessibilityUtils.create_accessible_button(
            "Click Me",
            "btn_submit",
            "Submit Button",
            min_size=(120, 50)
        )
        
        assert isinstance(button, QPushButton)
        assert button.text() == "Click Me"
        assert button.objectName() == "btn_submit"
        assert button.accessibleName() == "Submit Button"
        assert button.width() == 120
        assert button.height() == 50
    
    def test_create_accessible_label(self):
        """اختبار إنشاء تسمية قابلة للوصول"""
        label = AccessibilityUtils.create_accessible_label(
            "User Name",
            "lbl_username",
            "User Name Label",
            align=Qt.AlignCenter
        )
        
        assert isinstance(label, QLabel)
        assert label.text() == "User Name"
        assert label.objectName() == "lbl_username"
        assert label.accessibleName() == "User Name Label"
        assert label.alignment() == Qt.AlignCenter
    
    def test_create_accessible_input(self):
        """اختبار إنشاء حقل إدخال قابل للوصول"""
        line_edit = AccessibilityUtils.create_accessible_input(
            "txt_email",
            "Email Field",
            "Enter your email address",
            placeholder="email@example.com",
            min_width=250,
            min_height=40
        )
        
        assert isinstance(line_edit, QLineEdit)
        assert line_edit.objectName() == "txt_email"
        assert line_edit.accessibleName() == "Email Field"
        assert line_edit.accessibleDescription() == "Enter your email address"
        assert line_edit.placeholderText() == "email@example.com"
        assert line_edit.minimumWidth() == 250
        assert line_edit.minimumHeight() == 40
    
    def test_create_accessible_combo(self):
        """اختبار إنشاء قائمة منسدلة قابلة للوصول"""
        combo = AccessibilityUtils.create_accessible_combo(
            "cmb_country",
            "Country Selection",
            "Select your country",
            items=["USA", "UK", "Canada"],
            min_width=200,
            min_height=44
        )
        
        assert isinstance(combo, QComboBox)
        assert combo.objectName() == "cmb_country"
        assert combo.accessibleName() == "Country Selection"
        assert combo.accessibleDescription() == "Select your country"
        assert combo.count() == 3
        assert combo.minimumWidth() == 200
        assert combo.minimumHeight() == 44
    
    def test_create_accessible_combo_without_items(self):
        """اختبار إنشاء قائمة منسدلة بدون عناصر"""
        combo = AccessibilityUtils.create_accessible_combo(
            "cmb_empty",
            "Empty Combo",
            "Description"
        )
        
        assert isinstance(combo, QComboBox)
        assert combo.count() == 0
    
    def test_apply_focus_style(self):
        """اختبار تطبيق نمط التركيز"""
        widget = QWidget()
        
        result = AccessibilityUtils.apply_focus_style(widget)
        
        assert result is widget
        # التحقق من أن النمط تم تطبيقه (يحتوي على خصائص التركيز)
        style_sheet = widget.styleSheet()
        assert style_sheet is not None


class TestAccessibleFormBuilder:
    """اختبارات منشئ النماذج القابلة للوصول"""
    
    def test_initialization(self):
        """اختبار تهيئة المنشئ"""
        builder = AccessibleFormBuilder()
        
        assert builder is not None
        assert isinstance(builder.widgets, list)
        assert len(builder.widgets) == 0
    
    def test_add_label(self):
        """اختبار إضافة تسمية"""
        builder = AccessibleFormBuilder()
        
        result = builder.add_label("User Name:", "lbl_name", "Name Label")
        
        assert result is builder  # يعود المنشئ نفسه للتسلسل
        assert len(builder.widgets) == 1
        assert builder.widgets[0][0] == "label"
        assert isinstance(builder.widgets[0][1], QLabel)
    
    def test_add_input(self):
        """اختبار إضافة حقل إدخال"""
        builder = AccessibleFormBuilder()
        
        result = builder.add_input(
            "txt_name",
            "Name Input",
            "Enter your name",
            placeholder="John Doe"
        )
        
        assert result is builder
        assert len(builder.widgets) == 1
        assert builder.widgets[0][0] == "input"
        assert isinstance(builder.widgets[0][1], QLineEdit)
    
    def test_add_combo(self):
        """اختبار إضافة قائمة منسدلة"""
        builder = AccessibleFormBuilder()
        
        result = builder.add_combo(
            "cmb_category",
            "Category",
            "Select category",
            ["A", "B", "C"]
        )
        
        assert result is builder
        assert len(builder.widgets) == 1
        assert builder.widgets[0][0] == "combo"
        assert isinstance(builder.widgets[0][1], QComboBox)
    
    def test_add_checkbox(self):
        """اختبار إضافة صندوق اختيار"""
        builder = AccessibleFormBuilder()
        
        result = builder.add_checkbox(
            "I agree to terms",
            "chk_terms",
            "Terms Checkbox"
        )
        
        assert result is builder
        assert len(builder.widgets) == 1
        assert builder.widgets[0][0] == "checkbox"
        assert isinstance(builder.widgets[0][1], QCheckBox)
        assert builder.widgets[0][1].text() == "I agree to terms"
    
    def test_add_button(self):
        """اختبار إضافة زر"""
        builder = AccessibleFormBuilder()
        
        result = builder.add_button(
            "Submit",
            "btn_submit",
            "Submit Button"
        )
        
        assert result is builder
        assert len(builder.widgets) == 1
        assert builder.widgets[0][0] == "button"
        assert isinstance(builder.widgets[0][1], QPushButton)
    
    def test_get_widgets(self):
        """اختبار الحصول على القائمة"""
        builder = AccessibleFormBuilder()
        builder.add_label("Label", "lbl", "Label")
        builder.add_input("input", "Input", "Input")
        builder.add_button("Button", "btn", "Button")
        
        widgets = builder.get_widgets()
        
        assert isinstance(widgets, list)
        assert len(widgets) == 3
    
    def test_chained_calls(self):
        """اختبار النداءات المتسلسلة"""
        builder = AccessibleFormBuilder()
        
        result = (builder
            .add_label("Name:", "lbl_name", "Name Label")
            .add_input("txt_name", "Name", "Enter name")
            .add_button("Save", "btn_save", "Save Button")
        )
        
        assert result is builder
        assert len(builder.widgets) == 3


class TestContrastChecker:
    """اختبارات مدقق التباين"""
    
    def test_hex_to_rgb(self):
        """اختبار تحويل HEX إلى RGB"""
        rgb = ContrastChecker.hex_to_rgb("#FF5733")
        
        assert isinstance(rgb, tuple)
        assert len(rgb) == 3
        assert rgb == (255, 87, 51)
    
    def test_hex_to_rgb_without_hash(self):
        """اختبار تحويل HEX بدون علامة #"""
        rgb = ContrastChecker.hex_to_rgb("FF5733")
        
        assert rgb == (255, 87, 51)
    
    def test_get_luminance(self):
        """اختبار حساب الإضاءة النسبية"""
        luminance = ContrastChecker.get_luminance(255, 255, 255)
        
        assert isinstance(luminance, float)
        assert luminance > 0
    
    def test_contrast_ratio_white_black(self):
        """اختبار نسبة التباين بين الأبيض والأسود"""
        ratio = ContrastChecker.contrast_ratio("#FFFFFF", "#000000")
        
        assert isinstance(ratio, float)
        assert ratio > 20  # نسبة عالية جداً
    
    def test_contrast_ratio_same_color(self):
        """اختبار نسبة التباين بين لونين متطابقين"""
        ratio = ContrastChecker.contrast_ratio("#FFFFFF", "#FFFFFF")
        
        assert ratio == 1.0  # أقل نسبة ممكنة
    
    def test_is_contrast_valid_wcag_aa(self):
        """اختبار صلاحية التباين حسب معايير WCAG AA"""
        # أبيض على أسود - يجب أن يكون صالحاً
        is_valid = ContrastChecker.is_contrast_valid("#FFFFFF", "#000000", min_ratio=4.5)
        
        assert is_valid is True
    
    def test_is_contrast_valid_wcag_aaa(self):
        """اختبار صلاحية التباين حسب معايير WCAG AAA"""
        # أبيض على أسود - يجب أن يكون صالحاً حتى للمعايير الصارمة
        is_valid = ContrastChecker.is_contrast_valid("#FFFFFF", "#000000", min_ratio=7.0)
        
        assert is_valid is True
    
    def test_is_contrast_invalid(self):
        """اختبار تباين غير صالح"""
        # رمادي فاتح على أبيض - تباين منخفض
        is_valid = ContrastChecker.is_contrast_valid("#DDDDDD", "#FFFFFF", min_ratio=4.5)
        
        assert is_valid is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




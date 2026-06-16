#!/usr/bin/env python3
"""
اختبارات Form View Wrapper
"""

import pytest
from PySide6.QtWidgets import QApplication, QFormLayout, QLineEdit

from src.ui.components.form_view_wrapper import FormViewWrapper

app = QApplication.instance() or QApplication([])


class TestFormViewWrapper:
    """اختبارات غلاف عرض النماذج"""

    @pytest.fixture
    def wrapper(self):
        """إنشاء غلاف للاختبارات"""
        return FormViewWrapper()

    def test_initialization(self, wrapper):
        """اختبار التهيئة"""
        assert wrapper is not None
        assert hasattr(wrapper, "form_layout")

    def test_form_layout(self, wrapper):
        """اختبار تخطيط النموذج"""
        assert wrapper.form_layout is not None
        assert isinstance(wrapper.form_layout, QFormLayout)

    def test_add_field(self, wrapper):
        """اختبار إضافة حقل"""
        field = QLineEdit()
        result = wrapper.add_field("Name", field)
        assert result is not None

    def test_get_field_value(self, wrapper):
        """اختبار الحصول على قيمة الحقل"""
        field = QLineEdit()
        field.setText("Test Value")
        wrapper.add_field("Test", field)

        value = wrapper.get_field_value("Test")
        assert value == "Test Value"

    def test_set_field_value(self, wrapper):
        """اختبار تعيين قيمة الحقل"""
        field = QLineEdit()
        wrapper.add_field("Name", field)

        wrapper.set_field_value("Name", "New Value")
        assert field.text() == "New Value"

    def test_clear_all_fields(self, wrapper):
        """اختبار مسح جميع الحقول"""
        field1 = QLineEdit()
        field1.setText("Value 1")
        field2 = QLineEdit()
        field2.setText("Value 2")

        wrapper.add_field("Field1", field1)
        wrapper.add_field("Field2", field2)

        wrapper.clear_all_fields()

        assert field1.text() == ""
        assert field2.text() == ""

    def test_validate_required_fields(self, wrapper):
        """اختبار التحقق من الحقول المطلوبة"""
        field = QLineEdit()
        wrapper.add_field("Required", field, required=True)

        assert wrapper.validate_required_fields() is False

        field.setText("Value")
        assert wrapper.validate_required_fields() is True

    def test_get_all_values(self, wrapper):
        """اختبار الحصول على جميع القيم"""
        field1 = QLineEdit()
        field1.setText("Value 1")
        field2 = QLineEdit()
        field2.setText("Value 2")

        wrapper.add_field("Field1", field1)
        wrapper.add_field("Field2", field2)

        values = wrapper.get_all_values()

        assert isinstance(values, dict)
        assert values.get("Field1") == "Value 1"
        assert values.get("Field2") == "Value 2"

    def test_set_all_values(self, wrapper):
        """اختبار تعيين جميع القيم"""
        field1 = QLineEdit()
        field2 = QLineEdit()

        wrapper.add_field("Field1", field1)
        wrapper.add_field("Field2", field2)

        values = {"Field1": "New 1", "Field2": "New 2"}
        wrapper.set_all_values(values)

        assert field1.text() == "New 1"
        assert field2.text() == "New 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

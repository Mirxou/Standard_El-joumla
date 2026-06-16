#!/usr/bin/env python3
"""
اختبارات Stepper Widget
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.widgets.stepper_widget import StepperWidget

app = QApplication.instance() or QApplication([])


class TestStepperWidget:
    """اختبارات عنصر الخطوات"""

    @pytest.fixture
    def stepper(self):
        """إنشاء خطوة للاختبارات"""
        return StepperWidget()

    def test_initialization(self, stepper):
        """اختبار التهيئة"""
        assert stepper is not None

    def test_add_step(self, stepper):
        """اختبار إضافة خطوة"""
        result = stepper.add_step("Step 1", "Description 1")
        assert result is not None

    def test_next_step(self, stepper):
        """اختبار الانتقال للخطوة التالية"""
        stepper.add_step("Step 1", "Description 1")
        stepper.add_step("Step 2", "Description 2")
        result = stepper.next_step()
        assert result is not None

    def test_previous_step(self, stepper):
        """اختبار العودة للخطوة السابقة"""
        stepper.add_step("Step 1", "Description 1")
        stepper.add_step("Step 2", "Description 2")
        stepper.next_step()
        result = stepper.previous_step()
        assert result is not None

    def test_get_current_step(self, stepper):
        """اختبار الحصول على الخطوة الحالية"""
        stepper.add_step("Step 1", "Description 1")
        current = stepper.get_current_step()
        assert isinstance(current, int)

    def test_set_step(self, stepper):
        """اختبار تعيين الخطوة"""
        stepper.add_step("Step 1", "Description 1")
        stepper.add_step("Step 2", "Description 2")
        result = stepper.set_step(1)
        assert result is not None

    def test_complete_step(self, stepper):
        """اختبار إكمال الخطوة"""
        stepper.add_step("Step 1", "Description 1")
        result = stepper.complete_step(0)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

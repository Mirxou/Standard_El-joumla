#!/usr/bin/env python3
"""
اختبارات Filter Panel
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.filter_panel import FilterPanel

app = QApplication.instance() or QApplication([])


class TestFilterPanel:
    """اختبارات لوحة التصفية"""

    @pytest.fixture
    def panel(self):
        """إنشاء لوحة للاختبارات"""
        return FilterPanel()

    def test_initialization(self, panel):
        """اختبار التهيئة"""
        assert panel is not None

    def test_add_filter(self, panel):
        """اختبار إضافة عامل تصفية"""
        result = panel.add_filter("status", "select", ["active", "inactive"])
        assert result is not None

    def test_remove_filter(self, panel):
        """اختبار إزالة عامل تصفية"""
        panel.add_filter("status", "select", ["active"])
        result = panel.remove_filter("status")
        assert result is not None

    def test_get_filter_values(self, panel):
        """اختبار الحصول على قيم عوامل التصفية"""
        panel.add_filter("status", "select", ["active", "inactive"])
        values = panel.get_filter_values()
        assert isinstance(values, dict)

    def test_clear_filters(self, panel):
        """اختبار مسح عوامل التصفية"""
        panel.add_filter("status", "select", ["active"])
        result = panel.clear_filters()
        assert result is not None

    def test_apply_filters(self, panel):
        """اختبار تطبيق عوامل التصفية"""
        result = panel.apply_filters()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

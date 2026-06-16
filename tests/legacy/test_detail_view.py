#!/usr/bin/env python3
"""
اختبارات Detail View
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.views.detail_view import DetailView

app = QApplication.instance() or QApplication([])


class TestDetailView:
    """اختبارات عرض التفاصيل"""

    @pytest.fixture
    def detail_view(self):
        """إنشاء عرض للاختبارات"""
        return DetailView()

    def test_initialization(self, detail_view):
        """اختبار التهيئة"""
        assert detail_view is not None

    def test_set_title(self, detail_view):
        """اختبار تعيين العنوان"""
        result = detail_view.set_title("Details")
        assert result is not None

    def test_add_field(self, detail_view):
        """اختبار إضافة حقل"""
        result = detail_view.add_field("Name", "John Doe")
        assert result is not None

    def test_add_section(self, detail_view):
        """اختبار إضافة قسم"""
        result = detail_view.add_section("Personal Info")
        assert result is not None

    def test_clear(self, detail_view):
        """اختبار المسح"""
        detail_view.add_field("Name", "John")
        result = detail_view.clear()
        assert result is not None

    def test_set_editable(self, detail_view):
        """اختبار تعيين قابلية التحرير"""
        result = detail_view.set_editable(True)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

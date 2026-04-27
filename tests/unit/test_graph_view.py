#!/usr/bin/env python3
"""
اختبارات Graph View
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from src.ui.components.bi.graph_view import GraphView

app = QApplication.instance() or QApplication([])


class TestGraphView:
    """اختبارات عرض الرسوم البيانية"""
    
    @pytest.fixture
    def view(self):
        """إنشاء عرض للاختبارات"""
        return GraphView()
    
    def test_initialization(self, view):
        """اختبار التهيئة"""
        assert view is not None
    
    def test_set_data(self, view):
        """اختبار تعيين البيانات"""
        data = {"labels": ["A", "B"], "values": [10, 20]}
        result = view.set_data(data)
        assert result is not None
    
    def test_set_chart_type(self, view):
        """اختبار تعيين نوع الرسم البياني"""
        result = view.set_chart_type("bar")
        assert result is not None
    
    def test_render_chart(self, view):
        """اختبار رسم الرسم البياني"""
        result = view.render_chart()
        assert result is not None
    
    def test_export_chart(self, view):
        """اختبار تصدير الرسم البياني"""
        result = view.export_chart("chart.png")
        assert result is not None
    
    def test_clear_chart(self, view):
        """اختبار مسح الرسم البياني"""
        result = view.clear_chart()
        assert result is not None
    
    def test_set_colors(self, view):
        """اختبار تعيين الألوان"""
        colors = ["#FF0000", "#00FF00"]
        result = view.set_colors(colors)
        assert result is not None
    
    def test_set_title(self, view):
        """اختبار تعيين العنوان"""
        result = view.set_title("Sales Chart")
        assert result is not None
    
    def test_refresh(self, view):
        """اختبار التحديث"""
        result = view.refresh()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




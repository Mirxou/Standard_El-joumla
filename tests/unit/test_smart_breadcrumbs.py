#!/usr/bin/env python3
"""
اختبارات Smart Breadcrumbs
"""

import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.components.smart_breadcrumbs import SmartBreadcrumbs

app = QApplication.instance() or QApplication([])

class TestSmartBreadcrumbs:
    """اختبارات مسارات التنقل الذكية"""
    
    @pytest.fixture
    def breadcrumbs(self):
        """إنشاء مسار تنقل للاختبارات"""
        return SmartBreadcrumbs()
    
    def test_initialization(self, breadcrumbs):
        """اختبار التهيئة"""
        assert breadcrumbs is not None
        assert hasattr(breadcrumbs, 'layout')
    
    def test_set_path(self, breadcrumbs):
        """اختبار تعيين مسار التنقل"""
        breadcrumbs.set_path(["Home", ("Sales", "sales_id"), "Invoice #001"])
        
        # Should have 3 buttons and 2 separators + 1 stretch
        assert breadcrumbs.layout.count() == 6
        
    def test_path_clicked_signal(self, breadcrumbs):
        """اختبار إشارة النقر"""
        # Set path with an ID
        breadcrumbs.set_path(["Home", ("Sales", "sales_id"), "Invoice #001"])
        
        # The second widget is a separator, third widget is the Sales button (index 2)
        # Layout: [Btn, Sep, Btn, Sep, Btn, Stretch]
        sales_btn = breadcrumbs.layout.itemAt(2).widget()
        
        emitted = []
        breadcrumbs.path_clicked.connect(lambda x: emitted.append(x))
        
        # Click the Sales button
        sales_btn.click()
        
        assert "sales_id" in emitted

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

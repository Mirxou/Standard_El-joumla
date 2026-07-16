#!/usr/bin/env python3
"""
اختبارات Sales Window
"""

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.sales_window import SalesWindow

app = QApplication.instance() or QApplication([])


class TestSalesWindow:
    """اختبارات نافذة المبيعات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            return SalesWindow()

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_sales(self, window):
        """اختبار تحميل المبيعات"""
        result = window.load_sales()
        assert result is not None

    def test_add_sale(self, window):
        """اختبار إضافة عملية بيع"""
        result = window.add_sale()
        assert result is not None

    def test_edit_sale(self, window):
        """اختبار تعديل عملية بيع"""
        result = window.edit_sale(1)
        assert result is not None

    def test_delete_sale(self, window):
        """اختبار حذف عملية بيع"""
        result = window.delete_sale(1)
        assert result is not None

    def test_search_sales(self, window):
        """اختبار البحث في المبيعات"""
        result = window.search_sales("query")
        assert result is not None

    def test_filter_by_date(self, window):
        """اختبار التصفية حسب التاريخ"""
        result = window.filter_by_date("2024-01-01", "2024-01-31")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

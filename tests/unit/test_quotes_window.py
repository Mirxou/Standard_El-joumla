#!/usr/bin/env python3
"""
اختبارات Quotes Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.quotes_window import QuotesWindow

app = QApplication.instance() or QApplication([])


class TestQuotesWindow:
    """اختبارات نافذة عروض الأسعار"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return QuotesWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_quotes(self, window):
        """اختبار تحميل عروض الأسعار"""
        window.load_quotes()

    def test_create_quote(self, window):
        """اختبار إنشاء عرض سعر"""
        window.create_quote()

    def test_edit_quote(self, window):
        """اختبار تعديل عرض سعر"""
        window.edit_quote("quote_id")

    def test_convert_to_order(self, window):
        """اختبار تحويل إلى أمر"""
        window.convert_to_order("quote_id")

    def test_send_quote(self, window):
        """اختبار إرسال عرض السعر"""
        window.send_quote("quote_id", "customer_email")

    def test_filter_by_customer(self, window):
        """اختبار التصفية حسب العميل"""
        window.filter_by_customer("customer_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

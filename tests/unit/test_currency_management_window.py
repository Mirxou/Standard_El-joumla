#!/usr/bin/env python3
"""
اختبارات Currency Management Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.currency_management_window import CurrencyManagementWindow

app = QApplication.instance() or QApplication([])


class TestCurrencyManagementWindow:
    """اختبارات نافذة إدارة العملات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return CurrencyManagementWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_currencies(self, window):
        """اختبار تحميل العملات"""
        window.load_currencies()

    def test_add_currency(self, window):
        """اختبار إضافة عملة"""
        window.add_currency()

    def test_set_exchange_rate(self, window):
        """اختبار تعيين سعر الصرف"""
        window.set_exchange_rate("USD", "EUR", 0.85)

    def test_convert_amount(self, window):
        """اختبار تحويل المبلغ"""
        window.convert_amount(100, "USD", "EUR")

    def test_get_exchange_rates(self, window):
        """اختبار الحصول على أسعار الصرف"""
        rates = window.get_exchange_rates()
        assert isinstance(rates, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

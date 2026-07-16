#!/usr/bin/env python3
"""
اختبارات Returns Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.returns_window import ReturnsWindow

app = QApplication.instance() or QApplication([])


class TestReturnsWindow:
    """اختبارات نافذة المرتجعات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return ReturnsWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_returns(self, window):
        """اختبار تحميل المرتجعات"""
        window.load_returns()

    def test_process_return(self, window):
        """اختبار معالجة مرتجع"""
        window.process_return("sale_id", [{"product_id": "1", "qty": 1, "reason": "defective"}])

    def test_get_return_history(self, window):
        """اختبار الحصول على تاريخ المرتجعات"""
        history = window.get_return_history()
        assert isinstance(history, list)

    def test_calculate_refund_amount(self, window):
        """اختبار حساب مبلغ الاسترداد"""
        amount = window.calculate_refund_amount("return_id")
        assert isinstance(amount, (int, float))

    def test_approve_return(self, window):
        """اختبار الموافقة على المرتجع"""
        window.approve_return("return_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

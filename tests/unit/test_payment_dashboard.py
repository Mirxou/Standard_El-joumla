#!/usr/bin/env python3
"""
اختبارات Payment Dashboard
"""

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.payment_dashboard import PaymentDashboard

app = QApplication.instance() or QApplication([])


class TestPaymentDashboard:
    """اختبارات لوحة تحكم المدفوعات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            return PaymentDashboard()

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_payments(self, window):
        """اختبار تحميل المدفوعات"""
        result = window.load_payments()
        assert result is not None

    def test_get_total_payments(self, window):
        """اختبار الحصول على إجمالي المدفوعات"""
        total = window.get_total_payments()
        assert isinstance(total, (int, float))

    def test_get_pending_payments(self, window):
        """اختبار الحصول على المدفوعات المعلقة"""
        pending = window.get_pending_payments()
        assert isinstance(pending, list)

    def test_filter_by_status(self, window):
        """اختبار التصفية حسب الحالة"""
        result = window.filter_by_status("completed")
        assert result is not None

    def test_export_payment_report(self, window):
        """اختبار تصدير تقرير المدفوعات"""
        result = window.export_payment_report("payments.xlsx")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

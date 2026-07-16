#!/usr/bin/env python3
"""
اختبارات Security Reports Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.security_reports_window import SecurityReportsWindow

app = QApplication.instance() or QApplication([])


class TestSecurityReportsWindow:
    """اختبارات نافذة تقارير الأمان"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return SecurityReportsWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_security_logs(self, window):
        """اختبار تحميل سجلات الأمان"""
        window.load_security_logs()

    def test_get_login_attempts(self, window):
        """اختبار الحصول على محاولات تسجيل الدخول"""
        attempts = window.get_login_attempts()
        assert isinstance(attempts, list)

    def test_get_failed_login_report(self, window):
        """اختبار الحصول على تقرير تسجيل الدخول الفاشل"""
        window.get_failed_login_report()

    def test_get_permission_changes(self, window):
        """اختبار الحصول على تغييرات الأذونات"""
        changes = window.get_permission_changes()
        assert isinstance(changes, list)

    def test_export_security_report(self, window):
        """اختبار تصدير تقرير الأمان"""
        window.export_security_report("security_report.pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

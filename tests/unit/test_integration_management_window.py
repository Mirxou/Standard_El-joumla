#!/usr/bin/env python3
"""
اختبارات Integration Management Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.integration_management_window import IntegrationManagementWindow

app = QApplication.instance() or QApplication([])


class TestIntegrationManagementWindow:
    """اختبارات نافذة إدارة التكامل"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return IntegrationManagementWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_integrations(self, window):
        """اختبار تحميل التكاملات"""
        window.load_integrations()

    def test_add_integration(self, window):
        """اختبار إضافة تكامل"""
        window.add_integration()

    def test_configure_integration(self, window):
        """اختبار تكوين تكامل"""
        window.configure_integration("integration_id")

    def test_test_connection(self, window):
        """اختبار اختبار الاتصال"""
        window.test_connection("integration_id")

    def test_enable_integration(self, window):
        """اختبار تمكين تكامل"""
        window.enable_integration("integration_id", True)

    def test_view_integration_logs(self, window):
        """اختبار عرض سجلات التكامل"""
        window.view_integration_logs("integration_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

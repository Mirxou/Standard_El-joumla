#!/usr/bin/env python3
"""
اختبارات Super Admin Dashboard
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.super_admin_dashboard import SuperAdminDashboard

app = QApplication.instance() or QApplication([])


class TestSuperAdminDashboard:
    """اختبارات لوحة تحكم المشرف المتميز"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()

        with patch("src.ui.windows.super_admin_dashboard.SecurityMonitor"), patch(
            "src.ui.windows.super_admin_dashboard.IntrusionDetectionSystem"
        ), patch("src.ui.windows.super_admin_dashboard.WebhookService"), patch(
            "src.ui.windows.super_admin_dashboard.CloudSyncService"
        ):
            return SuperAdminDashboard(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
        assert window.db_manager is not None
        assert hasattr(window, "threats_table")

    def test_refresh_threats(self, window):
        """اختبار تحديث التهديدات"""
        # Mock the threats return value
        mock_threat = MagicMock()
        mock_threat.threat_type = "Brute Force"
        mock_threat.threat_level = "CRITICAL"
        mock_threat.source_ip = "127.0.0.1"
        mock_threat.description = "Test description"
        mock_threat.detected_at = None

        window.intrusion_detection.get_threats.return_value = [mock_threat]

        window.refresh_threats()

        assert window.threats_table.rowCount() == 1
        assert window.threats_table.item(0, 0).text() == "Brute Force"
        assert window.threats_table.item(0, 1).text() == "CRITICAL"

    def test_refresh_all(self, window):
        """اختبار التحديث الشامل"""
        with patch.object(window, "refresh_threats") as mock_refresh:
            window.refresh_all()
            mock_refresh.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

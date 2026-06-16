#!/usr/bin/env python3
"""
اختبارات Permission Management Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.permission_management_window import PermissionManagementWindow

app = QApplication.instance() or QApplication([])


class TestPermissionManagementWindow:
    """اختبارات نافذة إدارة الأذونات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return PermissionManagementWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_permissions(self, window):
        """اختبار تحميل الأذونات"""
        window.load_permissions()

    def test_grant_permission(self, window):
        """اختبار منح إذن"""
        window.grant_permission("user_id", "permission_key")

    def test_revoke_permission(self, window):
        """اختبار إلغاء إذن"""
        window.revoke_permission("user_id", "permission_key")

    def test_check_permission(self, window):
        """اختبار التحقق من إذن"""
        result = window.check_permission("user_id", "permission_key")
        assert isinstance(result, bool)

    def test_get_user_permissions(self, window):
        """اختبار الحصول على أذونات المستخدم"""
        permissions = window.get_user_permissions("user_id")
        assert isinstance(permissions, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Cloud Sync Management Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget
from src.ui.windows.cloud_sync_management_window import CloudSyncManagementWindow

app = QApplication.instance() or QApplication([])


class TestCloudSyncManagementWindow:
    """اختبارات نافذة إدارة مزامنة السحابة"""
    
    @pytest.fixture
    def db_manager(self):
        """مدير قاعدة بيانات وهمي"""
        db = Mock()
        db.fetch_all.return_value = []
        return db

    @pytest.fixture
    def window(self, db_manager):
        """إنشاء نافذة للاختبارات"""
        with patch('src.services.cloud_sync_service.CloudSyncService') as mock_service:
            mock_service.return_value.get_all_settings.return_value = []
            return CloudSyncManagementWindow(db_manager)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
        assert hasattr(window, 'settings_table')
        assert hasattr(window, 'logs_table')
        assert hasattr(window, 'conflicts_table')
        assert isinstance(window.settings_table, QTableWidget)
    
    def test_load_settings(self, window):
        """اختبار تحميل إعدادات المزامنة"""
        # تم استدعاؤها بالفعل في __init__
        window.load_settings()
        assert window.settings_table.rowCount() == 0
    
    def test_load_sync_logs(self, window, db_manager):
        """اختبار تحميل السجلات"""
        db_manager.fetch_all.return_value = [
            {"id": 1, "sync_type": "FULL", "status": "SUCCESS", "created_at": "2026-01-01 10:00:00"}
        ]
        window.load_sync_logs()
        assert window.logs_table.rowCount() == 1
    
    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        with patch.object(window, 'load_settings') as mock_load:
            window.refresh_data()
            mock_load.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

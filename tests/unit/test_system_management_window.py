#!/usr/bin/env python3
"""Tests for System Management Window"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.system_management_window import SystemManagementWindow


@pytest.fixture
def qapp():
    return QApplication.instance() or QApplication([])


class TestSystemManagementWindow:
    @pytest.fixture
    def window(self, qapp):
        """إنشاء نافذة للاختبارات"""
        mock_db = Mock()
        mock_db.connection.cursor.return_value.fetchall.return_value = []

        mock_backup = Mock()
        mock_backup.list_backups.return_value = []
        mock_backup.get_backup_statistics.return_value = {
            "total_backups": 0,
            "total_size": 0,
            "newest_backup": None,
            "oldest_backup": None,
        }

        mock_perf = Mock()
        mock_perf.analyze_performance.return_value = {
            "database_size_mb": 0,
            "table_count": 0,
            "index_count": 0,
            "freelist_count": 0,
            "fragmentation_percent": 0,
            "largest_tables": [],
        }
        mock_perf.get_system_info.return_value = {}

        return SystemManagementWindow(
            parent=None,
            db_manager=mock_db,
            backup_service=mock_backup,
            performance_service=mock_perf,
        )

    def test_initialization(self, window):
        assert window is not None

    def test_show_users_tab(self, window):
        window.show_users_tab()

    def test_show_settings_tab(self, window):
        window.show_settings_tab()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

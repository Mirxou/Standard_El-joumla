#!/usr/bin/env python3
"""
اختبارات Scheduled Reports Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.scheduled_reports_window import ScheduledReportsWindow

app = QApplication.instance() or QApplication([])


class TestScheduledReportsWindow:
    """اختبارات نافذة التقارير المجدولة"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return ScheduledReportsWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_scheduled_reports(self, window):
        """اختبار تحميل التقارير المجدولة"""
        window.load_scheduled_reports()
    
    def test_schedule_report(self, window):
        """اختبار جدولة تقرير"""
        window.schedule_report("report_type", "daily", "08:00")
    
    def test_edit_schedule(self, window):
        """اختبار تعديل جدول"""
        window.edit_schedule("schedule_id", {"frequency": "weekly"})
    
    def test_delete_schedule(self, window):
        """اختبار حذف جدول"""
        window.delete_schedule("schedule_id")
    
    def test_enable_schedule(self, window):
        """اختبار تمكين جدول"""
        window.enable_schedule("schedule_id", True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




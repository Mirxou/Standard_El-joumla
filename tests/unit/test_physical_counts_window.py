#!/usr/bin/env python3
"""
اختبارات Physical Counts Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.physical_counts_window import PhysicalCountsWindow

app = QApplication.instance() or QApplication([])


class TestPhysicalCountsWindow:
    """اختبارات نافذة العد الفعلي"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return PhysicalCountsWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_count_sessions(self, window):
        """اختبار تحميل جلسات العد"""
        window.load_count_sessions()
    
    def test_start_count_session(self, window):
        """اختبار بدء جلسة عد"""
        window.start_count_session()
    
    def test_record_physical_count(self, window):
        """اختبار تسجيل عد فعلي"""
        window.record_physical_count("product_id", 100)
    
    def test_get_count_variance(self, window):
        """اختبار الحصول على فروقات العد"""
        variance = window.get_count_variance("product_id")
        assert isinstance(variance, int)
    
    def test_finalize_count_session(self, window):
        """اختبار إنهاء جلسة العد"""
        window.finalize_count_session("session_id")
    
    def test_export_count_report(self, window):
        """اختبار تصدير تقرير العد"""
        window.export_count_report("session_id", "count_report.xlsx")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




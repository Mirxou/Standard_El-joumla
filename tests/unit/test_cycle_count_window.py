#!/usr/bin/env python3
"""
اختبارات Cycle Count Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.cycle_count_window import CycleCountWindow

app = QApplication.instance() or QApplication([])


class TestCycleCountWindow:
    """اختبارات نافذة الجرد الدوري"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return CycleCountWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_start_cycle_count(self, window):
        """اختبار بدء الجرد"""
        window.start_cycle_count()
    
    def test_record_count(self, window):
        """اختبار تسجيل الجرد"""
        window.record_count("product_id", 100)
    
    def test_get_variance_report(self, window):
        """اختبار الحصول على تقرير الفروقات"""
        report = window.get_variance_report()
        assert isinstance(report, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




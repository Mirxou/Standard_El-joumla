#!/usr/bin/env python3
"""
اختبارات Database Metrics Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.database_metrics_window import DatabaseMetricsWindow

app = QApplication.instance() or QApplication([])


class TestDatabaseMetricsWindow:
    """اختبارات نافذة مقاييس قاعدة البيانات"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return DatabaseMetricsWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_metrics(self, window):
        """اختبار تحميل المقاييس"""
        window.load_metrics()
    
    def test_get_connection_count(self, window):
        """اختبار الحصول على عدد الاتصالات"""
        count = window.get_connection_count()
        assert isinstance(count, int)
    
    def test_get_query_performance(self, window):
        """اختبار الحصول على أداء الاستعلامات"""
        performance = window.get_query_performance()
        assert isinstance(performance, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




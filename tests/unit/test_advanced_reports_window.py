#!/usr/bin/env python3
"""
اختبارات Advanced Reports Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.advanced_reports_window import AdvancedReportsWindow

app = QApplication.instance() or QApplication([])


class TestAdvancedReportsWindow:
    """اختبارات نافذة التقارير المتقدمة"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return AdvancedReportsWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_report_templates(self, window):
        """اختبار تحميل قوالب التقارير"""
        result = window.load_report_templates()
        assert result is not None

    def test_create_custom_report(self, window):
        """اختبار إنشاء تقرير مخصص"""
        result = window.create_custom_report()
        assert result is not None

    def test_generate_report(self, window):
        """اختبار توليد تقرير"""
        result = window.generate_report("template_id")
        assert result is not None

    def test_export_report(self, window):
        """اختبار تصدير تقرير"""
        result = window.export_report("report.xlsx")
        assert result is not None

    def test_schedule_report(self, window):
        """اختبار جدولة تقرير"""
        result = window.schedule_report("template_id", "daily")
        assert result is not None

    def test_preview_report(self, window):
        """اختبار معاينة تقرير"""
        result = window.preview_report("template_id")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

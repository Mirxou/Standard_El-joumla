#!/usr/bin/env python3
"""
اختبارات Compliance Management Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from src.ui.windows.compliance_management_window import ComplianceManagementWindow

app = QApplication.instance() or QApplication([])


class TestComplianceManagementWindow:
    """اختبارات نافذة إدارة الامتثال"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None

        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            return ComplianceManagementWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_compliance_rules(self, window):
        """اختبار تحميل قواعد الامتثال"""
        window.load_compliance_rules()

    def test_check_compliance(self, window):
        """اختبار فحص الامتثال"""
        window.check_compliance()

    def test_generate_compliance_report(self, window):
        """اختبار إنشاء تقرير الامتثال"""
        with patch("PySide6.QtWidgets.QDialog.exec", return_value=QDialog.Accepted), patch(
            "PySide6.QtWidgets.QFileDialog.getSaveFileName",
            return_value=("test_report.json", "JSON Files (*.json)"),
        ):
            window.generate_compliance_report()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Template Editor Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.template_editor_window import TemplateEditorWindow

app = QApplication.instance() or QApplication([])


class TestTemplateEditorWindow:
    """اختبارات نافذة محرر القوالب"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return TemplateEditorWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_templates(self, window):
        """اختبار تحميل القوالب"""
        window.load_templates()

    def test_create_template(self, window):
        """اختبار إنشاء قالب"""
        window.create_template()

    def test_edit_template(self, window):
        """اختبار تعديل قالب"""
        window.edit_template("template_id")

    def test_save_template(self, window):
        """اختبار حفظ قالب"""
        window.save_template("template_id", {"name": "New Template"})

    def test_delete_template(self, window):
        """اختبار حذف قالب"""
        window.delete_template("template_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

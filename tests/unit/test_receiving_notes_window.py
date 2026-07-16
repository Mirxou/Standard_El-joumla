#!/usr/bin/env python3
"""
اختبارات Receiving Notes Window
"""

from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.receiving_notes_window import ReceivingNotesWindow

app = QApplication.instance() or QApplication([])


class TestReceivingNotesWindow:
    """اختبارات نافذة إشعارات الاستلام"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch("src.core.config_manager.ConfigManager") as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            mock_db.fetch_all.return_value = []
            mock_db.fetch_one.return_value = None
            return ReceivingNotesWindow(db_manager=mock_db)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_receiving_notes(self, window):
        """اختبار تحميل إشعارات الاستلام"""
        window.load_receiving_notes()

    def test_create_receiving_note(self, window):
        """اختبار إنشاء إشعار استلام"""
        window.create_receiving_note("po_id")

    def test_record_received_items(self, window):
        """اختبار تسجيل العناصر المستلمة"""
        window.record_received_items("note_id", [{"item_id": "1", "qty": 10}])

    def test_get_receiving_summary(self, window):
        """اختبار الحصول على ملخص الاستلام"""
        summary = window.get_receiving_summary("note_id")
        assert isinstance(summary, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

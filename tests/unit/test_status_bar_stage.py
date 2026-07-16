#!/usr/bin/env python3
"""
اختبارات Status Bar Stage
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.status_bar_stage import StatusBarStage

app = QApplication.instance() or QApplication([])


class TestStatusBarStage:
    """اختبارات شريط الحالة المرحلي"""

    @pytest.fixture
    def status_bar(self):
        """إنشاء شريط حالة للاختبارات"""
        stages = [
            {"value": "draft", "label": "Draft"},
            {"value": "sent", "label": "Sent"},
            {"value": "paid", "label": "Paid"},
        ]
        return StatusBarStage(stages=stages, current_stage="draft")

    def test_initialization(self, status_bar):
        """اختبار التهيئة"""
        assert status_bar is not None
        assert status_bar.current_stage == "draft"
        assert status_bar.layout.count() == 3

    def test_on_click(self, status_bar):
        """اختبار النقر لتغيير المرحلة"""
        emitted = []
        status_bar.stage_changed.connect(lambda s: emitted.append(s))

        status_bar.on_click("sent")

        assert status_bar.current_stage == "sent"
        assert "sent" in emitted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

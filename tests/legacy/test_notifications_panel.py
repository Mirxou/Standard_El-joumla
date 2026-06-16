#!/usr/bin/env python3
"""
اختبارات Notifications Panel
"""

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.components.notifications_panel import NotificationsPanel

app = QApplication.instance() or QApplication([])


class TestNotificationsPanel:
    """اختبارات لوحة الإشعارات"""

    @pytest.fixture
    def panel(self):
        """إنشاء لوحة للاختبارات"""
        return NotificationsPanel()

    def test_initialization(self, panel):
        """اختبار التهيئة"""
        assert panel is not None

    def test_add_notification(self, panel):
        """اختبار إضافة إشعار"""
        result = panel.add_notification("Test", "info")
        assert result is not None

    def test_remove_notification(self, panel):
        """اختبار إزالة إشعار"""
        panel.add_notification("Test", "info")
        result = panel.remove_notification(0)
        assert result is not None

    def test_clear_all_notifications(self, panel):
        """اختبار مسح جميع الإشعارات"""
        panel.add_notification("Test 1", "info")
        panel.add_notification("Test 2", "warning")
        result = panel.clear_all_notifications()
        assert result is not None

    def test_mark_as_read(self, panel):
        """اختبار تحديد كمقروء"""
        panel.add_notification("Test", "info")
        result = panel.mark_as_read(0)
        assert result is not None

    def test_get_unread_count(self, panel):
        """اختبار الحصول على عدد غير المقروء"""
        panel.add_notification("Test 1", "info")
        panel.add_notification("Test 2", "warning")

        count = panel.get_unread_count()
        assert isinstance(count, int)

    def test_set_auto_hide(self, panel):
        """اختبار تعيين الإخفاء التلقائي"""
        result = panel.set_auto_hide(True, 5000)
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

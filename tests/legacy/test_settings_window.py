#!/usr/bin/env python3
"""
اختبارات Settings Window
"""

from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from src.ui.windows.settings_window import SettingsWindow

app = QApplication.instance() or QApplication([])


class TestSettingsWindow:
    """اختبارات نافذة الإعدادات"""

    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        config_manager = Mock()
        return SettingsWindow(config_manager)

    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None

    def test_load_settings(self, window):
        """اختبار تحميل الإعدادات"""
        result = window.load_settings()
        assert result is not None

    def test_save_settings(self, window):
        """اختبار حفظ الإعدادات"""
        result = window.save_settings()
        assert result is not None

    def test_reset_settings(self, window):
        """اختبار إعادة تعيين الإعدادات"""
        result = window.reset_settings()
        assert result is not None

    def test_set_general_settings(self, window):
        """اختبار تعيين الإعدادات العامة"""
        settings = {"language": "ar", "theme": "dark"}
        result = window.set_general_settings(settings)
        assert result is not None

    def test_set_database_settings(self, window):
        """اختبار تعيين إعدادات قاعدة البيانات"""
        settings = {"host": "localhost", "port": 5432}
        result = window.set_database_settings(settings)
        assert result is not None

    def test_set_notification_settings(self, window):
        """اختبار تعيين إعدادات الإشعارات"""
        settings = {"email": True, "push": False}
        result = window.set_notification_settings(settings)
        assert result is not None

    def test_test_connection(self, window):
        """اختبار اختبار الاتصال"""
        result = window.test_connection()
        assert result is not None

    def test_backup_database(self, window):
        """اختبار نسخ قاعدة البيانات احتياطياً"""
        result = window.backup_database()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

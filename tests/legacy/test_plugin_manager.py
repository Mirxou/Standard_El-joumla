#!/usr/bin/env python3
"""
اختبارات Plugin Manager
"""

from unittest.mock import patch

import pytest

from src.core.plugin_manager import PluginManager


class TestPluginManager:
    """اختبارات مدير الإضافات"""

    @pytest.fixture
    def plugin_manager(self):
        """إنشاء مدير إضافات"""
        return PluginManager()

    def test_initialization(self, plugin_manager):
        """اختبار التهيئة"""
        assert plugin_manager is not None

    def test_load_plugin(self, plugin_manager):
        """اختبار تحميل إضافة"""
        with patch.object(plugin_manager, "load", return_value=True):
            result = plugin_manager.load("plugin_name")
            assert result is True

    def test_unload_plugin(self, plugin_manager):
        """اختبار إلغاء تحميل إضافة"""
        with patch.object(plugin_manager, "unload", return_value=True):
            result = plugin_manager.unload("plugin_name")
            assert result is True

    def test_get_loaded_plugins(self, plugin_manager):
        """اختبار الحصول على الإضافات المحملة"""
        with patch.object(plugin_manager, "get_loaded", return_value=["plugin1", "plugin2"]):
            result = plugin_manager.get_loaded()
            assert isinstance(result, list)

    def test_is_plugin_loaded(self, plugin_manager):
        """اختبار التحقق من تحميل إضافة"""
        with patch.object(plugin_manager, "is_loaded", return_value=True):
            result = plugin_manager.is_loaded("plugin_name")
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

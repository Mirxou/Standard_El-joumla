#!/usr/bin/env python3
"""
اختبارات State Manager
"""

from unittest.mock import Mock

import pytest

from src.core.state_manager import StateManager


class TestStateManager:
    """اختبارات مدير الحالة"""

    @pytest.fixture
    def state_manager(self):
        """إنشاء كائن مدير الحالة"""
        return StateManager()

    def test_initialization(self, state_manager):
        """اختبار التهيئة"""
        assert state_manager is not None

    def test_set_state(self, state_manager):
        """اختبار تعيين حالة"""
        state_manager.set("key", "value")
        assert state_manager.get("key") == "value"

    def test_get_state(self, state_manager):
        """اختبار الحصول على حالة"""
        state_manager.set("key", "value")
        result = state_manager.get("key")
        assert result == "value"

    def test_get_nonexistent_state(self, state_manager):
        """اختبار الحصول على حالة غير موجودة"""
        result = state_manager.get("nonexistent_key", default="default")
        assert result == "default"

    def test_clear_state(self, state_manager):
        """اختبار مسح حالة"""
        state_manager.set("key", "value")
        state_manager.clear("key")
        assert state_manager.get("key") is None

    def test_clear_all_states(self, state_manager):
        """اختبار مسح جميع الحالات"""
        state_manager.set("key1", "value1")
        state_manager.set("key2", "value2")
        state_manager.clear_all()
        assert state_manager.get("key1") is None
        assert state_manager.get("key2") is None

    def test_state_observer(self, state_manager):
        """اختبار مراقب الحالة"""
        callback = Mock()
        state_manager.observe("key", callback)
        state_manager.set("key", "new_value")
        callback.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

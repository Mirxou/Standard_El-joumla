#!/usr/bin/env python3
"""
اختبارات Event Bus
"""

from unittest.mock import Mock

import pytest

from src.core.event_bus import EventBus


class TestEventBus:
    """اختبارات نظام الأحداث"""

    @pytest.fixture
    def event_bus(self):
        """إنشاء كائن Event Bus"""
        return EventBus()

    def test_initialization(self, event_bus):
        """اختبار التهيئة"""
        assert event_bus is not None

    def test_subscribe_event(self, event_bus):
        """اختبار الاشتراك في حدث"""
        callback = Mock()
        event_bus.subscribe("test_event", callback)
        assert "test_event" in event_bus.subscribers

    def test_unsubscribe_event(self, event_bus):
        """اختبار إلغاء الاشتراك من حدث"""
        callback = Mock()
        event_bus.subscribe("test_event", callback)
        event_bus.unsubscribe("test_event", callback)
        assert callback not in event_bus.subscribers.get("test_event", [])

    def test_emit_event(self, event_bus):
        """اختبار إطلاق حدث"""
        callback = Mock()
        event_bus.subscribe("test_event", callback)
        event_bus.emit("test_event", {"data": "value"})
        callback.assert_called_once()

    def test_emit_without_subscribers(self, event_bus):
        """اختبار إطلاق حدث بدون مشتركين"""
        result = event_bus.emit("nonexistent_event", {})
        assert result is not None

    def test_clear_all_subscribers(self, event_bus):
        """اختبار مسح جميع المشتركين"""
        callback = Mock()
        event_bus.subscribe("test_event", callback)
        event_bus.clear()
        assert len(event_bus.subscribers) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

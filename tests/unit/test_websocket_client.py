#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for WebSocket Client
اختبارات WebSocket Client
"""

import sys
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

# إنشاء QApplication للاختبارات (إذا لم يكن موجوداً)
if not QApplication.instance():
    app = QApplication(sys.argv)

from src.ui.websocket_client import WebSocketClient, WebSocketClientWorker


@pytest.fixture(scope="function")
def websocket_client():
    """WebSocketClient instance للاختبارات"""
    client = WebSocketClient(api_base_url="http://localhost:8000", room="test_room")
    yield client
    client.disconnect()


class TestWebSocketClient:
    """اختبارات WebSocketClient"""

    def test_websocket_client_initialization(self):
        """اختبار تهيئة WebSocketClient"""
        client = WebSocketClient(api_base_url="http://localhost:8000", room="test_room", token="test_token")

        assert client.api_base_url == "http://localhost:8000"
        assert client.room == "test_room"
        assert client.token == "test_token"
        assert client.ws_url == "ws://localhost:8000/ws/data-updates"
        assert client.worker is None
        assert client.is_connected is False
        assert len(client.event_handlers) == 0

    def test_websocket_client_url_conversion_http(self):
        """اختبار تحويل HTTP إلى WS"""
        client = WebSocketClient(api_base_url="http://localhost:8000")
        assert client.ws_url == "ws://localhost:8000/ws/data-updates"

    def test_websocket_client_url_conversion_https(self):
        """اختبار تحويل HTTPS إلى WSS"""
        client = WebSocketClient(api_base_url="https://example.com:8000")
        assert client.ws_url == "wss://example.com:8000/ws/data-updates"

    def test_websocket_client_url_removes_trailing_slash(self):
        """اختبار إزالة trailing slash من URL"""
        client = WebSocketClient(api_base_url="http://localhost:8000/")
        assert client.ws_url == "ws://localhost:8000/ws/data-updates"

    def test_websocket_client_is_connected_property(self, websocket_client):
        """اختبار خاصية is_connected"""
        assert websocket_client.is_connected is False

        # محاكاة الاتصال
        websocket_client.is_connected = True
        assert websocket_client.is_connected is True

    def test_websocket_client_on_event_handler(self, websocket_client):
        """اختبار إضافة event handler"""
        handler1 = Mock()
        handler2 = Mock()

        websocket_client.on("test_event", handler1)
        websocket_client.on("test_event", handler2)

        assert "test_event" in websocket_client.event_handlers
        assert len(websocket_client.event_handlers["test_event"]) == 2
        assert handler1 in websocket_client.event_handlers["test_event"]
        assert handler2 in websocket_client.event_handlers["test_event"]

    def test_websocket_client_off_event_handler(self, websocket_client):
        """اختبار إزالة event handler"""
        handler1 = Mock()
        handler2 = Mock()

        websocket_client.on("test_event", handler1)
        websocket_client.on("test_event", handler2)

        websocket_client.off("test_event", handler1)

        assert handler1 not in websocket_client.event_handlers["test_event"]
        assert handler2 in websocket_client.event_handlers["test_event"]

    def test_websocket_client_off_nonexistent_handler(self, websocket_client):
        """اختبار إزالة handler غير موجود"""
        handler = Mock()

        # يجب ألا يحدث خطأ
        websocket_client.off("nonexistent", handler)
        websocket_client.off("test_event", handler)

    def test_websocket_client_handle_message_data_update(self, websocket_client):
        """اختبار معالجة رسالة data_update"""
        # Mock للـ signals
        data_update_received_mock = Mock()
        websocket_client.data_update_received = data_update_received_mock

        handler_mock = Mock()
        websocket_client.on("data_update", handler_mock)

        message = {
            "type": "data_update",
            "data": {
                "entity_type": "product",
                "entity_id": 123,
                "action": "updated",
                "data": {"name": "Test Product"},
            },
        }

        websocket_client._handle_message(message)

        # التحقق من إرسال الإشارة
        data_update_received_mock.emit.assert_called_once_with("product", 123, "updated", {"name": "Test Product"})

        # التحقق من استدعاء handler
        handler_mock.assert_called_once()

    def test_websocket_client_handle_message_notification(self, websocket_client):
        """اختبار معالجة رسالة notification"""
        notification_received_mock = Mock()
        websocket_client.notification_received = notification_received_mock

        handler_mock = Mock()
        websocket_client.on("notification", handler_mock)

        message = {
            "type": "notification",
            "data": {
                "title": "Test Title",
                "message": "Test Message",
                "notification_type": "info",
            },
        }

        websocket_client._handle_message(message)

        # التحقق من إرسال الإشارة
        notification_received_mock.emit.assert_called_once_with("Test Title", "Test Message", "info")

        # التحقق من استدعاء handler
        handler_mock.assert_called_once()

    def test_websocket_client_handle_message_error(self, websocket_client):
        """اختبار معالجة رسالة error"""
        handler_mock = Mock()
        websocket_client.on("error", handler_mock)

        message = {"type": "error", "data": {"message": "Test error"}}

        websocket_client._handle_message(message)

        # التحقق من استدعاء handler
        handler_mock.assert_called_once()

    def test_websocket_client_handle_message_unknown_type(self, websocket_client):
        """اختبار معالجة رسالة نوع غير معروف"""
        # يجب ألا يحدث خطأ
        message = {"type": "unknown_type", "data": {}}

        websocket_client._handle_message(message)

    def test_websocket_client_handle_message_exception(self, websocket_client):
        """اختبار معالجة خطأ في _handle_message"""
        # Mock handler يرفع exception
        handler_mock = Mock(side_effect=Exception("Test error"))
        websocket_client.on("data_update", handler_mock)

        message = {
            "type": "data_update",
            "data": {
                "entity_type": "product",
                "entity_id": 123,
                "action": "updated",
                "data": {},
            },
        }

        # يجب ألا يحدث crash
        websocket_client._handle_message(message)

        # Handler يجب أن يكون تم استدعاؤه
        handler_mock.assert_called_once()

    def test_websocket_client_on_connection_status_changed_connected(self, websocket_client):
        """اختبار تغيير حالة الاتصال إلى متصل"""
        connection_status_changed_mock = Mock()
        websocket_client.connection_status_changed = connection_status_changed_mock

        # Mock polling_timer
        websocket_client.polling_timer = Mock()
        websocket_client.polling_timer.isActive = Mock(return_value=True)
        websocket_client.polling_timer.stop = Mock()

        websocket_client._on_connection_status_changed(True, "متصل")

        assert websocket_client.is_connected is True
        connection_status_changed_mock.emit.assert_called_once_with(True, "متصل")
        websocket_client.polling_timer.stop.assert_called_once()
        assert websocket_client.use_polling is False

    def test_websocket_client_on_connection_status_changed_disconnected(self, websocket_client):
        """اختبار تغيير حالة الاتصال إلى منقطع"""
        connection_status_changed_mock = Mock()
        websocket_client.connection_status_changed = connection_status_changed_mock

        # Mock polling_timer
        websocket_client.polling_timer = Mock()
        websocket_client.polling_timer.isActive = Mock(return_value=False)
        websocket_client.polling_timer.start = Mock()

        websocket_client._on_connection_status_changed(False, "منقطع")

        assert websocket_client.is_connected is False
        connection_status_changed_mock.emit.assert_called_once_with(False, "منقطع")
        assert websocket_client.use_polling is True
        websocket_client.polling_timer.start.assert_called_once_with(websocket_client.polling_interval)

    def test_websocket_client_check_for_updates(self, websocket_client):
        """اختبار _check_for_updates (polling fallback)"""
        # يجب ألا يحدث خطأ
        websocket_client._check_for_updates()

    def test_websocket_client_disconnect(self, websocket_client):
        """اختبار قطع الاتصال"""
        # Mock worker
        worker_mock = Mock()
        worker_mock.isRunning = Mock(return_value=False)
        worker_mock.stop = Mock()
        worker_mock.wait = Mock()
        websocket_client.worker = worker_mock

        # Mock polling_timer
        websocket_client.polling_timer = Mock()
        websocket_client.polling_timer.isActive = Mock(return_value=True)
        websocket_client.polling_timer.stop = Mock()

        websocket_client.disconnect()

        worker_mock.stop.assert_called_once()
        worker_mock.wait.assert_called_once_with(5000)
        websocket_client.polling_timer.stop.assert_called_once()
        assert websocket_client.is_connected is False
        assert websocket_client.worker is None

    def test_websocket_client_disconnect_no_worker(self, websocket_client):
        """اختبار قطع الاتصال بدون worker"""
        websocket_client.worker = None

        # يجب ألا يحدث خطأ
        websocket_client.disconnect()

    def test_websocket_client_emit_event(self, websocket_client):
        """اختبار _emit_event"""
        handler1 = Mock()
        handler2 = Mock()

        websocket_client.on("test_event", handler1)
        websocket_client.on("test_event", handler2)

        test_data = {"key": "value"}
        websocket_client._emit_event("test_event", test_data)

        handler1.assert_called_once_with(test_data)
        handler2.assert_called_once_with(test_data)

    def test_websocket_client_emit_event_nonexistent(self, websocket_client):
        """اختبار _emit_event لحدث غير موجود"""
        # يجب ألا يحدث خطأ
        websocket_client._emit_event("nonexistent", {})

    def test_websocket_client_emit_event_handler_exception(self, websocket_client):
        """اختبار _emit_event مع exception في handler"""
        handler1 = Mock(side_effect=Exception("Error"))
        handler2 = Mock()

        websocket_client.on("test_event", handler1)
        websocket_client.on("test_event", handler2)

        # يجب ألا يحدث crash
        websocket_client._emit_event("test_event", {})

        # Handler2 يجب أن يكون تم استدعاؤه رغم خطأ Handler1
        handler2.assert_called_once()


class TestWebSocketClientWorker:
    """اختبارات WebSocketClientWorker"""

    def test_websocket_client_worker_initialization(self):
        """اختبار تهيئة WebSocketClientWorker"""
        worker = WebSocketClientWorker(ws_url="ws://localhost:8000/ws", room="test_room", token="test_token")

        assert worker.ws_url == "ws://localhost:8000/ws"
        assert worker.room == "test_room"
        assert worker.token == "test_token"
        assert worker.should_connect is True
        assert worker.is_connected is False

    def test_websocket_client_worker_stop(self):
        """اختبار إيقاف Worker"""
        worker = WebSocketClientWorker("ws://localhost:8000/ws")

        worker.stop()

        assert worker.should_connect is False
        assert worker.is_connected is False

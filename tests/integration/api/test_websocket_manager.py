#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for WebSocket Manager
اختبارات WebSocket Manager
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocket

from src.api.websocket_manager import (
    MessageType,
    WebSocketManager,
    get_websocket_manager,
)


@pytest.fixture
def websocket_manager():
    """WebSocketManager instance للاختبارات"""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket"""
    ws = AsyncMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestWebSocketManager:
    """اختبارات WebSocketManager"""

    @pytest.mark.asyncio
    async def test_websocket_manager_initialization(self):
        """اختبار تهيئة WebSocketManager"""
        manager = WebSocketManager()

        assert isinstance(manager.active_connections, dict)
        assert isinstance(manager.user_connections, dict)
        assert len(manager.active_connections) == 0
        assert len(manager.user_connections) == 0

    @pytest.mark.asyncio
    async def test_websocket_manager_connect(self, websocket_manager, mock_websocket):
        """اختبار الاتصال"""
        await websocket_manager.connect(mock_websocket, room="test_room")

        mock_websocket.accept.assert_called_once()
        assert "test_room" in websocket_manager.active_connections
        assert mock_websocket in websocket_manager.active_connections["test_room"]

    @pytest.mark.asyncio
    async def test_websocket_manager_connect_with_user_id(self, websocket_manager, mock_websocket):
        """اختبار الاتصال مع user_id"""
        await websocket_manager.connect(mock_websocket, room="test_room", user_id=123)

        assert 123 in websocket_manager.user_connections
        assert mock_websocket in websocket_manager.user_connections[123]

    @pytest.mark.asyncio
    async def test_websocket_manager_connect_multiple_rooms(self, websocket_manager, mock_websocket):
        """اختبار الاتصال في عدة rooms"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()

        await websocket_manager.connect(ws1, room="room1")
        await websocket_manager.connect(ws2, room="room2")

        assert "room1" in websocket_manager.active_connections
        assert "room2" in websocket_manager.active_connections
        assert ws1 in websocket_manager.active_connections["room1"]
        assert ws2 in websocket_manager.active_connections["room2"]

    @pytest.mark.asyncio
    async def test_websocket_manager_disconnect(self, websocket_manager, mock_websocket):
        """اختبار قطع الاتصال"""
        await websocket_manager.connect(mock_websocket, room="test_room", user_id=123)

        assert mock_websocket in websocket_manager.active_connections["test_room"]
        assert mock_websocket in websocket_manager.user_connections[123]

        websocket_manager.disconnect(mock_websocket, room="test_room", user_id=123)

        assert (
            "test_room" not in websocket_manager.active_connections
            or mock_websocket not in websocket_manager.active_connections.get("test_room", set())
        )
        assert (
            123 not in websocket_manager.user_connections
            or mock_websocket not in websocket_manager.user_connections.get(123, set())
        )

    @pytest.mark.asyncio
    async def test_websocket_manager_disconnect_removes_empty_room(self, websocket_manager, mock_websocket):
        """اختبار حذف room فارغة بعد قطع الاتصال"""
        await websocket_manager.connect(mock_websocket, room="test_room")

        websocket_manager.disconnect(mock_websocket, room="test_room")

        assert "test_room" not in websocket_manager.active_connections

    @pytest.mark.asyncio
    async def test_websocket_manager_send_personal_message(self, websocket_manager, mock_websocket):
        """اختبار إرسال رسالة شخصية"""
        message = {"type": "test", "data": "test_data"}

        await websocket_manager.send_personal_message(message, mock_websocket)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_websocket_manager_send_personal_message_error(self, websocket_manager, mock_websocket):
        """اختبار معالجة خطأ في إرسال رسالة شخصية"""
        mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection error"))

        message = {"type": "test", "data": "test_data"}

        # يجب ألا يحدث crash
        await websocket_manager.send_personal_message(message, mock_websocket)

        mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_manager_send_to_user(self, websocket_manager):
        """اختبار إرسال رسالة لمستخدم"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock()

        await websocket_manager.connect(ws1, room="room1", user_id=123)
        await websocket_manager.connect(ws2, room="room2", user_id=123)

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.send_to_user(123, message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_websocket_manager_send_to_user_nonexistent(self, websocket_manager):
        """اختبار إرسال لمستخدم غير موجود"""
        message = {"type": "test", "data": "test_data"}

        # يجب ألا يحدث خطأ
        await websocket_manager.send_to_user(999, message)

    @pytest.mark.asyncio
    async def test_websocket_manager_send_to_user_with_disconnected(self, websocket_manager):
        """اختبار إرسال لمستخدم مع اتصال منقطع"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        await websocket_manager.connect(ws1, room="room1", user_id=123)
        await websocket_manager.connect(ws2, room="room2", user_id=123)

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.send_to_user(123, message)

        # ws1 يجب أن يتلقى الرسالة
        ws1.send_json.assert_called_once()

        # ws2 يجب أن يُزال من الاتصالات
        assert ws2 not in websocket_manager.user_connections[123]

    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast_to_room(self, websocket_manager):
        """اختبار بث رسالة إلى room"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock()
        ws3 = AsyncMock(spec=WebSocket)
        ws3.send_json = AsyncMock()

        await websocket_manager.connect(ws1, room="room1")
        await websocket_manager.connect(ws2, room="room1")
        await websocket_manager.connect(ws3, room="room2")

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.broadcast_to_room("room1", message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)
        ws3.send_json.assert_not_called()  # ws3 في room مختلف

    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast_to_room_nonexistent(self, websocket_manager):
        """اختبار بث إلى room غير موجود"""
        message = {"type": "test", "data": "test_data"}

        # يجب ألا يحدث خطأ
        await websocket_manager.broadcast_to_room("nonexistent", message)

    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast_to_room_with_disconnected(self, websocket_manager):
        """اختبار بث إلى room مع اتصالات منقطعة"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock(side_effect=Exception("Connection closed"))

        await websocket_manager.connect(ws1, room="room1")
        await websocket_manager.connect(ws2, room="room1")

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.broadcast_to_room("room1", message)

        ws1.send_json.assert_called_once()
        # ws2 يجب أن يُزال من الاتصالات
        assert ws2 not in websocket_manager.active_connections.get("room1", set())

    @pytest.mark.asyncio
    async def test_websocket_manager_broadcast(self, websocket_manager):
        """اختبار بث عام لجميع rooms"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.send_json = AsyncMock()
        ws3 = AsyncMock(spec=WebSocket)
        ws3.send_json = AsyncMock()

        await websocket_manager.connect(ws1, room="room1")
        await websocket_manager.connect(ws2, room="room2")
        await websocket_manager.connect(ws3, room="room2")

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.broadcast(message)

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()
        ws3.send_json.assert_called_once()

    def test_websocket_manager_send_notification(self, websocket_manager):
        """اختبار إرسال إشعار"""
        ws = AsyncMock(spec=WebSocket)
        ws.send_json = AsyncMock()

        # استخدام loop جديد
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:

            async def setup_and_send():
                await websocket_manager.connect(ws, room="room1", user_id=123)
                websocket_manager.send_notification(123, "Test Title", "Test Message", "info")
                # انتظار قصير للـ async task
                await asyncio.sleep(0.1)

            loop.run_until_complete(setup_and_send())

            # التحقق من أن send_json تم استدعاؤه
            assert ws.send_json.called
            call_args = ws.send_json.call_args[0][0]
            assert call_args["type"] == MessageType.NOTIFICATION.value
            assert call_args["data"]["title"] == "Test Title"
            assert call_args["data"]["message"] == "Test Message"
            assert call_args["data"]["notification_type"] == "info"
        finally:
            loop.close()

    def test_websocket_manager_send_data_update(self, websocket_manager):
        """اختبار إرسال تحديث بيانات"""
        ws = AsyncMock(spec=WebSocket)
        ws.send_json = AsyncMock()

        # استخدام loop جديد
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:

            async def setup_and_send():
                await websocket_manager.connect(ws, room="data_updates")
                websocket_manager.send_data_update("data_updates", "product", 123, "updated", {"name": "Test Product"})
                # انتظار قصير للـ async task
                await asyncio.sleep(0.1)

            loop.run_until_complete(setup_and_send())

            # التحقق من أن send_json تم استدعاؤه
            assert ws.send_json.called
            call_args = ws.send_json.call_args[0][0]
            assert call_args["type"] == MessageType.DATA_UPDATE.value
            assert call_args["data"]["entity_type"] == "product"
            assert call_args["data"]["entity_id"] == 123
            assert call_args["data"]["action"] == "updated"
            assert call_args["data"]["data"]["name"] == "Test Product"
        finally:
            loop.close()

    def test_get_websocket_manager_singleton(self):
        """اختبار أن get_websocket_manager يُرجع singleton"""
        manager1 = get_websocket_manager()
        manager2 = get_websocket_manager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_websocket_manager_multiple_connections_same_user(self, websocket_manager):
        """اختبار عدة اتصالات لنفس المستخدم"""
        ws1 = AsyncMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        ws2 = AsyncMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await websocket_manager.connect(ws1, room="room1", user_id=123)
        await websocket_manager.connect(ws2, room="room2", user_id=123)

        message = {"type": "test", "data": "test_data"}
        await websocket_manager.send_to_user(123, message)

        ws1.send_json.assert_called_once()
        ws2.send_json.assert_called_once()

import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Manager - مدير WebSockets
إدارة الاتصالات WebSocket للـ Real-time Updates
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """نوع الرسالة"""

    NOTIFICATION = "notification"
    DATA_UPDATE = "data_update"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


class WebSocketManager:
    """مدير WebSockets"""

    def __init__(self):
        """تهيئة مدير WebSockets"""
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_connections: Dict[int, Set[WebSocket]] = {}
        self.logger = logger

    async def connect(self, websocket: WebSocket, room: str = "default", user_id: Optional[int] = None):
        """
        الاتصال بـ WebSocket

        Args:
            websocket: WebSocket connection
            room: Room name (للـ broadcasting)
            user_id: User ID (لإرسال رسائل شخصية)
        """
        await websocket.accept()

        # إضافة إلى Room
        if room not in self.active_connections:
            self.active_connections[room] = set()
        self.active_connections[room].add(websocket)

        # إضافة إلى User Connections
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)

        self.logger.info(f"✅ WebSocket متصل: room={room}, user_id={user_id}")

    def disconnect(self, websocket: WebSocket, room: str = "default", user_id: Optional[int] = None):
        """
        قطع الاتصال بـ WebSocket

        Args:
            websocket: WebSocket connection
            room: Room name
            user_id: User ID
        """
        # إزالة من Room
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)
            if not self.active_connections[room]:
                del self.active_connections[room]

        # إزالة من User Connections
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        self.logger.info(f"❌ WebSocket منقطع: room={room}, user_id={user_id}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        إرسال رسالة شخصية

        Args:
            message: الرسالة (Dict)
            websocket: WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            self.logger.error(f"❌ خطأ في إرسال رسالة شخصية: {e}", exc_info=True)

    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """
        إرسال رسالة إلى مستخدم محدد

        Args:
            user_id: معرف المستخدم
            message: الرسالة (Dict)
        """
        if user_id in self.user_connections:
            disconnected = set()
            for websocket in self.user_connections[user_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    self.logger.error(f"❌ خطأ في إرسال رسالة للمستخدم {user_id}: {e}")
                    disconnected.add(websocket)

            # إزالة الاتصالات المنقطعة
            for ws in disconnected:
                self.user_connections[user_id].discard(ws)

    async def broadcast_to_room(self, room: str, message: Dict[str, Any]):
        """
        بث رسالة إلى جميع الاتصالات في Room

        Args:
            room: Room name
            message: الرسالة (Dict)
        """
        if room in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[room].copy():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    self.logger.error(f"❌ خطأ في بث رسالة إلى room {room}: {e}")
                    disconnected.add(websocket)

            # إزالة الاتصالات المنقطعة
            for ws in disconnected:
                self.active_connections[room].discard(ws)

    async def broadcast(self, message: Dict[str, Any]):
        """
        بث رسالة إلى جميع الاتصالات

        Args:
            message: الرسالة (Dict)
        """
        for room in list(self.active_connections.keys()):
            await self.broadcast_to_room(room, message)

    def send_notification(self, user_id: int, title: str, message: str, notification_type: str = "info"):
        """
        إرسال إشعار إلى مستخدم

        Args:
            user_id: معرف المستخدم
            title: عنوان الإشعار
            message: رسالة الإشعار
            notification_type: نوع الإشعار (info, success, warning, error)
        """
        notification = {
            "type": MessageType.NOTIFICATION.value,
            "data": {
                "title": title,
                "message": message,
                "notification_type": notification_type,
                "timestamp": datetime.now().isoformat(),
            },
        }
        # سيتم إرسالها بشكل async
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.send_to_user(user_id, notification))
            else:
                loop.run_until_complete(self.send_to_user(user_id, notification))
        except Exception as e:
            self.logger.debug(f"send_notification failed (non-critical): {e}")

    def send_data_update(
        self,
        room: str,
        entity_type: str,
        entity_id: int,
        action: str,
        data: Dict[str, Any],
    ):
        """
        إرسال تحديث بيانات

        Args:
            room: Room name
            entity_type: نوع الكيان
            entity_id: معرف الكيان
            action: الإجراء (created, updated, deleted)
            data: البيانات
        """
        update_message = {
            "type": MessageType.DATA_UPDATE.value,
            "data": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            },
        }
        # سيتم إرسالها بشكل async
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.broadcast_to_room(room, update_message))
            else:
                loop.run_until_complete(self.broadcast_to_room(room, update_message))
        except Exception as e:
            self.logger.debug(f"send_data_update failed (non-critical): {e}")


# Singleton instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager() -> WebSocketManager:
    """الحصول على مدير WebSockets (Singleton)"""
    global _websocket_manager
    if _websocket_manager is None:
        _websocket_manager = WebSocketManager()
    return _websocket_manager

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Client للـ Desktop Application
للاتصال بـ Backend WebSocket والاستماع للتحديثات الفورية
"""

import logging
import asyncio
import threading
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from enum import Enum
import websockets
from PySide6.QtCore import QObject, Signal, QTimer, QThread, QRunnable
from src.api.thread_pool_manager import ThreadPoolManager, BaseRunnable

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """نوع الرسالة"""
    CONNECTION = "connection"
    DATA_UPDATE = "data_update"
    NOTIFICATION = "notification"
    ERROR = "error"
    PONG = "pong"


class WebSocketSignals(QObject):
    """إشارات WebSocket (يجب أن تكون QObject)"""
    message_received = Signal(dict)
    connection_status_changed = Signal(bool, str)  # connected, message


class WebSocketClientRunnable(BaseRunnable):
    """Runnable لـ WebSocket connection (يستخدم QThreadPool)"""
    
    def __init__(self, ws_url: str, room: str = "data_updates", token: Optional[str] = None, 
                 signals: Optional[WebSocketSignals] = None, callback: Optional[Callable] = None):
        super().__init__(callback)
        self.ws_url = ws_url
        self.room = room
        self.token = token
        self.signals = signals or WebSocketSignals()
        self.should_connect = True
        self.is_connected = False
        
    def run(self):
        """تشغيل WebSocket connection"""
        asyncio.run(self._run_websocket())
    
    async def _run_websocket(self):
        """تشغيل WebSocket connection"""
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        reconnect_delay = 1  # ثانية
        
        while self.should_connect:
            try:
                # بناء URL
                url = f"{self.ws_url}?room={self.room}"
                if self.token:
                    url += f"&token={self.token}"
                
                logger.info(f"🔌 محاولة الاتصال بـ WebSocket: {url}")
                
                async with websockets.connect(url) as websocket:
                    self.is_connected = True
                    reconnect_attempts = 0
                    self.signals.connection_status_changed.emit(True, "متصل")
                    logger.info("✅ تم الاتصال بـ WebSocket بنجاح")
                    
                    # Keep-alive loop
                    while self.should_connect and self.is_connected:
                        try:
                            # استقبال رسالة (مع timeout)
                            message = await asyncio.wait_for(
                                websocket.recv(),
                                timeout=30.0  # 30 ثانية
                            )
                            
                            # معالجة الرسالة
                            try:
                                data = json.loads(message)
                                
                                # إرسال pong عند استلام ping
                                if data.get("type") == "ping":
                                    await websocket.send(json.dumps({"type": "pong"}))
                                    continue
                                
                                # إرسال الرسالة للإشارة
                                self.signals.message_received.emit(data)
                                
                            except json.JSONDecodeError:
                                logger.warning(f"رسالة غير صالحة: {message}")
                                
                        except asyncio.TimeoutError:
                            # إرسال ping للـ keep-alive
                            await websocket.send(json.dumps({"type": "ping"}))
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("WebSocket connection closed")
                            break
                        except Exception as e:
                            logger.error(f"خطأ في استقبال رسالة: {e}")
                            break
                            
            except Exception as e:
                # Log as debug/info to avoid console spam in local/offline mode
                if reconnect_attempts == 0:
                    logger.debug(f"⚠️ WebSocket connection failed: {e}")
                
                self.is_connected = False
                self.signals.connection_status_changed.emit(False, f"خطأ: {str(e)}")
                
                # إعادة الاتصال
                if self.should_connect and reconnect_attempts < max_reconnect_attempts:
                    reconnect_attempts += 1
                    delay = reconnect_delay * (2 ** (reconnect_attempts - 1))  # Exponential backoff
                    # logger.debug(f"🔄 إعادة الاتصال بعد {delay} ثانية...") 
                    await asyncio.sleep(delay)
                else:
                    if reconnect_attempts >= max_reconnect_attempts:
                         # Final failure -> Warning instead of Error
                        logger.warning("❌ تم تجاوز عدد محاولات إعادة الاتصال (WebSocket offline)")
                        self.signals.connection_status_changed.emit(False, "فشل إعادة الاتصال")
                    break
    
    def stop(self):
        """إيقاف الاتصال"""
        self.should_connect = False
        self.is_connected = False


# Backward compatibility - يمكن استخدام QThread أيضاً
class WebSocketClientWorker(QThread):
    """Worker thread لـ WebSocket connection (Legacy - يستخدم QThread)"""
    
    message_received = Signal(dict)
    connection_status_changed = Signal(bool, str)
    
    def __init__(self, ws_url: str, room: str = "data_updates", token: Optional[str] = None):
        super().__init__()
        self.ws_url = ws_url
        self.room = room
        self.token = token
        self.should_connect = True
        self.is_connected = False
        
    def run(self):
        """تشغيل WebSocket connection"""
        asyncio.run(self._run_websocket())
    
    async def _run_websocket(self):
        """تشغيل WebSocket connection"""
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        reconnect_delay = 1
        
        while self.should_connect:
            try:
                url = f"{self.ws_url}?room={self.room}"
                if self.token:
                    url += f"&token={self.token}"
                
                async with websockets.connect(url) as websocket:
                    self.is_connected = True
                    reconnect_attempts = 0
                    self.connection_status_changed.emit(True, "متصل")
                    
                    while self.should_connect and self.is_connected:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                            data = json.loads(message)
                            
                            if data.get("type") == "ping":
                                await websocket.send(json.dumps({"type": "pong"}))
                                continue
                            
                            self.message_received.emit(data)
                        except asyncio.TimeoutError:
                            await websocket.send(json.dumps({"type": "ping"}))
                        except websockets.exceptions.ConnectionClosed:
                            break
                        except Exception as e:
                            logger.error(f"خطأ في استقبال رسالة: {e}")
                            break
            except Exception as e:
                logger.error(f"❌ خطأ في WebSocket connection: {e}")
                self.is_connected = False
                self.connection_status_changed.emit(False, f"خطأ: {str(e)}")
                
                if self.should_connect and reconnect_attempts < max_reconnect_attempts:
                    reconnect_attempts += 1
                    delay = reconnect_delay * (2 ** (reconnect_attempts - 1))
                    await asyncio.sleep(delay)
                else:
                    break
    
    def stop(self):
        """إيقاف الاتصال"""
        self.should_connect = False
        self.is_connected = False


class WebSocketClient(QObject):
    """WebSocket Client للـ Desktop"""
    
    # إشارات Qt
    data_update_received = Signal(str, int, str, dict)  # entity_type, entity_id, action, data
    notification_received = Signal(str, str, str)  # title, message, notification_type
    connection_status_changed = Signal(bool, str)  # connected, message
    
    def __init__(
        self,
        api_base_url: str = "http://localhost:8000",
        room: str = "data_updates",
        token: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.api_base_url = api_base_url.rstrip('/')
        self.room = room
        self.token = token
        
        # تحويل HTTP/HTTPS إلى WS/WSS
        ws_url = self.api_base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        ws_path = "/ws/data-updates"
        self.ws_url = f"{ws_url}{ws_path}"
        
        # Worker (Runnable أو Thread)
        self.worker: Optional[WebSocketClientRunnable] = None
        self.worker_thread: Optional[WebSocketClientWorker] = None  # للـ backward compatibility
        self.signals: Optional[WebSocketSignals] = None
        self.is_connected = False
        self.use_thread_pool = True  # استخدام QThreadPool افتراضياً
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Polling fallback timer
        self.polling_timer = QTimer(self)
        self.polling_timer.timeout.connect(self._check_for_updates)
        self.use_polling = False
        self.polling_interval = 5000  # 5 ثوان
        
        logger.info(f"WebSocket Client تم إنشاؤه: {self.ws_url}")
    
    def connect(self):
        """بدء الاتصال"""
        if (self.worker and hasattr(self.worker, 'is_connected') and self.worker.is_connected) or \
           (self.worker_thread and self.worker_thread.isRunning()):
            logger.warning("WebSocket connection موجود بالفعل")
            return
        
        logger.info("🔌 بدء الاتصال بـ WebSocket...")
        
        if self.use_thread_pool:
            # استخدام QThreadPool (QRunnable)
            self.signals = WebSocketSignals()
            self.signals.message_received.connect(self._handle_message)
            self.signals.connection_status_changed.connect(self._on_connection_status_changed)
            
            self.worker = WebSocketClientRunnable(self.ws_url, self.room, self.token, self.signals)
            thread_pool = ThreadPoolManager.get_instance()
            thread_pool.start(self.worker)
        else:
            # استخدام QThread (backward compatibility)
            self.worker_thread = WebSocketClientWorker(self.ws_url, self.room, self.token)
            self.worker_thread.message_received.connect(self._handle_message)
            self.worker_thread.connection_status_changed.connect(self._on_connection_status_changed)
            self.worker_thread.start()
    
    def disconnect(self):
        """قطع الاتصال"""
        if self.worker:
            self.worker.stop()
            if hasattr(self.worker, 'wait'):
                try:
                    self.worker.wait(5000)
                except Exception:
                    pass
            self.worker = None
            self.signals = None
        
        if self.worker_thread:
            self.worker_thread.stop()
            self.worker_thread.wait(5000)  # انتظار حتى 5 ثوان
            self.worker_thread = None
        
        if self.polling_timer.isActive():
            self.polling_timer.stop()
        
        self.is_connected = False
        logger.info("❌ تم قطع الاتصال بـ WebSocket")
    
    def _handle_message(self, message: Dict[str, Any]):
        """معالجة الرسالة الواردة"""
        try:
            message_type = message.get("type")
            data = message.get("data", {})
            
            if message_type == "data_update":
                entity_type = data.get("entity_type", "")
                entity_id = data.get("entity_id", 0)
                action = data.get("action", "")
                entity_data = data.get("data", {})
                
                # إرسال إشارة
                self.data_update_received.emit(entity_type, entity_id, action, entity_data)
                
                # استدعاء handlers
                self._emit_event("data_update", {
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "action": action,
                    "data": entity_data
                })
                
            elif message_type == "notification":
                title = data.get("title", "")
                message_text = data.get("message", "")
                notification_type = data.get("notification_type", "info")
                
                self.notification_received.emit(title, message_text, notification_type)
                self._emit_event("notification", data)
            
            elif message_type == "error":
                logger.error(f"WebSocket error: {data.get('message', 'Unknown error')}")
                self._emit_event("error", data)
            
        except Exception as e:
            logger.error(f"خطأ في معالجة رسالة WebSocket: {e}")
    
    def _on_connection_status_changed(self, connected: bool, message: str):
        """معالجة تغيير حالة الاتصال"""
        self.is_connected = connected
        self.connection_status_changed.emit(connected, message)
        
        if connected:
            # إيقاف polling إذا كان مفعلاً
            if self.polling_timer.isActive():
                self.polling_timer.stop()
                self.use_polling = False
                logger.info("✅ تم الاتصال بـ WebSocket - تم إيقاف polling")
        else:
            # تفعيل polling fallback
            if not self.use_polling and not self.polling_timer.isActive():
                logger.warning("⚠️ تم فقدان الاتصال بـ WebSocket - تفعيل polling fallback")
                self.use_polling = True
                self.polling_timer.start(self.polling_interval)
    
    def _check_for_updates(self):
        """فحص التحديثات (polling fallback)"""
        # يمكن إضافة logic للـ polling هنا
        # على سبيل المثال: فحص آخر timestamp للبيانات
        pass
    
    def on(self, event: str, handler: Callable):
        """إضافة event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable):
        """إزالة event handler"""
        if event in self.event_handlers:
            try:
                self.event_handlers[event].remove(handler)
            except ValueError:
                pass
    
    def _emit_event(self, event: str, data: Dict[str, Any]):
        """إرسال event للمعالجات"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"خطأ في event handler: {e}")


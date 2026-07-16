#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remote Logger
نظام التسجيل والمراقبة عن بعد (Remote Logging/Telemetry)
"""

import platform
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from src.api.api_client import APIClient
from src.api.thread_pool_manager import BaseRunnable, ThreadPoolManager
from src.utils.logger import setup_logger


class LogLevel(Enum):
    """مستويات السجل"""

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


from PySide6.QtCore import QObject, Signal


class RemoteLogSignals(QObject):
    """إشارات Remote Logger (QObject)"""

    log_sent = Signal(bool, str)  # success, message


class RemoteLogRunnable(BaseRunnable):
    """Runnable لإرسال السجلات في الخلفية"""

    def __init__(
        self,
        log_data: Dict[str, Any],
        api_client: APIClient,
        signals: Optional[RemoteLogSignals] = None,
    ):
        super().__init__()
        self.log_data = log_data
        self.api_client = api_client
        self.signals = signals

    def run(self):
        """إرسال السجل"""
        try:
            self.api_client.post("/api/v1/logs", self.log_data)
            if self.signals:
                self.signals.log_sent.emit(True, "تم إرسال السجل")
        except Exception as e:
            if self.signals:
                self.signals.log_sent.emit(False, str(e))


class RemoteLogger:
    """نظام التسجيل والمراقبة عن بعد"""

    def __init__(self, api_client: APIClient, enabled: bool = True):
        self.api_client = api_client
        self.enabled = enabled
        self.logger = setup_logger(__name__)
        self.thread_pool = ThreadPoolManager.get_instance()

        # معلومات الجهاز
        self.device_info = self._get_device_info()

    def _get_device_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الجهاز"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        }

    def log(
        self,
        level: LogLevel,
        message: str,
        error: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
    ):
        """
        إرسال سجل إلى الخادم

        Args:
            level: مستوى السجل
            message: الرسالة
            error: خطأ (اختياري)
            context: سياق إضافي (اختياري)
            user_id: معرف المستخدم (اختياري)
        """
        if not self.enabled:
            return

        # إرسال فقط الأخطاء الحرجة
        if level not in [LogLevel.ERROR, LogLevel.CRITICAL]:
            return

        try:
            log_data = {
                "level": level.value,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "device_info": self.device_info,
                "user_id": user_id,
                "context": context or {},
            }

            if error:
                log_data["error"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": self._get_traceback(error),
                }

            # إرسال في الخلفية (Worker Thread)
            runnable = RemoteLogRunnable(log_data, self.api_client)
            self.thread_pool.start(runnable)

        except Exception as e:
            self.logger.warning(f"⚠️ فشل إرسال Remote Log: {str(e)}")

    def _get_traceback(self, error: Exception) -> str:
        """الحصول على Traceback"""
        import traceback

        return traceback.format_exc()

    def send_telemetry(self, metrics: Dict[str, Any]):
        """
        إرسال Telemetry data

        Args:
            metrics: البيانات المترية
        """
        if not self.enabled:
            return

        try:
            telemetry_data = {
                "type": "telemetry",
                "timestamp": datetime.now().isoformat(),
                "device_info": self.device_info,
                "metrics": metrics,
            }

            runnable = RemoteLogRunnable(telemetry_data, self.api_client)
            self.thread_pool.start(runnable)

        except Exception as e:
            self.logger.warning(f"⚠️ فشل إرسال Telemetry: {str(e)}")

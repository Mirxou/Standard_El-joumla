#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Circuit Breaker
نظام Circuit Breaker مع Exponential Backoff ووضع الطوارئ
"""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

from src.utils.logger import setup_logger


class CircuitState(Enum):
    """حالات Circuit Breaker"""

    CLOSED = "closed"  # طبيعي - كل الطلبات تمر
    OPEN = "open"  # فشل متكرر - توقف المحاولات
    HALF_OPEN = "half_open"  # محاولة استعادة الاتصال


class CircuitBreaker:
    """Circuit Breaker مع Exponential Backoff"""

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        half_open_timeout: int = 30,
        initial_backoff: float = 1.0,
        max_backoff: float = 300.0,
        backoff_multiplier: float = 2.0,
    ):
        """
        تهيئة Circuit Breaker

        Args:
            failure_threshold: عدد الفشل قبل فتح الدائرة
            timeout: وقت الانتظار قبل محاولة الاستعادة (ثوان)
            half_open_timeout: وقت الانتظار في حالة HALF_OPEN (ثوان)
            initial_backoff: وقت الانتظار الأولي (ثوان)
            max_backoff: الحد الأقصى لوقت الانتظار (ثوان)
            backoff_multiplier: مضاعف وقت الانتظار
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.half_open_timeout = half_open_timeout
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        self.backoff_multiplier = backoff_multiplier

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.manual_offline = False  # وضع الطوارئ (Manual Offline Mode)

        self.logger = setup_logger(__name__)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        استدعاء دالة مع حماية Circuit Breaker

        Args:
            func: الدالة للاستدعاء
            *args: معاملات الدالة
            **kwargs: معاملات الدالة

        Returns:
            نتيجة الدالة

        Raises:
            Exception: إذا كان Circuit Breaker مفتوحاً أو في وضع الطوارئ
        """
        # التحقق من وضع الطوارئ
        if self.manual_offline:
            raise Exception("Circuit Breaker في وضع الطوارئ (Manual Offline Mode)")

        # التحقق من حالة Circuit Breaker
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("🔄 Circuit Breaker: الانتقال إلى حالة HALF_OPEN")
            else:
                raise Exception(f"Circuit Breaker مفتوح - فشل {self.failure_count} مرة")

        # محاولة الاستدعاء
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """التحقق من إمكانية محاولة الاستعادة"""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.timeout

    def _on_success(self):
        """معالجة النجاح"""
        self.last_success_time = datetime.now()
        self.success_count += 1
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            # إذا نجحت في HALF_OPEN، أغلق الدائرة فوراً
            self.state = CircuitState.CLOSED
            self.success_count = 0
            self.logger.info("✅ Circuit Breaker: تم إغلاق الدائرة - الاتصال مستعاد")
        elif self.state == CircuitState.OPEN:
            # محاولة الانتقال إلى HALF_OPEN
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.logger.info("🔄 Circuit Breaker: الانتقال إلى حالة HALF_OPEN")

    def _on_failure(self):
        """معالجة الفشل"""
        self.last_failure_time = datetime.now()
        self.failure_count += 1
        self.success_count = 0

        # إذا فشل في HALF_OPEN، افتح الدائرة فوراً
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.logger.warning("⚠️ Circuit Breaker: فشل في HALF_OPEN - فتح الدائرة")
            return

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                self.logger.warning(f"⚠️ Circuit Breaker: تم فتح الدائرة - {self.failure_count} فشل")

    def get_backoff_delay(self) -> float:
        """
        الحصول على وقت الانتظار (Exponential Backoff)

        Returns:
            وقت الانتظار بالثواني
        """
        delay = min(
            self.initial_backoff * (self.backoff_multiplier ** (self.failure_count - 1)),
            self.max_backoff,
        )
        return delay

    def set_manual_offline(self, offline: bool = True):
        """
        تعيين وضع الطوارئ (Manual Offline Mode)

        Args:
            offline: True لوضع الطوارئ، False للعودة للوضع العادي
        """
        self.manual_offline = offline
        if offline:
            self.logger.info("🔴 Circuit Breaker: تم تفعيل وضع الطوارئ (Manual Offline Mode)")
        else:
            self.logger.info("🟢 Circuit Breaker: تم إلغاء وضع الطوارئ")

    def reset(self):
        """إعادة تعيين Circuit Breaker"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.manual_offline = False
        self.logger.info("🔄 Circuit Breaker: تم إعادة التعيين")

    def get_state(self) -> Dict[str, Any]:
        """
        الحصول على حالة Circuit Breaker

        Returns:
            معلومات حالة Circuit Breaker
        """
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (self.last_failure_time.isoformat() if self.last_failure_time else None),
            "last_success_time": (self.last_success_time.isoformat() if self.last_success_time else None),
            "manual_offline": self.manual_offline,
            "backoff_delay": self.get_backoff_delay(),
        }

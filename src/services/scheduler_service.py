"""
خدمة الجدولة البسيطة للتذكيرات
Reminder Scheduler Service

تشغّل فحص التذكيرات المستحقة كل فترة زمنية وتستدعي إرسالها.
يمكن تفعيلها أو تعطيلها عبر متغيرات البيئة:
- SCHEDULER_ENABLED=true|false (افتراضي true)
- SCHEDULER_INTERVAL_SECONDS=300 (افتراضي 300 ثانية)
"""
from __future__ import annotations
import os
import threading
import time
import logging
from typing import Optional, Callable

from src.services.reminder_service import ReminderService, get_reminder_service

logger = logging.getLogger(__name__)

class ReminderScheduler:
    def __init__(self, reminder_service: ReminderService, interval_seconds: Optional[int] = None):
        self.reminder_service = reminder_service
        self.interval = interval_seconds or int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "300"))
        self.enabled = os.getenv("SCHEDULER_ENABLED", "true").lower() in ("1", "true", "yes", "on")
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> bool:
        if not self.enabled:
            logger.info("ReminderScheduler disabled by environment variable")
            return False
        if self._running:
            return True
        logger.info(f"Starting ReminderScheduler interval={self.interval}s")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="ReminderScheduler", daemon=True)
        self._thread.start()
        self._running = True
        return True

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                rs = self.reminder_service
                result = rs.send_due_reminders()
                if result.get('total'):
                    logger.info(f"Sent reminders: {result}")
            except Exception as e:
                logger.error(f"Scheduler iteration failed: {e}")
            # الانتظار للفترة المحددة أو حتى الإيقاف
            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        if not self._running:
            return
        logger.info("Stopping ReminderScheduler")
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        self._running = False

    def is_running(self) -> bool:
        return self._running and not self._stop_event.is_set()

# واجهة عامة
_scheduler_global: Optional[ReminderScheduler] = None

def init_reminder_scheduler(reminder_service: Optional[ReminderService] = None) -> ReminderScheduler:
    global _scheduler_global
    if reminder_service is None:
        reminder_service = get_reminder_service()
        if reminder_service is None:
            raise RuntimeError("ReminderService not initialized before scheduler")
    _scheduler_global = ReminderScheduler(reminder_service)
    _scheduler_global.start()
    return _scheduler_global

def get_reminder_scheduler() -> Optional[ReminderScheduler]:
    return _scheduler_global

import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thread Pool Manager
مدير Thread Pool لاستخدام QThreadPool بدلاً من QThread
"""

from typing import Any, Callable, Optional

from PySide6.QtCore import QRunnable, QThreadPool

from src.utils.logger import setup_logger


class ThreadPoolManager:
    """مدير Thread Pool موحد للتطبيق"""

    _instance: Optional["ThreadPoolManager"] = None

    def __init__(self):
        if ThreadPoolManager._instance is not None:
            raise RuntimeError("ThreadPoolManager is a singleton. Use get_instance()")

        self.logger = setup_logger(__name__)
        self.thread_pool = QThreadPool.globalInstance()
        # تعيين عدد الخيوط المتاحة
        self.thread_pool.setMaxThreadCount(4)  # يمكن تعديله حسب الحاجة
        self.logger.info(f"✅ تم تهيئة Thread Pool Manager (Max Threads: {self.thread_pool.maxThreadCount()})")

    @classmethod
    def get_instance(cls) -> "ThreadPoolManager":
        """الحصول على Instance الوحيد"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def start(self, runnable: QRunnable, priority: int = 0):
        """
        تشغيل Runnable في Thread Pool

        Args:
            runnable: QRunnable للتشغيل
            priority: الأولوية (0 = عادية)
        """
        self.thread_pool.start(runnable, priority)
        self.logger.debug("🔄 تم بدء تشغيل Runnable في Thread Pool")

    def wait_for_done(self, timeout: int = -1) -> bool:
        """
        انتظار انتهاء جميع المهام

        Args:
            timeout: مهلة الانتظار بالمللي ثانية (-1 = لا نهائي)

        Returns:
            True إذا انتهت جميع المهام
        """
        return self.thread_pool.waitForDone(timeout)

    def active_thread_count(self) -> int:
        """عدد الخيوط النشطة"""
        return self.thread_pool.activeThreadCount()

    def max_thread_count(self) -> int:
        """الحد الأقصى لعدد الخيوط"""
        return self.thread_pool.maxThreadCount()

    def set_max_thread_count(self, count: int):
        """تعيين الحد الأقصى لعدد الخيوط"""
        self.thread_pool.setMaxThreadCount(count)
        self.logger.info(f"✅ تم تحديث Max Thread Count إلى: {count}")


class BaseRunnable(QRunnable):
    """الكلاس الأساسي لجميع Runnables"""

    def __init__(self, callback: Optional[Callable] = None):
        super().__init__()
        self.callback = callback
        self.logger = setup_logger(__name__)

    def run(self):
        """تنفيذ المهمة (يجب تخطيطه في الكلاسات الفرعية)"""
        raise NotImplementedError("Subclasses must implement run()")

    def on_complete(self, result: Any = None):
        """استدعاء Callback عند اكتمال المهمة"""
        if self.callback:
            try:
                self.callback(result)
            except Exception as e:
                self.logger.error(f"❌ خطأ في Callback: {str(e)}")

    def on_error(self, error: Exception):
        """معالجة الأخطاء"""
        self.logger.error(f"❌ خطأ في Runnable: {str(error)}")
        if self.callback:
            try:
                self.callback(None, error)
            except Exception as e:
                self.logger.debug(f"on_error callback failed (non-critical): {e}")

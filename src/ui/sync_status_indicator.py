#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
Sync Status Indicator - مؤشر حالة المزامنة
عرض حالة الاتصال والعمليات المعلقة للمزامنة
"""

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QLabel

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SyncStatusIndicator(QObject):
    """
    مؤشر حالة المزامنة
    يعرض حالة الاتصال وعدد العمليات المعلقة
    """

    # إشارات
    status_changed = Signal(str)  # حالة الاتصال تغيرت
    pending_count_changed = Signal(int)  # عدد العمليات المعلقة تغير

    def __init__(self, hybrid_service=None, parent=None):
        """
        تهيئة مؤشر حالة المزامنة

        Args:
            hybrid_service: HybridDataService (اختياري)
            parent: Widget parent
        """
        super().__init__(parent)
        self.hybrid_service = hybrid_service
        self.is_online = False
        self.pending_count = 0
        self.logger = setup_logger(__name__)

        # Timer لتحديث الحالة
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.setInterval(5000)  # تحديث كل 5 ثوان
        self.update_timer.start()

        # Timer للمزامنة التلقائية (كل 30 ثانية)
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.auto_sync)
        self.sync_timer.setInterval(30000)  # 30 ثانية
        self.sync_timer.start()

        # تحديث أولي
        self.update_status()

    def set_hybrid_service(self, hybrid_service):
        """تعيين HybridDataService"""
        self.hybrid_service = hybrid_service
        self.update_status()

    def update_status(self):
        """تحديث حالة الاتصال والعمليات المعلقة"""
        try:
            # التحقق من حالة الاتصال
            if self.hybrid_service and self.hybrid_service.api:
                new_online_status = self.hybrid_service.api.is_online(force_check=False)
                if new_online_status != self.is_online:
                    self.is_online = new_online_status
                    self.status_changed.emit(self.get_status_text())

            # حساب عدد العمليات المعلقة
            if self.hybrid_service:
                new_pending_count = self._get_pending_count()
                if new_pending_count != self.pending_count:
                    self.pending_count = new_pending_count
                    self.pending_count_changed.emit(self.pending_count)
        except Exception as e:
            self.logger.error(f"خطأ في تحديث حالة المزامنة: {e}")

    def _get_pending_count(self) -> int:
        """الحصول على عدد العمليات المعلقة"""
        try:
            if not self.hybrid_service or not self.hybrid_service.db:
                return 0

            with self.hybrid_service.db.get_cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM sync_queue WHERE synced = 0")
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception:
            # جدول sync_queue قد لا يكون موجوداً بعد
            return 0

    def get_status_text(self) -> str:
        """الحصول على نص الحالة"""
        if self.is_online:
            if self.pending_count > 0:
                return f"🟢 متصل ({self.pending_count} معلق)"
            else:
                return "🟢 متصل"
        else:
            if self.pending_count > 0:
                return f"🔴 غير متصل ({self.pending_count} معلق)"
            else:
                return "🔴 غير متصل"

    def get_status_color(self) -> str:
        """الحصول على لون الحالة"""
        if self.is_online:
            return "#28a745"  # أخضر
        else:
            return "#dc3545"  # أحمر

    def auto_sync(self):
        """مزامنة تلقائية للعمليات المعلقة"""
        if not self.hybrid_service or not self.is_online:
            return

        if self.pending_count > 0:
            try:
                result = self.hybrid_service.sync_pending_changes()
                if result["synced"] > 0:
                    self.logger.info(f"تمت مزامنة {result['synced']} عملية تلقائياً")
                self.update_status()
            except Exception as e:
                self.logger.error(f"خطأ في المزامنة التلقائية: {e}")

    def force_sync(self) -> dict:
        """
        فرض مزامنة العمليات المعلقة

        Returns:
            إحصائيات المزامنة
        """
        if not self.hybrid_service:
            return {"synced": 0, "failed": 0, "pending": 0}

        try:
            result = self.hybrid_service.sync_pending_changes()
            self.update_status()
            return result
        except Exception as e:
            self.logger.error(f"خطأ في المزامنة: {e}")
            return {"synced": 0, "failed": 0, "pending": self.pending_count}

    def set_syncing(self, syncing: bool) -> bool:
        """تعيين حالة المزامنة النشطة"""
        self.is_syncing = syncing
        if syncing:
            self.status_changed.emit("🔄 جاري المزامنة...")
        else:
            self.update_status()
        return True

    def set_sync_complete(self) -> bool:
        """تعيين المزامنة كمكتملة"""
        self.is_syncing = False
        self.update_status()
        return True


class SyncStatusWidget(QLabel):
    """
    Widget لعرض حالة المزامنة في StatusBar
    """

    def __init__(self, sync_indicator: SyncStatusIndicator, parent=None):
        """
        تهيئة Widget

        Args:
            sync_indicator: SyncStatusIndicator
            parent: Widget parent
        """
        super().__init__(parent)
        self.sync_indicator = sync_indicator

        # إعداد النص والألوان
        self.setStyleSheet("""
            QLabel {
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
        """)

        # ربط الإشارات
        self.sync_indicator.status_changed.connect(self.update_display)
        self.sync_indicator.pending_count_changed.connect(self.update_display)

        # تحديث أولي
        self.update_display()

    def update_display(self, text: str = None):
        """تحديث العرض"""
        if text is None:
            text = self.sync_indicator.get_status_text()

        self.setText(text)

        # تحديث اللون
        self.sync_indicator.get_status_color()
        self.setStyleSheet("""
            QLabel {{
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 11px;
                background-color: {color}20;
                color: {color};
                border: 1px solid {color}40;
            }}
        """)

    def mousePressEvent(self, event):
        """عند النقر - فرض مزامنة"""
        if event.button() == 1:  # Left click
            result = self.sync_indicator.force_sync()
            if result["synced"] > 0:
                self.setText(f"✅ تمت مزامنة {result['synced']} عملية")
            elif result["pending"] > 0:
                self.setText(f"⚠️ {result['pending']} عملية معلقة")
        super().mousePressEvent(event)

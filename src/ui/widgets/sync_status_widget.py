#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sync Status Widget
Widget لعرض حالة المزامنة في Main Window
"""

from datetime import datetime
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from src.utils.logger import setup_logger


class SyncStatusWidget(QWidget):
    """Widget حالة المزامنة"""

    sync_requested = Signal()
    offline_mode_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = setup_logger(__name__)
        self.is_online = True
        self.is_syncing = False
        self.last_synced: Optional[datetime] = None
        self.pending_count = 0
        self.manual_offline = False

        self.setup_ui()

        # Timer للتحديث التلقائي
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(5000)  # تحديث كل 5 ثوان

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # أيقونة الحالة
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        layout.addWidget(self.status_icon)

        # نص الحالة
        self.status_label = QLabel("جاري الاتصال...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.status_label)

        # زر المزامنة اليدوية
        self.sync_btn = QToolButton()
        self.sync_btn.setText("🔄")
        self.sync_btn.setToolTip("مزامنة الآن")
        self.sync_btn.clicked.connect(self.sync_requested.emit)
        self.sync_btn.setStyleSheet("""
            QToolButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                padding: 5px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        layout.addWidget(self.sync_btn)

        # زر وضع الطوارئ
        self.offline_btn = QToolButton()
        self.offline_btn.setText("🔴")
        self.offline_btn.setToolTip("وضع الطوارئ (إيقاف المزامنة)")
        self.offline_btn.clicked.connect(self.toggle_offline_mode)
        self.offline_btn.setStyleSheet("""
            QToolButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 3px;
                padding: 5px;
                color: white;
            }
            QToolButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        layout.addWidget(self.offline_btn)

        layout.addStretch()

    def update_status(self, status: Dict[str, Any]):
        """
        تحديث حالة المزامنة

        Args:
            status: معلومات الحالة
        """
        self.is_online = status.get("is_online", True)
        self.is_syncing = status.get("is_syncing", False)
        self.pending_count = status.get("pending_count", 0)
        self.manual_offline = status.get("manual_offline", False)

        last_synced_str = status.get("last_synced_at")
        if last_synced_str:
            try:
                self.last_synced = datetime.fromisoformat(last_synced_str)
            except Exception:
                self.last_synced = None
        else:
            self.last_synced = None

        self.update_display()

    def update_display(self):
        """تحديث العرض"""
        # تحديث الأيقونة
        if self.manual_offline:
            self._set_status_icon("red")  # وضع الطوارئ
            status_text = "وضع الطوارئ"
        elif not self.is_online:
            self._set_status_icon("red")  # غير متصل
            status_text = "غير متصل"
        elif self.is_syncing:
            self._set_status_icon("yellow")  # جاري المزامنة
            status_text = "جاري المزامنة..."
        elif self.pending_count > 0:
            self._set_status_icon("yellow")  # معلق
            status_text = f"{self.pending_count} معلق"
        else:
            self._set_status_icon("green")  # متزامن
            if self.last_synced:
                elapsed = (datetime.now() - self.last_synced).total_seconds()
                if elapsed < 60:
                    status_text = f"متزامن ({int(elapsed)}ث)"
                elif elapsed < 3600:
                    status_text = f"متزامن ({int(elapsed/60)}د)"
                else:
                    status_text = "متزامن"
            else:
                status_text = "متزامن"

        self.status_label.setText(status_text)

        # تحديث Tooltip
        tooltip = f"حالة المزامنة: {status_text}"
        if self.last_synced:
            tooltip += f"\nآخر مزامنة: {self.last_synced.strftime('%Y-%m-%d %H:%M:%S')}"
        if self.pending_count > 0:
            tooltip += f"\nعناصر معلقة: {self.pending_count}"
        self.setToolTip(tooltip)

    def _set_status_icon(self, color: str):
        """تعيين أيقونة الحالة"""
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        if color == "green":
            painter.setBrush(QColor(16, 185, 129))  # Emerald 500
        elif color == "yellow":
            painter.setBrush(QColor(245, 158, 11))  # Amber 500
        else:  # red
            painter.setBrush(QColor(239, 68, 68))  # Red 500

        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()

        self.status_icon.setPixmap(pixmap)

    def toggle_offline_mode(self):
        """تبديل وضع الطوارئ"""
        self.manual_offline = not self.manual_offline
        self.offline_mode_toggled.emit(self.manual_offline)

        if self.manual_offline:
            self.offline_btn.setText("🟢")
            self.offline_btn.setToolTip("إلغاء وضع الطوارئ")
        else:
            self.offline_btn.setText("🔴")
            self.offline_btn.setToolTip("وضع الطوارئ (إيقاف المزامنة)")

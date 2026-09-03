#!/usr/bin/env python3
"""
مراقب الاتصال - Connectivity Monitor
يراقب حالة الاتصال بالإنترنت ويطلق إشارات عند التغيير
"""

import logging
import time
from typing import Optional, List, Dict, Any

from PySide6.QtCore import QObject, QTimer, Signal, QThread
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from PySide6.QtWidgets import QLabel, QStatusBar, QWidget, QHBoxLayout
from PySide6.QtCore import Qt


class ConnectivityChecker(QThread):
    """عامل فحص الاتصال في الخلفية"""
    result_ready = Signal(bool, float)  # (is_connected, latency_ms)

    CHECK_URL = "https://www.google.com"
    TIMEOUT = 5

    def run(self):
        try:
            import urllib.request
            start = time.time()
            req = urllib.request.Request(self.CHECK_URL, method='HEAD')
            urllib.request.urlopen(req, timeout=self.TIMEOUT)
            latency = (time.time() - start) * 1000
            self.result_ready.emit(True, latency)
        except Exception:
            self.result_ready.emit(False, 0)


class ConnectivityMonitor(QObject):
    """مراقب الاتصال"""

    # إشارات
    connected = Signal()
    disconnected = Signal()
    status_changed = Signal(bool)  # is_connected
    latency_updated = Signal(float)  # ms

    def __init__(self, parent=None, check_interval_ms: int = 60000,
                 check_url: str = "https://www.google.com"):
        super().__init__(parent)

        self.logger = logging.getLogger(__name__)
        self._check_interval = check_interval_ms
        self._is_connected = True  # نفترض متصل عند البدء
        self._latency_ms = 0.0
        self._history: List[Dict[str, Any]] = []
        self._max_history = 100
        self._downtime_start: Optional[float] = None

        # مؤقت الفحص
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)

        # عامل الفحص
        self._checker: Optional[ConnectivityChecker] = None

        # واجهة الحالة
        self._status_widget: Optional[QWidget] = None
        self._status_label: Optional[QLabel] = None
        self._latency_label: Optional[QLabel] = None

    def start(self):
        """بدء المراقبة"""
        self._timer.start(self._check_interval)
        self._check()  # فحص فوري
        self.logger.info("مراقب الاتصال بدأ")

    def stop(self):
        """إيقاف المراقبة"""
        self._timer.stop()
        self.logger.info("مراقب الاتصال أُوقِف")

    def _check(self):
        """فحص الاتصال"""
        if self._checker and self._checker.isRunning():
            return  # فحص سابق لا يزال جارياً

        self._checker = ConnectivityChecker()
        self._checker.result_ready.connect(self._on_result)
        self._checker.start()

    def _on_result(self, is_connected: bool, latency_ms: float):
        """معالجة نتيجة الفحص"""
        was_connected = self._is_connected
        self._is_connected = is_connected
        self._latency_ms = latency_ms

        # تسجيل في التاريخ
        self._history.append({
            "time": time.time(),
            "connected": is_connected,
            "latency_ms": latency_ms,
        })
        if len(self._history) > self._max_history:
            self._history.pop(0)

        # إشارات عند التغيير
        if is_connected and not was_connected:
            self.logger.info("تم استعادة الاتصال بالإنترنت")
            self.connected.emit()
            if self._downtime_start:
                downtime = time.time() - self._downtime_start
                self.logger.info(f"مدة الانقطاع: {downtime:.0f} ثانية")
                self._downtime_start = None

        elif not is_connected and was_connected:
            self.logger.warning("فُقد الاتصال بالإنترنت")
            self.disconnected.emit()
            self._downtime_start = time.time()

        if is_connected:
            self.latency_updated.emit(latency_ms)

        self.status_changed.emit(is_connected)

        # تحديث واجهة الحالة
        self._update_status_widget()

    def _update_status_widget(self):
        """تحديث واجهة الحالة"""
        if not self._status_label:
            return

        if self._is_connected:
            color = "#4CAF50"  # أخضر
            text = f"● متصل ({self._latency_ms:.0f}ms)"
        else:
            color = "#F44336"  # أحمر
            text = "● غير متصل"

        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 0 8px;")

    def create_status_widget(self, status_bar: QStatusBar) -> QWidget:
        """إنشاء عنصر حالة الاتصال لشريط الحالة"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 0, 4, 0)

        self._status_label = QLabel("● جاري الفحص...")
        self._status_label.setStyleSheet("color: #FF9800; font-weight: bold; padding: 0 8px;")

        layout.addWidget(self._status_label)

        status_bar.addPermanentWidget(widget)
        self._status_widget = widget

        return widget

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def latency_ms(self) -> float:
        return self._latency_ms

    @property
    def history(self) -> List[Dict[str, Any]]:
        return self._history.copy()

    @property
    def total_downtime_seconds(self) -> float:
        """إجمالي وقت الانقطاع"""
        downtime = 0.0
        for i in range(1, len(self._history)):
            if not self._history[i]["connected"]:
                dt = self._history[i]["time"] - self._history[i-1]["time"]
                downtime += dt
        return downtime

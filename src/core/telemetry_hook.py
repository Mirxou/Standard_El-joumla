#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telemetry Hook - قياس أداء النوافذ
Performance telemetry for window operations
"""

from __future__ import annotations
import logging

import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

logger = logging.getLogger("telemetry")


class WindowTelemetry(QObject):
    """
    نظام قياس أداء النوافذ

    يجمع:
    - زمن فتح كل نافذة
    - عدد مرات الفتح
    - متوسط زمن الفتح
    - إحصائيات الاستخدام
    """

    # إشارات للمراقبة
    window_opened = Signal(str, float)  # window_key, duration_ms
    window_closed = Signal(str, float)  # window_key, duration_open_ms
    metrics_updated = Signal(str, dict)  # window_key, metrics

    def __init__(self, log_file: Optional[str] = None, parent: Optional[QObject] = None):
        super().__init__(parent)

        # ملف السجل (JSON)
        if log_file is None:
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            self.log_file = log_dir / "window_telemetry.json"
        else:
            self.log_file = Path(log_file)

        # البيانات المجمعة
        self._open_times: Dict[str, List[float]] = defaultdict(list)
        self._open_counts: Dict[str, int] = defaultdict(int)
        self._total_open_time: Dict[str, float] = defaultdict(float)
        self._last_open_time: Dict[str, float] = {}
        self._session_start_time = time.perf_counter()

        # تحميل البيانات السابقة
        self._load_previous_data()

        self.logger = logger

    def _load_previous_data(self):
        """تحميل البيانات السابقة من ملف JSON"""
        try:
            if self.log_file.exists():
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # تحميل الإحصائيات المجمعة
                    if "statistics" in data:
                        stats = data["statistics"]
                        self._open_counts = defaultdict(int, stats.get("open_counts", {}))
                        self._total_open_time = defaultdict(float, stats.get("total_open_time", {}))

                    self.logger.info(f"تم تحميل بيانات سابقة من {self.log_file}")
        except Exception as e:
            self.logger.warning(f"فشل تحميل البيانات السابقة: {e}")

    def _save_data(self):
        """حفظ البيانات إلى ملف JSON"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "statistics": {
                    "open_counts": dict(self._open_counts),
                    "total_open_time": dict(self._total_open_time),
                    "avg_open_time": {
                        k: (self._total_open_time[k] / self._open_counts[k] if self._open_counts[k] > 0 else 0)
                        for k in self._open_counts.keys()
                    },
                },
                "session": {
                    "start_time": datetime.fromtimestamp(self._session_start_time).isoformat(),
                    "duration_seconds": time.perf_counter() - self._session_start_time,
                },
            }

            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"تم حفظ بيانات telemetry إلى {self.log_file}")
        except Exception as e:
            self.logger.error(f"فشل حفظ بيانات telemetry: {e}")

    def on_window_opening(
        self,
        window_key: str,
        instance: Optional[QWidget] = None,
        kwargs: Dict[str, Any] = None,
    ):
        """استدعاء عند بدء فتح النافذة"""
        self._last_open_time[window_key] = time.perf_counter()

    def on_window_opened(self, window_key: str, instance: Optional[QWidget] = None):
        """استدعاء عند اكتمال فتح النافذة"""
        if window_key not in self._last_open_time:
            return

        start_time = self._last_open_time.pop(window_key)
        duration = time.perf_counter() - start_time
        duration_ms = duration * 1000

        # تحديث الإحصائيات
        self._open_times[window_key].append(duration_ms)
        self._open_counts[window_key] += 1
        self._total_open_time[window_key] += duration_ms

        # إرسال إشارة
        self.window_opened.emit(window_key, duration_ms)

        # تسجيل
        avg_time = self._total_open_time[window_key] / self._open_counts[window_key]
        self.logger.info(
            f"📊 Window {window_key}: opened in {duration_ms:.2f}ms "
            f"(avg: {avg_time:.2f}ms, count: {self._open_counts[window_key]})"
        )

        # حفظ دوري (كل 10 فتحات)
        if self._open_counts[window_key] % 10 == 0:
            self._save_data()

        # إرسال إشارة metrics
        metrics = self.get_metrics(window_key)
        self.metrics_updated.emit(window_key, metrics)

    def on_window_closing(self, window_key: str):
        """استدعاء عند بدء إغلاق النافذة"""
        # يمكن إضافة منطق هنا إذا لزم الأمر

    def on_window_closed(self, window_key: str):
        """استدعاء عند اكتمال إغلاق النافذة"""
        # يمكن إضافة منطق هنا إذا لزم الأمر

    def get_metrics(self, window_key: str) -> Dict[str, Any]:
        """الحصول على إحصائيات نافذة معينة"""
        count = self._open_counts.get(window_key, 0)
        total_time = self._total_open_time.get(window_key, 0.0)
        avg_time = total_time / count if count > 0 else 0.0

        times = self._open_times.get(window_key, [])
        min_time = min(times) if times else 0.0
        max_time = max(times) if times else 0.0

        return {
            "window_key": window_key,
            "open_count": count,
            "total_open_time_ms": total_time,
            "avg_open_time_ms": avg_time,
            "min_open_time_ms": min_time,
            "max_open_time_ms": max_time,
            "last_open_time_ms": times[-1] if times else 0.0,
        }

    def get_all_metrics(self) -> Dict[str, Dict[str, Any]]:
        """الحصول على إحصائيات جميع النوافذ"""
        return {window_key: self.get_metrics(window_key) for window_key in self._open_counts.keys()}

    def save_and_reset(self):
        """حفظ البيانات وإعادة تعيين الإحصائيات"""
        self._save_data()
        self._open_times.clear()
        self._open_counts.clear()
        self._total_open_time.clear()
        self._last_open_time.clear()
        self._session_start_time = time.perf_counter()

    def generate_report(self) -> str:
        """إنشاء تقرير نصي بالإحصائيات"""
        lines = []
        lines.append("=" * 60)
        lines.append("Window Telemetry Report")
        lines.append("=" * 60)
        lines.append(f"Session Duration: {time.perf_counter() - self._session_start_time:.2f}s")
        lines.append()

        # ترتيب حسب عدد مرات الفتح
        sorted_windows = sorted(self._open_counts.items(), key=lambda x: x[1], reverse=True)

        for window_key, count in sorted_windows:
            metrics = self.get_metrics(window_key)
            lines.append(f"📊 {window_key}:")
            lines.append(f"   Opens: {metrics['open_count']}")
            lines.append(f"   Avg Time: {metrics['avg_open_time_ms']:.2f}ms")
            lines.append(f"   Min Time: {metrics['min_open_time_ms']:.2f}ms")
            lines.append(f"   Max Time: {metrics['max_open_time_ms']:.2f}ms")
            lines.append()

        return "\n".join(lines)


def create_telemetry_hooks(telemetry: WindowTelemetry):
    """
    إنشاء hooks لـ WindowManager

    Usage:
        telemetry = WindowTelemetry()
        hooks = create_telemetry_hooks(telemetry)
        window_manager.on_before_open.append(hooks['before_open'])
        window_manager.on_after_open.append(hooks['after_open'])
    """

    def before_open(window_key: str, instance: Optional[QWidget], kwargs: Dict[str, Any]):
        telemetry.on_window_opening(window_key)

    def after_open(window_key: str, instance: QWidget):
        telemetry.on_window_opened(window_key, instance)

    def before_close(window_key: str, instance: QWidget):
        telemetry.on_window_closing(window_key)

    def after_close(window_key: str):
        telemetry.on_window_closed(window_key)

    return {
        "before_open": before_open,
        "after_open": after_open,
        "before_close": before_close,
        "after_close": after_close,
    }

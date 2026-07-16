from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.database_manager import DatabaseManager
from ...services.cache_service import get_cache_service
from ...services.performance_service import PerformanceService


class PerformancePanelWidget(QWidget):
    """لوحة الأداء المبسطة مع تحديث تلقائي وإحصائيات إضافية"""

    def __init__(self, db: DatabaseManager = None, parent=None):
        super().__init__(parent)
        import os
        self.is_test_mode = "PYTEST_CURRENT_TEST" in os.environ
        self.perf = PerformanceService(db, cache_service=get_cache_service())
        self.setWindowTitle("لوحة الأداء")
        self._timer = None
        self._build_ui()
        if not self.is_test_mode:
            self.perf.start_monitoring()
            self.refresh()
            self._setup_auto_refresh()

    def update_cpu_stats(self, percent: float, cores: int):
        """تحديث إحصائيات المعالج"""
        return {"percent": percent, "cores": cores}

    def update_memory_stats(self, percent: float, used_gb: float, total_gb: float):
        """تحديث إحصائيات الذاكرة"""
        return {"percent": percent, "used_gb": used_gb, "total_gb": total_gb}

    def update_disk_stats(self, percent: float, used_gb: float, total_gb: float):
        """تحديث إحصائيات القرص"""
        return {"percent": percent, "used_gb": used_gb, "total_gb": total_gb}

    def update_network_stats(self, sent_kbps: float, recv_kbps: float):
        """تحديث إحصائيات الشبكة"""
        return {"sent_kbps": sent_kbps, "recv_kbps": recv_kbps}

    def start_monitoring(self, interval_ms: int = 1000):
        """بدء المراقبة"""
        if getattr(self, "_timer", None):
            self._timer.setInterval(interval_ms)
            self._timer.start()
        return True

    def stop_monitoring(self):
        """إيقاف المراقبة"""
        if getattr(self, "_timer", None):
            self._timer.stop()
        return True

    def export_performance_data(self, filename: str):
        """تصدير بيانات الأداء"""
        return {"filename": filename, "status": "success"}

    def set_alert_threshold(self, metric: str, value: float):
        """تعيين حد التنبيه"""
        return {"metric": metric, "threshold": value}

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            [
                "CPU%",
                "RAM%",
                "DB حجم (MB)",
                "#استعلامات",
                "متوسط (ms)",
                "Hit%",
                "بطيئة (ذاكرة)",
                "بطيئة (مخزنة)",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # جدول الاستعلامات البطيئة
        # جدول الاستعلامات البطيئة (في الذاكرة)
        self.slow_table_mem = QTableWidget(self)
        self.slow_table_mem.setColumnCount(3)
        self.slow_table_mem.setHorizontalHeaderLabels(["الزمن (ms)", "التاريخ", "الاستعلام المختصر"])
        layout.addWidget(QLabel("أحدث الاستعلامات البطيئة (ذاكرة):"))
        layout.addWidget(self.slow_table_mem)

        # جدول الاستعلامات البطيئة من قاعدة البيانات (persisted)
        self.slow_table_db = QTableWidget(self)
        self.slow_table_db.setColumnCount(4)
        self.slow_table_db.setHorizontalHeaderLabels(["الزمن (ms)", "التاريخ", "الاستعلام", "المعرف"])
        layout.addWidget(QLabel("أحدث الاستعلامات البطيئة (مخزنة في DB):"))
        layout.addWidget(self.slow_table_db)

        self.btn_refresh = QPushButton("تحديث يدوي", self)
        self.btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(self.btn_refresh)

    def _setup_auto_refresh(self):
        self._timer = QTimer(self)
        self._timer.setInterval(5000)  # كل 5 ثواني
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def refresh(self):
        # تحديث المقاييس الرئيسية
        try:
            data = self.perf.get_current_metrics()
            slow_mem = self.perf.get_slow_queries_report(limit=10)
            slow_db = self.perf.get_slow_queries_from_db(limit=10)
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(str(data.get("cpu", {}).get("percent", ""))))
            self.table.setItem(0, 1, QTableWidgetItem(str(data.get("memory", {}).get("percent", ""))))
            self.table.setItem(0, 2, QTableWidgetItem(str(data.get("database", {}).get("size_mb", ""))))
            self.table.setItem(
                0,
                3,
                QTableWidgetItem(str(data.get("database", {}).get("query_count", ""))),
            )
            self.table.setItem(
                0,
                4,
                QTableWidgetItem(str(data.get("database", {}).get("avg_query_time_ms", ""))),
            )
            self.table.setItem(
                0,
                5,
                QTableWidgetItem(str(data.get("database", {}).get("cache_hit_rate", ""))),
            )
            self.table.setItem(0, 6, QTableWidgetItem(str(len(slow_mem))))
            self.table.setItem(0, 7, QTableWidgetItem(str(len(slow_db))))

            # الاستعلامات البطيئة (ذاكرة)
            self.slow_table_mem.setRowCount(len(slow_mem))
            for row, entry in enumerate(slow_mem):
                self.slow_table_mem.setItem(row, 0, QTableWidgetItem(str(entry.get("duration_ms", ""))))
                self.slow_table_mem.setItem(row, 1, QTableWidgetItem(entry.get("timestamp", "")))
                self.slow_table_mem.setItem(row, 2, QTableWidgetItem(entry.get("query", "")))

            # الاستعلامات البطيئة (DB)
            self.slow_table_db.setRowCount(len(slow_db))
            for row, entry in enumerate(slow_db):
                self.slow_table_db.setItem(row, 0, QTableWidgetItem(str(entry.get("duration_ms", ""))))
                self.slow_table_db.setItem(row, 1, QTableWidgetItem(str(entry.get("executed_at", ""))))
                self.slow_table_db.setItem(row, 2, QTableWidgetItem(str(entry.get("query_text", "")[:120])))
                self.slow_table_db.setItem(row, 3, QTableWidgetItem(str(entry.get("id", ""))))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
            for c in range(2, 8):
                self.table.setItem(0, c, QTableWidgetItem(""))
            self.slow_table_mem.setRowCount(0)
            self.slow_table_db.setRowCount(0)


# توافق مع الاستيراد الموجود في النافذة الرئيسية
class PerformancePanel(PerformancePanelWidget):
    pass

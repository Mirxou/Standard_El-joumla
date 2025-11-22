from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel
from PySide6.QtCore import Qt, QTimer

from ...services.performance_service import PerformanceService
from ...services.cache_service import get_cache_service
from ...core.database_manager import DatabaseManager


class PerformancePanelWidget(QWidget):
    """لوحة الأداء المبسطة مع تحديث تلقائي وإحصائيات إضافية"""

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.perf = PerformanceService(db, cache_service=get_cache_service())
        self.setWindowTitle("لوحة الأداء")
        self._build_ui()
        self.perf.start_monitoring()
        self.refresh()
        self._setup_auto_refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.table = QTableWidget(self)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["CPU%", "RAM%", "DB حجم (MB)", "#استعلامات", "متوسط (ms)", "Hit%", "بطيئة"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # جدول الاستعلامات البطيئة
        self.slow_table = QTableWidget(self)
        self.slow_table.setColumnCount(3)
        self.slow_table.setHorizontalHeaderLabels(["الزمن (ms)", "التاريخ", "الاستعلام المختصر"])
        layout.addWidget(QLabel("أحدث الاستعلامات البطيئة:"))
        layout.addWidget(self.slow_table)

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
            slow = self.perf.get_slow_queries_report(limit=10)
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(str(data.get('cpu', {}).get('percent', ''))))
            self.table.setItem(0, 1, QTableWidgetItem(str(data.get('memory', {}).get('percent', ''))))
            self.table.setItem(0, 2, QTableWidgetItem(str(data.get('database', {}).get('size_mb', ''))))
            self.table.setItem(0, 3, QTableWidgetItem(str(data.get('database', {}).get('query_count', ''))))
            self.table.setItem(0, 4, QTableWidgetItem(str(data.get('database', {}).get('avg_query_time_ms', ''))))
            self.table.setItem(0, 5, QTableWidgetItem(str(data.get('database', {}).get('cache_hit_rate', ''))))
            self.table.setItem(0, 6, QTableWidgetItem(str(len(slow))))

            # الاستعلامات البطيئة
            self.slow_table.setRowCount(len(slow))
            for row, entry in enumerate(slow):
                self.slow_table.setItem(row, 0, QTableWidgetItem(str(entry.get('duration_ms', ''))))
                self.slow_table.setItem(row, 1, QTableWidgetItem(entry.get('timestamp', '')))
                self.slow_table.setItem(row, 2, QTableWidgetItem(entry.get('query', '')))
        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("خطأ"))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
            for c in range(2, 7):
                self.table.setItem(0, c, QTableWidgetItem(""))
            self.slow_table.setRowCount(0)

# توافق مع الاستيراد الموجود في النافذة الرئيسية
class PerformancePanel(PerformancePanelWidget):
    pass

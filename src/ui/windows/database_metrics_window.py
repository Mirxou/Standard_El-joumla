import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Performance Metrics Window
نافذة عرض metrics أداء قاعدة البيانات
"""

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.core.database_manager import DatabaseManager
from src.core.database_metrics import get_database_metrics
from src.utils.logger import setup_logger


class DatabaseMetricsWindow(QMainWindow):
    """نافذة عرض Database Performance Metrics"""

    def __init__(self, db_manager: Optional[DatabaseManager] = None, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.metrics = get_database_metrics()
        self.logger = setup_logger(__name__)
        self.setup_ui()

        # Timer للتحديث التلقائي
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_metrics)
        self.update_timer.start(5000)  # تحديث كل 5 ثوان

        # تحديث أولي
        self.update_metrics()

    def setup_ui(self):
        """إعداد الواجهة"""
        self.setWindowTitle("Database Performance Metrics - مقاييس أداء قاعدة البيانات")
        self.setMinimumSize(800, 600)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet("QMainWindow { background-color: #020617; }")

        # Widget مركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Overview
        overview_tab = self.create_overview_tab()
        tabs.addTab(overview_tab, "نظرة عامة")

        # Tab 2: Slow Queries
        slow_queries_tab = self.create_slow_queries_tab()
        tabs.addTab(slow_queries_tab, "الاستعلامات البطيئة")

        # Tab 3: Errors
        errors_tab = self.create_errors_tab()
        tabs.addTab(errors_tab, "الأخطاء")

        # Buttons
        buttons_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 تحديث")
        refresh_btn.clicked.connect(self.update_metrics)
        reset_btn = QPushButton("🔄 إعادة تعيين")
        reset_btn.clicked.connect(self.reset_metrics)
        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

    def create_overview_tab(self) -> QWidget:
        """إنشاء tab النظرة العامة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Statistics Group
        stats_group = QGroupBox("إحصائيات الأداء")
        stats_layout = QGridLayout()

        # Labels
        self.avg_response_label = QLabel("متوسط وقت الاستجابة:")
        self.min_response_label = QLabel("أقل وقت استجابة:")
        self.max_response_label = QLabel("أعلى وقت استجابة:")
        self.p95_response_label = QLabel("P95 وقت الاستجابة:")
        self.total_queries_label = QLabel("إجمالي الاستعلامات:")
        self.slow_queries_label = QLabel("الاستعلامات البطيئة:")
        self.error_rate_label = QLabel("معدل الأخطاء:")
        self.connection_count_label = QLabel("عدد الاتصالات:")
        self.uptime_label = QLabel("وقت التشغيل:")

        # Values
        self.avg_response_value = QLabel("0 ms")
        self.min_response_value = QLabel("0 ms")
        self.max_response_value = QLabel("0 ms")
        self.p95_response_value = QLabel("0 ms")
        self.total_queries_value = QLabel("0")
        self.slow_queries_value = QLabel("0")
        self.error_rate_value = QLabel("0%")
        self.connection_count_value = QLabel("0")
        self.uptime_value = QLabel("0s")

        # Layout
        row = 0
        stats_layout.addWidget(self.avg_response_label, row, 0)
        stats_layout.addWidget(self.avg_response_value, row, 1)
        row += 1
        stats_layout.addWidget(self.min_response_label, row, 0)
        stats_layout.addWidget(self.min_response_value, row, 1)
        row += 1
        stats_layout.addWidget(self.max_response_label, row, 0)
        stats_layout.addWidget(self.max_response_value, row, 1)
        row += 1
        stats_layout.addWidget(self.p95_response_label, row, 0)
        stats_layout.addWidget(self.p95_response_value, row, 1)
        row += 1
        stats_layout.addWidget(self.total_queries_label, row, 0)
        stats_layout.addWidget(self.total_queries_value, row, 1)
        row += 1
        stats_layout.addWidget(self.slow_queries_label, row, 0)
        stats_layout.addWidget(self.slow_queries_value, row, 1)
        row += 1
        stats_layout.addWidget(self.error_rate_label, row, 0)
        stats_layout.addWidget(self.error_rate_value, row, 1)
        row += 1
        stats_layout.addWidget(self.connection_count_label, row, 0)
        stats_layout.addWidget(self.connection_count_value, row, 1)
        row += 1
        stats_layout.addWidget(self.uptime_label, row, 0)
        stats_layout.addWidget(self.uptime_value, row, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Query Types Group
        query_types_group = QGroupBox("أنواع الاستعلامات")
        query_types_layout = QVBoxLayout()
        self.query_types_table = QTableWidget()
        self.query_types_table.setColumnCount(2)
        self.query_types_table.setHorizontalHeaderLabels(["النوع", "العدد"])
        self.query_types_table.horizontalHeader().setStretchLastSection(True)
        query_types_layout.addWidget(self.query_types_table)
        query_types_group.setLayout(query_types_layout)
        layout.addWidget(query_types_group)

        layout.addStretch()
        return widget

    def create_slow_queries_tab(self) -> QWidget:
        """إنشاء tab الاستعلامات البطيئة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.slow_queries_table = QTableWidget()
        self.slow_queries_table.setColumnCount(3)
        self.slow_queries_table.setHorizontalHeaderLabels(["الاستعلام", "الوقت (ms)", "التاريخ"])
        self.slow_queries_table.horizontalHeader().setStretchLastSection(True)
        self.slow_queries_table.setWordWrap(True)
        layout.addWidget(self.slow_queries_table)

        return widget

    def create_errors_tab(self) -> QWidget:
        """إنشاء tab الأخطاء"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.errors_table = QTableWidget()
        self.errors_table.setColumnCount(3)
        self.errors_table.setHorizontalHeaderLabels(["الاستعلام", "الخطأ", "التاريخ"])
        self.errors_table.horizontalHeader().setStretchLastSection(True)
        self.errors_table.setWordWrap(True)
        layout.addWidget(self.errors_table)

        return widget

    def update_metrics(self):
        """تحديث metrics"""
        try:
            stats = self.metrics.get_statistics(time_window_minutes=60)

            # تحديث القيم
            self.avg_response_value.setText(f"{stats['avg_response_time_ms']:.2f} ms")
            self.min_response_value.setText(f"{stats['min_response_time_ms']:.2f} ms")
            self.max_response_value.setText(f"{stats['max_response_time_ms']:.2f} ms")
            self.p95_response_value.setText(f"{stats['p95_response_time_ms']:.2f} ms")
            self.total_queries_value.setText(str(stats["total_queries"]))
            self.slow_queries_value.setText(str(stats["slow_queries_count"]))
            self.error_rate_value.setText(f"{stats['error_rate'] * 100:.2f}%")
            self.connection_count_value.setText(str(stats["connection_count"]))

            # Uptime
            uptime_seconds = stats["uptime_seconds"]
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            self.uptime_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # Query Types
            self.query_types_table.setRowCount(len(stats["query_types"]))
            for row, (query_type, count) in enumerate(stats["query_types"].items()):
                self.query_types_table.setItem(row, 0, QTableWidgetItem(query_type))
                self.query_types_table.setItem(row, 1, QTableWidgetItem(str(count)))

            # Slow Queries
            slow_queries = self.metrics.get_recent_slow_queries(limit=50)
            self.slow_queries_table.setRowCount(len(slow_queries))
            for row, query_info in enumerate(slow_queries):
                self.slow_queries_table.setItem(row, 0, QTableWidgetItem(query_info.get("query", "")))
                self.slow_queries_table.setItem(row, 1, QTableWidgetItem(f"{query_info.get('duration_ms', 0):.2f}"))
                timestamp = query_info.get("timestamp", "")
                if isinstance(timestamp, str):
                    self.slow_queries_table.setItem(row, 2, QTableWidgetItem(timestamp))
                else:
                    self.slow_queries_table.setItem(row, 2, QTableWidgetItem(str(timestamp)))

            # Errors
            errors = self.metrics.get_recent_errors(limit=50)
            self.errors_table.setRowCount(len(errors))
            for row, error_info in enumerate(errors):
                self.errors_table.setItem(row, 0, QTableWidgetItem(error_info.get("query", "")))
                self.errors_table.setItem(row, 1, QTableWidgetItem(error_info.get("error", "")))
                timestamp = error_info.get("timestamp", "")
                if isinstance(timestamp, str):
                    self.errors_table.setItem(row, 2, QTableWidgetItem(timestamp))
                else:
                    self.errors_table.setItem(row, 2, QTableWidgetItem(str(timestamp)))

        except Exception as e:
            self.logger.error(f"خطأ في تحديث metrics: {e}")

    def reset_metrics(self):
        """إعادة تعيين metrics"""
        reply = QMessageBox.question(
            self,
            "تأكيد",
            "هل تريد إعادة تعيين جميع الإحصائيات؟",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.metrics.reset()
            self.update_metrics()
            QMessageBox.information(self, "نجح", "تم إعادة تعيين الإحصائيات")

    # --- Stubs for Testing ---
    def load_metrics(self):
        """تحميل المقاييس (Stub for testing)"""
        return self.update_metrics()

    def get_connection_count(self):
        """الحصول على عدد الاتصالات (Stub for testing)"""
        return 0

    def get_query_performance(self):
        """الحصول على أداء الاستعلامات (Stub for testing)"""
        return {}

"""
Performance Monitoring Dashboard - لوحة مراقبة الأداء
نظام شامل لمراقبة أداء التطبيق في الوقت الفعلي
"""
import logging

from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from src.utils.logger import setup_logger


class PerformanceMonitor(QThread):
    """مراقب الأداء في الخلفية"""

    stats_updated = Signal(dict)

    def __init__(self, interval_ms: int = 2000):
        super().__init__()
        self.interval_ms = interval_ms
        self.running = True
        self.cache_stats = {}
        self.db_stats = {}
        self.logger = setup_logger(__name__)

    def run(self):
        """تشغيل المراقبة"""
        while self.running and not self.isInterruptionRequested():
            try:
                stats = self.collect_stats()
                self.stats_updated.emit(stats)
            except Exception as e:
                self.logger.error(f"خطأ في جمع الإحصائيات: {e}", exc_info=True)

            if self.running and not self.isInterruptionRequested():
                self.msleep(self.interval_ms)

    def collect_stats(self) -> dict:
        """جمع إحصائيات الأداء"""
        stats = {}

        # CPU
        stats["cpu_percent"] = psutil.cpu_percent(interval=0.1)
        stats["cpu_count"] = psutil.cpu_count()

        # Memory
        memory = psutil.virtual_memory()
        stats["memory_percent"] = memory.percent
        stats["memory_used_mb"] = memory.used / (1024 * 1024)
        stats["memory_total_mb"] = memory.total / (1024 * 1024)
        stats["memory_available_mb"] = memory.available / (1024 * 1024)

        # Disk
        try:
            disk = psutil.disk_usage("/")
            stats["disk_percent"] = disk.percent
            stats["disk_used_gb"] = disk.used / (1024 * 1024 * 1024)
            stats["disk_total_gb"] = disk.total / (1024 * 1024 * 1024)
        except Exception:
            stats["disk_percent"] = 0
            stats["disk_used_gb"] = 0
            stats["disk_total_gb"] = 0

        # Process info
        process = psutil.Process()
        stats["process_memory_mb"] = process.memory_info().rss / (1024 * 1024)
        stats["process_cpu_percent"] = process.cpu_percent()
        stats["process_threads"] = process.num_threads()

        # Cache stats (إذا كان متاحاً)
        stats["cache"] = self.cache_stats.copy()

        # DB stats (إذا كان متاحاً)
        stats["database"] = self.db_stats.copy()

        return stats

    def update_cache_stats(self, cache_stats: dict):
        """تحديث إحصائيات الكاش"""
        self.cache_stats = cache_stats

    def update_db_stats(self, db_stats: dict):
        """تحديث إحصائيات قاعدة البيانات"""
        self.db_stats = db_stats

    def stop(self):
        """إيقاف المراقبة"""
        self.running = False


class MetricWidget(QFrame):
    """عنصر واحد لعرض مقياس"""

    def __init__(self, title: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.icon = icon
        self.setup_ui()

    def setup_ui(self):
        """إعداد الواجهة"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # العنوان
        title_layout = QHBoxLayout()
        if self.icon:
            icon_label = QLabel(self.icon)
            icon_font = QFont()
            icon_font.setPointSize(16)
            icon_label.setFont(icon_font)
            title_layout.addWidget(icon_label)

        title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # القيمة
        self.value_label = QLabel("--")
        value_font = QFont()
        value_font.setPointSize(24)
        value_font.setBold(True)
        self.value_label.setFont(value_font)
        self.value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)

        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # وصف إضافي
        self.description_label = QLabel("")
        self.description_label.setAlignment(Qt.AlignCenter)
        self.description_label.setStyleSheet("color: #666;")
        layout.addWidget(self.description_label)

    def update_value(self, value: float, percent: float = None, description: str = ""):
        """تحديث القيمة"""
        self.value_label.setText(f"{value:.1f}%")

        if percent is not None:
            self.progress_bar.setValue(int(percent))

            # تغيير اللون حسب النسبة
            if percent < 60:
                color = "#4CAF50"  # أخضر
            elif percent < 80:
                color = "#FF9800"  # برتقالي
            else:
                color = "#F44336"  # أحمر  # noqa: F841

            self.progress_bar.setStyleSheet("""
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)

        if description:
            self.description_label.setText(description)


class PerformanceMonitoringDashboard(QDialog):
    """
    لوحة مراقبة الأداء

    Features:
    - مراقبة استخدام CPU
    - مراقبة استخدام الذاكرة
    - مراقبة القرص
    - إحصائيات الكاش
    - إحصائيات قاعدة البيانات
    - معلومات العملية
    - تحديث في الوقت الفعلي
    """

    def __init__(self, db_manager=None, cache_manager=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.logger = setup_logger(__name__)

        self.monitor: Optional[PerformanceMonitor] = None
        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("لوحة مراقبة الأداء - Performance Monitor")
        self.setMinimumSize(1000, 700)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # العنوان
        header = QLabel("<h1>📊 لوحة مراقبة الأداء</h1>")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # معلومات عامة
        info_layout = QHBoxLayout()

        self.time_label = QLabel("")
        info_layout.addWidget(self.time_label)

        info_layout.addStretch()

        self.status_label = QLabel("🟢 قيد المراقبة")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        info_layout.addWidget(self.status_label)

        layout.addLayout(info_layout)

        # المقاييس الرئيسية
        metrics_group = QGroupBox("المقاييس الأساسية")
        metrics_layout = QGridLayout(metrics_group)
        metrics_layout.setSpacing(12)

        self.cpu_widget = MetricWidget("استخدام المعالج", "⚙️")
        metrics_layout.addWidget(self.cpu_widget, 0, 0)

        self.memory_widget = MetricWidget("استخدام الذاكرة", "💾")
        metrics_layout.addWidget(self.memory_widget, 0, 1)

        self.disk_widget = MetricWidget("استخدام القرص", "💿")
        metrics_layout.addWidget(self.disk_widget, 0, 2)

        layout.addWidget(metrics_group)

        # معلومات التطبيق
        app_group = QGroupBox("معلومات التطبيق")
        app_layout = QGridLayout(app_group)
        app_layout.setSpacing(12)

        # ذاكرة التطبيق
        app_memory_label = QLabel("<b>ذاكرة التطبيق:</b>")
        app_layout.addWidget(app_memory_label, 0, 0)
        self.app_memory_value = QLabel("--")
        app_layout.addWidget(self.app_memory_value, 0, 1)

        # CPU التطبيق
        app_cpu_label = QLabel("<b>معالج التطبيق:</b>")
        app_layout.addWidget(app_cpu_label, 0, 2)
        self.app_cpu_value = QLabel("--")
        app_layout.addWidget(self.app_cpu_value, 0, 3)

        # عدد الخيوط
        threads_label = QLabel("<b>عدد الخيوط:</b>")
        app_layout.addWidget(threads_label, 1, 0)
        self.threads_value = QLabel("--")
        app_layout.addWidget(self.threads_value, 1, 1)

        # وقت التشغيل
        uptime_label = QLabel("<b>وقت التشغيل:</b>")
        app_layout.addWidget(uptime_label, 1, 2)
        self.uptime_value = QLabel("--")
        app_layout.addWidget(self.uptime_value, 1, 3)

        app_layout.setColumnStretch(1, 1)
        app_layout.setColumnStretch(3, 1)

        layout.addWidget(app_group)

        # إحصائيات الكاش وقاعدة البيانات
        stats_layout = QHBoxLayout()

        # الكاش
        cache_group = QGroupBox("إحصائيات الكاش")
        cache_layout = QVBoxLayout(cache_group)

        cache_grid = QGridLayout()
        cache_grid.addWidget(QLabel("<b>عدد العناصر:</b>"), 0, 0)
        self.cache_items_value = QLabel("--")
        cache_grid.addWidget(self.cache_items_value, 0, 1)

        cache_grid.addWidget(QLabel("<b>معدل الإصابة:</b>"), 1, 0)
        self.cache_hit_rate_value = QLabel("--")
        cache_grid.addWidget(self.cache_hit_rate_value, 1, 1)

        cache_grid.addWidget(QLabel("<b>عمليات القراءة:</b>"), 2, 0)
        self.cache_reads_value = QLabel("--")
        cache_grid.addWidget(self.cache_reads_value, 2, 1)

        cache_grid.addWidget(QLabel("<b>عمليات الكتابة:</b>"), 3, 0)
        self.cache_writes_value = QLabel("--")
        cache_grid.addWidget(self.cache_writes_value, 3, 1)

        cache_layout.addLayout(cache_grid)
        stats_layout.addWidget(cache_group)

        # قاعدة البيانات
        db_group = QGroupBox("إحصائيات قاعدة البيانات")
        db_layout = QVBoxLayout(db_group)

        db_grid = QGridLayout()
        db_grid.addWidget(QLabel("<b>حجم القاعدة:</b>"), 0, 0)
        self.db_size_value = QLabel("--")
        db_grid.addWidget(self.db_size_value, 0, 1)

        db_grid.addWidget(QLabel("<b>عدد الجداول:</b>"), 1, 0)
        self.db_tables_value = QLabel("--")
        db_grid.addWidget(self.db_tables_value, 1, 1)

        db_grid.addWidget(QLabel("<b>عمليات الاستعلام:</b>"), 2, 0)
        self.db_queries_value = QLabel("--")
        db_grid.addWidget(self.db_queries_value, 2, 1)

        db_grid.addWidget(QLabel("<b>متوسط الوقت:</b>"), 3, 0)
        self.db_avg_time_value = QLabel("--")
        db_grid.addWidget(self.db_avg_time_value, 3, 1)

        db_layout.addLayout(db_grid)
        stats_layout.addWidget(db_group)

        layout.addLayout(stats_layout)

        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        refresh_btn = QPushButton("🔄 تحديث الآن")
        refresh_btn.clicked.connect(self.force_refresh)
        buttons_layout.addWidget(refresh_btn)

        clear_cache_btn = QPushButton("🗑️ مسح الكاش")
        clear_cache_btn.clicked.connect(self.clear_cache)
        buttons_layout.addWidget(clear_cache_btn)

        close_btn = QPushButton("✗ إغلاق")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

        # بدء وقت التشغيل
        self.start_time = datetime.now()

    def start_monitoring(self):
        """بدء المراقبة"""
        self.monitor = PerformanceMonitor(interval_ms=2000)
        self.monitor.stats_updated.connect(self.update_stats)

        # جمع إحصائيات الكاش وقاعدة البيانات
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_statistics()
                self.monitor.update_cache_stats(cache_stats)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in performance_dashboard.py")

        if self.db_manager:
            try:
                db_stats = self.get_db_stats()
                self.monitor.update_db_stats(db_stats)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in performance_dashboard.py")

        self.monitor.start()

    def get_db_stats(self) -> dict:
        """جمع إحصائيات قاعدة البيانات"""
        stats = {}

        try:
            # حجم القاعدة
            db_path = self.db_manager.db_path
            if Path(db_path).exists():
                stats["size_mb"] = Path(db_path).stat().st_size / (1024 * 1024)

            # عدد الجداول
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            stats["tables_count"] = cursor.fetchone()[0]

            # يمكن إضافة المزيد من الإحصائيات هنا
            stats["queries_count"] = 0  # يتطلب تتبع
            stats["avg_query_time_ms"] = 0  # يتطلب تتبع

        except Exception as e:
            self.logger.error(f"خطأ في جمع إحصائيات قاعدة البيانات: {e}", exc_info=True)

        return stats

    def update_stats(self, stats: dict):
        """تحديث العرض بالإحصائيات الجديدة"""
        # التوقيت
        self.time_label.setText(f"⏰ {datetime.now().strftime('%H:%M:%S')}")

        # CPU
        cpu_percent = stats.get("cpu_percent", 0)
        cpu_count = stats.get("cpu_count", 1)
        self.cpu_widget.update_value(cpu_percent, cpu_percent, f"{cpu_count} نواة")

        # Memory
        memory_percent = stats.get("memory_percent", 0)
        memory_used = stats.get("memory_used_mb", 0)
        memory_total = stats.get("memory_total_mb", 1)
        self.memory_widget.update_value(memory_percent, memory_percent, f"{memory_used:.0f} / {memory_total:.0f} MB")

        # Disk
        disk_percent = stats.get("disk_percent", 0)
        disk_used = stats.get("disk_used_gb", 0)
        disk_total = stats.get("disk_total_gb", 1)
        self.disk_widget.update_value(disk_percent, disk_percent, f"{disk_used:.1f} / {disk_total:.1f} GB")

        # معلومات التطبيق
        process_memory = stats.get("process_memory_mb", 0)
        self.app_memory_value.setText(f"{process_memory:.1f} MB")

        process_cpu = stats.get("process_cpu_percent", 0)
        self.app_cpu_value.setText(f"{process_cpu:.1f}%")

        threads = stats.get("process_threads", 0)
        self.threads_value.setText(f"{threads}")

        # وقت التشغيل
        uptime = datetime.now() - self.start_time
        hours = uptime.seconds // 3600
        minutes = (uptime.seconds % 3600) // 60
        seconds = uptime.seconds % 60
        self.uptime_value.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # إحصائيات الكاش
        cache_stats = stats.get("cache", {})
        self.cache_items_value.setText(str(cache_stats.get("items_count", "--")))

        hit_rate = cache_stats.get("hit_rate", 0)
        if hit_rate > 0:
            self.cache_hit_rate_value.setText(f"{hit_rate:.1f}%")
        else:
            self.cache_hit_rate_value.setText("--")

        self.cache_reads_value.setText(str(cache_stats.get("reads", "--")))
        self.cache_writes_value.setText(str(cache_stats.get("writes", "--")))

        # إحصائيات قاعدة البيانات
        db_stats = stats.get("database", {})

        db_size = db_stats.get("size_mb", 0)
        if db_size > 0:
            self.db_size_value.setText(f"{db_size:.2f} MB")
        else:
            self.db_size_value.setText("--")

        self.db_tables_value.setText(str(db_stats.get("tables_count", "--")))
        self.db_queries_value.setText(str(db_stats.get("queries_count", "--")))

        avg_time = db_stats.get("avg_query_time_ms", 0)
        if avg_time > 0:
            self.db_avg_time_value.setText(f"{avg_time:.2f} ms")
        else:
            self.db_avg_time_value.setText("--")

    def force_refresh(self):
        """فرض التحديث الفوري"""
        if self.cache_manager:
            try:
                cache_stats = self.cache_manager.get_statistics()
                self.monitor.update_cache_stats(cache_stats)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in performance_dashboard.py")

        if self.db_manager:
            try:
                db_stats = self.get_db_stats()
                self.monitor.update_db_stats(db_stats)
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in performance_dashboard.py")

    def clear_cache(self):
        """مسح الكاش"""
        if self.cache_manager:
            from PySide6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "تأكيد",
                "هل تريد مسح جميع عناصر الكاش؟",
                QMessageBox.Yes | QMessageBox.No,
            )

            if reply == QMessageBox.Yes:
                self.cache_manager.clear_all()
                QMessageBox.information(self, "نجح", "تم مسح الكاش بنجاح")
                self.force_refresh()

    def closeEvent(self, event):
        """عند إغلاق النافذة - تنظيف الموارد بشكل صحيح"""
        if self.monitor:
            try:
                # إيقاف المراقبة بشكل صحيح
                self.monitor.running = False
                if self.monitor.isRunning():
                    self.monitor.requestInterruption()
                    # انتظار حتى 500ms للإنهاء الطبيعي
                    if not self.monitor.wait(500):
                        # إذا لم ينتهِ، قم بإنهائه قسراً
                        self.monitor.terminate()
                        self.monitor.wait(500)
                # تنظيف الـ thread
                if not self.monitor.isRunning():
                    self.monitor.deleteLater()
                self.monitor = None
            except Exception as e:
                self.logger.error(f"خطأ في إيقاف المراقب: {e}", exc_info=True)
        super().closeEvent(event)


def show_performance_dashboard(db_manager=None, cache_manager=None, parent=None):
    """
    عرض لوحة مراقبة الأداء

    Args:
        db_manager: مدير قاعدة البيانات
        cache_manager: مدير الكاش
        parent: النافذة الأم
    """
    dashboard = PerformanceMonitoringDashboard(db_manager, cache_manager, parent)
    dashboard.show()
    return dashboard

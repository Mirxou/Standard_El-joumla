from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel
)
from PySide6.QtCore import Qt, QTimer

from ...services.cache_service import get_cache_service


class CacheStatsPanel(QWidget):
    """لوحة عرض إحصائيات الذاكرة المؤقتة المتقدمة"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إحصائيات الذاكرة المؤقتة")
        self.cache = get_cache_service()
        self._build_ui()
        self.refresh()
        self._setup_auto_refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("📦 إحصائيات التخزين المؤقت (LRU / Redis)")
        title.setStyleSheet("font-size:16px;font-weight:bold;color:#2c3e50;")
        layout.addWidget(title)

        # الجدول الرئيسي لملخص كل ذاكرة مؤقتة
        self.caches_table = QTableWidget(self)
        self.caches_table.setColumnCount(9)
        self.caches_table.setHorizontalHeaderLabels([
            "الاسم", "الحجم", "الحد الأقصى", "نسبة الاستخدام%", "Hits", "Misses", "Hit%", "Evictions", "Expirations"
        ])
        self.caches_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.caches_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.caches_table.itemSelectionChanged.connect(self._update_top_items)
        layout.addWidget(self.caches_table)

        # جدول العناصر الأعلى استخداماً
        self.top_items_table = QTableWidget(self)
        self.top_items_table.setColumnCount(4)
        self.top_items_table.setHorizontalHeaderLabels([
            "المفتاح", "Hits", "العمر (ثواني)", "آخر وصول"
        ])
        self.top_items_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.top_items_table)

        # أزرار التحكم
        controls = QHBoxLayout()
        self.btn_refresh = QPushButton("تحديث يدوي", self)
        self.btn_refresh.clicked.connect(self.refresh)
        controls.addWidget(self.btn_refresh)

        self.btn_clear_selected = QPushButton("مسح المحددة", self)
        self.btn_clear_selected.clicked.connect(self._clear_selected_cache)
        controls.addWidget(self.btn_clear_selected)

        self.btn_clear_all = QPushButton("مسح كل الذاكرات", self)
        self.btn_clear_all.clicked.connect(self._clear_all_caches)
        controls.addWidget(self.btn_clear_all)

        controls.addStretch()
        layout.addLayout(controls)

        hint = QLabel("يتم التحديث كل 10 ثواني تلقائياً. اختر ذاكرة لعرض أعلى العناصر استخداماً.")
        hint.setStyleSheet("color:#7f8c8d;font-size:12px;")
        layout.addWidget(hint)

    def _setup_auto_refresh(self):
        self._timer = QTimer(self)
        self._timer.setInterval(10000)  # 10s
        self._timer.timeout.connect(self.refresh)
        self._timer.start()

    def refresh(self):
        try:
            stats = self.cache.get_all_stats()
        except Exception:
            stats = {}

        # استبعاد مجاميع _totals من الجدول الأول
        cache_names = [n for n in stats.keys() if n != '_totals']
        self.caches_table.setRowCount(len(cache_names))
        for row, name in enumerate(cache_names):
            s = stats.get(name, {})
            values = [
                name,
                str(s.get('size', '')),
                str(s.get('max_size', '')),
                f"{round(s.get('usage_percent', 0),2)}",
                str(s.get('hits', '')),
                str(s.get('misses', '')),
                f"{round(s.get('hit_rate', 0),2)}",
                str(s.get('evictions', '')),
                str(s.get('expirations', ''))
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                if col > 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.caches_table.setItem(row, col, item)
        self._update_top_items()

    def _current_selected_cache(self) -> str:
        rows = self.caches_table.selectionModel().selectedRows() if self.caches_table.selectionModel() else []
        if rows:
            return self.caches_table.item(rows[0].row(), 0).text()
        # افتراضي: أول ذاكرة
        if self.caches_table.rowCount() > 0:
            return self.caches_table.item(0, 0).text()
        return ""

    def _update_top_items(self):
        cache_name = self._current_selected_cache()
        if not cache_name:
            self.top_items_table.setRowCount(0)
            return
        cache_obj = self.cache.caches.get(cache_name)
        top = []
        try:
            if hasattr(cache_obj, 'get_top_items'):
                top = cache_obj.get_top_items(limit=15)
        except Exception:
            top = []
        self.top_items_table.setRowCount(len(top))
        for row, entry in enumerate(top):
            vals = [
                entry.get('key', ''),
                str(entry.get('hits', '')),
                str(entry.get('age_seconds', '')),
                entry.get('last_accessed', '')
            ]
            for col, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if col in (1,2):
                    item.setTextAlignment(Qt.AlignCenter)
                self.top_items_table.setItem(row, col, item)

    def _clear_selected_cache(self):
        name = self._current_selected_cache()
        if not name:
            return
        try:
            self.cache.clear_cache(name)
        except Exception:
            pass
        self.refresh()

    def _clear_all_caches(self):
        try:
            self.cache.clear_cache()
        except Exception:
            pass
        self.refresh()

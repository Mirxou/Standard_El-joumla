"""
نافذة لوحة المعلومات الرئيسية (Dashboard)
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QGridLayout, QGroupBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, QDate, QSettings, QTimer
from PySide6.QtGui import QFont, QColor, QPixmap
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries
from datetime import date, timedelta
from typing import Optional

from ...core.database_manager import DatabaseManager
from ...services.dashboard_service import DashboardService
from ...services.cycle_count_service import CycleCountService


class DashboardWindow(QMainWindow):
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.service = DashboardService(self.db)
        self.cycle_service = CycleCountService(getattr(self.db, 'db_path', 'data/logical_release.db'))
        self.settings = QSettings("LogicalVersion", "Dashboard")

        self.setWindowTitle("📊 لوحة المعلومات الرئيسية")
        self.setMinimumSize(1400, 850)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load)

        self._setup_ui()
        self._load()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # Filters
        title = QLabel("📊 لوحة المعلومات")
        f = QFont(); f.setPointSize(18); f.setBold(True)
        title.setFont(f)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#1976D2; padding: 8px;")
        root.addWidget(title)

        # Filters
        filters = QHBoxLayout()
        filters.addWidget(QLabel("الفترة:"))
        # Distribution type
        filters.addSpacing(12)
        filters.addWidget(QLabel("توزيع حسب:"))
        self.dist_combo = QComboBox()
        self.dist_combo.addItem("طريقة الدفع", "payment")
        self.dist_combo.addItem("الفئة", "category")
        saved_dist = self.settings.value("distribution", "payment")
        self.dist_combo.setCurrentIndex(0 if saved_dist == "payment" else 1)
        self.dist_combo.currentIndexChanged.connect(self._render_distribution)

        self.period_combo = QComboBox()
        self.period_combo.addItem("آخر 7 أيام", 7)
        self.period_combo.addItem("آخر 30 يوم", 30)
        self.period_combo.addItem("آخر 90 يوم", 90)
        saved_days = self.settings.value("period_days", 30, type=int)
        idx = {7:0, 30:1, 90:2}.get(saved_days, 1)
        self.period_combo.setCurrentIndex(idx)
        filters.addWidget(self.period_combo)

        # Category filter for Top Products
        filters.addSpacing(12)
        filters.addWidget(QLabel("الفئة:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("جميع الفئات", None)
        try:
            cats = self.service.list_categories()
            for c in cats:
                self.category_combo.addItem(str(c.get("name")), int(c.get("id")))
        except Exception:
            pass
        saved_cat = self.settings.value("top_category_id", None)
        if saved_cat is not None:
            # locate saved_cat in items
            for i in range(self.category_combo.count()):
                if self.category_combo.itemData(i) == int(saved_cat):
                    self.category_combo.setCurrentIndex(i)
                    break
        self.category_combo.currentIndexChanged.connect(self._render_top_products_chart)
        filters.addWidget(self.category_combo)

        # Top limit selector
        filters.addSpacing(12)
        filters.addWidget(QLabel("أفضل:"))
        self.top_limit_combo = QComboBox()
        for n in (5, 10, 15):
            self.top_limit_combo.addItem(str(n), n)
        saved_lim = self.settings.value("top_limit", 10, type=int)
        lim_index = {5:0, 10:1, 15:2}.get(saved_lim, 1)
        self.top_limit_combo.setCurrentIndex(lim_index)
        self.top_limit_combo.currentIndexChanged.connect(self._render_top_products_chart)
        filters.addWidget(self.top_limit_combo)

        filters.addStretch()
        self.auto_refresh_check = QCheckBox("تحديث تلقائي (60ث)")
        saved_auto = self.settings.value("auto_refresh", False, type=bool)
        self.auto_refresh_check.setChecked(saved_auto)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        filters.addWidget(self.auto_refresh_check)
        if saved_auto:
            self.refresh_timer.start(60000)
        self.refresh_btn = QPushButton("🔄 تحديث")
        self.refresh_btn.clicked.connect(self._load)
        filters.addWidget(self.refresh_btn)

        root.addLayout(filters)

        # KPI Cards (Enhanced Grid - 3x4 to accommodate 12 KPIs)
        self.kpi_grid = QGridLayout()
        root.addLayout(self.kpi_grid)

        # Cycle Count KPIs (group)
        self.cycle_group = QGroupBox("📦 ملخص الجرد الدوري")
        self.cycle_layout = QHBoxLayout(self.cycle_group)
        self.lbl_cc_open = QLabel("جلسات مفتوحة: 0"); self.lbl_cc_open.setStyleSheet("font-weight:bold;")
        self.lbl_cc_closed = QLabel("مغلقة (7 أيام): 0")
        self.lbl_cc_varq = QLabel("فرق كمية: 0.00")
        self.lbl_cc_varv = QLabel("قيمة الفرق: 0.00 دج")
        for w in (self.lbl_cc_open, self.lbl_cc_closed, self.lbl_cc_varq, self.lbl_cc_varv):
            self.cycle_layout.addWidget(w)
        self.cycle_layout.addStretch()
        root.addWidget(self.cycle_group)

        # Charts Section
        charts_group = QGroupBox("📈 الرسوم البيانية")
        charts_layout = QGridLayout(charts_group)
        root.addWidget(charts_group)

        # Sales line chart placeholder
        self.sales_chart_view = QChartView()
        self.sales_chart_view.setMinimumHeight(300)
        charts_layout.addWidget(self.sales_chart_view, 0, 0, 1, 2)

        # Top products bar chart
        self.top_products_chart = QChartView(); self.top_products_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.top_products_chart, 1, 0)

        # Distribution donut chart
        self.pie_chart = QChartView(); self.pie_chart.setMinimumHeight(300)
        charts_layout.addWidget(self.pie_chart, 1, 1)

        # Toggles
        toggles = QHBoxLayout()
        self.toggle_sales = QCheckBox("المبيعات اليومية")
        self.toggle_sales.setChecked(True)
        self.toggle_top = QCheckBox("أفضل المنتجات")
        self.toggle_top.setChecked(self.settings.value("show_top", True, type=bool))
        self.toggle_pie = QCheckBox("توزيع (مستقبلاً)")
        self.toggle_pie.setChecked(self.settings.value("show_pie", True, type=bool))
        for w in (self.toggle_sales, self.toggle_top, self.toggle_pie):
            w.stateChanged.connect(self._update_widgets_visibility)
            toggles.addWidget(w)
        toggles.addStretch()
        export_sales_btn = QPushButton("💾 تصدير المبيعات")
        export_sales_btn.clicked.connect(lambda: self._export_chart(self.sales_chart_view, "sales"))
        toggles.addWidget(export_sales_btn)
        export_top_btn = QPushButton("💾 تصدير الأفضل")
        export_top_btn.clicked.connect(lambda: self._export_chart(self.top_products_chart, "top_products"))
        toggles.addWidget(export_top_btn)
        export_dist_btn = QPushButton("💾 تصدير التوزيع")
        export_dist_btn.clicked.connect(lambda: self._export_chart(self.pie_chart, "distribution"))
        toggles.addWidget(export_dist_btn)
        root.addLayout(toggles)

    def _update_widgets_visibility(self):
        self.sales_chart_view.setVisible(self.toggle_sales.isChecked())
        self.top_products_chart.setVisible(self.toggle_top.isChecked())
        self.pie_chart.setVisible(self.toggle_pie.isChecked())
        # persist
        self.settings.setValue("show_sales", self.toggle_sales.isChecked())
        self.settings.setValue("show_top", self.toggle_top.isChecked())
        self.settings.setValue("show_pie", self.toggle_pie.isChecked())

    def _add_kpi_card(self, row: int, col: int, title: str, value: str, color: str, change: float|None=None, icon: str = "📊"):
        """إنشاء بطاقة KPI محسّنة مع أيقونة وتدرج لوني"""
        card = QGroupBox()
        # Gradient background effect
        card.setStyleSheet(f"""
            QGroupBox {{ 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}, stop:1 {self._darken_color(color)});
                border-radius: 12px;
                padding: 10px;
                min-height: 100px;
            }}
        """)
        lay = QVBoxLayout(card)
        
        # Icon + Title row
        header = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("color:white; font-size:24px;")
        header.addWidget(icon_lbl)
        
        t = QLabel(title)
        t.setStyleSheet("color:white; font-weight:bold; font-size:11px;")
        t.setWordWrap(True)
        header.addWidget(t, 1)
        lay.addLayout(header)
        
        # Value
        v = QLabel(value)
        v.setStyleSheet("color:white; font-size:22px; font-weight:bold;")
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(v)
        
        # Change indicator
        if change is not None:
            arrow = "↑" if change >= 0 else "↓"
            ch_color = "#C8E6C9" if change >= 0 else "#FFCDD2"
            ch = QLabel(f"{arrow} {abs(change):.1f}%")
            ch.setStyleSheet(f"color:{ch_color}; font-size:12px; font-weight:bold;")
            ch.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(ch)
        
        self.kpi_grid.addWidget(card, row, col)
    
    def _darken_color(self, hex_color: str) -> str:
        """تعتيم اللون للتدرج"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 30)
        g = max(0, g - 30)
        b = max(0, b - 30)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _load(self):
        days = self.period_combo.currentData()
        self.settings.setValue("period_days", int(days))
        end = QDate.currentDate().toPython()
        start = end - timedelta(days=days)

        data = self.service.load_dashboard(start, end)

        # KPIs grid (3x4 for 12 KPIs)
        # clear previous
        for i in reversed(range(self.kpi_grid.count())):
            item = self.kpi_grid.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Icon mapping for KPIs
        kpi_icons = {
            "total_sales": "💰",
            "today_sales": "📅",
            "month_sales": "📆",
            "gross_profit": "💵",
            "profit_margin": "📈",
            "aov": "🛒",
            "inventory_value": "📦",
            "inventory_turnover": "🔄",
            "low_stock": "⚠️",
            "receivables": "💳",
            "payables": "💸",
            "cash_flow": "💹"
        }
        
        # Display KPIs in 3x4 grid
        for i, k in enumerate(data.kpis[:12]):
            r, c = divmod(i, 4)
            value_str = f"{k.value:,.2f}{(' ' + k.unit) if k.unit else ''}"
            icon = kpi_icons.get(k.key, "📊")
            self._add_kpi_card(r, c, k.title, value_str, k.color, k.change, icon)

        # Sales series -> line chart
        self._render_sales_chart(data)

        # Top products -> bar chart
        self._render_top_products_chart(data)

        # distribution chart
        self._render_distribution()

        self._update_widgets_visibility()

        # Update Cycle Count KPIs
        try:
            cc = self.cycle_service.get_dashboard_summary()
            self.lbl_cc_open.setText(f"جلسات مفتوحة: {int(cc.get('open_sessions', 0))}")
            self.lbl_cc_closed.setText(f"مغلقة (7 أيام): {int(cc.get('recent_closed', 0))}")
            self.lbl_cc_varq.setText(f"فرق كمية: {float(cc.get('variance_qty', 0.0)):.2f}")
            self.lbl_cc_varv.setText(f"قيمة الفرق: {float(cc.get('variance_value', 0.0)):.2f} دج")
        except Exception:
            # Keep silent; dashboard should not break if cycle data missing
            pass

    def _render_sales_chart(self, data):
        chart = QChart(); chart.setTitle("المبيعات اليومية")
        series = QLineSeries(); series.setName("المبيعات")
        labels = []
        max_val = 0
        for pt in (data.sales_series[0].points if data.sales_series else []):
            idx = len(labels)
            series.append(idx, pt.value)
            labels.append(pt.label)
            max_val = max(max_val, pt.value)
        chart.addSeries(series)
        axis_x = QBarCategoryAxis(); axis_x.append(labels)
        axis_y = QValueAxis(); axis_y.setRange(0, max_val * 1.2 if max_val else 1)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom); series.attachAxis(axis_x)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft); series.attachAxis(axis_y)
        chart.legend().setVisible(False)
        self.sales_chart_view.setChart(chart)

    def _render_top_products_chart(self, data):
        # persist and read filters
        cat_id = self.category_combo.currentData() if hasattr(self, 'category_combo') else None
        lim = self.top_limit_combo.currentData() if hasattr(self, 'top_limit_combo') else 10
        if cat_id is not None:
            self.settings.setValue("top_category_id", int(cat_id))
        self.settings.setValue("top_limit", int(lim))

        # get period
        end = QDate.currentDate().toPython()
        days = self.period_combo.currentData()
        start = end - timedelta(days=days)

        # fetch fresh top products with filters
        try:
            rows = self.service._top_products(start, end, limit=int(lim), category_id=cat_id)
        except Exception:
            rows = data.top_products

        chart = QChart(); chart.setTitle("أعلى المنتجات مبيعاً")
        series = QBarSeries()
        bar_set = QBarSet("المبيعات")
        labels = []
        for r in rows:
            labels.append(str(r.get("name")))
            bar_set.append(float(r.get("total") or 0))
        series.append(bar_set)
        chart.addSeries(series)
        axis_x = QBarCategoryAxis(); axis_x.append(labels)
        axis_y = QValueAxis(); chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft); series.attachAxis(axis_y)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom); series.attachAxis(axis_x)
        self.top_products_chart.setChart(chart)

    def _render_distribution(self):
        # persist choice
        kind = self.dist_combo.currentData() if hasattr(self, 'dist_combo') else 'payment'
        self.settings.setValue("distribution", kind)

        # load dataset from service
        end = QDate.currentDate().toPython()
        days = self.period_combo.currentData()
        start = end - timedelta(days=days)

        data = (
            self.service.get_distribution_by_payment_method(start, end)
            if kind == 'payment' else
            self.service.get_distribution_by_category(start, end)
        )

        chart = QChart()
        chart.setTitle("توزيع المبيعات")
        series = QPieSeries()
        total = 0.0
        for row in data:
            label = str(row.get('label') or 'غير محدد')
            value = float(row.get('value') or 0)
            total += value
            series.append(label, value)
        series.setHoleSize(0.45)
        chart.addSeries(series)
        chart.legend().setVisible(True)
        self.pie_chart.setChart(chart)

    def _toggle_auto_refresh(self):
        enabled = self.auto_refresh_check.isChecked()
        self.settings.setValue("auto_refresh", enabled)
        if enabled:
            self.refresh_timer.start(60000)
        else:
            self.refresh_timer.stop()

    def _export_chart(self, chart_view: QChartView, name: str):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "حفظ الرسم البياني", f"dashboard_{name}.png", "PNG (*.png)")
        if path:
            pixmap = chart_view.grab()
            pixmap.save(path, "PNG")
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(self, "نجح", f"تم حفظ الرسم في:\n{path}")

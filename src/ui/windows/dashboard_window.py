"""
نافذة لوحة المعلومات الرئيسية (Dashboard)
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QDateEdit, QGridLayout, QGroupBox, QCheckBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt, QDate, QSettings, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries
from datetime import date, timedelta
from typing import Optional

from ...core.database_manager import DatabaseManager
from ...services.dashboard_service import DashboardService
from ...services.cycle_count_service import CycleCountService
from ...ai.chatbot import ChatbotEngine


class DashboardWindow(QMainWindow):
    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "dashboard"
    window_singleton = True
    window_title = "📊 لوحة المعلومات الرئيسية"
    
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
        self._blink_timer = None  # Timer للوميض
        self._blink_state = False
        
        # تهيئة Chatbot
        try:
            self.chatbot = ChatbotEngine()
            self.chatbot_enabled = True
        except Exception:
            self.chatbot = None
            self.chatbot_enabled = False

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
        
        # Chatbot Widget (في الزاوية السفلية)
        if self.chatbot_enabled:
            chatbot_widget = self._create_chatbot_widget()
            root.addWidget(chatbot_widget)

    def _update_widgets_visibility(self):
        self.sales_chart_view.setVisible(self.toggle_sales.isChecked())
        self.top_products_chart.setVisible(self.toggle_top.isChecked())
        self.pie_chart.setVisible(self.toggle_pie.isChecked())
        # persist
        self.settings.setValue("show_sales", self.toggle_sales.isChecked())
        self.settings.setValue("show_top", self.toggle_top.isChecked())
        self.settings.setValue("show_pie", self.toggle_pie.isChecked())

    def _add_kpi_card(self, row: int, col: int, title: str, value: str, color: str, change: float|None=None, icon: str = "📊", kpi_key: str = ""):
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
        return card  # إرجاع البطاقة للسماح بالتفاعل
    
    def _add_blink_effect(self, card: QGroupBox):
        """إضافة تأثير وميض للبطاقة"""
        # تأثير بسيط باستخدام QTimer
        if self._blink_timer:
            self._blink_timer.stop()
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(lambda: self._toggle_blink(card))
        self._blink_timer.start(1000)  # وميض كل ثانية
        self._blink_state = False
    
    def _toggle_blink(self, card: QGroupBox):
        """تبديل حالة الوميض"""
        self._blink_state = not self._blink_state
        if self._blink_state:
            # لون أحمر فاتح
            card.setStyleSheet("""
                QGroupBox { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #F44336, stop:1 #D32F2F);
                    border-radius: 12px;
                    padding: 10px;
                    min-height: 100px;
                    border: 2px solid #FF5252;
                }
            """)
        else:
            # لون أحمر عادي
            card.setStyleSheet("""
                QGroupBox { 
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #F44336, stop:1 #D32F2F);
                    border-radius: 12px;
                    padding: 10px;
                    min-height: 100px;
                }
            """)
    
    def _show_low_stock_dialog(self):
        """عرض نافذة المنتجات منخفضة المخزون"""
        try:
            products = self.service.get_low_stock_products()
            if not products:
                QMessageBox.information(self, "معلومات", "لا توجد منتجات منخفضة المخزون حالياً.")
                return
            
            dialog = LowStockDialog(products, self, db_manager=self.db)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل المنتجات منخفضة المخزون:\n{str(e)}")
    
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
            card = self._add_kpi_card(r, c, k.title, value_str, k.color, k.change, icon, k.key)
            
            # جعل بطاقة low_stock قابلة للنقر وتظهر تحذير
            if k.key == "low_stock" and k.value > 0:
                card.setCursor(Qt.PointingHandCursor)
                card.mousePressEvent = lambda e, kpi_key=k.key: self._show_low_stock_dialog()
                # إضافة تأثير وميض
                self._add_blink_effect(card)

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
    
    def _create_chatbot_widget(self):
        """إنشاء widget للشات بوت"""
        chatbot_group = QGroupBox("🤖 المساعد الذكي")
        chatbot_group.setMaximumHeight(300)
        chatbot_group.setCheckable(True)
        chatbot_group.setChecked(False)  # مطوي افتراضياً
        chatbot_group.toggled.connect(lambda checked: self._toggle_chatbot(checked))
        
        layout = QVBoxLayout(chatbot_group)
        
        # منطقة المحادثة
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(200)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("اسألني عن المبيعات، المخزون، أو أي شيء آخر...")
        scroll.setWidget(self.chat_display)
        layout.addWidget(scroll)
        
        # حقل الإدخال
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("اكتب سؤالك هنا...")
        self.chat_input.returnPressed.connect(self._send_chat_message)
        input_layout.addWidget(self.chat_input)
        
        send_btn = QPushButton("إرسال")
        send_btn.clicked.connect(self._send_chat_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # إضافة رسالة ترحيبية
        self._add_chat_message("المساعد", "مرحباً! أنا المساعد الذكي. اسألني عن:\n- مبيعات اليوم\n- المنتجات الأكثر مبيعاً\n- المنتجات منخفضة المخزون\n- أو أي سؤال آخر!")
        
        return chatbot_group
    
    def _toggle_chatbot(self, visible: bool):
        """تبديل حالة الشات بوت"""
        if visible and self.chatbot:
            self.chat_input.setFocus()
    
    def _send_chat_message(self):
        """إرسال رسالة للشات بوت"""
        if not self.chatbot_enabled or not self.chatbot:
            return
        
        message = self.chat_input.text().strip()
        if not message:
            return
        
        # إضافة رسالة المستخدم
        self._add_chat_message("أنت", message)
        self.chat_input.clear()
        
        # معالجة الرسالة والحصول على الرد
        try:
            # محاولة الحصول على معلومات من لوحة التحكم
            response = self._process_chat_query(message)
            
            if not response:
                # استخدام chatbot الافتراضي
                result = self.chatbot.process_message(message, user_id="dashboard_user")
                response = result.get("response", "عذراً، لم أفهم السؤال. يمكنك إعادة صياغته.")
            
            self._add_chat_message("المساعد", response)
        except Exception as e:
            self._add_chat_message("المساعد", f"حدث خطأ: {str(e)}")
    
    def _add_chat_message(self, sender: str, message: str):
        """إضافة رسالة إلى عرض المحادثة"""
        color = "#1976D2" if sender == "المساعد" else "#4CAF50"
        self.chat_display.append(f'<div style="margin: 5px 0;"><b style="color: {color};">{sender}:</b> {message}</div>')
        # التمرير للأسفل
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _process_chat_query(self, message: str) -> str:
        """معالجة استعلامات خاصة من لوحة التحكم"""
        message_lower = message.lower()
        
        # استعلامات المبيعات
        if any(word in message_lower for word in ["مبيعات اليوم", "مبيعات اليوم", "مبيعات", "sales today"]):
            try:
                today = QDate.currentDate().toPython()
                data = self.service.load_dashboard(today, today)
                today_sales = next((k for k in data.kpis if k.key == "today_sales"), None)
                if today_sales:
                    return f"مبيعات اليوم: {today_sales.value:,.2f} {today_sales.unit}"
            except:
                pass
        
        # استعلامات المنتجات الأكثر مبيعاً
        if any(word in message_lower for word in ["أكثر منتج", "أفضل منتج", "top product", "best seller"]):
            try:
                end = QDate.currentDate().toPython()
                start = end - timedelta(days=30)
                top_products = self.service._top_products(start, end, limit=3)
                if top_products:
                    result = "أفضل 3 منتجات مبيعاً:\n"
                    for i, p in enumerate(top_products, 1):
                        result += f"{i}. {p.get('name', 'غير محدد')}: {p.get('total', 0):,.2f} د.ج\n"
                    return result
            except:
                pass
        
        # استعلامات المنتجات منخفضة المخزون
        if any(word in message_lower for word in ["منخفض", "ناقص", "low stock", "نواقص"]):
            try:
                low_stock = self.service._kpi_low_stock_count()
                if low_stock.value > 0:
                    products = self.service.get_low_stock_products()
                    result = f"يوجد {low_stock.value} منتج منخفض المخزون:\n"
                    for p in products[:5]:  # أول 5 منتجات
                        result += f"- {p.get('name', 'غير محدد')}: {p.get('current_stock', 0):,.0f} (الحد الأدنى: {p.get('min_stock', 0):,.0f})\n"
                    if len(products) > 5:
                        result += f"... و {len(products) - 5} منتج آخر"
                    return result
                else:
                    return "✅ لا توجد منتجات منخفضة المخزون حالياً."
            except:
                pass
        
        # استعلامات الربح
        if any(word in message_lower for word in ["ربح", "profit", "أرباح"]):
            try:
                end = QDate.currentDate().toPython()
                start = end - timedelta(days=30)
                data = self.service.load_dashboard(start, end)
                profit = next((k for k in data.kpis if k.key == "gross_profit"), None)
                if profit:
                    return f"إجمالي الربح (آخر 30 يوم): {profit.value:,.2f} {profit.unit}"
            except:
                pass
        
        return None  # لم يتم التعرف على الاستعلام، استخدم chatbot الافتراضي
    
    def closeEvent(self, event):
        """تنظيف الموارد عند إغلاق النافذة"""
        if self._blink_timer:
            self._blink_timer.stop()
        super().closeEvent(event)


class LowStockDialog(QDialog):
    """نافذة عرض المنتجات منخفضة المخزون"""
    
    def __init__(self, products: list, parent=None, db_manager=None):
        super().__init__(parent)
        self.products = products
        self.db_manager = db_manager
        self.setWindowTitle("⚠️ منتجات منخفضة المخزون")
        self.setMinimumSize(800, 500)
        self.setLayoutDirection(Qt.RightToLeft)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # العنوان
        title = QLabel("⚠️ منتجات منخفضة المخزون")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #F44336; padding: 10px;")
        layout.addWidget(title)
        
        # الجدول
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "المنتج", "الباركود", "المخزون الحالي", 
            "الحد الأدنى", "الحالة", "سعر التكلفة", "سعر البيع"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # ملء الجدول
        self._populate_table()
        
        layout.addWidget(self.table)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_create_purchase = QPushButton("🛒 إنشاء طلب شراء")
        self.btn_create_purchase.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_create_purchase.clicked.connect(self._create_purchase_order)
        buttons_layout.addWidget(self.btn_create_purchase)
        
        self.btn_close = QPushButton("إغلاق")
        self.btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(self.btn_close)
        
        layout.addLayout(buttons_layout)
    
    def _populate_table(self):
        """ملء الجدول بالمنتجات"""
        self.table.setRowCount(len(self.products))
        
        for row, product in enumerate(self.products):
            # اسم المنتج
            name_item = QTableWidgetItem(str(product.get('name', 'غير محدد')))
            self.table.setItem(row, 0, name_item)
            
            # الباركود
            barcode_item = QTableWidgetItem(str(product.get('barcode', '-')))
            self.table.setItem(row, 1, barcode_item)
            
            # المخزون الحالي
            current_stock = float(product.get('current_stock', 0))
            stock_item = QTableWidgetItem(f"{current_stock:,.0f}")
            if current_stock == 0:
                stock_item.setForeground(QColor("#F44336"))  # أحمر للنفاد
            else:
                stock_item.setForeground(QColor("#FF9800"))  # برتقالي للمنخفض
            self.table.setItem(row, 2, stock_item)
            
            # الحد الأدنى
            min_stock = float(product.get('min_stock', 0))
            min_item = QTableWidgetItem(f"{min_stock:,.0f}")
            self.table.setItem(row, 3, min_item)
            
            # الحالة
            status = product.get('status', 'عادي')
            status_item = QTableWidgetItem(status)
            if status == 'نفذ من المخزون':
                status_item.setForeground(QColor("#F44336"))
            else:
                status_item.setForeground(QColor("#FF9800"))
            self.table.setItem(row, 4, status_item)
            
            # سعر التكلفة
            cost = float(product.get('cost_price', 0))
            cost_item = QTableWidgetItem(f"{cost:,.2f} د.ج")
            self.table.setItem(row, 5, cost_item)
            
            # سعر البيع
            selling = float(product.get('selling_price', 0))
            selling_item = QTableWidgetItem(f"{selling:,.2f} د.ج")
            self.table.setItem(row, 6, selling_item)
        
        # ضبط عرض الأعمدة
        self.table.resizeColumnsToContents()
    
    def _create_purchase_order(self):
        """إنشاء طلب شراء للمنتجات المحددة"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "تحذير", "الرجاء تحديد منتج واحد على الأقل من الجدول.")
            return
        
        # جمع المنتجات المحددة
        selected_products = []
        for index in selected_rows:
            row = index.row()
            product = self.products[row]
            selected_products.append({
                'id': product.get('id'),
                'name': product.get('name'),
                'barcode': product.get('barcode', ''),
                'min_stock': float(product.get('min_stock', 0)),
                'current_stock': float(product.get('current_stock', 0)),
                'cost_price': float(product.get('cost_price', 0))
            })
        
        # عرض رسالة تأكيد
        product_names = "\n".join([f"- {p['name']}" for p in selected_products])
        reply = QMessageBox.question(
            self,
            "تأكيد",
            f"هل تريد إنشاء طلب شراء للمنتجات التالية؟\n\n{product_names}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Yes:
            try:
                # الحصول على db_manager
                db_manager = self.db_manager
                
                if not db_manager:
                    # محاولة الحصول من النافذة الأم
                    parent = self.parent()
                    if hasattr(parent, 'db'):
                        db_manager = parent.db
                    elif hasattr(parent, 'db_manager'):
                        db_manager = parent.db_manager
                
                if not db_manager:
                    QMessageBox.critical(
                        self,
                        "خطأ",
                        "لا يمكن الوصول إلى قاعدة البيانات.\n"
                        "يرجى فتح نافذة إنشاء طلب الشراء يدوياً."
                    )
                    return
                
                # استيراد PurchaseOrderDialog
                from ...dialogs.purchase_order_dialog import PurchaseOrderDialog
                
                # فتح نافذة إنشاء طلب الشراء مع المنتجات المسبقة
                dialog = PurchaseOrderDialog(
                    db_manager=db_manager,
                    parent=parent,
                    prefill_products=selected_products
                )
                
                if dialog.exec():
                    # تم إنشاء طلب الشراء بنجاح
                    QMessageBox.information(
                        self,
                        "نجاح",
                        f"تم إنشاء طلب شراء لـ {len(selected_products)} منتج بنجاح."
                    )
                    self.accept()  # إغلاق نافذة النواقص
                else:
                    # المستخدم ألغى العملية
                    pass
                    
            except ImportError as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"فشل في استيراد نافذة إنشاء طلب الشراء:\n{str(e)}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    f"حدث خطأ أثناء إنشاء طلب الشراء:\n{str(e)}"
                )

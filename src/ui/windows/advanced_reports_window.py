"""
نافذة التقارير المتقدمة الجديدة
Advanced Reports Window - Enhanced Version

نافذة شاملة لتوليد التقارير المتقدمة مع رسوم بيانية
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox,
    QMessageBox, QFileDialog, QTabWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont, QColor
from PySide6.QtCharts import (
    QChart, QChartView, QPieSeries, QBarSeries, 
    QBarSet, QBarCategoryAxis, QValueAxis
)
from datetime import datetime
from typing import Optional

from ...core.database_manager import DatabaseManager
from ...services.report_service import ReportService
from ...models.report import (
    Report, ReportType, ReportPeriod, ReportFilter, ChartType
)


class AdvancedReportsWindow(QMainWindow):
    """نافذة التقارير المتقدمة الجديدة"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.service = ReportService(db_manager)
        self.current_report: Optional[Report] = None
        
        self.setWindowTitle("📊 التقارير المتقدمة - نظام متكامل")
        self.setMinimumSize(1400, 850)
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # العنوان
        title = QLabel("📊 نظام التقارير المتقدمة")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1976D2; padding: 10px;")
        layout.addWidget(title)
        
        # الفلاتر
        filters_group = self._create_filters_section()
        layout.addWidget(filters_group)
        
        # التبويبات
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_report_tab(), "📄 عرض التقرير")
        self.tabs.addTab(self._create_charts_tab(), "📈 الرسوم البيانية")
        layout.addWidget(self.tabs)
        
        # الإجراءات
        actions = self._create_actions_section()
        layout.addLayout(actions)
    
    def _create_filters_section(self) -> QGroupBox:
        """إنشاء قسم الفلاتر"""
        group = QGroupBox("⚙️ إعدادات التقرير والفلاتر")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 6px;
                margin-top: 10px;
                padding: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        layout = QVBoxLayout(group)
        
        # صف 1: النوع والفترة
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("نوع التقرير:"))
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("📊 ملخص المبيعات", ReportType.SALES_SUMMARY)
        self.report_type_combo.addItem("📋 المبيعات التفصيلية", ReportType.SALES_DETAILED)
        self.report_type_combo.addItem("📦 المبيعات حسب المنتج", ReportType.SALES_BY_PRODUCT)
        self.report_type_combo.addItem("👥 المبيعات حسب العميل", ReportType.SALES_BY_CUSTOMER)
        self.report_type_combo.addItem("📁 المبيعات حسب الفئة", ReportType.SALES_BY_CATEGORY)
        self.report_type_combo.addItem("🔄 حركة المخزون", ReportType.INVENTORY_MOVEMENT)
        self.report_type_combo.addItem("💰 تقييم المخزون", ReportType.INVENTORY_VALUATION)
        self.report_type_combo.addItem("📊 ميزان المراجعة", ReportType.FINANCIAL_TRIAL_BALANCE)
        self.report_type_combo.addItem("💵 قائمة الدخل", ReportType.FINANCIAL_INCOME)
        self.report_type_combo.setMinimumWidth(280)
        row1.addWidget(self.report_type_combo)
        
        row1.addSpacing(30)
        row1.addWidget(QLabel("الفترة الزمنية:"))
        
        self.period_combo = QComboBox()
        self.period_combo.addItem("📅 يومي", ReportPeriod.DAILY)
        self.period_combo.addItem("📅 أسبوعي", ReportPeriod.WEEKLY)
        self.period_combo.addItem("📅 شهري", ReportPeriod.MONTHLY)
        self.period_combo.addItem("📅 ربع سنوي", ReportPeriod.QUARTERLY)
        self.period_combo.addItem("📅 سنوي", ReportPeriod.YEARLY)
        self.period_combo.addItem("📅 مخصص", ReportPeriod.CUSTOM)
        self.period_combo.setCurrentIndex(2)
        row1.addWidget(self.period_combo)
        row1.addStretch()
        
        layout.addLayout(row1)
        
        # صف 2: التواريخ
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("من تاريخ:"))
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        row2.addWidget(self.start_date)
        
        row2.addWidget(QLabel("إلى تاريخ:"))
        
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        row2.addWidget(self.end_date)
        row2.addStretch()
        
        layout.addLayout(row2)
        
        # صف 3: الخيارات والتوليد
        row3 = QHBoxLayout()
        
        self.include_returns = QCheckBox("✅ تضمين المرتجعات")
        self.include_returns.setChecked(True)
        row3.addWidget(self.include_returns)
        
        self.only_approved = QCheckBox("✅ المعتمد فقط")
        self.only_approved.setChecked(True)
        row3.addWidget(self.only_approved)
        
        row3.addStretch()
        
        self.generate_btn = QPushButton("🔄 توليد التقرير")
        self.generate_btn.setMinimumWidth(180)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976D2, stop:1 #1565C0);
            }
            QPushButton:pressed {
                background: #0D47A1;
            }
        """)
        row3.addWidget(self.generate_btn)
        
        layout.addLayout(row3)
        
        return group
    
    def _create_report_tab(self) -> QWidget:
        """إنشاء تبويب التقرير"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # بطاقات الملخص
        self.summary_layout = QHBoxLayout()
        layout.addLayout(self.summary_layout)
        
        # الجدول
        self.report_table = QTableWidget()
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.report_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.report_table)
        
        return widget
    
    def _create_charts_tab(self) -> QWidget:
        """إنشاء تبويب الرسوم البيانية"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        info_label = QLabel("📈 الرسوم البيانية التوضيحية")
        info_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        self.charts_layout = QVBoxLayout()
        layout.addLayout(self.charts_layout)
        layout.addStretch()
        
        return widget
    
    def _create_actions_section(self) -> QHBoxLayout:
        """إنشاء قسم الإجراءات"""
        layout = QHBoxLayout()
        
        btn_style = """
            QPushButton {
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                opacity: 0.9;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
        
        self.export_pdf_btn = QPushButton("📄 تصدير PDF")
        self.export_pdf_btn.setStyleSheet(btn_style + """
            QPushButton { background-color: #F44336; color: white; }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        self.export_pdf_btn.setEnabled(False)
        layout.addWidget(self.export_pdf_btn)
        
        self.export_excel_btn = QPushButton("📊 تصدير Excel")
        self.export_excel_btn.setStyleSheet(btn_style + """
            QPushButton { background-color: #4CAF50; color: white; }
            QPushButton:hover { background-color: #388E3C; }
        """)
        self.export_excel_btn.setEnabled(False)
        layout.addWidget(self.export_excel_btn)
        
        self.print_btn = QPushButton("🖨️ طباعة")
        self.print_btn.setStyleSheet(btn_style + """
            QPushButton { background-color: #FF9800; color: white; }
            QPushButton:hover { background-color: #F57C00; }
        """)
        self.print_btn.setEnabled(False)
        layout.addWidget(self.print_btn)
        
        layout.addStretch()
        
        self.close_btn = QPushButton("❌ إغلاق")
        self.close_btn.setStyleSheet(btn_style + """
            QPushButton { background-color: #757575; color: white; }
            QPushButton:hover { background-color: #616161; }
        """)
        layout.addWidget(self.close_btn)
        
        return layout
    
    def _connect_signals(self):
        """ربط الإشارات"""
        self.generate_btn.clicked.connect(self._generate_report)
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        self.export_excel_btn.clicked.connect(self._export_excel)
        self.print_btn.clicked.connect(self._print_report)
        self.close_btn.clicked.connect(self.close)
    
    def _on_period_changed(self):
        """معالج تغيير الفترة"""
        period = self.period_combo.currentData()
        today = QDate.currentDate()
        
        if period == ReportPeriod.DAILY:
            self.start_date.setDate(today)
            self.end_date.setDate(today)
        elif period == ReportPeriod.WEEKLY:
            self.start_date.setDate(today.addDays(-7))
            self.end_date.setDate(today)
        elif period == ReportPeriod.MONTHLY:
            self.start_date.setDate(today.addMonths(-1))
            self.end_date.setDate(today)
        elif period == ReportPeriod.QUARTERLY:
            self.start_date.setDate(today.addMonths(-3))
            self.end_date.setDate(today)
        elif period == ReportPeriod.YEARLY:
            self.start_date.setDate(today.addYears(-1))
            self.end_date.setDate(today)
    
    def _generate_report(self):
        """توليد التقرير"""
        try:
            filters = ReportFilter(
                start_date=self.start_date.date().toPython(),
                end_date=self.end_date.date().toPython(),
                period=self.period_combo.currentData(),
                include_returns=self.include_returns.isChecked(),
                only_approved=self.only_approved.isChecked()
            )
            
            report_type = self.report_type_combo.currentData()
            
            # توليد التقرير
            if report_type == ReportType.SALES_SUMMARY:
                self.current_report = self.service.generate_sales_summary_report(filters)
            elif report_type == ReportType.SALES_DETAILED:
                self.current_report = self.service.generate_sales_detailed_report(filters)
            elif report_type == ReportType.SALES_BY_PRODUCT:
                self.current_report = self.service.generate_sales_by_product_report(filters)
            elif report_type == ReportType.INVENTORY_MOVEMENT:
                self.current_report = self.service.generate_inventory_movement_report(filters)
            elif report_type == ReportType.INVENTORY_VALUATION:
                self.current_report = self.service.generate_inventory_valuation_report(filters)
            elif report_type == ReportType.FINANCIAL_TRIAL_BALANCE:
                self.current_report = self.service.generate_trial_balance_report(filters)
            elif report_type == ReportType.FINANCIAL_INCOME:
                self.current_report = self.service.generate_income_statement_report(filters)
            else:
                QMessageBox.warning(self, "تحذير", "نوع التقرير غير مدعوم حالياً")
                return
            
            self._display_report()
            
            self.export_pdf_btn.setEnabled(True)
            self.export_excel_btn.setEnabled(True)
            self.print_btn.setEnabled(True)
            
            QMessageBox.information(
                self, "✅ نجاح",
                f"تم توليد التقرير بنجاح!\n\n"
                f"عدد السطور: {self.current_report.get_total_lines()}\n"
                f"الفترة: {self.current_report.get_period_description()}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "❌ خطأ", f"فشل توليد التقرير:\n{str(e)}")
    
    def _display_report(self):
        """عرض التقرير"""
        if not self.current_report:
            return
        
        self._display_summary()
        self._display_data()
        
        if self.current_report.has_charts():
            self._display_charts()
    
    def _display_summary(self):
        """عرض بطاقات الملخص"""
        while self.summary_layout.count():
            item = self.summary_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self.current_report.sales_summary:
            s = self.current_report.sales_summary
            self._add_summary_card("إجمالي المبيعات", f"{s.total_sales:,.2f} ر.س", "#4CAF50")
            self._add_summary_card("عدد الفواتير", str(s.total_invoices), "#2196F3")
            self._add_summary_card("الأرباح", f"{s.total_profit:,.2f} ر.س", "#FF9800")
            self._add_summary_card("هامش الربح", f"{s.average_profit_margin:.1f}%", "#9C27B0")
            
        elif self.current_report.inventory_summary:
            s = self.current_report.inventory_summary
            self._add_summary_card("المنتجات", str(s.total_products), "#4CAF50")
            self._add_summary_card("الكمية", f"{s.total_quantity:,.0f}", "#2196F3")
            self._add_summary_card("القيمة", f"{s.total_value:,.2f} ر.س", "#FF9800")
            
        elif self.current_report.financial_summary:
            s = self.current_report.financial_summary
            self._add_summary_card("الإيرادات", f"{s.total_revenue:,.2f} ر.س", "#4CAF50")
            self._add_summary_card("المصروفات", f"{s.total_expenses:,.2f} ر.س", "#F44336")
            self._add_summary_card("صافي الدخل", f"{s.net_income:,.2f} ر.س", "#2196F3")
    
    def _add_summary_card(self, title: str, value: str, color: str):
        """إضافة بطاقة ملخص"""
        card = QWidget()
        card.setMinimumHeight(100)
        card.setStyleSheet(f"""
            QWidget {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {self._darken_color(color)});
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(5)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-size: 13px; font-weight: bold;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        layout.addWidget(value_label)
        
        self.summary_layout.addWidget(card)
    
    def _darken_color(self, hex_color: str) -> str:
        """تغميق اللون"""
        color = QColor(hex_color)
        return color.darker(120).name()
    
    def _display_data(self):
        """عرض البيانات"""
        self.report_table.clear()
        
        if self.current_report.sales_lines:
            self._display_sales_data()
        elif self.current_report.inventory_lines:
            self._display_inventory_data()
        elif self.current_report.financial_lines:
            self._display_financial_data()
    
    def _display_sales_data(self):
        """عرض بيانات المبيعات"""
        lines = self.current_report.sales_lines
        headers = ["التاريخ", "رقم الفاتورة", "العميل", "المنتج", 
                   "الكمية", "السعر", "الخصم", "الضريبة", "الإجمالي", "الربح"]
        
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(lines))
        
        for row, line in enumerate(lines):
            self.report_table.setItem(row, 0, QTableWidgetItem(str(line.date)))
            self.report_table.setItem(row, 1, QTableWidgetItem(line.invoice_number))
            self.report_table.setItem(row, 2, QTableWidgetItem(line.customer_name))
            self.report_table.setItem(row, 3, QTableWidgetItem(line.product_name or ""))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{line.quantity:,.2f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"{line.unit_price:,.2f}"))
            self.report_table.setItem(row, 6, QTableWidgetItem(f"{line.discount:,.2f}"))
            self.report_table.setItem(row, 7, QTableWidgetItem(f"{line.tax:,.2f}"))
            self.report_table.setItem(row, 8, QTableWidgetItem(f"{line.total:,.2f}"))
            
            profit_item = QTableWidgetItem(f"{line.profit:,.2f}")
            if line.profit > 0:
                profit_item.setForeground(QColor("#4CAF50"))
            elif line.profit < 0:
                profit_item.setForeground(QColor("#F44336"))
            self.report_table.setItem(row, 9, profit_item)
    
    def _display_inventory_data(self):
        """عرض بيانات المخزون"""
        lines = self.current_report.inventory_lines
        headers = ["الكود", "المنتج", "الفئة", "رصيد افتتاحي", 
                   "مشتريات", "مبيعات", "رصيد ختامي", "القيمة"]
        
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(lines))
        
        for row, line in enumerate(lines):
            self.report_table.setItem(row, 0, QTableWidgetItem(line.product_code))
            self.report_table.setItem(row, 1, QTableWidgetItem(line.product_name))
            self.report_table.setItem(row, 2, QTableWidgetItem(line.category_name))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{line.opening_quantity:,.2f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{line.purchases:,.2f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"{line.sales:,.2f}"))
            self.report_table.setItem(row, 6, QTableWidgetItem(f"{line.closing_quantity:,.2f}"))
            self.report_table.setItem(row, 7, QTableWidgetItem(f"{line.total_value:,.2f}"))
    
    def _display_financial_data(self):
        """عرض البيانات المالية"""
        lines = self.current_report.financial_lines
        headers = ["رمز الحساب", "اسم الحساب", "النوع", "مدين", "دائن", "الرصيد"]
        
        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(lines))
        
        for row, line in enumerate(lines):
            self.report_table.setItem(row, 0, QTableWidgetItem(line.account_code))
            self.report_table.setItem(row, 1, QTableWidgetItem(line.account_name))
            self.report_table.setItem(row, 2, QTableWidgetItem(line.account_type))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{line.debit:,.2f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{line.credit:,.2f}"))
            
            balance_item = QTableWidgetItem(f"{line.closing_balance:,.2f}")
            if line.closing_balance > 0:
                balance_item.setForeground(QColor("#4CAF50"))
            elif line.closing_balance < 0:
                balance_item.setForeground(QColor("#F44336"))
            self.report_table.setItem(row, 5, balance_item)
    
    def _display_charts(self):
        """عرض الرسوم البيانية"""
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for chart_data in self.current_report.charts:
            if chart_data.chart_type == ChartType.PIE:
                view = self._create_pie_chart(chart_data)
            elif chart_data.chart_type == ChartType.BAR:
                view = self._create_bar_chart(chart_data)
            else:
                continue
            
            self.charts_layout.addWidget(view)
    
    def _create_pie_chart(self, chart_data) -> QChartView:
        """إنشاء رسم دائري"""
        series = QPieSeries()
        
        for i, label in enumerate(chart_data.labels):
            value = chart_data.datasets[0]["data"][i]
            if value > 0:
                slice = series.append(label, value)
                if i < len(chart_data.colors):
                    slice.setColor(QColor(chart_data.colors[i]))
                slice.setLabelVisible(True)
                slice.setLabelColor(Qt.GlobalColor.black)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_data.title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        view = QChartView(chart)
        view.setRenderHint(view.RenderHint.Antialiasing)
        view.setMinimumHeight(450)
        
        return view
    
    def _create_bar_chart(self, chart_data) -> QChartView:
        """إنشاء رسم أعمدة"""
        series = QBarSeries()
        
        bar_set = QBarSet(chart_data.datasets[0].get("label", "البيانات"))
        for value in chart_data.datasets[0]["data"]:
            bar_set.append(value)
        
        if chart_data.colors:
            bar_set.setColor(QColor(chart_data.colors[0]))
        
        series.append(bar_set)
        
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle(chart_data.title)
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        axis_x = QBarCategoryAxis()
        axis_x.append(chart_data.labels)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)
        
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        
        view = QChartView(chart)
        view.setRenderHint(view.RenderHint.Antialiasing)
        view.setMinimumHeight(450)
        
        return view
    
    def _export_pdf(self):
        """تصدير إلى PDF"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ التقرير كـ PDF", "", "PDF Files (*.pdf)"
        )
        
        if file_path:
            try:
                success = self.service.export_report_to_pdf(self.current_report, file_path)
                if success:
                    QMessageBox.information(self, "✅ نجاح", f"تم حفظ التقرير بنجاح:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "❌ خطأ", f"فشل التصدير:\n{str(e)}")
    
    def _export_excel(self):
        """تصدير إلى Excel"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "حفظ التقرير كـ Excel", "", "Excel Files (*.xlsx)"
        )
        
        if file_path:
            try:
                success = self.service.export_report_to_excel(self.current_report, file_path)
                if success:
                    QMessageBox.information(self, "✅ نجاح", f"تم حفظ التقرير بنجاح:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "❌ خطأ", f"فشل التصدير:\n{str(e)}")
    
    def _print_report(self):
        """طباعة التقرير"""
        QMessageBox.information(
            self, "🖨️ الطباعة",
            "ميزة الطباعة قيد التطوير\n\nيمكنك تصدير التقرير كـ PDF والطباعة من هناك"
        )

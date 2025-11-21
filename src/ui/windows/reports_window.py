#!/usr/bin/env python3
"""
نافذة التقارير - Reports Window
واجهة شاملة لعرض وتصدير التقارير المختلفة مع دعم اللغة العربية
"""

import sys
import os
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QCheckBox, QFrame, QMessageBox, QProgressBar,
    QTabWidget, QGroupBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QScrollArea, QSizePolicy, QApplication, QCompleter, QButtonGroup,
    QRadioButton, QSlider, QDial, QCalendarWidget, QTimeEdit,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QStackedWidget, QToolBar, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QDate, QTime, QStringListModel, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QValidator, QDoubleValidator, QKeySequence, QShortcut, QAction
from PySide6.QtCharts import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QLineSeries, QValueAxis, QBarCategoryAxis, QDateTimeAxis

from ...core.database_manager import DatabaseManager
from ...services.reports_service import ReportsService, ReportType, ExportFormat, ReportFilter
from ...services.sales_service import SalesService
from ...services.inventory_service import InventoryService
from ...utils.logger import setup_logger


class ReportGenerationWorker(QThread):
    """عامل توليد التقارير"""
    report_generated = Signal(object)  # ReportData
    progress_updated = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, reports_service: ReportsService, report_type: ReportType, filters: ReportFilter):
        super().__init__()
        self.reports_service = reports_service
        self.report_type = report_type
        self.filters = filters
    
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            # توليد التقرير
            report_data = self.reports_service.generate_report(self.report_type, self.filters)
            
            self.progress_updated.emit(100)
            self.report_generated.emit(report_data)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class ReportExportWorker(QThread):
    """عامل تصدير التقارير"""
    export_completed = Signal(str)  # file_path
    progress_updated = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, reports_service: ReportsService, report_data, export_format: ExportFormat, file_path: str):
        super().__init__()
        self.reports_service = reports_service
        self.report_data = report_data
        self.export_format = export_format
        self.file_path = file_path
    
    def run(self):
        try:
            self.progress_updated.emit(10)
            
            # تصدير التقرير
            success = self.reports_service.export_report(
                self.report_data, 
                self.export_format, 
                self.file_path
            )
            
            self.progress_updated.emit(100)
            
            if success:
                self.export_completed.emit(self.file_path)
            else:
                self.error_occurred.emit("فشل في تصدير التقرير")
                
        except Exception as e:
            self.error_occurred.emit(str(e))


class ReportsWindow(QMainWindow):
    """نافذة التقارير الرئيسية"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.reports_service = ReportsService(db_manager)
        self.sales_service = SalesService(db_manager)
        self.inventory_service = InventoryService(db_manager)
        self.logger = setup_logger(__name__)
        
        # العمال
        self.generation_worker: Optional[ReportGenerationWorker] = None
        self.export_worker: Optional[ReportExportWorker] = None
        
        # البيانات الحالية
        self.current_report_data = None
        self.current_report_type = None
        
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        self.setup_shortcuts()
        self.load_initial_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("نظام التقارير - إدارة المخزون والمبيعات")
        self.setMinimumSize(1400, 900)
        
        # إعداد القوائم
        self.setup_menus()
        
        # إعداد شريط الأدوات
        self.setup_toolbar()
        
        # الويدجت المركزي
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # الجانب الأيسر - فلاتر التقارير
        left_panel = self.create_filters_panel()
        main_layout.addWidget(left_panel, 1)
        
        # الجانب الأيمن - عرض التقارير
        right_panel = self.create_reports_panel()
        main_layout.addWidget(right_panel, 3)
        
        # شريط الحالة
        self.setup_status_bar()
    
    def setup_menus(self):
        """إعداد القوائم"""
        menubar = self.menuBar()
        
        # قائمة الملف
        file_menu = menubar.addMenu("ملف")
        
        # تصدير
        export_action = QAction("تصدير التقرير", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self.export_current_report)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # طباعة
        print_action = QAction("طباعة", self)
        print_action.setShortcut("Ctrl+P")
        print_action.triggered.connect(self.print_current_report)
        file_menu.addAction(print_action)
        
        file_menu.addSeparator()
        
        # إغلاق
        close_action = QAction("إغلاق", self)
        close_action.setShortcut("Ctrl+Q")
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        
        # قائمة التقارير
        reports_menu = menubar.addMenu("التقارير")
        
        # تقارير المبيعات
        sales_action = QAction("تقارير المبيعات", self)
        sales_action.triggered.connect(lambda: self.select_report_type(ReportType.SALES_SUMMARY))
        reports_menu.addAction(sales_action)
        
        # تقارير المخزون
        inventory_action = QAction("تقارير المخزون", self)
        inventory_action.triggered.connect(lambda: self.select_report_type(ReportType.INVENTORY_STATUS))
        reports_menu.addAction(inventory_action)
        
        # التقارير المالية
        financial_action = QAction("التقارير المالية", self)
        financial_action.triggered.connect(lambda: self.select_report_type(ReportType.FINANCIAL_SUMMARY))
        reports_menu.addAction(financial_action)
        
        # قائمة المساعدة
        help_menu = menubar.addMenu("مساعدة")
        
        about_action = QAction("حول البرنامج", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = self.addToolBar("الأدوات الرئيسية")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # توليد التقرير
        generate_action = QAction("🔄 توليد التقرير", self)
        generate_action.setShortcut("F5")
        generate_action.triggered.connect(self.generate_report)
        toolbar.addAction(generate_action)
        
        toolbar.addSeparator()
        
        # تصدير
        export_action = QAction("📤 تصدير", self)
        export_action.triggered.connect(self.export_current_report)
        toolbar.addAction(export_action)
        
        # طباعة
        print_action = QAction("🖨️ طباعة", self)
        print_action.triggered.connect(self.print_current_report)
        toolbar.addAction(print_action)
        
        toolbar.addSeparator()
        
        # تحديث
        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
    
    def create_filters_panel(self) -> QWidget:
        """إنشاء لوحة الفلاتر"""
        widget = QWidget()
        widget.setMaximumWidth(350)
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # عنوان اللوحة
        title_label = QLabel("فلاتر التقارير")
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        layout.addWidget(title_label)
        
        # نوع التقرير
        report_type_group = QGroupBox("نوع التقرير")
        report_type_layout = QVBoxLayout(report_type_group)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItem("تقرير المبيعات", ReportType.SALES_SUMMARY)
        self.report_type_combo.addItem("حالة المخزون", ReportType.INVENTORY_STATUS)
        self.report_type_combo.addItem("التقرير المالي", ReportType.FINANCIAL_SUMMARY)
        self.report_type_combo.addItem("تحليل العملاء", ReportType.CUSTOMER_ANALYSIS)
        self.report_type_combo.addItem("تحليل الموردين", ReportType.SUPPLIER_ANALYSIS)
        self.report_type_combo.addItem("أداء المنتجات", ReportType.PRODUCT_PERFORMANCE)
        self.report_type_combo.addItem("الأرباح والخسائر", ReportType.PROFIT_LOSS)
        self.report_type_combo.addItem("حركة المخزون", ReportType.STOCK_MOVEMENT)
        # تقارير المدفوعات الجديدة
        self.report_type_combo.addItem("ملخص المدفوعات", ReportType.PAYMENT_SUMMARY)
        self.report_type_combo.addItem("أعمار الذمم المدينة", ReportType.RECEIVABLES_AGING)
        self.report_type_combo.addItem("أعمار الذمم الدائنة", ReportType.PAYABLES_AGING)
        self.report_type_combo.addItem("التدفق النقدي", ReportType.CASH_FLOW)
        self.report_type_combo.addItem("تحليل المدفوعات", ReportType.PAYMENT_ANALYSIS)
        self.report_type_combo.addItem("تحليل طرق الدفع", ReportType.PAYMENT_METHODS_ANALYSIS)
        report_type_layout.addWidget(self.report_type_combo)
        
        layout.addWidget(report_type_group)
        
        # فترة التقرير
        period_group = QGroupBox("فترة التقرير")
        period_layout = QFormLayout(period_group)
        
        # تاريخ البداية
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        period_layout.addRow("من تاريخ:", self.start_date_edit)
        
        # تاريخ النهاية
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        period_layout.addRow("إلى تاريخ:", self.end_date_edit)
        
        # فترات سريعة
        quick_periods_layout = QHBoxLayout()
        
        self.today_button = QPushButton("اليوم")
        self.today_button.clicked.connect(lambda: self.set_quick_period(0))
        quick_periods_layout.addWidget(self.today_button)
        
        self.week_button = QPushButton("أسبوع")
        self.week_button.clicked.connect(lambda: self.set_quick_period(7))
        quick_periods_layout.addWidget(self.week_button)
        
        self.month_button = QPushButton("شهر")
        self.month_button.clicked.connect(lambda: self.set_quick_period(30))
        quick_periods_layout.addWidget(self.month_button)
        
        period_layout.addRow("فترات سريعة:", quick_periods_layout)
        
        layout.addWidget(period_group)
        
        # فلاتر إضافية
        additional_group = QGroupBox("فلاتر إضافية")
        additional_layout = QFormLayout(additional_group)
        
        # العميل
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        additional_layout.addRow("العميل:", self.customer_combo)
        
        # المنتج
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        additional_layout.addRow("المنتج:", self.product_combo)
        
        # الفئة
        self.category_combo = QComboBox()
        additional_layout.addRow("الفئة:", self.category_combo)
        
        # طريقة الدفع
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItem("الكل", None)
        self.payment_method_combo.addItem("نقدي", "CASH")
        self.payment_method_combo.addItem("بطاقة ائتمان", "CREDIT_CARD")
        self.payment_method_combo.addItem("تحويل بنكي", "BANK_TRANSFER")
        self.payment_method_combo.addItem("شيك", "CHECK")
        self.payment_method_combo.addItem("آجل", "DEFERRED")
        additional_layout.addRow("طريقة الدفع:", self.payment_method_combo)
        
        # نوع المدفوعات (للتقارير المالية)
        self.payment_type_combo = QComboBox()
        self.payment_type_combo.addItem("الكل", None)
        self.payment_type_combo.addItem("مدفوعات العملاء", "CUSTOMER_PAYMENT")
        self.payment_type_combo.addItem("مدفوعات الموردين", "SUPPLIER_PAYMENT")
        self.payment_type_combo.addItem("مصروفات", "EXPENSE")
        self.payment_type_combo.addItem("إيرادات", "INCOME")
        self.payment_type_combo.addItem("مردودات", "REFUND")
        additional_layout.addRow("نوع المدفوعات:", self.payment_type_combo)
        
        # حالة المدفوعات
        self.payment_status_combo = QComboBox()
        self.payment_status_combo.addItem("الكل", None)
        self.payment_status_combo.addItem("مكتملة", "COMPLETED")
        self.payment_status_combo.addItem("معلقة", "PENDING")
        self.payment_status_combo.addItem("ملغية", "CANCELLED")
        self.payment_status_combo.addItem("مرفوضة", "REJECTED")
        additional_layout.addRow("حالة المدفوعات:", self.payment_status_combo)
        
        # نوع الحساب (للتقارير المحاسبية)
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItem("الكل", None)
        self.account_type_combo.addItem("ذمم مدينة", "RECEIVABLE")
        self.account_type_combo.addItem("ذمم دائنة", "PAYABLE")
        additional_layout.addRow("نوع الحساب:", self.account_type_combo)
        
        layout.addWidget(additional_group)
        
        # خيارات العرض
        display_group = QGroupBox("خيارات العرض")
        display_layout = QVBoxLayout(display_group)
        
        self.show_charts_checkbox = QCheckBox("عرض الرسوم البيانية")
        self.show_charts_checkbox.setChecked(True)
        display_layout.addWidget(self.show_charts_checkbox)
        
        self.show_details_checkbox = QCheckBox("عرض التفاصيل")
        self.show_details_checkbox.setChecked(True)
        display_layout.addWidget(self.show_details_checkbox)
        
        self.group_by_combo = QComboBox()
        self.group_by_combo.addItem("بدون تجميع", None)
        self.group_by_combo.addItem("حسب اليوم", "day")
        self.group_by_combo.addItem("حسب الأسبوع", "week")
        self.group_by_combo.addItem("حسب الشهر", "month")
        display_layout.addWidget(QLabel("تجميع البيانات:"))
        display_layout.addWidget(self.group_by_combo)
        
        layout.addWidget(display_group)
        
        # أزرار العمليات
        buttons_layout = QVBoxLayout()
        
        self.generate_button = QPushButton("🔄 توليد التقرير")
        self.generate_button.setMinimumHeight(40)
        self.generate_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        buttons_layout.addWidget(self.generate_button)
        
        self.clear_filters_button = QPushButton("🗑️ مسح الفلاتر")
        self.clear_filters_button.setMinimumHeight(35)
        buttons_layout.addWidget(self.clear_filters_button)
        
        layout.addLayout(buttons_layout)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        return widget
    
    def create_reports_panel(self) -> QWidget:
        """إنشاء لوحة عرض التقارير"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # شريط العنوان
        header_layout = QHBoxLayout()
        
        self.report_title_label = QLabel("اختر نوع التقرير وانقر على 'توليد التقرير'")
        self.report_title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        header_layout.addWidget(self.report_title_label)
        
        header_layout.addStretch()
        
        # أزرار التصدير
        export_buttons_layout = QHBoxLayout()
        
        self.export_pdf_button = QPushButton("📄 PDF")
        self.export_pdf_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_pdf_button)
        
        self.export_excel_button = QPushButton("📊 Excel")
        self.export_excel_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_excel_button)
        
        self.export_csv_button = QPushButton("📋 CSV")
        self.export_csv_button.setEnabled(False)
        export_buttons_layout.addWidget(self.export_csv_button)
        
        header_layout.addLayout(export_buttons_layout)
        
        layout.addLayout(header_layout)
        
        # منطقة المحتوى
        self.content_stack = QStackedWidget()
        
        # صفحة البداية
        welcome_page = self.create_welcome_page()
        self.content_stack.addWidget(welcome_page)
        
        # صفحة التقرير
        report_page = self.create_report_page()
        self.content_stack.addWidget(report_page)
        
        layout.addWidget(self.content_stack)
        
        return widget
    
    def create_welcome_page(self) -> QWidget:
        """إنشاء صفحة الترحيب"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        # أيقونة كبيرة
        icon_label = QLabel("📊")
        icon_label.setStyleSheet("font-size: 120px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        # نص الترحيب
        welcome_label = QLabel("مرحباً بك في نظام التقارير")
        welcome_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #34495e;
            margin: 20px;
        """)
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # تعليمات
        instructions_label = QLabel("""
        <div style="text-align: center; line-height: 1.6;">
            <p style="font-size: 16px; color: #7f8c8d;">
                اختر نوع التقرير من القائمة الجانبية<br>
                حدد الفترة الزمنية والفلاتر المطلوبة<br>
                انقر على "توليد التقرير" لعرض النتائج
            </p>
        </div>
        """)
        instructions_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions_label)
        
        # إحصائيات سريعة
        stats_frame = QFrame()
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 20px;
            }
        """)
        stats_layout = QGridLayout(stats_frame)
        
        # إجمالي المبيعات اليوم
        today_sales_label = QLabel("مبيعات اليوم")
        today_sales_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(today_sales_label, 0, 0)
        
        self.today_sales_value = QLabel("0.00 دج")
        self.today_sales_value.setStyleSheet("font-size: 18px; color: #28a745; font-weight: bold;")
        stats_layout.addWidget(self.today_sales_value, 0, 1)
        
        # عدد الفواتير اليوم
        today_invoices_label = QLabel("فواتير اليوم")
        today_invoices_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(today_invoices_label, 1, 0)
        
        self.today_invoices_value = QLabel("0")
        self.today_invoices_value.setStyleSheet("font-size: 18px; color: #007bff; font-weight: bold;")
        stats_layout.addWidget(self.today_invoices_value, 1, 1)
        
        # المنتجات منخفضة المخزون
        low_stock_label = QLabel("منتجات منخفضة المخزون")
        low_stock_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(low_stock_label, 2, 0)
        
        self.low_stock_value = QLabel("0")
        self.low_stock_value.setStyleSheet("font-size: 18px; color: #dc3545; font-weight: bold;")
        stats_layout.addWidget(self.low_stock_value, 2, 1)
        
        layout.addWidget(stats_frame)
        
        return widget
    
    def create_report_page(self) -> QWidget:
        """إنشاء صفحة التقرير"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # تبويبات التقرير
        self.report_tabs = QTabWidget()
        
        # تبويب الجدول
        table_tab = QWidget()
        table_layout = QVBoxLayout(table_tab)
        
        self.report_table = QTableWidget()
        self.report_table.setAlternatingRowColors(True)
        self.report_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table_layout.addWidget(self.report_table)
        
        self.report_tabs.addTab(table_tab, "📋 الجدول")
        
        # تبويب الرسوم البيانية
        charts_tab = QWidget()
        charts_layout = QVBoxLayout(charts_tab)
        
        self.chart_view = QChartView()
        charts_layout.addWidget(self.chart_view)
        
        self.report_tabs.addTab(charts_tab, "📊 الرسوم البيانية")
        
        # تبويب الملخص
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        summary_layout.addWidget(self.summary_text)
        
        self.report_tabs.addTab(summary_tab, "📄 الملخص")
        
        layout.addWidget(self.report_tabs)
        
        return widget
    
    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        status_bar = self.statusBar()
        
        # معلومات التقرير الحالي
        self.report_info_label = QLabel("جاهز")
        status_bar.addWidget(self.report_info_label)
        
        status_bar.addPermanentWidget(QLabel(""))
        
        # الوقت الحالي
        self.time_label = QLabel()
        self.update_time()
        status_bar.addPermanentWidget(self.time_label)
        
        # تحديث الوقت كل دقيقة
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(60000)  # كل دقيقة
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        # أزرار الفلاتر
        self.generate_button.clicked.connect(self.generate_report)
        self.clear_filters_button.clicked.connect(self.clear_filters)
        
        # أزرار التصدير
        self.export_pdf_button.clicked.connect(lambda: self.export_report(ExportFormat.PDF))
        self.export_excel_button.clicked.connect(lambda: self.export_report(ExportFormat.EXCEL))
        self.export_csv_button.clicked.connect(lambda: self.export_report(ExportFormat.CSV))
        
        # تغيير نوع التقرير
        self.report_type_combo.currentTextChanged.connect(self.on_report_type_changed)
        
        # تغيير خيارات العرض
        self.show_charts_checkbox.toggled.connect(self.update_report_display)
        self.show_details_checkbox.toggled.connect(self.update_report_display)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # F5 - توليد التقرير
        generate_shortcut = QShortcut(QKeySequence("F5"), self)
        generate_shortcut.activated.connect(self.generate_report)
        
        # Ctrl+E - تصدير
        export_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        export_shortcut.activated.connect(self.export_current_report)
        
        # Ctrl+P - طباعة
        print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        print_shortcut.activated.connect(self.print_current_report)
        
        # Ctrl+R - تحديث
        refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        refresh_shortcut.activated.connect(self.refresh_data)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #007bff;
                color: white;
                border-radius: 4px;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                border: 2px solid #ced4da;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border-color: #007bff;
            }
            
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e9ecef;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e9ecef;
            }
            
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: 1px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px 16px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                font-family: 'Courier New', monospace;
            }
        """)
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        try:
            # تحميل العملاء
            # customers = self.customer_manager.get_all_customers()
            self.customer_combo.clear()
            self.customer_combo.addItem("جميع العملاء", None)
            # for customer in customers:
            #     if customer.is_active:
            #         self.customer_combo.addItem(customer.name, customer.id)
            
            # تحميل المنتجات
            # products = self.product_manager.get_all_products()
            self.product_combo.clear()
            self.product_combo.addItem("جميع المنتجات", None)
            # for product in products:
            #     if product.is_active:
            #         self.product_combo.addItem(product.name, product.id)
            
            # تحميل الفئات
            # categories = self.category_manager.get_all_categories()
            self.category_combo.clear()
            self.category_combo.addItem("جميع الفئات", None)
            # for category in categories:
            #     if category.is_active:
            #         self.category_combo.addItem(category.name, category.id)
            
            # تحديث الإحصائيات السريعة
            self.update_quick_stats()
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل البيانات الأولية: {str(e)}")
    
    def update_quick_stats(self):
        """تحديث الإحصائيات السريعة"""
        try:
            today = date.today()
            
            # مبيعات اليوم
            today_sales = 0.0  # يمكن جلبها من قاعدة البيانات
            self.today_sales_value.setText(f"{today_sales:.2f} دج")
            
            # فواتير اليوم
            today_invoices = 0  # يمكن جلبها من قاعدة البيانات
            self.today_invoices_value.setText(str(today_invoices))
            
            # المنتجات منخفضة المخزون
            low_stock_count = 0  # يمكن جلبها من قاعدة البيانات
            self.low_stock_value.setText(str(low_stock_count))
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث الإحصائيات السريعة: {str(e)}")
    
    def update_time(self):
        """تحديث الوقت في شريط الحالة"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.time_label.setText(current_time)
    
    def set_quick_period(self, days: int):
        """تعيين فترة سريعة"""
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-days)
        
        self.start_date_edit.setDate(start_date)
        self.end_date_edit.setDate(end_date)
    
    def select_report_type(self, report_type: ReportType):
        """اختيار نوع التقرير"""
        for i in range(self.report_type_combo.count()):
            if self.report_type_combo.itemData(i) == report_type:
                self.report_type_combo.setCurrentIndex(i)
                break
    
    def on_report_type_changed(self):
        """معالجة تغيير نوع التقرير"""
        report_type = self.report_type_combo.currentData()
        
        # تحديث عنوان التقرير
        report_name = self.report_type_combo.currentText()
        self.report_title_label.setText(f"تقرير: {report_name}")
        
        # تحديث الفلاتر المتاحة حسب نوع التقرير
        self.update_available_filters(report_type)
    
    def update_available_filters(self, report_type: ReportType):
        """تحديث الفلاتر المتاحة حسب نوع التقرير"""
        # إخفاء/إظهار الفلاتر حسب نوع التقرير
        if report_type == ReportType.SALES_SUMMARY:
            self.customer_combo.setEnabled(True)
            self.product_combo.setEnabled(True)
            self.payment_method_combo.setEnabled(True)
            self.payment_type_combo.setEnabled(False)
            self.payment_status_combo.setEnabled(False)
            self.account_type_combo.setEnabled(False)
        elif report_type == ReportType.INVENTORY_STATUS:
            self.customer_combo.setEnabled(False)
            self.product_combo.setEnabled(True)
            self.payment_method_combo.setEnabled(False)
            self.payment_type_combo.setEnabled(False)
            self.payment_status_combo.setEnabled(False)
            self.account_type_combo.setEnabled(False)
        elif report_type == ReportType.FINANCIAL_SUMMARY:
            self.customer_combo.setEnabled(True)
            self.product_combo.setEnabled(False)
            self.payment_method_combo.setEnabled(True)
            self.payment_type_combo.setEnabled(True)
            self.payment_status_combo.setEnabled(True)
            self.account_type_combo.setEnabled(False)
        # تقارير المدفوعات
        elif report_type in [ReportType.PAYMENT_SUMMARY, ReportType.PAYMENT_ANALYSIS, ReportType.PAYMENT_METHODS_ANALYSIS]:
            self.customer_combo.setEnabled(True)
            self.product_combo.setEnabled(False)
            self.payment_method_combo.setEnabled(True)
            self.payment_type_combo.setEnabled(True)
            self.payment_status_combo.setEnabled(True)
            self.account_type_combo.setEnabled(False)
        elif report_type in [ReportType.RECEIVABLES_AGING, ReportType.PAYABLES_AGING]:
            self.customer_combo.setEnabled(True)
            self.product_combo.setEnabled(False)
            self.payment_method_combo.setEnabled(False)
            self.payment_type_combo.setEnabled(False)
            self.payment_status_combo.setEnabled(False)
            self.account_type_combo.setEnabled(True)
        elif report_type == ReportType.CASH_FLOW:
            self.customer_combo.setEnabled(False)
            self.product_combo.setEnabled(False)
            self.payment_method_combo.setEnabled(True)
            self.payment_type_combo.setEnabled(True)
            self.payment_status_combo.setEnabled(True)
            self.account_type_combo.setEnabled(False)
        else:
            # تقارير أخرى
            self.customer_combo.setEnabled(True)
            self.product_combo.setEnabled(True)
            self.payment_method_combo.setEnabled(True)
            self.payment_type_combo.setEnabled(False)
            self.payment_status_combo.setEnabled(False)
            self.account_type_combo.setEnabled(False)
    
    def clear_filters(self):
        """مسح جميع الفلاتر"""
        # إعادة تعيين التواريخ
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.end_date_edit.setDate(QDate.currentDate())
        
        # إعادة تعيين الكومبوبوكسات
        self.customer_combo.setCurrentIndex(0)
        self.product_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.payment_method_combo.setCurrentIndex(0)
        self.payment_type_combo.setCurrentIndex(0)
        self.payment_status_combo.setCurrentIndex(0)
        self.account_type_combo.setCurrentIndex(0)
        self.group_by_combo.setCurrentIndex(0)
        
        # إعادة تعيين الخيارات
        self.show_charts_checkbox.setChecked(True)
        self.show_details_checkbox.setChecked(True)
    
    def generate_report(self):
        """توليد التقرير"""
        try:
            # التحقق من صحة البيانات
            if self.start_date_edit.date() > self.end_date_edit.date():
                QMessageBox.warning(self, "خطأ", "تاريخ البداية يجب أن يكون قبل تاريخ النهاية")
                return
            
            # إعداد الفلاتر
            filters = ReportFilter(
                start_date=self.start_date_edit.date().toPython(),
                end_date=self.end_date_edit.date().toPython(),
                customer_id=self.customer_combo.currentData(),
                product_id=self.product_combo.currentData(),
                category_id=self.category_combo.currentData(),
                payment_method=self.payment_method_combo.currentData(),
                payment_type=self.payment_type_combo.currentData(),
                payment_status=self.payment_status_combo.currentData(),
                account_type=self.account_type_combo.currentData(),
                group_by=self.group_by_combo.currentData()
            )
            
            report_type = self.report_type_combo.currentData()
            
            # تعطيل الواجهة أثناء التوليد
            self.set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            
            # بدء توليد التقرير في خيط منفصل
            self.generation_worker = ReportGenerationWorker(
                self.reports_service, 
                report_type, 
                filters
            )
            self.generation_worker.report_generated.connect(self.on_report_generated)
            self.generation_worker.progress_updated.connect(self.progress_bar.setValue)
            self.generation_worker.error_occurred.connect(self.on_generation_error)
            self.generation_worker.start()
            
            # تحديث شريط الحالة
            self.report_info_label.setText("جاري توليد التقرير...")
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد التقرير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في توليد التقرير: {str(e)}")
            self.set_ui_enabled(True)
            self.progress_bar.setVisible(False)
    
    def on_report_generated(self, report_data):
        """معالجة اكتمال توليد التقرير"""
        try:
            self.current_report_data = report_data
            self.current_report_type = self.report_type_combo.currentData()
            
            # عرض التقرير
            self.display_report(report_data)
            
            # تفعيل أزرار التصدير
            self.export_pdf_button.setEnabled(True)
            self.export_excel_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)
            
            # تحديث شريط الحالة
            self.report_info_label.setText(f"تم توليد التقرير - {len(report_data.data)} عنصر")
            
            # التبديل إلى صفحة التقرير
            self.content_stack.setCurrentIndex(1)
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض التقرير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في عرض التقرير: {str(e)}")
        finally:
            self.set_ui_enabled(True)
            self.progress_bar.setVisible(False)
    
    def on_generation_error(self, error_message: str):
        """معالجة خطأ في توليد التقرير"""
        QMessageBox.critical(self, "خطأ", f"فشل في توليد التقرير: {error_message}")
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.report_info_label.setText("جاهز")
    
    def display_report(self, report_data):
        """عرض التقرير"""
        try:
            # عرض الجدول
            self.display_table(report_data)
            
            # عرض الرسوم البيانية
            if self.show_charts_checkbox.isChecked():
                self.display_charts(report_data)
            
            # عرض الملخص
            self.display_summary(report_data)
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض التقرير: {str(e)}")
    
    def display_table(self, report_data):
        """عرض جدول التقرير"""
        try:
            data = report_data.data
            headers = report_data.headers
            
            # إعداد الجدول
            self.report_table.setRowCount(len(data))
            self.report_table.setColumnCount(len(headers))
            self.report_table.setHorizontalHeaderLabels(headers)
            
            # ملء البيانات
            for row, item in enumerate(data):
                for col, header in enumerate(headers):
                    value = item.get(header, "")
                    if isinstance(value, (int, float, Decimal)):
                        value = f"{value:.2f}" if isinstance(value, (float, Decimal)) else str(value)
                    
                    table_item = QTableWidgetItem(str(value))
                    self.report_table.setItem(row, col, table_item)
            
            # تحسين عرض الأعمدة
            self.report_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض الجدول: {str(e)}")
    
    def display_charts(self, report_data):
        """عرض الرسوم البيانية"""
        try:
            # إنشاء رسم بياني بسيط
            chart = QChart()
            chart.setTitle(report_data.title)
            
            # رسم دائري للمبيعات حسب المنتج (مثال)
            if self.current_report_type == ReportType.SALES_SUMMARY:
                series = QPieSeries()
                
                # تجميع البيانات
                product_sales = {}
                for item in report_data.data:
                    product = item.get('المنتج', 'غير محدد')
                    amount = float(item.get('المبلغ', 0))
                    product_sales[product] = product_sales.get(product, 0) + amount
                
                # إضافة البيانات للرسم
                for product, amount in list(product_sales.items())[:10]:  # أول 10 منتجات
                    series.append(product, amount)
                
                chart.addSeries(series)
            
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض الرسوم البيانية: {str(e)}")
    
    def display_summary(self, report_data):
        """عرض ملخص التقرير"""
        try:
            summary_text = f"""
            <h2>{report_data.title}</h2>
            <p><strong>الفترة:</strong> من {self.start_date_edit.date().toString()} إلى {self.end_date_edit.date().toString()}</p>
            <p><strong>عدد العناصر:</strong> {len(report_data.data)}</p>
            <p><strong>تاريخ التوليد:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <h3>الملخص الإحصائي:</h3>
            """
            
            # إضافة إحصائيات حسب نوع التقرير
            if self.current_report_type == ReportType.SALES_SUMMARY:
                total_sales = sum(float(item.get('المبلغ', 0)) for item in report_data.data)
                total_quantity = sum(int(item.get('الكمية', 0)) for item in report_data.data)
                
                summary_text += f"""
                <ul>
                    <li><strong>إجمالي المبيعات:</strong> {total_sales:.2f} دج</li>
                    <li><strong>إجمالي الكمية:</strong> {total_quantity}</li>
                    <li><strong>متوسط قيمة الفاتورة:</strong> {total_sales/len(report_data.data) if report_data.data else 0:.2f} دج</li>
                </ul>
                """
            
            self.summary_text.setHtml(summary_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض الملخص: {str(e)}")
    
    def update_report_display(self):
        """تحديث عرض التقرير"""
        if self.current_report_data:
            self.display_report(self.current_report_data)
    
    def export_current_report(self):
        """تصدير التقرير الحالي"""
        if not self.current_report_data:
            QMessageBox.warning(self, "تحذير", "لا يوجد تقرير لتصديره")
            return
        
        # عرض نافذة اختيار نوع التصدير
        dialog = QDialog(self)
        dialog.setWindowTitle("تصدير التقرير")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # اختيار نوع التصدير
        format_group = QGroupBox("نوع التصدير")
        format_layout = QVBoxLayout(format_group)
        
        pdf_radio = QRadioButton("PDF")
        pdf_radio.setChecked(True)
        format_layout.addWidget(pdf_radio)
        
        excel_radio = QRadioButton("Excel")
        format_layout.addWidget(excel_radio)
        
        csv_radio = QRadioButton("CSV")
        format_layout.addWidget(csv_radio)
        
        layout.addWidget(format_group)
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        export_button = QPushButton("تصدير")
        export_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(export_button)
        
        cancel_button = QPushButton("إلغاء")
        cancel_button.clicked.connect(dialog.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        
        if dialog.exec() == QDialog.Accepted:
            # تحديد نوع التصدير
            if pdf_radio.isChecked():
                self.export_report(ExportFormat.PDF)
            elif excel_radio.isChecked():
                self.export_report(ExportFormat.EXCEL)
            elif csv_radio.isChecked():
                self.export_report(ExportFormat.CSV)
    
    def export_report(self, export_format: ExportFormat):
        """تصدير التقرير"""
        if not self.current_report_data:
            QMessageBox.warning(self, "تحذير", "لا يوجد تقرير لتصديره")
            return
        
        try:
            # اختيار مسار الحفظ
            format_extensions = {
                ExportFormat.PDF: "pdf",
                ExportFormat.EXCEL: "xlsx",
                ExportFormat.CSV: "csv"
            }
            
            extension = format_extensions.get(export_format, "txt")
            filter_text = f"{extension.upper()} Files (*.{extension})"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "حفظ التقرير",
                f"تقرير_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}",
                filter_text
            )
            
            if not file_path:
                return
            
            # تعطيل الواجهة أثناء التصدير
            self.set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            
            # بدء التصدير في خيط منفصل
            self.export_worker = ReportExportWorker(
                self.reports_service,
                self.current_report_data,
                export_format,
                file_path
            )
            self.export_worker.export_completed.connect(self.on_export_completed)
            self.export_worker.progress_updated.connect(self.progress_bar.setValue)
            self.export_worker.error_occurred.connect(self.on_export_error)
            self.export_worker.start()
            
            # تحديث شريط الحالة
            self.report_info_label.setText("جاري تصدير التقرير...")
            
        except Exception as e:
            self.logger.error(f"خطأ في تصدير التقرير: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تصدير التقرير: {str(e)}")
            self.set_ui_enabled(True)
            self.progress_bar.setVisible(False)
    
    def on_export_completed(self, file_path: str):
        """معالجة اكتمال التصدير"""
        QMessageBox.information(
            self, 
            "نجح", 
            f"تم تصدير التقرير بنجاح إلى:\n{file_path}"
        )
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.report_info_label.setText("تم التصدير بنجاح")
    
    def on_export_error(self, error_message: str):
        """معالجة خطأ في التصدير"""
        QMessageBox.critical(self, "خطأ", f"فشل في تصدير التقرير: {error_message}")
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        self.report_info_label.setText("جاهز")
    
    def print_current_report(self):
        """طباعة التقرير الحالي"""
        if not self.current_report_data:
            QMessageBox.warning(self, "تحذير", "لا يوجد تقرير للطباعة")
            return
        
        # هنا يمكن إضافة كود الطباعة
        QMessageBox.information(self, "معلومات", "سيتم إضافة وظيفة الطباعة قريباً")
    
    def refresh_data(self):
        """تحديث البيانات"""
        self.load_initial_data()
        self.update_quick_stats()
        QMessageBox.information(self, "تحديث", "تم تحديث البيانات بنجاح")
    
    def show_about(self):
        """عرض معلومات البرنامج"""
        QMessageBox.about(
            self,
            "حول البرنامج",
            """
            <h3>نظام إدارة المخزون والمبيعات</h3>
            <p><strong>الإصدار:</strong> 1.0.0</p>
            <p><strong>المطور:</strong> فريق التطوير</p>
            <p><strong>الوصف:</strong> نظام شامل لإدارة المخزون والمبيعات مع نظام تقارير متقدم</p>
            <p><strong>الميزات:</strong></p>
            <ul>
                <li>إدارة المنتجات والمخزون</li>
                <li>نظام نقاط البيع (POS)</li>
                <li>إدارة العملاء والموردين</li>
                <li>تقارير شاملة مع إمكانية التصدير</li>
                <li>واجهة عربية سهلة الاستخدام</li>
            </ul>
            """
        )
    
    def set_ui_enabled(self, enabled: bool):
        """تفعيل/تعطيل عناصر الواجهة"""
        self.generate_button.setEnabled(enabled)
        self.clear_filters_button.setEnabled(enabled)
        self.export_pdf_button.setEnabled(enabled and self.current_report_data is not None)
        self.export_excel_button.setEnabled(enabled and self.current_report_data is not None)
        self.export_csv_button.setEnabled(enabled and self.current_report_data is not None)
        
        # فلاتر
        self.report_type_combo.setEnabled(enabled)
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)
        self.customer_combo.setEnabled(enabled)
        self.product_combo.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)
        self.payment_method_combo.setEnabled(enabled)
        self.group_by_combo.setEnabled(enabled)
    
    def set_report_type(self, report_type: ReportType):
        """تعيين نوع التقرير"""
        try:
            # البحث عن الفهرس المناسب في الكومبوبوكس
            for i in range(self.report_type_combo.count()):
                if self.report_type_combo.itemData(i) == report_type:
                    self.report_type_combo.setCurrentIndex(i)
                    break
            
            # تحديث الفلاتر
            self.update_available_filters(report_type)
            
        except Exception as e:
            self.logger.error(f"خطأ في تعيين نوع التقرير: {str(e)}")
    
    def set_filters(self, filters: ReportFilter):
        """تعيين فلاتر التقرير"""
        try:
            if filters.start_date:
                self.start_date_edit.setDate(QDate.fromString(filters.start_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
            
            if filters.end_date:
                self.end_date_edit.setDate(QDate.fromString(filters.end_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
            
            if filters.customer_id:
                # البحث عن العميل في الكومبوبوكس
                for i in range(self.customer_combo.count()):
                    if self.customer_combo.itemData(i) == filters.customer_id:
                        self.customer_combo.setCurrentIndex(i)
                        break
            
            if filters.product_id:
                # البحث عن المنتج في الكومبوبوكس
                for i in range(self.product_combo.count()):
                    if self.product_combo.itemData(i) == filters.product_id:
                        self.product_combo.setCurrentIndex(i)
                        break
            
            if filters.category_id:
                # البحث عن الفئة في الكومبوبوكس
                for i in range(self.category_combo.count()):
                    if self.category_combo.itemData(i) == filters.category_id:
                        self.category_combo.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            self.logger.error(f"خطأ في تعيين فلاتر التقرير: {str(e)}")
    
    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        # إيقاف العمال
        if self.generation_worker and self.generation_worker.isRunning():
            self.generation_worker.terminate()
            self.generation_worker.wait()
        
        if self.export_worker and self.export_worker.isRunning():
            self.export_worker.terminate()
            self.export_worker.wait()
        
        # إيقاف المؤقت
        if hasattr(self, 'time_timer'):
            self.time_timer.stop()
        
        super().closeEvent(event)


# اختبار النافذة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # إعداد الخط العربي
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # إعداد اتجاه النص
    app.setLayoutDirection(Qt.RightToLeft)
    
    # إنشاء قاعدة بيانات وهمية للاختبار
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager(":memory:")
    
    window = ReportsWindow(db)
    window.show()
    
    sys.exit(app.exec())
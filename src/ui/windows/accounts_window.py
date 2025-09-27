#!/usr/bin/env python3
"""
نافذة إدارة الحسابات المدينة والدائنة - Accounts Management Window
واجهة شاملة لإدارة الحسابات المدينة والدائنة مع دعم اللغة العربية
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

from ...core.database_manager import DatabaseManager
from ...services.payment_service import PaymentService
from ...models.payment import PaymentType, PaymentMethod, PaymentStatus, AccountType
from ...utils.logger import setup_logger
from ..dialogs.payment_dialog import PaymentDialog


class AccountsRefreshWorker(QThread):
    """عامل تحديث بيانات الحسابات"""
    data_loaded = Signal(dict)  # {receivables: [], payables: [], schedules: []}
    error_occurred = Signal(str)
    
    def __init__(self, payment_service: PaymentService):
        super().__init__()
        self.payment_service = payment_service
    
    def run(self):
        try:
            receivables = self.payment_service.get_accounts_receivable()
            payables = self.payment_service.get_accounts_payable()
            schedules = self.payment_service.get_payment_schedules()
            
            self.data_loaded.emit({
                'receivables': receivables,
                'payables': payables,
                'schedules': schedules
            })
        except Exception as e:
            self.error_occurred.emit(str(e))


class AccountsWindow(QMainWindow):
    """نافذة إدارة الحسابات المدينة والدائنة"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.payment_service = PaymentService(db_manager)
        self.logger = setup_logger(__name__)
        
        self.setWindowTitle("إدارة الحسابات المدينة والدائنة")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # إعداد الواجهة
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        
        # تحديث البيانات
        self.refresh_data()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # التخطيط الرئيسي
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # شريط الأدوات
        self.setup_toolbar()
        
        # التبويبات الرئيسية
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # تبويب الحسابات المدينة
        self.setup_receivables_tab()
        
        # تبويب الحسابات الدائنة
        self.setup_payables_tab()
        
        # تبويب جدولة المدفوعات
        self.setup_schedules_tab()
        
        # تبويب التقارير
        self.setup_reports_tab()
        
        # شريط الحالة
        self.setup_status_bar()
    
    def setup_toolbar(self):
        """إعداد شريط الأدوات"""
        toolbar = self.addToolBar("الأدوات الرئيسية")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # زر إضافة دفعة جديدة
        add_payment_action = QAction("إضافة دفعة", self)
        add_payment_action.triggered.connect(self.add_payment)
        toolbar.addAction(add_payment_action)
        
        toolbar.addSeparator()
        
        # زر تحديث البيانات
        refresh_action = QAction("تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)
        
        # زر تصدير التقارير
        export_action = QAction("تصدير", self)
        export_action.triggered.connect(self.export_reports)
        toolbar.addAction(export_action)
    
    def setup_receivables_tab(self):
        """إعداد تبويب الحسابات المدينة"""
        receivables_widget = QWidget()
        layout = QVBoxLayout(receivables_widget)
        
        # عنوان القسم
        title_label = QLabel("الحسابات المدينة (المستحقة من العملاء)")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # فلاتر البحث
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.StyledPanel)
        filters_layout = QHBoxLayout(filters_frame)
        
        # بحث بالعميل
        filters_layout.addWidget(QLabel("العميل:"))
        self.receivables_customer_filter = QLineEdit()
        self.receivables_customer_filter.setPlaceholderText("ابحث بالعميل...")
        filters_layout.addWidget(self.receivables_customer_filter)
        
        # فلتر المبلغ
        filters_layout.addWidget(QLabel("المبلغ من:"))
        self.receivables_amount_from = QDoubleSpinBox()
        self.receivables_amount_from.setMaximum(999999.99)
        filters_layout.addWidget(self.receivables_amount_from)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.receivables_amount_to = QDoubleSpinBox()
        self.receivables_amount_to.setMaximum(999999.99)
        self.receivables_amount_to.setValue(999999.99)
        filters_layout.addWidget(self.receivables_amount_to)
        
        # زر البحث
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.filter_receivables)
        filters_layout.addWidget(search_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        # جدول الحسابات المدينة
        self.receivables_table = QTableWidget()
        self.receivables_table.setColumnCount(6)
        self.receivables_table.setHorizontalHeaderLabels([
            "العميل", "الرصيد المستحق", "آخر دفعة", "تاريخ آخر دفعة", "مبلغ آخر دفعة", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.receivables_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.receivables_table.setAlternatingRowColors(True)
        self.receivables_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.receivables_table)
        
        # إجمالي الحسابات المدينة
        self.receivables_total_label = QLabel("إجمالي الحسابات المدينة: 0.00 ج.م")
        self.receivables_total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;")
        layout.addWidget(self.receivables_total_label)
        
        self.tab_widget.addTab(receivables_widget, "الحسابات المدينة")
    
    def setup_payables_tab(self):
        """إعداد تبويب الحسابات الدائنة"""
        payables_widget = QWidget()
        layout = QVBoxLayout(payables_widget)
        
        # عنوان القسم
        title_label = QLabel("الحسابات الدائنة (المستحقة للموردين)")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # فلاتر البحث
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.StyledPanel)
        filters_layout = QHBoxLayout(filters_frame)
        
        # بحث بالمورد
        filters_layout.addWidget(QLabel("المورد:"))
        self.payables_supplier_filter = QLineEdit()
        self.payables_supplier_filter.setPlaceholderText("ابحث بالمورد...")
        filters_layout.addWidget(self.payables_supplier_filter)
        
        # فلتر المبلغ
        filters_layout.addWidget(QLabel("المبلغ من:"))
        self.payables_amount_from = QDoubleSpinBox()
        self.payables_amount_from.setMaximum(999999.99)
        filters_layout.addWidget(self.payables_amount_from)
        
        filters_layout.addWidget(QLabel("إلى:"))
        self.payables_amount_to = QDoubleSpinBox()
        self.payables_amount_to.setMaximum(999999.99)
        self.payables_amount_to.setValue(999999.99)
        filters_layout.addWidget(self.payables_amount_to)
        
        # زر البحث
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.filter_payables)
        filters_layout.addWidget(search_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        # جدول الحسابات الدائنة
        self.payables_table = QTableWidget()
        self.payables_table.setColumnCount(6)
        self.payables_table.setHorizontalHeaderLabels([
            "المورد", "الرصيد المستحق", "آخر دفعة", "تاريخ آخر دفعة", "مبلغ آخر دفعة", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.payables_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.payables_table.setAlternatingRowColors(True)
        self.payables_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.payables_table)
        
        # إجمالي الحسابات الدائنة
        self.payables_total_label = QLabel("إجمالي الحسابات الدائنة: 0.00 ج.م")
        self.payables_total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
        layout.addWidget(self.payables_total_label)
        
        self.tab_widget.addTab(payables_widget, "الحسابات الدائنة")
    
    def setup_schedules_tab(self):
        """إعداد تبويب جدولة المدفوعات"""
        schedules_widget = QWidget()
        layout = QVBoxLayout(schedules_widget)
        
        # عنوان القسم
        title_label = QLabel("جدولة المدفوعات المستقبلية")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # فلاتر البحث
        filters_frame = QFrame()
        filters_frame.setFrameStyle(QFrame.StyledPanel)
        filters_layout = QHBoxLayout(filters_frame)
        
        # فلتر النوع
        filters_layout.addWidget(QLabel("النوع:"))
        self.schedules_type_filter = QComboBox()
        self.schedules_type_filter.addItems(["الكل", "عميل", "مورد"])
        filters_layout.addWidget(self.schedules_type_filter)
        
        # فلتر الحالة
        filters_layout.addWidget(QLabel("الحالة:"))
        self.schedules_status_filter = QComboBox()
        self.schedules_status_filter.addItems(["الكل", "معلق", "مدفوع", "متأخر", "ملغي"])
        filters_layout.addWidget(self.schedules_status_filter)
        
        # فلتر التاريخ
        filters_layout.addWidget(QLabel("من تاريخ:"))
        self.schedules_date_from = QDateEdit()
        self.schedules_date_from.setDate(QDate.currentDate())
        filters_layout.addWidget(self.schedules_date_from)
        
        filters_layout.addWidget(QLabel("إلى تاريخ:"))
        self.schedules_date_to = QDateEdit()
        self.schedules_date_to.setDate(QDate.currentDate().addDays(30))
        filters_layout.addWidget(self.schedules_date_to)
        
        # زر البحث
        search_btn = QPushButton("بحث")
        search_btn.clicked.connect(self.filter_schedules)
        filters_layout.addWidget(search_btn)
        
        filters_layout.addStretch()
        layout.addWidget(filters_frame)
        
        # جدول جدولة المدفوعات
        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(7)
        self.schedules_table.setHorizontalHeaderLabels([
            "النوع", "الاسم", "المبلغ", "تاريخ الاستحقاق", "الحالة", "ملاحظات", "الإجراءات"
        ])
        
        # إعداد الجدول
        header = self.schedules_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.schedules_table.setAlternatingRowColors(True)
        self.schedules_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.schedules_table)
        
        self.tab_widget.addTab(schedules_widget, "جدولة المدفوعات")
    
    def setup_reports_tab(self):
        """إعداد تبويب التقارير"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)
        
        # عنوان القسم
        title_label = QLabel("تقارير الحسابات والمدفوعات")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # أزرار التقارير
        reports_frame = QFrame()
        reports_frame.setFrameStyle(QFrame.StyledPanel)
        reports_layout = QGridLayout(reports_frame)
        
        # تقرير الحسابات المدينة
        receivables_report_btn = QPushButton("تقرير الحسابات المدينة")
        receivables_report_btn.clicked.connect(self.generate_receivables_report)
        reports_layout.addWidget(receivables_report_btn, 0, 0)
        
        # تقرير الحسابات الدائنة
        payables_report_btn = QPushButton("تقرير الحسابات الدائنة")
        payables_report_btn.clicked.connect(self.generate_payables_report)
        reports_layout.addWidget(payables_report_btn, 0, 1)
        
        # تقرير الأعمار
        aging_report_btn = QPushButton("تقرير أعمار الديون")
        aging_report_btn.clicked.connect(self.generate_aging_report)
        reports_layout.addWidget(aging_report_btn, 1, 0)
        
        # تقرير التدفق النقدي
        cashflow_report_btn = QPushButton("تقرير التدفق النقدي")
        cashflow_report_btn.clicked.connect(self.generate_cashflow_report)
        reports_layout.addWidget(cashflow_report_btn, 1, 1)
        
        layout.addWidget(reports_frame)
        
        # منطقة عرض التقارير
        self.reports_text = QTextEdit()
        self.reports_text.setReadOnly(True)
        layout.addWidget(self.reports_text)
        
        self.tab_widget.addTab(reports_widget, "التقارير")
    
    def setup_status_bar(self):
        """إعداد شريط الحالة"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("جاهز")
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def setup_connections(self):
        """إعداد الاتصالات والإشارات"""
        # فلاتر البحث
        self.receivables_customer_filter.textChanged.connect(self.filter_receivables)
        self.payables_supplier_filter.textChanged.connect(self.filter_payables)
        
        # تغيير التبويبات
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
            }
            
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #dee2e6;
            }
            
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
                border-color: #007bff;
                outline: none;
            }
        """)
    
    def refresh_data(self):
        """تحديث جميع البيانات"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # شريط تقدم غير محدد
        self.status_bar.showMessage("جاري تحديث البيانات...")
        
        # تشغيل عامل التحديث
        self.refresh_worker = AccountsRefreshWorker(self.payment_service)
        self.refresh_worker.data_loaded.connect(self.on_data_loaded)
        self.refresh_worker.error_occurred.connect(self.on_error)
        self.refresh_worker.start()
    
    def on_data_loaded(self, data):
        """معالجة البيانات المحدثة"""
        try:
            # تحديث الحسابات المدينة
            self.update_receivables_table(data['receivables'])
            
            # تحديث الحسابات الدائنة
            self.update_payables_table(data['payables'])
            
            # تحديث جدولة المدفوعات
            self.update_schedules_table(data['schedules'])
            
            self.progress_bar.setVisible(False)
            self.status_bar.showMessage("تم تحديث البيانات بنجاح")
            
        except Exception as e:
            self.logger.error(f"خطأ في تحديث البيانات: {e}")
            self.on_error(str(e))
    
    def update_receivables_table(self, receivables):
        """تحديث جدول الحسابات المدينة"""
        self.receivables_table.setRowCount(len(receivables))
        total = Decimal('0')
        
        for row, account in enumerate(receivables):
            # اسم العميل
            self.receivables_table.setItem(row, 0, QTableWidgetItem(str(account.get('customer_name', ''))))
            
            # الرصيد
            balance = Decimal(str(account.get('balance', 0)))
            total += balance
            self.receivables_table.setItem(row, 1, QTableWidgetItem(f"{balance:.2f} ج.م"))
            
            # آخر دفعة
            last_payment = account.get('last_payment_amount', 0)
            self.receivables_table.setItem(row, 2, QTableWidgetItem(f"{last_payment:.2f} ج.م" if last_payment else "لا توجد"))
            
            # تاريخ آخر دفعة
            last_date = account.get('last_payment_date', '')
            self.receivables_table.setItem(row, 3, QTableWidgetItem(str(last_date) if last_date else "لا يوجد"))
            
            # مبلغ آخر دفعة
            self.receivables_table.setItem(row, 4, QTableWidgetItem(f"{last_payment:.2f} ج.م" if last_payment else "0.00 ج.م"))
            
            # أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            pay_btn = QPushButton("دفع")
            pay_btn.clicked.connect(lambda checked, customer_id=account.get('entity_id'): self.make_customer_payment(customer_id))
            actions_layout.addWidget(pay_btn)
            
            self.receivables_table.setCellWidget(row, 5, actions_widget)
        
        # تحديث الإجمالي
        self.receivables_total_label.setText(f"إجمالي الحسابات المدينة: {total:.2f} ج.م")
    
    def update_payables_table(self, payables):
        """تحديث جدول الحسابات الدائنة"""
        self.payables_table.setRowCount(len(payables))
        total = Decimal('0')
        
        for row, account in enumerate(payables):
            # اسم المورد
            self.payables_table.setItem(row, 0, QTableWidgetItem(str(account.get('supplier_name', ''))))
            
            # الرصيد
            balance = Decimal(str(account.get('balance', 0)))
            total += balance
            self.payables_table.setItem(row, 1, QTableWidgetItem(f"{balance:.2f} ج.م"))
            
            # آخر دفعة
            last_payment = account.get('last_payment_amount', 0)
            self.payables_table.setItem(row, 2, QTableWidgetItem(f"{last_payment:.2f} ج.م" if last_payment else "لا توجد"))
            
            # تاريخ آخر دفعة
            last_date = account.get('last_payment_date', '')
            self.payables_table.setItem(row, 3, QTableWidgetItem(str(last_date) if last_date else "لا يوجد"))
            
            # مبلغ آخر دفعة
            self.payables_table.setItem(row, 4, QTableWidgetItem(f"{last_payment:.2f} ج.م" if last_payment else "0.00 ج.م"))
            
            # أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            pay_btn = QPushButton("دفع")
            pay_btn.clicked.connect(lambda checked, supplier_id=account.get('entity_id'): self.make_supplier_payment(supplier_id))
            actions_layout.addWidget(pay_btn)
            
            self.payables_table.setCellWidget(row, 5, actions_widget)
        
        # تحديث الإجمالي
        self.payables_total_label.setText(f"إجمالي الحسابات الدائنة: {total:.2f} ج.م")
    
    def update_schedules_table(self, schedules):
        """تحديث جدول جدولة المدفوعات"""
        self.schedules_table.setRowCount(len(schedules))
        
        for row, schedule in enumerate(schedules):
            # النوع
            entity_type = "عميل" if schedule.get('entity_type') == 'customer' else "مورد"
            self.schedules_table.setItem(row, 0, QTableWidgetItem(entity_type))
            
            # الاسم
            entity_name = schedule.get('entity_name', '')
            self.schedules_table.setItem(row, 1, QTableWidgetItem(str(entity_name)))
            
            # المبلغ
            amount = Decimal(str(schedule.get('amount', 0)))
            self.schedules_table.setItem(row, 2, QTableWidgetItem(f"{amount:.2f} ج.م"))
            
            # تاريخ الاستحقاق
            due_date = schedule.get('due_date', '')
            self.schedules_table.setItem(row, 3, QTableWidgetItem(str(due_date)))
            
            # الحالة
            status_map = {
                'pending': 'معلق',
                'paid': 'مدفوع',
                'overdue': 'متأخر',
                'cancelled': 'ملغي'
            }
            status = status_map.get(schedule.get('status', ''), 'غير معروف')
            self.schedules_table.setItem(row, 4, QTableWidgetItem(status))
            
            # الملاحظات
            notes = schedule.get('notes', '')
            self.schedules_table.setItem(row, 5, QTableWidgetItem(str(notes)))
            
            # أزرار الإجراءات
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 5, 5, 5)
            
            if schedule.get('status') == 'pending':
                pay_btn = QPushButton("دفع")
                pay_btn.clicked.connect(lambda checked, schedule_id=schedule.get('id'): self.pay_schedule(schedule_id))
                actions_layout.addWidget(pay_btn)
                
                cancel_btn = QPushButton("إلغاء")
                cancel_btn.clicked.connect(lambda checked, schedule_id=schedule.get('id'): self.cancel_schedule(schedule_id))
                actions_layout.addWidget(cancel_btn)
            
            self.schedules_table.setCellWidget(row, 6, actions_widget)
    
    def filter_receivables(self):
        """فلترة الحسابات المدينة"""
        # تطبيق الفلاتر على الجدول
        customer_filter = self.receivables_customer_filter.text().lower()
        amount_from = self.receivables_amount_from.value()
        amount_to = self.receivables_amount_to.value()
        
        for row in range(self.receivables_table.rowCount()):
            show_row = True
            
            # فلتر العميل
            if customer_filter:
                customer_name = self.receivables_table.item(row, 0).text().lower()
                if customer_filter not in customer_name:
                    show_row = False
            
            # فلتر المبلغ
            if show_row:
                balance_text = self.receivables_table.item(row, 1).text().replace(' ج.م', '')
                try:
                    balance = float(balance_text)
                    if not (amount_from <= balance <= amount_to):
                        show_row = False
                except ValueError:
                    show_row = False
            
            self.receivables_table.setRowHidden(row, not show_row)
    
    def filter_payables(self):
        """فلترة الحسابات الدائنة"""
        # تطبيق الفلاتر على الجدول
        supplier_filter = self.payables_supplier_filter.text().lower()
        amount_from = self.payables_amount_from.value()
        amount_to = self.payables_amount_to.value()
        
        for row in range(self.payables_table.rowCount()):
            show_row = True
            
            # فلتر المورد
            if supplier_filter:
                supplier_name = self.payables_table.item(row, 0).text().lower()
                if supplier_filter not in supplier_name:
                    show_row = False
            
            # فلتر المبلغ
            if show_row:
                balance_text = self.payables_table.item(row, 1).text().replace(' ج.م', '')
                try:
                    balance = float(balance_text)
                    if not (amount_from <= balance <= amount_to):
                        show_row = False
                except ValueError:
                    show_row = False
            
            self.payables_table.setRowHidden(row, not show_row)
    
    def filter_schedules(self):
        """فلترة جدولة المدفوعات"""
        # تطبيق الفلاتر على الجدول
        type_filter = self.schedules_type_filter.currentText()
        status_filter = self.schedules_status_filter.currentText()
        date_from = self.schedules_date_from.date().toPython()
        date_to = self.schedules_date_to.date().toPython()
        
        for row in range(self.schedules_table.rowCount()):
            show_row = True
            
            # فلتر النوع
            if type_filter != "الكل":
                row_type = self.schedules_table.item(row, 0).text()
                if type_filter != row_type:
                    show_row = False
            
            # فلتر الحالة
            if show_row and status_filter != "الكل":
                row_status = self.schedules_table.item(row, 4).text()
                if status_filter != row_status:
                    show_row = False
            
            # فلتر التاريخ
            if show_row:
                try:
                    due_date_str = self.schedules_table.item(row, 3).text()
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    if not (date_from <= due_date <= date_to):
                        show_row = False
                except (ValueError, AttributeError):
                    show_row = False
            
            self.schedules_table.setRowHidden(row, not show_row)
    
    def add_payment(self):
        """إضافة دفعة جديدة"""
        dialog = PaymentDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()
    
    def make_customer_payment(self, customer_id):
        """إجراء دفعة من عميل"""
        dialog = PaymentDialog(self.db_manager, self, payment_type=PaymentType.CUSTOMER_PAYMENT, entity_id=customer_id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()
    
    def make_supplier_payment(self, supplier_id):
        """إجراء دفعة لمورد"""
        dialog = PaymentDialog(self.db_manager, self, payment_type=PaymentType.SUPPLIER_PAYMENT, entity_id=supplier_id)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_data()
    
    def pay_schedule(self, schedule_id):
        """دفع جدولة مدفوعات"""
        try:
            # الحصول على تفاصيل الجدولة
            schedule = self.payment_service.get_payment_schedule(schedule_id)
            if not schedule:
                QMessageBox.warning(self, "خطأ", "لم يتم العثور على الجدولة المحددة")
                return
            
            # فتح نافذة الدفع
            payment_type = PaymentType.CUSTOMER_PAYMENT if schedule['entity_type'] == 'customer' else PaymentType.SUPPLIER_PAYMENT
            dialog = PaymentDialog(self.db_manager, self, payment_type=payment_type, 
                                 entity_id=schedule['entity_id'], amount=schedule['amount'])
            
            if dialog.exec() == QDialog.Accepted:
                # تحديث حالة الجدولة
                self.payment_service.update_payment_schedule_status(schedule_id, 'paid')
                self.refresh_data()
                
        except Exception as e:
            self.logger.error(f"خطأ في دفع الجدولة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء دفع الجدولة: {str(e)}")
    
    def cancel_schedule(self, schedule_id):
        """إلغاء جدولة مدفوعات"""
        reply = QMessageBox.question(self, "تأكيد الإلغاء", 
                                   "هل أنت متأكد من إلغاء هذه الجدولة؟",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.payment_service.update_payment_schedule_status(schedule_id, 'cancelled')
                self.refresh_data()
            except Exception as e:
                self.logger.error(f"خطأ في إلغاء الجدولة: {e}")
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء إلغاء الجدولة: {str(e)}")
    
    def generate_receivables_report(self):
        """توليد تقرير الحسابات المدينة"""
        try:
            report = self.payment_service.get_payment_summary_report()
            receivables_data = report.get('receivables', [])
            
            report_text = "تقرير الحسابات المدينة\n"
            report_text += "=" * 50 + "\n\n"
            
            total = Decimal('0')
            for account in receivables_data:
                customer_name = account.get('customer_name', 'غير محدد')
                balance = Decimal(str(account.get('balance', 0)))
                total += balance
                
                report_text += f"العميل: {customer_name}\n"
                report_text += f"الرصيد المستحق: {balance:.2f} ج.م\n"
                report_text += "-" * 30 + "\n"
            
            report_text += f"\nإجمالي الحسابات المدينة: {total:.2f} ج.م\n"
            
            self.reports_text.setText(report_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد تقرير الحسابات المدينة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء توليد التقرير: {str(e)}")
    
    def generate_payables_report(self):
        """توليد تقرير الحسابات الدائنة"""
        try:
            report = self.payment_service.get_payment_summary_report()
            payables_data = report.get('payables', [])
            
            report_text = "تقرير الحسابات الدائنة\n"
            report_text += "=" * 50 + "\n\n"
            
            total = Decimal('0')
            for account in payables_data:
                supplier_name = account.get('supplier_name', 'غير محدد')
                balance = Decimal(str(account.get('balance', 0)))
                total += balance
                
                report_text += f"المورد: {supplier_name}\n"
                report_text += f"الرصيد المستحق: {balance:.2f} ج.م\n"
                report_text += "-" * 30 + "\n"
            
            report_text += f"\nإجمالي الحسابات الدائنة: {total:.2f} ج.م\n"
            
            self.reports_text.setText(report_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد تقرير الحسابات الدائنة: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء توليد التقرير: {str(e)}")
    
    def generate_aging_report(self):
        """توليد تقرير أعمار الديون"""
        try:
            aging_report = self.payment_service.get_aging_report()
            
            report_text = "تقرير أعمار الديون\n"
            report_text += "=" * 50 + "\n\n"
            
            for category, accounts in aging_report.items():
                report_text += f"{category}:\n"
                report_text += "-" * 20 + "\n"
                
                for account in accounts:
                    name = account.get('name', 'غير محدد')
                    balance = Decimal(str(account.get('balance', 0)))
                    days = account.get('days_overdue', 0)
                    
                    report_text += f"الاسم: {name}\n"
                    report_text += f"الرصيد: {balance:.2f} ج.م\n"
                    report_text += f"عدد الأيام: {days} يوم\n"
                    report_text += "\n"
                
                report_text += "\n"
            
            self.reports_text.setText(report_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد تقرير أعمار الديون: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء توليد التقرير: {str(e)}")
    
    def generate_cashflow_report(self):
        """توليد تقرير التدفق النقدي"""
        try:
            # الحصول على تقرير التدفق النقدي للشهر الحالي
            start_date = date.today().replace(day=1)
            end_date = date.today()
            
            cashflow_report = self.payment_service.get_cash_flow_report(start_date, end_date)
            
            report_text = f"تقرير التدفق النقدي من {start_date} إلى {end_date}\n"
            report_text += "=" * 60 + "\n\n"
            
            # التدفقات الداخلة
            report_text += "التدفقات الداخلة (من العملاء):\n"
            report_text += "-" * 30 + "\n"
            
            inflows = cashflow_report.get('inflows', [])
            total_inflows = Decimal('0')
            
            for flow in inflows:
                amount = Decimal(str(flow.get('amount', 0)))
                total_inflows += amount
                date_str = flow.get('date', '')
                description = flow.get('description', '')
                
                report_text += f"التاريخ: {date_str}\n"
                report_text += f"المبلغ: {amount:.2f} ج.م\n"
                report_text += f"الوصف: {description}\n"
                report_text += "\n"
            
            report_text += f"إجمالي التدفقات الداخلة: {total_inflows:.2f} ج.م\n\n"
            
            # التدفقات الخارجة
            report_text += "التدفقات الخارجة (للموردين):\n"
            report_text += "-" * 30 + "\n"
            
            outflows = cashflow_report.get('outflows', [])
            total_outflows = Decimal('0')
            
            for flow in outflows:
                amount = Decimal(str(flow.get('amount', 0)))
                total_outflows += amount
                date_str = flow.get('date', '')
                description = flow.get('description', '')
                
                report_text += f"التاريخ: {date_str}\n"
                report_text += f"المبلغ: {amount:.2f} ج.م\n"
                report_text += f"الوصف: {description}\n"
                report_text += "\n"
            
            report_text += f"إجمالي التدفقات الخارجة: {total_outflows:.2f} ج.م\n\n"
            
            # صافي التدفق النقدي
            net_flow = total_inflows - total_outflows
            report_text += f"صافي التدفق النقدي: {net_flow:.2f} ج.م\n"
            
            self.reports_text.setText(report_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في توليد تقرير التدفق النقدي: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء توليد التقرير: {str(e)}")
    
    def export_reports(self):
        """تصدير التقارير"""
        if not self.reports_text.toPlainText().strip():
            QMessageBox.warning(self, "تحذير", "لا يوجد تقرير لتصديره. يرجى توليد تقرير أولاً.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "تصدير التقرير", 
            f"تقرير_الحسابات_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.reports_text.toPlainText())
                
                QMessageBox.information(self, "نجح التصدير", f"تم تصدير التقرير بنجاح إلى:\n{file_path}")
                
            except Exception as e:
                self.logger.error(f"خطأ في تصدير التقرير: {e}")
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء تصدير التقرير: {str(e)}")
    
    def on_tab_changed(self, index):
        """معالجة تغيير التبويب"""
        # يمكن إضافة منطق خاص لكل تبويب هنا
        pass
    
    def on_error(self, error_message):
        """معالجة الأخطاء"""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("حدث خطأ")
        
        self.logger.error(f"خطأ في نافذة الحسابات: {error_message}")
        QMessageBox.critical(self, "خطأ", f"حدث خطأ: {error_message}")
    
    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        # إيقاف أي عمليات جارية
        if hasattr(self, 'refresh_worker') and self.refresh_worker.isRunning():
            self.refresh_worker.terminate()
            self.refresh_worker.wait()
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # إعداد قاعدة البيانات
    db_manager = DatabaseManager()
    
    # إنشاء النافذة
    window = AccountsWindow(db_manager)
    window.show()
    
    sys.exit(app.exec())
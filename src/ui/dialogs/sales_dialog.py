#!/usr/bin/env python3
"""
نافذة فاتورة المبيعات - Sales Dialog
واجهة شاملة لإنشاء وإدارة فواتير المبيعات مع دعم اللغة العربية
"""

import sys
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QTextEdit, QCheckBox, QFrame, QMessageBox, QProgressBar,
    QTabWidget, QWidget, QGroupBox, QDateEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter,
    QScrollArea, QSizePolicy, QApplication, QCompleter, QButtonGroup,
    QRadioButton, QSlider, QDial, QCalendarWidget, QTimeEdit
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QDate, QTime, QStringListModel
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QValidator, QDoubleValidator, QKeySequence, QShortcut

from ...core.database_manager import DatabaseManager
from ...models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from ...models.product import ProductManager
from ...models.customer import CustomerManager
from ...services.sales_service import SalesService
try:
    from ...services.sales_service_enhanced import SalesService as EnhancedSalesService
except Exception:
    EnhancedSalesService = None
from ...utils.logger import setup_logger


class ProductSearchWorker(QThread):
    """عامل البحث عن المنتجات"""
    search_completed = Signal(list)  # List[Product]
    
    def __init__(self, product_manager: ProductManager, search_term: str):
        super().__init__()
        self.product_manager = product_manager
        self.search_term = search_term
    
    def run(self):
        try:
            # البحث بالاسم أو الباركود
            products = []
            
            # البحث بالباركود أولاً
            if self.search_term.isdigit():
                product = self.product_manager.get_product_by_barcode(self.search_term)
                if product and product.is_active:
                    products.append(product)
            
            # البحث بالاسم
            if not products:
                search_results = self.product_manager.search_products(self.search_term)
                products = [p for p in search_results if p.is_active and getattr(p, 'is_sellable', True)]
            
            self.search_completed.emit(products)
            
        except Exception as e:
            self.search_completed.emit([])


class SalesDialog(QDialog):
    """نافذة فاتورة المبيعات"""
    
    # إشارات مخصصة
    sale_completed = Signal(object)  # Sale
    
    def __init__(self, db_manager: DatabaseManager, sale: Optional[Sale] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.sale_manager = SaleManager(db_manager)
        self.product_manager = ProductManager(db_manager)
        self.customer_manager = CustomerManager(db_manager)
        # prefer enhanced sales service if available
        self.legacy_sales_service = SalesService(db_manager)
        if EnhancedSalesService:
            try:
                self.sales_service = EnhancedSalesService(db_manager)
            except Exception:
                self.sales_service = self.legacy_sales_service
        else:
            self.sales_service = self.legacy_sales_service
        self.logger = setup_logger(__name__)
        
        self.sale = sale  # الفاتورة للتعديل (None للإنشاء الجديد)
        self.is_edit_mode = sale is not None
        self.search_worker: Optional[ProductSearchWorker] = None
        
        # بيانات الفاتورة
        self.sale_items: List[SaleItem] = []
        self.current_customer = None
        self.discount_amount = Decimal('0')
        self.tax_rate = Decimal('0.15')  # ضريبة القيمة المضافة 15%
        
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        self.setup_shortcuts()
        self.load_data()
        
        if self.is_edit_mode:
            self.populate_form()
        else:
            self.create_new_sale()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        title = "تعديل الفاتورة" if self.is_edit_mode else "فاتورة مبيعات جديدة"
        self.setWindowTitle(title)
        self.setMinimumSize(1200, 800)
        self.setModal(True)
        
        # تخطيط رئيسي
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # شريط العنوان
        self.setup_header(main_layout)
        
        # المحتوى الرئيسي
        splitter = QSplitter(Qt.Horizontal)
        
        # الجانب الأيسر - إدخال المنتجات
        left_widget = self.create_input_panel()
        splitter.addWidget(left_widget)
        
        # الجانب الأيمن - تفاصيل الفاتورة
        right_widget = self.create_invoice_panel()
        splitter.addWidget(right_widget)
        
        # تحديد نسب العرض
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        main_layout.addWidget(self.progress_bar)
        
        # منطقة الأزرار
        self.setup_buttons(main_layout)
    
    def setup_header(self, layout: QVBoxLayout):
        """إعداد منطقة الرأس"""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        
        # معلومات الفاتورة
        info_layout = QVBoxLayout()
        
        title = "تعديل الفاتورة" if self.is_edit_mode else "فاتورة مبيعات جديدة"
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)
        info_layout.addWidget(title_label)
        
        # رقم الفاتورة والتاريخ
        details_layout = QHBoxLayout()
        
        self.invoice_number_label = QLabel("رقم الفاتورة: جديدة")
        self.invoice_number_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
        details_layout.addWidget(self.invoice_number_label)
        
        details_layout.addStretch()
        
        self.date_label = QLabel(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self.date_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
        details_layout.addWidget(self.date_label)
        
        info_layout.addLayout(details_layout)
        header_layout.addLayout(info_layout)
        
        # أيقونة الفاتورة
        icon_label = QLabel("🧾")
        icon_label.setStyleSheet("font-size: 32px; color: white;")
        header_layout.addWidget(icon_label)
        
        layout.addWidget(header_frame)
    
    def create_input_panel(self) -> QWidget:
        """إنشاء لوحة الإدخال"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # مجموعة البحث عن المنتجات
        search_group = QGroupBox("البحث عن المنتجات")
        search_layout = QVBoxLayout(search_group)
        
        # حقل البحث
        search_input_layout = QHBoxLayout()
        
        self.product_search_edit = QLineEdit()
        self.product_search_edit.setPlaceholderText("ابحث بالاسم أو الباركود أو امسح الباركود...")
        self.product_search_edit.setMinimumHeight(35)
        search_input_layout.addWidget(self.product_search_edit)
        
        self.search_button = QPushButton("بحث")
        self.search_button.setMinimumHeight(35)
        self.search_button.setMaximumWidth(80)
        search_input_layout.addWidget(self.search_button)
        
        search_layout.addLayout(search_input_layout)
        
        # جدول نتائج البحث
        self.search_results_table = QTableWidget()
        self.search_results_table.setColumnCount(5)
        self.search_results_table.setHorizontalHeaderLabels([
            "الاسم", "الباركود", "السعر", "المخزون", "إضافة"
        ])
        self.search_results_table.setMaximumHeight(200)
        self.search_results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # إعداد عرض الأعمدة
        header = self.search_results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # الاسم
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # الباركود
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # السعر
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # المخزون
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # إضافة
        
        search_layout.addWidget(self.search_results_table)
        
        layout.addWidget(search_group)
        
        # مجموعة العميل
        customer_group = QGroupBox("العميل")
        customer_layout = QFormLayout(customer_group)
        
        # اختيار العميل
        customer_input_layout = QHBoxLayout()
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setMinimumHeight(30)
        customer_input_layout.addWidget(self.customer_combo)
        
        self.new_customer_button = QPushButton("عميل جديد")
        self.new_customer_button.setMaximumWidth(100)
        customer_input_layout.addWidget(self.new_customer_button)
        
        customer_layout.addRow("العميل:", customer_input_layout)
        
        # معلومات العميل
        self.customer_info_label = QLabel("لم يتم اختيار عميل")
        self.customer_info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        customer_layout.addRow("", self.customer_info_label)
        
        layout.addWidget(customer_group)
        
        # مجموعة الإعدادات السريعة
        settings_group = QGroupBox("إعدادات سريعة")
        settings_layout = QFormLayout(settings_group)
        
        # نوع الدفع
        self.payment_method_combo = QComboBox()
        for method in PaymentMethod:
            self.payment_method_combo.addItem(method.value, method)
        settings_layout.addRow("طريقة الدفع:", self.payment_method_combo)
        
        # معدل الضريبة
        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setRange(0, 100)
        self.tax_rate_spin.setValue(15)
        self.tax_rate_spin.setSuffix("%")
        settings_layout.addRow("معدل الضريبة:", self.tax_rate_spin)
        
        layout.addWidget(settings_group)
        
        layout.addStretch()
        return widget
    
    def create_invoice_panel(self) -> QWidget:
        """إنشاء لوحة الفاتورة"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # جدول عناصر الفاتورة
        items_group = QGroupBox("عناصر الفاتورة")
        items_layout = QVBoxLayout(items_group)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "المنتج", "السعر", "الكمية", "الخصم", "الإجمالي", "حذف", "تعديل"
        ])
        
        # إعداد عرض الأعمدة
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # المنتج
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # السعر
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # الكمية
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # الخصم
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # الإجمالي
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # حذف
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # تعديل
        
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setAlternatingRowColors(True)
        
        items_layout.addWidget(self.items_table)
        layout.addWidget(items_group)
        
        # ملخص الفاتورة
        summary_group = QGroupBox("ملخص الفاتورة")
        summary_layout = QGridLayout(summary_group)
        
        # المجموع الفرعي
        summary_layout.addWidget(QLabel("المجموع الفرعي:"), 0, 0)
        self.subtotal_label = QLabel("0.00 ريال")
        self.subtotal_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        summary_layout.addWidget(self.subtotal_label, 0, 1)
        
        # الخصم
        summary_layout.addWidget(QLabel("الخصم:"), 1, 0)
        discount_layout = QHBoxLayout()
        
        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setRange(0, 999999.99)
        self.discount_spin.setDecimals(2)
        self.discount_spin.setSuffix(" ريال")
        discount_layout.addWidget(self.discount_spin)
        
        self.discount_percent_button = QPushButton("%")
        self.discount_percent_button.setMaximumWidth(30)
        self.discount_percent_button.setCheckable(True)
        discount_layout.addWidget(self.discount_percent_button)
        
        summary_layout.addLayout(discount_layout, 1, 1)
        
        # الضريبة
        summary_layout.addWidget(QLabel("الضريبة:"), 2, 0)
        self.tax_label = QLabel("0.00 ريال")
        self.tax_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        summary_layout.addWidget(self.tax_label, 2, 1)
        
        # المجموع الكلي
        summary_layout.addWidget(QLabel("المجموع الكلي:"), 3, 0)
        self.total_label = QLabel("0.00 ريال")
        self.total_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 18px; 
            color: #27ae60;
            border: 2px solid #27ae60;
            border-radius: 5px;
            padding: 5px;
            background-color: #f8fff8;
        """)
        summary_layout.addWidget(self.total_label, 3, 1)
        
        layout.addWidget(summary_group)
        
        # ملاحظات
        notes_group = QGroupBox("ملاحظات")
        notes_layout = QVBoxLayout(notes_group)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("ملاحظات إضافية على الفاتورة...")
        self.notes_edit.setMaximumHeight(80)
        notes_layout.addWidget(self.notes_edit)
        
        layout.addWidget(notes_group)
        
        return widget
    
    def setup_buttons(self, layout: QVBoxLayout):
        """إعداد الأزرار"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # أزرار العمليات السريعة
        quick_actions_layout = QHBoxLayout()
        
        self.clear_button = QPushButton("مسح الكل")
        self.clear_button.setMinimumHeight(35)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        quick_actions_layout.addWidget(self.clear_button)
        
        self.hold_button = QPushButton("تعليق الفاتورة")
        self.hold_button.setMinimumHeight(35)
        quick_actions_layout.addWidget(self.hold_button)
        
        self.print_button = QPushButton("طباعة")
        self.print_button.setMinimumHeight(35)
        quick_actions_layout.addWidget(self.print_button)
        
        buttons_layout.addLayout(quick_actions_layout)
        
        buttons_layout.addStretch()
        
        # أزرار الحفظ والإلغاء
        main_buttons_layout = QHBoxLayout()
        
        # زر الحفظ
        self.save_button = QPushButton("حفظ الفاتورة")
        self.save_button.setMinimumHeight(40)
        self.save_button.setMinimumWidth(120)
        self.save_button.setDefault(True)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        main_buttons_layout.addWidget(self.save_button)
        
        # زر الحفظ والطباعة
        self.save_and_print_button = QPushButton("حفظ وطباعة")
        self.save_and_print_button.setMinimumHeight(40)
        self.save_and_print_button.setMinimumWidth(120)
        main_buttons_layout.addWidget(self.save_and_print_button)
        
        # زر الإلغاء
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setMinimumWidth(80)
        main_buttons_layout.addWidget(self.cancel_button)
        
        buttons_layout.addLayout(main_buttons_layout)
        layout.addLayout(buttons_layout)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        # البحث عن المنتجات
        self.product_search_edit.textChanged.connect(self.on_search_text_changed)
        self.product_search_edit.returnPressed.connect(self.search_products)
        self.search_button.clicked.connect(self.search_products)
        
        # العميل
        self.customer_combo.currentTextChanged.connect(self.on_customer_changed)
        self.new_customer_button.clicked.connect(self.add_new_customer)
        
        # الحسابات
        self.discount_spin.valueChanged.connect(self.calculate_totals)
        self.discount_percent_button.toggled.connect(self.on_discount_type_changed)
        self.tax_rate_spin.valueChanged.connect(self.calculate_totals)
        
        # الأزرار
        self.save_button.clicked.connect(self.handle_save)
        self.save_and_print_button.clicked.connect(self.handle_save_and_print)
        self.cancel_button.clicked.connect(self.reject)
        self.clear_button.clicked.connect(self.clear_invoice)
        self.hold_button.clicked.connect(self.hold_invoice)
        self.print_button.clicked.connect(self.print_invoice)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # F1 - البحث
        search_shortcut = QShortcut(QKeySequence("F1"), self)
        search_shortcut.activated.connect(lambda: self.product_search_edit.setFocus())
        
        # F2 - عميل جديد
        customer_shortcut = QShortcut(QKeySequence("F2"), self)
        customer_shortcut.activated.connect(self.add_new_customer)
        
        # F3 - خصم
        discount_shortcut = QShortcut(QKeySequence("F3"), self)
        discount_shortcut.activated.connect(lambda: self.discount_spin.setFocus())
        
        # F9 - تعليق
        hold_shortcut = QShortcut(QKeySequence("F9"), self)
        hold_shortcut.activated.connect(self.hold_invoice)
        
        # F12 - حفظ
        save_shortcut = QShortcut(QKeySequence("F12"), self)
        save_shortcut.activated.connect(self.handle_save)
        
        # Ctrl+P - طباعة
        print_shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        print_shortcut.activated.connect(self.print_invoice)
        
        # Escape - إلغاء
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self.reject)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
            
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                background-color: white;
            }
            
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #3498db;
            }
            
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                gridline-color: #eee;
            }
            
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
            
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
                background-color: white;
            }
            
            QTextEdit:focus {
                border-color: #3498db;
            }
        """)
    
    def load_data(self):
        """تحميل البيانات من قاعدة البيانات"""
        try:
            # تحميل العملاء
            customers = self.customer_manager.get_all_customers()
            self.customer_combo.clear()
            self.customer_combo.addItem("-- عميل نقدي --", None)
            for customer in customers:
                if customer.is_active:
                    self.customer_combo.addItem(f"{customer.name} - {customer.phone or 'بدون هاتف'}", customer.id)
                    
        except Exception as e:
            self.logger.error(f"خطأ في تحميل البيانات: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل البيانات: {str(e)}")
    
    def create_new_sale(self):
        """إنشاء فاتورة جديدة"""
        try:
            from ...models.sale import Sale, SaleStatus, PaymentMethod
            from datetime import date
            
            # إنشاء كائن فاتورة جديد
            new_sale = Sale(
                invoice_number=self._generate_invoice_number(),
                sale_date=date.today(),
                status=SaleStatus.DRAFT,
                payment_method=PaymentMethod.CASH,
                items=[]
            )
            
            # إنشاء الفاتورة في قاعدة البيانات
            sale_id = None
            # try enhanced API names first
            if hasattr(self.sales_service, 'create_order'):
                try:
                    sale_id = self.sales_service.create_order(new_sale)
                except Exception:
                    sale_id = None
            if not sale_id and hasattr(self.sales_service, 'create_sale'):
                try:
                    sale_id = self.sales_service.create_sale(new_sale)
                except Exception:
                    sale_id = None
            if sale_id:
                new_sale.id = sale_id
                self.sale = new_sale
                self.invoice_number_label.setText(f"رقم الفاتورة: {self.sale.invoice_number}")
            else:
                QMessageBox.critical(self, "خطأ", "فشل في إنشاء فاتورة جديدة")
                self.reject()
                
        except Exception as e:
            self.logger.error(f"خطأ في إنشاء فاتورة جديدة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في إنشاء فاتورة جديدة: {str(e)}")
            self.reject()
    
    def _generate_invoice_number(self):
        """توليد رقم فاتورة جديد"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"INV-{timestamp}"
    
    def populate_form(self):
        """ملء النموذج ببيانات الفاتورة (للتعديل)"""
        if not self.sale:
            return
        
        try:
            # معلومات الفاتورة
            self.invoice_number_label.setText(f"رقم الفاتورة: {self.sale.invoice_number}")
            self.date_label.setText(f"التاريخ: {self.sale.sale_date}")
            
            # العميل
            if self.sale.customer_id:
                index = self.customer_combo.findData(self.sale.customer_id)
                if index >= 0:
                    self.customer_combo.setCurrentIndex(index)
            
            # طريقة الدفع
            for i in range(self.payment_method_combo.count()):
                if self.payment_method_combo.itemData(i) == self.sale.payment_method:
                    self.payment_method_combo.setCurrentIndex(i)
                    break
            
            # الخصم والضريبة
            self.discount_spin.setValue(float(self.sale.discount_amount or 0))
            if hasattr(self.sale, 'tax_rate'):
                self.tax_rate_spin.setValue(float(self.sale.tax_rate or 0) * 100)
            
            # الملاحظات
            self.notes_edit.setPlainText(self.sale.notes or "")
            
            # تحميل عناصر الفاتورة
            self.load_sale_items()
            
        except Exception as e:
            self.logger.error(f"خطأ في ملء النموذج: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تحميل بيانات الفاتورة: {str(e)}")
    
    def load_sale_items(self):
        """تحميل عناصر الفاتورة"""
        if not self.sale:
            return
        
        try:
            # جلب عناصر الفاتورة من قاعدة البيانات
            items = self.sale_manager.get_sale_items(self.sale.id)
            self.sale_items = items
            self.refresh_items_table()
            
        except Exception as e:
            self.logger.error(f"خطأ في تحميل عناصر الفاتورة: {str(e)}")
    
    def on_search_text_changed(self, text: str):
        """معالجة تغيير نص البحث"""
        # البحث التلقائي عند إدخال باركود
        if len(text) >= 3 and text.isdigit():
            QTimer.singleShot(500, self.search_products)
    
    def search_products(self):
        """البحث عن المنتجات"""
        search_term = self.product_search_edit.text().strip()
        if not search_term:
            self.search_results_table.setRowCount(0)
            return
        
        # تعطيل البحث أثناء التنفيذ
        self.search_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        # بدء البحث في خيط منفصل
        self.search_worker = ProductSearchWorker(self.product_manager, search_term)
        self.search_worker.search_completed.connect(self.on_search_completed)
        self.search_worker.start()
    
    def on_search_completed(self, products: List):
        """معالجة اكتمال البحث"""
        self.search_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        # عرض النتائج
        self.search_results_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            # اسم المنتج
            name_item = QTableWidgetItem(product.name)
            name_item.setData(Qt.UserRole, product)
            self.search_results_table.setItem(row, 0, name_item)
            
            # الباركود
            barcode_item = QTableWidgetItem(product.barcode or "")
            self.search_results_table.setItem(row, 1, barcode_item)
            
            # السعر
            price_item = QTableWidgetItem(f"{product.selling_price:.2f}")
            self.search_results_table.setItem(row, 2, price_item)
            
            # المخزون
            stock_item = QTableWidgetItem(str(product.stock_quantity))
            if product.stock_quantity <= product.min_stock_level:
                stock_item.setBackground(QColor("#ffebee"))
            self.search_results_table.setItem(row, 3, stock_item)
            
            # زر الإضافة
            add_button = QPushButton("إضافة")
            add_button.setStyleSheet("""
                QPushButton {
                    background-color: #4caf50;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            add_button.clicked.connect(lambda checked, p=product: self.add_product_to_sale(p))
            self.search_results_table.setCellWidget(row, 4, add_button)
        
        # إذا كان هناك منتج واحد فقط، أضفه تلقائياً
        if len(products) == 1:
            self.add_product_to_sale(products[0])
            self.product_search_edit.clear()
    
    def add_product_to_sale(self, product):
        """إضافة منتج إلى الفاتورة"""
        try:
            # التحقق من المخزون
            if product.track_stock and product.stock_quantity <= 0:
                QMessageBox.warning(self, "تحذير", f"المنتج '{product.name}' غير متوفر في المخزون")
                return
            
            # البحث عن المنتج في الفاتورة
            existing_item = None
            for item in self.sale_items:
                if item.product_id == product.id:
                    existing_item = item
                    break
            
            if existing_item:
                # زيادة الكمية
                new_quantity = existing_item.quantity + 1
                if product.track_stock and new_quantity > product.stock_quantity:
                    QMessageBox.warning(self, "تحذير", f"الكمية المطلوبة ({new_quantity}) أكبر من المتوفر في المخزون ({product.stock_quantity})")
                    return
                
                existing_item.quantity = new_quantity
                existing_item.total_price = existing_item.unit_price * existing_item.quantity - existing_item.discount_amount
            else:
                # إضافة عنصر جديد
                sale_item = SaleItem(
                    id=None,
                    sale_id=self.sale.id if self.sale else None,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=1,
                    unit_price=product.selling_price,
                    discount_amount=Decimal('0'),
                    total_price=product.selling_price
                )
                self.sale_items.append(sale_item)
            
            # تحديث الجدول والحسابات
            self.refresh_items_table()
            self.calculate_totals()
            
            # مسح البحث
            self.product_search_edit.clear()
            self.search_results_table.setRowCount(0)
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة المنتج: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في إضافة المنتج: {str(e)}")
    
    def refresh_items_table(self):
        """تحديث جدول عناصر الفاتورة"""
        self.items_table.setRowCount(len(self.sale_items))
        
        for row, item in enumerate(self.sale_items):
            # اسم المنتج
            product_item = QTableWidgetItem(item.product_name)
            self.items_table.setItem(row, 0, product_item)
            
            # السعر
            price_item = QTableWidgetItem(f"{item.unit_price:.2f}")
            self.items_table.setItem(row, 1, price_item)
            
            # الكمية
            quantity_spin = QSpinBox()
            quantity_spin.setRange(1, 9999)
            quantity_spin.setValue(item.quantity)
            quantity_spin.valueChanged.connect(lambda value, i=row: self.update_item_quantity(i, value))
            self.items_table.setCellWidget(row, 2, quantity_spin)
            
            # الخصم
            discount_spin = QDoubleSpinBox()
            discount_spin.setRange(0, 999999.99)
            discount_spin.setValue(float(item.discount_amount))
            discount_spin.setSuffix(" ريال")
            discount_spin.valueChanged.connect(lambda value, i=row: self.update_item_discount(i, value))
            self.items_table.setCellWidget(row, 3, discount_spin)
            
            # الإجمالي
            total_item = QTableWidgetItem(f"{item.total_price:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, total_item)
            
            # زر الحذف
            delete_button = QPushButton("حذف")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_button.clicked.connect(lambda checked, i=row: self.remove_item(i))
            self.items_table.setCellWidget(row, 5, delete_button)
            
            # زر التعديل
            edit_button = QPushButton("تعديل")
            edit_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff9800;
                    color: white;
                    border: none;
                    border-radius: 3px;
                    padding: 4px 8px;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            edit_button.clicked.connect(lambda checked, i=row: self.edit_item(i))
            self.items_table.setCellWidget(row, 6, edit_button)
    
    def update_item_quantity(self, row: int, quantity: int):
        """تحديث كمية العنصر"""
        if row < len(self.sale_items):
            item = self.sale_items[row]
            
            # التحقق من المخزون
            product = self.product_manager.get_product_by_id(item.product_id)
            if product and product.track_stock and quantity > product.stock_quantity:
                QMessageBox.warning(self, "تحذير", f"الكمية المطلوبة ({quantity}) أكبر من المتوفر في المخزون ({product.stock_quantity})")
                return
            
            item.quantity = quantity
            item.total_price = item.unit_price * item.quantity - item.discount_amount
            
            # تحديث الجدول
            total_item = QTableWidgetItem(f"{item.total_price:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, total_item)
            
            self.calculate_totals()
    
    def update_item_discount(self, row: int, discount: float):
        """تحديث خصم العنصر"""
        if row < len(self.sale_items):
            item = self.sale_items[row]
            item.discount_amount = Decimal(str(discount))
            item.total_price = item.unit_price * item.quantity - item.discount_amount
            
            # تحديث الجدول
            total_item = QTableWidgetItem(f"{item.total_price:.2f}")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            self.items_table.setItem(row, 4, total_item)
            
            self.calculate_totals()
    
    def remove_item(self, row: int):
        """حذف عنصر من الفاتورة"""
        if row < len(self.sale_items):
            item = self.sale_items[row]
            reply = QMessageBox.question(
                self, 
                "تأكيد الحذف", 
                f"هل تريد حذف '{item.product_name}' من الفاتورة؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.sale_items.pop(row)
                self.refresh_items_table()
                self.calculate_totals()
    
    def edit_item(self, row: int):
        """تعديل عنصر في الفاتورة"""
        # يمكن إضافة نافذة تعديل مفصلة هنا
        pass
    
    def calculate_totals(self):
        """حساب المجاميع"""
        try:
            # المجموع الفرعي
            subtotal = sum(item.total_price for item in self.sale_items)
            
            # الخصم
            discount = Decimal(str(self.discount_spin.value()))
            if self.discount_percent_button.isChecked():
                # خصم بالنسبة المئوية
                discount = subtotal * (discount / 100)
            
            # المجموع بعد الخصم
            after_discount = subtotal - discount
            
            # الضريبة
            tax_rate = Decimal(str(self.tax_rate_spin.value())) / 100
            tax_amount = after_discount * tax_rate
            
            # المجموع الكلي
            total = after_discount + tax_amount
            
            # تحديث التسميات
            self.subtotal_label.setText(f"{subtotal:.2f} ريال")
            self.tax_label.setText(f"{tax_amount:.2f} ريال")
            self.total_label.setText(f"{total:.2f} ريال")
            
            # حفظ القيم
            self.discount_amount = discount
            
        except Exception as e:
            self.logger.error(f"خطأ في حساب المجاميع: {str(e)}")
    
    def on_discount_type_changed(self, is_percentage: bool):
        """معالجة تغيير نوع الخصم"""
        if is_percentage:
            self.discount_spin.setSuffix("%")
            self.discount_spin.setRange(0, 100)
        else:
            self.discount_spin.setSuffix(" ريال")
            self.discount_spin.setRange(0, 999999.99)
        
        self.calculate_totals()
    
    def on_customer_changed(self, customer_text: str):
        """معالجة تغيير العميل"""
        customer_id = self.customer_combo.currentData()
        if customer_id:
            try:
                customer = self.customer_manager.get_customer_by_id(customer_id)
                if customer:
                    self.current_customer = customer
                    info_text = f"الهاتف: {customer.phone or 'غير محدد'}"
                    if customer.credit_limit > 0:
                        info_text += f" | الحد الائتماني: {customer.credit_limit:.2f}"
                    if customer.current_balance > 0:
                        info_text += f" | الرصيد الحالي: {customer.current_balance:.2f}"
                    self.customer_info_label.setText(info_text)
                else:
                    self.current_customer = None
                    self.customer_info_label.setText("عميل غير موجود")
            except Exception as e:
                self.logger.error(f"خطأ في تحميل بيانات العميل: {str(e)}")
                self.customer_info_label.setText("خطأ في تحميل بيانات العميل")
        else:
            self.current_customer = None
            self.customer_info_label.setText("عميل نقدي")
    
    def add_new_customer(self):
        """إضافة عميل جديد"""
        try:
            from .customer_dialog import CustomerDialog
            
            dialog = CustomerDialog(self.db_manager, parent=self)
            if dialog.exec() == QDialog.Accepted:
                # إعادة تحميل العملاء
                self.load_data()
                
                # اختيار العميل الجديد
                new_customer = dialog.get_saved_customer()
                if new_customer:
                    index = self.customer_combo.findData(new_customer.id)
                    if index >= 0:
                        self.customer_combo.setCurrentIndex(index)
                        
        except ImportError:
            QMessageBox.information(self, "معلومات", "نافذة إضافة العملاء غير متوفرة حالياً")
        except Exception as e:
            self.logger.error(f"خطأ في إضافة عميل جديد: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في إضافة عميل جديد: {str(e)}")
    
    def clear_invoice(self):
        """مسح الفاتورة"""
        reply = QMessageBox.question(
            self, 
            "تأكيد المسح", 
            "هل تريد مسح جميع عناصر الفاتورة؟",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.sale_items.clear()
            self.refresh_items_table()
            self.calculate_totals()
            self.product_search_edit.clear()
            self.search_results_table.setRowCount(0)
    
    def hold_invoice(self):
        """تعليق الفاتورة"""
        try:
            if not self.sale_items:
                QMessageBox.warning(self, "تحذير", "لا يمكن تعليق فاتورة فارغة")
                return
            
            # حفظ الفاتورة بحالة معلقة
            self.save_sale(status=SaleStatus.PENDING)
            QMessageBox.information(self, "نجح", "تم تعليق الفاتورة بنجاح")
            self.accept()
            
        except Exception as e:
            self.logger.error(f"خطأ في تعليق الفاتورة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في تعليق الفاتورة: {str(e)}")
    
    def print_invoice(self):
        """طباعة الفاتورة"""
        try:
            if not self.sale or not self.sale_items:
                QMessageBox.warning(self, "تحذير", "لا يمكن طباعة فاتورة فارغة")
                return
            
            # هنا يمكن إضافة كود الطباعة
            QMessageBox.information(self, "معلومات", "سيتم إضافة وظيفة الطباعة قريباً")
            
        except Exception as e:
            self.logger.error(f"خطأ في طباعة الفاتورة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في طباعة الفاتورة: {str(e)}")
    
    def handle_save(self):
        """معالجة حفظ الفاتورة"""
        self.save_sale()
    
    def handle_save_and_print(self):
        """معالجة حفظ وطباعة الفاتورة"""
        if self.save_sale():
            self.print_invoice()
    
    def save_sale(self, status: SaleStatus = SaleStatus.CONFIRMED) -> bool:
        """حفظ الفاتورة"""
        try:
            if not self.sale_items:
                QMessageBox.warning(self, "تحذير", "لا يمكن حفظ فاتورة فارغة")
                return False
            
            # تعطيل الواجهة أثناء الحفظ
            self.set_ui_enabled(False)
            self.progress_bar.setVisible(True)
            
            # تحديث بيانات الفاتورة
            customer_id = self.customer_combo.currentData()
            payment_method = self.payment_method_combo.currentData()
            notes = self.notes_edit.toPlainText().strip()
            
            # حساب المجاميع النهائية
            subtotal = sum(item.total_price for item in self.sale_items)
            tax_amount = subtotal * (Decimal(str(self.tax_rate_spin.value())) / 100)
            total_amount = subtotal + tax_amount - self.discount_amount
            
            # إضافة العناصر إلى الفاتورة
            for item in self.sale_items:
                success = False
                # try enhanced method names
                if hasattr(self.sales_service, 'add_item_to_order'):
                    try:
                        success = self.sales_service.add_item_to_order(
                            self.sale.id,
                            item.product_id,
                            item.quantity,
                            item.unit_price,
                            item.discount_amount
                        )
                    except Exception:
                        success = False
                # fallback to legacy
                if not success and hasattr(self.sales_service, 'add_item_to_sale'):
                    try:
                        success = self.sales_service.add_item_to_sale(
                            self.sale.id,
                            item.product_id,
                            item.quantity,
                            item.unit_price,
                            item.discount_amount
                        )
                    except Exception:
                        success = False
                if not success:
                    raise Exception(f"فشل في إضافة المنتج: {item.product_name}")
            
            # إكمال الفاتورة
            completed_sale = None
            # try enhanced confirm API
            if hasattr(self.sales_service, 'confirm_order'):
                try:
                    completed_sale = self.sales_service.confirm_order(
                        self.sale.id,
                        payment_method=payment_method,
                        customer_id=customer_id,
                        discount_amount=self.discount_amount,
                        notes=notes
                    )
                except Exception:
                    completed_sale = None
            # fallback to legacy
            if not completed_sale and hasattr(self.sales_service, 'complete_sale'):
                try:
                    completed_sale = self.sales_service.complete_sale(
                        self.sale.id,
                        payment_method=payment_method,
                        customer_id=customer_id,
                        discount_amount=self.discount_amount,
                        notes=notes
                    )
                except Exception:
                    completed_sale = None
            
            if completed_sale:
                self.sale = completed_sale
                self.sale_completed.emit(completed_sale)
                
                QMessageBox.information(
                    self, 
                    "نجح", 
                    f"تم حفظ الفاتورة بنجاح\nرقم الفاتورة: {completed_sale.invoice_number}\nالمجموع: {total_amount:.2f} ريال"
                )
                
                self.accept()
                return True
            else:
                raise Exception("فشل في إكمال الفاتورة")
                
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الفاتورة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الفاتورة: {str(e)}")
            return False
        finally:
            self.set_ui_enabled(True)
            self.progress_bar.setVisible(False)
    
    def set_ui_enabled(self, enabled: bool):
        """تفعيل/تعطيل عناصر الواجهة"""
        self.product_search_edit.setEnabled(enabled)
        self.search_button.setEnabled(enabled)
        self.customer_combo.setEnabled(enabled)
        self.new_customer_button.setEnabled(enabled)
        self.payment_method_combo.setEnabled(enabled)
        self.tax_rate_spin.setEnabled(enabled)
        self.discount_spin.setEnabled(enabled)
        self.items_table.setEnabled(enabled)
        self.notes_edit.setEnabled(enabled)
        self.save_button.setEnabled(enabled)
        self.save_and_print_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.clear_button.setEnabled(enabled)
        self.hold_button.setEnabled(enabled)
        self.print_button.setEnabled(enabled)
    
    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()
        
        # التحقق من وجود تغييرات غير محفوظة
        if self.sale_items and not self.is_edit_mode:
            reply = QMessageBox.question(
                self,
                "تأكيد الإغلاق",
                "هناك فاتورة غير محفوظة. هل تريد الإغلاق بدون حفظ؟",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
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
    
    dialog = SalesDialog(db)
    
    if dialog.exec() == QDialog.Accepted:
        print("تم حفظ الفاتورة بنجاح")
    else:
        print("تم إلغاء العملية")
    
    sys.exit()
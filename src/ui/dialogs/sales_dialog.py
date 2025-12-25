#!/usr/bin/env python3
"""
نافذة فاتورة المبيعات - Sales Dialog
واجهة شاملة لإنشاء وإدارة فواتير المبيعات مع دعم اللغة العربية
التصميم الجديد: 3-Zone Enterprise Layout
"""

import sys
from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, date
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
    QComboBox, QFrame, QMessageBox, QCompleter, QAbstractItemView, QWidget,
    QApplication, QDoubleSpinBox, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QTimer, QDate, Signal, QObject, QEvent
from PySide6.QtGui import QIcon, QFont, QColor, QPainter, QKeySequence, QShortcut

# --- استيراد العقل والأدوات (The Core Dependencies) ---
from ...core.database_manager import DatabaseManager
from ...core.signals import signals
from ...models.sale import Sale, SaleItem, SaleManager, SaleStatus, PaymentMethod
from ...models.product import ProductManager, Product
from ...models.customer import CustomerManager
from ...services.sales_service import SalesService
from ...utils.logger import setup_logger
from ...utils.i18n_api import I18n
from ...utils.math_utils import (
    to_decimal, calculate_line_total, calculate_subtotal, 
    calculate_discount_amount, calculate_tax_amount, calculate_grand_total,
    format_currency
)


class SalesDialog(QDialog):
    """نافذة فاتورة المبيعات - تصميم 3-Zone Enterprise Layout"""
    
    # إشارات مخصصة
    sale_completed = Signal(object)  # Sale
    
    def __init__(self, db_manager: DatabaseManager, sale: Optional[Sale] = None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        
        # 👇 الإصلاح 1: تفعيل الوضع العربي (RTL) إجبارياً
        self.setLayoutDirection(Qt.RightToLeft)
        
        # تهيئة المديرين (المخ الحقيقي للعملية)
        self.sale_manager = SaleManager(db_manager, logger=setup_logger(__name__))
        self.product_manager = ProductManager(db_manager)
        self.customer_manager = CustomerManager(db_manager)
        self.sales_service = SalesService(db_manager, logger=setup_logger(__name__))
        self.logger = setup_logger(__name__)
        
        # تهيئة نظام الترجمة
        from pathlib import Path
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        # --- متغيرات الحالة (State Management) - يجب تهيئتها قبل الاستخدام ---
        self.sale = sale  # الفاتورة للتعديل (None للإنشاء الجديد)
        self.is_edit_mode = sale is not None
        
        # إعدادات النافذة
        if self.is_edit_mode:
            self.setWindowTitle(self.i18n.get_message("invoice_edit_title", invoice_number=sale.invoice_number))
        else:
            self.setWindowTitle(self.i18n.get_message("invoice_new_title"))
        self.setModal(True)
        
        # حساب الأبعاد بشكل responsive
        app = QApplication.instance()
        if app:
            screen = app.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                screen_width = screen_geometry.width()
                screen_height = screen_geometry.height()
                
                optimal_width = min(1400, int(screen_width * 0.85))
                optimal_height = min(900, int(screen_height * 0.85))
                
                self.setMinimumSize(max(1000, int(screen_width * 0.60)), max(700, int(screen_height * 0.65)))
                self.setMaximumSize(min(1800, screen_width - 50), min(1200, screen_height - 50))
                self.resize(optimal_width, optimal_height)
                
                # مركز النافذة
                if self.parent():
                    parent_geometry = self.parent().geometry()
                    x = parent_geometry.x() + (parent_geometry.width() - optimal_width) // 2
                    y = parent_geometry.y() + (parent_geometry.height() - optimal_height) // 2
                    self.move(x, y)
                else:
                    x = (screen_width - optimal_width) // 2
                    y = (screen_height - optimal_height) // 2
                    self.move(x, y)
            else:
                self.setMinimumSize(1000, 700)
                self.setMaximumSize(1800, 1200)
                self.resize(1366, 800)
        else:
            self.setMinimumSize(1000, 700)
            self.setMaximumSize(1800, 1200)
            self.resize(1366, 800)
        
        # --- متغيرات الحالة (State Management) ---
        # هذه القائمة هي "الموديل" الحقيقي في الذاكرة (🚫 القاعدة 1: لا نحسب من النصوص)
        self.cart_items: List[Dict[str, Any]] = []  # قائمة المنتجات في السلة
        self.current_customer_id = None
        # ملاحظة: sale و is_edit_mode تم تهيئتهما أعلاه قبل إعدادات النافذة
        self.tax_rate = Decimal('0')  # نسبة الضريبة الحالية (قابلة للتعديل)
        self.paid_amount = Decimal('0')  # المبلغ المدفوع
        
        # 1. بناء الواجهة
        self.setup_ui()
        self.setup_styles()
        self.setup_shortcuts()
        
        # 2. تحميل البيانات الأولية (العملاء والمنتجات)
        self.load_initial_data()
        self.setup_smart_search()
        
        # الإصلاح 1: تحديث بطاقات العميل عند التحميل الأولي
        if self.combo_customer.count() > 0:
            self.on_customer_changed(0)
        
        # 3. التركيز على البحث فوراً (⚡ القاعدة 3: سرعة الكاشير)
        QTimer.singleShot(100, lambda: self.search_input.setFocus())
        # سيتم التعامل مع returnPressed مباشرة في on_search_enter
        
        # 4. إذا كان في وضع التعديل، تحميل البيانات
        if self.is_edit_mode:
            if self.logger:
                self.logger.info(f"فتح نافذة التعديل للفاتورة {self.sale.id if self.sale else 'None'}")
            self.populate_form()
        else:
            self.create_new_sale()
    
    def setup_ui(self):
        """بناء تخطيط المناطق الثلاث (3-Zone Enterprise Layout)"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        # الإصلاح 3: توسيع المساحة السفلية لتجنب قطع الأزرار
        main_layout.setContentsMargins(0, 0, 0, 20)
        
        # ============================================================
        # ZONE 1: سياق العميل (Customer Header)
        # ============================================================
        header_frame = QFrame()
        header_frame.setObjectName("Zone1")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # اختيار العميل
        customer_layout = QVBoxLayout()
        lbl_cust = QLabel(self.i18n.get_message("customer") + ":")
        lbl_cust.setObjectName("LabelDim")
        
        self.combo_customer = QComboBox()
        self.combo_customer.setEditable(True)  # قابل للبحث
        self.combo_customer.setMinimumWidth(250)
        self.combo_customer.setPlaceholderText(self.i18n.get_message("search_customer"))
        
        customer_layout.addWidget(lbl_cust)
        customer_layout.addWidget(self.combo_customer)
        
        # بطاقات المعلومات الحية (Live Insights)
        currency_symbol = self.i18n.get_message("currency_symbol")
        self.card_balance = self.create_info_card(self.i18n.get_message("current_balance"), f"0.00 {currency_symbol}", "#10b981")
        self.card_limit = self.create_info_card(self.i18n.get_message("credit_limit"), f"0.00 {currency_symbol}", "#3b82f6")
        
        header_layout.addLayout(customer_layout)
        header_layout.addSpacing(40)
        header_layout.addWidget(self.card_balance)
        header_layout.addWidget(self.card_limit)
        header_layout.addStretch()
        
        # التاريخ ورقم الفاتورة
        meta_layout = QVBoxLayout()
        self.lbl_invoice_no = QLabel(self.i18n.get_message("invoice_new"))
        self.lbl_invoice_no.setObjectName("InvoiceNo")
        self.lbl_date = QLabel(datetime.now().strftime("%Y-%m-%d"))
        self.lbl_date.setAlignment(Qt.AlignRight)
        
        meta_layout.addWidget(self.lbl_invoice_no)
        meta_layout.addWidget(self.lbl_date)
        header_layout.addLayout(meta_layout)
        main_layout.addWidget(header_frame)
        
        # ============================================================
        # ZONE 2: جدول المنتجات (Product Grid)
        # ============================================================
        body_frame = QFrame()
        body_frame.setObjectName("Zone2")
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(20, 20, 20, 10)
        
        # شريط البحث الذكي
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.i18n.get_message("search_product"))
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("font-size: 16px; padding: 0 15px; border: 2px solid #3b82f6; border-radius: 8px;")
        # الإصلاح 1: منع Enter من إغلاق النافذة - جعل البحث هو الافتراضي
        self.search_input.setFocusPolicy(Qt.StrongFocus)
        
        search_layout.addWidget(self.search_input)
        body_layout.addLayout(search_layout)
        
        # الجدول (نستخدم QTableWidget للسهولة البصرية، لكن البيانات في cart_items)
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # زيادة للأعمدة
        self.table.setHorizontalHeaderLabels([
            self.i18n.get_message("table_id"),
            self.i18n.get_message("table_product"),
            self.i18n.get_message("table_stock"),
            self.i18n.get_message("table_unit"),
            self.i18n.get_message("table_quantity"),
            self.i18n.get_message("table_price"),
            self.i18n.get_message("table_discount"),
            self.i18n.get_message("table_total"),
            self.i18n.get_message("table_delete")
        ])
        
        # تنسيق الجدول - تحسين الحجم لسهولة العرض والتعديل
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID (مخفي لاحقاً)
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # اسم المنتج (العمود الرئيسي)
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # المخزون - حجم معقول
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # الوحدة - حجم معقول
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # الكمية - حجم معقول للتعديل
        header.setSectionResizeMode(5, QHeaderView.Interactive)  # السعر - حجم معقول
        header.setSectionResizeMode(6, QHeaderView.Interactive)  # الخصم - حجم معقول
        header.setSectionResizeMode(7, QHeaderView.Interactive)  # الإجمالي - حجم معقول
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # زر الحذف
        
        # تحديد أحجام أولية معقولة للأعمدة
        header.resizeSection(2, 100)  # المخزون
        header.resizeSection(3, 80)  # الوحدة
        header.resizeSection(4, 100)  # الكمية (أكبر للتعديل)
        header.resizeSection(5, 120)  # السعر
        header.resizeSection(6, 100)  # الخصم
        header.resizeSection(7, 120)  # الإجمالي
        
        self.table.setColumnHidden(0, True)  # إخفاء ID
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setRowHeight(0, 60)  # زيادة ارتفاع الصفوف لسهولة التعديل
        # الإصلاح 5: تفعيل عجلة التحكم (Scrollbar) عند الحاجة
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # تحسين الخط والمسافات لسهولة القراءة والتعديل
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #f1f5f9;
                font-size: 15px;
            }
            QTableWidget::item {
                padding: 8px;
                min-height: 40px;
            }
            QTableWidget::item:selected {
                background-color: #eff6ff;
            }
        """)
        
        # ربط حدث التعديل في الجدول
        self.table.itemChanged.connect(self.on_table_change)
        
        body_layout.addWidget(self.table)
        main_layout.addWidget(body_frame, stretch=1)
        
        # ============================================================
        # ZONE 3: الفوتر واللوجستيات (Footer)
        # ============================================================
        footer_frame = QFrame()
        footer_frame.setObjectName("Zone3")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 20, 20, 20)
        
        # 3.1 اللوجستيات (يسار)
        logistics_layout = QVBoxLayout()
        
        # حالة الفاتورة
        logistics_layout.addWidget(QLabel(self.i18n.get_message("invoice_status") + ":"))
        self.combo_status = QComboBox()
        self.combo_status.addItems([
            self.i18n.get_message("invoice_status_draft"),
            self.i18n.get_message("invoice_status_confirmed"),
            self.i18n.get_message("invoice_status_paid"),
            self.i18n.get_message("invoice_status_partial"),
            self.i18n.get_message("invoice_status_cancelled")
        ])
        self.combo_status.setEnabled(True)  # تفعيل التعديل - يمكن للمستخدم تغيير الحالة
        logistics_layout.addWidget(self.combo_status)
        
        # طريقة الدفع
        logistics_layout.addWidget(QLabel(self.i18n.get_message("payment_method") + ":"))
        self.combo_payment = QComboBox()
        self.combo_payment.addItems([
            self.i18n.get_message("payment_cash"),
            self.i18n.get_message("payment_card"),
            self.i18n.get_message("payment_transfer"),
            self.i18n.get_message("payment_credit")
        ])
        logistics_layout.addWidget(self.combo_payment)
        
        # المبلغ المدفوع (قابل للتعديل)
        logistics_layout.addWidget(QLabel(self.i18n.get_message("paid_amount") + ":"))
        self.paid_amount_spin = QDoubleSpinBox()
        self.paid_amount_spin.setMinimum(0.0)
        self.paid_amount_spin.setMaximum(999999999.0)
        self.paid_amount_spin.setValue(0.0)
        currency_symbol = self.i18n.get_message("currency_symbol")
        self.paid_amount_spin.setSuffix(f" {currency_symbol}")
        self.paid_amount_spin.setDecimals(2)
        self.paid_amount_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.paid_amount_spin.valueChanged.connect(self.on_paid_amount_changed)
        logistics_layout.addWidget(self.paid_amount_spin)
        
        # المبلغ المتبقي (للقراءة فقط - يُحسب تلقائياً)
        logistics_layout.addWidget(QLabel(self.i18n.get_message("remaining_amount") + ":"))
        currency_symbol = self.i18n.get_message("currency_symbol")
        self.lbl_remaining_amount = QLabel(f"0.00 {currency_symbol}")
        self.lbl_remaining_amount.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
        logistics_layout.addWidget(self.lbl_remaining_amount)
        
        # ملاحظات
        logistics_layout.addWidget(QLabel(self.i18n.get_message("invoice_notes_label") + ":"))
        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText(self.i18n.get_message("invoice_notes"))
        logistics_layout.addWidget(self.input_notes)
        logistics_layout.addStretch()
        
        # 3.2 الملخص المالي (يمين)
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(10)
        
        self.lbl_subtotal = self.create_total_row(totals_layout, self.i18n.get_message("subtotal_label") + ":", "0.00")
        self.lbl_discount_total = self.create_total_row(totals_layout, self.i18n.get_message("total_discount") + ":", "0.00", color="#ef4444")
        
        # حقل الضريبة القابل للتعديل
        tax_row = QHBoxLayout()
        tax_label = QLabel(self.i18n.get_message("tax_percent"))
        tax_label.setStyleSheet("color: #64748b; font-size: 14px;")
        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setMinimum(0.0)
        self.tax_rate_spin.setMaximum(100.0)
        self.tax_rate_spin.setValue(0.0)
        self.tax_rate_spin.setSuffix(" %")
        self.tax_rate_spin.setDecimals(2)
        self.tax_rate_spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                padding: 5px;
                font-size: 14px;
                min-width: 80px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #3b82f6;
            }
        """)
        self.tax_rate_spin.valueChanged.connect(self.on_tax_rate_changed)
        tax_row.addWidget(tax_label)
        tax_row.addWidget(self.tax_rate_spin)
        tax_row.addStretch()
        totals_layout.addLayout(tax_row)
        
        # قيمة الضريبة المحسوبة
        self.lbl_tax_total = self.create_total_row(totals_layout, self.i18n.get_message("tax_amount") + ":", "0.00")
        
        # خط فاصل
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #cbd5e1;")
        totals_layout.addWidget(line)
        
        # الإجمالي النهائي
        currency_symbol = self.i18n.get_message("currency_symbol")
        self.lbl_grand_total = QLabel(f"0.00 {currency_symbol}")
        self.lbl_grand_total.setObjectName("GrandTotal")
        self.lbl_grand_total.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.lbl_grand_total)
        
        # 3.3 أزرار الإجراءات
        actions_layout = QHBoxLayout()
        self.btn_cancel = QPushButton(self.i18n.get_message("cancel_button"))
        # الإصلاح 1: منع Enter من إغلاق النافذة
        self.btn_cancel.setDefault(False)
        self.btn_cancel.setAutoDefault(False)
        
        # زر إلغاء الفاتورة (يظهر فقط في وضع التعديل)
        self.btn_cancel_invoice = QPushButton("❌ إلغاء الفاتورة")
        self.btn_cancel_invoice.setObjectName("BtnDanger")
        self.btn_cancel_invoice.setMinimumHeight(50)
        self.btn_cancel_invoice.setCursor(Qt.PointingHandCursor)
        self.btn_cancel_invoice.setDefault(False)
        self.btn_cancel_invoice.setAutoDefault(False)
        self.btn_cancel_invoice.setVisible(self.is_edit_mode)  # يظهر فقط في وضع التعديل
        self.btn_cancel_invoice.setStyleSheet("""
            QPushButton#BtnDanger {
                background-color: #dc2626;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#BtnDanger:hover {
                background-color: #b91c1c;
            }
            QPushButton#BtnDanger:pressed {
                background-color: #991b1b;
            }
        """)
        
        self.btn_save = QPushButton(self.i18n.get_message("save_print_button"))
        self.btn_save.setObjectName("BtnPrimary")
        self.btn_save.setMinimumHeight(50)
        self.btn_save.setCursor(Qt.PointingHandCursor)
        # الإصلاح 1: منع Enter من إغلاق النافذة
        self.btn_save.setDefault(False)
        self.btn_save.setAutoDefault(False)
        
        actions_layout.addWidget(self.btn_cancel)
        if self.is_edit_mode:
            actions_layout.addWidget(self.btn_cancel_invoice)
        actions_layout.addWidget(self.btn_save)
        
        # تجميع الفوتر
        footer_layout.addLayout(logistics_layout, stretch=1)
        footer_layout.addSpacing(50)
        
        right_panel = QVBoxLayout()
        right_panel.addLayout(totals_layout)
        right_panel.addSpacing(20)
        right_panel.addLayout(actions_layout)
        
        footer_layout.addLayout(right_panel, stretch=1)
        main_layout.addWidget(footer_frame)
        
        # ربط الأزرار
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self.save_invoice)
        if self.is_edit_mode:
            self.btn_cancel_invoice.clicked.connect(self.cancel_invoice_handler)
            # التأكد من أن الزر مرئي ومفعل
            self.btn_cancel_invoice.setVisible(True)
            self.btn_cancel_invoice.setEnabled(True)
        
        # الإصلاح 1: منع Enter من إغلاق النافذة - التأكد من عدم وجود default button
        self.btn_save.setAutoDefault(False)  # منع التفعيل التلقائي عند Enter
        self.btn_cancel.setAutoDefault(False)  # منع التفعيل التلقائي عند Enter
        self.btn_cancel.setAutoDefault(False)
        self.btn_save.setDefault(False)  # إزالة الافتراضي
        
        # ربط تغيير العميل
        self.combo_customer.currentIndexChanged.connect(self.on_customer_changed)
    
    # --- دوال مساعدة للواجهة ---
    def create_info_card(self, title, value, color):
        """إنشاء بطاقة معلومات حية - الإصلاح 3: توسيع المساحة"""
        card = QFrame()
        card.setStyleSheet(f"background: white; border: 1px solid #e2e8f0; border-radius: 12px; border-right: 5px solid {color};")
        # الإصلاح 3: زيادة العرض الأدنى من 150 إلى 180
        card.setMinimumWidth(180)
        l = QVBoxLayout(card)
        # زيادة المسافات الداخلية لتجنب التداخل
        l.setContentsMargins(15, 12, 15, 12)
        l.setSpacing(5)
        t = QLabel(title)
        t.setStyleSheet("color: #64748b; font-size: 11px; font-weight: normal;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        l.addWidget(t)
        l.addWidget(v)
        return card
    
    def create_total_row(self, layout, text, value, color="#1e293b"):
        """إنشاء صف في الملخص المالي"""
        row = QHBoxLayout()
        l = QLabel(text)
        l.setStyleSheet("color: #64748b; font-size: 14px;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 15px;")
        v.setAlignment(Qt.AlignRight)
        row.addWidget(l)
        row.addWidget(v)
        layout.addLayout(row)
        return v
    
    def setup_styles(self):
        """إعداد الأنماط - تصميم احترافي Modern Business Theme"""
        self.setStyleSheet("""
            QDialog { background-color: #f1f5f9; font-family: 'Segoe UI', sans-serif; }
            #Zone1, #Zone2, #Zone3 { background-color: white; border-bottom: 1px solid #e2e8f0; }
            #Zone2 { margin: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
            #Zone3 { border-top: 1px solid #e2e8f0; }
            QTableWidget { border: none; gridline-color: #f1f5f9; font-size: 14px; }
            QHeaderView::section { background: #f8fafc; border: none; padding: 10px; color: #475569; font-weight: bold; }
            #BtnPrimary { 
                background-color: #3b82f6; color: white; border-radius: 6px; 
                font-size: 16px; font-weight: bold; border: none;
            }
            #BtnPrimary:hover { background-color: #2563eb; }
            #GrandTotal { font-size: 32px; font-weight: 800; color: #059669; }
            #LabelDim { color: #64748b; }
            #InvoiceNo { font-size: 18px; font-weight: bold; color: #3b82f6; }
        """)
    
    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        # F10 - حفظ وطباعة
        save_shortcut = QShortcut(QKeySequence("F10"), self)
        save_shortcut.activated.connect(self.save_invoice)
        
        # Escape - إلغاء
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self.reject)
    
    # ============================================================
    # 🧠 الجزء الثاني: المنطق والعقل (The Logic Engine)
    # ============================================================
    
    def load_initial_data(self):
        """تحميل العملاء والمنتجات عند الفتح"""
        # 1. تحميل العملاء
        try:
            customers = self.customer_manager.get_all_customers()
            self.combo_customer.clear()
            self.combo_customer.addItem("-- عميل نقدي --", None)
            for customer in customers:
                if customer.is_active:
                    self.combo_customer.addItem(f"{customer.name} - {customer.phone or 'بدون هاتف'}", customer.id)
        except Exception as e:
            self.logger.error(f"خطأ في تحميل العملاء: {e}")
    
    def setup_smart_search(self):
        """إعداد البحث الذكي مع الإكمال التلقائي (Autocomplete)"""
        try:
            # تحميل قائمة المنتجات للكاش (Name + Barcode)
            # استخدام ProductManager للحصول على المنتجات
            all_products = self.product_manager.get_all_products(active_only=True)
            
            search_list = []
            self.product_map = {}  # خريطة للوصول السريع للمنتج
            
            for product in all_products:
                # إضافة الاسم والباركود للقائمة
                search_list.append(product.name)
                if product.barcode:
                    search_list.append(product.barcode)
                
                # تخزين البيانات (تحويل Product إلى dict للسهولة)
                product_dict = {
                    'id': product.id,
                    'name': product.name,
                    'barcode': product.barcode,
                    'selling_price': float(product.selling_price),
                    'current_stock': product.current_stock,
                    'unit': product.unit
                }
                self.product_map[product.name] = product_dict
                if product.barcode:
                    self.product_map[product.barcode] = product_dict
            
            # إعداد الـ Completer
            completer = QCompleter(search_list)
            completer.setFilterMode(Qt.MatchContains)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.search_input.setCompleter(completer)
            
            # ⚡ ربط زر Enter للتنفيذ الفوري (القاعدة 3: سرعة الكاشير)
            self.search_input.returnPressed.connect(self.on_search_enter)
        except Exception as e:
            self.logger.error(f"خطأ في إعداد البحث الذكي: {e}")
    
    def on_search_enter(self):
        """عند ضغط Enter في البحث - الإصلاح 1+2+3: منع إغلاق النافذة + بحث مرن + دعم الباركود"""
        query = self.search_input.text().strip()
        
        # DEBUG: طباعة للتشخيص
        if self.logger:
            self.logger.debug(f"DEBUG: البحث عن '{query}'")
        print(f"DEBUG: Searching for '{query}'")  # للتحقق السريع
        
        if not query:
            # الإصلاح 1: إذا كان البحث فارغاً، لا نفعل شيئاً ولا نغلق النافذة
            return
        
        # تهيئة المتغير
        product = None
        
        # الإصلاح 3: استخراج الباركود من النص (مثل "منتج 1000 (1391881226731)")
        import re
        barcode_match = re.search(r'\((\d+)\)', query)
        if barcode_match:
            barcode = barcode_match.group(1)
            product = self.product_map.get(barcode)
            if product:
                print(f"DEBUG: Found by extracted barcode: {barcode}")
            else:
                # البحث بالباركود المستخرج
                query = barcode
        
        # 1. البحث المباشر (مطابقة تامة) - الإصلاح 3: دعم الباركود
        if not product:
            product = self.product_map.get(query)
        
        # 2. البحث "الذكي" (بدون همزات أو بحث جزئي) - الإصلاح 3: دعم الباركود
        if not product:
            # تنظيف النص من التشكيل (اختياري) والبحث الجزئي
            matches = [p for name, p in self.product_map.items() if query.lower() in name.lower() or query == str(p.get('barcode', ''))]
            
            if len(matches) >= 1:
                # إذا وجدنا أي تطابق، نأخذ الأول فوراً (لسرعة الكاشير)
                product = matches[0]
                if self.logger:
                    self.logger.debug(f"DEBUG: Found match: {product['name']}")
                print(f"DEBUG: Found match: {product['name']}")
            else:
                if self.logger:
                    self.logger.debug("DEBUG: Product NOT found!")
                print("DEBUG: Product NOT found!")
                # 🗣️ القاعدة 5: لا تترك المستخدم يخمن (Feedback Loop)
                QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("product_not_found", product=query))
                self.search_input.selectAll()
                # الإصلاح 1: إعادة التركيز على البحث بعد الرسالة
                QTimer.singleShot(100, lambda: self.search_input.setFocus())
                return
        
        # إضافة المنتج للسلة
        try:
            self.add_product_to_cart(product)
            if self.logger:
                self.logger.debug(f"✅ تم إضافة المنتج: {product['name']}")
            print(f"✅ تم إضافة المنتج: {product['name']} - عدد المنتجات في السلة: {len(self.cart_items)}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة المنتج: {e}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('add_product_failed')}: {e}")
            # الإصلاح 1: إعادة التركيز على البحث بعد الخطأ
            QTimer.singleShot(100, lambda: self.search_input.setFocus())
            return
        
        # تنظيف وإعادة التركيز (⚡ القاعدة 3: سرعة الكاشير)
        self.search_input.clear()
        # الإصلاح 1+2: إعادة التركيز على البحث بعد الإضافة (لإضافة منتجات متعددة)
        QTimer.singleShot(50, lambda: self.search_input.setFocus())
    
    def add_product_to_cart(self, product_data):
        """إضافة منتج للسلة (تحديث الذاكرة + الجدول) - مع التحقق من المخزون"""
        product_id = product_data['id']
        available_stock = int(product_data['current_stock'])
        
        # الإصلاح 2: التحقق من المخزون قبل الإضافة
        if available_stock <= 0:
            QMessageBox.warning(
                self, 
                self.i18n.get_message("warning"), 
                self.i18n.get_message("product_out_of_stock", product=product_data['name'], stock=available_stock)
            )
            self.search_input.selectAll()
            QTimer.singleShot(100, lambda: self.search_input.setFocus())
            return
        
        # 1. هل المنتج موجود مسبقاً؟ (زيادة الكمية)
        for row, item in enumerate(self.cart_items):
            if item['id'] == product_id:
                new_qty = item['qty'] + Decimal('1')
                # الإصلاح 2: التحقق من المخزون قبل زيادة الكمية
                if new_qty > available_stock:
                    QMessageBox.warning(
                        self,
                        "تنبيه",
                        f"لا يمكن إضافة المزيد من '{item['name']}'!\n\n"
                        f"الكمية الحالية في السلة: {item['qty']}\n"
                        f"المخزون المتاح: {available_stock}\n"
                        f"الحد الأقصى المسموح: {available_stock}"
                    )
                    return
                
                item['qty'] = new_qty
                # تحديث الكمية في الجدول
                self.table.blockSignals(True)
                qty_item = self.table.item(row, 4)
                if qty_item:
                    qty_item.setText(str(item['qty']))
                self.table.blockSignals(False)
                self.recalc_row(row)  # إعادة حساب السطر
                # تمرير الجدول للسطر المحدث
                self.table.scrollToItem(self.table.item(row, 1))
                self.table.selectRow(row)
                print(f"✅ تم تحديث الكمية للمنتج: {item['name']} - الكمية الجديدة: {item['qty']}")
                return
        
        # 2. إضافة منتج جديد
        # 🚫 القاعدة 1: استخدام Decimal للأموال والكميات لتفادي أخطاء التقريب
        item = {
            'id': product_id,
            'name': product_data['name'],
            'stock': available_stock,
            'unit': product_data.get('unit', 'قطعة'),
            'price': to_decimal(product_data['selling_price']),
            'qty': to_decimal(1),
            'discount': to_decimal(0),  # الإصلاح 3: الخصم صفر افتراضياً
            'total': to_decimal(0)  # سيحسب فوراً
        }
        
        self.cart_items.append(item)
        row_idx = len(self.cart_items) - 1
        
        # إضافة سطر للجدول وتعبئته
        self.table.insertRow(row_idx)
        self.render_table_row(row_idx, item)
        self.recalc_row(row_idx)  # حساب السطر لأول مرة
        
        # تمرير الجدول للأسفل
        self.table.scrollToBottom()
        self.table.selectRow(row_idx)
        print(f"✅ تم إضافة منتج جديد: {item['name']} - إجمالي المنتجات في السلة: {len(self.cart_items)}")
    
    def render_table_row(self, row_idx, item):
        """رسم بيانات السطر في الجدول (عرض فقط)"""
        # تعبئة الخلايا (Columns: ID, Product, Stock, Unit, Qty, Price, Discount, Total, Actions)
        
        # 0. ID (مخفي)
        self.table.setItem(row_idx, 0, QTableWidgetItem(str(item['id'])))
        
        # 1. المنتج
        self.table.setItem(row_idx, 1, QTableWidgetItem(item['name']))
        
        # 2. المخزون (تلوين تحذيري)
        stock_item = QTableWidgetItem(str(item['stock']))
        stock_item.setTextAlignment(Qt.AlignCenter)
        if item['stock'] <= 0:
            stock_item.setForeground(QColor("red"))
            stock_item.setBackground(QColor("#fee2e2"))
        self.table.setItem(row_idx, 2, stock_item)
        
        # 3. الوحدة
        self.table.setItem(row_idx, 3, QTableWidgetItem(item['unit']))
        
        # 4. الكمية (قابلة للتعديل) - الإصلاح 1: تحسين قابلية التعديل
        qty_item = QTableWidgetItem(str(item['qty']))
        qty_item.setTextAlignment(Qt.AlignCenter)
        qty_item.setBackground(QColor("#f0fdf4"))  # أخضر فاتح
        qty_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)  # قابل للتعديل
        self.table.setItem(row_idx, 4, qty_item)
        
        # 5. السعر (للقراءة فقط) - الإصلاح 3: السعر يأتي من المخزون ولا يمكن تعديله
        price_item = QTableWidgetItem(f"{item['price']:.2f}")
        price_item.setTextAlignment(Qt.AlignCenter)
        price_item.setFlags(Qt.ItemIsEnabled)  # للقراءة فقط - لا يمكن التعديل
        price_item.setBackground(QColor("#f8fafc"))  # لون رمادي فاتح للدلالة على أنه للقراءة فقط
        self.table.setItem(row_idx, 5, price_item)
        
        # 6. الخصم (قابل للتعديل) - الإصلاح 1: تحسين قابلية التعديل
        discount_item = QTableWidgetItem(str(item['discount']))
        discount_item.setTextAlignment(Qt.AlignCenter)
        discount_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)  # قابل للتعديل
        self.table.setItem(row_idx, 6, discount_item)
        
        # 7. الإجمالي (للقراءة فقط)
        total_item = QTableWidgetItem(f"{item['total']:.2f}")
        total_item.setFlags(Qt.ItemIsEnabled)
        total_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table.setItem(row_idx, 7, total_item)
        
        # 8. زر الحذف (أيقونة) - الإصلاح 4: تحسين المحاذاة والتنسيق
        btn_del = QPushButton("❌")
        btn_del.setFlat(True)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setFixedSize(30, 30)  # حجم ثابت للزر
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 18px;
                color: #ef4444;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-radius: 4px;
            }
        """)
        # الإصلاح 2: استخدام functools.partial لتجنب مشكلة closure في lambda
        from functools import partial
        btn_del.clicked.connect(partial(self.remove_item, row_idx))
        self.table.setCellWidget(row_idx, 8, btn_del)
        
        # الإصلاح 4: محاذاة الزر في المنتصف
        self.table.setRowHeight(row_idx, 50)  # ارتفاع ثابت للصف
    
    def on_table_change(self, item):
        """معالجة تعديل الكمية أو الخصم من الجدول"""
        if self.table.signalsBlocked():  # لتجنب الحلقات المفرغة
            return
        
        row = item.row()
        col = item.column()
        
        try:
            # نحصل على القيمة الجديدة
            val_text = item.text()
            
            # الكمية (العمود 4) - الإصلاح 2: التحقق من المخزون
            if col == 4:
                new_qty = to_decimal(val_text)
                if new_qty <= 0:
                    raise ValueError("الكمية يجب أن تكون أكبر من صفر")
                
                # التحقق من المخزون المتاح
                available_stock = self.cart_items[row]['stock']
                if new_qty > available_stock:
                    QMessageBox.warning(
                        self,
                        self.i18n.get_message("warning"),
                        self.i18n.get_message("quantity_exceeds_stock", qty=int(new_qty), stock=available_stock) + "\n\n"
                        f"الكمية المطلوبة: {new_qty}\n"
                        f"المخزون المتاح: {available_stock}"
                    )
                    # إعادة القيمة القديمة
                    self.table.blockSignals(True)
                    self.table.item(row, 4).setText(str(self.cart_items[row]['qty']))
                    self.table.blockSignals(False)
                    return
                
                self.cart_items[row]['qty'] = new_qty
                self.recalc_row(row)
            
            # السعر (العمود 5) - الإصلاح 3: السعر للقراءة فقط (لا يمكن التعديل)
            elif col == 5:
                # لا يمكن تعديل السعر - إعادة القيمة القديمة
                self.table.blockSignals(True)
                self.table.item(row, 5).setText(f"{self.cart_items[row]['price']:.2f}")
                self.table.blockSignals(False)
                QMessageBox.information(
                    self,
                    "معلومة",
                    "السعر يأتي من المخزون ولا يمكن تعديله من هنا."
                )
            
            # الخصم (العمود 6)
            elif col == 6:
                self.cart_items[row]['discount'] = to_decimal(val_text)
                self.recalc_row(row)
        
        except Exception as e:
            # إذا أدخل المستخدم قيمة خاطئة، نعيد القيمة القديمة
            self.logger.warning(f"خطأ في تعديل القيمة: {e}")
            # إعادة رسم السطر بالقيمة القديمة
            self.render_table_row(row, self.cart_items[row])
    
    def recalc_row(self, row):
        """إعادة حساب سطر واحد وتحديث الإجماليات"""
        item = self.cart_items[row]
        
        # استخدام دوال math_utils
        item['total'] = calculate_line_total(item['price'], item['qty'], item['discount'])
        
        # تحديث خلية الإجمالي في الجدول فقط (بدون إعادة رسم كل شيء)
        self.table.blockSignals(True)  # تجميد الإشارات لحظياً
        if self.table.item(row, 7):
            self.table.item(row, 7).setText(f"{item['total']:.2f}")
        self.table.blockSignals(False)
        
        self.calculate_invoice_totals()
    
    def remove_item(self, row):
        """حذف منتج من السلة - الإصلاح 2: تحسين الحذف"""
        if 0 <= row < len(self.cart_items):
            # الإصلاح 2: تأكيد قبل الحذف
            reply = QMessageBox.question(
                self, 
                "تأكيد الحذف", 
                f"هل تريد حذف '{self.cart_items[row]['name']}' من الفاتورة؟",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # حذف المنتج
            self.cart_items.pop(row)
            
            # إعادة رسم الجدول بالكامل (لضمان تحديث جميع الأزرار)
            self.table.clearContents()
            self.table.setRowCount(0)
            
            for i, item in enumerate(self.cart_items):
                self.table.insertRow(i)
                self.render_table_row(i, item)
            
            self.calculate_invoice_totals()
            
            # إعادة التركيز على البحث بعد الحذف
            QTimer.singleShot(50, lambda: self.search_input.setFocus())
    
    def on_tax_rate_changed(self, value):
        """معالجة تغيير نسبة الضريبة"""
        self.tax_rate = Decimal(str(value))
        self.calculate_invoice_totals()
    
    def on_paid_amount_changed(self, value):
        """معالجة تغيير المبلغ المدفوع"""
        self.paid_amount = to_decimal(str(value))
        self.calculate_invoice_totals()
    
    def calculate_invoice_totals(self):
        """حساب إجمالي الفاتورة (Zone 3) - مع دعم الضريبة والمبلغ المدفوع"""
        # استخدام math_utils للحسابات الدقيقة
        subtotal = calculate_subtotal([item['total'] for item in self.cart_items])
        
        # الخصم العام صفر افتراضياً (يمكن إضافته لاحقاً من واجهة المستخدم)
        global_discount = to_decimal(0)
        
        # استخدام نسبة الضريبة من الحقل القابل للتعديل
        tax_rate = self.tax_rate
        tax = calculate_tax_amount(subtotal - global_discount, global_discount, tax_rate)
        
        # الإجمالي النهائي
        grand_total = calculate_grand_total(subtotal, global_discount, tax)
        
        # حساب المبلغ المتبقي
        remaining_amount = grand_total - self.paid_amount
        
        # تحديث حالة الفاتورة تلقائياً
        if self.paid_amount >= grand_total:
            status = "مدفوعة"
        elif self.paid_amount > 0:
            status = "مدفوعة جزئياً"
        elif self.is_edit_mode:
            status = "مؤكدة"  # فاتورة موجودة
        else:
            status = "مسودة"  # فاتورة جديدة
        
        # تحديث الواجهة
        self.lbl_subtotal.setText(format_currency(subtotal))
        self.lbl_discount_total.setText(format_currency(global_discount))
        # تحديث قيمة الضريبة المحسوبة
        self.lbl_tax_total.setText(format_currency(tax))
        self.lbl_grand_total.setText(format_currency(grand_total))
        
        # تحديث المبلغ المتبقي
        self.lbl_remaining_amount.setText(format_currency(remaining_amount))
        if remaining_amount > 0:
            self.lbl_remaining_amount.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
        else:
            self.lbl_remaining_amount.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
        
        # تحديث حالة الفاتورة
        index = self.combo_status.findText(status)
        if index >= 0:
            self.combo_status.setCurrentIndex(index)
    
    def on_customer_changed(self, index):
        """معالجة تغيير العميل"""
        customer_id = self.combo_customer.currentData()
        self.current_customer_id = customer_id
        
        if customer_id:
            try:
                customer = self.customer_manager.get_customer_by_id(customer_id)
                if customer:
                    # تحديث بطاقات المعلومات الحية
                    balance = format_currency(customer.current_balance or 0)
                    limit = format_currency(customer.credit_limit or 0)
                    
                    # الحصول على value_label من البطاقة
                    balance_card_layout = self.card_balance.layout()
                    limit_card_layout = self.card_limit.layout()
                    
                    if balance_card_layout and balance_card_layout.count() >= 2:
                        balance_label = balance_card_layout.itemAt(1).widget()
                        if balance_label:
                            balance_label.setText(balance)
                            # تلوين الرصيد حسب الحالة
                            if customer.current_balance and customer.current_balance > 0:
                                balance_label.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 14px;")
                            else:
                                balance_label.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
                    
                    if limit_card_layout and limit_card_layout.count() >= 2:
                        limit_label = limit_card_layout.itemAt(1).widget()
                        if limit_label:
                            limit_label.setText(limit)
            except Exception as e:
                self.logger.error(f"خطأ في تحميل بيانات العميل: {e}")
        else:
            # عميل نقدي
            balance_card_layout = self.card_balance.layout()
            limit_card_layout = self.card_limit.layout()
            
            if balance_card_layout and balance_card_layout.count() >= 2:
                balance_label = balance_card_layout.itemAt(1).widget()
                if balance_label:
                    currency_symbol = self.i18n.get_message("currency_symbol")
                    balance_label.setText(f"0.00 {currency_symbol}")
            
            if limit_card_layout and limit_card_layout.count() >= 2:
                limit_label = limit_card_layout.itemAt(1).widget()
                if limit_label:
                    currency_symbol = self.i18n.get_message("currency_symbol")
                    limit_label.setText(f"0.00 {currency_symbol}")
    
    def create_new_sale(self):
        """إنشاء فاتورة جديدة - بدون حفظ في قاعدة البيانات حتى يتم إضافة المنتجات"""
        try:
            # إنشاء كائن فاتورة جديد (في الذاكرة فقط)
            new_sale = Sale(
                id=None,
                invoice_number=self._generate_invoice_number(),
                sale_date=date.today(),
                status=SaleStatus.DRAFT,
                payment_method=PaymentMethod.CASH,
                items=[],
                subtotal=Decimal('0.00'),
                discount_amount=Decimal('0.00'),
                discount_percentage=Decimal('0.00'),
                tax_amount=Decimal('0.00'),
                tax_percentage=Decimal('0.00'),
                total_amount=Decimal('0.00'),
                paid_amount=Decimal('0.00'),
                remaining_amount=Decimal('0.00')
            )
            
            self.sale = new_sale
            self.lbl_invoice_no.setText(self.i18n.get_message("invoice_number", invoice_number=self.sale.invoice_number))
            
            if self.logger:
                self.logger.debug(f"✅ تم إنشاء فاتورة جديدة في الذاكرة: {self.sale.invoice_number}")
        
        except Exception as e:
            error_msg = f"خطأ في إنشاء فاتورة جديدة: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            QMessageBox.critical(self, self.i18n.get_message("error"), error_msg)
            self.reject()
    
    def _generate_invoice_number(self):
        """توليد رقم فاتورة جديد"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"INV-{timestamp}"
    
    def populate_form(self):
        """ملء النموذج ببيانات الفاتورة (للتعديل)"""
        if not self.sale:
            if self.logger:
                self.logger.warning("populate_form: self.sale is None")
            return
        
        try:
            if self.logger:
                self.logger.info(f"بدء ملء النموذج للفاتورة {self.sale.id}, عدد العناصر: {len(self.sale.items) if self.sale.items else 0}")
            # معلومات الفاتورة
            self.lbl_invoice_no.setText(self.i18n.get_message("invoice_number", invoice_number=self.sale.invoice_number))
            if self.sale.sale_date:
                self.lbl_date.setText(self.sale.sale_date.strftime("%Y-%m-%d"))
            
            # العميل
            if self.sale.customer_id:
                index = self.combo_customer.findData(self.sale.customer_id)
                if index >= 0:
                    self.combo_customer.setCurrentIndex(index)
            
            # تحديث نسبة الضريبة من الفاتورة
            if self.sale.tax_percentage:
                self.tax_rate = self.sale.tax_percentage
                self.tax_rate_spin.setValue(float(self.tax_rate))
            
            # تحديث المبلغ المدفوع
            if self.sale.paid_amount:
                self.paid_amount = self.sale.paid_amount
                self.paid_amount_spin.setValue(float(self.paid_amount))
            
            # تحديث حالة الفاتورة
            if self.sale.status:
                status_text = self.sale.status.value if hasattr(self.sale.status, 'value') else str(self.sale.status)
                index = self.combo_status.findText(status_text)
                if index >= 0:
                    self.combo_status.setCurrentIndex(index)
            
            # تحديث طريقة الدفع
            if self.sale.payment_method:
                payment_text = self.sale.payment_method.value if hasattr(self.sale.payment_method, 'value') else str(self.sale.payment_method)
                index = self.combo_payment.findText(payment_text)
                if index >= 0:
                    self.combo_payment.setCurrentIndex(index)
            
            # تحديث الملاحظات
            if self.sale.notes:
                self.input_notes.setText(self.sale.notes)
            
            # تحميل عناصر الفاتورة
            self.load_sale_items()
            
            # إعادة حساب المجاميع بعد تحميل البيانات
            self.calculate_invoice_totals()
        
        except Exception as e:
            self.logger.error(f"خطأ في ملء النموذج: {str(e)}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('invoice_load_failed')}: {str(e)}")
    
    def load_sale_items(self):
        """تحميل عناصر الفاتورة"""
        if not self.sale or not self.sale.id:
            return
        
        try:
            # التأكد من أن العناصر محملة (إذا لم تكن محملة، جلبها من قاعدة البيانات)
            sale_id = self.sale.id
            if not self.sale.items or len(self.sale.items) == 0:
                # إعادة تحميل الفاتورة مع العناصر
                reloaded_sale = self.sale_manager.get_sale_by_id(sale_id)
                if reloaded_sale:
                    self.sale = reloaded_sale
                else:
                    if self.logger:
                        self.logger.error(f"فشل في تحميل الفاتورة {sale_id}")
                    return
            
            # تحويل SaleItem إلى dict للتوافق مع cart_items
            self.cart_items.clear()  # مسح السلة أولاً
            for item in self.sale.items:
                if item:
                    # جلب معلومات المخزون من المنتج
                    try:
                        product = self.product_manager.get_product_by_id(item.product_id)
                        stock = product.current_stock if product else 0
                        unit = product.unit if product and hasattr(product, 'unit') else 'قطعة'
                    except:
                        stock = 0
                        unit = 'قطعة'
                    
                    item_dict = {
                        'id': item.product_id,
                        'name': item.product_name or 'منتج غير محدد',
                        'stock': stock,
                        'unit': unit,
                        'price': to_decimal(item.unit_price),
                        'qty': to_decimal(item.quantity),
                        'discount': to_decimal(item.discount_amount),
                        'total': to_decimal(item.total_amount)
                    }
                    self.cart_items.append(item_dict)
            
            # إعادة رسم الجدول
            self.table.clearContents()
            self.table.setRowCount(0)
            for i, item in enumerate(self.cart_items):
                self.table.insertRow(i)
                self.render_table_row(i, item)
            
            self.calculate_invoice_totals()
            
            if self.logger:
                self.logger.info(f"تم تحميل {len(self.cart_items)} عنصر من الفاتورة {self.sale.id}")
        
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل عناصر الفاتورة: {str(e)}")
                import traceback
                self.logger.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
            QMessageBox.warning(self, self.i18n.get_message("warning"), f"{self.i18n.get_message('invoice_items_load_failed')}:\n{str(e)}")
    
    # ============================================================
    # 💾 الحفظ الذري (Atomic Save) - قلب النظام
    # ============================================================
    
    def save_invoice(self):
        """حفظ الفاتورة باستخدام SaleManager (⚛️ القاعدة 2: الحفظ الذري)"""
        if not self.cart_items:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("empty_invoice"))
            return
        
        if QMessageBox.question(self, self.i18n.get_message("confirm"), self.i18n.get_message("save_print_confirm")) != QMessageBox.Yes:
            return
        
        try:
            # تعطيل الواجهة أثناء الحفظ
            self.setEnabled(False)
            
            # تحويل cart_items إلى SaleItem objects
            sale_items: List[SaleItem] = []
            for item in self.cart_items:
                sale_item = SaleItem(
                    id=None,
                    sale_id=None,
                    product_id=item['id'],
                    product_name=item['name'],
                    quantity=int(item['qty']),
                    unit_price=item['price'],
                    discount_amount=item['discount'],
                    total_amount=item['total']
                )
                sale_item.calculate_total()  # إعادة حساب الإجمالي
                sale_items.append(sale_item)
            
            # تحديث بيانات الفاتورة
            customer_id = self.combo_customer.currentData()
            if customer_id:
                customer = self.customer_manager.get_customer_by_id(customer_id)
                customer_name = customer.name if customer else None
                customer_phone = customer.phone if customer else None
            else:
                customer_id = None
                customer_name = None
                customer_phone = None
            
            # تحديد طريقة الدفع - تحويل النص إلى PaymentMethod
            payment_text = self.combo_payment.currentText()
            payment_method = PaymentMethod.CASH  # افتراضي
            if "بطاقة" in payment_text or "بنكية" in payment_text:
                payment_method = PaymentMethod.CARD
            elif "تحويل" in payment_text:
                payment_method = PaymentMethod.BANK_TRANSFER
            elif "آجل" in payment_text or "ذمم" in payment_text:
                payment_method = PaymentMethod.CREDIT
            
            # حساب المجاميع النهائية - استخدام نسبة الضريبة من الحقل القابل للتعديل
            subtotal = calculate_subtotal([item['total'] for item in self.cart_items])
            discount_amount = to_decimal(0)  # يمكن إضافته لاحقاً
            tax_rate = self.tax_rate  # استخدام نسبة الضريبة من الحقل القابل للتعديل
            tax_amount = calculate_tax_amount(subtotal, discount_amount, tax_rate)
            total_amount = calculate_grand_total(subtotal, discount_amount, tax_amount)
            
            # تحديث بيانات الفاتورة
            if not self.sale:
                self.create_new_sale()
            
            # الإصلاح 4: التأكد من وجود جميع الحقول المطلوبة قبل الحفظ
            from datetime import date, datetime
            
            self.sale.customer_id = customer_id
            self.sale.customer_name = customer_name
            self.sale.customer_phone = customer_phone
            self.sale.sale_date = date.today()  # التأكد من وجود sale_date
            self.sale.due_date = None  # يمكن إضافته لاحقاً
            
            # تحديد حالة الفاتورة من القائمة المنسدلة
            status_text = self.combo_status.currentText()
            status_mapping = {
                "مسودة": SaleStatus.DRAFT,
                "مؤكدة": SaleStatus.CONFIRMED,
                "مدفوعة": SaleStatus.PAID,
                "مدفوعة جزئياً": SaleStatus.PARTIALLY_PAID,
                "ملغية": SaleStatus.CANCELLED
            }
            self.sale.status = status_mapping.get(status_text, SaleStatus.CONFIRMED)
            
            self.sale.payment_method = payment_method
            self.sale.subtotal = subtotal
            self.sale.discount_amount = discount_amount
            self.sale.discount_percentage = Decimal('0')  # التأكد من وجود discount_percentage
            self.sale.tax_amount = tax_amount
            self.sale.tax_percentage = tax_rate  # استخدام نسبة الضريبة من الحقل القابل للتعديل
            self.sale.total_amount = total_amount
            # تحديث المبلغ المدفوع والمتبقي من الواجهة
            self.sale.paid_amount = self.paid_amount
            self.sale.remaining_amount = total_amount - self.paid_amount
            
            # 🔒 التحقق: إذا كان هناك مبلغ متبقي، لا يمكن حفظ الفاتورة بحالة "مدفوعة"
            if self.sale.status == SaleStatus.PAID and self.sale.remaining_amount > 0:
                QMessageBox.warning(
                    self, 
                    "خطأ في الحالة", 
                    f"لا يمكن حفظ الفاتورة بحالة 'مدفوعة' إذا كان هناك مبلغ متبقي.\n\n"
                    f"المبلغ الإجمالي: {format_currency(total_amount)}\n"
                    f"المبلغ المدفوع: {format_currency(self.paid_amount)}\n"
                    f"المبلغ المتبقي: {format_currency(self.sale.remaining_amount)}\n\n"
                    f"يرجى تغيير الحالة إلى 'مدفوعة جزئياً' أو 'مؤكدة'."
                )
                # تحديث الحالة تلقائياً بناءً على المبلغ المدفوع
                if self.paid_amount > 0:
                    self.sale.status = SaleStatus.PARTIALLY_PAID
                    # تحديث القائمة المنسدلة
                    index = self.combo_status.findText("مدفوعة جزئياً")
                    if index >= 0:
                        self.combo_status.setCurrentIndex(index)
                else:
                    self.sale.status = SaleStatus.CONFIRMED
                    # تحديث القائمة المنسدلة
                    index = self.combo_status.findText("مؤكدة")
                    if index >= 0:
                        self.combo_status.setCurrentIndex(index)
                return  # إيقاف الحفظ
            
            # ملاحظة: الحالة يتم تحديدها من combo_status أعلاه
            # يمكن إضافة منطق تلقائي هنا إذا رغب المستخدم، لكن حالياً نستخدم القيمة المختارة يدوياً
            
            self.sale.notes = self.input_notes.text().strip() or None
            self.sale.created_by = None  # يمكن إضافته لاحقاً عند إضافة نظام المستخدمين
            self.sale.items = sale_items
            
            # ⚛️ الحفظ الذري باستخدام SaleManager (يدير المعاملات تلقائياً)
            if self.sale.id is None:
                # إنشاء فاتورة جديدة
                if self.logger:
                    self.logger.debug(f"محاولة حفظ الفاتورة: invoice_number={self.sale.invoice_number}, items_count={len(self.sale.items)}")
                
                sale_id = self.sale_manager.create_sale(self.sale)
                if sale_id:
                    self.sale.id = sale_id
                    if self.logger:
                        self.logger.info(f"✅ تم إنشاء فاتورة جديدة: {self.sale.invoice_number} (ID: {sale_id})")
                else:
                    # الحصول على تفاصيل الخطأ من السجلات
                    error_details = f"فشل في إنشاء الفاتورة في قاعدة البيانات.\n\n"
                    error_details += f"رقم الفاتورة: {self.sale.invoice_number}\n"
                    error_details += f"عدد العناصر: {len(self.sale.items)}\n"
                    error_details += f"المجموع: {self.sale.total_amount}\n\n"
                    error_details += "تحقق من السجلات (logs) لمزيد من التفاصيل."
                    raise Exception(error_details)
            else:
                # تحديث فاتورة موجودة
                if self.logger:
                    self.logger.debug(f"محاولة تحديث الفاتورة: ID={self.sale.id}, invoice_number={self.sale.invoice_number}")
                
                success = self.sale_manager.update_sale(self.sale)
                if not success:
                    error_details = f"فشل في تحديث الفاتورة في قاعدة البيانات.\n\n"
                    error_details += f"رقم الفاتورة: {self.sale.invoice_number}\n"
                    error_details += f"ID: {self.sale.id}\n"
                    error_details += f"عدد العناصر: {len(self.sale.items)}\n"
                    error_details += f"المجموع: {self.sale.total_amount}\n\n"
                    error_details += "تحقق من السجلات (logs) لمزيد من التفاصيل."
                    raise Exception(error_details)
                
                if self.logger:
                    self.logger.info(f"✅ تم تحديث الفاتورة: {self.sale.invoice_number} (ID: {self.sale.id})")
            
            # إطلاق الإشارات (تم إطلاقها تلقائياً في SaleManager.create_sale/update_sale)
            # لكن نؤكدها هنا للتأكد من التحديث الفوري لجميع الأقسام
            try:
                if self.is_edit_mode:
                    # عند التعديل
                    signals.sales_updated.emit()
                    signals.sale_updated.emit(self.sale.id)
                    signals.inventory_updated.emit()
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات التعديل: sales_updated, sale_updated({self.sale.id}), inventory_updated")
                else:
                    # عند الإنشاء
                    signals.sales_updated.emit()
                    signals.sale_created.emit(self.sale.id)
                    signals.inventory_updated.emit()
                    if self.logger:
                        self.logger.debug(f"✅ تم إطلاق إشارات الإنشاء: sales_updated, sale_created({self.sale.id}), inventory_updated")
            except Exception as e:
                if self.logger:
                    # تحسين رسالة التحذير لتكون أكثر وضوحاً
                    error_msg = str(e)
                    if "attempted relative import beyond top-level package" in error_msg:
                        self.logger.warning(
                            f"⚠️ فشل إطلاق الإشارات: مشكلة في الاستيراد النسبي. "
                            f"يتم استخدام استيراد مطلق الآن. التفاصيل: {error_msg}"
                        )
                    else:
                        self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {error_msg}")
            
            self.sale_completed.emit(self.sale)
            
            currency_symbol = self.i18n.get_message("currency_symbol")
            QMessageBox.information(
                self, 
                self.i18n.get_message("success"), 
                self.i18n.get_message("invoice_saved_success", 
                                     invoice_number=self.sale.invoice_number,
                                     total=total_amount,
                                     currency=currency_symbol)
            )
            
            self.accept()
        
        except Exception as e:
            self.logger.error(f"خطأ في حفظ الفاتورة: {str(e)}", exc_info=True)
            QMessageBox.critical(self, self.i18n.get_message("fatal_error"), f"{self.i18n.get_message('operation_failed')}: {e}")
        finally:
            self.setEnabled(True)
    
    def cancel_invoice_handler(self):
        """معالج إلغاء الفاتورة - يطلب التأكيد وسبب الإلغاء ثم يستدعي الدالة"""
        
        # 1. التحقق من وجود الفاتورة
        if not self.sale or not self.sale.id:
            QMessageBox.warning(self, "تحذير", "لا توجد فاتورة محفوظة لإلغائها")
            return
        
        # 2. التحقق من أن الفاتورة ليست ملغاة بالفعل
        # التحقق من الحالة بعدة طرق للتأكد من التوافق
        sale_status = self.sale.status
        if isinstance(sale_status, SaleStatus):
            status_value = sale_status.value if hasattr(sale_status, 'value') else str(sale_status)
        else:
            status_value = str(sale_status)
        
        if status_value == "ملغية" or status_value == "Cancelled" or sale_status == SaleStatus.CANCELLED:
            QMessageBox.information(self, "تنبيه", "هذه الفاتورة ملغاة بالفعل")
            return
        
        # 3. طلب التأكيد من المستخدم
        reply = QMessageBox.question(
            self,
            "تأكيد الإلغاء",
            f"هل أنت متأكد من رغبتك في إلغاء الفاتورة رقم {self.sale.invoice_number}؟\n\n"
            "⚠️ سيتم:\n"
            "• استعادة المخزون للمنتجات\n"
            "• تعديل رصيد العميل (إن وجد)\n"
            "• تغيير حالة الفاتورة إلى 'ملغاة'",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # 4. طلب سبب الإلغاء (اختياري لكن مفضل للتدقيق)
        reason, ok = QInputDialog.getText(
            self,
            "سبب الإلغاء",
            "الرجاء إدخال سبب الإلغاء (اختياري):",
            text=""
        )
        
        if not ok:
            return  # المستخدم ألغى العملية
        
        # إذا لم يدخل المستخدم سبباً، نستخدم سبب افتراضي
        if not reason.strip():
            reason = "إلغاء من المستخدم"
        
        # 5. تنفيذ العملية عبر SalesService
        try:
            # تغيير شكل المؤشر للانتظار
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.btn_cancel_invoice.setEnabled(False)
            self.setEnabled(False)
            
            # محاولة الحصول على معرف المستخدم من النافذة الأب
            current_user_id = getattr(self.parent(), 'current_user_id', getattr(self.parent(), 'user_id', 1)) if self.parent() else 1
            
            success = self.sales_service.cancel_invoice(
                sale_id=self.sale.id,
                cancellation_reason=reason.strip(),
                user_id=current_user_id
            )
            
            QApplication.restoreOverrideCursor()
            
            if success:
                # تحديث حالة الفاتورة في الذاكرة
                self.sale.status = SaleStatus.CANCELLED
                
                # تحديث الواجهة
                status_index = self.combo_status.findText(
                    self.i18n.get_message("invoice_status_cancelled")
                )
                if status_index >= 0:
                    self.combo_status.setCurrentIndex(status_index)
                
                # تحديث الملاحظات
                existing_notes = self.sale.notes or ""
                updated_notes = f"{existing_notes}\n[إلغاء] {reason} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                self.sale.notes = updated_notes
                
                # إطلاق الإشارات لتحديث الواجهات الأخرى
                try:
                    signals.sales_updated.emit()
                    signals.sale_updated.emit(self.sale.id)
                    signals.inventory_updated.emit()
                except Exception as sig_error:
                    if self.logger:
                        self.logger.warning(f"فشل إطلاق الإشارات: {sig_error}")
                
                # رسالة نجاح
                QMessageBox.information(
                    self,
                    "نجاح",
                    f"✅ تم إلغاء الفاتورة رقم {self.sale.invoice_number} واستعادة المخزون بنجاح."
                )
                
                # إغلاق النافذة وإرسال إشارة نجاح للنافذة الأم
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "خطأ",
                    "❌ حدث خطأ أثناء إلغاء الفاتورة.\nراجع السجلات للتفاصيل."
                )
                self.btn_cancel_invoice.setEnabled(True)
                self.setEnabled(True)
        
        except Exception as e:
            QApplication.restoreOverrideCursor()
            if self.logger:
                self.logger.error(f"UI Error cancelling invoice: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "خطأ",
                f"حدث خطأ غير متوقع:\n{str(e)}"
            )
            self.btn_cancel_invoice.setEnabled(True)
            self.setEnabled(True)
    
    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        # التحقق من وجود تغييرات غير محفوظة
        if self.cart_items and not self.is_edit_mode:
            reply = QMessageBox.question(
                self,
                self.i18n.get_message("close_without_save"),
                self.i18n.get_message("unsaved_invoice_warning"),
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
    # استخدام استيراد مطلق لتجنب مشكلة "attempted relative import beyond top-level package"
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.core.database_manager import DatabaseManager
    
    db = DatabaseManager(":memory:")
    db.initialize()
    
    dialog = SalesDialog(db)
    
    if dialog.exec() == QDialog.Accepted:
        print("تم حفظ الفاتورة بنجاح")
    else:
        print("تم إلغاء العملية")
    
    sys.exit()

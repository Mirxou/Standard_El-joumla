import logging
#!/usr/bin/env python3
"""
نافذة فاتورة المبيعات - Sales Dialog
واجهة شاملة لإنشاء وإدارة فواتير المبيعات مع دعم اللغة العربية
التصميم الجديد: 3-Zone Enterprise Layout
"""

import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, QRegularExpression, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QRegularExpressionValidator,
    QShortcut,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QCompleter,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.utils.ui_utils import prevent_double_click

# --- استيراد العقل والأدوات (The Core Dependencies) ---
from ...core.local_database_manager import LocalDatabaseManager
from ...core.signals import signals
from ...models.customer import CustomerManager
from ...models.product import ProductManager
from ...models.sale import PaymentMethod, Sale, SaleItem, SaleManager, SaleStatus
from ...services.sales_service import SalesService
from ...ui.widgets.quantum_notification import NotificationManager
from ...utils.i18n_api import I18n
from ...utils.logger import setup_logger
from ...utils.math_utils import (
    calculate_grand_total,
    calculate_line_total,
    calculate_subtotal,
    calculate_tax_amount,
    format_currency,
    to_decimal,
)


class SaleOperationWorker(QObject):
    """عامل خلفية لتنفيذ عمليات المبيعات (حفظ، تحديث، إلغاء) بدون تجميد الواجهة"""

    finished = Signal(bool, str, object)  # success, error_message, result_data

    def __init__(self, operation_type, manager, **kwargs):
        super().__init__()
        self.operation_type = operation_type
        self.manager = manager
        self.kwargs = kwargs

    def run(self):
        try:
            success = False
            result_data = None
            error_msg = ""

            if self.operation_type == "create":
                sale = self.kwargs.get("sale")
                sale_id = self.manager.create_sale(sale)
                if sale_id:
                    success = True
                    result_data = sale_id
                else:
                    error_msg = "فشل في إنشاء الفاتورة في قاعدة البيانات."

            elif self.operation_type == "update":
                sale = self.kwargs.get("sale")
                success = self.manager.update_sale(sale)
                if not success:
                    error_msg = "فشل في تحديث الفاتورة في قاعدة البيانات."

            elif self.operation_type == "cancel":
                sale_id = self.kwargs.get("sale_id")
                self.kwargs.get("reason")
                user_id = self.kwargs.get("user_id")
                # SalesService uses cancel_sale(sale_id, user_id)
                success = self.manager.cancel_sale(sale_id=sale_id, user_id=user_id)
                if not success:
                    error_msg = "حدث خطأ أثناء إلغاء الفاتورة."

            self.finished.emit(success, error_msg, result_data)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class SalesDialog(BaseDialog):
    """نافذة فاتورة المبيعات - تصميم 3-Zone Enterprise Layout"""

    # إشارات مخصصة
    sale_completed = Signal(object)  # Sale

    def __init__(self, db_manager: LocalDatabaseManager, sale: Optional[Sale] = None, parent=None):
        super().__init__(title="", parent=parent)
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

        if self.is_edit_mode:
            # self.setWindowTitle(...) # Handled by CustomTitleBar
            pass
        else:
            # self.setWindowTitle(...)
            pass

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.setModal(True)

        # حساب الأبعاد
        app = QApplication.instance()
        # [Existing Geometry Logic Kept Simplified]
        if app:
            screen = app.primaryScreen()
            if screen:
                screen_geometry = screen.geometry()
                self.resize(
                    int(screen_geometry.width() * 0.85),
                    int(screen_geometry.height() * 0.85),
                )

        # --- متغيرات الحالة (State Management) ---
        self.cart_items: List[Dict[str, Any]] = []
        self.current_customer_id = None
        self.tax_rate = Decimal("0")
        self.paid_amount = Decimal("0")

        # 1. بناء الواجهة
        self.setup_ui()
        self.setup_styles()
        self.setup_shortcuts()

        # 2. تحميل البيانات الأولية
        self.load_initial_data()
        self.setup_smart_search()

        if self.combo_customer.count() > 0:
            self.on_customer_changed(0)

        QTimer.singleShot(100, lambda: self.search_input.setFocus())

        if self.is_edit_mode:
            self.populate_form()
        else:
            self.create_new_sale()

    def setup_ui(self):
        """بناء تخطيط المناطق الثلاث (3-Zone Enterprise Layout) - Quantum Frameless Version"""
        layout = self.content_layout

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
        self.card_balance = self.create_info_card(
            self.i18n.get_message("current_balance"),
            f"0.00 {currency_symbol}",
            "#10b981",
        )
        self.card_limit = self.create_info_card(
            self.i18n.get_message("credit_limit"), f"0.00 {currency_symbol}", "#3b82f6"
        )

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
        layout.addWidget(header_frame)

        # حاوية القسمين (المنتجات + اللوجستيات) - تصميم POS الحديث
        pos_split_layout = QHBoxLayout()
        pos_split_layout.setSpacing(15)
        pos_split_layout.setContentsMargins(20, 10, 20, 20)
        layout.addLayout(pos_split_layout, stretch=1)

        # ============================================================
        # ZONE 2: جدول المنتجات (Product Grid)
        # ============================================================
        body_frame = QFrame()
        body_frame.setObjectName("Zone2")
        body_layout = QVBoxLayout(body_frame)
        body_layout.setContentsMargins(15, 15, 15, 10)

        # شريط البحث الذكي
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.i18n.get_message("search_product"))
        self.search_input.setFixedHeight(45)
        self.search_input.setStyleSheet("font-size: 16px; padding: 0 15px; border-radius: 8px;")
        # الإصلاح 1: منع Enter من إغلاق النافذة - جعل البحث هو الافتراضي
        self.search_input.setFocusPolicy(Qt.StrongFocus)

        search_layout.addWidget(self.search_input)
        body_layout.addLayout(search_layout)

        # الجدول (نستخدم QTableWidget للسهولة البصرية، لكن البيانات في cart_items)
        self.table = QTableWidget()
        self.table.setColumnCount(9)  # زيادة للأعمدة
        self.table.setHorizontalHeaderLabels(
            [
                self.i18n.get_message("table_id"),
                self.i18n.get_message("table_product"),
                self.i18n.get_message("table_stock"),
                self.i18n.get_message("table_unit"),
                self.i18n.get_message("table_quantity"),
                self.i18n.get_message("table_price"),
                self.i18n.get_message("table_discount"),
                self.i18n.get_message("table_total"),
                self.i18n.get_message("table_delete"),
            ]
        )

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
        pos_split_layout.addWidget(body_frame, stretch=7)

        # ============================================================
        # ZONE 3: اللوحة الجانبية للمبيعات (POS Sidebar)
        # ============================================================
        footer_frame = QFrame()
        footer_frame.setObjectName("Zone3")
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(0)

        from PySide6.QtWidgets import QFormLayout, QScrollArea

        # منطقة التمرير للمعلومات العلوية لتفادي التداخل
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background: transparent; } QWidget#ScrollContent { background: transparent; }"
        )

        scroll_content = QFrame()
        scroll_content.setObjectName("ScrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(16, 16, 16, 10)
        scroll_layout.setSpacing(16)

        # 3.1 حالة الفاتورة
        logistics_layout = QFormLayout()
        logistics_layout.setSpacing(10)
        logistics_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # حالة الفاتورة
        self.combo_status = QComboBox()
        self.combo_status.addItems(
            [
                self.i18n.get_message("invoice_status_draft"),
                self.i18n.get_message("invoice_status_confirmed"),
                self.i18n.get_message("invoice_status_paid"),
                self.i18n.get_message("invoice_status_partial"),
                self.i18n.get_message("invoice_status_cancelled"),
            ]
        )
        self.combo_status.setEnabled(True)
        self.combo_status.setMinimumHeight(38)
        # منع عجلة الماوس من تغيير الحالة عرضياً
        self.combo_status.wheelEvent = lambda e: None
        logistics_layout.addRow(self.i18n.get_message("invoice_status") + ":", self.combo_status)

        # ملاحظات
        self.input_notes = QLineEdit()
        self.input_notes.setPlaceholderText(self.i18n.get_message("invoice_notes"))
        self.input_notes.setMinimumHeight(38)
        logistics_layout.addRow(self.i18n.get_message("invoice_notes_label") + ":", self.input_notes)

        scroll_layout.addLayout(logistics_layout)

        # ============================================================
        # 3.2 طريقة الدفع - أزرار كبيرة (Button Group بدل ComboBox)
        # ============================================================
        payment_section = QFrame()
        payment_section.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 10px;
            }
        """)
        payment_section_layout = QVBoxLayout(payment_section)
        payment_section_layout.setContentsMargins(14, 12, 14, 12)
        payment_section_layout.setSpacing(10)

        lbl_pay_method = QLabel("💳 " + self.i18n.get_message("payment_method"))
        lbl_pay_method.setStyleSheet(
            "color: #94a3b8; font-size: 12px; font-weight: 600; border: none; background: transparent;"
        )
        payment_section_layout.addWidget(lbl_pay_method)

        # صف أزرار طريقة الدفع
        payment_btns_row1 = QHBoxLayout()
        payment_btns_row1.setSpacing(8)
        payment_btns_row2 = QHBoxLayout()
        payment_btns_row2.setSpacing(8)

        # تعريف مجموعة الأزرار
        self._payment_buttons = {}
        self._selected_payment = "cash"  # الافتراضي

        payment_options = [
            ("cash", "💵", self.i18n.get_message("payment_cash"), "#10b981"),
            ("card", "💳", self.i18n.get_message("payment_card"), "#3b82f6"),
            ("transfer", "🏦", self.i18n.get_message("payment_transfer"), "#8b5cf6"),
            ("credit", "📅", self.i18n.get_message("payment_credit"), "#f59e0b"),
        ]

        from functools import partial as _partial

        for i, (key, icon, label, color) in enumerate(payment_options):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setCheckable(True)
            btn.setMinimumHeight(56)
            btn.setMinimumWidth(80)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {{
                    background: #1e293b;
                    color: #94a3b8;
                    border: 2px solid #334155;
                    border-radius: 8px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 6px 4px;
                }}
                QPushButton:checked {{
                    background: {color}22;
                    color: {color};
                    border: 2px solid {color};
                }}
                QPushButton:hover:!checked {{
                    background: #334155;
                    color: #e2e8f0;
                    border-color: #475569;
                }}
            """)
            btn.clicked.connect(_partial(self._on_payment_btn_clicked, key))
            self._payment_buttons[key] = btn
            if i < 2:
                payment_btns_row1.addWidget(btn)
            else:
                payment_btns_row2.addWidget(btn)

        # تفعيل الزر الافتراضي
        self._payment_buttons["cash"].setChecked(True)

        payment_section_layout.addLayout(payment_btns_row1)
        payment_section_layout.addLayout(payment_btns_row2)

        # حقل المبلغ المدفوع - نصي كبير واضح
        lbl_paid = QLabel("💰 " + self.i18n.get_message("paid_amount"))
        lbl_paid.setStyleSheet(
            "color: #94a3b8; font-size: 12px; font-weight: 600; border: none; background: transparent;"
        )
        payment_section_layout.addWidget(lbl_paid)

        currency_symbol = self.i18n.get_message("currency_symbol")

        # حقل إدخال المبلغ كبير وبدون عجلة
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText(f"0.00 {currency_symbol}")
        self.paid_amount_input.setMinimumHeight(52)
        self.paid_amount_input.setText("0.00")
        self.paid_amount_input.setAlignment(Qt.AlignCenter)
        self.paid_amount_input.setStyleSheet("""
            QLineEdit {
                background: #0f172a;
                border: 2px solid #334155;
                border-radius: 8px;
                color: #06b6d4;
                font-size: 22px;
                font-weight: bold;
                padding: 8px 16px;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
                background: #0a1628;
            }
        """)
        # فقط أرقام ونقطة عشرية
        validator = QRegularExpressionValidator(QRegularExpression(r"^\d{0,10}(\.\d{0,2})?$"))
        self.paid_amount_input.setValidator(validator)
        self.paid_amount_input.textChanged.connect(self._on_paid_input_changed)
        payment_section_layout.addWidget(self.paid_amount_input)

        # أزرار سريعة للمبلغ (دفع كامل / صفر)
        quick_pay_row = QHBoxLayout()
        quick_pay_row.setSpacing(6)

        self.btn_pay_full = QPushButton("✅ دفع كامل")
        self.btn_pay_full.setMinimumHeight(36)
        self.btn_pay_full.setCursor(Qt.PointingHandCursor)
        self.btn_pay_full.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 6px;
            }
            QPushButton:hover { background: #059669; }
        """)
        self.btn_pay_full.clicked.connect(self._on_pay_full)

        self.btn_pay_zero = QPushButton("✖️ صفر")
        self.btn_pay_zero.setMinimumHeight(36)
        self.btn_pay_zero.setCursor(Qt.PointingHandCursor)
        self.btn_pay_zero.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                padding: 6px;
            }
            QPushButton:hover { background: #dc2626; }
        """)
        self.btn_pay_zero.clicked.connect(self._on_pay_zero)

        quick_pay_row.addWidget(self.btn_pay_full)
        quick_pay_row.addWidget(self.btn_pay_zero)
        payment_section_layout.addLayout(quick_pay_row)

        # المبلغ المتبقي (للقراءة فقط - يُحسب تلقائياً)
        remaining_row = QHBoxLayout()
        remaining_row.setSpacing(8)
        lbl_rem_title = QLabel("🔴 متبقي:")
        lbl_rem_title.setStyleSheet("color: #94a3b8; font-size: 13px; border: none; background: transparent;")
        self.lbl_remaining_amount = QLabel(f"0.00 {currency_symbol}")
        self.lbl_remaining_amount.setStyleSheet(
            "color: #ef4444; font-weight: bold; font-size: 18px; border: none; background: transparent;"
        )
        self.lbl_remaining_amount.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        remaining_row.addWidget(lbl_rem_title)
        remaining_row.addStretch()
        remaining_row.addWidget(self.lbl_remaining_amount)
        payment_section_layout.addLayout(remaining_row)

        scroll_layout.addWidget(payment_section)

        # متغير داخلي لتخزين طريقة الدفع (للتوافق مع الكود القديم)
        # combo_payment (مخفي - نستخدم _selected_payment بدلاً)
        self.combo_payment = QComboBox()
        self.combo_payment.addItems(
            [
                self.i18n.get_message("payment_cash"),
                self.i18n.get_message("payment_card"),
                self.i18n.get_message("payment_transfer"),
                self.i18n.get_message("payment_credit"),
            ]
        )
        self.combo_payment.setVisible(False)  # مخفي - للتوافق فقط

        # متغير داخلي قديم لحساب paid_amount (legacy compatibility)
        self.paid_amount_spin = QDoubleSpinBox()
        self.paid_amount_spin.setVisible(False)  # مخفي - نستخدم paid_amount_input
        self.paid_amount_spin.setMinimum(0.0)
        self.paid_amount_spin.setMaximum(999999999.0)
        self.paid_amount_spin.setValue(0.0)

        # الملخص المالي
        totals_layout = QVBoxLayout()
        totals_layout.setSpacing(8)

        self.lbl_subtotal = self.create_total_row(totals_layout, self.i18n.get_message("subtotal_label") + ":", "0.00")
        self.lbl_discount_total = self.create_total_row(
            totals_layout,
            self.i18n.get_message("total_discount") + ":",
            "0.00",
            color="#ef4444",
        )

        # حقل الضريبة القابل للتعديل
        tax_row = QHBoxLayout()
        tax_label = QLabel(self.i18n.get_message("tax_percent"))
        tax_label.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        self.tax_rate_spin = QDoubleSpinBox()
        self.tax_rate_spin.setMinimum(0.0)
        self.tax_rate_spin.setMaximum(100.0)
        self.tax_rate_spin.setValue(0.0)
        self.tax_rate_spin.setSuffix(" %")
        self.tax_rate_spin.setDecimals(2)
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
        self.lbl_grand_total = QLabel(f"0.00 {currency_symbol}")
        self.lbl_grand_total.setObjectName("GrandTotal")
        self.lbl_grand_total.setAlignment(Qt.AlignRight)
        totals_layout.addWidget(self.lbl_grand_total)

        # إضافة الملخص المالي إلى منطقة التمرير
        scroll_layout.addStretch(1)
        scroll_layout.addLayout(totals_layout)

        scroll_area.setWidget(scroll_content)
        footer_layout.addWidget(scroll_area, stretch=1)

        # 3.3 أزرار الإجراءات - ثابتة في الأسفل (Fixed at bottom)
        actions_frame = QFrame()
        actions_frame.setStyleSheet("background: transparent; border-top: 1px solid #334155; border-radius: 0;")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(20, 15, 20, 20)
        actions_layout.setSpacing(12)

        # زر إلغاء
        self.btn_cancel = QPushButton(self.i18n.get_message("cancel_button"))
        self.btn_cancel.setMinimumSize(120, 44)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
                min-height: 44px;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
                color: #0f172a;
            }
            QPushButton:pressed {
                background-color: #cbd5e1;
            }
        """)

        # زر إلغاء الفاتورة (يظهر فقط في وضع التعديل)
        self.btn_cancel_invoice = QPushButton("❌ إلغاء الفاتورة")
        self.btn_cancel_invoice.setObjectName("BtnDanger")
        self.btn_cancel_invoice.setMinimumSize(140, 44)
        self.btn_cancel_invoice.setCursor(Qt.PointingHandCursor)
        self.btn_cancel_invoice.setVisible(self.is_edit_mode)
        self.btn_cancel_invoice.setStyleSheet("""
            QPushButton#BtnDanger {
                background-color: #fef2f2;
                color: #ef4444;
                border: 1px solid #fecaca;
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: 700;
                font-size: 14px;
                min-height: 44px;
            }
            QPushButton#BtnDanger:hover { background-color: #fee2e2; }
        """)

        # زر حفظ
        self.btn_save = QPushButton("💾 حفظ الفاتورة")
        self.btn_save.setObjectName("BtnPrimary")
        self.btn_save.setMinimumSize(140, 44)
        self.btn_save.setCursor(Qt.PointingHandCursor)

        actions_layout.addWidget(self.btn_save)
        if self.is_edit_mode:
            actions_layout.addWidget(self.btn_cancel_invoice)
        actions_layout.addWidget(self.btn_cancel)

        footer_layout.addWidget(actions_frame, stretch=0)

        pos_split_layout.addWidget(footer_frame, stretch=3)

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
        """إنشاء بطاقة معلومات حية - Quantum Glassmorphism Style"""
        card = QFrame()
        card.setProperty("class", "glass-card")
        card.setStyleSheet("""
            QFrame {{
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                border-right: 5px solid {color};
            }}
        """)
        card.setMinimumWidth(180)
        l = QVBoxLayout(card)  # noqa: E741
        l.setContentsMargins(15, 12, 15, 12)
        l.setSpacing(5)
        t = QLabel(title)
        t.setStyleSheet("color: #94a3b8; font-size: 11px; font-weight: normal;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        l.addWidget(t)
        l.addWidget(v)
        return card

    def create_total_row(self, layout, text, value, color="#1e293b"):
        """إنشاء صف في الملخص المالي"""
        row = QHBoxLayout()
        l = QLabel(text)  # noqa: E741
        l.setStyleSheet("color: #cbd5e1; font-size: 14px;")
        v = QLabel(value)
        v.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 15px;")
        v.setAlignment(Qt.AlignRight)
        row.addWidget(l)
        row.addWidget(v)
        layout.addLayout(row)
        return v

    def setup_styles(self):
        """إعداد الأنماط - نظام التصميم الموحد (Quantum Theme)"""
        self.setStyleSheet("""
            QDialog {
                background-color: transparent;
            }
            QLabel {
                color: #e2e8f0;
            }
            QLabel#LabelDim {
                color: #94a3b8;
                font-size: 13px;
            }
            QLabel#InvoiceNo {
                color: #06b6d4;
                font-size: 18px;
                font-weight: bold;
            }
            QLabel#GrandTotal {
                color: #06b6d4;
                font-size: 36px;
                font-weight: bold;
            }
            QFrame#Zone1, QFrame#Zone2, QFrame#Zone3 {
                background: #1e293b;
                border: 1px solid #1e293b;
                border-radius: 12px;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 8px 12px;
                color: #f8fafc;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #06b6d4;
                background-color: #0f172a;
            }
            QPushButton#BtnPrimary {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #a855f7);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton#BtnPrimary:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #22d3ee, stop:1 #c084fc);
            }
        """)

    def setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح - تحسين WCAG 2.2 Keyboard Navigation"""
        # F10 - حفظ وطباعة
        save_shortcut = QShortcut(QKeySequence("F10"), self)
        save_shortcut.activated.connect(self.save_invoice)

        # Escape - إلغاء
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self.reject)

        # Ctrl+S - حفظ (بديل لـ F10)
        save_alt_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_alt_shortcut.activated.connect(self.save_invoice)

        # تحسين Tab Order للأزرار الرئيسية
        self.btn_cancel.setFocusPolicy(Qt.StrongFocus)
        self.btn_save.setFocusPolicy(Qt.StrongFocus)
        if self.is_edit_mode:
            self.btn_cancel_invoice.setFocusPolicy(Qt.StrongFocus)

        # إعداد Tab Order
        if self.is_edit_mode:
            self.setTabOrder(self.btn_cancel, self.btn_cancel_invoice)
            self.setTabOrder(self.btn_cancel_invoice, self.btn_save)
        else:
            self.setTabOrder(self.btn_cancel, self.btn_save)

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
                    self.combo_customer.addItem(
                        f"{customer.name} - {customer.phone or 'بدون هاتف'}",
                        customer.id,
                    )
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
                    "id": product.id,
                    "name": product.name,
                    "barcode": product.barcode,
                    "selling_price": float(product.selling_price),
                    "current_stock": product.current_stock,
                    "unit": product.unit,
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
        # print(f"DEBUG: Searching for '{query}'")  # للتحقق السريع

        if not query:
            # الإصلاح 1: إذا كان البحث فارغاً، لا نفعل شيئاً ولا نغلق النافذة
            return

        # تهيئة المتغير
        product = None

        # الإصلاح 3: استخراج الباركود من النص (مثل "منتج 1000 (1391881226731)")
        import re

        barcode_match = re.search(r"\((\d+)\)", query)
        if barcode_match:
            barcode = barcode_match.group(1)
            product = self.product_map.get(barcode)
            if product:
                pass  # Found by extracted barcode
            else:
                # البحث بالباركود المستخرج
                query = barcode

        # 1. البحث المباشر (مطابقة تامة) - الإصلاح 3: دعم الباركود
        if not product:
            product = self.product_map.get(query)

        # 2. البحث "الذكي" (بدون همزات أو بحث جزئي) - الإصلاح 3: دعم الباركود
        if not product:
            # تنظيف النص من التشكيل (اختياري) والبحث الجزئي
            matches = [
                p
                for name, p in self.product_map.items()
                if query.lower() in name.lower() or query == str(p.get("barcode", ""))
            ]

            if len(matches) >= 1:
                # إذا وجدنا أي تطابق، نأخذ الأول فوراً (لسرعة الكاشير)
                product = matches[0]
                if self.logger:
                    self.logger.debug(f"DEBUG: Found match: {product['name']}")
                # print(f"DEBUG: Found match: {product['name']}")
            else:
                if self.logger:
                    self.logger.debug("DEBUG: Product NOT found!")
                # print("DEBUG: Product NOT found!")
                # 🗣️ القاعدة 5: لا تترك المستخدم يخمن (Feedback Loop)
                QMessageBox.warning(
                    self,
                    self.i18n.get_message("warning"),
                    self.i18n.get_message("product_not_found", product=query),
                )
                self.search_input.selectAll()
                # الإصلاح 1: إعادة التركيز على البحث بعد الرسالة
                QTimer.singleShot(100, lambda: self.search_input.setFocus())
                return

        # إضافة المنتج للسلة
        try:
            self.add_product_to_cart(product)
            if self.logger:
                self.logger.debug(f"✅ تم إضافة المنتج: {product['name']}")
            # print(f"✅ تم إضافة المنتج: {product['name']} - عدد المنتجات في السلة: {len(self.cart_items)}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في إضافة المنتج: {e}")
            QMessageBox.critical(
                self,
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('add_product_failed')}: {e}",
            )
            # الإصلاح 1: إعادة التركيز على البحث بعد الخطأ
            QTimer.singleShot(100, lambda: self.search_input.setFocus())
            return

        # تنظيف وإعادة التركيز (⚡ القاعدة 3: سرعة الكاشير)
        self.search_input.clear()
        # الإصلاح 1+2: إعادة التركيز على البحث بعد الإضافة (لإضافة منتجات متعددة)
        QTimer.singleShot(50, lambda: self.search_input.setFocus())

    def add_product_to_cart(self, product_data):
        """إضافة منتج للسلة (تحديث الذاكرة + الجدول) - مع التحقق من المخزون"""
        product_id = product_data["id"]
        available_stock = int(product_data["current_stock"])

        # الإصلاح 2: التحقق من المخزون قبل الإضافة
        if available_stock <= 0:
            QMessageBox.warning(
                self,
                self.i18n.get_message("warning"),
                self.i18n.get_message(
                    "product_out_of_stock",
                    product=product_data["name"],
                    stock=available_stock,
                ),
            )
            self.search_input.selectAll()
            QTimer.singleShot(100, lambda: self.search_input.setFocus())
            return

        # 1. هل المنتج موجود مسبقاً؟ (زيادة الكمية)
        for row, item in enumerate(self.cart_items):
            if item["id"] == product_id:
                new_qty = item["qty"] + Decimal("1")
                # الإصلاح 2: التحقق من المخزون قبل زيادة الكمية
                if new_qty > available_stock:
                    QMessageBox.warning(
                        self,
                        "تنبيه",
                        f"لا يمكن إضافة المزيد من '{item['name']}'!\n\n"
                        f"الكمية الحالية في السلة: {item['qty']}\n"
                        f"المخزون المتاح: {available_stock}\n"
                        f"الحد الأقصى المسموح: {available_stock}",
                    )
                    return

                item["qty"] = new_qty
                # تحديث الكمية في الجدول
                self.table.blockSignals(True)
                qty_item = self.table.item(row, 4)
                if qty_item:
                    qty_item.setText(str(item["qty"]))
                self.table.blockSignals(False)
                self.recalc_row(row)  # إعادة حساب السطر
                # تمرير الجدول للسطر المحدث
                self.table.scrollToItem(self.table.item(row, 1))
                self.table.selectRow(row)
                # print(f"✅ تم تحديث الكمية للمنتج: {item['name']} - الكمية الجديدة: {item['qty']}")
                return

        # 2. إضافة منتج جديد
        # 🚫 القاعدة 1: استخدام Decimal للأموال والكميات لتفادي أخطاء التقريب
        item = {
            "id": product_id,
            "name": product_data["name"],
            "stock": available_stock,
            "unit": product_data.get("unit", "قطعة"),
            "price": to_decimal(product_data["selling_price"]),
            "qty": to_decimal(1),
            "discount": to_decimal(0),  # الإصلاح 3: الخصم صفر افتراضياً
            "total": to_decimal(0),  # سيحسب فوراً
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
        # print(f"✅ تم إضافة منتج جديد: {item['name']} - إجمالي المنتجات في السلة: {len(self.cart_items)}")

    def render_table_row(self, row_idx, item):
        """رسم بيانات السطر في الجدول (عرض فقط)"""
        # تعبئة الخلايا (Columns: ID, Product, Stock, Unit, Qty, Price, Discount, Total, Actions)

        # 0. ID (مخفي)
        self.table.setItem(row_idx, 0, QTableWidgetItem(str(item["id"])))

        # 1. المنتج
        self.table.setItem(row_idx, 1, QTableWidgetItem(item["name"]))

        # 2. المخزون (تلوين تحذيري)
        stock_item = QTableWidgetItem(str(item["stock"]))
        stock_item.setTextAlignment(Qt.AlignCenter)
        if item["stock"] <= 0:
            stock_item.setForeground(QColor("red"))
            stock_item.setBackground(QColor("#fee2e2"))
        self.table.setItem(row_idx, 2, stock_item)

        # 3. الوحدة
        self.table.setItem(row_idx, 3, QTableWidgetItem(item["unit"]))

        # 4. الكمية (قابلة للتعديل) - الإصلاح 1: تحسين قابلية التعديل
        qty_item = QTableWidgetItem(str(item["qty"]))
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
        discount_item = QTableWidgetItem(str(item["discount"]))
        discount_item.setTextAlignment(Qt.AlignCenter)
        discount_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable)  # قابل للتعديل
        self.table.setItem(row_idx, 6, discount_item)

        # 7. الإجمالي (للقراءة فقط)
        total_item = QTableWidgetItem(f"{item['total']:.2f}")
        total_item.setFlags(Qt.ItemIsEnabled)
        total_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table.setItem(row_idx, 7, total_item)

        # 8. زر الحذف (أيقونة) - تحسين Fitts Law وWCAG 2.2
        btn_del = QPushButton("❌")
        btn_del.setFlat(True)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setMinimumSize(44, 44)  # Fitts Law: minimum 44x44px
        btn_del.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 20px;
                color: #ef4444;
                padding: 0px;
                min-width: 44px;
                min-height: 44px;
            }
            QPushButton:hover {
                background-color: #fee2e2;
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: #fecaca;
            }
            QPushButton:focus {
                outline: 2px solid #ef4444;
                outline-offset: 2px;
                border-radius: 6px;
            }
        """)
        # الإصلاح 2: استخدام functools.partial لتجنب مشكلة closure في lambda
        from functools import partial

        btn_del.clicked.connect(partial(self.remove_item, row_idx))
        self.table.setCellWidget(row_idx, 8, btn_del)

        # الإصلاح 4: محاذاة الزر في المنتصف مع ارتفاع مناسب لـ Fitts Law
        self.table.setRowHeight(row_idx, 60)  # ارتفاع أكبر للصف لدعم Fitts Law

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
                available_stock = self.cart_items[row]["stock"]
                if new_qty > available_stock:
                    QMessageBox.warning(
                        self,
                        self.i18n.get_message("warning"),
                        self.i18n.get_message(
                            "quantity_exceeds_stock",
                            qty=int(new_qty),
                            stock=available_stock,
                        )
                        + "\n\n"
                        f"الكمية المطلوبة: {new_qty}\n"
                        f"المخزون المتاح: {available_stock}",
                    )
                    # إعادة القيمة القديمة
                    self.table.blockSignals(True)
                    self.table.item(row, 4).setText(str(self.cart_items[row]["qty"]))
                    self.table.blockSignals(False)
                    return

                self.cart_items[row]["qty"] = new_qty
                self.recalc_row(row)

            # السعر (العمود 5) - الإصلاح 3: السعر للقراءة فقط (لا يمكن التعديل)
            elif col == 5:
                # لا يمكن تعديل السعر - إعادة القيمة القديمة
                self.table.blockSignals(True)
                self.table.item(row, 5).setText(f"{self.cart_items[row]['price']:.2f}")
                self.table.blockSignals(False)
                QMessageBox.information(self, "معلومة", "السعر يأتي من المخزون ولا يمكن تعديله من هنا.")

            # الخصم (العمود 6)
            elif col == 6:
                self.cart_items[row]["discount"] = to_decimal(val_text)
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
        item["total"] = calculate_line_total(item["price"], item["qty"], item["discount"])

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
            if QApplication.platformName() == "offscreen":
                reply = QMessageBox.Yes
            else:
                reply = QMessageBox.question(
                    self,
                    "تأكيد الحذف",
                    f"هل تريد حذف '{self.cart_items[row]['name']}' من الفاتورة؟",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

            if reply != QMessageBox.Yes:
                return False

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
            return True
        return False

    def on_tax_rate_changed(self, value):
        """معالجة تغيير نسبة الضريبة"""
        self.tax_rate = Decimal(str(value))
        self.calculate_invoice_totals()

    def _on_payment_btn_clicked(self, key: str):
        """معالجة اختيار طريقة الدفع من الأزرار الكبيرة"""
        # إلغاء تحديد جميع الأزرار أولاً
        for k, btn in self._payment_buttons.items():
            btn.setChecked(k == key)
        self._selected_payment = key
        # مزامنة مع combo_payment المخفي (للتوافق)
        key_to_text = {
            "cash": self.i18n.get_message("payment_cash"),
            "card": self.i18n.get_message("payment_card"),
            "transfer": self.i18n.get_message("payment_transfer"),
            "credit": self.i18n.get_message("payment_credit"),
        }
        idx = self.combo_payment.findText(key_to_text.get(key, ""))
        if idx >= 0:
            self.combo_payment.setCurrentIndex(idx)

    def _on_paid_input_changed(self, text: str):
        """معالجة تغيير نص مبلغ الدفع الجديد"""
        try:
            self.paid_amount = to_decimal(text) if text.strip() else to_decimal(0)
        except Exception:
            self.paid_amount = to_decimal(0)
        # تحديث paid_amount_spin للتوافق
        self.paid_amount_spin.setValue(float(self.paid_amount))
        self.calculate_invoice_totals()

    def _on_pay_full(self):
        """دفع كامل - ضبط المبلغ على الإجمالي النهائي"""
        grand_total_text = self.lbl_grand_total.text()
        # استخراج الرقم من النص
        import re

        nums = re.findall(r"[\d.]+", grand_total_text.replace(",", ""))
        if nums:
            self.paid_amount_input.setText(nums[0])
        else:
            self.paid_amount_input.setText("0.00")

    def _on_pay_zero(self):
        """دفع صفر - مسح مبلغ الدفع"""
        self.paid_amount_input.setText("0.00")

    def on_paid_amount_changed(self, value):
        """معالجة تغيير المبلغ المدفوع (للتوافق مع الكود القديم)"""
        self.paid_amount = to_decimal(str(value))
        # تحديث paid_amount_input فقط إذا تغيير
        try:
            current_val = to_decimal(self.paid_amount_input.text() or "0")
            if abs(current_val - self.paid_amount) > Decimal("0.001"):
                self.paid_amount_input.setText(f"{float(self.paid_amount):.2f}")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in sales_dialog.py")
        self.calculate_invoice_totals()

    def calculate_invoice_totals(self):
        """حساب إجمالي الفاتورة (Zone 3) - مع دعم الضريبة والمبلغ المدفوع"""
        # استخدام math_utils للحسابات الدقيقة
        subtotal = calculate_subtotal([item["total"] for item in self.cart_items])

        # الخصم العام
        discount_percentage = getattr(self, "discount_percentage", to_decimal(0))
        if discount_percentage > 0:
            global_discount = subtotal * (discount_percentage / Decimal("100.00"))
        else:
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
            self.lbl_remaining_amount.setStyleSheet(
                "color: #ef4444; font-weight: bold; font-size: 18px; border: none; background: transparent;"
            )
        else:
            self.lbl_remaining_amount.setStyleSheet(
                "color: #10b981; font-weight: bold; font-size: 18px; border: none; background: transparent;"
            )

        # تحديث حالة الفاتورة
        index = self.combo_status.findText(status)
        if index >= 0:
            self.combo_status.setCurrentIndex(index)

    # --- Stubs/Wrappers for Testing ---
    @property
    def items_table(self):
        """جدول العناصر"""
        return self.table

    @property
    def total_label(self):
        """ملصق المجموع النهائي"""
        return self.lbl_grand_total

    def add_item(self, item):
        """إضافة عنصر (ماتش مع اختبارات الوحدة)"""
        product_id = item.get("id", len(self.cart_items) + 1)
        name = item.get("product_name", "منتج")
        qty = item.get("quantity", 1)
        price = item.get("price", Decimal("0.00"))
        discount = item.get("discount", Decimal("0.00"))

        qty_dec = to_decimal(qty)
        price_dec = to_decimal(price)
        discount_dec = to_decimal(discount)

        cart_item = {
            "id": product_id,
            "name": name,
            "stock": 100,
            "unit": "قطعة",
            "price": price_dec,
            "qty": qty_dec,
            "discount": discount_dec,
            "total": (qty_dec * price_dec) - discount_dec,
        }

        self.cart_items.append(cart_item)
        row_idx = len(self.cart_items) - 1

        self.table.blockSignals(True)
        self.table.insertRow(row_idx)
        self.render_table_row(row_idx, cart_item)
        self.recalc_row(row_idx)
        self.table.blockSignals(False)

        self.calculate_invoice_totals()
        return True

    def calculate_total(self) -> Decimal:
        """حساب وإرجاع الإجمالي النهائي"""
        subtotal = calculate_subtotal([item["total"] for item in self.cart_items])
        discount_percentage = getattr(self, "discount_percentage", to_decimal(0))
        if discount_percentage > 0:
            global_discount = subtotal * (discount_percentage / Decimal("100.00"))
        else:
            global_discount = to_decimal(0)
        tax = calculate_tax_amount(subtotal - global_discount, global_discount, self.tax_rate)
        return calculate_grand_total(subtotal, global_discount, tax)

    def apply_discount(self, discount_percentage) -> bool:
        """تطبيق خصم عام بنسبة معينة"""
        self.discount_percentage = to_decimal(discount_percentage)
        self.calculate_invoice_totals()
        return True

    def on_complete_sale(self) -> bool:
        """إتمام البيع"""
        self.save_invoice()
        return True

    def clear_items(self) -> bool:
        """مسح جميع العناصر من السلة"""
        self.cart_items.clear()
        self.table.clearContents()
        self.table.setRowCount(0)
        self.calculate_invoice_totals()
        return True

    def get_sale_data(self) -> Dict[str, Any]:
        """الحصول على بيانات البيع الإجمالية"""
        subtotal = calculate_subtotal([item["total"] for item in self.cart_items])
        discount_percentage = getattr(self, "discount_percentage", to_decimal(0))
        if discount_percentage > 0:
            global_discount = subtotal * (discount_percentage / Decimal("100.00"))
        else:
            global_discount = to_decimal(0)
        tax = calculate_tax_amount(subtotal - global_discount, global_discount, self.tax_rate)
        grand_total = calculate_grand_total(subtotal, global_discount, tax)

        return {
            "items": self.cart_items,
            "total": grand_total,
            "subtotal": subtotal,
            "discount": global_discount,
            "tax": tax,
        }

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
                status=SaleStatus.DRAFT.value,
                payment_method=PaymentMethod.CASH.value,
                items=[],
                total_amount=Decimal("0.00"),
                discount_amount=Decimal("0.00"),
                final_amount=Decimal("0.00"),
                paid_amount=Decimal("0.00"),
                remaining_amount=Decimal("0.00"),
            )

            self.sale = new_sale
            self.lbl_invoice_no.setText(
                self.i18n.get_message("invoice_number", invoice_number=self.sale.invoice_number)
            )

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
                self.logger.info(
                    f"بدء ملء النموذج للفاتورة {self.sale.id}, عدد العناصر: {len(self.sale.items) if self.sale.items else 0}"  # noqa: E501
                )
            # معلومات الفاتورة
            self.lbl_invoice_no.setText(
                self.i18n.get_message("invoice_number", invoice_number=self.sale.invoice_number)
            )
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
                self.paid_amount_input.setText(f"{float(self.paid_amount):.2f}")

            # تحديث حالة الفاتورة
            if self.sale.status:
                status_text = self.sale.status.value if hasattr(self.sale.status, "value") else str(self.sale.status)
                index = self.combo_status.findText(status_text)
                if index >= 0:
                    self.combo_status.setCurrentIndex(index)

            # تحديث طريقة الدفع - تحديث الأزرار الجديدة
            if self.sale.payment_method:
                payment_text = (
                    self.sale.payment_method.value
                    if hasattr(self.sale.payment_method, "value")
                    else str(self.sale.payment_method)
                )
                index = self.combo_payment.findText(payment_text)
                if index >= 0:
                    self.combo_payment.setCurrentIndex(index)
                # تحديث أزرار الدفع
                _payment_map = {
                    "نقدي": "cash",
                    "نقد": "cash",
                    "بطاقة": "card",
                    "بطاقة بنكية": "card",
                    "تحويل": "transfer",
                    "تحويل بنكي": "transfer",
                    "آجل": "credit",
                    "ذمم": "credit",
                }
                pay_key = _payment_map.get(payment_text, "cash")
                self._on_payment_btn_clicked(pay_key)

            # تحديث الملاحظات
            if self.sale.notes:
                self.input_notes.setText(self.sale.notes)

            # تحميل عناصر الفاتورة
            self.load_sale_items()

            # إعادة حساب المجاميع بعد تحميل البيانات
            self.calculate_invoice_totals()

        except Exception as e:
            self.logger.error(f"خطأ في ملء النموذج: {str(e)}")
            QMessageBox.critical(
                self,
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('invoice_load_failed')}: {str(e)}",
            )

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
                        unit = product.unit if product and hasattr(product, "unit") else "قطعة"
                    except Exception:
                        stock = 0
                        unit = "قطعة"

                    item_dict = {
                        "id": item.product_id,
                        "name": item.product_name or "منتج غير محدد",
                        "stock": stock,
                        "unit": unit,
                        "price": to_decimal(item.unit_price),
                        "qty": to_decimal(item.quantity),
                        "discount": to_decimal(item.discount_amount),
                        "total": to_decimal(item.total_amount),
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
            QMessageBox.warning(
                self,
                self.i18n.get_message("warning"),
                f"{self.i18n.get_message('invoice_items_load_failed')}:\n{str(e)}",
            )

    # ============================================================
    # 💾 الحفظ الذري (Atomic Save) - قلب النظام
    # ============================================================

    @prevent_double_click(wait_ms=2000)
    def save_invoice(self):
        """حفظ الفاتورة باستخدام SaleManager بشكل غير متزامن لتجنب تجميد الواجهة"""
        if not self.cart_items:
            QMessageBox.warning(
                self,
                self.i18n.get_message("warning"),
                self.i18n.get_message("empty_invoice"),
            )
            return

        if QApplication.platformName() != "offscreen":
            if QMessageBox.question(self, "تأكيد", "هل تريد حفظ الفاتورة؟") != QMessageBox.Yes:
                return

        try:
            # تحويل cart_items إلى SaleItem objects
            sale_items: List[SaleItem] = []
            for item in self.cart_items:
                sale_item = SaleItem(
                    id=None,
                    sale_id=None,
                    product_id=item["id"],
                    product_name=item["name"],
                    quantity=int(item["qty"]),
                    unit_price=item["price"],
                    discount=item["discount"],
                    total_price=item["total"],
                )
                sale_item.calculate_totals()
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

            # تحديد طريقة الدفع
            payment_mapping = {
                "cash": PaymentMethod.CASH,
                "card": PaymentMethod.CARD,
                "transfer": PaymentMethod.BANK_TRANSFER,
                "credit": PaymentMethod.CREDIT,
            }
            selected_key = getattr(self, "_selected_payment", "cash")
            payment_method = payment_mapping.get(selected_key, PaymentMethod.CASH)

            subtotal = calculate_subtotal([item["total"] for item in self.cart_items])
            discount_amount = to_decimal(0)
            tax_rate = self.tax_rate
            tax_amount = calculate_tax_amount(subtotal, discount_amount, tax_rate)
            total_amount = calculate_grand_total(subtotal, discount_amount, tax_amount)

            if not self.sale:
                self.create_new_sale()

            from datetime import date

            self.sale.customer_id = customer_id
            self.sale.customer_name = customer_name
            self.sale.customer_phone = customer_phone
            self.sale.sale_date = date.today()
            self.sale.due_date = None

            status_text = self.combo_status.currentText()
            status_mapping = {
                "مسودة": SaleStatus.DRAFT.value,
                "مؤكدة": SaleStatus.CONFIRMED.value,
                "مدفوعة": SaleStatus.PAID.value,
                "مدفوعة جزئياً": SaleStatus.PARTIALLY_PAID.value,
                "ملغية": SaleStatus.CANCELLED.value,
            }
            self.sale.status = status_mapping.get(status_text, SaleStatus.CONFIRMED.value)

            pm_val = payment_method.value if isinstance(payment_method, PaymentMethod) else payment_method
            self.sale.payment_method = pm_val
            self.sale.total_amount = subtotal
            self.sale.discount_amount = discount_amount
            self.sale.final_amount = total_amount
            self.sale.paid_amount = self.paid_amount
            self.sale.remaining_amount = total_amount - self.paid_amount

            # التحقق من الحالة
            if self.sale.status == SaleStatus.PAID.value and self.sale.remaining_amount > 0:
                QMessageBox.warning(
                    self,
                    "خطأ في الحالة",
                    "لا يمكن حفظ الفاتورة بحالة 'مدفوعة' إذا كان هناك مبلغ متبقي.\n\n"
                    f"المبلغ المتبقي: {format_currency(self.sale.remaining_amount)}\n\n"
                    "يرجى تغيير الحالة إلى 'مدفوعة جزئياً' أو 'مؤكدة'.",
                )
                if self.paid_amount > 0:
                    self.sale.status = SaleStatus.PARTIALLY_PAID.value
                    index = self.combo_status.findText("مدفوعة جزئياً")
                    if index >= 0:
                        self.combo_status.setCurrentIndex(index)
                else:
                    self.sale.status = SaleStatus.CONFIRMED.value
                    index = self.combo_status.findText("مؤكدة")
                    if index >= 0:
                        self.combo_status.setCurrentIndex(index)
                return

            self.sale.notes = self.input_notes.text().strip() or None
            self.sale.created_by = None
            self.sale.items = sale_items

            # --- البداية غير المتزامنة (Async Start) ---
            self.setEnabled(False)

            # إنشاء نافذة انتظار
            self.progress_dialog = QProgressDialog("جاري حفظ الفاتورة، يرجى الانتظار...", None, 0, 0, self)
            self.progress_dialog.setWindowTitle("معالجة البيانات")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.show()

            # إعداد مسار العمل الخلفي
            self.thread = QThread()
            is_new = self.sale.id is None

            self.worker = SaleOperationWorker(
                operation_type="create" if is_new else "update",
                manager=self.sales_service,
                sale=self.sale,
            )
            self.worker.moveToThread(self.thread)

            # ربط الإشارات
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._on_save_finished)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            # تمرير is_new كمتغير للحالة
            self._is_new_sale = is_new
            self.thread.start()

        except Exception as e:
            self.setEnabled(True)
            self.logger.error(f"خطأ في إعداد حفظ الفاتورة: {str(e)}", exc_info=True)
            QMessageBox.critical(
                self,
                self.i18n.get_message("fatal_error"),
                f"{self.i18n.get_message('operation_failed')}: {e}",
            )

    def _on_save_finished(self, success, error_msg, result_data):
        """دالة الاستدعاء عند انتهاء حفظ الفاتورة"""
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        self.setEnabled(True)

        if success:
            is_new = getattr(self, "_is_new_sale", False)
            if is_new and result_data:
                self.sale.id = result_data
                if self.logger:
                    self.logger.info(f"✅ تم إنشاء فاتورة جديدة: {self.sale.invoice_number} (ID: {result_data})")
            else:
                if self.logger:
                    self.logger.info(f"✅ تم تحديث الفاتورة: {self.sale.invoice_number} (ID: {self.sale.id})")

            try:
                if not is_new:
                    signals.sales_updated.emit()
                    signals.sale_updated.emit(self.sale.id)
                    signals.inventory_updated.emit()
                else:
                    signals.sales_updated.emit()
                    signals.sale_created.emit(self.sale.id)
                    signals.inventory_updated.emit()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"⚠️ فشل إطلاق الإشارات: {e}")

            self.sale_completed.emit(self.sale)

            currency_symbol = self.i18n.get_message("currency_symbol")
            QMessageBox.information(
                self,
                self.i18n.get_message("success"),
                self.i18n.get_message(
                    "invoice_saved_success",
                    invoice_number=self.sale.invoice_number,
                    total=self.sale.total_amount,
                    currency=currency_symbol,
                ),
            )
            self.accept()
        else:
            error_details = error_msg + f"\nرقم الفاتورة: {self.sale.invoice_number}"
            QMessageBox.critical(self, "خطأ", error_details)

    def cancel_invoice_handler(self):
        """معالج إلغاء الفاتورة بشكل غير متزامن لتجنب تجميد الواجهة"""
        if not self.sale or not self.sale.id:
            QMessageBox.warning(self, "تحذير", "لا توجد فاتورة محفوظة لإلغائها")
            return

        sale_status = self.sale.status
        status_value = sale_status.value if hasattr(sale_status, "value") else str(sale_status)
        if status_value == "ملغية" or status_value == "Cancelled" or sale_status == SaleStatus.CANCELLED:
            QMessageBox.information(self, "تنبيه", "هذه الفاتورة ملغاة بالفعل")
            return

        reply = QMessageBox.question(
            self,
            "تأكيد الإلغاء",
            f"هل أنت متأكد من رغبتك في إلغاء الفاتورة رقم {self.sale.invoice_number}؟\n\n⚠️ سيتم استعادة المخزون.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.No:
            return

        reason, ok = QInputDialog.getText(self, "سبب الإلغاء", "الرجاء إدخال سبب الإلغاء (اختياري):", text="")
        if not ok:
            return
        if not reason.strip():
            reason = "إلغاء من المستخدم"

        try:
            self.btn_cancel_invoice.setEnabled(False)
            self.setEnabled(False)

            self.progress_dialog = QProgressDialog("جاري إلغاء الفاتورة، يرجى الانتظار...", None, 0, 0, self)
            self.progress_dialog.setWindowTitle("معالجة البيانات")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setCancelButton(None)
            self.progress_dialog.show()

            current_user_id = (
                getattr(
                    self.parent(),
                    "current_user_id",
                    getattr(self.parent(), "user_id", 1),
                )
                if self.parent()
                else 1
            )

            self.cancel_thread = QThread()
            self.cancel_worker = SaleOperationWorker(
                operation_type="cancel",
                manager=self.sales_service,
                sale_id=self.sale.id,
                reason=reason.strip(),
                user_id=current_user_id,
            )
            self.cancel_worker.moveToThread(self.cancel_thread)

            self.cancel_thread.started.connect(self.cancel_worker.run)
            self.cancel_worker.finished.connect(
                lambda success, err, data: self._on_cancel_finished(success, err, reason)
            )
            self.cancel_worker.finished.connect(self.cancel_thread.quit)
            self.cancel_worker.finished.connect(self.cancel_worker.deleteLater)
            self.cancel_thread.finished.connect(self.cancel_thread.deleteLater)

            self.cancel_thread.start()

        except Exception as e:
            if hasattr(self, "progress_dialog") and self.progress_dialog:
                self.progress_dialog.close()
            self.btn_cancel_invoice.setEnabled(True)
            self.setEnabled(True)
            self.logger.error(f"UI Error starting cancel: {e}")
            QMessageBox.critical(self, "خطأ", f"حدث خطأ غير متوقع:\n{str(e)}")

    def _on_cancel_finished(self, success, error_msg, reason):
        if hasattr(self, "progress_dialog") and self.progress_dialog:
            self.progress_dialog.close()

        self.btn_cancel_invoice.setEnabled(True)
        self.setEnabled(True)

        if success:
            self.sale.status = SaleStatus.CANCELLED
            status_index = self.combo_status.findText(self.i18n.get_message("invoice_status_cancelled"))
            if status_index >= 0:
                self.combo_status.setCurrentIndex(status_index)

            existing_notes = self.sale.notes or ""
            self.sale.notes = f"{existing_notes}\n[إلغاء] {reason} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"

            try:
                signals.sales_updated.emit()
                signals.sale_updated.emit(self.sale.id)
                signals.inventory_updated.emit()
            except Exception as e:
                self.logger.warning(f"فشل إطلاق الإشارات: {e}")

            QMessageBox.information(
                self,
                "نجاح",
                f"✅ تم إلغاء الفاتورة رقم {self.sale.invoice_number} واستعادة المخزون بنجاح.",
            )
            self.accept()
        else:
            QMessageBox.critical(self, "خطأ", f"❌ حدث خطأ أثناء إلغاء الفاتورة.\n{error_msg}")

    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        # التحقق من وجود تغييرات غير محفوظة
        if self.cart_items and not self.is_edit_mode:
            reply = QMessageBox.question(
                self,
                self.i18n.get_message("close_without_save"),
                self.i18n.get_message("unsaved_invoice_warning"),
                QMessageBox.Yes | QMessageBox.No,
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
    from src.core.database_manager import DatabaseManager

    db = DatabaseManager(":memory:")
    db.initialize()

    dialog = SalesDialog(db)

    if dialog.exec() == QDialog.Accepted:
        pass  # Invoice saved
    else:
        pass  # Cancelled

    sys.exit()

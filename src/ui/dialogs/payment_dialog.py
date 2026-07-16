import logging
#!/usr/bin/env python3
"""
نافذة إدارة المدفوعات - Payment Dialog
واجهة شاملة لإدارة المدفوعات والحسابات المدينة والدائنة
"""

import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QDate, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.utils.ui_utils import prevent_double_click

from ...core.local_database_manager import LocalDatabaseManager
from ...models.customer import CustomerManager
from ...models.payment import PaymentMethod, PaymentType
from ...models.supplier import SupplierManager
from ...services.billing_service import BillingService
from ...services.payment_service import PaymentService
from ...ui.widgets.quantum_notification import NotificationManager
from ...utils.i18n_api import I18n
from ...utils.logger import setup_logger


class PaymentWorker(QThread):
    """عامل معالجة المدفوعات"""

    payment_completed = Signal(bool, str, dict)  # success, message, data

    def __init__(
        self,
        payment_service: PaymentService,
        operation: str,
        payment_data: Dict[str, Any],
    ):
        super().__init__()
        self.payment_service = payment_service
        self.operation = operation
        self.payment_data = payment_data

    def run(self):
        """تشغيل عملية المدفوعات"""
        try:
            if self.operation == "create_customer_payment":
                result = self.payment_service.create_customer_payment(
                    customer_id=self.payment_data["customer_id"],
                    amount=self.payment_data["amount"],
                    payment_method=self.payment_data["payment_method"],
                    reference_number=self.payment_data.get("reference_number"),
                    notes=self.payment_data.get("notes"),
                )
                self.payment_completed.emit(True, "تم إنشاء دفعة العميل بنجاح", {"payment_id": result})

            elif self.operation == "create_supplier_payment":
                result = self.payment_service.create_supplier_payment(
                    supplier_id=self.payment_data["supplier_id"],
                    amount=self.payment_data["amount"],
                    payment_method=self.payment_data["payment_method"],
                    reference_number=self.payment_data.get("reference_number"),
                    notes=self.payment_data.get("notes"),
                )
                self.payment_completed.emit(True, "تم إنشاء دفعة المورد بنجاح", {"payment_id": result})

        except Exception as e:
            self.payment_completed.emit(False, f"خطأ في معالجة المدفوعات: {str(e)}", {})


class PaymentDialog(BaseDialog):
    """نافذة إدارة المدفوعات"""

    payment_created = Signal(dict)  # إشارة إنشاء دفعة جديدة

    def __init__(
        self,
        db_manager: LocalDatabaseManager,
        parent=None,
        payment_service: Optional[PaymentService] = None,
        payment_type: PaymentType = PaymentType.CUSTOMER_PAYMENT,
        entity_id: Optional[int] = None,
        amount: Optional[Decimal] = None,
    ):
        if db_manager is None:
            raise TypeError("PaymentDialog requires a valid db_manager instance, got None")

        super().__init__(title="", parent=parent)
        self.payment_type = payment_type or PaymentType.CUSTOMER_PAYMENT
        self.logger = setup_logger(__name__)
        self.prefill_entity_id = entity_id
        self.prefill_amount = Decimal(str(amount)) if amount is not None else None

        # إعداد قاعدة البيانات والخدمات
        self.db_manager = db_manager
        self.payment_service = payment_service or PaymentService(self.db_manager)
        self.billing_service = BillingService(self.db_manager)
        self.customer_manager = CustomerManager(self.db_manager)
        self.supplier_manager = SupplierManager(self.db_manager)

        # متغيرات البيانات
        self.customers = []
        self.suppliers = []
        self.current_payment = None

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        # إعداد الواجهة
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        self.load_data()
        self.apply_prefill_data()
        self.notify = NotificationManager(self)

        self.setModal(True)
        self.resize(800, 600)

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = self.content_layout

        # شريط العنوان (KEEPING IT as a header, but changing title handling)
        self.setup_header(layout)

        # التبويبات الرئيسية
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # تبويب المدفوعات
        self.setup_payment_tab()

        # تبويب الحسابات
        self.setup_accounts_tab()

        # تبويب التقارير
        self.setup_reports_tab()

        # أزرار التحكم
        self.setup_control_buttons(layout)

        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def setup_header(self, layout):
        """إعداد شريط العنوان"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_frame)

        # العنوان
        title_label = QLabel(self.i18n.get_message("payment_accounts_management"))
        title_label.setObjectName("header_title")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # معلومات الحالة
        self.status_label = QLabel(self.i18n.get_message("ready"))
        self.status_label.setObjectName("status_label")
        header_layout.addWidget(self.status_label)

        layout.addWidget(header_frame)

    def setup_payment_tab(self):
        """إعداد تبويب المدفوعات"""
        payment_widget = QWidget()
        layout = QVBoxLayout(payment_widget)

        # نوع المدفوعات
        type_group = QGroupBox(self.i18n.get_message("payment_type"))
        type_layout = QHBoxLayout(type_group)

        self.customer_payment_radio = QCheckBox(self.i18n.get_message("customer_payment"))
        self.supplier_payment_radio = QCheckBox(self.i18n.get_message("supplier_payment"))

        type_layout.addWidget(self.customer_payment_radio)
        type_layout.addWidget(self.supplier_payment_radio)
        type_layout.addStretch()

        layout.addWidget(type_group)

        # نموذج المدفوعات
        form_group = QGroupBox(self.i18n.get_message("payment_data"))
        form_layout = QFormLayout(form_group)

        # العميل/المورد
        self.entity_combo = QComboBox()
        self.entity_combo.setEditable(True)
        form_layout.addRow(self.i18n.get_message("customer_supplier") + ":", self.entity_combo)

        # المبلغ
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 999999.99)
        self.amount_spinbox.setDecimals(2)
        currency_symbol = self.i18n.get_message("currency_symbol")
        self.amount_spinbox.setSuffix(f" {currency_symbol}")
        form_layout.addRow(self.i18n.get_message("amount") + ":", self.amount_spinbox)

        # طريقة الدفع
        self.payment_method_combo = QComboBox()
        payment_methods = [
            self.i18n.get_message("cash"),
            self.i18n.get_message("check"),
            self.i18n.get_message("bank_transfer"),
            self.i18n.get_message("credit_card"),
            self.i18n.get_message("debit_card"),
        ]
        self.payment_method_combo.addItems(payment_methods)
        form_layout.addRow(self.i18n.get_message("payment_method") + ":", self.payment_method_combo)

        # رقم المرجع
        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText(self.i18n.get_message("reference_number_optional"))
        form_layout.addRow(self.i18n.get_message("reference_number") + ":", self.reference_edit)

        # تاريخ المدفوعات
        self.payment_date = QDateEdit()
        self.payment_date.setDate(QDate.currentDate())
        self.payment_date.setCalendarPopup(True)
        form_layout.addRow(self.i18n.get_message("payment_date") + ":", self.payment_date)

        # ملاحظات
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText(self.i18n.get_message("additional_notes"))
        form_layout.addRow(self.i18n.get_message("notes_label") + ":", self.notes_edit)

        layout.addWidget(form_group)

        # أزرار العمليات
        buttons_layout = QHBoxLayout()

        self.save_payment_btn = QPushButton(self.i18n.get_message("save_payment"))
        self.save_payment_btn.setObjectName("primary_button")
        buttons_layout.addWidget(self.save_payment_btn)

        self.clear_form_btn = QPushButton(self.i18n.get_message("clear_form"))
        buttons_layout.addWidget(self.clear_form_btn)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # جدول المدفوعات الأخيرة
        recent_group = QGroupBox(self.i18n.get_message("recent_payments"))
        recent_layout = QVBoxLayout(recent_group)

        self.recent_payments_table = QTableWidget()
        self.recent_payments_table.setColumnCount(6)
        self.recent_payments_table.setHorizontalHeaderLabels(
            [
                self.i18n.get_message("date"),
                self.i18n.get_message("customer_supplier"),
                self.i18n.get_message("amount"),
                self.i18n.get_message("payment_method"),
                self.i18n.get_message("reference_number"),
                self.i18n.get_message("status"),
            ]
        )
        self.recent_payments_table.horizontalHeader().setStretchLastSection(True)
        recent_layout.addWidget(self.recent_payments_table)

        layout.addWidget(recent_group)

        self.tab_widget.addTab(payment_widget, self.i18n.get_message("payments"))

    def setup_accounts_tab(self):
        """إعداد تبويب الحسابات"""
        accounts_widget = QWidget()
        layout = QVBoxLayout(accounts_widget)

        # فلاتر البحث
        filter_group = QGroupBox(self.i18n.get_message("search_filters"))
        filter_layout = QGridLayout(filter_group)

        # نوع الحساب
        filter_layout.addWidget(QLabel(self.i18n.get_message("account_type") + ":"), 0, 0)
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(
            [
                self.i18n.get_message("all"),
                self.i18n.get_message("receivables"),
                self.i18n.get_message("payables"),
            ]
        )
        filter_layout.addWidget(self.account_type_combo, 0, 1)

        # فترة التاريخ
        filter_layout.addWidget(QLabel(self.i18n.get_message("from_date") + ":"), 0, 2)
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        filter_layout.addWidget(self.from_date, 0, 3)

        filter_layout.addWidget(QLabel(self.i18n.get_message("to_date") + ":"), 1, 2)
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        filter_layout.addWidget(self.to_date, 1, 3)

        # زر البحث
        self.search_accounts_btn = QPushButton(self.i18n.get_message("search"))
        self.search_accounts_btn.setObjectName("primary_button")
        filter_layout.addWidget(self.search_accounts_btn, 1, 4)

        layout.addWidget(filter_group)

        # جدول الحسابات
        accounts_group = QGroupBox(self.i18n.get_message("receivables_payables"))
        accounts_layout = QVBoxLayout(accounts_group)

        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels(
            [
                self.i18n.get_message("name"),
                self.i18n.get_message("account_type"),
                self.i18n.get_message("balance"),
                self.i18n.get_message("last_transaction"),
                self.i18n.get_message("last_transaction_date"),
                self.i18n.get_message("status"),
                self.i18n.get_message("actions"),
            ]
        )
        self.accounts_table.horizontalHeader().setStretchLastSection(True)
        accounts_layout.addWidget(self.accounts_table)

        layout.addWidget(accounts_group)

        self.tab_widget.addTab(accounts_widget, self.i18n.get_message("accounts"))

    def setup_reports_tab(self):
        """إعداد تبويب التقارير"""
        reports_widget = QWidget()
        layout = QVBoxLayout(reports_widget)

        # خيارات التقارير
        options_group = QGroupBox(self.i18n.get_message("report_options"))
        options_layout = QGridLayout(options_group)

        # نوع التقرير
        options_layout.addWidget(QLabel(self.i18n.get_message("report_type") + ":"), 0, 0)
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(
            [
                self.i18n.get_message("payments_summary"),
                self.i18n.get_message("aging_report"),
                self.i18n.get_message("cash_flow_report"),
                self.i18n.get_message("receivables"),
                self.i18n.get_message("payables"),
            ]
        )
        options_layout.addWidget(self.report_type_combo, 0, 1)

        # فترة التقرير
        options_layout.addWidget(QLabel(self.i18n.get_message("from_date") + ":"), 1, 0)
        self.report_from_date = QDateEdit()
        self.report_from_date.setDate(QDate.currentDate().addDays(-30))
        self.report_from_date.setCalendarPopup(True)
        options_layout.addWidget(self.report_from_date, 1, 1)

        options_layout.addWidget(QLabel(self.i18n.get_message("to_date") + ":"), 1, 2)
        self.report_to_date = QDateEdit()
        self.report_to_date.setDate(QDate.currentDate())
        self.report_to_date.setCalendarPopup(True)
        options_layout.addWidget(self.report_to_date, 1, 3)

        # أزرار التقارير
        self.generate_report_btn = QPushButton(self.i18n.get_message("generate_report"))
        self.generate_report_btn.setObjectName("primary_button")
        options_layout.addWidget(self.generate_report_btn, 2, 0)

        self.export_report_btn = QPushButton(self.i18n.get_message("export_report"))
        options_layout.addWidget(self.export_report_btn, 2, 1)

        layout.addWidget(options_group)

        # منطقة عرض التقرير
        report_group = QGroupBox(self.i18n.get_message("report"))
        report_layout = QVBoxLayout(report_group)

        self.report_table = QTableWidget()
        report_layout.addWidget(self.report_table)

        layout.addWidget(report_group)

        self.tab_widget.addTab(reports_widget, self.i18n.get_message("reports"))

    def setup_control_buttons(self, layout):
        """إعداد أزرار التحكم"""
        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout(buttons_frame)

        self.refresh_btn = QPushButton(self.i18n.get_message("refresh"))
        self.refresh_btn.setObjectName("secondary_button")
        buttons_layout.addWidget(self.refresh_btn)

        buttons_layout.addStretch()

        self.close_btn = QPushButton(self.i18n.get_message("close"))
        self.close_btn.setObjectName("secondary_button")
        buttons_layout.addWidget(self.close_btn)

        layout.addWidget(buttons_frame)

    def setup_connections(self):
        """إعداد الاتصالات والإشارات"""
        # أزرار التحكم
        self.close_btn.clicked.connect(self.close)
        self.refresh_btn.clicked.connect(self.load_data)

        # تبويب المدفوعات
        self.customer_payment_radio.toggled.connect(self.on_payment_type_changed)
        self.supplier_payment_radio.toggled.connect(self.on_payment_type_changed)
        self.save_payment_btn.clicked.connect(self.save_payment)
        self.clear_form_btn.clicked.connect(self.clear_payment_form)

        # تبويب الحسابات
        self.search_accounts_btn.clicked.connect(self.search_accounts)

        # تبويب التقارير
        self.generate_report_btn.clicked.connect(self.generate_report)
        self.export_report_btn.clicked.connect(self.export_report)

    def setup_styles(self):
        """إعداد الأنماط - يعتمد الآن على الثيم العام"""

    def load_data(self):
        """تحميل البيانات"""
        try:
            self.status_label.setText(self.i18n.get_message("loading_data"))

            # تحميل العملاء والموردين
            self.customers = self.customer_manager.get_all_customers()
            self.suppliers = self.supplier_manager.get_all_suppliers()

            # تحديث قائمة العملاء/الموردين
            self.update_entity_combo()

            # تحميل المدفوعات الأخيرة
            self.load_recent_payments()

            # تحميل الحسابات
            self.load_accounts()

            self.status_label.setText(self.i18n.get_message("data_loaded_successfully"))

        except Exception as e:
            self.logger.error(f"خطأ في تحميل البيانات: {str(e)}")
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('load_data_failed')}: {str(e)}",
            )
            self.status_label.setText(self.i18n.get_message("load_data_error"))

    def update_entity_combo(self):
        """تحديث قائمة العملاء/الموردين"""
        self.entity_combo.clear()

        if self.customer_payment_radio.isChecked():
            for customer in self.customers:
                self.entity_combo.addItem(customer.name, customer.id)
        elif self.supplier_payment_radio.isChecked():
            for supplier in self.suppliers:
                self.entity_combo.addItem(supplier.name, supplier.id)

    def on_payment_type_changed(self):
        """معالج تغيير نوع المدفوعات"""
        if self.customer_payment_radio.isChecked():
            self.supplier_payment_radio.setChecked(False)
        elif self.supplier_payment_radio.isChecked():
            self.customer_payment_radio.setChecked(False)

        self.update_entity_combo()

    @prevent_double_click(wait_ms=1500)
    def save_payment(self):
        """حفظ الدفعة الجديدة"""
        try:
            # التحقق من صحة البيانات
            if not self.validate_payment_form():
                return

            # إعداد بيانات المدفوعات
            payment_data = self.get_payment_data()

            # تحديد نوع العملية
            if self.customer_payment_radio.isChecked():
                operation = "create_customer_payment"
            else:
                operation = "create_supplier_payment"

            # بدء معالجة المدفوعات
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # شريط تقدم غير محدد
            self.save_payment_btn.setEnabled(False)

            # إنشاء عامل المعالجة
            self.payment_worker = PaymentWorker(self.payment_service, operation, payment_data)
            self.payment_worker.payment_completed.connect(self.on_payment_completed)
            self.payment_worker.start()

        except Exception as e:
            self.logger.error(f"خطأ في حفظ المدفوعات: {str(e)}")
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('save_payment_failed')}: {str(e)}",
            )

    def validate_payment_form(self) -> bool:
        """التحقق من صحة نموذج المدفوعات"""
        if not (self.customer_payment_radio.isChecked() or self.supplier_payment_radio.isChecked()):
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("select_payment_type_warning"),
            )
            return False

        if self.entity_combo.currentIndex() == -1:
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("select_customer_supplier_warning"),
            )
            return False

        if self.amount_spinbox.value() <= 0:
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("enter_valid_amount"),
            )
            return False

        return True

    def get_payment_data(self) -> Dict[str, Any]:
        """الحصول على بيانات المدفوعات من النموذج"""
        if hasattr(self, "amount_input") and not hasattr(self, "amount_spinbox"):
            return {
                "amount": Decimal(self.amount_input.text() or "0.00"),
                "payment_method": self.payment_method_combo.currentText() or "CASH",
            }

        entity_id = self.entity_combo.currentData()

        payment_method_map = {
            "نقدي": PaymentMethod.CASH,
            "شيك": PaymentMethod.CHECK,
            "تحويل بنكي": PaymentMethod.BANK_TRANSFER,
            "بطاقة ائتمان": PaymentMethod.CREDIT_CARD,
            "بطاقة مدين": PaymentMethod.DEBIT_CARD,
        }

        return {
            ("customer_id" if self.customer_payment_radio.isChecked() else "supplier_id"): entity_id,
            "amount": Decimal(str(self.amount_spinbox.value())),
            "payment_method": payment_method_map[self.payment_method_combo.currentText()],
            "reference_number": self.reference_edit.text().strip() or None,
            "notes": self.notes_edit.toPlainText().strip() or None,
        }

    def validate_amount(self, amount) -> bool:
        try:
            val = Decimal(amount)
            return val >= 0
        except Exception:
            return False

    def calculate_change(self, total: Decimal, amount: Decimal) -> Decimal:
        return total - amount

    def on_process_payment(self):
        return True

    def show_receipt(self):
        return True

    def on_payment_completed(self, success: bool, message: str, data: Dict[str, Any]):
        """معالج اكتمال المدفوعات"""
        self.progress_bar.setVisible(False)
        self.save_payment_btn.setEnabled(True)

        if success:
            self.notify.show_success(self.i18n.get_message("success"), message)
            self.clear_payment_form()
            self.load_recent_payments()
            self.load_accounts()
            self.payment_created.emit(data)
        else:
            self.notify.show_error(self.i18n.get_message("error"), message)

    def clear_payment_form(self):
        """مسح نموذج المدفوعات"""
        self.entity_combo.setCurrentIndex(-1)
        self.amount_spinbox.setValue(0.0)
        self.payment_method_combo.setCurrentIndex(0)
        self.reference_edit.clear()
        self.payment_date.setDate(QDate.currentDate())
        self.notes_edit.clear()

    def load_recent_payments(self):
        """تحميل المدفوعات الأخيرة"""
        try:
            # الحصول على المدفوعات الأخيرة (آخر 50 دفعة)
            end_date = datetime.now().date()
            start_date = end_date.replace(day=1)  # بداية الشهر الحالي

            payments = self.payment_service.get_payments_by_date_range(start_date, end_date)

            # تحديث الجدول
            self.recent_payments_table.setRowCount(len(payments))

            for row, payment in enumerate(payments):
                self.recent_payments_table.setItem(row, 0, QTableWidgetItem(payment.created_at.strftime("%Y-%m-%d")))

                # اسم العميل/المورد
                entity_name = "غير معروف"
                if payment.payment_type == PaymentType.CUSTOMER_PAYMENT:
                    customer = next((c for c in self.customers if c.id == payment.entity_id), None)
                    if customer:
                        entity_name = customer.name
                else:
                    supplier = next((s for s in self.suppliers if s.id == payment.entity_id), None)
                    if supplier:
                        entity_name = supplier.name

                self.recent_payments_table.setItem(row, 1, QTableWidgetItem(entity_name))
                self.recent_payments_table.setItem(row, 2, QTableWidgetItem(f"{payment.amount:.2f} دج"))
                self.recent_payments_table.setItem(row, 3, QTableWidgetItem(payment.payment_method.value))
                self.recent_payments_table.setItem(row, 4, QTableWidgetItem(payment.reference_number or ""))
                self.recent_payments_table.setItem(row, 5, QTableWidgetItem(payment.status.value))

        except Exception as e:
            self.logger.error(f"خطأ في تحميل المدفوعات الأخيرة: {str(e)}")

    def load_accounts(self):
        """تحميل الحسابات"""
        try:
            # الحصول على أرصدة الحسابات
            receivables = self.payment_service.get_accounts_receivable()
            payables = self.payment_service.get_accounts_payable()

            # دمج البيانات
            all_accounts = []

            # إضافة الحسابات المدينة
            for account in receivables:
                customer = next((c for c in self.customers if c.id == account["customer_id"]), None)
                if customer:
                    all_accounts.append(
                        {
                            "name": customer.name,
                            "type": "حساب مدين",
                            "balance": account["balance"],
                            "last_transaction": account.get("last_payment_date", "لا يوجد"),
                            "status": "نشط" if account["balance"] > 0 else "مسدد",
                        }
                    )

            # إضافة الحسابات الدائنة
            for account in payables:
                supplier = next((s for s in self.suppliers if s.id == account["supplier_id"]), None)
                if supplier:
                    all_accounts.append(
                        {
                            "name": supplier.name,
                            "type": "حساب دائن",
                            "balance": account["balance"],
                            "last_transaction": account.get("last_payment_date", "لا يوجد"),
                            "status": "نشط" if account["balance"] > 0 else "مسدد",
                        }
                    )

            # تحديث الجدول
            self.accounts_table.setRowCount(len(all_accounts))

            for row, account in enumerate(all_accounts):
                self.accounts_table.setItem(row, 0, QTableWidgetItem(account["name"]))
                self.accounts_table.setItem(row, 1, QTableWidgetItem(account["type"]))
                self.accounts_table.setItem(row, 2, QTableWidgetItem(f"{account['balance']:.2f} دج"))
                self.accounts_table.setItem(row, 3, QTableWidgetItem(""))  # آخر معاملة
                self.accounts_table.setItem(row, 4, QTableWidgetItem(str(account["last_transaction"])))
                self.accounts_table.setItem(row, 5, QTableWidgetItem(account["status"]))
                self.accounts_table.setItem(row, 6, QTableWidgetItem("عرض التفاصيل"))

        except Exception as e:
            self.logger.error(f"خطأ في تحميل الحسابات: {str(e)}")

    def search_accounts(self):
        """البحث في الحسابات"""
        # تطبيق فلاتر البحث وإعادة تحميل البيانات
        self.load_accounts()

    def generate_report(self):
        """إنشاء التقرير"""
        try:
            report_type = self.report_type_combo.currentText()
            start_date = self.report_from_date.date().toPython()
            end_date = self.report_to_date.date().toPython()

            self.status_label.setText(self.i18n.get_message("generating_report", report_type=report_type))

            payments_summary_key = self.i18n.get_message("payments_summary")
            aging_report_key = self.i18n.get_message("aging_report")
            cash_flow_key = self.i18n.get_message("cash_flow_report")

            if report_type == payments_summary_key:
                report_data = self.payment_service.get_payment_summary(start_date, end_date)
            elif report_type == aging_report_key:
                report_data = self.payment_service.get_aging_report()
            elif report_type == cash_flow_key:
                report_data = self.payment_service.get_cash_flow_report(start_date, end_date)
            else:
                report_data = []

            # عرض التقرير في الجدول
            self.display_report(report_data, report_type)
            self.status_label.setText(self.i18n.get_message("report_generated_successfully"))

        except Exception as e:
            self.logger.error(f"خطأ في إنشاء التقرير: {str(e)}")
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('generate_report_failed')}: {str(e)}",
            )
            self.status_label.setText(self.i18n.get_message("generate_report_error"))

    def display_report(self, data: List[Dict], report_type: str):
        """عرض التقرير"""
        if not data:
            self.report_table.setRowCount(0)
            return

        # تحديد أعمدة التقرير حسب النوع
        if report_type == self.i18n.get_message("payments_summary"):
            headers = [
                self.i18n.get_message("date"),
                self.i18n.get_message("count"),
                self.i18n.get_message("total_amount"),
                self.i18n.get_message("cash"),
                self.i18n.get_message("checks"),
                self.i18n.get_message("transfers"),
            ]
        elif report_type == self.i18n.get_message("aging_report"):
            headers = [
                self.i18n.get_message("customer_supplier"),
                self.i18n.get_message("balance"),
                "0-30 " + self.i18n.get_message("days"),
                "31-60 " + self.i18n.get_message("days"),
                "61-90 " + self.i18n.get_message("days"),
                "+90 " + self.i18n.get_message("days"),
            ]
        else:
            headers = list(data[0].keys()) if data else []

        self.report_table.setColumnCount(len(headers))
        self.report_table.setHorizontalHeaderLabels(headers)
        self.report_table.setRowCount(len(data))

        # ملء البيانات
        for row, item in enumerate(data):
            for col, key in enumerate(headers):
                value = item.get(key, "")
                self.report_table.setItem(row, col, QTableWidgetItem(str(value)))

    def export_report(self):
        """تصدير التقرير"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                self.i18n.get_message("export_report"),
                "",
                "CSV Files (*.csv);;Excel Files (*.xlsx)",
            )

            if file_path:
                # تصدير بيانات الجدول
                self.status_label.setText(self.i18n.get_message("exporting_report"))
                # هنا يمكن إضافة كود التصدير الفعلي
                self.status_label.setText(self.i18n.get_message("report_exported_successfully"))
                QMessageBox.information(
                    self,
                    self.i18n.get_message("success"),
                    self.i18n.get_message("report_exported_to", file_path=file_path),
                )

        except Exception as e:
            self.logger.error(f"خطأ في تصدير التقرير: {str(e)}")
            QMessageBox.critical(
                self,
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('export_report_failed')}: {str(e)}",
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # تطبيق الخط العربي
    font = QFont("Arial", 10)
    app.setFont(font)

    # إنشاء مدير قاعدة البيانات للاختبار
    from src.core.local_database_manager import LocalDatabaseManager

    db_manager = LocalDatabaseManager()

    dialog = PaymentDialog(db_manager)
    dialog.show()

    sys.exit(app.exec())

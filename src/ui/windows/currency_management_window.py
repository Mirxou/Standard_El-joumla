import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة إدارة العملات - Currency Management Window
واجهة شاملة لإدارة العملات وأسعار الصرف
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

project_root = Path(__file__).parent.parent.parent.parent

from src.core.database_manager import DatabaseManager
from src.models.currency import Currency, CurrencyManager, ExchangeRate
from src.services.exchange_rate_service import ExchangeRateService
from src.utils.logger import setup_logger


class CurrencyDialog(QDialog):
    """حوار إضافة/تعديل عملة"""

    def __init__(
        self,
        currency: Optional[Currency] = None,
        currency_manager: CurrencyManager = None,
        parent=None,
    ):
        super().__init__(parent)
        self.currency = currency
        self.currency_manager = currency_manager
        self.setWindowTitle("إضافة عملة" if not currency else "تعديل عملة")
        self.setMinimumWidth(500)
        self.setup_ui()

        if currency:
            self.load_data()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # رمز العملة
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("مثل: USD, EUR, GBP")
        self.code_edit.setMaxLength(3)
        form.addRow("رمز العملة * (3 أحرف):", self.code_edit)

        # اسم العملة
        self.name_edit = QLineEdit()
        form.addRow("اسم العملة *:", self.name_edit)

        # رمز العملة (Symbol)
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("مثل: $, €, £")
        form.addRow("رمز العملة (Symbol):", self.symbol_edit)

        # عدد الأرقام العشرية
        self.decimal_places_spin = QSpinBox()
        self.decimal_places_spin.setMinimum(0)
        self.decimal_places_spin.setMaximum(6)
        self.decimal_places_spin.setValue(2)
        form.addRow("عدد الأرقام العشرية:", self.decimal_places_spin)

        # عملة أساسية
        self.is_base_checkbox = QCheckBox()
        form.addRow("عملة أساسية:", self.is_base_checkbox)

        # نشط
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        form.addRow("نشط:", self.is_active_checkbox)

        layout.addLayout(form)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_data(self):
        """تحميل بيانات العملة"""
        if self.currency:
            self.code_edit.setText(self.currency.code)
            self.name_edit.setText(self.currency.name)
            self.symbol_edit.setText(self.currency.symbol)
            self.decimal_places_spin.setValue(self.currency.decimal_places)
            self.is_base_checkbox.setChecked(self.currency.is_base)
            self.is_active_checkbox.setChecked(self.currency.is_active)

    def get_currency(self) -> Optional[Currency]:
        """الحصول على بيانات العملة"""
        code = self.code_edit.text().strip().upper()
        name = self.name_edit.text().strip()
        symbol = self.symbol_edit.text().strip()

        if not code or not name:
            QMessageBox.warning(self, "خطأ", "رمز العملة والاسم مطلوبان")
            return None

        if len(code) != 3:
            QMessageBox.warning(self, "خطأ", "رمز العملة يجب أن يكون 3 أحرف")
            return None

        return Currency(
            id=self.currency.id if self.currency else None,
            code=code,
            name=name,
            symbol=symbol or code,
            decimal_places=self.decimal_places_spin.value(),
            is_base=self.is_base_checkbox.isChecked(),
            is_active=self.is_active_checkbox.isChecked(),
        )


class ExchangeRateDialog(QDialog):
    """حوار إضافة/تعديل سعر صرف"""

    def __init__(
        self,
        exchange_rate: Optional[ExchangeRate] = None,
        currency_manager: CurrencyManager = None,
        exchange_rate_service: ExchangeRateService = None,
        parent=None,
    ):
        super().__init__(parent)
        self.exchange_rate = exchange_rate
        self.currency_manager = currency_manager
        self.exchange_rate_service = exchange_rate_service
        self.setWindowTitle("إضافة سعر صرف" if not exchange_rate else "تعديل سعر صرف")
        self.setMinimumWidth(500)
        self.setup_ui()

        if exchange_rate:
            self.load_data()

    def setup_ui(self):
        """إعداد الواجهة"""
        layout = QVBoxLayout(self)

        form = QFormLayout()

        # العملة المصدر
        self.from_currency_combo = QComboBox()
        form.addRow("من العملة *:", self.from_currency_combo)

        # العملة الهدف
        self.to_currency_combo = QComboBox()
        form.addRow("إلى العملة *:", self.to_currency_combo)

        # سعر الصرف
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.0001)
        self.rate_spin.setMaximum(999999.9999)
        self.rate_spin.setDecimals(4)
        self.rate_spin.setValue(1.0)
        form.addRow("سعر الصرف *:", self.rate_spin)

        # تاريخ السريان
        self.effective_date_edit = QDateEdit()
        self.effective_date_edit.setCalendarPopup(True)
        self.effective_date_edit.setDate(QDate.currentDate())
        form.addRow("تاريخ السريان *:", self.effective_date_edit)

        # تاريخ الانتهاء
        self.expiry_date_edit = QDateEdit()
        self.expiry_date_edit.setCalendarPopup(True)
        self.expiry_date_edit.setDate(QDate())
        self.expiry_date_edit.setSpecialValueText("بدون تاريخ انتهاء")
        form.addRow("تاريخ الانتهاء:", self.expiry_date_edit)

        # المصدر
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("مثل: manual, api, bank")
        form.addRow("المصدر:", self.source_edit)

        # نشط
        self.is_active_checkbox = QCheckBox()
        self.is_active_checkbox.setChecked(True)
        form.addRow("نشط:", self.is_active_checkbox)

        layout.addLayout(form)

        # أزرار
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # تحميل العملات
        self.load_currencies()

    def load_currencies(self):
        """تحميل قائمة العملات"""
        if self.currency_manager:
            currencies = self.currency_manager.get_all_currencies()
            for currency in currencies:
                display_text = f"{currency.code} - {currency.name}"
                self.from_currency_combo.addItem(display_text, currency.id)
                self.to_currency_combo.addItem(display_text, currency.id)

    def load_data(self):
        """تحميل بيانات سعر الصرف"""
        if self.exchange_rate:
            # تحديد العملة المصدر
            from_idx = self.from_currency_combo.findData(self.exchange_rate.from_currency_id)
            if from_idx >= 0:
                self.from_currency_combo.setCurrentIndex(from_idx)

            # تحديد العملة الهدف
            to_idx = self.to_currency_combo.findData(self.exchange_rate.to_currency_id)
            if to_idx >= 0:
                self.to_currency_combo.setCurrentIndex(to_idx)

            self.rate_spin.setValue(float(self.exchange_rate.rate))

            if self.exchange_rate.effective_date:
                effective_qdate = QDate(
                    self.exchange_rate.effective_date.year,
                    self.exchange_rate.effective_date.month,
                    self.exchange_rate.effective_date.day,
                )
                self.effective_date_edit.setDate(effective_qdate)

            if self.exchange_rate.expiry_date:
                expiry_qdate = QDate(
                    self.exchange_rate.expiry_date.year,
                    self.exchange_rate.expiry_date.month,
                    self.exchange_rate.expiry_date.day,
                )
                self.expiry_date_edit.setDate(expiry_qdate)

            self.source_edit.setText(self.exchange_rate.source or "")
            self.is_active_checkbox.setChecked(self.exchange_rate.is_active)

    def get_exchange_rate(self) -> Optional[ExchangeRate]:
        """الحصول على بيانات سعر الصرف"""
        from_currency_id = self.from_currency_combo.currentData()
        to_currency_id = self.to_currency_combo.currentData()
        rate = Decimal(str(self.rate_spin.value()))

        if not from_currency_id or not to_currency_id:
            QMessageBox.warning(self, "خطأ", "يجب اختيار العملة المصدر والهدف")
            return None

        if from_currency_id == to_currency_id:
            QMessageBox.warning(self, "خطأ", "العملة المصدر والهدف يجب أن تكونا مختلفتين")
            return None

        effective_qdate = self.effective_date_edit.date()
        effective_date = date(effective_qdate.year(), effective_qdate.month(), effective_qdate.day())

        expiry_date = None
        expiry_qdate = self.expiry_date_edit.date()
        if expiry_qdate.isValid():
            expiry_date = date(expiry_qdate.year(), expiry_qdate.month(), expiry_qdate.day())

        return ExchangeRate(
            id=self.exchange_rate.id if self.exchange_rate else None,
            from_currency_id=from_currency_id,
            to_currency_id=to_currency_id,
            rate=rate,
            effective_date=effective_date,
            expiry_date=expiry_date,
            source=self.source_edit.text().strip() or "manual",
            is_active=self.is_active_checkbox.isChecked(),
        )


class CurrencyManagementWindow(QMainWindow):
    """نافذة إدارة العملات وأسعار الصرف"""

    # Window Manager attributes (للتسجيل التلقائي)
    window_key = "currency_management"
    window_singleton = True
    window_title = "💰 إدارة العملات وأسعار الصرف"

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.logger = setup_logger(__name__)
        self.currency_manager = CurrencyManager(db_manager, self.logger)
        self.exchange_rate_service = ExchangeRateService(db_manager, self.logger)

        self.setWindowTitle("💰 إدارة العملات وأسعار الصرف")
        self.setMinimumSize(1200, 700)

        # تطبيق ستايل الهوية الموحدة
        self.setStyleSheet("QMainWindow { background-color: #020617; }")

        self.setup_ui()
        self.load_currencies()
        self.load_exchange_rates()

    def setup_ui(self):
        """إعداد الواجهة"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # شريط الأدوات
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        # أزرار العملات
        add_currency_action = QAction("➕ إضافة عملة", self)
        add_currency_action.triggered.connect(self.add_currency)
        toolbar.addAction(add_currency_action)

        edit_currency_action = QAction("✏️ تعديل عملة", self)
        edit_currency_action.triggered.connect(self.edit_currency)
        toolbar.addAction(edit_currency_action)

        delete_currency_action = QAction("🗑️ حذف عملة", self)
        delete_currency_action.triggered.connect(self.delete_currency)
        toolbar.addAction(delete_currency_action)

        toolbar.addSeparator()

        # أزرار أسعار الصرف
        add_rate_action = QAction("➕ إضافة سعر صرف", self)
        add_rate_action.triggered.connect(self.add_exchange_rate)
        toolbar.addAction(add_rate_action)

        edit_rate_action = QAction("✏️ تعديل سعر صرف", self)
        edit_rate_action.triggered.connect(self.edit_exchange_rate)
        toolbar.addAction(edit_rate_action)

        delete_rate_action = QAction("🗑️ حذف سعر صرف", self)
        delete_rate_action.triggered.connect(self.delete_exchange_rate)
        toolbar.addAction(delete_rate_action)

        toolbar.addSeparator()

        refresh_action = QAction("🔄 تحديث", self)
        refresh_action.triggered.connect(self.refresh_data)
        toolbar.addAction(refresh_action)

        # تبويبات
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # تبويب العملات
        currency_tab = QWidget()
        currency_layout = QVBoxLayout(currency_tab)

        # جدول العملات
        self.currencies_table = QTableWidget()
        self.currencies_table.setColumnCount(7)
        self.currencies_table.setHorizontalHeaderLabels(
            [
                "المعرف",
                "الرمز",
                "الاسم",
                "الرمز (Symbol)",
                "الأرقام العشرية",
                "أساسية",
                "نشط",
            ]
        )
        self.currencies_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.currencies_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.currencies_table.horizontalHeader().setStretchLastSection(True)
        currency_layout.addWidget(self.currencies_table)

        tabs.addTab(currency_tab, "العملات")

        # تبويب أسعار الصرف
        rates_tab = QWidget()
        rates_layout = QVBoxLayout(rates_tab)

        # جدول أسعار الصرف
        self.rates_table = QTableWidget()
        self.rates_table.setColumnCount(8)
        self.rates_table.setHorizontalHeaderLabels(
            [
                "المعرف",
                "من العملة",
                "إلى العملة",
                "سعر الصرف",
                "تاريخ السريان",
                "تاريخ الانتهاء",
                "المصدر",
                "نشط",
            ]
        )
        self.rates_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.rates_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.rates_table.horizontalHeader().setStretchLastSection(True)
        rates_layout.addWidget(self.rates_table)

        tabs.addTab(rates_tab, "أسعار الصرف")

        # شريط الحالة
        self.statusBar().showMessage("جاهز")

    def load_currencies(self):
        """تحميل قائمة العملات"""
        try:
            currencies = self.currency_manager.get_all_currencies()
            self.currencies_table.setRowCount(len(currencies))

            for row, currency in enumerate(currencies):
                self.currencies_table.setItem(row, 0, QTableWidgetItem(str(currency.id)))
                self.currencies_table.setItem(row, 1, QTableWidgetItem(currency.code))
                self.currencies_table.setItem(row, 2, QTableWidgetItem(currency.name))
                self.currencies_table.setItem(row, 3, QTableWidgetItem(currency.symbol))
                self.currencies_table.setItem(row, 4, QTableWidgetItem(str(currency.decimal_places)))

                # أساسية
                base_item = QTableWidgetItem("✓" if currency.is_base else "")
                base_item.setTextAlignment(Qt.AlignCenter)
                self.currencies_table.setItem(row, 5, base_item)

                # نشط
                active_item = QTableWidgetItem("✓" if currency.is_active else "")
                active_item.setTextAlignment(Qt.AlignCenter)
                self.currencies_table.setItem(row, 6, active_item)

            self.statusBar().showMessage(f"تم تحميل {len(currencies)} عملة")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل العملات: {str(e)}")
            self.logger.error(f"خطأ في تحميل العملات: {str(e)}")

    def load_exchange_rates(self):
        """تحميل قائمة أسعار الصرف"""
        try:
            rates = self.exchange_rate_service.get_exchange_rates()
            self.rates_table.setRowCount(len(rates))

            for row, rate in enumerate(rates):
                self.rates_table.setItem(row, 0, QTableWidgetItem(str(rate.id)))

                # من العملة
                from_currency = self.currency_manager.get_currency(rate.from_currency_id)
                from_text = from_currency.code if from_currency else str(rate.from_currency_id)
                self.rates_table.setItem(row, 1, QTableWidgetItem(from_text))

                # إلى العملة
                to_currency = self.currency_manager.get_currency(rate.to_currency_id)
                to_text = to_currency.code if to_currency else str(rate.to_currency_id)
                self.rates_table.setItem(row, 2, QTableWidgetItem(to_text))

                self.rates_table.setItem(row, 3, QTableWidgetItem(str(rate.rate)))
                self.rates_table.setItem(
                    row,
                    4,
                    QTableWidgetItem(rate.effective_date.isoformat() if rate.effective_date else ""),
                )
                self.rates_table.setItem(
                    row,
                    5,
                    QTableWidgetItem(rate.expiry_date.isoformat() if rate.expiry_date else ""),
                )
                self.rates_table.setItem(row, 6, QTableWidgetItem(rate.source or ""))

                # نشط
                active_item = QTableWidgetItem("✓" if rate.is_active else "")
                active_item.setTextAlignment(Qt.AlignCenter)
                self.rates_table.setItem(row, 7, active_item)

            self.statusBar().showMessage(f"تم تحميل {len(rates)} سعر صرف")

        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل أسعار الصرف: {str(e)}")
            self.logger.error(f"خطأ في تحميل أسعار الصرف: {str(e)}")

    def add_currency(self):
        """إضافة عملة جديدة"""
        dialog = CurrencyDialog(currency_manager=self.currency_manager, parent=self)
        if dialog.exec() == QDialog.Accepted:
            currency = dialog.get_currency()
            if currency:
                try:
                    currency_id = self.currency_manager.add_currency(currency)
                    if currency_id:
                        QMessageBox.information(self, "نجح", "تم إضافة العملة بنجاح")
                        self.load_currencies()
                    else:
                        QMessageBox.warning(self, "خطأ", "فشل إضافة العملة")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"خطأ في إضافة العملة: {str(e)}")
                    self.logger.error(f"خطأ في إضافة العملة: {str(e)}")

    def edit_currency(self):
        """تعديل عملة"""
        current_row = self.currencies_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عملة للتعديل")
            return

        currency_id = int(self.currencies_table.item(current_row, 0).text())
        currency = self.currency_manager.get_currency(currency_id)

        if currency:
            dialog = CurrencyDialog(currency=currency, currency_manager=self.currency_manager, parent=self)
            if dialog.exec() == QDialog.Accepted:
                updated_currency = dialog.get_currency()
                if updated_currency:
                    try:
                        if self.currency_manager.update_currency(updated_currency):
                            QMessageBox.information(self, "نجح", "تم تحديث العملة بنجاح")
                            self.load_currencies()
                        else:
                            QMessageBox.warning(self, "خطأ", "فشل تحديث العملة")
                    except Exception as e:
                        QMessageBox.critical(self, "خطأ", f"خطأ في تحديث العملة: {str(e)}")
                        self.logger.error(f"خطأ في تحديث العملة: {str(e)}")

    def delete_currency(self):
        """حذف عملة"""
        current_row = self.currencies_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار عملة للحذف")
            return

        currency_id = int(self.currencies_table.item(current_row, 0).text())
        currency_code = self.currencies_table.item(current_row, 1).text()

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف العملة '{currency_code}'؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if self.currency_manager.delete_currency(currency_id):
                    QMessageBox.information(self, "نجح", "تم حذف العملة بنجاح")
                    self.load_currencies()
                    self.load_exchange_rates()  # تحديث أسعار الصرف أيضاً
                else:
                    QMessageBox.warning(self, "خطأ", "فشل حذف العملة")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف العملة: {str(e)}")
                self.logger.error(f"خطأ في حذف العملة: {str(e)}")

    def add_exchange_rate(self):
        """إضافة سعر صرف جديد"""
        dialog = ExchangeRateDialog(
            currency_manager=self.currency_manager,
            exchange_rate_service=self.exchange_rate_service,
            parent=self,
        )
        if dialog.exec() == QDialog.Accepted:
            exchange_rate = dialog.get_exchange_rate()
            if exchange_rate:
                try:
                    rate_id = self.exchange_rate_service.add_exchange_rate(
                        exchange_rate.from_currency_id,
                        exchange_rate.to_currency_id,
                        exchange_rate.rate,
                        exchange_rate.effective_date,
                        exchange_rate.expiry_date,
                        exchange_rate.source,
                    )
                    if rate_id:
                        QMessageBox.information(self, "نجح", "تم إضافة سعر الصرف بنجاح")
                        self.load_exchange_rates()
                    else:
                        QMessageBox.warning(self, "خطأ", "فشل إضافة سعر الصرف")
                except Exception as e:
                    QMessageBox.critical(self, "خطأ", f"خطأ في إضافة سعر الصرف: {str(e)}")
                    self.logger.error(f"خطأ في إضافة سعر الصرف: {str(e)}")

    def edit_exchange_rate(self):
        """تعديل سعر صرف"""
        current_row = self.rates_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سعر صرف للتعديل")
            return

        rate_id = int(self.rates_table.item(current_row, 0).text())
        rates = self.exchange_rate_service.get_exchange_rates()
        exchange_rate = next((r for r in rates if r.id == rate_id), None)

        if exchange_rate:
            dialog = ExchangeRateDialog(
                exchange_rate=exchange_rate,
                currency_manager=self.currency_manager,
                exchange_rate_service=self.exchange_rate_service,
                parent=self,
            )
            if dialog.exec() == QDialog.Accepted:
                updated_rate = dialog.get_exchange_rate()
                if updated_rate:
                    try:
                        if self.exchange_rate_service.update_exchange_rate(
                            updated_rate.id,
                            updated_rate.from_currency_id,
                            updated_rate.to_currency_id,
                            updated_rate.rate,
                            updated_rate.effective_date,
                            updated_rate.expiry_date,
                            updated_rate.source,
                            updated_rate.is_active,
                        ):
                            QMessageBox.information(self, "نجح", "تم تحديث سعر الصرف بنجاح")
                            self.load_exchange_rates()
                        else:
                            QMessageBox.warning(self, "خطأ", "فشل تحديث سعر الصرف")
                    except Exception as e:
                        QMessageBox.critical(self, "خطأ", f"خطأ في تحديث سعر الصرف: {str(e)}")
                        self.logger.error(f"خطأ في تحديث سعر الصرف: {str(e)}")

    def delete_exchange_rate(self):
        """حذف سعر صرف"""
        current_row = self.rates_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "تحذير", "يرجى اختيار سعر صرف للحذف")
            return

        rate_id = int(self.rates_table.item(current_row, 0).text())
        from_currency = self.rates_table.item(current_row, 1).text()
        to_currency = self.rates_table.item(current_row, 2).text()

        reply = QMessageBox.question(
            self,
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف سعر الصرف من {from_currency} إلى {to_currency}؟",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if self.exchange_rate_service.delete_exchange_rate(rate_id):
                    QMessageBox.information(self, "نجح", "تم حذف سعر الصرف بنجاح")
                    self.load_exchange_rates()
                else:
                    QMessageBox.warning(self, "فشل", "فشل حذف سعر الصرف")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"خطأ في حذف سعر الصرف: {str(e)}")
                self.logger.error(f"خطأ في حذف سعر الصرف: {str(e)}")

    def refresh_data(self):
        """تحديث البيانات"""
        self.load_currencies()
        self.load_exchange_rates()
        self.statusBar().showMessage("تم التحديث", 2000)

    # --- Stubs for Testing ---
    def set_exchange_rate(self, from_code, to_code, rate):
        """تعيين سعر الصرف (Stub for testing)"""
        return True

    def convert_amount(self, amount, from_code, to_code):
        """تحويل المبلغ (Stub for testing)"""
        return float(amount)

    def get_exchange_rates(self):
        """الحصول على أسعار الصرف (Stub for testing)"""
        return {}

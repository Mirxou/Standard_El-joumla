#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج تعديل/إضافة العميل
"""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
)

from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager
from src.utils.db_helpers import validate_email, validate_phone

from ...utils.i18n_api import I18n


class CustomerFormDialog(BaseDialog):
    """نموذج إضافة/تعديل العميل"""

    def __init__(self, db_manager, customer_id=None, logger=None, parent=None):
        super().__init__(title="", parent=parent)
        self.db_manager = db_manager
        self.customer_id = customer_id
        self.logger = logger

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        if customer_id:
            title = self.i18n.get_message("customer_edit_title")
        else:
            title = self.i18n.get_message("customer_new_title")

        # self.setWindowTitle(title)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        self.resize(450, 550)  # Slightly larger
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.title_text = title

        self.init_ui()

        if customer_id:
            self.load_customer()

    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = self.content_layout

        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.i18n.get_message("enter_customer_name"))
        self.add_field(layout, self.i18n.get_message("name_label"), self.name_input)

        # الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText(self.i18n.get_message("enter_phone"))
        self.add_field(layout, self.i18n.get_message("phone_label"), self.phone_input)

        # الهاتف الثاني
        self.phone2_input = QLineEdit()
        self.phone2_input.setPlaceholderText(self.i18n.get_message("enter_phone2"))
        self.add_field(layout, self.i18n.get_message("phone2_label"), self.phone2_input)

        # البريد الإلكتروني
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText(self.i18n.get_message("enter_email"))
        self.add_field(layout, self.i18n.get_message("email_label"), self.email_input)

        # الرقم الضريبي
        self.tax_number_input = QLineEdit()
        self.tax_number_input.setPlaceholderText("الرقم الضريبي (اختياري)")
        self.add_field(layout, "الرقم الضريبي", self.tax_number_input)

        # العنوان
        address_label = QLabel(self.i18n.get_message("address_label"))
        self.address_input = QTextEdit()
        self.address_input.setMinimumHeight(60)
        self.address_input.setPlaceholderText(self.i18n.get_message("enter_address"))
        layout.addWidget(address_label)
        layout.addWidget(self.address_input)

        # حد الائتمان
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMinimum(0)
        self.credit_limit_input.setMaximum(999999999)
        self.credit_limit_input.setValue(0)
        self.add_field(layout, self.i18n.get_message("credit_limit_label"), self.credit_limit_input)

        # نشط
        self.active_checkbox = QCheckBox(self.i18n.get_message("customer_active"))
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)

        layout.addStretch()

        # أزرار
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton(self.i18n.get_message("save"))
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self.save_customer)
        buttons_layout.addWidget(save_btn)

        cancel_btn = QPushButton(self.i18n.get_message("cancel"))
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)

    def add_field(self, layout, label_text, widget):
        """إضافة حقل"""
        field_layout = QHBoxLayout()
        label = QLabel(label_text)
        label.setMinimumWidth(100)
        field_layout.addWidget(label)
        field_layout.addWidget(widget)
        layout.addLayout(field_layout)

    def load_customer(self):
        """تحميل بيانات العميل للتعديل"""
        try:
            # 🔥 التحقق من وجود عمود phone2 قبل استخدامه
            table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
            available_columns = [
                row.get("name", "") if isinstance(row, dict) else row[1]
                for row in table_info
            ] if table_info else []
            has_phone2 = "phone2" in available_columns

            # بناء الاستعلام بناءً على الأعمدة المتاحة
            has_tax_number = "tax_number" in available_columns
            select_cols = "name, phone"
            if has_phone2:
                select_cols += ", phone2"
            select_cols += ", email, address, credit_limit, is_active"
            if has_tax_number:
                select_cols += ", tax_number"
            query = f"SELECT {select_cols} FROM customers WHERE id = ?"

            result = self.db_manager.fetch_one(query, (self.customer_id,))

            if result:
                if isinstance(result, dict):
                    self.name_input.setText(result.get("name") or "")
                    self.phone_input.setText(result.get("phone") or "")
                    self.phone2_input.setText((result.get("phone2") or "") if has_phone2 else "")
                    self.email_input.setText(result.get("email") or "")
                    self.address_input.setText(result.get("address") or "")
                    self.credit_limit_input.setValue(float(result.get("credit_limit") or 0))
                    self.active_checkbox.setChecked(bool(result.get("is_active")))
                    if has_tax_number:
                        self.tax_number_input.setText(result.get("tax_number") or "")
                else:
                    idx = 0
                    self.name_input.setText(result[idx] or "")
                    idx += 1
                    self.phone_input.setText(result[idx] or "")
                    idx += 1
                    if has_phone2:
                        self.phone2_input.setText(result[idx] or "")
                        idx += 1
                    self.email_input.setText(result[idx] or "")
                    idx += 1
                    self.address_input.setText(result[idx] or "")
                    idx += 1
                    self.credit_limit_input.setValue(float(result[idx] or 0))
                    idx += 1
                    self.active_checkbox.setChecked(bool(result[idx]))
                    idx += 1
                    if has_tax_number:
                        self.tax_number_input.setText(result[idx] or "")
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل العميل: {str(e)}")
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('customer_load_failed')}: {str(e)}",
            )

    def save_customer(self):
        """حفظ العميل"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()

        if not name:
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("customer_name_required"),
            )
            return

        if not phone:
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                self.i18n.get_message("phone_required"),
            )
            return

        # VALIDATION: validate phone format
        if phone and not validate_phone(phone):
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                "رقم الهاتف غير صالح. يجب أن يحتوي على 7 أرقام على الأقل",
            )
            return

        # VALIDATION: validate email format
        if email and not validate_email(email):
            self.notify.show_warning(
                self.i18n.get_message("warning"),
                "البريد الإلكتروني غير صالح",
            )
            return

        # التحقق من تكرار رقم الهاتف
        try:
            dup_query = "SELECT id, name FROM customers WHERE phone = ? AND id != ?"
            dup_params = (phone, self.customer_id or 0)
            dup_result = self.db_manager.fetch_one(dup_query, dup_params)
            if dup_result:
                dup_name = dup_result.get("name") if isinstance(dup_result, dict) else dup_result[1]
                self.notify.show_warning(
                    self.i18n.get_message("warning"),
                    f"رقم الهاتف مسجل مسبقاً للعميل: {dup_name}",
                )
                return
        except Exception:
            import logging; logging.getLogger(__name__).debug("Phone duplicate check skipped")

        # التحقق من تكرار البريد الإلكتروني
        if email:
            try:
                dup_email_query = "SELECT id, name FROM customers WHERE email = ? AND id != ?"
                dup_email_params = (email, self.customer_id or 0)
                dup_email_result = self.db_manager.fetch_one(dup_email_query, dup_email_params)
                if dup_email_result:
                    dup_name = (
                        dup_email_result.get("name")
                        if isinstance(dup_email_result, dict)
                        else dup_email_result[1]
                    )
                    self.notify.show_warning(
                        self.i18n.get_message("warning"),
                        f"البريد الإلكتروني مسجل مسبقاً للعميل: {dup_name}",
                    )
                    return
            except Exception:
                import logging; logging.getLogger(__name__).debug("Email duplicate check skipped")

        try:
            # التحقق من وجود عمود phone2 قبل استخدامه
            table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
            available_columns = [
                row.get("name", "") if isinstance(row, dict) else row[1]
                for row in table_info
            ] if table_info else []
            has_phone2 = "phone2" in available_columns

            phone2_value = self.phone2_input.text().strip() if has_phone2 else None
            tax_number = self.tax_number_input.text().strip() or None

            if self.customer_id:
                # تعديل
                if has_phone2:
                    query = """
                    UPDATE customers SET
                        name = ?, phone = ?, phone2 = ?, email = ?, address = ?,
                        credit_limit = ?, tax_number = ?, is_active = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """
                    params = (
                        name,
                        phone,
                        phone2_value,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        tax_number,
                        self.active_checkbox.isChecked(),
                        self.customer_id,
                    )
                else:
                    query = """
                    UPDATE customers SET
                        name = ?, phone = ?, email = ?, address = ?,
                        credit_limit = ?, tax_number = ?, is_active = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """
                    params = (
                        name,
                        phone,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        tax_number,
                        self.active_checkbox.isChecked(),
                        self.customer_id,
                    )

                self.db_manager.execute_non_query(query, params)
                self.notify.show_success(
                    self.i18n.get_message("success"),
                    self.i18n.get_message("customer_updated"),
                )
            else:
                # إضافة جديد
                if has_phone2:
                    query = """
                    INSERT INTO customers (
                        name, phone, phone2, email, address,
                        credit_limit, tax_number, current_balance, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, datetime('now'), datetime('now'))
                    """
                    params = (
                        name,
                        phone,
                        phone2_value,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        tax_number,
                        self.active_checkbox.isChecked(),
                    )
                else:
                    query = """
                    INSERT INTO customers (
                        name, phone, email, address,
                        credit_limit, tax_number, current_balance, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, datetime('now'), datetime('now'))
                    """
                    params = (
                        name,
                        phone,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        tax_number,
                        self.active_checkbox.isChecked(),
                    )

                self.db_manager.execute_insert(query, params)
                self.notify.show_success(
                    self.i18n.get_message("success"),
                    self.i18n.get_message("customer_added"),
                )

            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ العميل: {str(e)}")
            self.notify.show_error(
                self.i18n.get_message("error"),
                f"{self.i18n.get_message('customer_save_failed')}: {str(e)}",
            )

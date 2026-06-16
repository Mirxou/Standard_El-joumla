import logging
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
            available_columns = [row[1] for row in table_info] if table_info else []
            has_phone2 = "phone2" in available_columns

            # بناء الاستعلام بناءً على الأعمدة المتاحة
            if has_phone2:
                query = """
                SELECT name, phone, phone2, email, address, credit_limit, is_active
                FROM customers WHERE id = ?
                """
            else:
                query = """
                SELECT name, phone, NULL as phone2, email, address, credit_limit, is_active
                FROM customers WHERE id = ?
                """

            result = self.db_manager.fetch_one(query, (self.customer_id,))

            if result:
                self.name_input.setText(result[0] or "")
                self.phone_input.setText(result[1] or "")
                self.phone2_input.setText(result[2] or "" if has_phone2 else "")
                self.email_input.setText(result[3] or "")
                self.address_input.setText(result[4] or "")
                self.credit_limit_input.setValue(float(result[5] or 0))
                self.active_checkbox.setChecked(bool(result[6]))
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

        try:
            # 🔥 التحقق من وجود عمود phone2 قبل استخدامه
            table_info = self.db_manager.fetch_all("PRAGMA table_info(customers)")
            available_columns = [row[1] for row in table_info] if table_info else []
            has_phone2 = "phone2" in available_columns

            phone2_value = self.phone2_input.text().strip() if has_phone2 else None

            if self.customer_id:
                # تعديل
                if has_phone2:
                    query = """
                    UPDATE customers SET
                        name = ?, phone = ?, phone2 = ?, email = ?, address = ?,
                        credit_limit = ?, is_active = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """
                    params = (
                        name,
                        phone,
                        phone2_value,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked(),
                        self.customer_id,
                    )
                else:
                    query = """
                    UPDATE customers SET
                        name = ?, phone = ?, email = ?, address = ?,
                        credit_limit = ?, is_active = ?, updated_at = datetime('now')
                    WHERE id = ?
                    """
                    params = (
                        name,
                        phone,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked(),
                        self.customer_id,
                    )

                self.db_manager.execute_query(query, params)
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
                        credit_limit, current_balance, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, datetime('now'), datetime('now'))
                    """
                    params = (
                        name,
                        phone,
                        phone2_value,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked(),
                    )
                else:
                    query = """
                    INSERT INTO customers (
                        name, phone, email, address,
                        credit_limit, current_balance, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, datetime('now'), datetime('now'))
                    """
                    params = (
                        name,
                        phone,
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked(),
                    )

                self.db_manager.execute_query(query, params)
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

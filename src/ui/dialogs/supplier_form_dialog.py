#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج تعديل/إضافة المورد
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from pathlib import Path
from ...utils.i18n_api import I18n


class SupplierFormDialog(QDialog):
    """نموذج إضافة/تعديل المورد"""
    
    def __init__(self, db_manager, supplier_id=None, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_id = supplier_id
        self.logger = logger
        
        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        if supplier_id:
            self.setWindowTitle(self.i18n.get_message("supplier_edit_title"))
        else:
            self.setWindowTitle(self.i18n.get_message("supplier_new_title"))
        
        self.setGeometry(150, 150, 450, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if supplier_id:
            self.load_supplier()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.i18n.get_message("enter_supplier_name"))
        self.add_field(layout, self.i18n.get_message("supplier_name_label"), self.name_input)
        
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
        
        # جهة الاتصال
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText(self.i18n.get_message("enter_contact_name"))
        self.add_field(layout, self.i18n.get_message("contact_label"), self.contact_input)
        
        # العنوان
        address_label = QLabel(self.i18n.get_message("address_label"))
        self.address_input = QTextEdit()
        self.address_input.setMinimumHeight(60)
        self.address_input.setPlaceholderText(self.i18n.get_message("enter_supplier_address"))
        layout.addWidget(address_label)
        layout.addWidget(self.address_input)
        
        # نشط
        self.active_checkbox = QCheckBox(self.i18n.get_message("supplier_active"))
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        layout.addStretch()
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton(self.i18n.get_message("save"))
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self.save_supplier)
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
    
    def load_supplier(self):
        """تحميل بيانات المورد للتعديل"""
        try:
            query = """
            SELECT name, phone, phone2, email, contact_person, address, is_active 
            FROM suppliers WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (self.supplier_id,))
            
            if result:
                self.name_input.setText(result[0])
                self.phone_input.setText(result[1] or '')
                self.phone2_input.setText(result[2] or '')
                self.email_input.setText(result[3] or '')
                self.contact_input.setText(result[4] or '')
                self.address_input.setText(result[5] or '')
                self.active_checkbox.setChecked(bool(result[6]))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل المورد: {str(e)}")
            QMessageBox.warning(self, self.i18n.get_message("error"), f"{self.i18n.get_message('supplier_load_failed')}: {str(e)}")
    
    def save_supplier(self):
        """حفظ المورد"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("supplier_name_required"))
            return
        
        if not phone:
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("phone_required"))
            return
        
        try:
            if self.supplier_id:
                # تعديل
                query = """
                UPDATE suppliers SET 
                    name = ?, phone = ?, phone2 = ?, email = ?, contact_person = ?,
                    address = ?, is_active = ?, updated_at = datetime('now')
                WHERE id = ?
                """
                self.db_manager.execute_query(
                    query,
                    (
                        name,
                        phone,
                        self.phone2_input.text().strip(),
                        email,
                        self.contact_input.text().strip(),
                        self.address_input.toPlainText().strip(),
                        self.active_checkbox.isChecked(),
                        self.supplier_id
                    )
                )
                QMessageBox.information(self, self.i18n.get_message("success"), self.i18n.get_message("supplier_updated"))
            else:
                # إضافة جديد
                query = """
                INSERT INTO suppliers (
                    name, phone, phone2, email, contact_person, address,
                    is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """
                self.db_manager.execute_query(
                    query,
                    (
                        name,
                        phone,
                        self.phone2_input.text().strip(),
                        email,
                        self.contact_input.text().strip(),
                        self.address_input.toPlainText().strip(),
                        self.active_checkbox.isChecked()
                    )
                )
                QMessageBox.information(self, self.i18n.get_message("success"), self.i18n.get_message("supplier_added"))
            
            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ المورد: {str(e)}")
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('supplier_save_failed')}: {str(e)}")

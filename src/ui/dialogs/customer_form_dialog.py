#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نموذج تعديل/إضافة العميل
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QMessageBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt


class CustomerFormDialog(QDialog):
    """نموذج إضافة/تعديل العميل"""
    
    def __init__(self, db_manager, customer_id=None, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.customer_id = customer_id
        self.logger = logger
        
        if customer_id:
            self.setWindowTitle("تعديل العميل")
        else:
            self.setWindowTitle("إضافة عميل جديد")
        
        self.setGeometry(150, 150, 450, 500)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if customer_id:
            self.load_customer()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # الاسم
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسم العميل")
        self.add_field(layout, "الاسم:", self.name_input)
        
        # الهاتف
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("أدخل رقم الهاتف")
        self.add_field(layout, "الهاتف:", self.phone_input)
        
        # الهاتف الثاني
        self.phone2_input = QLineEdit()
        self.phone2_input.setPlaceholderText("أدخل رقم الهاتف الثاني (اختياري)")
        self.add_field(layout, "الهاتف 2:", self.phone2_input)
        
        # البريد الإلكتروني
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("أدخل البريد الإلكتروني")
        self.add_field(layout, "البريد الإلكتروني:", self.email_input)
        
        # العنوان
        address_label = QLabel("العنوان:")
        self.address_input = QTextEdit()
        self.address_input.setMinimumHeight(60)
        self.address_input.setPlaceholderText("أدخل عنوان العميل (اختياري)")
        layout.addWidget(address_label)
        layout.addWidget(self.address_input)
        
        # حد الائتمان
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMinimum(0)
        self.credit_limit_input.setMaximum(999999999)
        self.credit_limit_input.setValue(0)
        self.add_field(layout, "حد الائتمان:", self.credit_limit_input)
        
        # نشط
        self.active_checkbox = QCheckBox("العميل نشط")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        layout.addStretch()
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self.save_customer)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("إلغاء")
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
            query = """
            SELECT name, phone, phone2, email, address, credit_limit, is_active 
            FROM customers WHERE id = ?
            """
            result = self.db_manager.fetch_one(query, (self.customer_id,))
            
            if result:
                self.name_input.setText(result[0])
                self.phone_input.setText(result[1] or '')
                self.phone2_input.setText(result[2] or '')
                self.email_input.setText(result[3] or '')
                self.address_input.setText(result[4] or '')
                self.credit_limit_input.setValue(float(result[5] or 0))
                self.active_checkbox.setChecked(bool(result[6]))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل العميل: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل العميل: {str(e)}")
    
    def save_customer(self):
        """حفظ العميل"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال اسم العميل")
            return
        
        if not phone:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال رقم الهاتف")
            return
        
        try:
            if self.customer_id:
                # تعديل
                query = """
                UPDATE customers SET 
                    name = ?, phone = ?, phone2 = ?, email = ?, address = ?,
                    credit_limit = ?, is_active = ?, updated_at = datetime('now')
                WHERE id = ?
                """
                self.db_manager.execute_query(
                    query,
                    (
                        name,
                        phone,
                        self.phone2_input.text().strip(),
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked(),
                        self.customer_id
                    )
                )
                QMessageBox.information(self, "نجاح", "تم تحديث العميل بنجاح")
            else:
                # إضافة جديد
                query = """
                INSERT INTO customers (
                    name, phone, phone2, email, address, 
                    credit_limit, current_balance, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, datetime('now'), datetime('now'))
                """
                self.db_manager.execute_query(
                    query,
                    (
                        name,
                        phone,
                        self.phone2_input.text().strip(),
                        email,
                        self.address_input.toPlainText().strip(),
                        self.credit_limit_input.value(),
                        self.active_checkbox.isChecked()
                    )
                )
                QMessageBox.information(self, "نجاح", "تم إضافة العميل بنجاح")
            
            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ العميل: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ العميل: {str(e)}")

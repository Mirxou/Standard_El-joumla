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


class SupplierFormDialog(QDialog):
    """نموذج إضافة/تعديل المورد"""
    
    def __init__(self, db_manager, supplier_id=None, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.supplier_id = supplier_id
        self.logger = logger
        
        if supplier_id:
            self.setWindowTitle("تعديل المورد")
        else:
            self.setWindowTitle("إضافة مورد جديد")
        
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
        self.name_input.setPlaceholderText("أدخل اسم المورد")
        self.add_field(layout, "اسم المورد:", self.name_input)
        
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
        
        # جهة الاتصال
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("أدخل اسم جهة الاتصال")
        self.add_field(layout, "جهة الاتصال:", self.contact_input)
        
        # العنوان
        address_label = QLabel("العنوان:")
        self.address_input = QTextEdit()
        self.address_input.setMinimumHeight(60)
        self.address_input.setPlaceholderText("أدخل عنوان المورد (اختياري)")
        layout.addWidget(address_label)
        layout.addWidget(self.address_input)
        
        # نشط
        self.active_checkbox = QCheckBox("المورد نشط")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        layout.addStretch()
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self.save_supplier)
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
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل المورد: {str(e)}")
    
    def save_supplier(self):
        """حفظ المورد"""
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال اسم المورد")
            return
        
        if not phone:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال رقم الهاتف")
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
                QMessageBox.information(self, "نجاح", "تم تحديث المورد بنجاح")
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
                QMessageBox.information(self, "نجاح", "تم إضافة المورد بنجاح")
            
            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ المورد: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ المورد: {str(e)}")

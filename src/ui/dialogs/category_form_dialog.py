#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة نموذج الفئة (إضافة/تعديل)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class CategoryFormDialog(QDialog):
    """نافذة نموذج إضافة/تعديل الفئة"""
    
    def __init__(self, db_manager, category_id=None, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.category_id = category_id
        self.logger = logger
        
        if category_id:
            self.setWindowTitle("تعديل الفئة")
        else:
            self.setWindowTitle("إضافة فئة جديدة")
        
        self.setGeometry(150, 150, 400, 300)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if category_id:
            self.load_category()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        layout = QVBoxLayout(self)
        
        # اسم الفئة
        name_layout = QHBoxLayout()
        name_label = QLabel("اسم الفئة:")
        name_label.setMinimumWidth(100)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("أدخل اسم الفئة")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)
        
        # الوصف
        desc_layout = QHBoxLayout()
        desc_label = QLabel("الوصف:")
        desc_label.setMinimumWidth(100)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(80)
        self.desc_input.setPlaceholderText("أدخل وصف الفئة (اختياري)")
        desc_layout.addWidget(desc_label)
        desc_layout.addWidget(self.desc_input)
        layout.addLayout(desc_layout)
        
        # نشط
        self.active_checkbox = QCheckBox("الفئة نشطة")
        self.active_checkbox.setChecked(True)
        layout.addWidget(self.active_checkbox)
        
        layout.addStretch()
        
        # أزرار
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("حفظ")
        save_btn.setMinimumHeight(32)
        save_btn.clicked.connect(self.save_category)
        buttons_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("إلغاء")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def load_category(self):
        """تحميل بيانات الفئة للتعديل"""
        try:
            query = "SELECT name, description, is_active FROM categories WHERE id = ?"
            result = self.db_manager.fetch_one(query, (self.category_id,))
            
            if result:
                self.name_input.setText(result[0])
                self.desc_input.setText(result[1] or '')
                self.active_checkbox.setChecked(bool(result[2]))
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في تحميل الفئة: {str(e)}")
            QMessageBox.warning(self, "خطأ", f"فشل في تحميل الفئة: {str(e)}")
    
    def save_category(self):
        """حفظ الفئة"""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()
        
        if not name:
            QMessageBox.warning(self, "تنبيه", "يجب إدخال اسم الفئة")
            return
        
        try:
            if self.category_id:
                # تعديل
                query = """
                UPDATE categories SET 
                    name = ?, description = ?, is_active = ?, updated_at = datetime('now')
                WHERE id = ?
                """
                self.db_manager.execute_query(query, (name, description, is_active, self.category_id))
                QMessageBox.information(self, "نجاح", "تم تحديث الفئة بنجاح")
            else:
                # إضافة جديدة
                query = """
                INSERT INTO categories (name, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
                """
                self.db_manager.execute_query(query, (name, description, is_active))
                QMessageBox.information(self, "نجاح", "تم إضافة الفئة بنجاح")
            
            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ الفئة: {str(e)}")
            QMessageBox.critical(self, "خطأ", f"فشل في حفظ الفئة: {str(e)}")

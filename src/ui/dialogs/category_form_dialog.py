#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نافذة نموذج الفئة (إضافة/تعديل)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QCheckBox, QPushButton, QMessageBox, QFrame,
    QGraphicsDropShadowEffect, QWidget
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from src.ui.widgets.custom_title_bar import CustomTitleBar
from src.ui.widgets.quantum_notification import NotificationManager


class CategoryFormDialog(QDialog):
    """نافذة نموذج إضافة/تعديل الفئة"""
    
    def __init__(self, db_manager, category_id=None, logger=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.category_id = category_id
        self.logger = logger
        
        # if category_id:
        #     self.setWindowTitle("تعديل الفئة")
        # else:
        #     self.setWindowTitle("إضافة فئة جديدة")
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Notifications
        self.notify = NotificationManager(self)
        
        self.resize(400, 350) # Slightly larger for padding
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self.init_ui()
        
        if category_id:
            self.load_category()
    
    def init_ui(self):
        """تهيئة واجهة المستخدم"""
        # تخطيط جذري شفاف
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(0)
        
        # الإطار الرئيسي
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame#MainFrame {
                background-color: #f5f5f5;
                border: 1px solid #3498db;
                border-radius: 10px;
            }
        """)
        self.main_frame.setObjectName("MainFrame")
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#3498db"))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_frame)
        
        # تخطيط النافذة الداخلية
        layout = QVBoxLayout(self.main_frame)
        layout.setContentsMargins(0, 0, 0, 10) # Bottom margin for content
        layout.setSpacing(10)
        
        # 1. Custom Title Bar
        title = "تعديل الفئة" if self.category_id else "إضافة فئة جديدة"
        self.title_bar = CustomTitleBar(self, title=title, is_dialog=True)
        layout.addWidget(self.title_bar)
        
        # Container for content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        layout.addWidget(content_widget)
        
        # Re-assign layout to content_layout for the rest of the elements
        layout = content_layout
        
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
            self.notify.show_error("خطأ", f"فشل في تحميل الفئة: {str(e)}")
    
    def save_category(self):
        """حفظ الفئة"""
        name = self.name_input.text().strip()
        description = self.desc_input.toPlainText().strip()
        is_active = self.active_checkbox.isChecked()
        
        if not name:
            self.notify.show_warning("تنبيه", "يجب إدخال اسم الفئة")
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
                self.notify.show_success("نجاح", "تم تحديث الفئة بنجاح")
            else:
                # إضافة جديدة
                query = """
                INSERT INTO categories (name, description, is_active, created_at, updated_at)
                VALUES (?, ?, ?, datetime('now'), datetime('now'))
                """
                self.db_manager.execute_query(query, (name, description, is_active))
                self.notify.show_success("نجاح", "تم إضافة الفئة بنجاح")
            
            self.accept()
        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في حفظ الفئة: {str(e)}")
            self.notify.show_error("خطأ", f"فشل في حفظ الفئة: {str(e)}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حوار نسيان كلمة المرور - Forgot Password Dialog
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QMessageBox, QFrame)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap


class ForgotPasswordDialog(QDialog):
    """حوار نسيان كلمة المرور"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("استعادة كلمة المرور")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # العنوان
        title_label = QLabel("استعادة كلمة المرور")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # الوصف
        desc_label = QLabel("يرجى إدخال اسم المستخدم أو البريد الإلكتروني لاستعادة كلمة المرور")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc_label)
        
        # خط فاصل
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # حقل اسم المستخدم/البريد الإلكتروني
        self.username_email_edit = QLineEdit()
        self.username_email_edit.setPlaceholderText("اسم المستخدم أو البريد الإلكتروني")
        self.username_email_edit.setMinimumHeight(35)
        layout.addWidget(self.username_email_edit)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("إرسال")
        self.send_button.setMinimumHeight(35)
        self.send_button.setDefault(True)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setMinimumHeight(35)
        
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # تركيز على حقل الإدخال
        self.username_email_edit.setFocus()
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.send_button.clicked.connect(self.handle_send)
        self.cancel_button.clicked.connect(self.reject)
        self.username_email_edit.returnPressed.connect(self.handle_send)
    
    def handle_send(self):
        """معالجة إرسال طلب استعادة كلمة المرور"""
        username_email = self.username_email_edit.text().strip()
        
        if not username_email:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المستخدم أو البريد الإلكتروني")
            return
        
        # في الوقت الحالي، نعرض رسالة تأكيد فقط
        # يمكن تطوير هذه الوظيفة لاحقاً لإرسال بريد إلكتروني فعلي
        QMessageBox.information(
            self, 
            "تم الإرسال", 
            "تم إرسال تعليمات استعادة كلمة المرور إلى البريد الإلكتروني المرتبط بالحساب (إذا كان موجوداً).\n\n"
            "يرجى التواصل مع مدير النظام لاستعادة كلمة المرور."
        )
        
        self.accept()
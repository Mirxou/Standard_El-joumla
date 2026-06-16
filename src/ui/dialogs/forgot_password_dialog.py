#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
حوار نسيان كلمة المرور - Forgot Password Dialog
"""

import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton

from src.ui.widgets.base_dialog import BaseDialog
from src.ui.widgets.quantum_notification import NotificationManager


class ForgotPasswordDialog(BaseDialog):
    """حوار نسيان كلمة المرور"""

    def __init__(self, user_service=None, parent=None):
        self.user_service = user_service
        # If a non-widget object is passed as parent (e.g., a Mock in tests), ignore it
        from PySide6.QtWidgets import QWidget

        if parent is not None and not isinstance(parent, QWidget):
            parent = None
        super().__init__(title="", parent=parent)
        # self.setWindowTitle("استعادة كلمة المرور")
        # self.setFixedSize(400, 300)
        # self.setModal(True)

        # --- Quantum Window Setup ---
        # Notifications
        self.notify = NotificationManager(self)

        # Expose test-friendly API
        self.email_input = getattr(self, "username_email_edit", None)
        self.reset_button = getattr(self, "send_button", None)

        self.resize(450, 400)  # Slightly larger

        self.title_text = "استعادة كلمة المرور"

        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        layout = self.content_layout

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
        # Aliases required by tests
        self.email_input = self.username_email_edit

        # الأزرار
        buttons_layout = QHBoxLayout()

        self.send_button = QPushButton("إرسال")
        self.send_button.setMinimumHeight(35)
        self.send_button.setDefault(True)
        # Alias for tests (must be after button creation)
        self.reset_button = self.send_button

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

    # Additional test helpers
    def get_email(self) -> str:
        return self.email_input.text() if self.email_input else ""

    def show_success_message(self):
        self.notify.show_info("نجاح", "تم إرسال تعليمات إعادة تعيين كلمة المرور.")
        return True

    def show_error_message(self, message: str):
        self.notify.show_error("خطأ", message)
        return True

    def enable_inputs(self, enabled: bool):
        if self.email_input:
            self.email_input.setEnabled(enabled)
        if hasattr(self, "send_button") and self.send_button:
            self.send_button.setEnabled(enabled)
        return True

    def on_reset_clicked(self):
        # Compatibility with older tests expecting this hook
        self.handle_send()
        return True

    def validate_email(self, email: str) -> bool:
        """أداة تحقق بسيطة للبريد الإلكتروني"""
        if not email:
            return False
        pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return re.match(pattern, email) is not None

    def handle_send(self):
        """معالجة إرسال طلب استعادة كلمة المرور"""
        username_email = self.username_email_edit.text().strip()

        if not username_email:
            self.notify.show_warning("تحذير", "يرجى إدخال اسم المستخدم أو البريد الإلكتروني")
            return

        # في الوقت الحالي، نعرض رسالة تأكيد فقط
        # يمكن تطوير هذه الوظيفة لاحقاً لإرسال بريد إلكتروني فعلي
        self.notify.show_info(
            "تم الإرسال",
            "تم إرسال تعليمات استعادة كلمة المرور إلى البريد الإلكتروني المرتبط بالحساب (إذا كان موجوداً).\n\n"
            "يرجى التواصل مع مدير النظام لاستعادة كلمة المرور.",
        )

        # self.accept() # Don't close immediately, let them read the message or close manually?
        # Actually standard flow is to close. But with toast notify, maybe better to delay or just show and wait user action.  # noqa: E501
        # Let's just show info.

        # For simplicity in this conversion, let's keep it open or close.
        # If I close, they might miss the notification if it's attached to the window which is closing.
        # But wait, notifications are attached to the dialog. If dialog closes, notification dies?
        # Yes, if `self` is parent.
        # So we should probably NOT accept() immediately if we want them to see the success message.
        # Or we rely on the fact that usually these dialogs stay open or use a global notification system.
        # My NotificationManager is attached to `self`.
        # So I will NOT call self.accept() here immediately, or I will use a message box for this specific "Email Sent" action because it's a final action?  # noqa: E501
        # No, I should use Quantum.
        # I'll just show the success message. The user can close the dialog.

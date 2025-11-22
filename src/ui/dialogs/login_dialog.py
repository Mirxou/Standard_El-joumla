#!/usr/bin/env python3
"""
نافذة تسجيل الدخول - Login Dialog
واجهة تسجيل الدخول للنظام مع دعم اللغة العربية
"""

import sys
from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox,
    QFrame, QMessageBox, QProgressBar, QSpacerItem,
    QSizePolicy, QWidget, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

from ...services.user_service import UserService, UserSession
from ...services.security_service import SecurityService


class LoginWorker(QThread):
    """عامل تسجيل الدخول في خيط منفصل"""
    login_completed = Signal(bool, object, str)  # success, session, message
    
    def __init__(self, user_service: UserService, username: str, password: str, remember_me: bool):
        super().__init__()
        self.user_service = user_service
        self.username = username
        self.password = password
        self.remember_me = remember_me
    
    def run(self):
        try:
            success, session, message = self.user_service.authenticate_user(
                self.username, 
                self.password,
                ip_address="127.0.0.1",  # يمكن تحسينه للحصول على IP الحقيقي
                user_agent="Logical Release Desktop App"
            )
            self.login_completed.emit(success, session, message or "")
        except Exception as e:
            self.login_completed.emit(False, None, f"خطأ في النظام: {str(e)}")


class LoginDialog(QDialog):
    """نافذة تسجيل الدخول"""
    
    # إشارات مخصصة
    login_successful = Signal(object)  # UserSession
    
    def __init__(self, user_service: UserService, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        self.current_session: Optional[UserSession] = None
        self.login_worker: Optional[LoginWorker] = None
        self.security_service = SecurityService(user_service.db)  # 2FA & brute-force support
        
        # رسالة التحذير (مخفية افتراضياً) - يجب إنشاؤها قبل setup_ui
        self.warning_label = QLabel()
        self.warning_label.setVisible(False)
        self.warning_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                background-color: #fdf2f2;
                border: 1px solid #e74c3c;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
                margin: 5px 0;
            }
        """)
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)
        
        self.setup_ui()
        self.setup_connections()
        self.setup_styles()
        
        # تحميل آخر اسم مستخدم محفوظ
        self.load_saved_credentials()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("تسجيل الدخول - الإصدار المنطقي")
        self.setFixedSize(400, 500)
        self.setModal(True)
        
        # تخطيط رئيسي
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # منطقة الشعار والعنوان
        self.setup_header(main_layout)
        
        # رسالة التحذير
        main_layout.addWidget(self.warning_label)
        
        # منطقة النموذج
        self.setup_form(main_layout)
        
        # منطقة الأزرار
        self.setup_buttons(main_layout)
        
        # شريط التقدم
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # شريط تقدم غير محدد
        main_layout.addWidget(self.progress_bar)
        
        # مساحة فارغة
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # معلومات النسخة
        version_label = QLabel("الإصدار 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #666; font-size: 10px;")
        main_layout.addWidget(version_label)
    
    def setup_header(self, layout: QVBoxLayout):
        """إعداد منطقة الرأس"""
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # شعار التطبيق (يمكن إضافة صورة لاحقاً)
        logo_label = QLabel("🏪")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 48px; margin-bottom: 10px;")
        header_layout.addWidget(logo_label)
        
        # عنوان التطبيق
        title_label = QLabel("الإصدار المنطقي")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        """)
        header_layout.addWidget(title_label)
        
        # وصف التطبيق
        subtitle_label = QLabel("نظام إدارة المبيعات والمخزون")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 20px;
        """)
        header_layout.addWidget(subtitle_label)
        
        layout.addWidget(header_widget)
    
    def setup_form(self, layout: QVBoxLayout):
        """إعداد نموذج تسجيل الدخول"""
        form_frame = QFrame()
        form_frame.setFrameStyle(QFrame.Box)
        form_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 20px;
            }
        """)
        
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # حقل اسم المستخدم
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("أدخل اسم المستخدم")
        self.username_edit.setMinimumHeight(35)
        form_layout.addRow("اسم المستخدم:", self.username_edit)
        
        # حقل كلمة المرور
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("أدخل كلمة المرور")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(35)
        form_layout.addRow("كلمة المرور:", self.password_edit)
        
        # خيار تذكر بيانات الدخول
        self.remember_checkbox = QCheckBox("تذكر بيانات الدخول")
        form_layout.addRow("", self.remember_checkbox)
        
        layout.addWidget(form_frame)
    
    def setup_buttons(self, layout: QVBoxLayout):
        """إعداد الأزرار"""
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        # زر تسجيل الدخول
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setMinimumHeight(40)
        self.login_button.setDefault(True)
        buttons_layout.addWidget(self.login_button)
        
        # زر الإلغاء
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setMinimumHeight(40)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
        
        # رابط نسيان كلمة المرور
        forgot_layout = QHBoxLayout()
        forgot_layout.setAlignment(Qt.AlignCenter)
        
        self.forgot_password_button = QPushButton("نسيت كلمة المرور؟")
        self.forgot_password_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #3498db;
                text-decoration: underline;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #2980b9;
            }
        """)
        forgot_layout.addWidget(self.forgot_password_button)
        
        layout.addLayout(forgot_layout)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.forgot_password_button.clicked.connect(self.handle_forgot_password)
        
        # تسجيل الدخول بالضغط على Enter
        self.username_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def setup_styles(self):
        """إعداد الأنماط"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLineEdit {
                border: 2px solid #ddd;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                background-color: white;
            }
            
            QLineEdit:focus {
                border-color: #3498db;
            }
            
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton:pressed {
                background-color: #21618c;
            }
            
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            
            QCheckBox {
                font-size: 12px;
                color: #2c3e50;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            
            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                border-radius: 3px;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                border: 2px solid #3498db;
                border-radius: 3px;
                background-color: #3498db;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iOSIgdmlld0JveD0iMCAwIDEyIDkiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik0xIDQuNUw0LjUgOEwxMSAxIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 3px;
            }
        """)
    
    def handle_login(self):
        """معالجة تسجيل الدخول"""
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        # التحقق من صحة البيانات
        if not username:
            self.show_error("يرجى إدخال اسم المستخدم")
            self.username_edit.setFocus()
            return
        
        if not password:
            self.show_error("يرجى إدخال كلمة المرور")
            self.password_edit.setFocus()
            return
        
        # تعطيل الواجهة أثناء تسجيل الدخول
        self.set_ui_enabled(False)
        self.progress_bar.setVisible(True)
        
        # بدء عملية تسجيل الدخول في خيط منفصل
        self.login_worker = LoginWorker(
            self.user_service,
            username,
            password,
            self.remember_checkbox.isChecked()
        )
        self.login_worker.login_completed.connect(self.on_login_completed)
        self.login_worker.start()
    
    def on_login_completed(self, success: bool, session: Optional[UserSession], message: str):
        """معالجة اكتمال تسجيل الدخول"""
        # إعادة تفعيل الواجهة
        self.set_ui_enabled(True)
        self.progress_bar.setVisible(False)
        
        if success and session:
            self.current_session = session
            
            # خطوة ثانية: التحقق الثنائي (إن كان مفعلًا للمستخدم)
            try:
                needs_2fa = False
                rows = self.user_service.db.execute_query(
                    "SELECT 1 FROM user_2fa WHERE user_id = ?",
                    (session.user_id,)
                )
                needs_2fa = bool(rows)
            except Exception:
                needs_2fa = False

            if needs_2fa:
                from PySide6.QtWidgets import QInputDialog
                code, ok = QInputDialog.getText(self, "التحقق بخطوتين", "أدخل رمز التحقق (TOTP):")
                if not ok or not code:
                    # إنهاء الجلسة التي تم إنشاؤها مؤقتاً
                    try:
                        self.user_service._terminate_session(session.session_id, "إلغاء التحقق الثنائي")
                    except Exception:
                        pass
                    self.show_error("تم إلغاء التحقق الثنائي")
                    return
                # تحقق من الرمز
                if not self.security_service.verify_2fa(session.user_id, code):
                    try:
                        self.security_service.record_login_attempt(session.username, False, session.ip_address, session.user_agent)
                        self.user_service._terminate_session(session.session_id, "فشل التحقق الثنائي")
                    except Exception:
                        pass
                    self.show_error("رمز التحقق غير صحيح")
                    return

            # حفظ بيانات الدخول إذا كان المستخدم يريد ذلك
            if self.remember_checkbox.isChecked():
                self.save_credentials()
            
            # إرسال إشارة نجاح تسجيل الدخول
            self.login_successful.emit(session)
            
            # إغلاق النافذة
            self.accept()
        else:
            # عرض رسالة الخطأ
            self.show_error(message or "فشل في تسجيل الدخول")
            self.password_edit.clear()
            self.password_edit.setFocus()
    
    def handle_forgot_password(self):
        """معالجة نسيان كلمة المرور"""
        # Use the ForgotPasswordDialog defined at the bottom of this file
        dialog = ForgotPasswordDialog(self.user_service, self)
        if dialog.exec() == QDialog.Accepted:
            self.show_info("تم إرسال كلمة المرور الجديدة. يرجى التحقق من الإدارة.")
    
    def set_ui_enabled(self, enabled: bool):
        """تفعيل/تعطيل عناصر الواجهة"""
        self.username_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.forgot_password_button.setEnabled(enabled)
    
    def show_error(self, message: str):
        """عرض رسالة خطأ"""
        QMessageBox.critical(self, "خطأ", message)
    
    def show_info(self, message: str):
        """عرض رسالة معلومات"""
        QMessageBox.information(self, "معلومات", message)
    
    def save_credentials(self):
        """حفظ بيانات الدخول"""
        try:
            # يمكن حفظ اسم المستخدم فقط في ملف إعدادات
            # لأسباب أمنية، لا نحفظ كلمة المرور
            import json
            import os
            
            config_dir = os.path.join(os.path.expanduser("~"), ".logical_release")
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, "login_config.json")
            config = {
                "last_username": self.username_edit.text(),
                "remember_username": True
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            # تجاهل أخطاء الحفظ
            pass
    
    def load_saved_credentials(self):
        """تحميل بيانات الدخول المحفوظة"""
        try:
            import json
            import os
            
            config_file = os.path.join(os.path.expanduser("~"), ".logical_release", "login_config.json")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if config.get("remember_username") and config.get("last_username"):
                    self.username_edit.setText(config["last_username"])
                    self.remember_checkbox.setChecked(True)
                    self.password_edit.setFocus()
                    
        except Exception as e:
            # تجاهل أخطاء التحميل
            pass
    
    def get_current_session(self) -> Optional[UserSession]:
        """الحصول على الجلسة الحالية"""
        return self.current_session
    
    def set_warning_message(self, message: str):
        """تعيين رسالة التحذير"""
        self.warning_label.setText(message)
        self.warning_label.setVisible(True)
    
    def hide_warning_message(self):
        """إخفاء رسالة التحذير"""
        self.warning_label.setVisible(False)
    
    def closeEvent(self, event):
        """معالجة إغلاق النافذة"""
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()
        
        super().closeEvent(event)


# نافذة نسيان كلمة المرور
class ForgotPasswordDialog(QDialog):
    """نافذة نسيان كلمة المرور"""
    
    def __init__(self, user_service: UserService, parent=None):
        super().__init__(parent)
        self.user_service = user_service
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle("استعادة كلمة المرور")
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # تعليمات
        info_label = QLabel("أدخل اسم المستخدم لاستعادة كلمة المرور:")
        layout.addWidget(info_label)
        
        # حقل اسم المستخدم
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("اسم المستخدم")
        self.username_edit.setMinimumHeight(35)
        layout.addWidget(self.username_edit)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("استعادة كلمة المرور")
        self.reset_button.setMinimumHeight(35)
        buttons_layout.addWidget(self.reset_button)
        
        self.cancel_button = QPushButton("إلغاء")
        self.cancel_button.setMinimumHeight(35)
        buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.reset_button.clicked.connect(self.handle_reset)
        self.cancel_button.clicked.connect(self.reject)
        self.username_edit.returnPressed.connect(self.handle_reset)
    
    def handle_reset(self):
        """معالجة استعادة كلمة المرور"""
        username = self.username_edit.text().strip()
        
        if not username:
            QMessageBox.warning(self, "تحذير", "يرجى إدخال اسم المستخدم")
            return
        
        try:
            success, message, temp_password = self.user_service.reset_password(username)
            
            if success:
                QMessageBox.information(
                    self, 
                    "تم بنجاح", 
                    f"تم إنشاء كلمة مرور مؤقتة: {temp_password}\n\nيرجى تغيير كلمة المرور بعد تسجيل الدخول."
                )
                self.accept()
            else:
                QMessageBox.critical(self, "خطأ", message or "فشل في استعادة كلمة المرور")
                
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ في النظام: {str(e)}")


# اختبار النافذة
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # إعداد الخط العربي
    font = QFont("Arial", 10)
    app.setFont(font)
    
    # إعداد اتجاه النص
    app.setLayoutDirection(Qt.RightToLeft)
    
    # إنشاء قاعدة بيانات وهمية للاختبار
    from ...core.database_manager import DatabaseManager
    
    db = DatabaseManager(":memory:")
    
    dialog = LoginDialog(db)
    
    if dialog.exec() == QDialog.Accepted:
        session = dialog.get_current_session()
        print(f"تم تسجيل الدخول بنجاح: {session.username}")
    else:
        print("تم إلغاء تسجيل الدخول")
    
    sys.exit()
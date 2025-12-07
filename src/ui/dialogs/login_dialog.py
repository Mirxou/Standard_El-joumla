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
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QPropertyAnimation, QEasingCurve, QRect, Property, QEvent
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPainter, QBrush, QLinearGradient, QShowEvent

from ...services.user_service import UserService, UserSession
from ...services.security_service import SecurityService
from pathlib import Path
from ...utils.i18n_api import I18n


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
        
        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
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
        
        # إصلاح التخطيط عند أول تحميل
        QTimer.singleShot(0, self._fix_layout)
        QTimer.singleShot(10, self._ensure_proper_display)
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الاحترافية العالمية"""
        self.setWindowTitle(self.i18n.get_message("login_title"))
        self.setMinimumSize(500, 650)
        self.setMaximumSize(500, 650)
        self.resize(500, 650)
        self.setModal(True)
        
        # تطبيق CSS احترافي شامل
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #ffffff);
            }
        """)
        
        # تخطيط رئيسي
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # رأس احترافي بتدرج متقدم
        header_frame = QFrame()
        header_frame.setFixedHeight(200)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 30, 30, 30)
        header_layout.setSpacing(12)
        
        # أيقونة احترافية مع تأثير
        logo_label = QLabel("💼")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                font-size: 64px;
                background: transparent;
                padding: 10px;
            }
        """)
        header_layout.addWidget(logo_label)
        
        # عنوان احترافي
        title_label = QLabel(self.i18n.get_message("app_name_short"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
            font-weight: bold;
                color: white;
                background: transparent;
                letter-spacing: 1px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # وصف احترافي
        subtitle_label = QLabel(self.i18n.get_message("app_description"))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: rgba(255, 255, 255, 0.95);
                background: transparent;
                font-weight: 500;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addWidget(header_frame)
        
        # محتوى النموذج مع خلفية بيضاء
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            QWidget#contentWidget {
                background-color: white;
                min-height: 400px;
            }
        """)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(40, 35, 40, 30)
        content_layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)
        
        # رسالة التحذير
        content_layout.addWidget(self.warning_label)
        
        # منطقة النموذج
        self.setup_form(content_layout)
        
        # منطقة الأزرار
        self.setup_buttons(content_layout)
        
        # شريط التقدم الاحترافي
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #e9ecef;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
            }
        """)
        content_layout.addWidget(self.progress_bar)
        
        main_layout.addWidget(content_widget)
        
        # تذييل احترافي
        footer_frame = QFrame()
        footer_frame.setFixedHeight(45)
        footer_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border-top: 1px solid #dee2e6;
            }
        """)
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 10, 20, 10)
        
        version_label = QLabel(self.i18n.get_message("app_version_copyright"))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 10px;
                background: transparent;
                font-weight: 500;
            }
        """)
        footer_layout.addWidget(version_label)
        
        main_layout.addWidget(footer_frame)
    
    
    def setup_form(self, layout: QVBoxLayout):
        """إعداد نموذج تسجيل الدخول الاحترافي العالمي"""
        # حقل اسم المستخدم مع تصميم احترافي
        username_container = QFrame()
        username_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        username_container_layout = QVBoxLayout(username_container)
        username_container_layout.setContentsMargins(0, 0, 0, 0)
        username_container_layout.setSpacing(8)
        
        username_label = QLabel(self.i18n.get_message("username_label"))
        username_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 2px;
            }
        """)
        username_container_layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText(self.i18n.get_message("enter_username"))
        self.username_edit.setMinimumHeight(52)
        self.username_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                background-color: #f8f9fa;
                selection-background-color: #667eea;
                selection-color: white;
            }
            QLineEdit:hover {
                border-color: #cbd5e0;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: #ffffff;
            }
        """)
        username_container_layout.addWidget(self.username_edit)
        layout.addWidget(username_container)
        
        # حقل كلمة المرور مع تصميم احترافي
        password_container = QFrame()
        password_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        password_container_layout = QVBoxLayout(password_container)
        password_container_layout.setContentsMargins(0, 0, 0, 0)
        password_container_layout.setSpacing(8)
        
        password_label = QLabel(self.i18n.get_message("password_label"))
        password_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 2px;
            }
        """)
        password_container_layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.i18n.get_message("enter_password"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(52)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                background-color: #f8f9fa;
                selection-background-color: #667eea;
                selection-color: white;
            }
            QLineEdit:hover {
                border-color: #cbd5e0;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background-color: #ffffff;
            }
        """)
        password_container_layout.addWidget(self.password_edit)
        layout.addWidget(password_container)
        
        # خيار تذكر بيانات الدخول احترافي
        remember_container = QHBoxLayout()
        remember_container.setContentsMargins(2, 8, 2, 0)
        
        self.remember_checkbox = QCheckBox("تذكر بيانات الدخول")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: #495057;
                font-size: 13px;
                spacing: 10px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #cbd5e0;
                border-radius: 5px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #667eea;
            }
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
                border-color: #667eea;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxNiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEgNkw2IDExTDE1IDIiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMi41IiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
        """)
        remember_container.addWidget(self.remember_checkbox)
        remember_container.addStretch()
        layout.addLayout(remember_container)
    
    def setup_buttons(self, layout: QVBoxLayout):
        """إعداد الأزرار الاحترافية العالمية"""
        # زر تسجيل الدخول الرئيسي بتدرج احترافي
        self.login_button = QPushButton(self.i18n.get_message("login_button"))
        self.login_button.setMinimumHeight(56)
        self.login_button.setDefault(True)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                color: white;
                border: none;
                border-radius: 14px;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5568d3, stop:1 #6a3f8f);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4a5bc0, stop:1 #5d357c);
            }
            QPushButton:disabled {
                background-color: #dee2e6;
                color: #adb5bd;
            }
        """)
        layout.addWidget(self.login_button)
        
        # زر الإلغاء احترافي
        self.cancel_button = QPushButton(self.i18n.get_message("cancel"))
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #495057;
                border: 2px solid #e1e8ed;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #cbd5e0;
                color: #212529;
            }
            QPushButton:pressed {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
        """)
        layout.addWidget(self.cancel_button)
        
        # رابط نسيان كلمة المرور احترافي
        self.forgot_password_button = QPushButton(self.i18n.get_message("forgot_password"))
        self.forgot_password_button.setCursor(Qt.PointingHandCursor)
        self.forgot_password_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #667eea;
                font-size: 13px;
                background: transparent;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #764ba2;
                text-decoration: underline;
            }
        """)
        layout.addWidget(self.forgot_password_button, alignment=Qt.AlignCenter)
    
    def setup_connections(self):
        """إعداد الاتصالات"""
        self.login_button.clicked.connect(self.handle_login)
        self.cancel_button.clicked.connect(self.reject)
        self.forgot_password_button.clicked.connect(self.handle_forgot_password)
        
        # تسجيل الدخول بالضغط على Enter
        self.username_edit.returnPressed.connect(self.handle_login)
        self.password_edit.returnPressed.connect(self.handle_login)
    
    def setup_styles(self):
        """إعداد الأنماط الاحترافية العالمية"""
        # تم تطبيق الأنماط مباشرة في setup_ui
        pass
    
    def showEvent(self, event: QShowEvent):
        """معالجة حدث العرض لضمان التخطيط الصحيح"""
        super().showEvent(event)
        # إصلاح التخطيط عند العرض
        QTimer.singleShot(0, self._fix_layout_on_show)
    
    def _fix_layout_on_show(self):
        """إصلاح التخطيط عند العرض"""
        try:
            # ضمان الحجم الصحيح
            self.setFixedSize(500, 650)
            # تحديث التخطيط
            self.updateGeometry()
            if self.layout():
                self.layout().update()
            # تحديث جميع العناصر الفرعية
            for widget in self.findChildren(QWidget):
                widget.updateGeometry()
                widget.update()
            # إعادة الرسم
            self.repaint()
            QApplication.processEvents()
        except Exception as e:
            print(f"خطأ في إصلاح التخطيط: {e}")
    
    def _fix_layout(self):
        """إصلاح التخطيط عند أول تحميل"""
        try:
            self.setFixedSize(500, 650)
            self.updateGeometry()
            self.update()
            QApplication.processEvents()
        except Exception:
            pass
    
    def _ensure_proper_display(self):
        """ضمان العرض الصحيح"""
        try:
            # تحديث جميع العناصر
            self.setFixedSize(500, 650)
            self.updateGeometry()
            self.repaint()
            QApplication.processEvents()
        except Exception:
            pass
    
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
        """معالجة اكتمال تسجيل الدخول (محسّنة)"""
        # إعادة تفعيل الواجهة فوراً
        self.progress_bar.setVisible(False)
        QApplication.processEvents()
        
        if success and session:
            self.set_ui_enabled(False)  # منع التفاعل أثناء المعالجة
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
                QTimer.singleShot(0, self.save_credentials)
            
            # إرسال إشارة نجاح تسجيل الدخول
            self.current_session = session
            self.login_successful.emit(session)
            
            # إغلاق النافذة
            QTimer.singleShot(50, self.accept)
        else:
            # إعادة تفعيل الواجهة
            self.set_ui_enabled(True)
            
            # عرض رسالة الخطأ
            QTimer.singleShot(0, lambda: self.show_error(message or "فشل في تسجيل الدخول"))
            self.password_edit.clear()
            QTimer.singleShot(100, lambda: self.password_edit.setFocus())
    
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
        QMessageBox.critical(self, self.i18n.get_message("error"), message)
    
    def show_info(self, message: str):
        """عرض رسالة معلومات"""
        QMessageBox.information(self, self.i18n.get_message("info"), message)
    
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
        
        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """إعداد واجهة المستخدم"""
        self.setWindowTitle(self.i18n.get_message("forgot_password_title"))
        self.setFixedSize(350, 200)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # تعليمات
        info_label = QLabel(self.i18n.get_message("forgot_password_info"))
        layout.addWidget(info_label)
        
        # حقل اسم المستخدم
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText(self.i18n.get_message("username_placeholder"))
        self.username_edit.setMinimumHeight(35)
        layout.addWidget(self.username_edit)
        
        # الأزرار
        buttons_layout = QHBoxLayout()
        
        self.reset_button = QPushButton(self.i18n.get_message("reset_password"))
        self.reset_button.setMinimumHeight(35)
        buttons_layout.addWidget(self.reset_button)
        
        self.cancel_button = QPushButton(self.i18n.get_message("cancel"))
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
            QMessageBox.warning(self, self.i18n.get_message("warning"), self.i18n.get_message("username_required"))
            return
        
        try:
            success, message, temp_password = self.user_service.reset_password(username)
            
            if success:
                QMessageBox.information(
                    self, 
                    self.i18n.get_message("success"), 
                    f"{self.i18n.get_message('password_reset_success', temp_password=temp_password)}"
                )
                self.accept()
            else:
                QMessageBox.critical(self, self.i18n.get_message("error"), message or self.i18n.get_message("password_reset_failed"))
                
        except Exception as e:
            QMessageBox.critical(self, self.i18n.get_message("error"), f"{self.i18n.get_message('system_error_occurred_msg')}: {str(e)}")


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
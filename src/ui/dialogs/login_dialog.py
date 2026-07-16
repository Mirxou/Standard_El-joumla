import logging
#!/usr/bin/env python3
"""
نافذة تسجيل الدخول - Login Dialog
واجهة تسجيل الدخول للنظام مع دعم اللغة العربية
"""

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QShowEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.widgets.base_dialog import BaseDialog

from ...services.security_service import SecurityService
from ...services.user_service import UserService, UserSession
from ...ui.animations.animation_manager import AnimationManager
from ...ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from ...ui.widgets.quantum_notification import NotificationManager
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
                user_agent="Standard El Joumla Desktop App",
            )
            self.login_completed.emit(success, session, message or "")
        except Exception as e:
            self.login_completed.emit(False, None, f"خطأ في النظام: {str(e)}")


class LoginDialog(BaseDialog):
    """نافذة تسجيل الدخول"""

    # إشارات مخصصة
    login_successful = Signal(object)  # UserSession

    def __init__(self, user_service: UserService, parent=None):
        # If a non-widget object is passed as parent (as some tests do using Mock),
        # gracefully ignore it by not passing it to the QWidget base constructor.
        from PySide6.QtWidgets import QWidget

        if parent is not None and not isinstance(parent, QWidget):
            parent = None
        super().__init__(title="", parent=parent)
        self.user_service = user_service
        self.current_session: Optional[UserSession] = None
        self.login_worker: Optional[LoginWorker] = None
        self.security_service = SecurityService(user_service.db)  # 2FA & brute-force support

        # تهيئة نظام الترجمة
        self.i18n = I18n(locales_dir=str(Path(__file__).parent.parent.parent.parent / "locales"))

        # تهيئة Animation Manager
        self.animation_manager = AnimationManager(self)

        # رسالة التحذير (مخفية افتراضياً) - يجب إنشاؤها قبل setup_ui
        self.warning_label = QLabel()
        self.warning_label.setVisible(False)
        self.warning_label.setStyleSheet("""
            QLabel {
                color: #ef4444;
                background-color: #fdf2f2;
                border: 1px solid #ef4444;
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

        # إعداد Opacity للـ fade in
        self.setWindowOpacity(0.0)

        # Notifications
        self.notify = NotificationManager(self)

    def setup_ui(self):
        """إعداد واجهة المستخدم الاحترافية العالمية"""
        self.setWindowTitle(self.i18n.get_message("login_title"))
        self.setMinimumSize(450, 650)  # Responsive minimum
        self.setModal(True)

        # تطبيق CSS احترافي شامل - Quantum Theme
        self.setStyleSheet("""
            QDialog {
                background-color: #0f172a; /* Deep Void */
                color: #e2e8f0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
        """)

        # --- Quantum Window Setup ---
        layout = self.content_layout
        layout.setSizeConstraint(QVBoxLayout.SetMinimumSize)

        # رسالة التحذير
        layout.addWidget(self.warning_label)

        # منطقة الشعار
        logo_container = QFrame()
        logo_container.setStyleSheet("background: transparent; border: none; margin-bottom: 20px;")
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setAlignment(Qt.AlignCenter)

        self.logo_label = QLabel()
        logo_path = Path(__file__).parent.parent.parent.parent / "assets" / "images" / "standard_eljoumla_logo.png"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText("🛒")
            self.logo_label.setStyleSheet("font-size: 64px; color: #06b6d4;")

        logo_layout.addWidget(self.logo_label)

        title_label = QLabel(self.i18n.get_message("app_name_short"))
        title_label.setStyleSheet("color: #f8fafc; font-size: 24px; font-weight: 800; background: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(title_label)

        subtitle_label = QLabel(self.i18n.get_message("app_description"))
        subtitle_label.setStyleSheet("color: #94a3b8; font-size: 14px; background: transparent;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(subtitle_label)

        layout.addWidget(logo_container)

        # منطقة النموذج
        self.setup_form(layout)

        # منطقة الأزرار
        self.setup_buttons(layout)

        # شريط التقدم الاحترافي
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #1e293b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #3b82f6);
                border-radius: 10px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # تذييل احترافي
        footer_frame = QFrame()
        footer_frame.setFixedHeight(45)
        footer_frame.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border: none;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        footer_layout = QVBoxLayout(footer_frame)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        version_label = QLabel(self.i18n.get_message("app_version_copyright"))
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #475569;
                font-size: 10px;
                background: transparent;
                font-weight: 500;
            }
        """)
        footer_layout.addWidget(version_label)

        self._internal_layout.addWidget(footer_frame)

    def setup_form(self, layout: QVBoxLayout):
        """إعداد نموذج تسجيل الدخول الاحترافي العالمي"""
        # حقل اسم المستخدم مع تصميم احترافي
        username_container = QFrame()
        username_container.setStyleSheet("background: transparent; border: none;")
        username_container_layout = QVBoxLayout(username_container)
        username_container_layout.setContentsMargins(0, 0, 0, 0)
        username_container_layout.setSpacing(8)

        username_label = QLabel(self.i18n.get_message("username_label"))
        username_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
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
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                background-color: #1e293b;
                color: #06b6d4;
                selection-background-color: #06b6d4;
                selection-color: black;
            }
            QLineEdit:hover {
                border: 1px solid #475569;
                background-color: #1e293b;
            }
            QLineEdit:focus {
                border: 1px solid #06b6d4;
                background-color: #0f172a;
            }
        """)
        username_container_layout.addWidget(self.username_edit)
        layout.addWidget(username_container)

        # حقل كلمة المرور مع تصميم احترافي
        password_container = QFrame()
        password_container.setStyleSheet("background: transparent; border: none;")
        password_container_layout = QVBoxLayout(password_container)
        password_container_layout.setContentsMargins(0, 0, 0, 0)
        password_container_layout.setSpacing(8)

        password_label = QLabel(self.i18n.get_message("password_label"))
        password_label.setStyleSheet("""
            QLabel {
                color: #cbd5e1;
                font-size: 13px;
                font-weight: 600;
                background: transparent;
                padding-left: 2px;
            }
        """)
        password_container_layout.addWidget(password_label)

        # صف يضم حقل كلمة المرور + زر الإظهار
        password_row = QHBoxLayout()
        password_row.setContentsMargins(0, 0, 0, 0)
        password_row.setSpacing(0)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.i18n.get_message("enter_password"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(52)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #334155;
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
                border-top-left-radius: 0px;
                border-bottom-left-radius: 0px;
                border-left: none;
                padding: 14px 18px;
                font-size: 15px;
                background-color: #1e293b;
                color: #06b6d4;
                selection-background-color: #06b6d4;
                selection-color: black;
            }
            QLineEdit:hover {
                border: 1px solid #475569;
                border-left: none;
                background-color: #1e293b;
            }
            QLineEdit:focus {
                border: 1px solid #06b6d4;
                border-left: none;
                background-color: #0f172a;
            }
        """)
        password_row.addWidget(self.password_edit)

        # زر إظهار/إخفاء كلمة المرور
        self.show_password_btn = QPushButton("👁")
        self.show_password_btn.setFixedSize(52, 52)
        self.show_password_btn.setCursor(Qt.PointingHandCursor)
        self.show_password_btn.setCheckable(True)
        self.show_password_btn.setToolTip("إظهار/إخفاء كلمة المرور")
        self.show_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-top-left-radius: 12px;
                border-bottom-left-radius: 12px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                font-size: 18px;
                border-right: none;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #06b6d4;
                border-color: #475569;
            }
            QPushButton:checked {
                color: #06b6d4;
                background-color: #1e293b;
            }
        """)
        self.show_password_btn.clicked.connect(self.toggle_password_visibility)
        password_row.addWidget(self.show_password_btn)

        password_container_layout.addLayout(password_row)
        layout.addWidget(password_container)

        # خيار تذكر بيانات الدخول احترافي
        remember_container = QHBoxLayout()
        remember_container.setContentsMargins(2, 8, 2, 0)

        self.remember_checkbox = QCheckBox("تذكر بيانات الدخول")
        self.remember_checkbox.setStyleSheet("""
            QCheckBox {
                color: #94a3b8;
                font-size: 13px;
                spacing: 10px;
                background: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 1px solid #475569;
                border-radius: 5px;
                background-color: #1e293b;
            }
            QCheckBox::indicator:hover {
                border-color: #06b6d4;
            }
            QCheckBox::indicator:checked {
                background-color: #06b6d4;
                border-color: #06b6d4;
                /* Checkmark logic needed or use helper image */
            }
        """)
        remember_container.addWidget(self.remember_checkbox)
        remember_container.addStretch()
        layout.addLayout(remember_container)

    def setup_buttons(self, layout: QVBoxLayout):
        """إعداد الأزرار الاحترافية العالمية"""
        # زر تسجيل الدخول الرئيسي بتدرج احترافي
        self.login_button = QPushButton(self.i18n.get_message("login_button", default="تسجيل الدخول"))
        self.login_button.setMinimumHeight(56)
        self.login_button.setDefault(True)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #06b6d4, stop:1 #2563eb);
                color: white;
                border: none;
                border-radius: 14px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5eead4, stop:1 #3b82f6);
            }
            QPushButton:pressed {
                background: #06b6d4;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #cbd5e1;
            }
        """)
        layout.addWidget(self.login_button)

        # زر الإلغاء احترافي
        self.cancel_button = QPushButton(self.i18n.get_message("cancel", default="إلغاء"))
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #cbd5e1;
                color: #e2e8f0;
            }
            QPushButton:pressed {
                background-color: #1e293b;
            }
        """)
        layout.addWidget(self.cancel_button)

        # رابط نسيان كلمة المرور احترافي
        self.forgot_password_button = QPushButton(self.i18n.get_message("forgot_password"))
        self.forgot_password_button.setCursor(Qt.PointingHandCursor)
        self.forgot_password_button.setStyleSheet("""
            QPushButton {
                border: none;
                color: #38bdf8;
                font-size: 13px;
                background: transparent;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                color: #06b6d4;
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

    def showEvent(self, event: QShowEvent):
        """معالجة حدث العرض لضمان التخطيط الصحيح"""
        super().showEvent(event)
        # إصلاح التخطيط عند العرض
        QTimer.singleShot(0, self._fix_layout_on_show)
        # تطبيق fade in animation
        QTimer.singleShot(50, lambda: self.animation_manager.fade_in(self, duration=300))

    def toggle_password_visibility(self, checked: bool):
        """تبديل إظهار/إخفاء كلمة المرور"""
        if checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
            self.show_password_btn.setText("🔒")
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)
            self.show_password_btn.setText("👁")

    def _fix_layout_on_show(self):
        """إصلاح التخطيط عند العرض"""
        try:
            self.updateGeometry()
            if self.layout():
                self.layout().update()
            for widget in self.findChildren(QWidget):
                widget.updateGeometry()
                widget.update()
            self.repaint()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def _fix_layout(self):
        """إصلاح التخطيط عند أول تحميل"""
        try:
            self.updateGeometry()
            self.update()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def _ensure_proper_display(self):
        """ضمان العرض الصحيح"""
        try:
            self.updateGeometry()
            self.repaint()
            QApplication.processEvents()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

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
        QApplication.processEvents()

        # تنفيذ عملية تسجيل الدخول مباشرة على الخيط الرئيسي لمنع مشاكل SQLite والتعليق في خيط منفصل
        try:
            success, session, message = self.user_service.authenticate_user(
                username,
                password,
                ip_address="127.0.0.1",
                user_agent="Standard El Joumla Desktop App",
            )
            self.on_login_completed(success, session, message or "")
        except Exception as e:
            self.on_login_completed(False, None, f"خطأ في النظام: {str(e)}")


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
                    "SELECT 1 FROM user_2fa WHERE user_id = ?", (session.user_id,)
                )
                needs_2fa = bool(rows)
            except Exception:
                needs_2fa = False

            if needs_2fa:
                from PySide6.QtWidgets import QInputDialog

                code, ok = QInputDialog.getText(
                    self,
                    self.i18n.get_message("two_factor_title", default="التحقق بخطوتين"),
                    self.i18n.get_message("two_factor_prompt", default="أدخل رمز التحقق (TOTP):"),
                )
                if not ok or not code:
                    # إنهاء الجلسة التي تم إنشاؤها مؤقتاً
                    try:
                        self.user_service._terminate_session(session.session_id, "إلغاء التحقق الثنائي")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")
                    self.show_error("تم إلغاء التحقق الثنائي")
                    return
                # تحقق من الرمز
                if not self.security_service.verify_2fa(session.user_id, code):
                    try:
                        self.security_service.record_login_attempt(
                            session.username,
                            False,
                            session.ip_address,
                            session.user_agent,
                        )
                        self.user_service._terminate_session(session.session_id, "فشل التحقق الثنائي")
                    except Exception:
                        logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")
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

            # عرض رسالة الخطأ مباشرة (لتوافق اختبارات الوحدة والهدوء في headless)
            self.show_error(message or "فشل في تسجيل الدخول")
            self.password_edit.clear()
            QTimer.singleShot(100, lambda: self.password_edit.setFocus())

    def handle_forgot_password(self):
        """معالجة نسيان كلمة المرور"""
        # Use the external Quantum ForgotPasswordDialog
        # Note: The external dialog handles its own notifications and logic
        dialog = ForgotPasswordDialog(self.user_service, self)
        dialog.exec()

    def set_ui_enabled(self, enabled: bool):
        """تفعيل/تعطيل عناصر الواجهة"""
        self.username_edit.setEnabled(enabled)
        self.password_edit.setEnabled(enabled)
        self.show_password_btn.setEnabled(enabled)
        self.remember_checkbox.setEnabled(enabled)
        self.login_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.forgot_password_button.setEnabled(enabled)

    def show_error(self, message: str):
        """عرض رسالة خطأ"""
        self.notify.show_error(self.i18n.get_message("error"), message)

    def show_info(self, message: str):
        """عرض رسالة معلومات"""
        self.notify.show_info(self.i18n.get_message("info"), message)

    def save_credentials(self):
        """حفظ بيانات الدخول"""
        try:
            # يمكن حفظ اسم المستخدم فقط في ملف إعدادات
            # لأسباب أمنية، لا نحفظ كلمة المرور
            import json
            import os

            config_dir = os.path.join(os.path.expanduser("~"), ".standard_eljoumla")
            os.makedirs(config_dir, exist_ok=True)

            config_file = os.path.join(config_dir, "login_config.json")
            config = {
                "last_username": self.username_edit.text(),
                "remember_username": True,
            }

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

        except Exception:
            # تجاهل أخطاء الحفظ
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

    def load_saved_credentials(self):
        """تحميل بيانات الدخول المحفوظة"""
        try:
            import json
            import os

            config_file = os.path.join(os.path.expanduser("~"), ".standard_eljoumla", "login_config.json")

            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if config.get("remember_username") and config.get("last_username"):
                    self.username_edit.setText(config["last_username"])
                    self.remember_checkbox.setChecked(True)
                    self.password_edit.setFocus()

        except Exception:
            # تجاهل أخطاء التحميل
            logging.getLogger(__name__).warning("Ignored exception in login_dialog.py")

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
        """معالجة إغلاق النافذة مع fade out animation"""
        # إذا كنا بالفعل في عملية الإغلاق، دع الحدث يمر
        if getattr(self, "_is_closing", False):
            event.accept()
            return

        # إلغاء أي عمليات جارية
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()

        # تطبيق fade out animation
        if hasattr(self, "animation_manager"):
            # منع الإغلاق الفوري
            event.ignore()

            # تعيين علامة الإغلاق وتشغيل الأنيميشن
            self._is_closing = True
            self.animation_manager.fade_out(self, duration=200)

            # استدعاء الإغلاق النهائي لاحقاً
            QTimer.singleShot(250, self._finalize_close)
        else:
            event.accept()

    def _finalize_close(self):
        """إتمام إغلاق النافذة بعد انتهاء animation"""
        # استدعاء close() مرة أخرى، وهذه المرة سيمر عبر التحقق من _is_closing
        self.close()


# نافذة نسيان كلمة المرور

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
        pass  # Login successful
    else:
        pass  # Login cancelled

    sys.exit()

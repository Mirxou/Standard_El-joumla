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
from ...ui.widgets.quantum_notification import NotificationManager
from ...ui.dialogs.forgot_password_dialog import ForgotPasswordDialog
from ...utils.i18n_api import I18n
from ...ui.animations.animation_manager import AnimationManager


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
        # If a non-widget object is passed as parent (as some tests do using Mock),
        # gracefully ignore it by not passing it to the QWidget base constructor.
        from PySide6.QtWidgets import QWidget
        if parent is not None and not isinstance(parent, QWidget):
            parent = None
        super().__init__(parent)
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
        
        # إعداد Opacity للـ fade in
        self.setWindowOpacity(0.0)

        # Notifications
        self.notify = NotificationManager(self)
    
    def setup_ui(self):
        """إعداد واجهة المستخدم الاحترافية العالمية"""
        self.setWindowTitle(self.i18n.get_message("login_title"))
        self.setMinimumSize(500, 650)
        self.setMaximumSize(500, 650)
        self.resize(500, 650)
        self.setModal(True)
        
        # تطبيق CSS احترافي شامل - Quantum Theme
        self.setStyleSheet("""
            QDialog {
                background-color: #020617; /* Deep Void */
                color: #e2e8f0;
            }
        """)
        
        
        # --- Quantum Window Setup ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # تخطيط جذري شفاف
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(10, 10, 10, 10) # For shadow
        root_layout.setSpacing(0)
        
        # الإطار الرئيسي (The Window Border)
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet("""
            QFrame {
                background-color: #020617; /* Deep Void */
                border: 1px solid #00f3ff; /* Neon Cyan Border */
                border-radius: 10px;
            }
        """)
        # إضافة ظل للإطار الرئيسي
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor("#00f3ff"))
        shadow.setOffset(0, 0)
        self.main_frame.setGraphicsEffect(shadow)
        
        root_layout.addWidget(self.main_frame)
        
        # تخطيظ الإطار
        window_layout = QVBoxLayout(self.main_frame)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        
        # 1. شريط العنوان المخصص
        from ...ui.widgets.custom_title_bar import CustomTitleBar
        self.title_bar = CustomTitleBar(self, title=self.i18n.get_message("login_title"), is_dialog=True)
        try:
            window_layout.addWidget(self.title_bar)
        except TypeError:
            # In test environments the CustomTitleBar may be patched to a non-QWidget object
            pass
        
        # 2. رأس احترافي بتدرج متقدم (بدون border-top لأنه تحت الTitleBar)
        header_frame = QFrame()
        header_frame.setFixedHeight(180) # Reduced height since we have titlebar
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f172a, stop:1 #020617);
                border: none;
                border-bottom: 1px solid rgba(0, 243, 255, 0.1);
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(30, 20, 30, 30)
        header_layout.setSpacing(10)
        
        # أيقونة احترافية
        logo_label = QLabel("⚛️")
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
                color: #00f3ff; /* Neon Cyan */
                background: transparent;
                letter-spacing: 2px;
                text-transform: uppercase;
            }
        """)
        header_layout.addWidget(title_label)
        
        # وصف احترافي
        subtitle_label = QLabel(self.i18n.get_message("app_description"))
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #94a3b8;
                background: transparent;
                font-weight: 500;
            }
        """)
        header_layout.addWidget(subtitle_label)
        
        window_layout.addWidget(header_frame)
        
        # محتوى النموذج مع خلفية داكنة
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_widget.setStyleSheet("""
            QWidget#contentWidget {
                background-color: #020617;
                min-height: 400px;
                border: none;
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
                background-color: #1e293b;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00f3ff, stop:1 #3b82f6);
                border-radius: 10px;
            }
        """)
        content_layout.addWidget(self.progress_bar)
        
        window_layout.addWidget(content_widget)
        
        # تذييل احترافي
        footer_frame = QFrame()
        footer_frame.setFixedHeight(45)
        footer_frame.setStyleSheet("""
            QFrame {
                background: #020617;
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
        
        window_layout.addWidget(footer_frame)
    
    
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
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                background-color: rgba(30, 41, 59, 0.5);
                color: #00f3ff;
                selection-background-color: #00f3ff;
                selection-color: black;
            }
            QLineEdit:hover {
                border: 1px solid rgba(148, 163, 184, 0.4);
                background-color: rgba(30, 41, 59, 0.7);
            }
            QLineEdit:focus {
                border: 1px solid #00f3ff;
                background-color: rgba(15, 23, 42, 0.9);
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
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText(self.i18n.get_message("enter_password"))
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(52)
        self.password_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid rgba(148, 163, 184, 0.2);
                border-radius: 12px;
                padding: 14px 18px;
                font-size: 15px;
                background-color: rgba(30, 41, 59, 0.5);
                color: #00f3ff;
                selection-background-color: #00f3ff;
                selection-color: black;
            }
            QLineEdit:hover {
                border: 1px solid rgba(148, 163, 184, 0.4);
                background-color: rgba(30, 41, 59, 0.7);
            }
            QLineEdit:focus {
                border: 1px solid #00f3ff;
                background-color: rgba(15, 23, 42, 0.9);
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
                background-color: rgba(30, 41, 59, 0.5);
            }
            QCheckBox::indicator:hover {
                border-color: #00f3ff;
            }
            QCheckBox::indicator:checked {
                background-color: #00f3ff;
                border-color: #00f3ff;
                /* Checkmark logic needed or use helper image */
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
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #00f3ff, stop:1 #2563eb);
                color: black;
                border: none;
                border-radius: 14px;
                padding: 15px;
                font-size: 16px;
                font-weight: 800;
                letter-spacing: 0.5px;
                text-transform: uppercase;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5eead4, stop:1 #3b82f6);
                border: 1px solid #00f3ff; /* Glow hint */
            }
            QPushButton:pressed {
                background: #00f3ff;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        layout.addWidget(self.login_button)
        
        # زر الإلغاء احترافي
        self.cancel_button = QPushButton(self.i18n.get_message("cancel"))
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
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
                color: #00f3ff;
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
        # تطبيق fade in animation
        QTimer.singleShot(50, lambda: self.animation_manager.fade_in(self, duration=300))
    
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
        """معالجة إغلاق النافذة مع fade out animation"""
        # إذا كنا بالفعل في عملية الإغلاق، دع الحدث يمر
        if getattr(self, '_is_closing', False):
            event.accept()
            return

        # إلغاء أي عمليات جارية
        if self.login_worker and self.login_worker.isRunning():
            self.login_worker.terminate()
            self.login_worker.wait()
        
        # تطبيق fade out animation
        if hasattr(self, 'animation_manager'):
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
        print(f"تم تسجيل الدخول بنجاح: {session.username}")
    else:
        print("تم إلغاء تسجيل الدخول")

    sys.exit()

#!/usr/bin/env python3
"""
Unit Tests for Login Dialog
اختبارات وحدة نافذة تسجيل الدخول
"""

from unittest.mock import Mock, patch

import pytest
from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton

from src.ui.dialogs.login_dialog import LoginDialog, LoginWorker

# استخدام تطبيق Qt موجود أو إنشاء واحد جديد
app = QApplication.instance() or QApplication([])


class TestLoginDialog:
    """اختبارات نافذة تسجيل الدخول"""

    @pytest.fixture
    def login_dialog(self):
        """إنشاء نافذة تسجيل دخول للاختبارات"""
        user_service = Mock()
        # محاكاة قاعدة البيانات في خدمة المستخدم
        user_service.db = Mock()

        with patch("src.ui.dialogs.login_dialog.I18n") as mock_i18n_cls, patch(
            "src.ui.dialogs.login_dialog.AnimationManager"
        ), patch("src.ui.dialogs.login_dialog.NotificationManager"), patch(
            "src.ui.dialogs.login_dialog.SecurityService"
        ), patch(
            "src.ui.widgets.custom_title_bar.CustomTitleBar"
        ):

            mock_i18n = mock_i18n_cls.return_value
            mock_i18n.get_message.return_value = "Test Message"

            dialog = LoginDialog(user_service)
            return dialog

    def test_initialization(self, login_dialog):
        """اختبار تهيئة النافذة"""
        assert login_dialog is not None
        assert isinstance(login_dialog.username_edit, QLineEdit)
        assert isinstance(login_dialog.password_edit, QLineEdit)
        assert isinstance(login_dialog.login_button, QPushButton)
        assert isinstance(login_dialog.remember_checkbox, QCheckBox)

    def test_ui_elements_exist(self, login_dialog):
        """التحقق من وجود عناصر واجهة المستخدم"""
        assert login_dialog.username_edit is not None
        assert login_dialog.password_edit is not None
        assert login_dialog.login_button is not None
        assert login_dialog.cancel_button is not None
        assert login_dialog.forgot_password_button is not None

    def test_password_echo_mode(self, login_dialog):
        """التحقق من وضع إخفاء كلمة المرور"""
        assert login_dialog.password_edit.echoMode() == QLineEdit.Password

    def test_set_ui_enabled(self, login_dialog):
        """اختبار تفعيل وتعطيل الواجهة"""
        login_dialog.set_ui_enabled(False)
        assert login_dialog.username_edit.isEnabled() is False
        assert login_dialog.login_button.isEnabled() is False

        login_dialog.set_ui_enabled(True)
        assert login_dialog.username_edit.isEnabled() is True
        assert login_dialog.login_button.isEnabled() is True

    def test_handle_login_empty_fields(self, login_dialog):
        """اختبار معالجة تسجيل الدخول بحقول فارغة"""
        with patch.object(login_dialog, "show_error") as mock_error:
            login_dialog.username_edit.setText("")
            login_dialog.handle_login()
            mock_error.assert_called_with("يرجى إدخال اسم المستخدم")

            login_dialog.username_edit.setText("admin")
            login_dialog.password_edit.setText("")
            login_dialog.handle_login()
            mock_error.assert_called_with("يرجى إدخال كلمة المرور")

    def test_on_login_completed_failure(self, login_dialog):
        """اختبار معالجة فشل تسجيل الدخول"""
        with patch.object(login_dialog, "show_error") as mock_error:
            login_dialog.on_login_completed(False, None, "Invalid credentials")
            mock_error.assert_called()
            assert login_dialog.username_edit.isEnabled() is True

    def test_get_current_session(self, login_dialog):
        """اختبار الحصول على الجلسة الحالية"""
        mock_session = Mock()
        login_dialog.current_session = mock_session
        assert login_dialog.get_current_session() == mock_session


class TestLoginWorker:
    """اختبارات عامل تسجيل الدخول"""

    def test_worker_initialization(self):
        """اختبار تهيئة العامل"""
        user_service = Mock()
        worker = LoginWorker(user_service, "user", "pass", True)
        assert worker.username == "user"
        assert worker.password == "pass"
        assert worker.remember_me is True

    def test_worker_run_success(self):
        """اختبار تشغيل العامل بنجاح"""
        user_service = Mock()
        mock_session = Mock()
        user_service.authenticate_user.return_value = (True, mock_session, "Success")

        worker = LoginWorker(user_service, "user", "pass", False)

        emitted_args = []
        worker.login_completed.connect(lambda s, sess, m: emitted_args.append((s, sess, m)))
        worker.run()
        assert len(emitted_args) == 1
        assert emitted_args[0] == (True, mock_session, "Success")

    def test_worker_run_exception(self):
        """اختبار تشغيل العامل مع حدوث خطأ"""
        user_service = Mock()
        user_service.authenticate_user.side_effect = Exception("Connection lost")

        worker = LoginWorker(user_service, "user", "pass", False)

        emitted_args = []
        worker.login_completed.connect(lambda s, sess, m: emitted_args.append((s, sess, m)))
        worker.run()
        assert len(emitted_args) == 1
        assert emitted_args[0][0] is False
        assert "خطأ في النظام" in emitted_args[0][2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

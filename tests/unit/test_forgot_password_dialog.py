#!/usr/bin/env python3
"""
اختبارات Forgot Password Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton
from PySide6.QtCore import Qt
from src.ui.dialogs.forgot_password_dialog import ForgotPasswordDialog

app = QApplication.instance() or QApplication([])


class TestForgotPasswordDialog:
    """اختبارات نافذة نسيت كلمة المرور"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        user_service = Mock()
        return ForgotPasswordDialog(user_service)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'email_input')
        assert hasattr(dialog, 'reset_button')
    
    def test_email_input_exists(self, dialog):
        """اختبار وجود حقل البريد"""
        assert dialog.email_input is not None
        assert isinstance(dialog.email_input, QLineEdit)
    
    def test_set_email(self, dialog):
        """اختبار تعيين البريد"""
        dialog.email_input.setText("user@example.com")
        assert dialog.email_input.text() == "user@example.com"
    
    def test_get_email(self, dialog):
        """اختبار الحصول على البريد"""
        dialog.email_input.setText("test@domain.com")
        assert dialog.get_email() == "test@domain.com"
    
    def test_reset_button_click(self, dialog):
        """اختبار النقر على زر إعادة التعيين"""
        dialog.email_input.setText("valid@email.com")
        result = dialog.on_reset_clicked()
        assert result is not None
    
    def test_validate_email_valid(self, dialog):
        """اختبار التحقق من بريد صحيح"""
        assert dialog.validate_email("user@example.com") is True
    
    def test_validate_email_invalid(self, dialog):
        """اختبار التحقق من بريد خاطئ"""
        assert dialog.validate_email("invalid-email") is False
    
    def test_show_success_message(self, dialog):
        """اختبار عرض رسالة النجاح"""
        result = dialog.show_success_message()
        assert result is not None
    
    def test_show_error_message(self, dialog):
        """اختبار عرض رسالة الخطأ"""
        result = dialog.show_error_message("Error occurred")
        assert result is not None
    
    def test_enable_inputs(self, dialog):
        """اختبار تمكين/تعطيل المدخلات"""
        dialog.enable_inputs(False)
        assert dialog.email_input.isEnabled() is False
        dialog.enable_inputs(True)
        assert dialog.email_input.isEnabled() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




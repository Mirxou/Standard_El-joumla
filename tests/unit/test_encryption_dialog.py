#!/usr/bin/env python3
"""
اختبارات Encryption Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QLineEdit, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from src.ui.dialogs.encryption_dialog import EncryptionDialog, EncryptionWorker

app = QApplication.instance() or QApplication([])


class TestEncryptionDialog:
    """اختبارات نافذة التشفير"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        db_manager = Mock()
        db_manager.is_encrypted = False
        with patch('src.ui.dialogs.encryption_dialog.NotificationManager'), \
             patch('src.ui.widgets.custom_title_bar.CustomTitleBar'):
            dialog = EncryptionDialog(db_manager)
            return dialog
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'enable_password_input')
        assert hasattr(dialog, 'disable_password_input')
        assert hasattr(dialog, 'old_password_input')
        assert isinstance(dialog.enable_password_input, QLineEdit)
        assert isinstance(dialog.backup_checkbox, QCheckBox)
    
    def test_update_encryption_status_disabled(self, dialog):
        """اختبار حالة التشفير عندما يكون معطلاً"""
        dialog.db_manager.is_encrypted = False
        dialog.update_encryption_status()
        assert dialog.enable_button.isEnabled() is True
        assert dialog.disable_button.isEnabled() is False
        assert dialog.change_password_button.isEnabled() is False
        assert dialog.encryption_status_label.text() == "غير مُفعّل"
        
    def test_update_encryption_status_enabled(self, dialog):
        """اختبار حالة التشفير عندما يكون مفعلاً"""
        dialog.db_manager.is_encrypted = True
        dialog.update_encryption_status()
        assert dialog.enable_button.isEnabled() is False
        assert dialog.disable_button.isEnabled() is True
        assert dialog.change_password_button.isEnabled() is True
        assert dialog.encryption_status_label.text() == "مُفعّل"
        
    def test_generate_password(self, dialog):
        """اختبار توليد كلمة المرور"""
        dialog.generate_password()
        generated = dialog.generated_password_display.text()
        assert len(generated) == 16
        assert dialog.copy_button.isEnabled() is True
        
    def test_clear_inputs(self, dialog):
        """اختبار تفريغ المدخلات"""
        dialog.enable_password_input.setText("test")
        dialog.disable_password_input.setText("test")
        dialog.old_password_input.setText("test")
        
        dialog.clear_inputs()
        
        assert dialog.enable_password_input.text() == ""
        assert dialog.disable_password_input.text() == ""
        assert dialog.old_password_input.text() == ""

class TestEncryptionWorker:
    """اختبارات عامل التشفير"""
    
    def test_worker_enable(self):
        """اختبار تفعيل التشفير"""
        db_manager = Mock()
        db_manager.enable_encryption.return_value = True
        worker = EncryptionWorker("enable", db_manager, password="test")
        
        completed_args = []
        worker.operation_completed.connect(lambda s, m: completed_args.append((s, m)))
        worker.run()
        
        assert len(completed_args) == 1
        assert completed_args[0][0] is True
        db_manager.enable_encryption.assert_called_once_with("test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

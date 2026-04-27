#!/usr/bin/env python3
"""
اختبارات Customer Form Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QTextEdit, QPushButton
from PySide6.QtCore import Qt
from src.ui.dialogs.customer_form_dialog import CustomerFormDialog

app = QApplication.instance() or QApplication([])


class TestCustomerFormDialog:
    """اختبارات نافذة نموذج العميل"""
    
    @pytest.fixture
    def db_manager(self):
        return MagicMock()
        
    @pytest.fixture
    def dialog(self, db_manager):
        """إنشاء نافذة للاختبارات"""
        # mock fetch_all for PRAGMA table_info
        db_manager.fetch_all.return_value = [(0, 'id'), (1, 'name'), (2, 'phone'), (3, 'phone2')]
        return CustomerFormDialog(db_manager=db_manager)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'name_input')
        assert hasattr(dialog, 'phone_input')
        assert hasattr(dialog, 'email_input')
        assert hasattr(dialog, 'address_input')
        assert hasattr(dialog, 'credit_limit_input')
    
    def test_name_input(self, dialog):
        """اختبار حقل الاسم"""
        dialog.name_input.setText("محمد أحمد")
        assert dialog.name_input.text() == "محمد أحمد"
    
    def test_phone_input(self, dialog):
        """اختبار حقل الهاتف"""
        dialog.phone_input.setText("+1234567890")
        assert dialog.phone_input.text() == "+1234567890"
    
    def test_email_input(self, dialog):
        """اختبار حقل البريد"""
        dialog.email_input.setText("customer@example.com")
        assert dialog.email_input.text() == "customer@example.com"
    
    def test_load_customer(self, db_manager):
        """اختبار تحميل بيانات العميل للتعديل"""
        db_manager.fetch_all.return_value = [(0, 'id'), (1, 'name'), (2, 'phone'), (3, 'phone2')]
        db_manager.fetch_one.return_value = ("Customer Name", "12345", "67890", "test@test.com", "Address", 1000.0, 1)
        
        dialog = CustomerFormDialog(db_manager=db_manager, customer_id=1)
        
        assert dialog.name_input.text() == "Customer Name"
        assert dialog.phone_input.text() == "12345"
        assert dialog.email_input.text() == "test@test.com"
        assert dialog.credit_limit_input.value() == 1000.0
        assert dialog.active_checkbox.isChecked() is True
    
    def test_save_customer_valid(self, dialog):
        """اختبار حفظ العميل"""
        dialog.name_input.setText("Valid Customer")
        dialog.phone_input.setText("123456789")
        
        with patch.object(dialog.notify, 'show_success') as mock_success:
            dialog.save_customer()
            mock_success.assert_called_once()
            dialog.db_manager.execute_query.assert_called_once()

    def test_save_customer_invalid_name(self, dialog):
        """اختبار حفظ العميل بدون اسم"""
        dialog.name_input.setText("")
        dialog.phone_input.setText("123456")
        
        with patch.object(dialog.notify, 'show_warning') as mock_warning:
            dialog.save_customer()
            mock_warning.assert_called_once()
            dialog.db_manager.execute_query.assert_not_called()
            
    def test_save_customer_invalid_phone(self, dialog):
        """اختبار حفظ العميل بدون هاتف"""
        dialog.name_input.setText("Name")
        dialog.phone_input.setText("")
        
        with patch.object(dialog.notify, 'show_warning') as mock_warning:
            dialog.save_customer()
            mock_warning.assert_called_once()
            dialog.db_manager.execute_query.assert_not_called()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

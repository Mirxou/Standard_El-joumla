#!/usr/bin/env python3
"""
اختبارات Supplier Form Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.dialogs.supplier_form_dialog import SupplierFormDialog

app = QApplication.instance() or QApplication([])

class TestSupplierFormDialog:
    """اختبارات نافذة نموذج المورد"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_one.return_value = ("Name", "123", "456", "email@test.com", "Contact", "Address", 1)
        with patch('src.utils.i18n_api.I18n') as MockI18n:
            mock_i18n_instance = MockI18n.return_value
            mock_i18n_instance.get_message.return_value = "Test"
            return SupplierFormDialog(db_manager=mock_db)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'name_input')
        assert hasattr(dialog, 'contact_input')
        assert hasattr(dialog, 'phone_input')
        assert hasattr(dialog, 'email_input')
    
    def test_name_input(self, dialog):
        """اختبار حقل اسم المورد"""
        dialog.name_input.setText("مورد التجزئة")
        assert dialog.name_input.text() == "مورد التجزئة"
    
    def test_contact_input(self, dialog):
        """اختبار حقل الشخص المسؤول"""
        dialog.contact_input.setText("أحمد محمد")
        assert dialog.contact_input.text() == "أحمد محمد"
    
    def test_phone_input(self, dialog):
        """اختبار حقل الهاتف"""
        dialog.phone_input.setText("+1234567890")
        assert dialog.phone_input.text() == "+1234567890"
    
    def test_load_supplier(self, dialog):
        """اختبار تعيين بيانات المورد"""
        dialog.supplier_id = 1
        dialog.load_supplier()
        assert dialog.name_input.text() == "Name"
        assert dialog.phone_input.text() == "123"
        
    def test_save_supplier_valid(self, dialog):
        """اختبار حفظ المورد"""
        dialog.name_input.setText("Test Supplier")
        dialog.phone_input.setText("123456")
        
        dialog.save_supplier()
        dialog.db_manager.execute_query.assert_called()

    def test_save_supplier_invalid(self, dialog):
        """اختبار التحقق من مورد بدون اسم"""
        dialog.name_input.setText("")
        dialog.save_supplier()
        # Should show warning, execute_query not called
        assert not dialog.db_manager.execute_query.called

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

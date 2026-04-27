#!/usr/bin/env python3
"""
اختبارات Category Form Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QLineEdit, QTextEdit, QCheckBox
from src.ui.dialogs.category_form_dialog import CategoryFormDialog

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestCategoryFormDialog:
    """اختبارات نافذة نموذج الفئة"""
    
    @pytest.fixture
    def db_manager(self):
        """مدير قاعدة بيانات وهمي"""
        db = Mock()
        db.fetch_one.return_value = ("Electronics", "Gadgets", 1)
        return db
    
    @pytest.fixture
    def dialog(self, db_manager):
        """إنشاء النافذة للاختبارات"""
        return CategoryFormDialog(db_manager)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'name_input')
        assert hasattr(dialog, 'desc_input')
        assert hasattr(dialog, 'active_checkbox')
        assert isinstance(dialog.name_input, QLineEdit)
        assert isinstance(dialog.desc_input, QTextEdit)
        assert isinstance(dialog.active_checkbox, QCheckBox)
    
    def test_load_category(self, db_manager):
        """اختبار تحميل بيانات فئة موجودة"""
        dialog = CategoryFormDialog(db_manager, category_id=1)
        # load_category يتم استدعاؤها في __init__
        assert dialog.name_input.text() == "Electronics"
        assert dialog.desc_input.toPlainText() == "Gadgets"
        assert dialog.active_checkbox.isChecked() is True
    
    def test_save_category_new(self, dialog, db_manager):
        """اختبار حفظ فئة جديدة"""
        dialog.name_input.setText("New Category")
        dialog.desc_input.setText("New Description")
        
        with patch.object(dialog, 'accept') as mock_accept:
            dialog.save_category()
            db_manager.execute_query.assert_called()
            mock_accept.assert_called_once()
    
    def test_save_category_empty_name(self, dialog, db_manager):
        """اختبار حفظ فئة بدون اسم"""
        dialog.name_input.setText("")
        
        with patch.object(dialog.notify, 'show_warning') as mock_warn:
            dialog.save_category()
            mock_warn.assert_called_with("تنبيه", "يجب إدخال اسم الفئة")
            db_manager.execute_query.assert_not_called()
    
    def test_save_category_update(self, db_manager):
        """اختبار تحديث فئة موجودة"""
        dialog = CategoryFormDialog(db_manager, category_id=1)
        dialog.name_input.setText("Updated Name")
        
        with patch.object(dialog, 'accept') as mock_accept:
            dialog.save_category()
            db_manager.execute_query.assert_called()
            # التأكد من وجود UPDATE في الاستعلام
            args = db_manager.execute_query.call_args[0][0]
            assert "UPDATE categories" in args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

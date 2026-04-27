#!/usr/bin/env python3
"""
اختبارات Category Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication, QTableWidget
from PySide6.QtCore import Qt
from src.ui.dialogs.category_dialog import CategoryDialog

# إنشاء تطبيق Qt للاختبارات
app = QApplication.instance() or QApplication([])


class TestCategoryDialog:
    """اختبارات نافذة الفئات"""
    
    @pytest.fixture
    def db_manager(self):
        """مدير قاعدة بيانات وهمي"""
        db = Mock()
        db.fetch_all.return_value = [
            (1, "Electronics", "Gadgets", 1),
            (2, "Clothing", "Apparel", 1)
        ]
        db.fetch_one.return_value = (5,) # 5 products
        return db
    
    @pytest.fixture
    def dialog(self, db_manager):
        """إنشاء النافذة للاختبارات"""
        return CategoryDialog(db_manager)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'table')
        assert hasattr(dialog, 'search_input')
        assert isinstance(dialog.table, QTableWidget)
    
    def test_load_categories(self, dialog, db_manager):
        """اختبار تحميل الفئات"""
        dialog.load_categories()
        assert len(dialog.categories) == 2
        assert dialog.table.rowCount() == 2
        db_manager.fetch_all.assert_called()
    
    def test_on_search(self, dialog):
        """اختبار البحث"""
        dialog.categories = [
            {'id': 1, 'name': 'Electronics', 'description': ''},
            {'id': 2, 'name': 'Clothing', 'description': ''}
        ]
        dialog.on_search("Elect")
        assert dialog.table.rowCount() == 1
        assert dialog.table.item(0, 0).text() == "Electronics"
    
    def test_delete_category_with_products(self, dialog, db_manager):
        """اختبار منع حذف فئة بها منتجات"""
        db_manager.fetch_one.return_value = (5,) # 5 products
        
        with patch.object(dialog.notify, 'show_warning') as mock_warn:
            dialog.delete_category(1)
            mock_warn.assert_called_with("تحذير", "لا يمكن حذف هذه الفئة. هناك 5 منتج مرتبط بها.")
            db_manager.execute_query.assert_not_called()
    
    def test_delete_category_empty(self, dialog, db_manager):
        """اختبار حذف فئة فارغة"""
        db_manager.fetch_one.return_value = (0,) # 0 products
        
        with patch('PySide6.QtWidgets.QMessageBox.question', return_value=pytest.importorskip('PySide6.QtWidgets').QMessageBox.StandardButton.Yes):
            dialog.delete_category(1)
            db_manager.execute_query.assert_called_with("DELETE FROM categories WHERE id = ?", (1,))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

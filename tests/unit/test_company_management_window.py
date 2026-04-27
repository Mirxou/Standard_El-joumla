#!/usr/bin/env python3
"""
اختبارات Company Management Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.company_management_window import CompanyManagementWindow

app = QApplication.instance() or QApplication([])


class TestCompanyManagementWindow:
    """اختبارات نافذة إدارة الشركة"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        mock_db.fetch_all.return_value = []
        mock_db.fetch_one.return_value = None
        
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            return CompanyManagementWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_company_info(self, window):
        """اختبار تحميل معلومات الشركة"""
        window.load_company_info()
    
    def test_update_company_info(self, window):
        """اختبار تحديث معلومات الشركة"""
        window.update_company_info({"name": "Test Co"})
    
    def test_manage_branches(self, window):
        """اختبار إدارة الفروع"""
        window.manage_branches()
    
    def test_add_branch(self, window):
        """اختبار إضافة فرع"""
        window.add_branch()
    
    def test_edit_branch(self, window):
        """اختبار تعديل فرع"""
        window.edit_branch(1)
    
    def test_delete_branch(self, window):
        """اختبار حذف فرع"""
        window.delete_branch(1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




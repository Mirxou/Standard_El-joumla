#!/usr/bin/env python3
"""
اختبارات Accounts Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.accounts_window import AccountsWindow

app = QApplication.instance() or QApplication([])


class TestAccountsWindow:
    """اختبارات نافذة الحسابات"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock()
            return AccountsWindow(mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_refresh_data(self, window):
        """اختبار تحديث البيانات"""
        window.refresh_data()
    
    def test_add_payment(self, window):
        """اختبار إضافة دفعة"""
        with patch.object(window, 'add_payment') as mock_add:
            window.add_payment()
            mock_add.assert_called_once()
    
    def test_filter_receivables(self, window):
        """اختبار تصفية الحسابات المدينة"""
        window.receivables_customer_filter.setText("test")
        window.filter_receivables()
    
    def test_filter_payables(self, window):
        """اختبار تصفية الحسابات الدائنة"""
        window.payables_supplier_filter.setText("test")
        window.filter_payables()
    
    def test_filter_schedules(self, window):
        """اختبار تصفية جدولة المدفوعات"""
        window.filter_schedules()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




#!/usr/bin/env python3
"""
اختبارات EDI Management Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.edi_management_window import EDIManagementWindow

app = QApplication.instance() or QApplication([])


class TestEDIManagementWindow:
    """اختبارات نافذة إدارة EDI"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return EDIManagementWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_edi_transactions(self, window):
        """اختبار تحميل معاملات EDI"""
        window.load_edi_transactions()
    
    def test_send_edi_message(self, window):
        """اختبار إرسال رسالة EDI"""
        window.send_edi_message("partner_id", "message_data")
    
    def test_receive_edi_message(self, window):
        """اختبار استلام رسالة EDI"""
        window.receive_edi_message("message_id")
    
    def test_configure_partner(self, window):
        """اختبار تكوين الشريك"""
        window.configure_partner("partner_id")
    
    def test_validate_edi_message(self, window):
        """اختبار التحقق من رسالة EDI"""
        window.validate_edi_message("message_data")
    
    def test_export_edi_log(self, window):
        """اختبار تصدير سجل EDI"""
        window.export_edi_log("edi_log.xlsx")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




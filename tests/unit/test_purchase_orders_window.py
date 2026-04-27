#!/usr/bin/env python3
"""
اختبارات Purchase Orders Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.purchase_orders_window import PurchaseOrdersWindow

app = QApplication.instance() or QApplication([])


class TestPurchaseOrdersWindow:
    """اختبارات نافذة أوامر الشراء"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return PurchaseOrdersWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_purchase_orders(self, window):
        """اختبار تحميل أوامر الشراء"""
        window.load_purchase_orders()
    
    def test_create_purchase_order(self, window):
        """اختبار إنشاء أمر شراء"""
        window.create_purchase_order()
    
    def test_edit_purchase_order(self, window):
        """اختبار تعديل أمر شراء"""
        window.edit_purchase_order("po_id")
    
    def test_approve_purchase_order(self, window):
        """اختبار الموافقة على أمر شراء"""
        window.approve_purchase_order("po_id")
    
    def test_receive_purchase_order(self, window):
        """اختبار استلام أمر شراء"""
        window.receive_purchase_order("po_id")
    
    def test_filter_by_status(self, window):
        """اختبار التصفية حسب الحالة"""
        window.filter_by_status("pending")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




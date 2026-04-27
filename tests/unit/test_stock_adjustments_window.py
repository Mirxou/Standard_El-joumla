#!/usr/bin/env python3
"""
اختبارات Stock Adjustments Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.stock_adjustments_window import StockAdjustmentsWindow
from src.models.physical_count import StockAdjustment, AdjustmentStatus, AdjustmentType
from decimal import Decimal
from datetime import date

app = QApplication.instance() or QApplication([])

class TestStockAdjustmentsWindow:
    """اختبارات نافذة تسويات المخزون"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        mock_db = MagicMock()
        with patch('src.ui.windows.stock_adjustments_window.InventoryCountService') as mock_service_class:
            mock_service = mock_service_class.return_value
            
            mock_adj = MagicMock(spec=StockAdjustment)
            mock_adj.id = 1
            mock_adj.adjustment_number = "ADJ-001"
            mock_adj.adjustment_date = date.today()
            mock_adj.type_label = "Test"
            mock_adj.product_code = "P1"
            mock_adj.product_name = "Product 1"
            mock_adj.quantity_before = Decimal("10")
            mock_adj.adjustment_quantity = Decimal("5")
            mock_adj.is_increase = True
            mock_adj.quantity_after = Decimal("15")
            mock_adj.adjustment_value = Decimal("50")
            mock_adj.status_label = "Pending"
            mock_adj.status = AdjustmentStatus.PENDING
            mock_adj.created_by_name = "Admin"
            
            mock_service.get_all_adjustments.return_value = [mock_adj]
            return StockAdjustmentsWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
        assert window.table.rowCount() == 1
    
    def test_load_data(self, window):
        """اختبار تحميل التسويات"""
        window.load_data()
        assert window.table.rowCount() == 1
    
    def test_create_adjustment(self, window):
        """اختبار إنشاء تسوية (Stub)"""
        assert window.create_adjustment() is True
    
    def test_approve_adjustment_stub(self, window):
        """اختبار الموافقة (Stubbed flow)"""
        with patch.object(window, 'get_selected_adjustment_id', return_value=None):
            window.approve_adjustment()
    
    def test_get_adjustment_history(self, window):
        """اختبار الحصول على تاريخ التسويات (Stub)"""
        history = window.get_adjustment_history("product_id")
        assert history is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

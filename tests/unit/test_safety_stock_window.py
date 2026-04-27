#!/usr/bin/env python3
"""
اختبارات Safety Stock Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.safety_stock_window import SafetyStockWindow

app = QApplication.instance() or QApplication([])


class TestSafetyStockWindow:
    """اختبارات نافذة المخزون الاحتياطي"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return SafetyStockWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_safety_stock_settings(self, window):
        """اختبار تحميل إعدادات المخزون الاحتياطي"""
        window.load_safety_stock_settings()
    
    def test_set_safety_stock_level(self, window):
        """اختبار تعيين مستوى المخزون الاحتياطي"""
        window.set_safety_stock_level("product_id", 50)
    
    def test_get_safety_stock_level(self, window):
        """اختبار الحصول على مستوى المخزون الاحتياطي"""
        level = window.get_safety_stock_level("product_id")
        assert isinstance(level, int)
    
    def test_calculate_safety_stock(self, window):
        """اختبار حساب المخزون الاحتياطي"""
        window.calculate_safety_stock("product_id")
    
    def test_get_below_safety_stock_products(self, window):
        """اختبار الحصول على المنتجات تحت المخزون الاحتياطي"""
        products = window.get_below_safety_stock_products()
        assert isinstance(products, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




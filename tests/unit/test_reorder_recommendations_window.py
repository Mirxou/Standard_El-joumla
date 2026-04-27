#!/usr/bin/env python3
"""
اختبارات Reorder Recommendations Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.reorder_recommendations_window import ReorderRecommendationsWindow

app = QApplication.instance() or QApplication([])


class TestReorderRecommendationsWindow:
    """اختبارات نافذة توصيات إعادة الطلب"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return ReorderRecommendationsWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_reorder_recommendations(self, window):
        """اختبار تحميل توصيات إعادة الطلب"""
        window.load_reorder_recommendations()
    
    def test_generate_recommendations(self, window):
        """اختبار إنشاء التوصيات"""
        window.generate_recommendations()
    
    def test_get_product_reorder_point(self, window):
        """اختبار الحصول على نقطة إعادة الطلب للمنتج"""
        point = window.get_product_reorder_point("product_id")
        assert isinstance(point, int)
    
    def test_get_economic_order_quantity(self, window):
        """اختبار الحصول على الكمية الاقتصادية للطلب"""
        qty = window.get_economic_order_quantity("product_id")
        assert isinstance(qty, int)
    
    def test_create_purchase_order_from_recommendation(self, window):
        """اختبار إنشاء أمر شراء من التوصية"""
        window.create_purchase_order_from_recommendation("product_id")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




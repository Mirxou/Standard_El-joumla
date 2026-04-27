#!/usr/bin/env python3
"""
اختبارات Payment Plans Window
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from src.ui.windows.payment_plans_window import PaymentPlansWindow

app = QApplication.instance() or QApplication([])


class TestPaymentPlansWindow:
    """اختبارات نافذة خطط الدفع"""
    
    @pytest.fixture
    def window(self):
        """إنشاء نافذة للاختبارات"""
        with patch('src.core.config_manager.ConfigManager') as mock_config:
            mock_config.return_value.get.return_value = {}
            mock_db = MagicMock(); mock_db.fetch_all.return_value = []; mock_db.fetch_one.return_value = None; return PaymentPlansWindow(db_manager=mock_db)
    
    def test_initialization(self, window):
        """اختبار التهيئة"""
        assert window is not None
    
    def test_load_payment_plans(self, window):
        """اختبار تحميل خطط الدفع"""
        window.load_payment_plans()
    
    def test_create_payment_plan(self, window):
        """اختبار إنشاء خطة دفع"""
        window.create_payment_plan()
    
    def test_edit_payment_plan(self, window):
        """اختبار تعديل خطة دفع"""
        window.edit_payment_plan("plan_id")
    
    def test_delete_payment_plan(self, window):
        """اختبار حذف خطة دفع"""
        window.delete_payment_plan("plan_id")
    
    def test_get_installments(self, window):
        """اختبار الحصول على الأقساط"""
        installments = window.get_installments("plan_id")
        assert isinstance(installments, list)
    
    def test_record_payment(self, window):
        """اختبار تسجيل دفعة"""
        window.record_payment("installment_id", 100.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




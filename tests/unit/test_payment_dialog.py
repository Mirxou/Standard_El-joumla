#!/usr/bin/env python3
"""
اختبارات Payment Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QComboBox
from PySide6.QtCore import Qt
from src.ui.dialogs.payment_dialog import PaymentDialog

app = QApplication.instance() or QApplication([])


class TestPaymentDialog:
    """اختبارات نافذة الدفع"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        invoice = Mock()
        invoice.total = Decimal("100.00")
        invoice.id = "INV001"
        return PaymentDialog(invoice)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'amount_input')
        assert hasattr(dialog, 'payment_method_combo')
    
    def test_amount_input(self, dialog):
        """اختبار حقل المبلغ"""
        dialog.amount_input.setText("50.00")
        assert dialog.amount_input.text() == "50.00"
    
    def test_payment_method_combo(self, dialog):
        """اختبار قائمة طريقة الدفع"""
        assert dialog.payment_method_combo is not None
        assert isinstance(dialog.payment_method_combo, QComboBox)
    
    def test_get_payment_data(self, dialog):
        """اختبار الحصول على بيانات الدفع"""
        dialog.amount_input.setText("75.00")
        
        data = dialog.get_payment_data()
        
        assert isinstance(data, dict)
        assert "amount" in data
        assert "payment_method" in data
    
    def test_validate_amount_valid(self, dialog):
        """اختبار التحقق من مبلغ صحيح"""
        assert dialog.validate_amount("50.00") is True
    
    def test_validate_amount_invalid(self, dialog):
        """اختبار التحقق من مبلغ خاطئ"""
        assert dialog.validate_amount("-10.00") is False
    
    def test_calculate_change(self, dialog):
        """اختبار حساب الباقي"""
        change = dialog.calculate_change(Decimal("100.00"), Decimal("75.00"))
        assert change == Decimal("25.00")
    
    def test_on_process_payment(self, dialog):
        """اختبار معالجة الدفع"""
        dialog.amount_input.setText("100.00")
        result = dialog.on_process_payment()
        assert result is not None
    
    def test_show_receipt(self, dialog):
        """اختبار عرض الإيصال"""
        result = dialog.show_receipt()
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




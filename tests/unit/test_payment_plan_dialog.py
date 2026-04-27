#!/usr/bin/env python3
"""
اختبارات Payment Plan Dialog
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from datetime import date, timedelta
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QTableWidget, QPushButton, QSpinBox, QComboBox
from PySide6.QtCore import Qt
from src.ui.dialogs.payment_plan_dialog import PaymentPlanDialog

app = QApplication.instance() or QApplication([])


class TestPaymentPlanDialog:
    """اختبارات نافذة خطة الدفع"""
    
    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        payment_service = Mock()
        return PaymentPlanDialog(payment_service)
    
    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, 'plan_name_input')
        assert hasattr(dialog, 'number_of_payments_spin')
        assert hasattr(dialog, 'payment_interval_combo')
    
    def test_plan_name_input(self, dialog):
        """اختبار حقل اسم الخطة"""
        dialog.plan_name_input.setText("خطة شهرية")
        assert dialog.plan_name_input.text() == "خطة شهرية"
    
    def test_number_of_payments_spin(self, dialog):
        """اختبار حقل عدد الدفعات"""
        dialog.number_of_payments_spin.setValue(12)
        assert dialog.number_of_payments_spin.value() == 12
    
    def test_payment_interval_combo(self, dialog):
        """اختبار قائمة الفترة بين الدفعات"""
        assert dialog.payment_interval_combo is not None
        assert isinstance(dialog.payment_interval_combo, QComboBox)
    
    def test_set_plan_details(self, dialog):
        """اختبار تعيين تفاصيل الخطة"""
        dialog.plan_name_input.setText("خطة 6 أشهر")
        dialog.number_of_payments_spin.setValue(6)
        
        assert dialog.get_plan_name() == "خطة 6 أشهر"
        assert dialog.get_number_of_payments() == 6
    
    def test_generate_schedule(self, dialog):
        """اختبار إنشاء الجدول الزمني"""
        dialog.plan_name_input.setText("خطة تجريبية")
        dialog.number_of_payments_spin.setValue(3)
        
        schedule = dialog.generate_schedule()
        
        assert isinstance(schedule, list)
        assert len(schedule) == 3
    
    def test_get_payment_interval(self, dialog):
        """اختبار الحصول على الفترة بين الدفعات"""
        interval = dialog.get_payment_interval()
        
        assert isinstance(interval, int)
        assert interval > 0
    
    def test_validate_plan_valid(self, dialog):
        """اختبار التحقق من خطة صحيحة"""
        dialog.plan_name_input.setText("Valid Plan")
        dialog.number_of_payments_spin.setValue(6)
        assert dialog.validate_plan() is True
    
    def test_validate_plan_invalid(self, dialog):
        """اختبار التحقق من خطة بدون اسم"""
        dialog.plan_name_input.setText("")
        assert dialog.validate_plan() is False
    
    def test_on_save_plan(self, dialog):
        """اختبار حفظ الخطة"""
        dialog.plan_name_input.setText("Test Plan")
        dialog.number_of_payments_spin.setValue(3)
        
        result = dialog.on_save_plan()
        
        assert result is not None
    
    def test_get_plan_data(self, dialog):
        """اختبار الحصول على بيانات الخطة"""
        dialog.plan_name_input.setText("My Plan")
        dialog.number_of_payments_spin.setValue(6)
        
        data = dialog.get_plan_data()
        
        assert isinstance(data, dict)
        assert data.get("name") == "My Plan"
        assert data.get("number_of_payments") == 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




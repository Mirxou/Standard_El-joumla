#!/usr/bin/env python3
"""
اختبارات Installment Payment Dialog
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication, QTableWidget

from src.ui.dialogs.installment_payment_dialog import InstallmentPaymentDialog

app = QApplication.instance() or QApplication([])


class TestInstallmentPaymentDialog:
    """اختبارات نافذة الدفع بالتقسيط"""

    @pytest.fixture
    def dialog(self):
        """إنشاء نافذة للاختبارات"""
        payment_service = Mock()
        invoice = {
            "id": 1,
            "total": Decimal("1000.00"),
            "remaining": Decimal("1000.00"),
        }
        return InstallmentPaymentDialog(payment_service, invoice)

    def test_initialization(self, dialog):
        """اختبار تهيئة النافذة"""
        assert dialog is not None
        assert hasattr(dialog, "total_amount_label")
        assert hasattr(dialog, "installments_table")

    def test_total_amount_display(self, dialog):
        """اختبار عرض المبلغ الإجمالي"""
        assert dialog.total_amount_label is not None

    def test_installments_table(self, dialog):
        """اختبار جدول الأقساط"""
        assert dialog.installments_table is not None
        assert isinstance(dialog.installments_table, QTableWidget)

    def test_calculate_installments(self, dialog):
        """اختبار حساب الأقساط"""
        result = dialog.calculate_installments(10)

        assert result is not None

    def test_get_installment_amount(self, dialog):
        """اختبار الحصول على مبلغ القسط"""
        amount = dialog.get_installment_amount(10)

        assert isinstance(amount, Decimal)
        assert amount == Decimal("100.00")

    def test_add_installment(self, dialog):
        """اختبار إضافة قسط"""
        result = dialog.add_installment(date(2024, 1, 15), Decimal("100.00"))

        assert result is not None

    def test_remove_installment(self, dialog):
        """اختبار إزالة قسط"""
        dialog.add_installment(date(2024, 1, 15), Decimal("100.00"))
        result = dialog.remove_installment(0)

        assert result is not None

    def test_validate_installments(self, dialog):
        """اختبار التحقق من الأقساط"""
        dialog.add_installment(date(2024, 1, 15), Decimal("500.00"))
        dialog.add_installment(date(2024, 2, 15), Decimal("500.00"))

        assert dialog.validate_installments() is True

    def test_on_save_plan(self, dialog):
        """اختبار حفظ خطة الأقساط"""
        dialog.add_installment(date(2024, 1, 15), Decimal("500.00"))
        dialog.add_installment(date(2024, 2, 15), Decimal("500.00"))

        result = dialog.on_save_plan()

        assert result is not None

    def test_get_installment_schedule(self, dialog):
        """اختبار الحصول على جدول الأقساط"""
        dialog.add_installment(date(2024, 1, 15), Decimal("500.00"))
        dialog.add_installment(date(2024, 2, 15), Decimal("500.00"))

        schedule = dialog.get_installment_schedule()

        assert isinstance(schedule, list)
        assert len(schedule) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

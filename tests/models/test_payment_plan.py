#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج خطط الدفع والتقسيط - Payment Plan Model Tests
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from src.models.payment_plan import (
    PaymentPlanStatus, InstallmentStatus, PaymentFrequency,
    LateFeeType, PaymentInstallment
)


class TestPaymentPlanStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات خطة الدفع"""
    
    def test_payment_plan_status_values(self):
        """اختبار قيم حالات خطة الدفع"""
        self.assertEqual(PaymentPlanStatus.DRAFT.value, "مسودة")
        self.assertEqual(PaymentPlanStatus.ACTIVE.value, "نشط")
        self.assertEqual(PaymentPlanStatus.COMPLETED.value, "مكتمل")
        self.assertEqual(PaymentPlanStatus.CANCELLED.value, "ملغي")
        self.assertEqual(PaymentPlanStatus.DEFAULTED.value, "متعثر")
        self.assertEqual(PaymentPlanStatus.ON_HOLD.value, "معلق")
    
    def test_all_payment_plan_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(PaymentPlanStatus)
        self.assertEqual(len(statuses), 6)


class TestInstallmentStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات الأقساط"""
    
    def test_installment_status_values(self):
        """اختبار قيم حالات الأقساط"""
        self.assertEqual(InstallmentStatus.PENDING.value, "معلق")
        self.assertEqual(InstallmentStatus.PAID.value, "مدفوع")
        self.assertEqual(InstallmentStatus.PARTIALLY_PAID.value, "مدفوع جزئياً")
        self.assertEqual(InstallmentStatus.OVERDUE.value, "متأخر")
        self.assertEqual(InstallmentStatus.CANCELLED.value, "ملغي")
        self.assertEqual(InstallmentStatus.WAIVED.value, "معفي")
    
    def test_all_installment_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(InstallmentStatus)
        self.assertEqual(len(statuses), 6)


class TestPaymentFrequencyEnum(unittest.TestCase):
    """اختبارات تعداد تكرارات الدفع"""
    
    def test_payment_frequency_values(self):
        """اختبار قيم تكرارات الدفع"""
        self.assertEqual(PaymentFrequency.DAILY.value, "يومي")
        self.assertEqual(PaymentFrequency.WEEKLY.value, "أسبوعي")
        self.assertEqual(PaymentFrequency.MONTHLY.value, "شهري")
        self.assertEqual(PaymentFrequency.QUARTERLY.value, "ربع سنوي")
        self.assertEqual(PaymentFrequency.SEMIANNUAL.value, "نصف سنوي")
        self.assertEqual(PaymentFrequency.ANNUAL.value, "سنوي")
        self.assertEqual(PaymentFrequency.CUSTOM.value, "مخصص")
    
    def test_all_payment_frequencies(self):
        """اختبار عدد جميع التكرارات"""
        frequencies = list(PaymentFrequency)
        self.assertEqual(len(frequencies), 8)


class TestLateFeeTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع غرامات التأخير"""
    
    def test_late_fee_type_values(self):
        """اختبار قيم أنواع الغرامات"""
        self.assertEqual(LateFeeType.NONE.value, "بدون")
        self.assertEqual(LateFeeType.FIXED.value, "مبلغ ثابت")
        self.assertEqual(LateFeeType.PERCENTAGE.value, "نسبة مئوية")
        self.assertEqual(LateFeeType.COMPOUNDING.value, "نسبة تراكمية")
    
    def test_all_late_fee_types(self):
        """اختبار عدد جميع الأنواع"""
        types = list(LateFeeType)
        self.assertEqual(len(types), 4)


class TestPaymentInstallmentCreation(unittest.TestCase):
    """اختبارات إنشاء قسط الدفع"""
    
    def test_installment_default_values(self):
        """اختبار القيم الافتراضية"""
        installment = PaymentInstallment()
        
        self.assertIsNone(installment.id)
        self.assertEqual(installment.installment_number, 1)
        self.assertEqual(installment.principal_amount, Decimal('0.00'))
        self.assertEqual(installment.interest_amount, Decimal('0.00'))
        self.assertEqual(installment.status, InstallmentStatus.PENDING)
    
    def test_installment_with_values(self):
        """اختبار إنشاء قسط مع قيم"""
        due_date = date(2024, 12, 31)
        installment = PaymentInstallment(
            installment_number=1,
            due_date=due_date,
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00'),
            total_amount=Decimal('1100.00')
        )
        
        self.assertEqual(installment.installment_number, 1)
        self.assertEqual(installment.due_date, due_date)
        self.assertEqual(installment.principal_amount, Decimal('1000.00'))
        self.assertEqual(installment.total_amount, Decimal('1100.00'))


class TestInstallmentAmounts(unittest.TestCase):
    """اختبارات مبالغ الأقساط"""
    
    def test_installment_principal(self):
        """اختبار المبلغ الأصلي"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00')
        )
        
        self.assertEqual(installment.principal_amount, Decimal('1000.00'))
    
    def test_installment_with_interest(self):
        """اختبار القسط مع الفائدة"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00')
        )
        
        self.assertEqual(installment.principal_amount, Decimal('1000.00'))
        self.assertEqual(installment.interest_amount, Decimal('100.00'))
    
    def test_installment_with_late_fee(self):
        """اختبار القسط مع غرامة التأخير"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            late_fee=Decimal('50.00')
        )
        
        self.assertEqual(installment.late_fee, Decimal('50.00'))
    
    def test_installment_total_amount(self):
        """اختبار المبلغ الإجمالي"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00'),
            late_fee=Decimal('50.00'),
            total_amount=Decimal('1150.00')
        )
        
        self.assertEqual(installment.total_amount, Decimal('1150.00'))
    
    def test_installment_amount_paid(self):
        """اختبار المبلغ المدفوع"""
        installment = PaymentInstallment(
            total_amount=Decimal('1150.00'),
            amount_paid=Decimal('575.00')
        )
        
        self.assertEqual(installment.amount_paid, Decimal('575.00'))
    
    def test_installment_remaining_amount(self):
        """اختبار المبلغ المتبقي"""
        installment = PaymentInstallment(
            total_amount=Decimal('1150.00'),
            amount_paid=Decimal('575.00'),
            remaining_amount=Decimal('575.00')
        )
        
        self.assertEqual(installment.remaining_amount, Decimal('575.00'))


class TestInstallmentStatus(unittest.TestCase):
    """اختبارات حالات الأقساط"""
    
    def test_installment_pending(self):
        """اختبار قسط معلق"""
        installment = PaymentInstallment(
            status=InstallmentStatus.PENDING
        )
        
        self.assertEqual(installment.status, InstallmentStatus.PENDING)
    
    def test_installment_paid(self):
        """اختبار قسط مدفوع"""
        installment = PaymentInstallment(
            status=InstallmentStatus.PAID,
            amount_paid=Decimal('1150.00'),
            payment_date=date.today()
        )
        
        self.assertEqual(installment.status, InstallmentStatus.PAID)
        self.assertIsNotNone(installment.payment_date)
    
    def test_installment_partially_paid(self):
        """اختبار قسط مدفوع جزئياً"""
        installment = PaymentInstallment(
            status=InstallmentStatus.PARTIALLY_PAID,
            total_amount=Decimal('1150.00'),
            amount_paid=Decimal('500.00')
        )
        
        self.assertEqual(installment.status, InstallmentStatus.PARTIALLY_PAID)
        self.assertLess(installment.amount_paid, installment.total_amount)
    
    def test_installment_overdue(self):
        """اختبار قسط متأخر"""
        past_date = date.today() - timedelta(days=30)
        installment = PaymentInstallment(
            status=InstallmentStatus.OVERDUE,
            due_date=past_date
        )
        
        self.assertEqual(installment.status, InstallmentStatus.OVERDUE)
        self.assertLess(installment.due_date, date.today())
    
    def test_installment_cancelled(self):
        """اختبار قسط ملغي"""
        installment = PaymentInstallment(
            status=InstallmentStatus.CANCELLED
        )
        
        self.assertEqual(installment.status, InstallmentStatus.CANCELLED)
    
    def test_installment_waived(self):
        """اختبار قسط معفي"""
        installment = PaymentInstallment(
            status=InstallmentStatus.WAIVED
        )
        
        self.assertEqual(installment.status, InstallmentStatus.WAIVED)


class TestInstallmentDates(unittest.TestCase):
    """اختبارات تواريخ الأقساط"""
    
    def test_installment_due_date(self):
        """اختبار تاريخ الاستحقاق"""
        due_date = date(2024, 12, 31)
        installment = PaymentInstallment(due_date=due_date)
        
        self.assertEqual(installment.due_date, due_date)
    
    def test_installment_payment_date(self):
        """اختبار تاريخ الدفع"""
        payment_date = date(2024, 12, 25)
        installment = PaymentInstallment(payment_date=payment_date)
        
        self.assertEqual(installment.payment_date, payment_date)
    
    def test_installment_early_payment(self):
        """اختبار الدفع المبكر"""
        due_date = date(2024, 12, 31)
        payment_date = date(2024, 12, 20)
        
        installment = PaymentInstallment(
            due_date=due_date,
            payment_date=payment_date
        )
        
        self.assertLess(installment.payment_date, installment.due_date)
    
    def test_installment_late_payment(self):
        """اختبار الدفع المتأخر"""
        due_date = date(2024, 12, 31)
        payment_date = date(2025, 1, 15)
        
        installment = PaymentInstallment(
            due_date=due_date,
            payment_date=payment_date
        )
        
        self.assertGreater(installment.payment_date, installment.due_date)


class TestInstallmentPayment(unittest.TestCase):
    """اختبارات معلومات الدفع"""
    
    def test_installment_payment_method(self):
        """اختبار طريقة الدفع"""
        installment = PaymentInstallment(
            payment_method="تحويل بنكي"
        )
        
        self.assertEqual(installment.payment_method, "تحويل بنكي")
    
    def test_installment_payment_reference(self):
        """اختبار مرجع الدفع"""
        installment = PaymentInstallment(
            payment_reference="PAY-001-2024"
        )
        
        self.assertEqual(installment.payment_reference, "PAY-001-2024")
    
    def test_installment_payment_details(self):
        """اختبار تفاصيل الدفع الكاملة"""
        installment = PaymentInstallment(
            payment_method="شيك",
            payment_reference="CHK-12345",
            payment_date=date.today(),
            amount_paid=Decimal('575.00')
        )
        
        self.assertEqual(installment.payment_method, "شيك")
        self.assertEqual(installment.payment_reference, "CHK-12345")
        self.assertEqual(installment.amount_paid, Decimal('575.00'))


class TestInstallmentNotes(unittest.TestCase):
    """اختبارات ملاحظات الأقساط"""
    
    def test_installment_notes(self):
        """اختبار ملاحظات القسط"""
        installment = PaymentInstallment(
            notes="تم التأجيل بسبب ظرف طارئ"
        )
        
        self.assertEqual(installment.notes, "تم التأجيل بسبب ظرف طارئ")
    
    def test_installment_no_notes(self):
        """اختبار بدون ملاحظات"""
        installment = PaymentInstallment()
        
        self.assertIsNone(installment.notes)


class TestInstallmentEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_installment_zero_amount(self):
        """اختبار مبلغ صفر"""
        installment = PaymentInstallment(
            principal_amount=Decimal('0.00'),
            total_amount=Decimal('0.00')
        )
        
        self.assertEqual(installment.principal_amount, Decimal('0.00'))
    
    def test_installment_large_amount(self):
        """اختبار مبلغ كبير"""
        installment = PaymentInstallment(
            principal_amount=Decimal('999999.99'),
            total_amount=Decimal('999999.99')
        )
        
        self.assertEqual(installment.principal_amount, Decimal('999999.99'))
    
    def test_installment_high_interest(self):
        """اختبار فائدة عالية"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('500.00')
        )
        
        self.assertGreater(installment.interest_amount, Decimal('0'))
    
    def test_installment_no_interest(self):
        """اختبار بدون فائدة"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('0.00')
        )
        
        self.assertEqual(installment.interest_amount, Decimal('0.00'))
    
    def test_installment_high_late_fee(self):
        """اختبار غرامة تأخير عالية"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            late_fee=Decimal('500.00')
        )
        
        self.assertGreater(installment.late_fee, Decimal('0'))
    
    def test_installment_no_late_fee(self):
        """اختبار بدون غرامة تأخير"""
        installment = PaymentInstallment(
            principal_amount=Decimal('1000.00'),
            late_fee=Decimal('0.00')
        )
        
        self.assertEqual(installment.late_fee, Decimal('0.00'))
    
    def test_installment_overpayment(self):
        """اختبار الدفع الزائد"""
        installment = PaymentInstallment(
            total_amount=Decimal('1150.00'),
            amount_paid=Decimal('1200.00')
        )
        
        self.assertGreater(installment.amount_paid, installment.total_amount)
    
    def test_installment_far_future_due_date(self):
        """اختبار تاريخ استحقاق بعيد في المستقبل"""
        future_date = date.today() + timedelta(days=365)
        installment = PaymentInstallment(due_date=future_date)
        
        self.assertGreater(installment.due_date, date.today())


class TestInstallmentIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""
    
    def test_installment_complete_paid(self):
        """اختبار قسط مدفوع بشكل كامل"""
        installment = PaymentInstallment(
            id=1,
            payment_plan_id=1,
            installment_number=1,
            due_date=date(2024, 12, 31),
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00'),
            late_fee=Decimal('0.00'),
            total_amount=Decimal('1100.00'),
            amount_paid=Decimal('1100.00'),
            remaining_amount=Decimal('0.00'),
            status=InstallmentStatus.PAID,
            payment_date=date(2024, 12, 25),
            payment_method="تحويل بنكي",
            payment_reference="TRANSFER-001"
        )
        
        self.assertEqual(installment.id, 1)
        self.assertEqual(installment.amount_paid, Decimal('1100.00'))
        self.assertEqual(installment.remaining_amount, Decimal('0.00'))
        self.assertEqual(installment.status, InstallmentStatus.PAID)
    
    def test_installment_complete_overdue(self):
        """اختبار قسط متأخر مع غرامة"""
        installment = PaymentInstallment(
            id=2,
            payment_plan_id=1,
            installment_number=2,
            due_date=date(2024, 12, 15),
            principal_amount=Decimal('1000.00'),
            interest_amount=Decimal('100.00'),
            late_fee=Decimal('50.00'),
            total_amount=Decimal('1150.00'),
            amount_paid=Decimal('500.00'),
            remaining_amount=Decimal('650.00'),
            status=InstallmentStatus.OVERDUE,
            payment_date=None
        )
        
        self.assertEqual(installment.id, 2)
        self.assertLess(installment.due_date, date.today())
        self.assertEqual(installment.status, InstallmentStatus.OVERDUE)
        self.assertGreater(installment.late_fee, Decimal('0'))


if __name__ == '__main__':
    unittest.main()

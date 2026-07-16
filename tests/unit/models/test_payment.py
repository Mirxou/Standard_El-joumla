"""
اختبارات شاملة لنموذج Payment
Comprehensive tests for Payment model
"""

import unittest
from datetime import date
from decimal import Decimal

from src.models.payment import (
    AccountType,
    Payment,
    PaymentMethod,
    PaymentStatus,
    PaymentType,
)


class TestPaymentTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع المدفوعات"""

    def test_payment_type_customer(self):
        """نوع دفعة العميل"""
        self.assertEqual(PaymentType.CUSTOMER_PAYMENT.value, "دفعة عميل")

    def test_payment_type_supplier(self):
        """نوع دفعة المورد"""
        self.assertEqual(PaymentType.SUPPLIER_PAYMENT.value, "دفعة مورد")

    def test_payment_type_expense(self):
        """نوع المصروف"""
        self.assertEqual(PaymentType.EXPENSE.value, "مصروف")

    def test_payment_type_income(self):
        """نوع الإيراد"""
        self.assertEqual(PaymentType.INCOME.value, "إيراد")

    def test_payment_type_refund(self):
        """نوع الاسترداد"""
        self.assertEqual(PaymentType.REFUND.value, "استرداد")


class TestPaymentMethodEnum(unittest.TestCase):
    """اختبارات تعداد طرق الدفع"""

    def test_payment_method_cash(self):
        """طريقة نقدي"""
        self.assertEqual(PaymentMethod.CASH.value, "نقدي")

    def test_payment_method_bank_transfer(self):
        """طريقة التحويل البنكي"""
        self.assertEqual(PaymentMethod.BANK_TRANSFER.value, "تحويل بنكي")

    def test_payment_method_check(self):
        """طريقة الشيك"""
        self.assertEqual(PaymentMethod.CHECK.value, "شيك")

    def test_payment_method_credit_card(self):
        """طريقة البطاقة الائتمانية"""
        self.assertEqual(PaymentMethod.CREDIT_CARD.value, "بطاقة ائتمان")

    def test_payment_method_debit_card(self):
        """طريقة بطاقة الخصم"""
        self.assertEqual(PaymentMethod.DEBIT_CARD.value, "بطاقة خصم")

    def test_payment_method_online(self):
        """طريقة الدفع الإلكتروني"""
        self.assertEqual(PaymentMethod.ONLINE.value, "دفع إلكتروني")


class TestPaymentStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات المدفوعات"""

    def test_payment_status_pending(self):
        """حالة معلق"""
        self.assertEqual(PaymentStatus.PENDING.value, "معلق")

    def test_payment_status_completed(self):
        """حالة مكتمل"""
        self.assertEqual(PaymentStatus.COMPLETED.value, "مكتمل")

    def test_payment_status_cancelled(self):
        """حالة ملغي"""
        self.assertEqual(PaymentStatus.CANCELLED.value, "ملغي")

    def test_payment_status_failed(self):
        """حالة فاشل"""
        self.assertEqual(PaymentStatus.FAILED.value, "فاشل")

    def test_payment_status_refunded(self):
        """حالة مسترد"""
        self.assertEqual(PaymentStatus.REFUNDED.value, "مسترد")


class TestAccountTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع الحسابات"""

    def test_account_type_receivable(self):
        """نوع ذمة مدينة"""
        self.assertEqual(AccountType.RECEIVABLE.value, "ذمة مدينة")

    def test_account_type_payable(self):
        """نوع ذمة دائنة"""
        self.assertEqual(AccountType.PAYABLE.value, "ذمة دائنة")

    def test_account_type_cash(self):
        """نوع نقدية"""
        self.assertEqual(AccountType.CASH.value, "نقدية")

    def test_account_type_bank(self):
        """نوع بنكي"""
        self.assertEqual(AccountType.BANK.value, "بنكي")


class TestPaymentCreation(unittest.TestCase):
    """اختبارات إنشاء دفعة"""

    def test_payment_basic_creation(self):
        """إنشاء دفعة أساسية"""
        payment = Payment(amount=Decimal("1000.00"), customer_id=1)
        self.assertEqual(payment.amount, Decimal("1000.00"))
        self.assertEqual(payment.customer_id, 1)

    def test_payment_default_type(self):
        """نوع الدفعة الافتراضي"""
        payment = Payment(amount=Decimal("1000.00"))
        self.assertEqual(payment.payment_type, PaymentType.CUSTOMER_PAYMENT.value)

    def test_payment_default_method(self):
        """طريقة الدفع الافتراضية"""
        payment = Payment(amount=Decimal("1000.00"))
        self.assertEqual(payment.payment_method, PaymentMethod.CASH.value)

    def test_payment_default_status(self):
        """حالة الدفعة الافتراضية"""
        payment = Payment(amount=Decimal("1000.00"))
        self.assertEqual(payment.status, PaymentStatus.PENDING.value)

    def test_payment_with_date(self):
        """دفعة مع تاريخ"""
        today = date.today()
        payment = Payment(amount=Decimal("1000.00"), payment_date=today)
        self.assertEqual(payment.payment_date, today)

    def test_payment_with_reference(self):
        """دفعة مع رقم مرجعي"""
        payment = Payment(amount=Decimal("1000.00"), reference_number="CHK12345")
        self.assertEqual(payment.reference_number, "CHK12345")

    def test_payment_with_bank_info(self):
        """دفعة مع معلومات بنكية"""
        payment = Payment(
            amount=Decimal("1000.00"),
            bank_name="بنك الجزائر",
            account_number="1234567890",
        )
        self.assertEqual(payment.bank_name, "بنك الجزائر")
        self.assertEqual(payment.account_number, "1234567890")


class TestPaymentGeneration(unittest.TestCase):
    """اختبارات توليد أرقام الدفعات"""

    def test_payment_number_generation(self):
        """توليد رقم الدفعة"""
        payment = Payment(amount=Decimal("1000.00"))
        self.assertIsNotNone(payment.payment_number)
        self.assertTrue(payment.payment_number.startswith("PAY-"))

    def test_payment_number_custom(self):
        """دفعة برقم مخصص"""
        payment = Payment(amount=Decimal("1000.00"), payment_number="PAY-CUSTOM-001")
        self.assertEqual(payment.payment_number, "PAY-CUSTOM-001")


class TestPaymentTypes(unittest.TestCase):
    """اختبارات أنواع المدفوعات"""

    def test_customer_payment(self):
        """دفعة عميل"""
        payment = Payment(
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CUSTOMER_PAYMENT.value,
            customer_id=1,
        )
        self.assertEqual(payment.payment_type, PaymentType.CUSTOMER_PAYMENT.value)
        self.assertEqual(payment.customer_id, 1)

    def test_supplier_payment(self):
        """دفعة مورد"""
        payment = Payment(
            amount=Decimal("1000.00"),
            payment_type=PaymentType.SUPPLIER_PAYMENT.value,
            supplier_id=1,
        )
        self.assertEqual(payment.payment_type, PaymentType.SUPPLIER_PAYMENT.value)
        self.assertEqual(payment.supplier_id, 1)

    def test_expense_payment(self):
        """دفعة مصروف"""
        payment = Payment(amount=Decimal("500.00"), payment_type=PaymentType.EXPENSE.value)
        self.assertEqual(payment.payment_type, PaymentType.EXPENSE.value)

    def test_income_payment(self):
        """دفعة إيراد"""
        payment = Payment(amount=Decimal("500.00"), payment_type=PaymentType.INCOME.value)
        self.assertEqual(payment.payment_type, PaymentType.INCOME.value)

    def test_refund_payment(self):
        """دفعة استرداد"""
        payment = Payment(amount=Decimal("200.00"), payment_type=PaymentType.REFUND.value)
        self.assertEqual(payment.payment_type, PaymentType.REFUND.value)


class TestPaymentMethods(unittest.TestCase):
    """اختبارات طرق الدفع"""

    def test_cash_payment(self):
        """دفع نقدي"""
        payment = Payment(amount=Decimal("1000.00"), payment_method=PaymentMethod.CASH.value)
        self.assertEqual(payment.payment_method, PaymentMethod.CASH.value)

    def test_bank_transfer_payment(self):
        """دفع بتحويل بنكي"""
        payment = Payment(
            amount=Decimal("1000.00"),
            payment_method=PaymentMethod.BANK_TRANSFER.value,
            bank_name="بنك الجزائر",
        )
        self.assertEqual(payment.payment_method, PaymentMethod.BANK_TRANSFER.value)

    def test_check_payment(self):
        """دفع بشيك"""
        payment = Payment(
            amount=Decimal("1000.00"),
            payment_method=PaymentMethod.CHECK.value,
            reference_number="CHECK-001",
        )
        self.assertEqual(payment.payment_method, PaymentMethod.CHECK.value)

    def test_credit_card_payment(self):
        """دفع ببطاقة ائتمان"""
        payment = Payment(amount=Decimal("1000.00"), payment_method=PaymentMethod.CREDIT_CARD.value)
        self.assertEqual(payment.payment_method, PaymentMethod.CREDIT_CARD.value)


class TestPaymentStatus(unittest.TestCase):
    """اختبارات حالات المدفوعات"""

    def test_payment_pending(self):
        """دفعة معلقة"""
        payment = Payment(amount=Decimal("1000.00"), status=PaymentStatus.PENDING.value)
        self.assertEqual(payment.status, PaymentStatus.PENDING.value)

    def test_payment_completed(self):
        """دفعة مكتملة"""
        payment = Payment(amount=Decimal("1000.00"), status=PaymentStatus.COMPLETED.value)
        self.assertEqual(payment.status, PaymentStatus.COMPLETED.value)

    def test_payment_cancelled(self):
        """دفعة ملغاة"""
        payment = Payment(amount=Decimal("1000.00"), status=PaymentStatus.CANCELLED.value)
        self.assertEqual(payment.status, PaymentStatus.CANCELLED.value)

    def test_payment_failed(self):
        """دفعة فاشلة"""
        payment = Payment(amount=Decimal("1000.00"), status=PaymentStatus.FAILED.value)
        self.assertEqual(payment.status, PaymentStatus.FAILED.value)

    def test_payment_refunded(self):
        """دفعة مسترجعة"""
        payment = Payment(amount=Decimal("1000.00"), status=PaymentStatus.REFUNDED.value)
        self.assertEqual(payment.status, PaymentStatus.REFUNDED.value)


class TestPaymentMultiCurrency(unittest.TestCase):
    """اختبارات الدفع بعملات متعددة"""

    def test_payment_with_currency(self):
        """دفعة بعملة محددة"""
        payment = Payment(amount=Decimal("1000.00"), currency_id=2, exchange_rate=Decimal("1.5"))
        self.assertEqual(payment.currency_id, 2)
        self.assertEqual(payment.exchange_rate, Decimal("1.5"))

    def test_payment_base_amount_calculation(self):
        """حساب المبلغ بالعملة الأساسية"""
        payment = Payment(amount=Decimal("1000.00"), currency_id=2, exchange_rate=Decimal("3.75"))
        expected = Decimal("1000.00") * Decimal("3.75")
        self.assertEqual(payment.amount_in_base_currency, expected)


class TestPaymentSerialization(unittest.TestCase):
    """اختبارات تسلسل بيانات الدفعة"""

    def test_payment_to_dict(self):
        """تحويل دفعة إلى قاموس"""
        payment = Payment(
            id=1,
            amount=Decimal("1000.00"),
            payment_type=PaymentType.CUSTOMER_PAYMENT.value,
            customer_id=1,
        )
        payment_dict = payment.to_dict()

        self.assertEqual(payment_dict["id"], 1)
        self.assertEqual(payment_dict["amount"], 1000.0)
        self.assertEqual(payment_dict["payment_type"], PaymentType.CUSTOMER_PAYMENT.value)
        self.assertEqual(payment_dict["customer_id"], 1)

    def test_payment_to_dict_with_dates(self):
        """تحويل دفعة مع تواريخ"""
        today = date.today()
        payment = Payment(amount=Decimal("1000.00"), payment_date=today)
        payment_dict = payment.to_dict()

        self.assertEqual(payment_dict["payment_date"], today.isoformat())


class TestPaymentEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدية"""

    def test_payment_zero_amount(self):
        """دفعة بمبلغ صفر"""
        payment = Payment(amount=Decimal("0.00"))
        self.assertEqual(payment.amount, Decimal("0.00"))

    def test_payment_large_amount(self):
        """دفعة بمبلغ كبير"""
        payment = Payment(amount=Decimal("999999.99"))
        self.assertEqual(payment.amount, Decimal("999999.99"))

    def test_payment_with_notes(self):
        """دفعة مع ملاحظات"""
        payment = Payment(amount=Decimal("1000.00"), notes="دفعة لفاتورة رقم 001")
        self.assertEqual(payment.notes, "دفعة لفاتورة رقم 001")

    def test_payment_with_attachments(self):
        """دفعة مع ملفات مرفقة"""
        payment = Payment(amount=Decimal("1000.00"), attachments=["file1.pdf", "file2.jpg"])
        self.assertEqual(len(payment.attachments), 2)

    def test_payment_timestamps(self):
        """دفعة مع الطوابع الزمنية"""
        payment = Payment(amount=Decimal("1000.00"))
        self.assertIsNotNone(payment.created_at)
        self.assertIsNotNone(payment.updated_at)

    def test_payment_with_related_invoice(self):
        """دفعة مرتبطة بفاتورة"""
        payment = Payment(
            amount=Decimal("1000.00"),
            sale_id=1,
            payment_type=PaymentType.CUSTOMER_PAYMENT.value,
        )
        self.assertEqual(payment.sale_id, 1)

    def test_payment_with_related_purchase(self):
        """دفعة مرتبطة بفاتورة شراء"""
        payment = Payment(
            amount=Decimal("1000.00"),
            purchase_id=1,
            payment_type=PaymentType.SUPPLIER_PAYMENT.value,
        )
        self.assertEqual(payment.purchase_id, 1)

    def test_payment_with_cost_center(self):
        """دفعة مع مركز تكلفة"""
        payment = Payment(amount=Decimal("1000.00"), cost_center="CC-001")
        self.assertEqual(payment.cost_center, "CC-001")


if __name__ == "__main__":
    unittest.main()

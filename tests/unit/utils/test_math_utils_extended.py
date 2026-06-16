"""
اختبارات شاملة لوحدة math_utils
تغطي التحويل إلى Decimal والحسابات المالية الأساسية
"""

import unittest
from decimal import Decimal

from src.utils import math_utils


class TestToDecimal(unittest.TestCase):
    """اختبارات التحويل إلى Decimal"""

    def test_int_and_float(self):
        self.assertEqual(math_utils.to_decimal(100), Decimal("100"))
        self.assertEqual(math_utils.to_decimal(100.5), Decimal("100.5"))

    def test_string_normal(self):
        self.assertEqual(math_utils.to_decimal("123.45"), Decimal("123.45"))

    def test_string_with_currency_and_commas(self):
        self.assertEqual(math_utils.to_decimal("1,234.56 د.ج"), Decimal("1234.56"))
        self.assertEqual(math_utils.to_decimal("1،234.56 د.ج"), Decimal("1234.56"))

    def test_string_negative(self):
        self.assertEqual(math_utils.to_decimal("-99.99"), Decimal("-99.99"))

    def test_invalid_inputs(self):
        self.assertEqual(math_utils.to_decimal(None), Decimal("0.00"))
        self.assertEqual(math_utils.to_decimal("abc"), Decimal("0.00"))
        self.assertEqual(math_utils.to_decimal("--"), Decimal("0.00"))


class TestCalculateLineTotal(unittest.TestCase):
    """اختبارات إجمالي السطر"""

    def test_basic_total(self):
        result = math_utils.calculate_line_total(100, 2, 0, 15)
        self.assertEqual(result, Decimal("230.00"))

    def test_with_discount(self):
        result = math_utils.calculate_line_total(50, 3, 20, 10)
        # subtotal 150 - discount 20 = 130; tax 13 => 143
        self.assertEqual(result, Decimal("143.00"))

    def test_no_tax(self):
        result = math_utils.calculate_line_total(10, 5, 0, 0)
        self.assertEqual(result, Decimal("50.00"))

    def test_negative_discount_clamped(self):
        result = math_utils.calculate_line_total(10, 1, 20, 0)
        self.assertEqual(result, Decimal("0.00"))


class TestCalculateSubtotal(unittest.TestCase):
    """اختبارات الإجمالي الفرعي"""

    def test_mixed_items(self):
        items = [Decimal("10.00"), {"total": "20.50"}, {"total_price": 5}, 3]
        self.assertEqual(math_utils.calculate_subtotal(items), Decimal("38.50"))

    def test_object_like(self):
        class Obj:
            def __init__(self, total):
                self.total = total

        items = [Obj("10.00"), Obj("5.25")]
        self.assertEqual(math_utils.calculate_subtotal(items), Decimal("15.25"))


class TestDiscountAmount(unittest.TestCase):
    """اختبارات حساب الخصم"""

    def test_percentage_flag(self):
        self.assertEqual(
            math_utils.calculate_discount_amount(200, discount=10, is_percentage=True),
            Decimal("20.00"),
        )

    def test_fixed_discount(self):
        self.assertEqual(
            math_utils.calculate_discount_amount(100, discount=30, is_percentage=False),
            Decimal("30.00"),
        )

    def test_legacy_percentage(self):
        self.assertEqual(
            math_utils.calculate_discount_amount(100, discount_percentage=15),
            Decimal("15.00"),
        )

    def test_legacy_amount(self):
        self.assertEqual(
            math_utils.calculate_discount_amount(100, discount_amount=120),
            Decimal("100.00"),
        )


class TestTaxAndGrandTotal(unittest.TestCase):
    """اختبارات الضريبة والإجمالي النهائي"""

    def test_tax_amount_percent(self):
        self.assertEqual(
            math_utils.calculate_tax_amount(200, discount_amount=20, tax_rate=10),
            Decimal("18.00"),
        )

    def test_tax_amount_decimal_rate(self):
        self.assertEqual(
            math_utils.calculate_tax_amount(100, discount_amount=0, tax_rate=Decimal("0.15")),
            Decimal("15.00"),
        )

    def test_grand_total(self):
        self.assertEqual(
            math_utils.calculate_grand_total(Decimal("200.00"), Decimal("20.00"), Decimal("18.00")),
            Decimal("198.00"),
        )


class TestFormatAndDivide(unittest.TestCase):
    """اختبارات تنسيق العملات والقسمة الآمنة"""

    def test_format_currency_default(self):
        self.assertEqual(math_utils.format_currency(1000.5), "1,000.50 دج")

    def test_format_currency_custom(self):
        self.assertEqual(math_utils.format_currency("1234.567", "USD", 2), "1,234.57 USD")

    def test_safe_divide_normal(self):
        self.assertEqual(math_utils.safe_divide(100, 4), Decimal("25.00"))

    def test_safe_divide_zero(self):
        self.assertEqual(math_utils.safe_divide(10, 0, default=Decimal("-1.00")), Decimal("-1.00"))


if __name__ == "__main__":
    unittest.main()

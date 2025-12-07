"""
Unit Tests for Math Utils
اختبارات وحدة لأدوات الرياضيات
"""

import pytest
from decimal import Decimal
from src.utils.math_utils import (
    to_decimal,
    calculate_line_total,
    calculate_subtotal,
    calculate_discount_amount,
    calculate_tax_amount,
    calculate_grand_total
)


class TestToDecimal:
    """اختبارات دالة to_decimal"""
    
    def test_int_to_decimal(self):
        """اختبار تحويل int إلى Decimal"""
        assert to_decimal(100) == Decimal('100')
        assert to_decimal(0) == Decimal('0')
        assert to_decimal(-50) == Decimal('-50')
    
    def test_float_to_decimal(self):
        """اختبار تحويل float إلى Decimal"""
        assert to_decimal(100.5) == Decimal('100.5')
        assert to_decimal(0.0) == Decimal('0')
        assert to_decimal(-50.25) == Decimal('-50.25')
    
    def test_string_to_decimal(self):
        """اختبار تحويل string إلى Decimal"""
        assert to_decimal("100") == Decimal('100')
        assert to_decimal("100.50") == Decimal('100.50')
        assert to_decimal("0") == Decimal('0')
    
    def test_string_with_currency_to_decimal(self):
        """اختبار تحويل string مع عملة إلى Decimal"""
        assert to_decimal("100.00 د.ج") == Decimal('100.00')
        assert to_decimal("1,234.56 د.ج") == Decimal('1234.56')
    
    def test_none_to_decimal(self):
        """اختبار تحويل None إلى Decimal"""
        assert to_decimal(None) == Decimal('0')
    
    def test_empty_string_to_decimal(self):
        """اختبار تحويل string فارغ إلى Decimal"""
        assert to_decimal("") == Decimal('0')
        assert to_decimal("   ") == Decimal('0')


class TestCalculateLineTotal:
    """اختبارات حساب إجمالي السطر"""
    
    def test_calculate_line_total_basic(self):
        """اختبار حساب إجمالي سطر أساسي"""
        price = Decimal('100')  # سعر الوحدة
        quantity = Decimal('5')  # الكمية
        discount = Decimal('10')  # الخصم
        
        result = calculate_line_total(price, quantity, discount)
        assert result == Decimal('490.00')  # (5 * 100) - 10 = 490 (بدون ضريبة)
    
    def test_calculate_line_total_no_discount(self):
        """اختبار حساب إجمالي سطر بدون خصم"""
        quantity = Decimal('3')
        unit_price = Decimal('50')
        discount = Decimal('0')
        
        result = calculate_line_total(quantity, unit_price, discount)
        assert result == Decimal('150.00')
    
    def test_calculate_line_total_zero_quantity(self):
        """اختبار حساب إجمالي سطر بكمية صفر"""
        quantity = Decimal('0')
        unit_price = Decimal('100')
        discount = Decimal('0')
        
        result = calculate_line_total(quantity, unit_price, discount)
        assert result == Decimal('0.00')


class TestCalculateSubtotal:
    """اختبارات حساب المجموع الفرعي"""
    
    def test_calculate_subtotal_basic(self):
        """اختبار حساب المجموع الفرعي الأساسي"""
        line_totals = [
            Decimal('100.00'),
            Decimal('200.00'),
            Decimal('300.00')
        ]
        
        result = calculate_subtotal(line_totals)
        assert result == Decimal('600.00')
    
    def test_calculate_subtotal_empty(self):
        """اختبار حساب المجموع الفرعي لقائمة فارغة"""
        result = calculate_subtotal([])
        assert result == Decimal('0.00')
    
    def test_calculate_subtotal_single_item(self):
        """اختبار حساب المجموع الفرعي لعنصر واحد"""
        result = calculate_subtotal([Decimal('150.50')])
        assert result == Decimal('150.50')


class TestCalculateDiscountAmount:
    """اختبارات حساب مبلغ الخصم"""
    
    def test_calculate_discount_percentage(self):
        """اختبار حساب الخصم كنسبة مئوية"""
        subtotal = Decimal('1000.00')
        discount = Decimal('10')  # 10%
        
        result = calculate_discount_amount(subtotal, discount, is_percentage=True)
        assert result == Decimal('100.00')
    
    def test_calculate_discount_fixed_amount(self):
        """اختبار حساب الخصم كمبلغ ثابت"""
        subtotal = Decimal('1000.00')
        discount = Decimal('50')
        
        result = calculate_discount_amount(subtotal, discount, is_percentage=False)
        assert result == Decimal('50.00')
    
    def test_calculate_discount_zero(self):
        """اختبار حساب الخصم بصفر"""
        result = calculate_discount_amount(Decimal('1000'), Decimal('0'))
        assert result == Decimal('0.00')


class TestCalculateTaxAmount:
    """اختبارات حساب الضريبة"""
    
    def test_calculate_tax_basic(self):
        """اختبار حساب الضريبة الأساسي"""
        subtotal = Decimal('1000.00')
        discount_amount = Decimal('100.00')
        tax_rate = Decimal('15')  # 15% (كنسبة مئوية)
        
        result = calculate_tax_amount(subtotal, discount_amount, tax_rate)
        assert result == Decimal('135.00')  # (1000 - 100) * 15% = 135
    
    def test_calculate_tax_zero_rate(self):
        """اختبار حساب الضريبة بمعدل صفر"""
        result = calculate_tax_amount(Decimal('1000'), Decimal('0'), Decimal('0'))
        assert result == Decimal('0.00')
    
    def test_calculate_tax_with_decimal_rate(self):
        """اختبار حساب الضريبة بنسبة عشرية (0.15 = 15%)"""
        result = calculate_tax_amount(Decimal('1000'), Decimal('0'), Decimal('0.15'))
        assert result == Decimal('150.00')  # 1000 * 0.15 = 150


class TestCalculateGrandTotal:
    """اختبارات حساب الإجمالي النهائي"""
    
    def test_calculate_grand_total_complete(self):
        """اختبار حساب الإجمالي النهائي الكامل"""
        subtotal = Decimal('1000.00')
        discount_amount = Decimal('100.00')
        tax_amount = Decimal('135.00')
        
        result = calculate_grand_total(subtotal, discount_amount, tax_amount)
        assert result == Decimal('1035.00')  # 1000 - 100 + 135
    
    def test_calculate_grand_total_no_discount(self):
        """اختبار حساب الإجمالي النهائي بدون خصم"""
        result = calculate_grand_total(Decimal('1000'), Decimal('0'), Decimal('150'))
        assert result == Decimal('1150.00')


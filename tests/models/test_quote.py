#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج عروض الأسعار - Quote Model Tests
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from src.models.quote import Quote, QuoteItem, QuoteStatus


class TestQuoteStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات عرض السعر"""
    
    def test_quote_status_values(self):
        """اختبار قيم حالات عرض السعر"""
        self.assertEqual(QuoteStatus.DRAFT.value, "مسودة")
        self.assertEqual(QuoteStatus.SENT.value, "مرسل")
        self.assertEqual(QuoteStatus.ACCEPTED.value, "مقبول")
        self.assertEqual(QuoteStatus.REJECTED.value, "مرفوض")
        self.assertEqual(QuoteStatus.EXPIRED.value, "منتهي")
        self.assertEqual(QuoteStatus.CONVERTED.value, "محول")
        self.assertEqual(QuoteStatus.CANCELLED.value, "ملغي")
    
    def test_all_quote_statuses(self):
        """اختبار وجود جميع الحالات"""
        statuses = [QuoteStatus.DRAFT, QuoteStatus.SENT, QuoteStatus.ACCEPTED,
                   QuoteStatus.REJECTED, QuoteStatus.EXPIRED, QuoteStatus.CONVERTED,
                   QuoteStatus.CANCELLED]
        
        self.assertEqual(len(statuses), 7)


class TestQuoteItemCreation(unittest.TestCase):
    """اختبارات إنشاء بند عرض السعر"""
    
    def test_quote_item_default_values(self):
        """اختبار القيم الافتراضية لبند العرض"""
        item = QuoteItem()
        
        self.assertIsNone(item.id)
        self.assertIsNone(item.quote_id)
        self.assertEqual(item.product_id, 0)
        self.assertEqual(item.quantity, Decimal('1'))
        self.assertEqual(item.unit_price, Decimal('0.00'))
        self.assertEqual(item.tax_percentage, Decimal('15.00'))
    
    def test_quote_item_with_values(self):
        """اختبار إنشاء بند مع قيم"""
        item = QuoteItem(
            product_id=1,
            product_name="منتج اختبار",
            quantity=Decimal('5'),
            unit_price=Decimal('100.00')
        )
        
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج اختبار")
        self.assertEqual(item.quantity, Decimal('5'))
        self.assertEqual(item.unit_price, Decimal('100.00'))
    
    def test_quote_item_decimal_conversion(self):
        """اختبار تحويل القيم إلى Decimal"""
        item = QuoteItem(
            quantity=5,
            unit_price=100
        )
        
        self.assertIsInstance(item.quantity, Decimal)
        self.assertIsInstance(item.unit_price, Decimal)


class TestQuoteItemCalculations(unittest.TestCase):
    """اختبارات حسابات بند عرض السعر"""
    
    def test_quote_item_subtotal(self):
        """اختبار حساب المجموع الفرعي"""
        item = QuoteItem(
            quantity=Decimal('5'),
            unit_price=Decimal('100.00')
        )
        
        self.assertEqual(item.subtotal, Decimal('500.00'))
    
    def test_quote_item_net_amount(self):
        """اختبار حساب المبلغ الصافي"""
        item = QuoteItem(
            quantity=Decimal('5'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('50.00')
        )
        
        self.assertEqual(item.net_amount, Decimal('450.00'))
    
    def test_quote_item_calculate_totals_with_discount(self):
        """اختبار حساب المجاميع مع الخصم"""
        item = QuoteItem(
            quantity=Decimal('10'),
            unit_price=Decimal('100.00'),
            discount_percentage=Decimal('10'),
            tax_percentage=Decimal('15')
        )
        
        item.calculate_totals()
        
        # Subtotal: 1000.00
        # Discount: 100.00
        # Net: 900.00
        # Tax: 135.00
        # Total: 1035.00
        self.assertEqual(item.subtotal, Decimal('1000.00'))
        self.assertEqual(item.discount_amount, Decimal('100.00'))
        self.assertEqual(item.net_amount, Decimal('900.00'))
        self.assertGreater(item.tax_amount, Decimal('0'))
    
    def test_quote_item_to_dict(self):
        """اختبار تحويل البند إلى قاموس"""
        item = QuoteItem(
            id=1,
            product_id=1,
            product_name="Test",
            quantity=Decimal('5'),
            unit_price=Decimal('100.00')
        )
        
        item_dict = item.to_dict()
        
        self.assertEqual(item_dict['id'], 1)
        self.assertEqual(item_dict['product_id'], 1)
        self.assertEqual(item_dict['quantity'], 5.0)
        self.assertEqual(item_dict['unit_price'], 100.0)


class TestQuoteCreation(unittest.TestCase):
    """اختبارات إنشاء عرض السعر"""
    
    def test_quote_creation_default_values(self):
        """اختبار إنشاء عرض بالقيم الافتراضية"""
        quote = Quote()
        
        self.assertIsNone(quote.id)
        self.assertEqual(quote.quote_number, "")
        self.assertEqual(quote.status, QuoteStatus.DRAFT)
        self.assertEqual(quote.items, [])
        self.assertEqual(quote.total_amount, Decimal('0.00'))
    
    def test_quote_creation_with_values(self):
        """اختبار إنشاء عرض مع قيم"""
        today = date.today()
        quote = Quote(
            id=1,
            quote_number="QT001",
            customer_id=1,
            customer_name="عميل اختبار",
            quote_date=today,
            status=QuoteStatus.SENT
        )
        
        self.assertEqual(quote.id, 1)
        self.assertEqual(quote.quote_number, "QT001")
        self.assertEqual(quote.customer_name, "عميل اختبار")
        self.assertEqual(quote.status, QuoteStatus.SENT)
    
    def test_quote_with_items(self):
        """اختبار عرض مع بنود"""
        quote = Quote(quote_number="QT001")
        item = QuoteItem(product_id=1, quantity=Decimal('5'), unit_price=Decimal('100'))
        quote.add_item(item)
        
        self.assertEqual(len(quote.items), 1)
        self.assertEqual(quote.items[0].product_id, 1)


class TestQuoteValidity(unittest.TestCase):
    """اختبارات صحة عرض السعر"""
    
    def test_quote_is_valid_no_expiry_date(self):
        """اختبار أن العرض بدون تاريخ انتهاء صلاحية يكون صالحاً"""
        quote = Quote(quote_number="QT001")
        
        self.assertTrue(quote.is_valid)
        self.assertFalse(quote.is_expired)
    
    def test_quote_is_valid_future_date(self):
        """اختبار عرض بتاريخ انتهاء صلاحية في المستقبل"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            valid_until=future_date
        )
        
        self.assertTrue(quote.is_valid)
        self.assertFalse(quote.is_expired)
    
    def test_quote_is_expired(self):
        """اختبار عرض منتهي الصلاحية"""
        past_date = date.today() - timedelta(days=1)
        quote = Quote(
            quote_number="QT001",
            valid_until=past_date
        )
        
        self.assertFalse(quote.is_valid)
        self.assertTrue(quote.is_expired)
    
    def test_quote_days_until_expiry(self):
        """اختبار عدد الأيام حتى انتهاء الصلاحية"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            valid_until=future_date
        )
        
        self.assertEqual(quote.days_until_expiry, 30)
    
    def test_quote_days_until_expiry_no_date(self):
        """اختبار عدد الأيام عندما لا يكون هناك تاريخ انتهاء"""
        quote = Quote(quote_number="QT001")
        
        self.assertIsNone(quote.days_until_expiry)


class TestQuoteConversion(unittest.TestCase):
    """اختبارات تحويل عرض السعر"""
    
    def test_can_be_converted_accepted_status(self):
        """اختبار إمكانية التحويل عندما تكون الحالة مقبول"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.ACCEPTED,
            valid_until=future_date
        )
        
        # إضافة عنصر واحد على الأقل
        quote.items = [QuoteItem(product_id=1)]
        
        self.assertTrue(quote.can_be_converted)
    
    def test_cannot_convert_expired_quote(self):
        """اختبار عدم إمكانية تحويل عرض منتهي الصلاحية"""
        past_date = date.today() - timedelta(days=1)
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.ACCEPTED,
            valid_until=past_date
        )
        
        self.assertFalse(quote.can_be_converted)
    
    def test_cannot_convert_draft_quote(self):
        """اختبار عدم إمكانية تحويل عرض في حالة مسودة"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.DRAFT,
            valid_until=future_date
        )
        
        self.assertFalse(quote.can_be_converted)
    
    def test_cannot_convert_already_converted_quote(self):
        """اختبار عدم إمكانية تحويل عرض تم تحويله مسبقاً"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.ACCEPTED,
            valid_until=future_date,
            converted_to_sale_id=1
        )
        
        self.assertFalse(quote.can_be_converted)
    
    def test_cannot_convert_quote_without_items(self):
        """اختبار عدم إمكانية تحويل عرض بدون بنود"""
        future_date = date.today() + timedelta(days=30)
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.ACCEPTED,
            valid_until=future_date,
            items=[]
        )
        
        self.assertFalse(quote.can_be_converted)


class TestQuoteAddItem(unittest.TestCase):
    """اختبارات إضافة بنود للعرض"""
    
    def test_add_single_item(self):
        """اختبار إضافة بند واحد"""
        quote = Quote(id=1, quote_number="QT001")
        item = QuoteItem(product_id=1, quantity=Decimal('5'), unit_price=Decimal('100'))
        
        quote.add_item(item)
        
        self.assertEqual(len(quote.items), 1)
        self.assertEqual(quote.items[0].quote_id, 1)
    
    def test_add_multiple_items(self):
        """اختبار إضافة عدة بنود"""
        quote = Quote(id=1, quote_number="QT001")
        
        for i in range(3):
            item = QuoteItem(
                product_id=i+1,
                quantity=Decimal('5'),
                unit_price=Decimal('100')
            )
            quote.add_item(item)
        
        self.assertEqual(len(quote.items), 3)
    
    def test_item_calculates_totals_on_add(self):
        """اختبار أن البند يحسب المجاميع عند الإضافة"""
        quote = Quote(quote_number="QT001")
        item = QuoteItem(
            product_id=1,
            quantity=Decimal('10'),
            unit_price=Decimal('100'),
            discount_percentage=Decimal('10'),
            tax_percentage=Decimal('15')
        )
        
        quote.add_item(item)
        
        # التحقق من أن المجاميع تم حسابها
        self.assertGreater(quote.items[0].tax_amount, Decimal('0'))


class TestQuoteStatus(unittest.TestCase):
    """اختبارات حالات عرض السعر المختلفة"""
    
    def test_draft_quote(self):
        """اختبار عرض في حالة مسودة"""
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.DRAFT
        )
        
        self.assertEqual(quote.status, QuoteStatus.DRAFT)
    
    def test_sent_quote(self):
        """اختبار عرض مرسول"""
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.SENT,
            sent_date=date.today()
        )
        
        self.assertEqual(quote.status, QuoteStatus.SENT)
        self.assertIsNotNone(quote.sent_date)
    
    def test_accepted_quote(self):
        """اختبار عرض مقبول"""
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.ACCEPTED,
            response_date=date.today()
        )
        
        self.assertEqual(quote.status, QuoteStatus.ACCEPTED)
    
    def test_rejected_quote(self):
        """اختبار عرض مرفوض"""
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.REJECTED,
            response_date=date.today()
        )
        
        self.assertEqual(quote.status, QuoteStatus.REJECTED)
    
    def test_converted_quote(self):
        """اختبار عرض تم تحويله"""
        quote = Quote(
            quote_number="QT001",
            status=QuoteStatus.CONVERTED,
            converted_to_sale_id=1,
            converted_date=date.today()
        )
        
        self.assertEqual(quote.status, QuoteStatus.CONVERTED)
        self.assertEqual(quote.converted_to_sale_id, 1)


class TestQuoteCustomerInfo(unittest.TestCase):
    """اختبارات معلومات العميل في العرض"""
    
    def test_quote_customer_details(self):
        """اختبار تفاصيل العميل"""
        quote = Quote(
            quote_number="QT001",
            customer_id=1,
            customer_name="محمد علي",
            customer_phone="0123456789",
            customer_email="customer@example.com",
            customer_address="شارع النيل"
        )
        
        self.assertEqual(quote.customer_id, 1)
        self.assertEqual(quote.customer_name, "محمد علي")
        self.assertEqual(quote.customer_phone, "0123456789")
        self.assertEqual(quote.customer_email, "customer@example.com")
        self.assertEqual(quote.customer_address, "شارع النيل")


class TestQuoteTerms(unittest.TestCase):
    """اختبارات شروط العرض"""
    
    def test_quote_payment_terms(self):
        """اختبار شروط الدفع"""
        quote = Quote(
            quote_number="QT001",
            payment_terms="الدفع عند التسليم"
        )
        
        self.assertEqual(quote.payment_terms, "الدفع عند التسليم")
    
    def test_quote_delivery_terms(self):
        """اختبار شروط التسليم"""
        quote = Quote(
            quote_number="QT001",
            delivery_terms="التسليم خلال 7 أيام"
        )
        
        self.assertEqual(quote.delivery_terms, "التسليم خلال 7 أيام")
    
    def test_quote_terms_and_conditions(self):
        """اختبار الشروط والأحكام"""
        quote = Quote(
            quote_number="QT001",
            terms_and_conditions="شروط قياسية"
        )
        
        self.assertEqual(quote.terms_and_conditions, "شروط قياسية")


class TestQuoteNotes(unittest.TestCase):
    """اختبارات ملاحظات العرض"""
    
    def test_quote_notes(self):
        """اختبار الملاحظات العامة"""
        quote = Quote(
            quote_number="QT001",
            notes="ملاحظات عامة للعميل"
        )
        
        self.assertEqual(quote.notes, "ملاحظات عامة للعميل")
    
    def test_quote_internal_notes(self):
        """اختبار الملاحظات الداخلية"""
        quote = Quote(
            quote_number="QT001",
            internal_notes="ملاحظات داخلية لا يراها العميل"
        )
        
        self.assertEqual(quote.internal_notes, "ملاحظات داخلية لا يراها العميل")


class TestQuoteEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_quote_with_zero_total(self):
        """اختبار عرض بمجموع صفر"""
        quote = Quote(
            quote_number="QT001",
            total_amount=Decimal('0.00')
        )
        
        self.assertEqual(quote.total_amount, Decimal('0.00'))
    
    def test_quote_with_large_amounts(self):
        """اختبار عرض بمبالغ كبيرة"""
        quote = Quote(
            quote_number="QT001",
            total_amount=Decimal('999999.99'),
            subtotal=Decimal('999999.99')
        )
        
        self.assertEqual(quote.total_amount, Decimal('999999.99'))
    
    def test_quote_item_with_100_percent_discount(self):
        """اختبار بند مع خصم 100%"""
        item = QuoteItem(
            product_id=1,
            quantity=Decimal('10'),
            unit_price=Decimal('100'),
            discount_percentage=Decimal('100')
        )
        
        item.calculate_totals()
        
        # بعد الخصم يجب أن يكون صفر
        self.assertEqual(item.net_amount, Decimal('0.00'))
    
    def test_quote_today_expiry(self):
        """اختبار عرض ينتهي اليوم"""
        today = date.today()
        quote = Quote(
            quote_number="QT001",
            valid_until=today
        )
        
        self.assertTrue(quote.is_valid)
        self.assertEqual(quote.days_until_expiry, 0)


if __name__ == '__main__':
    unittest.main()




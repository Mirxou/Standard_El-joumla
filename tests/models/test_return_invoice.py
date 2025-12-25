#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج المرتجعات - Return Invoice Model Tests
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from src.models.return_invoice import (
    ReturnType, ReturnReason, ReturnStatus, RefundMethod, ReturnItem
)


class TestReturnTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع المرتجعات"""
    
    def test_return_type_values(self):
        """اختبار قيم أنواع المرتجعات"""
        self.assertEqual(ReturnType.SALE_RETURN.value, "مرتجع مبيعات")
        self.assertEqual(ReturnType.PURCHASE_RETURN.value, "مرتجع مشتريات")
    
    def test_all_return_types(self):
        """اختبار عدد جميع الأنواع"""
        types = list(ReturnType)
        self.assertEqual(len(types), 2)


class TestReturnReasonEnum(unittest.TestCase):
    """اختبارات تعداد أسباب المرتجعات"""
    
    def test_return_reason_values(self):
        """اختبار قيم أسباب المرتجعات"""
        self.assertEqual(ReturnReason.DEFECTIVE.value, "معيب")
        self.assertEqual(ReturnReason.DAMAGED.value, "تالف")
        self.assertEqual(ReturnReason.WRONG_ITEM.value, "منتج خاطئ")
        self.assertEqual(ReturnReason.EXPIRED.value, "منتهي الصلاحية")
        self.assertEqual(ReturnReason.NOT_AS_DESCRIBED.value, "مخالف للوصف")
        self.assertEqual(ReturnReason.CUSTOMER_REQUEST.value, "طلب العميل")
        self.assertEqual(ReturnReason.OVERSTOCK.value, "فائض مخزون")
        self.assertEqual(ReturnReason.OTHER.value, "أخرى")
    
    def test_all_return_reasons(self):
        """اختبار عدد جميع الأسباب"""
        reasons = list(ReturnReason)
        self.assertEqual(len(reasons), 8)


class TestReturnStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات المرتجعات"""
    
    def test_return_status_values(self):
        """اختبار قيم حالات المرتجعات"""
        self.assertEqual(ReturnStatus.PENDING.value, "معلق")
        self.assertEqual(ReturnStatus.APPROVED.value, "موافق عليه")
        self.assertEqual(ReturnStatus.REJECTED.value, "مرفوض")
        self.assertEqual(ReturnStatus.COMPLETED.value, "مكتمل")
        self.assertEqual(ReturnStatus.CANCELLED.value, "ملغي")
    
    def test_all_return_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(ReturnStatus)
        self.assertEqual(len(statuses), 5)


class TestRefundMethodEnum(unittest.TestCase):
    """اختبارات تعداد طرق الاسترداد"""
    
    def test_refund_method_values(self):
        """اختبار قيم طرق الاسترداد"""
        self.assertEqual(RefundMethod.CASH.value, "نقدي")
        self.assertEqual(RefundMethod.CREDIT_NOTE.value, "إشعار دائن")
        self.assertEqual(RefundMethod.EXCHANGE.value, "استبدال")
        self.assertEqual(RefundMethod.BANK_TRANSFER.value, "تحويل بنكي")
        self.assertEqual(RefundMethod.STORE_CREDIT.value, "رصيد المتجر")
    
    def test_all_refund_methods(self):
        """اختبار عدد جميع طرق الاسترداد"""
        methods = list(RefundMethod)
        self.assertEqual(len(methods), 5)


class TestReturnItemCreation(unittest.TestCase):
    """اختبارات إنشاء بند المرتجعات"""
    
    def test_return_item_default_values(self):
        """اختبار القيم الافتراضية لبند المرتجع"""
        item = ReturnItem()
        
        self.assertIsNone(item.id)
        self.assertIsNone(item.return_id)
        self.assertEqual(item.product_id, 0)
        self.assertEqual(item.quantity_returned, Decimal('0'))
        self.assertEqual(item.quantity_original, Decimal('0'))
        self.assertTrue(item.restockable)
    
    def test_return_item_with_values(self):
        """اختبار إنشاء بند مع قيم"""
        item = ReturnItem(
            product_id=1,
            product_name="منتج مرتجع",
            quantity_returned=Decimal('5'),
            unit_price=Decimal('100.00'),
            return_reason=ReturnReason.DEFECTIVE
        )
        
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج مرتجع")
        self.assertEqual(item.quantity_returned, Decimal('5'))
        self.assertEqual(item.return_reason, ReturnReason.DEFECTIVE)


class TestReturnItemQuantities(unittest.TestCase):
    """اختبارات كميات المرتجعات"""
    
    def test_return_item_quantities(self):
        """اختبار الكميات"""
        item = ReturnItem(
            quantity_returned=Decimal('5'),
            quantity_original=Decimal('10')
        )
        
        self.assertEqual(item.quantity_returned, Decimal('5'))
        self.assertEqual(item.quantity_original, Decimal('10'))
    
    def test_return_item_partial_return(self):
        """اختبار الإرجاع الجزئي"""
        item = ReturnItem(
            quantity_returned=Decimal('3'),
            quantity_original=Decimal('10')
        )
        
        self.assertLess(item.quantity_returned, item.quantity_original)
    
    def test_return_item_full_return(self):
        """اختبار الإرجاع الكامل"""
        item = ReturnItem(
            quantity_returned=Decimal('10'),
            quantity_original=Decimal('10')
        )
        
        self.assertEqual(item.quantity_returned, item.quantity_original)
    
    def test_return_item_decimal_quantities(self):
        """اختبار كميات عشرية"""
        item = ReturnItem(
            quantity_returned=Decimal('2.5'),
            quantity_original=Decimal('5.0')
        )
        
        self.assertEqual(item.quantity_returned, Decimal('2.5'))


class TestReturnItemPricing(unittest.TestCase):
    """اختبارات تسعير بنود المرتجعات"""
    
    def test_return_item_unit_price(self):
        """اختبار سعر الوحدة"""
        item = ReturnItem(
            quantity_returned=Decimal('5'),
            unit_price=Decimal('100.00')
        )
        
        self.assertEqual(item.unit_price, Decimal('100.00'))
    
    def test_return_item_discount(self):
        """اختبار الخصم"""
        item = ReturnItem(
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('50.00')
        )
        
        self.assertEqual(item.discount_amount, Decimal('50.00'))
    
    def test_return_item_tax(self):
        """اختبار الضريبة"""
        item = ReturnItem(
            unit_price=Decimal('100.00'),
            tax_amount=Decimal('15.00')
        )
        
        self.assertEqual(item.tax_amount, Decimal('15.00'))
    
    def test_return_item_total_amount(self):
        """اختبار المبلغ الإجمالي"""
        item = ReturnItem(
            quantity_returned=Decimal('5'),
            unit_price=Decimal('100.00'),
            total_amount=Decimal('500.00')
        )
        
        self.assertEqual(item.total_amount, Decimal('500.00'))


class TestReturnItemReason(unittest.TestCase):
    """اختبارات أسباب الإرجاع"""
    
    def test_return_item_defective_reason(self):
        """اختبار سبب الإرجاع: معيب"""
        item = ReturnItem(
            product_id=1,
            return_reason=ReturnReason.DEFECTIVE
        )
        
        self.assertEqual(item.return_reason, ReturnReason.DEFECTIVE)
    
    def test_return_item_damaged_reason(self):
        """اختبار سبب الإرجاع: تالف"""
        item = ReturnItem(
            product_id=1,
            return_reason=ReturnReason.DAMAGED
        )
        
        self.assertEqual(item.return_reason, ReturnReason.DAMAGED)
    
    def test_return_item_wrong_item_reason(self):
        """اختبار سبب الإرجاع: منتج خاطئ"""
        item = ReturnItem(
            product_id=1,
            return_reason=ReturnReason.WRONG_ITEM
        )
        
        self.assertEqual(item.return_reason, ReturnReason.WRONG_ITEM)
    
    def test_return_item_expired_reason(self):
        """اختبار سبب الإرجاع: منتهي الصلاحية"""
        item = ReturnItem(
            product_id=1,
            return_reason=ReturnReason.EXPIRED
        )
        
        self.assertEqual(item.return_reason, ReturnReason.EXPIRED)
    
    def test_return_item_customer_request_reason(self):
        """اختبار سبب الإرجاع: طلب العميل"""
        item = ReturnItem(
            product_id=1,
            return_reason=ReturnReason.CUSTOMER_REQUEST
        )
        
        self.assertEqual(item.return_reason, ReturnReason.CUSTOMER_REQUEST)


class TestReturnItemCondition(unittest.TestCase):
    """اختبارات حالة المنتج المرتجع"""
    
    def test_return_item_condition(self):
        """اختبار حالة المنتج"""
        item = ReturnItem(
            product_id=1,
            condition="حالة جيدة - الصندوق مفتوح"
        )
        
        self.assertEqual(item.condition, "حالة جيدة - الصندوق مفتوح")
    
    def test_return_item_restockable(self):
        """اختبار إعادة التخزين"""
        item = ReturnItem(
            product_id=1,
            restockable=True
        )
        
        self.assertTrue(item.restockable)
    
    def test_return_item_not_restockable(self):
        """اختبار عدم إعادة التخزين"""
        item = ReturnItem(
            product_id=1,
            restockable=False
        )
        
        self.assertFalse(item.restockable)


class TestReturnItemReferences(unittest.TestCase):
    """اختبارات المراجع والروابط"""
    
    def test_return_item_sale_reference(self):
        """اختبار المرجع لفاتورة مبيعات"""
        item = ReturnItem(
            product_id=1,
            original_sale_item_id=100
        )
        
        self.assertEqual(item.original_sale_item_id, 100)
    
    def test_return_item_purchase_reference(self):
        """اختبار المرجع لفاتورة مشتريات"""
        item = ReturnItem(
            product_id=1,
            original_purchase_item_id=50
        )
        
        self.assertEqual(item.original_purchase_item_id, 50)
    
    def test_return_item_no_references(self):
        """اختبار بند بدون مراجع"""
        item = ReturnItem(product_id=1)
        
        self.assertIsNone(item.original_sale_item_id)
        self.assertIsNone(item.original_purchase_item_id)


class TestReturnItemProductInfo(unittest.TestCase):
    """اختبارات معلومات المنتج"""
    
    def test_return_item_product_details(self):
        """اختبار تفاصيل المنتج"""
        item = ReturnItem(
            product_id=1,
            product_name="منتج متقدم",
            product_barcode="123456789"
        )
        
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج متقدم")
        self.assertEqual(item.product_barcode, "123456789")


class TestReturnItemNotes(unittest.TestCase):
    """اختبارات ملاحظات البند"""
    
    def test_return_item_notes(self):
        """اختبار ملاحظات البند"""
        item = ReturnItem(
            product_id=1,
            notes="ملاحظات خاصة عن المرتجع"
        )
        
        self.assertEqual(item.notes, "ملاحظات خاصة عن المرتجع")
    
    def test_return_item_no_notes(self):
        """اختبار بند بدون ملاحظات"""
        item = ReturnItem(product_id=1)
        
        self.assertIsNone(item.notes)


class TestReturnItemEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_return_item_zero_quantity(self):
        """اختبار كمية صفر"""
        item = ReturnItem(
            quantity_returned=Decimal('0')
        )
        
        self.assertEqual(item.quantity_returned, Decimal('0'))
    
    def test_return_item_large_quantity(self):
        """اختبار كمية كبيرة"""
        item = ReturnItem(
            quantity_returned=Decimal('999999')
        )
        
        self.assertEqual(item.quantity_returned, Decimal('999999'))
    
    def test_return_item_zero_price(self):
        """اختبار سعر صفر"""
        item = ReturnItem(
            unit_price=Decimal('0.00')
        )
        
        self.assertEqual(item.unit_price, Decimal('0.00'))
    
    def test_return_item_negative_discount(self):
        """اختبار خصم سلبي (إضافة)"""
        item = ReturnItem(
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('-10.00')
        )
        
        self.assertLess(item.discount_amount, Decimal('0'))
    
    def test_return_item_high_tax(self):
        """اختبار ضريبة عالية"""
        item = ReturnItem(
            unit_price=Decimal('100.00'),
            tax_amount=Decimal('100.00')
        )
        
        self.assertEqual(item.tax_amount, Decimal('100.00'))


class TestReturnItemIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""
    
    def test_return_item_complete_sale_return(self):
        """اختبار بند مرتجع مبيعات كامل"""
        item = ReturnItem(
            id=1,
            return_id=1,
            original_sale_item_id=100,
            product_id=1,
            product_name="منتج مرتجع",
            product_barcode="123456",
            quantity_returned=Decimal('5'),
            quantity_original=Decimal('10'),
            unit_price=Decimal('100.00'),
            discount_amount=Decimal('50.00'),
            tax_amount=Decimal('75.00'),
            total_amount=Decimal('475.00'),
            return_reason=ReturnReason.DEFECTIVE,
            condition="معيب - عيب في الصندوق",
            restockable=False,
            notes="تم فحص المنتج"
        )
        
        self.assertEqual(item.id, 1)
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.quantity_returned, Decimal('5'))
        self.assertEqual(item.return_reason, ReturnReason.DEFECTIVE)
        self.assertFalse(item.restockable)
    
    def test_return_item_complete_purchase_return(self):
        """اختبار بند مرتجع مشتريات كامل"""
        item = ReturnItem(
            id=2,
            return_id=2,
            original_purchase_item_id=50,
            product_id=2,
            product_name="منتج مشتريات مرتجع",
            quantity_returned=Decimal('20'),
            quantity_original=Decimal('50'),
            unit_price=Decimal('50.00'),
            total_amount=Decimal('1000.00'),
            return_reason=ReturnReason.OVERSTOCK,
            restockable=True
        )
        
        self.assertEqual(item.id, 2)
        self.assertEqual(item.original_purchase_item_id, 50)
        self.assertTrue(item.restockable)


if __name__ == '__main__':
    unittest.main()

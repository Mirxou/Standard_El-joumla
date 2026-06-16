#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج أوامر الشراء - Purchase Order Model Tests
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal

from src.models.purchase_order import (
    DeliveryTerms,
    PaymentTerms,
    POPriority,
    POStatus,
    PurchaseOrderItem,
)


class TestPOStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات أمر الشراء"""

    def test_po_status_values(self):
        """اختبار قيم حالات أمر الشراء"""
        self.assertEqual(POStatus.DRAFT.value, "مسودة")
        self.assertEqual(POStatus.PENDING_APPROVAL.value, "في انتظار الموافقة")
        self.assertEqual(POStatus.APPROVED.value, "موافق عليه")
        self.assertEqual(POStatus.SENT.value, "مرسل للمورد")
        self.assertEqual(POStatus.CONFIRMED.value, "مؤكد")
        self.assertEqual(POStatus.PARTIALLY_RECEIVED.value, "مستلم جزئياً")
        self.assertEqual(POStatus.FULLY_RECEIVED.value, "مستلم بالكامل")
        self.assertEqual(POStatus.CLOSED.value, "مغلق")
        self.assertEqual(POStatus.CANCELLED.value, "ملغي")

    def test_all_po_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(POStatus)
        self.assertEqual(len(statuses), 9)


class TestPOPriorityEnum(unittest.TestCase):
    """اختبارات تعداد الأولويات"""

    def test_priority_values(self):
        """اختبار قيم الأولويات"""
        self.assertEqual(POPriority.LOW.value, "منخفضة")
        self.assertEqual(POPriority.NORMAL.value, "عادية")
        self.assertEqual(POPriority.HIGH.value, "عالية")
        self.assertEqual(POPriority.URGENT.value, "عاجلة")

    def test_all_priorities(self):
        """اختبار عدد الأولويات"""
        priorities = list(POPriority)
        self.assertEqual(len(priorities), 4)


class TestDeliveryTermsEnum(unittest.TestCase):
    """اختبارات تعداد شروط التسليم"""

    def test_delivery_terms_values(self):
        """اختبار قيم شروط التسليم"""
        self.assertEqual(DeliveryTerms.EXW.value, "EXW - من المصنع")
        self.assertEqual(DeliveryTerms.FOB.value, "FOB - على ظهر السفينة")
        self.assertEqual(DeliveryTerms.CIF.value, "CIF - التكلفة والتأمين والشحن")
        self.assertEqual(DeliveryTerms.DAP.value, "DAP - التسليم في المكان")
        self.assertEqual(DeliveryTerms.DDP.value, "DDP - التسليم بعد دفع الرسوم")

    def test_all_delivery_terms(self):
        """اختبار عدد شروط التسليم"""
        terms = list(DeliveryTerms)
        self.assertEqual(len(terms), 5)


class TestPaymentTermsEnum(unittest.TestCase):
    """اختبارات تعداد شروط الدفع"""

    def test_payment_terms_values(self):
        """اختبار قيم شروط الدفع"""
        self.assertEqual(PaymentTerms.CASH.value, "نقدي فوري")
        self.assertEqual(PaymentTerms.NET_7.value, "خلال 7 أيام")
        self.assertEqual(PaymentTerms.NET_30.value, "خلال 30 يوم")
        self.assertEqual(PaymentTerms.ADVANCE_50.value, "دفعة مقدمة 50%")
        self.assertEqual(PaymentTerms.ADVANCE_100.value, "دفع كامل مقدم")

    def test_all_payment_terms(self):
        """اختبار عدد شروط الدفع"""
        terms = list(PaymentTerms)
        self.assertEqual(len(terms), 8)


class TestPOItemCreation(unittest.TestCase):
    """اختبارات إنشاء بند أمر الشراء"""

    def test_po_item_default_values(self):
        """اختبار القيم الافتراضية للبند"""
        item = PurchaseOrderItem()

        self.assertIsNone(item.id)
        self.assertIsNone(item.po_id)
        self.assertEqual(item.product_id, 0)
        self.assertEqual(item.quantity_ordered, Decimal("0"))
        self.assertEqual(item.quantity_received, Decimal("0"))
        self.assertEqual(item.unit_price, Decimal("0.00"))
        self.assertEqual(item.tax_percentage, Decimal("15.00"))

    def test_po_item_with_values(self):
        """اختبار إنشاء بند مع قيم"""
        item = PurchaseOrderItem(
            product_id=1,
            product_name="منتج اختبار",
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("50.00"),
        )

        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج اختبار")
        self.assertEqual(item.quantity_ordered, Decimal("100"))
        self.assertEqual(item.unit_price, Decimal("50.00"))

    def test_po_item_inspection_required(self):
        """اختبار خاصية الفحص المطلوب"""
        item = PurchaseOrderItem(product_id=1, inspection_required=True)

        self.assertTrue(item.inspection_required)

    def test_po_item_specifications(self):
        """اختبار مواصفات المنتج"""
        item = PurchaseOrderItem(product_id=1, specifications="مواصفات خاصة", manufacturer="الشركة المصنعة")

        self.assertEqual(item.specifications, "مواصفات خاصة")
        self.assertEqual(item.manufacturer, "الشركة المصنعة")


class TestPOItemQuantities(unittest.TestCase):
    """اختبارات كميات البند"""

    def test_po_item_quantities(self):
        """اختبار الكميات المختلفة"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), quantity_received=Decimal("50"))

        self.assertEqual(item.quantity_ordered, Decimal("100"))
        self.assertEqual(item.quantity_received, Decimal("50"))
        # quantity_pending يجب أن تكون محسوبة: 100 - 50 = 50
        expected_pending = item.quantity_ordered - item.quantity_received
        self.assertEqual(expected_pending, Decimal("50"))

    def test_po_item_fully_received(self):
        """اختبار استقبال كامل الكمية"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), quantity_received=Decimal("100"))

        self.assertEqual(item.quantity_ordered, item.quantity_received)

    def test_po_item_zero_quantity(self):
        """اختبار كمية صفر"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("0"), quantity_received=Decimal("0"))

        self.assertEqual(item.quantity_ordered, Decimal("0"))


class TestPOItemDelivery(unittest.TestCase):
    """اختبارات تسليم البند"""

    def test_po_item_delivery_dates(self):
        """اختبار تواريخ التسليم"""
        expected_date = date(2024, 12, 31)
        actual_date = date(2024, 12, 25)

        item = PurchaseOrderItem(
            product_id=1,
            expected_delivery_date=expected_date,
            actual_delivery_date=actual_date,
        )

        self.assertEqual(item.expected_delivery_date, expected_date)
        self.assertEqual(item.actual_delivery_date, actual_date)

    def test_po_item_lead_time(self):
        """اختبار وقت التسليم"""
        item = PurchaseOrderItem(product_id=1, lead_time_days=14)

        self.assertEqual(item.lead_time_days, 14)

    def test_po_item_unit_of_measure(self):
        """اختبار وحدة القياس"""
        item = PurchaseOrderItem(product_id=1, unit_of_measure="كيس/10 كجم")

        self.assertEqual(item.unit_of_measure, "كيس/10 كجم")


class TestPOItemPricing(unittest.TestCase):
    """اختبارات تسعير البند"""

    def test_po_item_unit_price(self):
        """اختبار سعر الوحدة"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), unit_price=Decimal("50.00"))

        self.assertEqual(item.unit_price, Decimal("50.00"))

    def test_po_item_discount_percentage(self):
        """اختبار نسبة الخصم"""
        item = PurchaseOrderItem(
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("50.00"),
            discount_percentage=Decimal("10"),
        )

        self.assertEqual(item.discount_percentage, Decimal("10"))

    def test_po_item_discount_amount(self):
        """اختبار مبلغ الخصم"""
        item = PurchaseOrderItem(
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("50.00"),
            discount_amount=Decimal("500.00"),
        )

        self.assertEqual(item.discount_amount, Decimal("500.00"))

    def test_po_item_tax_percentage(self):
        """اختبار نسبة الضريبة"""
        item = PurchaseOrderItem(tax_percentage=Decimal("19.00"))

        self.assertEqual(item.tax_percentage, Decimal("19.00"))

    def test_po_item_tax_amount(self):
        """اختبار مبلغ الضريبة"""
        item = PurchaseOrderItem(
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("50.00"),
            tax_amount=Decimal("950.00"),
        )

        self.assertEqual(item.tax_amount, Decimal("950.00"))

    def test_po_item_total_amount(self):
        """اختبار المبلغ الإجمالي"""
        item = PurchaseOrderItem(total_amount=Decimal("5950.00"))

        self.assertEqual(item.total_amount, Decimal("5950.00"))


class TestPOItemQuality(unittest.TestCase):
    """اختبارات متطلبات الجودة"""

    def test_po_item_quality_requirements(self):
        """اختبار متطلبات الجودة"""
        item = PurchaseOrderItem(product_id=1, quality_requirements="معايير ISO 9001")

        self.assertEqual(item.quality_requirements, "معايير ISO 9001")

    def test_po_item_inspection_flag(self):
        """اختبار علم الفحص"""
        item = PurchaseOrderItem(product_id=1, inspection_required=True)

        self.assertTrue(item.inspection_required)

    def test_po_item_no_inspection_required(self):
        """اختبار عدم طلب الفحص"""
        item = PurchaseOrderItem(product_id=1, inspection_required=False)

        self.assertFalse(item.inspection_required)


class TestPOItemNotes(unittest.TestCase):
    """اختبارات ملاحظات البند"""

    def test_po_item_notes(self):
        """اختبار ملاحظات البند"""
        item = PurchaseOrderItem(product_id=1, notes="ملاحظات خاصة عن هذا البند")

        self.assertEqual(item.notes, "ملاحظات خاصة عن هذا البند")

    def test_po_item_description(self):
        """اختبار وصف البند"""
        item = PurchaseOrderItem(product_id=1, description="وصف تفصيلي للمنتج")

        self.assertEqual(item.description, "وصف تفصيلي للمنتج")

    def test_po_item_product_code(self):
        """اختبار رمز المنتج"""
        item = PurchaseOrderItem(product_id=1, product_code="PROD-001")

        self.assertEqual(item.product_code, "PROD-001")


class TestPOItemEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""

    def test_po_item_large_quantity(self):
        """اختبار كمية كبيرة جداً"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("999999"))

        self.assertEqual(item.quantity_ordered, Decimal("999999"))

    def test_po_item_decimal_quantity(self):
        """اختبار كمية عشرية"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("1.5"))

        self.assertEqual(item.quantity_ordered, Decimal("1.5"))

    def test_po_item_zero_price(self):
        """اختبار سعر صفر"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), unit_price=Decimal("0.00"))

        self.assertEqual(item.unit_price, Decimal("0.00"))

    def test_po_item_100_percent_discount(self):
        """اختبار خصم 100%"""
        item = PurchaseOrderItem(
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("100.00"),
        )

        self.assertEqual(item.discount_percentage, Decimal("100.00"))

    def test_po_item_no_tax(self):
        """اختبار بدون ضريبة"""
        item = PurchaseOrderItem(
            quantity_ordered=Decimal("100"),
            unit_price=Decimal("50.00"),
            tax_percentage=Decimal("0.00"),
        )

        self.assertEqual(item.tax_percentage, Decimal("0.00"))

    def test_po_item_future_delivery_date(self):
        """اختبار تاريخ تسليم في المستقبل"""
        future_date = date.today() + timedelta(days=90)
        item = PurchaseOrderItem(product_id=1, expected_delivery_date=future_date)

        self.assertEqual(item.expected_delivery_date, future_date)

    def test_po_item_past_delivery_date(self):
        """اختبار تاريخ تسليم في الماضي"""
        past_date = date.today() - timedelta(days=30)
        item = PurchaseOrderItem(product_id=1, actual_delivery_date=past_date)

        self.assertEqual(item.actual_delivery_date, past_date)


class TestPOItemCompletion(unittest.TestCase):
    """اختبارات حالة استكمال البند"""

    def test_po_item_pending_qty_calculation(self):
        """اختبار حساب الكمية المعلقة"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), quantity_received=Decimal("60"))

        # الكمية المعلقة = 100 - 60 = 40
        pending = item.quantity_ordered - item.quantity_received
        self.assertEqual(pending, Decimal("40"))

    def test_po_item_no_pending_qty(self):
        """اختبار عدم وجود كمية معلقة"""
        item = PurchaseOrderItem(quantity_ordered=Decimal("100"), quantity_received=Decimal("100"))

        pending = item.quantity_ordered - item.quantity_received
        self.assertEqual(pending, Decimal("0"))


class TestPOItemMultipleFields(unittest.TestCase):
    """اختبارات بند بعدة حقول"""

    def test_po_item_complete(self):
        """اختبار بند كامل مع جميع الحقول"""
        item = PurchaseOrderItem(
            id=1,
            po_id=1,
            product_id=1,
            product_name="منتج كامل",
            product_code="PROD-001",
            description="وصف شامل",
            quantity_ordered=Decimal("100"),
            quantity_received=Decimal("50"),
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10.00"),
            tax_percentage=Decimal("15.00"),
            unit_of_measure="صندوق",
            expected_delivery_date=date(2024, 12, 31),
            actual_delivery_date=date(2024, 12, 25),
            lead_time_days=7,
            quality_requirements="ISO 9001",
            inspection_required=True,
            manufacturer="الشركة المصنعة",
            notes="ملاحظات مهمة",
        )

        self.assertEqual(item.id, 1)
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.quantity_ordered, Decimal("100"))
        self.assertTrue(item.inspection_required)
        self.assertEqual(item.notes, "ملاحظات مهمة")


if __name__ == "__main__":
    unittest.main()

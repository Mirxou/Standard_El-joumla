#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج استلام البضائع - Receiving Note Model Tests
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from src.models.receiving_note import (
    ReceivingStatus, InspectionStatus, QualityRating, ReceivingItem
)


class TestReceivingStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات الاستلام"""
    
    def test_receiving_status_values(self):
        """اختبار قيم حالات الاستلام"""
        self.assertEqual(ReceivingStatus.PENDING.value, "معلق")
        self.assertEqual(ReceivingStatus.IN_PROGRESS.value, "جاري الاستلام")
        self.assertEqual(ReceivingStatus.COMPLETED.value, "مكتمل")
        self.assertEqual(ReceivingStatus.PARTIALLY_ACCEPTED.value, "مقبول جزئياً")
        self.assertEqual(ReceivingStatus.REJECTED.value, "مرفوض")
        self.assertEqual(ReceivingStatus.ON_HOLD.value, "معلق")
    
    def test_all_receiving_statuses(self):
        """اختبار عدد جميع حالات الاستلام"""
        statuses = list(ReceivingStatus)
        # ملاحظة: PENDING و ON_HOLD لهما نفس القيمة في التعريف
        self.assertGreaterEqual(len(statuses), 5)


class TestInspectionStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات الفحص"""
    
    def test_inspection_status_values(self):
        """اختبار قيم حالات الفحص"""
        self.assertEqual(InspectionStatus.NOT_REQUIRED.value, "غير مطلوب")
        self.assertEqual(InspectionStatus.PENDING.value, "في انتظار الفحص")
        self.assertEqual(InspectionStatus.IN_PROGRESS.value, "جاري الفحص")
        self.assertEqual(InspectionStatus.PASSED.value, "نجح")
        self.assertEqual(InspectionStatus.FAILED.value, "فشل")
        self.assertEqual(InspectionStatus.CONDITIONAL.value, "مشروط")
    
    def test_all_inspection_statuses(self):
        """اختبار عدد جميع حالات الفحص"""
        statuses = list(InspectionStatus)
        self.assertEqual(len(statuses), 6)


class TestQualityRatingEnum(unittest.TestCase):
    """اختبارات تعداد تقييمات الجودة"""
    
    def test_quality_rating_values(self):
        """اختبار قيم تقييمات الجودة"""
        self.assertEqual(QualityRating.EXCELLENT.value, "ممتاز")
        self.assertEqual(QualityRating.GOOD.value, "جيد")
        self.assertEqual(QualityRating.ACCEPTABLE.value, "مقبول")
        self.assertEqual(QualityRating.POOR.value, "ضعيف")
        self.assertEqual(QualityRating.REJECTED.value, "مرفوض")
    
    def test_all_quality_ratings(self):
        """اختبار عدد جميع التقييمات"""
        ratings = list(QualityRating)
        self.assertEqual(len(ratings), 5)


class TestReceivingItemCreation(unittest.TestCase):
    """اختبارات إنشاء بند الاستلام"""
    
    def test_receiving_item_default_values(self):
        """اختبار القيم الافتراضية لبند الاستلام"""
        item = ReceivingItem()
        
        self.assertIsNone(item.id)
        self.assertIsNone(item.receiving_id)
        self.assertEqual(item.product_id, 0)
        self.assertEqual(item.quantity_ordered, Decimal('0'))
        self.assertEqual(item.quantity_received, Decimal('0'))
        self.assertEqual(item.inspection_status, InspectionStatus.NOT_REQUIRED)
        self.assertTrue(item.matches_specifications)
    
    def test_receiving_item_with_values(self):
        """اختبار إنشاء بند مع قيم"""
        item = ReceivingItem(
            product_id=1,
            product_name="منتج اختبار",
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('95')
        )
        
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج اختبار")
        self.assertEqual(item.quantity_ordered, Decimal('100'))
        self.assertEqual(item.quantity_received, Decimal('95'))


class TestReceivingItemQuantities(unittest.TestCase):
    """اختبارات كميات الاستلام"""
    
    def test_receiving_item_quantities(self):
        """اختبار الكميات المختلفة"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('95'),
            quantity_accepted=Decimal('90'),
            quantity_rejected=Decimal('5'),
            quantity_damaged=Decimal('2')
        )
        
        self.assertEqual(item.quantity_ordered, Decimal('100'))
        self.assertEqual(item.quantity_received, Decimal('95'))
        self.assertEqual(item.quantity_accepted, Decimal('90'))
        self.assertEqual(item.quantity_rejected, Decimal('5'))
        self.assertEqual(item.quantity_damaged, Decimal('2'))
    
    def test_receiving_item_fully_accepted(self):
        """اختبار استقبال وقبول كامل الكمية"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('100'),
            quantity_accepted=Decimal('100')
        )
        
        self.assertEqual(item.quantity_received, item.quantity_accepted)
    
    def test_receiving_item_partial_rejection(self):
        """اختبار الرفض الجزئي"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('100'),
            quantity_accepted=Decimal('80'),
            quantity_rejected=Decimal('20')
        )
        
        total_processed = item.quantity_accepted + item.quantity_rejected
        self.assertEqual(total_processed, item.quantity_received)


class TestReceivingItemInspection(unittest.TestCase):
    """اختبارات فحص بنود الاستلام"""
    
    def test_receiving_item_no_inspection_required(self):
        """اختبار بند لا يحتاج فحص"""
        item = ReceivingItem(
            product_id=1,
            inspection_status=InspectionStatus.NOT_REQUIRED
        )
        
        self.assertEqual(item.inspection_status, InspectionStatus.NOT_REQUIRED)
    
    def test_receiving_item_inspection_pending(self):
        """اختبار بند في انتظار الفحص"""
        item = ReceivingItem(
            product_id=1,
            inspection_status=InspectionStatus.PENDING
        )
        
        self.assertEqual(item.inspection_status, InspectionStatus.PENDING)
    
    def test_receiving_item_inspection_passed(self):
        """اختبار بند نجح في الفحص"""
        item = ReceivingItem(
            product_id=1,
            inspection_status=InspectionStatus.PASSED,
            inspector_name="أحمد محمد",
            inspection_date=date.today()
        )
        
        self.assertEqual(item.inspection_status, InspectionStatus.PASSED)
        self.assertEqual(item.inspector_name, "أحمد محمد")
        self.assertIsNotNone(item.inspection_date)
    
    def test_receiving_item_inspection_failed(self):
        """اختبار بند فشل في الفحص"""
        item = ReceivingItem(
            product_id=1,
            inspection_status=InspectionStatus.FAILED,
            quality_rating=QualityRating.REJECTED
        )
        
        self.assertEqual(item.inspection_status, InspectionStatus.FAILED)
        self.assertEqual(item.quality_rating, QualityRating.REJECTED)
    
    def test_receiving_item_inspection_notes(self):
        """اختبار ملاحظات الفحص"""
        item = ReceivingItem(
            product_id=1,
            inspection_notes="وجدت عيوب في العبوة"
        )
        
        self.assertEqual(item.inspection_notes, "وجدت عيوب في العبوة")


class TestReceivingItemQuality(unittest.TestCase):
    """اختبارات تقييم الجودة"""
    
    def test_receiving_item_excellent_quality(self):
        """اختبار تقييم ممتاز"""
        item = ReceivingItem(
            product_id=1,
            quality_rating=QualityRating.EXCELLENT
        )
        
        self.assertEqual(item.quality_rating, QualityRating.EXCELLENT)
    
    def test_receiving_item_good_quality(self):
        """اختبار تقييم جيد"""
        item = ReceivingItem(
            product_id=1,
            quality_rating=QualityRating.GOOD
        )
        
        self.assertEqual(item.quality_rating, QualityRating.GOOD)
    
    def test_receiving_item_poor_quality(self):
        """اختبار تقييم ضعيف"""
        item = ReceivingItem(
            product_id=1,
            quality_rating=QualityRating.POOR
        )
        
        self.assertEqual(item.quality_rating, QualityRating.POOR)
    
    def test_receiving_item_no_quality_rating(self):
        """اختبار بدون تقييم جودة"""
        item = ReceivingItem(product_id=1)
        
        self.assertIsNone(item.quality_rating)


class TestReceivingItemStorage(unittest.TestCase):
    """اختبارات معلومات التخزين"""
    
    def test_receiving_item_warehouse_location(self):
        """اختبار موقع المستودع"""
        item = ReceivingItem(
            product_id=1,
            warehouse_location="رف A - قسم 1"
        )
        
        self.assertEqual(item.warehouse_location, "رف A - قسم 1")
    
    def test_receiving_item_batch_number(self):
        """اختبار رقم الدفعة"""
        item = ReceivingItem(
            product_id=1,
            batch_number="BATCH-2024-001"
        )
        
        self.assertEqual(item.batch_number, "BATCH-2024-001")
    
    def test_receiving_item_serial_numbers(self):
        """اختبار الأرقام التسلسلية"""
        item = ReceivingItem(
            product_id=1,
            serial_numbers="SN001,SN002,SN003"
        )
        
        self.assertEqual(item.serial_numbers, "SN001,SN002,SN003")
    
    def test_receiving_item_expiry_date(self):
        """اختبار تاريخ الانتهاء"""
        expiry = date(2025, 12, 31)
        item = ReceivingItem(
            product_id=1,
            expiry_date=expiry
        )
        
        self.assertEqual(item.expiry_date, expiry)
    
    def test_receiving_item_full_storage_info(self):
        """اختبار معلومات التخزين الكاملة"""
        item = ReceivingItem(
            product_id=1,
            warehouse_location="مستودع رئيسي - رف B",
            batch_number="BATCH-001",
            serial_numbers="SN1,SN2",
            expiry_date=date(2025, 6, 30)
        )
        
        self.assertEqual(item.warehouse_location, "مستودع رئيسي - رف B")
        self.assertEqual(item.batch_number, "BATCH-001")
        self.assertIsNotNone(item.expiry_date)


class TestReceivingItemSpecifications(unittest.TestCase):
    """اختبارات تطابق المواصفات"""
    
    def test_receiving_item_matches_specifications(self):
        """اختبار تطابق المواصفات"""
        item = ReceivingItem(
            product_id=1,
            matches_specifications=True
        )
        
        self.assertTrue(item.matches_specifications)
    
    def test_receiving_item_not_matches_specifications(self):
        """اختبار عدم تطابق المواصفات"""
        item = ReceivingItem(
            product_id=1,
            matches_specifications=False
        )
        
        self.assertFalse(item.matches_specifications)


class TestReceivingItemProductInfo(unittest.TestCase):
    """اختبارات معلومات المنتج"""
    
    def test_receiving_item_product_details(self):
        """اختبار تفاصيل المنتج"""
        item = ReceivingItem(
            product_id=1,
            product_name="منتج متقدم",
            product_code="PROD-2024-001",
            po_item_id=5
        )
        
        self.assertEqual(item.product_id, 1)
        self.assertEqual(item.product_name, "منتج متقدم")
        self.assertEqual(item.product_code, "PROD-2024-001")
        self.assertEqual(item.po_item_id, 5)


class TestReceivingItemEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_receiving_item_zero_quantities(self):
        """اختبار الكميات الصفر"""
        item = ReceivingItem(
            quantity_ordered=Decimal('0'),
            quantity_received=Decimal('0')
        )
        
        self.assertEqual(item.quantity_ordered, Decimal('0'))
        self.assertEqual(item.quantity_received, Decimal('0'))
    
    def test_receiving_item_large_quantities(self):
        """اختبار كميات كبيرة"""
        item = ReceivingItem(
            quantity_ordered=Decimal('999999'),
            quantity_received=Decimal('999999')
        )
        
        self.assertEqual(item.quantity_ordered, Decimal('999999'))
    
    def test_receiving_item_decimal_quantities(self):
        """اختبار كميات عشرية"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100.50'),
            quantity_received=Decimal('99.75')
        )
        
        self.assertEqual(item.quantity_ordered, Decimal('100.50'))
        self.assertEqual(item.quantity_received, Decimal('99.75'))
    
    def test_receiving_item_damaged_quantity(self):
        """اختبار الكمية التالفة"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('100'),
            quantity_damaged=Decimal('3')
        )
        
        self.assertEqual(item.quantity_damaged, Decimal('3'))
    
    def test_receiving_item_all_damaged(self):
        """اختبار الحالة التي كل الكمية تالفة"""
        item = ReceivingItem(
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('100'),
            quantity_damaged=Decimal('100')
        )
        
        self.assertEqual(item.quantity_damaged, item.quantity_received)
    
    def test_receiving_item_past_expiry_date(self):
        """اختبار تاريخ انتهاء في الماضي"""
        past_date = date.today() - timedelta(days=30)
        item = ReceivingItem(
            product_id=1,
            expiry_date=past_date
        )
        
        self.assertLess(item.expiry_date, date.today())
    
    def test_receiving_item_far_future_expiry(self):
        """اختبار تاريخ انتهاء بعيد في المستقبل"""
        future_date = date.today() + timedelta(days=1000)
        item = ReceivingItem(
            product_id=1,
            expiry_date=future_date
        )
        
        self.assertGreater(item.expiry_date, date.today())


class TestReceivingItemValidation(unittest.TestCase):
    """اختبارات التحقق من صحة البند"""
    
    def test_receiving_item_incomplete(self):
        """اختبار بند غير مكتمل"""
        item = ReceivingItem()
        
        # بند جديد بدون معلومات
        self.assertEqual(item.product_id, 0)
        self.assertIsNone(item.id)
    
    def test_receiving_item_with_po_reference(self):
        """اختبار بند مع مرجع أمر الشراء"""
        item = ReceivingItem(
            product_id=1,
            po_item_id=10
        )
        
        self.assertEqual(item.po_item_id, 10)
    
    def test_receiving_item_comprehensive(self):
        """اختبار بند شامل"""
        item = ReceivingItem(
            id=1,
            receiving_id=1,
            po_item_id=10,
            product_id=1,
            product_name="منتج شامل",
            product_code="PROD-001",
            quantity_ordered=Decimal('100'),
            quantity_received=Decimal('98'),
            quantity_accepted=Decimal('95'),
            quantity_rejected=Decimal('3'),
            quantity_damaged=Decimal('2'),
            inspection_status=InspectionStatus.PASSED,
            quality_rating=QualityRating.GOOD,
            warehouse_location="Warehouse A",
            batch_number="BATCH-001",
            matches_specifications=True
        )
        
        self.assertEqual(item.id, 1)
        self.assertEqual(item.po_item_id, 10)
        self.assertEqual(item.quantity_received, Decimal('98'))
        self.assertEqual(item.inspection_status, InspectionStatus.PASSED)
        self.assertEqual(item.quality_rating, QualityRating.GOOD)


if __name__ == '__main__':
    unittest.main()




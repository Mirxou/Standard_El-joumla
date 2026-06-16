#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج الجرد الدوري والتسويات - Physical Count Model Tests
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal

from src.models.physical_count import (
    AdjustmentStatus,
    AdjustmentType,
    CountStatus,
    PhysicalCount,
)


class TestCountStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات الجرد"""

    def test_count_status_values(self):
        """اختبار قيم حالات الجرد"""
        self.assertEqual(CountStatus.DRAFT.value, "draft")
        self.assertEqual(CountStatus.IN_PROGRESS.value, "in_progress")
        self.assertEqual(CountStatus.COMPLETED.value, "completed")
        self.assertEqual(CountStatus.APPROVED.value, "approved")
        self.assertEqual(CountStatus.CANCELLED.value, "cancelled")

    def test_all_count_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(CountStatus)
        self.assertEqual(len(statuses), 5)


class TestAdjustmentTypeEnum(unittest.TestCase):
    """اختبارات تعداد أنواع التسويات"""

    def test_adjustment_type_values(self):
        """اختبار قيم أنواع التسويات"""
        self.assertEqual(AdjustmentType.COUNT_ADJUSTMENT.value, "count_adjustment")
        self.assertEqual(AdjustmentType.DAMAGE.value, "damage")
        self.assertEqual(AdjustmentType.EXPIRY.value, "expiry")
        self.assertEqual(AdjustmentType.THEFT.value, "theft")
        self.assertEqual(AdjustmentType.LOSS.value, "loss")
        self.assertEqual(AdjustmentType.FOUND.value, "found")
        self.assertEqual(AdjustmentType.CORRECTION.value, "correction")
        self.assertEqual(AdjustmentType.TRANSFER.value, "transfer")
        self.assertEqual(AdjustmentType.OTHER.value, "other")

    def test_all_adjustment_types(self):
        """اختبار عدد جميع الأنواع"""
        types = list(AdjustmentType)
        self.assertEqual(len(types), 9)


class TestAdjustmentStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات التسوية"""

    def test_adjustment_status_values(self):
        """اختبار قيم حالات التسوية"""
        self.assertEqual(AdjustmentStatus.PENDING.value, "pending")
        self.assertEqual(AdjustmentStatus.APPROVED.value, "approved")
        self.assertEqual(AdjustmentStatus.REJECTED.value, "rejected")
        self.assertEqual(AdjustmentStatus.APPLIED.value, "applied")

    def test_all_adjustment_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(AdjustmentStatus)
        self.assertEqual(len(statuses), 4)


class TestPhysicalCountCreation(unittest.TestCase):
    """اختبارات إنشاء الجرد الدوري"""

    def test_physical_count_default_values(self):
        """اختبار القيم الافتراضية"""
        count = PhysicalCount()

        self.assertIsNone(count.id)
        self.assertEqual(count.count_number, "")
        self.assertEqual(count.status, CountStatus.DRAFT)
        self.assertEqual(count.total_items, 0)
        self.assertEqual(count.items, [])

    def test_physical_count_with_values(self):
        """اختبار إنشاء جرد مع قيم"""
        today = date.today()
        count = PhysicalCount(
            id=1,
            count_number="PHC001",
            count_date=today,
            description="جرد المستودع الرئيسي",
        )

        self.assertEqual(count.id, 1)
        self.assertEqual(count.count_number, "PHC001")
        self.assertEqual(count.count_date, today)


class TestPhysicalCountStatus(unittest.TestCase):
    """اختبارات حالات الجرد"""

    def test_count_status_draft(self):
        """اختبار حالة المسودة"""
        count = PhysicalCount(status=CountStatus.DRAFT)
        self.assertEqual(count.status, CountStatus.DRAFT)

    def test_count_status_in_progress(self):
        """اختبار حالة قيد التنفيذ"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS)
        self.assertEqual(count.status, CountStatus.IN_PROGRESS)

    def test_count_status_completed(self):
        """اختبار حالة مكتمل"""
        count = PhysicalCount(status=CountStatus.COMPLETED, completed_at=datetime.now())
        self.assertEqual(count.status, CountStatus.COMPLETED)

    def test_status_label_draft(self):
        """اختبار تسمية الحالة بالعربية"""
        count = PhysicalCount(status=CountStatus.DRAFT)
        self.assertEqual(count.status_label, "مسودة")

    def test_status_label_in_progress(self):
        """اختبار تسمية قيد التنفيذ"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS)
        self.assertEqual(count.status_label, "قيد التنفيذ")


class TestPhysicalCountStatistics(unittest.TestCase):
    """اختبارات إحصائيات الجرد"""

    def test_total_items(self):
        """اختبار عدد العناصر الكلي"""
        count = PhysicalCount(total_items=100)
        self.assertEqual(count.total_items, 100)

    def test_counted_items(self):
        """اختبار عدد العناصر المجردة"""
        count = PhysicalCount(total_items=100, counted_items=85)
        self.assertEqual(count.counted_items, 85)

    def test_items_with_variance(self):
        """اختبار أصناف بها فروقات"""
        count = PhysicalCount(total_items=100, items_with_variance=5)
        self.assertEqual(count.items_with_variance, 5)

    def test_total_variance_value(self):
        """اختبار قيمة الفروقات الكلية"""
        count = PhysicalCount(total_variance_value=Decimal("1500.00"))
        self.assertEqual(count.total_variance_value, Decimal("1500.00"))


class TestPhysicalCountCompletion(unittest.TestCase):
    """اختبارات نسبة الإنجاز والاكتمال"""

    def test_completion_percentage_zero(self):
        """اختبار نسبة إنجاز صفر"""
        count = PhysicalCount(total_items=0)
        self.assertEqual(count.completion_percentage, 0.0)

    def test_completion_percentage_partial(self):
        """اختبار نسبة إنجاز جزئية"""
        count = PhysicalCount(total_items=100, counted_items=50)
        self.assertEqual(count.completion_percentage, 50.0)

    def test_completion_percentage_full(self):
        """اختبار نسبة إنجاز كاملة"""
        count = PhysicalCount(total_items=100, counted_items=100)
        self.assertEqual(count.completion_percentage, 100.0)

    def test_is_complete_true(self):
        """اختبار اكتمال الجرد"""
        count = PhysicalCount(total_items=100, counted_items=100)
        self.assertTrue(count.is_complete)

    def test_is_complete_false(self):
        """اختبار عدم اكتمال الجرد"""
        count = PhysicalCount(total_items=100, counted_items=50)
        self.assertFalse(count.is_complete)


class TestPhysicalCountVariances(unittest.TestCase):
    """اختبارات الفروقات"""

    def test_has_variances_true(self):
        """اختبار وجود فروقات"""
        count = PhysicalCount(items_with_variance=5)
        self.assertTrue(count.has_variances)

    def test_has_variances_false(self):
        """اختبار عدم وجود فروقات"""
        count = PhysicalCount(items_with_variance=0)
        self.assertFalse(count.has_variances)


class TestPhysicalCountApproval(unittest.TestCase):
    """اختبارات الموافقة والتحرير"""

    def test_requires_approval_true(self):
        """اختبار الحاجة للموافقة"""
        count = PhysicalCount(status=CountStatus.COMPLETED, approved_at=None)
        self.assertTrue(count.requires_approval)

    def test_requires_approval_false(self):
        """اختبار عدم الحاجة للموافقة"""
        count = PhysicalCount(status=CountStatus.DRAFT, approved_at=None)
        self.assertFalse(count.requires_approval)

    def test_is_editable_draft(self):
        """اختبار قابلية التعديل في المسودة"""
        count = PhysicalCount(status=CountStatus.DRAFT)
        self.assertTrue(count.is_editable)

    def test_is_editable_in_progress(self):
        """اختبار قابلية التعديل قيد التنفيذ"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS)
        self.assertTrue(count.is_editable)

    def test_is_editable_completed(self):
        """اختبار عدم قابلية التعديل بعد الاكتمال"""
        count = PhysicalCount(status=CountStatus.COMPLETED)
        self.assertFalse(count.is_editable)


class TestPhysicalCountTransitions(unittest.TestCase):
    """اختبارات انتقالات الحالة"""

    def test_start_count_from_draft(self):
        """اختبار بدء الجرد من المسودة"""
        count = PhysicalCount(status=CountStatus.DRAFT)
        result = count.start_count()

        self.assertTrue(result)
        self.assertEqual(count.status, CountStatus.IN_PROGRESS)

    def test_start_count_from_in_progress(self):
        """اختبار عدم إمكانية البدء من قيد التنفيذ"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS)
        result = count.start_count()

        self.assertFalse(result)

    def test_complete_count_when_complete(self):
        """اختبار إكمال الجرد عند الاكتمال"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS, total_items=100, counted_items=100)
        result = count.complete_count()

        self.assertTrue(result)
        self.assertEqual(count.status, CountStatus.COMPLETED)
        self.assertIsNotNone(count.completed_at)

    def test_complete_count_when_incomplete(self):
        """اختبار عدم إمكانية الإكمال قبل اكتمال جميع العناصر"""
        count = PhysicalCount(status=CountStatus.IN_PROGRESS, total_items=100, counted_items=50)
        result = count.complete_count()

        self.assertFalse(result)


class TestPhysicalCountUser(unittest.TestCase):
    """اختبارات معلومات المستخدم"""

    def test_counted_by_info(self):
        """اختبار معلومات من قام بالجرد"""
        count = PhysicalCount(counted_by=1, counted_by_name="أحمد محمد")

        self.assertEqual(count.counted_by, 1)
        self.assertEqual(count.counted_by_name, "أحمد محمد")

    def test_approved_by_info(self):
        """اختبار معلومات من وافق على الجرد"""
        count = PhysicalCount(approved_by=2, approved_by_name="محمود علي", approved_at=datetime.now())

        self.assertEqual(count.approved_by, 2)
        self.assertEqual(count.approved_by_name, "محمود علي")
        self.assertIsNotNone(count.approved_at)


class TestPhysicalCountLocation(unittest.TestCase):
    """اختبارات معلومات الموقع"""

    def test_physical_count_location(self):
        """اختبار موقع الجرد"""
        count = PhysicalCount(location="المستودع الرئيسي - قسم أ")

        self.assertEqual(count.location, "المستودع الرئيسي - قسم أ")


class TestPhysicalCountDates(unittest.TestCase):
    """اختبارات التواريخ"""

    def test_count_date(self):
        """اختبار تاريخ الجرد"""
        today = date.today()
        count = PhysicalCount(count_date=today)

        self.assertEqual(count.count_date, today)

    def test_scheduled_date(self):
        """اختبار التاريخ المخطط"""
        scheduled = date.today() + timedelta(days=7)
        count = PhysicalCount(scheduled_date=scheduled)

        self.assertEqual(count.scheduled_date, scheduled)

    def test_completed_at(self):
        """اختبار تاريخ الإكمال"""
        completed = datetime.now()
        count = PhysicalCount(completed_at=completed)

        self.assertEqual(count.completed_at, completed)


class TestPhysicalCountNotes(unittest.TestCase):
    """اختبارات الملاحظات"""

    def test_notes(self):
        """اختبار الملاحظات"""
        count = PhysicalCount(notes="جرد عاجل بسبب عدم توافق الأرصدة")

        self.assertEqual(count.notes, "جرد عاجل بسبب عدم توافق الأرصدة")


class TestPhysicalCountEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""

    def test_zero_total_items(self):
        """اختبار جرد بدون عناصر"""
        count = PhysicalCount(total_items=0)
        self.assertEqual(count.total_items, 0)

    def test_large_number_of_items(self):
        """اختبار عدد كبير من العناصر"""
        count = PhysicalCount(total_items=10000, counted_items=9500)
        self.assertEqual(count.counted_items, 9500)
        self.assertAlmostEqual(count.completion_percentage, 95.0)

    def test_very_large_variance_value(self):
        """اختبار قيمة فروقات كبيرة جداً"""
        count = PhysicalCount(total_variance_value=Decimal("999999.99"))
        self.assertEqual(count.total_variance_value, Decimal("999999.99"))

    def test_zero_variance_value(self):
        """اختبار بدون فروقات"""
        count = PhysicalCount(total_variance_value=Decimal("0.00"))
        self.assertEqual(count.total_variance_value, Decimal("0.00"))

    def test_long_description(self):
        """اختبار وصف طويل"""
        long_desc = "ا" * 500
        count = PhysicalCount(description=long_desc)
        self.assertEqual(len(count.description), 500)


class TestPhysicalCountIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""

    def test_complete_physical_count(self):
        """اختبار جرد كامل"""
        now = datetime.now()
        today = date.today()

        count = PhysicalCount(
            id=1,
            count_number="PHC-2024-001",
            count_date=today,
            scheduled_date=today,
            description="جرد شامل للمستودع",
            location="المستودع الرئيسي",
            counted_by=1,
            counted_by_name="أحمد محمد",
            status=CountStatus.COMPLETED,
            approved_by=2,
            approved_by_name="محمود علي",
            approved_at=now,
            total_items=500,
            counted_items=500,
            items_with_variance=0,
            total_variance_value=Decimal("0.00"),
            created_at=now,
            updated_at=now,
            completed_at=now,
            notes="جرد بدون فروقات",
        )

        self.assertEqual(count.id, 1)
        self.assertEqual(count.count_number, "PHC-2024-001")
        self.assertTrue(count.is_complete)
        self.assertFalse(count.has_variances)
        self.assertFalse(count.is_editable)
        self.assertEqual(count.completion_percentage, 100.0)

    def test_in_progress_physical_count(self):
        """اختبار جرد قيد التنفيذ"""
        count = PhysicalCount(
            id=2,
            count_number="PHC-2024-002",
            status=CountStatus.IN_PROGRESS,
            total_items=1000,
            counted_items=400,
            items_with_variance=10,
            total_variance_value=Decimal("2500.50"),
        )

        self.assertEqual(count.completion_percentage, 40.0)
        self.assertTrue(count.has_variances)
        self.assertTrue(count.is_editable)
        self.assertFalse(count.is_complete)


if __name__ == "__main__":
    unittest.main()

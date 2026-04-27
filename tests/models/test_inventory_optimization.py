#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبارات نموذج تحسين المخزون - Inventory Optimization Model Tests
اختبارات تحليل ABC، الأرصدة الآمنة، وتتبع الدفعات
"""

import unittest
from datetime import date, datetime, timedelta
from decimal import Decimal
from src.models.inventory_optimization import (
    ABCCategory, ReorderStatus, BatchStatus,
    ABCAnalysisResult, SafetyStockConfig
)


class TestABCCategoryEnum(unittest.TestCase):
    """اختبارات تعداد فئات تحليل ABC"""
    
    def test_abc_category_a(self):
        """اختبار فئة A"""
        self.assertEqual(ABCCategory.A.value, "A")
    
    def test_abc_category_b(self):
        """اختبار فئة B"""
        self.assertEqual(ABCCategory.B.value, "B")
    
    def test_abc_category_c(self):
        """اختبار فئة C"""
        self.assertEqual(ABCCategory.C.value, "C")
    
    def test_all_abc_categories(self):
        """اختبار عدد الفئات"""
        categories = list(ABCCategory)
        self.assertEqual(len(categories), 3)


class TestReorderStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات إعادة الطلب"""
    
    def test_reorder_status_normal(self):
        """اختبار الحالة العادية"""
        self.assertEqual(ReorderStatus.NORMAL.value, "NORMAL")
    
    def test_reorder_status_approaching(self):
        """اختبار الاقتراب من نقطة الطلب"""
        self.assertEqual(ReorderStatus.APPROACHING.value, "APPROACHING")
    
    def test_reorder_status_reorder(self):
        """اختبار حالة إعادة الطلب"""
        self.assertEqual(ReorderStatus.REORDER.value, "REORDER")
    
    def test_reorder_status_critical(self):
        """اختبار الحالة الحرجة"""
        self.assertEqual(ReorderStatus.CRITICAL.value, "CRITICAL")
    
    def test_reorder_status_stockout(self):
        """اختبار نفاذ المخزون"""
        self.assertEqual(ReorderStatus.STOCKOUT.value, "STOCKOUT")
    
    def test_all_reorder_statuses(self):
        """اختبار عدد جميع الحالات"""
        statuses = list(ReorderStatus)
        self.assertEqual(len(statuses), 5)


class TestBatchStatusEnum(unittest.TestCase):
    """اختبارات تعداد حالات الدفعات"""
    
    def test_batch_status_active(self):
        """اختبار الدفعة النشطة"""
        self.assertEqual(BatchStatus.ACTIVE.value, "ACTIVE")
    
    def test_batch_status_expired(self):
        """اختبار الدفعة المنتهية"""
        self.assertEqual(BatchStatus.EXPIRED.value, "EXPIRED")
    
    def test_batch_status_expiring_soon(self):
        """اختبار الدفعة التي تقترب من الانتهاء"""
        self.assertEqual(BatchStatus.EXPIRING_SOON.value, "EXPIRING_SOON")
    
    def test_batch_status_damaged(self):
        """اختبار الدفعة التالفة"""
        self.assertEqual(BatchStatus.DAMAGED.value, "DAMAGED")
    
    def test_batch_status_recalled(self):
        """اختبار الدفعة المسحوبة"""
        self.assertEqual(BatchStatus.RECALLED.value, "RECALLED")
    
    def test_all_batch_statuses(self):
        """اختبار عدد جميع حالات الدفعات"""
        statuses = list(BatchStatus)
        self.assertEqual(len(statuses), 5)


class TestABCAnalysisResultCreation(unittest.TestCase):
    """اختبارات إنشاء نتائج تحليل ABC"""
    
    def test_abc_analysis_default_values(self):
        """اختبار القيم الافتراضية"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج 1"
        )
        
        self.assertEqual(result.product_id, 1)
        self.assertEqual(result.product_code, "P001")
        self.assertEqual(result.product_name, "منتج 1")
        self.assertEqual(result.annual_sales_quantity, Decimal('0'))
        self.assertEqual(result.abc_category, ABCCategory.C.value)
    
    def test_abc_analysis_with_values(self):
        """اختبار إنشاء تحليل مع قيم"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج عالي القيمة",
            annual_sales_quantity=Decimal('1000'),
            annual_sales_value=Decimal('50000'),
            current_stock=Decimal('500')
        )
        
        self.assertEqual(result.annual_sales_quantity, Decimal('1000'))
        self.assertEqual(result.annual_sales_value, Decimal('50000'))
        self.assertEqual(result.current_stock, Decimal('500'))


class TestABCAnalysisCategoryLabel(unittest.TestCase):
    """اختبارات تسمية فئات التحليل"""
    
    def test_category_a_label(self):
        """اختبار تسمية فئة A"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.A.value
        )
        self.assertEqual(result.category_label, "فئة A - عالية القيمة")
    
    def test_category_b_label(self):
        """اختبار تسمية فئة B"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.B.value
        )
        self.assertEqual(result.category_label, "فئة B - متوسطة القيمة")
    
    def test_category_c_label(self):
        """اختبار تسمية فئة C"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.C.value
        )
        self.assertEqual(result.category_label, "فئة C - منخفضة القيمة")


class TestABCAnalysisAttention(unittest.TestCase):
    """اختبارات الحاجة للانتباه"""
    
    def test_category_a_needs_attention(self):
        """اختبار منتج A بدون مبيعات حديثة"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.A.value,
            days_since_last_sale=45
        )
        self.assertTrue(result.needs_attention)
    
    def test_category_a_recent_sales(self):
        """اختبار منتج A مع مبيعات حديثة"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.A.value,
            days_since_last_sale=10
        )
        self.assertFalse(result.needs_attention)
    
    def test_high_value_stagnant_stock(self):
        """اختبار مخزون راكد بقيمة عالية"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            stock_value=Decimal('15000'),
            days_since_last_sale=70
        )
        self.assertTrue(result.needs_attention)


class TestABCAnalysisRecommendations(unittest.TestCase):
    """اختبارات توليد التوصيات"""
    
    def test_recommendations_category_a(self):
        """اختبار توصيات فئة A"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.A.value
        )
        result.generate_recommendations()
        
        self.assertGreater(len(result.recommendations), 0)
        self.assertEqual(result.priority_level, 5)
        self.assertIn("مراقبة دقيقة", result.recommendations[0])
    
    def test_recommendations_category_b(self):
        """اختبار توصيات فئة B"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.B.value
        )
        result.generate_recommendations()
        
        self.assertGreater(len(result.recommendations), 0)
        self.assertEqual(result.priority_level, 3)
    
    def test_recommendations_category_c(self):
        """اختبار توصيات فئة C"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            abc_category=ABCCategory.C.value
        )
        result.generate_recommendations()
        
        self.assertGreater(len(result.recommendations), 0)
        self.assertEqual(result.priority_level, 1)


class TestABCAnalysisToDict(unittest.TestCase):
    """اختبارات تحويل التحليل إلى قاموس"""
    
    def test_to_dict(self):
        """اختبار تحويل إلى قاموس"""
        today = date.today()
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            annual_sales_value=Decimal('50000'),
            analysis_date=today
        )
        
        data = result.to_dict()
        self.assertEqual(data['product_id'], 1)
        self.assertEqual(data['product_code'], "P001")
        self.assertEqual(data['annual_sales_value'], 50000.0)
        self.assertEqual(data['analysis_date'], today.isoformat())


class TestSafetyStockConfigCreation(unittest.TestCase):
    """اختبارات إنشاء إعدادات الأرصدة الآمنة"""
    
    def test_safety_stock_config_defaults(self):
        """اختبار القيم الافتراضية"""
        config = SafetyStockConfig(product_id=1)
        
        self.assertEqual(config.product_id, 1)
        self.assertEqual(config.reorder_point, Decimal('0'))
        self.assertEqual(config.safety_stock, Decimal('0'))
        self.assertEqual(config.lead_time_days, 7)
        self.assertEqual(config.service_level, Decimal('95'))
    
    def test_safety_stock_config_with_values(self):
        """اختبار إنشاء إعدادات مع قيم"""
        config = SafetyStockConfig(
            product_id=1,
            product_code="P001",
            product_name="منتج",
            reorder_point=Decimal('100'),
            safety_stock=Decimal('50'),
            average_daily_demand=Decimal('10')
        )
        
        self.assertEqual(config.reorder_point, Decimal('100'))
        self.assertEqual(config.safety_stock, Decimal('50'))
        self.assertEqual(config.average_daily_demand, Decimal('10'))


class TestSafetyStockStatusLabel(unittest.TestCase):
    """اختبارات تسمية حالات الأرصدة الآمنة"""
    
    def test_status_label_normal(self):
        """اختبار تسمية الحالة العادية"""
        config = SafetyStockConfig(
            product_id=1,
            reorder_status=ReorderStatus.NORMAL.value
        )
        self.assertEqual(config.status_label, "عادي ✓")
    
    def test_status_label_approaching(self):
        """اختبار تسمية الاقتراب من نقطة الطلب"""
        config = SafetyStockConfig(
            product_id=1,
            reorder_status=ReorderStatus.APPROACHING.value
        )
        self.assertEqual(config.status_label, "يقترب من نقطة الطلب ⚠️")
    
    def test_status_label_critical(self):
        """اختبار تسمية الحالة الحرجة"""
        config = SafetyStockConfig(
            product_id=1,
            reorder_status=ReorderStatus.CRITICAL.value
        )
        self.assertEqual(config.status_label, "حرج جداً ⛔")


class TestSafetyStockDaysUntilStockout(unittest.TestCase):
    """اختبارات حساب الأيام حتى نفاذ المخزون"""
    
    def test_days_until_stockout(self):
        """اختبار حساب الأيام"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('100'),
            average_daily_demand=Decimal('10')
        )
        self.assertEqual(config.days_until_stockout, 10)
    
    def test_days_until_stockout_zero_demand(self):
        """اختبار بدون طلب"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('100'),
            average_daily_demand=Decimal('0')
        )
        self.assertIsNone(config.days_until_stockout)


class TestSafetyStockQuantityBelowReorder(unittest.TestCase):
    """اختبارات حساب الكمية تحت نقطة الطلب"""
    
    def test_quantity_below_reorder(self):
        """اختبار الكمية تحت النقطة"""
        config = SafetyStockConfig(
            product_id=1,
            reorder_point=Decimal('100'),
            current_stock=Decimal('60')
        )
        self.assertEqual(config.quantity_below_reorder, Decimal('40'))
    
    def test_quantity_above_reorder(self):
        """اختبار الكمية فوق النقطة"""
        config = SafetyStockConfig(
            product_id=1,
            reorder_point=Decimal('100'),
            current_stock=Decimal('150')
        )
        self.assertEqual(config.quantity_below_reorder, Decimal('0'))


class TestSafetyStockCalculations(unittest.TestCase):
    """اختبارات عمليات الحسابات"""
    
    def test_calculate_reorder_point(self):
        """اختبار حساب نقطة الطلب"""
        config = SafetyStockConfig(
            product_id=1,
            average_daily_demand=Decimal('10'),
            lead_time_days=7,
            safety_stock=Decimal('50')
        )
        config.calculate_reorder_point()
        
        expected = (Decimal('10') * 7) + Decimal('50')
        self.assertEqual(config.reorder_point, expected)
    
    def test_calculate_safety_stock_simple(self):
        """اختبار حساب المخزون الآمن - طريقة بسيطة"""
        config = SafetyStockConfig(
            product_id=1,
            average_daily_demand=Decimal('10'),
            lead_time_days=7
        )
        config.calculate_safety_stock()
        
        expected = Decimal('10') * 7 * Decimal('0.5')
        self.assertEqual(config.safety_stock, expected)
    
    def test_calculate_economic_order_quantity(self):
        """اختبار حساب كمية الطلب الاقتصادية"""
        config = SafetyStockConfig(
            product_id=1,
            order_cost=Decimal('50'),
            holding_cost_percentage=Decimal('20')
        )
        config.calculate_economic_order_quantity(
            annual_demand=Decimal('1000'),
            unit_cost=Decimal('100')
        )
        
        self.assertGreater(config.economic_order_quantity, 0)


class TestSafetyStockReorderStatus(unittest.TestCase):
    """اختبارات تحديث حالة الطلب"""
    
    def test_update_reorder_status_stockout(self):
        """اختبار حالة نفاذ المخزون"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('0')
        )
        config.update_reorder_status()
        self.assertEqual(config.reorder_status, ReorderStatus.STOCKOUT.value)
    
    def test_update_reorder_status_critical(self):
        """اختبار الحالة الحرجة"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('10'),
            minimum_stock=Decimal('20')
        )
        config.update_reorder_status()
        self.assertEqual(config.reorder_status, ReorderStatus.CRITICAL.value)
    
    def test_update_reorder_status_reorder(self):
        """اختبار حالة إعادة الطلب"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('50'),
            minimum_stock=Decimal('10'),
            reorder_point=Decimal('100')
        )
        config.update_reorder_status()
        self.assertEqual(config.reorder_status, ReorderStatus.REORDER.value)
    
    def test_update_reorder_status_approaching(self):
        """اختبار الاقتراب من النقطة"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('110'),
            minimum_stock=Decimal('10'),
            reorder_point=Decimal('100')
        )
        config.update_reorder_status()
        self.assertEqual(config.reorder_status, ReorderStatus.APPROACHING.value)
    
    def test_update_reorder_status_normal(self):
        """اختبار الحالة العادية"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('200'),
            minimum_stock=Decimal('10'),
            reorder_point=Decimal('100')
        )
        config.update_reorder_status()
        self.assertEqual(config.reorder_status, ReorderStatus.NORMAL.value)


class TestSafetyStockSuggestedOrder(unittest.TestCase):
    """اختبارات حساب الطلب المقترح"""
    
    def test_calculate_suggested_order_below_reorder(self):
        """اختبار الطلب المقترح تحت النقطة"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('50'),
            reorder_point=Decimal('100'),
            maximum_stock=Decimal('500'),
            economic_order_quantity=Decimal('100')
        )
        config.calculate_suggested_order()
        
        self.assertGreater(config.suggested_order_quantity, 0)
    
    def test_calculate_suggested_order_above_reorder(self):
        """اختبار الطلب المقترح فوق النقطة"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('200'),
            reorder_point=Decimal('100'),
            maximum_stock=Decimal('500')
        )
        config.calculate_suggested_order()
        
        self.assertEqual(config.suggested_order_quantity, Decimal('0'))


class TestSafetyStockDictConversion(unittest.TestCase):
    """اختبارات تحويل الإعدادات إلى قاموس"""
    
    def test_to_dict(self):
        """اختبار تحويل إلى قاموس"""
        today = date.today()
        config = SafetyStockConfig(
            id=1,
            product_id=1,
            product_code="P001",
            product_name="منتج",
            reorder_point=Decimal('100'),
            current_stock=Decimal('50'),
            last_reorder_date=today
        )
        
        data = config.to_dict()
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['product_id'], 1)
        self.assertEqual(data['reorder_point'], 100.0)
        self.assertEqual(data['current_stock'], 50.0)


class TestInventoryOptimizationEdgeCases(unittest.TestCase):
    """اختبارات الحالات الحدودية"""
    
    def test_zero_demand(self):
        """اختبار صفر الطلب"""
        config = SafetyStockConfig(
            product_id=1,
            average_daily_demand=Decimal('0')
        )
        config.calculate_reorder_point()
        self.assertEqual(config.reorder_point, config.safety_stock)
    
    def test_large_demand(self):
        """اختبار طلب كبير"""
        config = SafetyStockConfig(
            product_id=1,
            average_daily_demand=Decimal('10000'),
            lead_time_days=30,
            safety_stock=Decimal('50000')
        )
        self.assertEqual(config.average_daily_demand, Decimal('10000'))
    
    def test_fractional_stock(self):
        """اختبار أسهم كسرية"""
        config = SafetyStockConfig(
            product_id=1,
            current_stock=Decimal('0.5'),
            average_daily_demand=Decimal('0.25')
        )
        self.assertEqual(config.days_until_stockout, 2)


class TestInventoryOptimizationIntegration(unittest.TestCase):
    """اختبارات التكامل الشاملة"""
    
    def test_complete_safety_stock_analysis(self):
        """اختبار تحليل كامل للأرصدة الآمنة"""
        config = SafetyStockConfig(
            product_id=1,
            product_code="P001",
            product_name="منتج عالي الطلب",
            average_daily_demand=Decimal('50'),
            lead_time_days=7,
            # ضبط المخزون الحالي أعلى من 120% من نقطة إعادة الطلب لضمان الحالة العادية
            current_stock=Decimal('700'),
            maximum_stock=Decimal('700'),
            minimum_stock=Decimal('100'),
            order_cost=Decimal('100'),
            holding_cost_percentage=Decimal('15'),
            service_level=Decimal('95')
        )
        
        # تنفيذ العمليات الحسابية
        config.calculate_safety_stock()
        config.calculate_reorder_point()
        config.update_reorder_status()
        config.calculate_suggested_order()
        
        # التحقق من النتائج
        self.assertGreater(config.reorder_point, 0)
        self.assertEqual(config.reorder_status, ReorderStatus.NORMAL.value)
    
    def test_complete_abc_analysis(self):
        """اختبار تحليل ABC كامل"""
        result = ABCAnalysisResult(
            product_id=1,
            product_code="P001",
            product_name="منتج فاخر",
            annual_sales_quantity=Decimal('5000'),
            annual_sales_value=Decimal('500000'),
            current_stock=Decimal('500'),
            stock_value=Decimal('50000'),
            abc_category=ABCCategory.A.value,
            percentage_of_total_value=Decimal('45'),
            sales_frequency=120,
            last_sale_date=date.today() - timedelta(days=2),
            days_since_last_sale=2
        )
        
        result.generate_recommendations()
        
        self.assertEqual(result.priority_level, 5)
        self.assertFalse(result.needs_attention)
        self.assertGreater(len(result.recommendations), 0)


if __name__ == '__main__':
    unittest.main()




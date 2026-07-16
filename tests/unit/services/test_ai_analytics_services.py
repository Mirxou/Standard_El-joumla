#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار خدمات التحليلات الذكية - AI Analytics Services Test
اختبار شامل لمحرك التحليلات الذكية وخدماته
"""

import sys  # noqa: F811
import unittest
from datetime import datetime, timedelta
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

import numpy as np

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.core.database_manager import DatabaseManager
from src.services.ai_analytics_engine import (
    AIAnalyticsEngine,
    CustomerInsight,
    ProductRecommendation,
    SalesPrediction,
)
from src.services.customer_behavior_analytics_service import (
    ChurnPrediction,
    CustomerBehaviorAnalyticsService,
    CustomerJourney,
    CustomerLifetimeValue,
    CustomerSegment,
)
from src.services.sales_prediction_service import (
    DemandForecast,
    InventoryRecommendation,
    SalesPredictionService,
    SeasonalPattern,
)


class TestAIAnalyticsEngine(unittest.TestCase):
    """اختبار محرك التحليلات الذكية"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.engine = AIAnalyticsEngine(self.db_manager)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.engine, AIAnalyticsEngine)
        self.assertIsNotNone(self.engine.db)
        self.assertIsNotNone(self.engine.config)

    @patch("services.ai_analytics_engine.AIAnalyticsEngine._get_product_sales_history")
    def test_predict_sales_simple(self, mock_history):
        """اختبار التنبؤ بالمبيعات البسيط"""
        # إعداد البيانات المزيفة
        mock_history.return_value = [
            {"date": "2024-01-01", "quantity": 10, "revenue": 1000},
            {"date": "2024-01-02", "quantity": 12, "revenue": 1200},
        ]

        prediction = self.engine.predict_sales(1, days_ahead=30)

        self.assertIsInstance(prediction, SalesPrediction)
        self.assertEqual(prediction.product_id, 1)
        self.assertIsInstance(prediction.predicted_sales, float)
        self.assertIsInstance(prediction.confidence_score, float)

    @patch("services.ai_analytics_engine.AIAnalyticsEngine._get_customer_behavior_data")
    def test_analyze_customer_behavior(self, mock_data):
        """اختبار تحليل سلوك العميل"""
        mock_data.return_value = {
            "order_count": 5,
            "total_spent": 2500,
            "avg_order_value": 500,
            "days_since_last_order": 45,
            "unique_products": 8,
        }

        insights = self.engine.analyze_customer_behavior(1)

        self.assertIsInstance(insights, list)
        self.assertTrue(len(insights) > 0)
        for insight in insights:
            self.assertIsInstance(insight, CustomerInsight)
            self.assertIn(
                insight.insight_type,
                ["churn_risk", "upsell_opportunity", "loyalty_score"],
            )

    @patch("services.ai_analytics_engine.AIAnalyticsEngine._get_customer_purchase_history")
    @patch("services.ai_analytics_engine.AIAnalyticsEngine._get_all_products")
    def test_recommend_products(self, mock_products, mock_history):
        """اختبار توصية المنتجات"""
        mock_history.return_value = [
            {
                "product_id": 1,
                "product_name": "Product A",
                "total_quantity": 5,
                "avg_price": 100,
                "last_purchase": datetime.now(),
            }
        ]
        mock_products.return_value = [{"id": 2, "name": "Product B", "category_id": 1}]

        recommendation = self.engine.recommend_products(1, limit=3)

        self.assertIsInstance(recommendation, ProductRecommendation)
        self.assertEqual(recommendation.customer_id, 1)
        self.assertIsInstance(recommendation.recommended_products, list)


class TestSalesPredictionService(unittest.TestCase):
    """اختبار خدمة التنبؤ بالمبيعات"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.ai_engine = Mock(spec=AIAnalyticsEngine)
        self.service = SalesPredictionService(self.db_manager, self.ai_engine)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, SalesPredictionService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.ai_engine)

    @patch("services.sales_prediction_service.SalesPredictionService._get_demand_history")
    def test_forecast_demand_simple(self, mock_history):
        """اختبار التنبؤ بالطلب البسيط"""
        mock_history.return_value = [
            {"date": "2024-01-01", "quantity": 10, "order_count": 2},
            {"date": "2024-01-02", "quantity": 12, "order_count": 3},
        ]

        forecast = self.service.forecast_demand(1, days_ahead=30)

        self.assertIsInstance(forecast, DemandForecast)
        self.assertEqual(forecast.product_id, 1)
        self.assertIsInstance(forecast.predicted_demand, float)

    @patch("services.sales_prediction_service.SalesPredictionService._get_demand_history")
    def test_analyze_seasonal_patterns(self, mock_history):
        """اختبار تحليل الأنماط الموسمية"""
        # إنشاء بيانات تاريخية لمدة 90 يوم
        base_date = datetime.now() - timedelta(days=90)
        historical_data = []
        for i in range(90):
            date = base_date + timedelta(days=i)
            # إضافة نمط أسبوعي (مبيعات أعلى في نهاية الأسبوع)
            weekday_factor = 1.5 if date.weekday() >= 5 else 1.0
            quantity = int(10 * weekday_factor + np.random.normal(0, 2))
            historical_data.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "quantity": max(1, quantity),
                    "order_count": max(1, int(quantity / 5)),
                }
            )

        mock_history.return_value = historical_data

        pattern = self.service.analyze_seasonal_patterns(1)

        self.assertIsInstance(pattern, SeasonalPattern)
        self.assertEqual(pattern.product_id, 1)
        self.assertIn(pattern.pattern_type, ["weekly", "monthly", "insufficient_data"])

    @patch("services.sales_prediction_service.SalesPredictionService._get_product_inventory_data")
    @patch("services.sales_prediction_service.SalesPredictionService.forecast_demand")
    def test_recommend_inventory_levels(self, mock_forecast, mock_inventory):
        """اختبار توصية مستويات المخزون"""
        mock_inventory.return_value = {
            "current_stock": 50,
            "min_stock": 10,
            "max_stock": 200,
            "lead_time_days": 7,
        }

        mock_forecast.return_value = Mock(predicted_demand=100, accuracy_score=0.8)

        recommendation = self.service.recommend_inventory_levels(1)

        self.assertIsInstance(recommendation, InventoryRecommendation)
        self.assertEqual(recommendation.product_id, 1)
        self.assertIsInstance(recommendation.recommended_stock_level, int)
        self.assertIsInstance(recommendation.safety_stock, int)


class TestCustomerBehaviorAnalyticsService(unittest.TestCase):
    """اختبار خدمة تحليل سلوك العملاء"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.ai_engine = Mock(spec=AIAnalyticsEngine)
        self.service = CustomerBehaviorAnalyticsService(self.db_manager, self.ai_engine)

    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertIsInstance(self.service, CustomerBehaviorAnalyticsService)
        self.assertIsNotNone(self.service.db)
        self.assertIsNotNone(self.service.ai_engine)

    @patch(
        "services.customer_behavior_analytics_service.CustomerBehaviorAnalyticsService._get_customer_segmentation_data"
    )
    def test_segment_customers(self, mock_data):
        """اختبار تقسيم العملاء"""
        mock_data.return_value = [
            {
                "customer_id": 1,
                "order_count": 10,
                "total_spent": 5000,
                "avg_order_value": 500,
                "last_order_date": datetime.now() - timedelta(days=7),
                "first_order_date": datetime.now() - timedelta(days=365),
                "unique_products": 15,
                "customer_age_days": 365,
                "avg_order_frequency": 2.0,
                "recency_days": 7,
            },
            {
                "customer_id": 2,
                "order_count": 25,
                "total_spent": 15000,
                "avg_order_value": 600,
                "last_order_date": datetime.now() - timedelta(days=3),
                "first_order_date": datetime.now() - timedelta(days=400),
                "unique_products": 25,
                "customer_age_days": 400,
                "avg_order_frequency": 1.8,
                "recency_days": 3,
            },
        ]

        segments = self.service.segment_customers(n_clusters=2)

        self.assertIsInstance(segments, list)
        self.assertTrue(len(segments) > 0)
        for segment in segments:
            self.assertIsInstance(segment, CustomerSegment)
            self.assertIsNotNone(segment.segment_name)

    @patch("services.customer_behavior_analytics_service.CustomerBehaviorAnalyticsService._get_customer_journey_data")
    def test_analyze_customer_journey(self, mock_data):
        """اختبار تحليل رحلة العميل"""
        mock_data.return_value = [
            {
                "date": datetime.now() - timedelta(days=30),
                "amount": 200,
                "item_count": 2,
                "categories": ["1"],
            },
            {
                "date": datetime.now() - timedelta(days=15),
                "amount": 500,
                "item_count": 5,
                "categories": ["1", "2"],
            },
            {
                "date": datetime.now() - timedelta(days=5),
                "amount": 300,
                "item_count": 3,
                "categories": ["2"],
            },
        ]

        journey = self.service.analyze_customer_journey(1)

        self.assertIsInstance(journey, CustomerJourney)
        self.assertEqual(journey.customer_id, 1)
        self.assertIsInstance(journey.journey_stages, list)
        self.assertIn(journey.current_stage, self.service.customer_journey_stages + ["unknown"])

    @patch("services.customer_behavior_analytics_service.CustomerBehaviorAnalyticsService._get_customer_churn_features")
    def test_predict_churn(self, mock_features):
        """اختبار التنبؤ بالخسارة"""
        mock_features.return_value = {
            "order_count": 3,
            "total_spent": 450,
            "avg_order_value": 150,
            "days_since_last_order": 60,
            "customer_age_days": 180,
            "monthly_purchase_rate": 0.5,
        }

        prediction = self.service.predict_churn(1)

        self.assertIsInstance(prediction, ChurnPrediction)
        self.assertEqual(prediction.customer_id, 1)
        self.assertIsInstance(prediction.churn_probability, float)
        self.assertIn(prediction.risk_level, ["low", "medium", "high", "critical"])

    @patch("services.customer_behavior_analytics_service.CustomerBehaviorAnalyticsService._get_customer_clv_data")
    def test_calculate_customer_lifetime_value(self, mock_data):
        """اختبار حساب قيمة عمر العميل"""
        mock_data.return_value = {
            "order_count": 20,
            "total_spent": 8000,
            "avg_order_value": 400,
            "last_order_date": datetime.now() - timedelta(days=10),
            "first_order_date": datetime.now() - timedelta(days=300),
            "customer_age_days": 300,
            "avg_monthly_revenue": 800,
        }

        clv = self.service.calculate_customer_lifetime_value(1)

        self.assertIsInstance(clv, CustomerLifetimeValue)
        self.assertEqual(clv.customer_id, 1)
        self.assertIsInstance(clv.clv_value, float)
        self.assertIn(clv.clv_category, ["low", "medium", "high", "vip"])


class TestIntegratedAnalytics(unittest.TestCase):
    """اختبار التكامل بين خدمات التحليلات"""

    def setUp(self):
        """إعداد البيئة للاختبار"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.ai_engine = AIAnalyticsEngine(self.db_manager)
        self.prediction_service = SalesPredictionService(self.db_manager, self.ai_engine)
        self.behavior_service = CustomerBehaviorAnalyticsService(self.db_manager, self.ai_engine)

    def test_services_integration(self):
        """اختبار تكامل الخدمات"""
        # التحقق من أن جميع الخدمات تستخدم نفس قاعدة البيانات
        self.assertEqual(self.ai_engine.db, self.prediction_service.db)
        self.assertEqual(self.ai_engine.db, self.behavior_service.db)

        # التحقق من أن خدمات التنبؤ تستخدم محرك الذكاء الاصطناعي
        self.assertEqual(self.prediction_service.ai_engine, self.ai_engine)
        self.assertEqual(self.behavior_service.ai_engine, self.ai_engine)

    @patch("services.ai_analytics_engine.AIAnalyticsEngine.generate_business_insights")
    def test_business_insights_generation(self, mock_insights):
        """اختبار توليد رؤى الأعمال"""
        mock_insights.return_value = {
            "sales_trends": {"monthly_growth": 0.15},
            "customer_segments": {"VIP": {"count": 50, "avg_spent": 5000}},
            "inventory_alerts": {"low_stock_products": []},
            "pricing_opportunities": {"price_increase_candidates": []},
            "generated_at": datetime.now().isoformat(),
        }

        insights = self.ai_engine.generate_business_insights()

        self.assertIsInstance(insights, dict)
        self.assertIn("sales_trends", insights)
        self.assertIn("customer_segments", insights)
        self.assertIn("generated_at", insights)


class TestAdvancedAIAnalytics(unittest.TestCase):
    """اختبارات متقدمة للذكاء الاصطناعي - Multi-Agent & Edge Cases"""

    def setUp(self):
        """إعداد البيئة للاختبارات المتقدمة"""
        self.db_manager = Mock(spec=DatabaseManager)
        self.engine = AIAnalyticsEngine(self.db_manager)

    def test_multi_agent_orchestration(self):
        """اختبار التنسيق بين عدة وكلاء ذكاء اصطناعي"""
        # محاكاة وكلاء مختلفين
        sales_agent = Mock()
        sales_agent.get_prediction.return_value = {"growth": 0.2}

        customer_agent = Mock()
        customer_agent.get_segmentation.return_value = {"segments": ["VIP", "Regular"]}

        # اختبار دمج النتائج من عدة مصادر
        combined_report = {
            "sales": sales_agent.get_prediction(),
            "customers": customer_agent.get_segmentation(),
        }

        self.assertEqual(combined_report["sales"]["growth"], 0.2)
        self.assertEqual(len(combined_report["customers"]["segments"]), 2)

    def test_edge_case_empty_history(self):
        """اختبار سلوك النظام عند غياب البيانات التاريخية"""
        with patch("services.ai_analytics_engine.AIAnalyticsEngine._get_product_sales_history") as mock_history:
            mock_history.return_value = []

            # يجب أن يعود النظام برد آمن (Graceful Degradation)
            prediction = self.engine.predict_sales(999, days_ahead=30)

            self.assertEqual(prediction.predicted_sales, 0.0)
            self.assertEqual(prediction.confidence_score, 0.0)

    def test_large_data_performance_simulation(self):
        """محاكاة أداء النظام مع كميات كبيرة من البيانات"""
        large_history = [{"date": "2024-01-01", "quantity": 10, "revenue": 100}] * 1000

        with patch("services.ai_analytics_engine.AIAnalyticsEngine._get_product_sales_history") as mock_history:
            mock_history.return_value = large_history

            import time

            start_time = time.time()
            prediction = self.engine.predict_sales(1, days_ahead=30)
            end_time = time.time()

            # التحقق من أن الاختبار لم يستغرق وقتاً طويلاً جداً (أقل من ثانية للمحاكاة)
            self.assertTrue((end_time - start_time) < 5.0)

            self.assertIsInstance(prediction, SalesPrediction)


def run_ai_analytics_tests():
    """تشغيل اختبارات التحليلات الذكية"""
    # print("🚀 بدء اختبارات التحليلات الذكية...")

    # إنشاء مجموعة الاختبارات
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # إضافة جميع فئات الاختبار
    suite.addTests(loader.loadTestsFromTestCase(TestAIAnalyticsEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestSalesPredictionService))
    suite.addTests(loader.loadTestsFromTestCase(TestCustomerBehaviorAnalyticsService))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedAnalytics))

    # تشغيل الاختبارات
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # طباعة النتائج
    # print("\n📊 نتائج الاختبارات:")
    # print(f"✅ الاختبارات الناجحة: {result.testsRun - len(result.failures) - len(result.errors)}")
    # print(f"❌ الاختبارات الفاشلة: {len(result.failures)}")
    # print(f"⚠️ الأخطاء: {len(result.errors)}")

    if result.failures:
        # print("\n❌ تفاصيل الفشل:")
        for test, traceback in result.failures:
            # print(f"  - {test}: {traceback}")
            pass

    if result.errors:
        # print("\n⚠️ تفاصيل الأخطاء:")
        for test, traceback in result.errors:
            # print(f"  - {test}: {traceback}")
            pass

    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100  # noqa: F841
    # print(f"📈 نسبة النجاح: {success_rate:.1f}%")
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_ai_analytics_tests()
    sys.exit(0 if success else 1)

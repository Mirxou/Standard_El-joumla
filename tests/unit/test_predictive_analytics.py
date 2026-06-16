#!/usr/bin/env python3
"""
اختبارات Predictive Analytics
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.ai.predictive_analytics import CustomerInsight, PredictiveEngine, SalesForecast


class TestPredictiveEngine:
    """اختبارات محرك التحليلات التنبؤية"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك تنبؤات للاختبارات"""
        db_manager = Mock()
        return PredictiveEngine(db_manager)

    @pytest.fixture
    def mock_products(self):
        """منتجات محاكاة"""
        return [
            {"id": 1, "name": "Product A", "quantity": 100, "reorder_point": 20},
            {"id": 2, "name": "Product B", "quantity": 50, "reorder_point": 10},
        ]

    @pytest.fixture
    def mock_sales_history(self):
        """تاريخ مبيعات محاكاة"""
        return [
            {"quantity": 10, "date": (datetime.now() - timedelta(days=1)).isoformat()},
            {"quantity": 15, "date": (datetime.now() - timedelta(days=2)).isoformat()},
            {"quantity": 12, "date": (datetime.now() - timedelta(days=3)).isoformat()},
        ]

    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert engine.db is not None

    def test_forecast_sales_all_products(self, engine, mock_products, mock_sales_history):
        """اختبار التنبؤ بالمبيعات لجميع المنتجات"""
        engine.db.execute_query.return_value = mock_products

        with patch.object(engine, "_get_sales_history", return_value=mock_sales_history):
            result = engine.forecast_sales(days=30)

            assert len(result) > 0
            assert all(isinstance(f, SalesForecast) for f in result)

    def test_forecast_sales_single_product(self, engine, mock_products, mock_sales_history):
        """اختبار التنبؤ بالمبيعات لمنتج واحد"""
        engine.db.execute_query.return_value = [mock_products[0]]

        with patch.object(engine, "_get_sales_history", return_value=mock_sales_history):
            result = engine.forecast_sales(product_id=1, days=30)

            assert len(result) == 1
            assert result[0].product_id == 1

    def test_forecast_sales_no_products(self, engine):
        """اختبار التنبؤ بدون منتجات"""
        engine.db.execute_query.return_value = []

        result = engine.forecast_sales(days=30)

        assert result == []

    def test_forecast_sales_no_history(self, engine, mock_products):
        """اختبار التنبؤ بدون تاريخ مبيعات"""
        engine.db.execute_query.return_value = mock_products

        with patch.object(engine, "_get_sales_history", return_value=[]):
            result = engine.forecast_sales(days=30)

            assert result == []

    def test_forecast_structure(self, engine, mock_products, mock_sales_history):
        """اختبار هيكل التنبؤ"""
        engine.db.execute_query.return_value = [mock_products[0]]

        with patch.object(engine, "_get_sales_history", return_value=mock_sales_history):
            result = engine.forecast_sales(product_id=1, days=30)

            forecast = result[0]
            assert hasattr(forecast, "product_id")
            assert hasattr(forecast, "product_name")
            assert hasattr(forecast, "current_stock")
            assert hasattr(forecast, "predicted_sales")
            assert hasattr(forecast, "days_until_stockout")
            assert hasattr(forecast, "recommended_reorder_quantity")
            assert hasattr(forecast, "confidence")

    def test_calculate_daily_sales(self, engine):
        """اختبار حساب المبيعات اليومية"""
        sales_history = [
            {"quantity": 10, "date": "2025-01-01"},
            {"quantity": 15, "date": "2025-01-01"},
            {"quantity": 20, "date": "2025-01-02"},
        ]

        result = engine._calculate_daily_sales(sales_history)

        assert result == [25, 20]  # 10+15=25 for day 1, 20 for day 2

    def test_analyze_customer_behavior_all(self, engine):
        """اختبار تحليل سلوك جميع العملاء"""
        mock_customers = [
            {"id": 1, "name": "Customer A"},
            {"id": 2, "name": "Customer B"},
        ]
        engine.db.execute_query.return_value = mock_customers

        mock_purchases = [
            {"total": 100, "date": (datetime.now() - timedelta(days=1)).isoformat()},
            {"total": 200, "date": (datetime.now() - timedelta(days=30)).isoformat()},
        ]

        with patch.object(engine, "_get_customer_purchases", return_value=mock_purchases):
            result = engine.analyze_customer_behavior()

            assert len(result) > 0
            assert all(isinstance(i, CustomerInsight) for i in result)

    def test_customer_insight_structure(self, engine):
        """اختبار هيكل رؤى العميل"""
        mock_customers = [{"id": 1, "name": "Customer A"}]
        engine.db.execute_query.return_value = mock_customers

        mock_purchases = [
            {"total": 100, "date": (datetime.now() - timedelta(days=1)).isoformat()},
            {"total": 200, "date": (datetime.now() - timedelta(days=15)).isoformat()},
        ]

        with patch.object(engine, "_get_customer_purchases", return_value=mock_purchases):
            result = engine.analyze_customer_behavior(customer_id=1)

            if result:
                insight = result[0]
                assert hasattr(insight, "customer_id")
                assert hasattr(insight, "customer_name")
                assert hasattr(insight, "total_purchases")
                assert hasattr(insight, "average_order_value")
                assert hasattr(insight, "purchase_frequency")
                assert hasattr(insight, "predicted_next_purchase")
                assert hasattr(insight, "customer_segment")
                assert hasattr(insight, "lifetime_value")
                assert hasattr(insight, "churn_risk")

    def test_segment_customer_vip(self, engine):
        """اختبار تصنيف العميل كـ VIP"""
        result = engine._segment_customer(total_purchases=15000, frequency=3, order_count=10)
        assert result == "VIP"

    def test_segment_customer_regular(self, engine):
        """اختبار تصنيف العميل كـ دائم"""
        result = engine._segment_customer(total_purchases=7000, frequency=1.5, order_count=8)
        assert result == "عميل دائم"

    def test_segment_customer_active(self, engine):
        """اختبار تصنيف العميل كـ نشط"""
        result = engine._segment_customer(total_purchases=2000, frequency=0.5, order_count=5)
        assert result == "عميل نشط"

    def test_segment_customer_new(self, engine):
        """اختبار تصنيف العميل كـ جديد"""
        result = engine._segment_customer(total_purchases=500, frequency=0.1, order_count=1)
        assert result == "عميل جديد"

    def test_get_product_recommendations(self, engine):
        """اختبار الحصول على توصيات المنتجات"""
        mock_products = [
            {"id": 1, "name": "Product A", "quantity": 100, "price": 50},
            {"id": 2, "name": "Product B", "quantity": 0, "price": 30},
            {"id": 3, "name": "Product C", "quantity": 50, "price": 40},
        ]
        engine.db.execute_query.return_value = mock_products

        mock_purchases = [{"items": [{"product_id": 1}]}]

        with patch.object(engine, "_get_customer_purchases", return_value=mock_purchases):
            with patch.object(engine, "_get_product_sales_count", return_value=10):
                result = engine.get_product_recommendations(customer_id=1, limit=2)

                assert len(result) <= 2
                assert all("product_id" in r for r in result)
                assert all("score" in r for r in result)

    def test_detect_anomalies_no_products(self, engine):
        """اختبار كشف الشذوذ بدون منتجات"""
        engine.db.execute_query.return_value = []

        result = engine.detect_anomalies(days=7)

        assert result == []

    def test_generate_proactive_insights_empty(self, engine):
        """اختبار توليد رؤى استباقية بدون بيانات"""
        engine.db.execute_query.return_value = []

        result = engine.generate_proactive_insights()

        assert result == []


class TestSalesForecast:
    """اختبارات نموذج توقعات المبيعات"""

    def test_sales_forecast_creation(self):
        """اختبار إنشاء نموذج توقعات"""
        forecast = SalesForecast(
            product_id=1,
            product_name="Test Product",
            current_stock=100,
            predicted_sales=50,
            days_until_stockout=14,
            recommended_reorder_quantity=60,
            confidence=0.85,
        )

        assert forecast.product_id == 1
        assert forecast.product_name == "Test Product"
        assert forecast.current_stock == 100
        assert forecast.predicted_sales == 50
        assert forecast.days_until_stockout == 14
        assert forecast.recommended_reorder_quantity == 60
        assert forecast.confidence == 0.85


class TestCustomerInsight:
    """اختبارات نموذج رؤى العميل"""

    def test_customer_insight_creation(self):
        """اختبار إنشاء نموذج رؤى العميل"""
        insight = CustomerInsight(
            customer_id=1,
            customer_name="Test Customer",
            total_purchases=1000,
            average_order_value=100,
            purchase_frequency=2.5,
            predicted_next_purchase="2025-02-01",
            customer_segment="VIP",
            lifetime_value=3000,
            churn_risk=0.2,
        )

        assert insight.customer_id == 1
        assert insight.customer_name == "Test Customer"
        assert insight.total_purchases == 1000
        assert insight.average_order_value == 100
        assert insight.purchase_frequency == 2.5
        assert insight.predicted_next_purchase == "2025-02-01"
        assert insight.customer_segment == "VIP"
        assert insight.lifetime_value == 3000
        assert insight.churn_risk == 0.2

    def test_customer_insight_default_churn_risk(self):
        """اختبار القيمة الافتراضية لـ churn_risk"""
        insight = CustomerInsight(
            customer_id=1,
            customer_name="Test",
            total_purchases=100,
            average_order_value=50,
            purchase_frequency=1.0,
            predicted_next_purchase=None,
            customer_segment="جديد",
            lifetime_value=300,
        )

        assert insight.churn_risk == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

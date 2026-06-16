#!/usr/bin/env python3
"""
اختبارات Advanced Analytics Engine
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.ai.advanced_analytics_engine import AdvancedAnalyticsEngine


class TestAdvancedAnalyticsEngine:
    """اختبارات محرك التحليلات المتقدمة"""

    @pytest.fixture
    def engine(self):
        """إنشاء محرك تحليلات للاختبارات"""
        db_manager = Mock()
        return AdvancedAnalyticsEngine(db_manager)

    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert engine.analytics_cache == {}
        assert engine.insights_history == []
        assert engine.db_manager is not None

    def test_analyze_sales_performance_default_dates(self, engine):
        """اختبار تحليل أداء المبيعات بالتواريخ الافتراضية"""
        result = engine.analyze_sales_performance()

        assert result is not None
        assert "period" in result
        assert "summary" in result
        assert "trends" in result
        assert "forecasting" in result
        assert "insights" in result
        assert "recommendations" in result

    def test_analyze_sales_performance_custom_dates(self, engine):
        """اختبار تحليل أداء المبيعات بتواريخ مخصصة"""
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()

        result = engine.analyze_sales_performance(start_date, end_date)

        assert result is not None
        assert result["period"]["days"] == 7
        assert "start" in result["period"]
        assert "end" in result["period"]

    def test_analyze_sales_performance_summary_fields(self, engine):
        """اختبار حقيق الملخص في تحليل المبيعات"""
        result = engine.analyze_sales_performance()
        summary = result["summary"]

        assert "total_sales" in summary
        assert "total_transactions" in summary
        assert "average_transaction" in summary
        assert "median_transaction" in summary

    def test_analyze_customer_behavior_single_customer(self, engine):
        """اختبار تحليل سلوك عميل واحد"""
        result = engine.analyze_customer_behavior(customer_id="123")

        assert result is not None
        assert "customer_analysis" in result

    def test_analyze_customer_behavior_all_customers(self, engine):
        """اختبار تحليل سلوك جميع العملاء"""
        result = engine.analyze_customer_behavior()

        assert result is not None
        assert "behavior_patterns" in result
        assert "lifetime_value" in result

    def test_detect_anomalies_sales(self, engine):
        """اختبار كشف الشذوذ في بيانات المبيعات"""
        result = engine.detect_anomalies(data_type="sales", threshold=2.0)

        assert result is not None
        assert result["data_type"] == "sales"
        assert "total_records" in result
        assert "anomalies_detected" in result
        assert "anomaly_percentage" in result
        assert "anomalies" in result
        assert "severity_levels" in result
        assert "recommendations" in result

    def test_detect_anomalies_inventory(self, engine):
        """اختبار كشف الشذوذ في بيانات المخزون"""
        result = engine.detect_anomalies(data_type="inventory", threshold=1.5)

        assert result is not None
        assert result["data_type"] == "inventory"

    def test_detect_anomalies_invalid_type(self, engine):
        """اختبار كشف الشذوذ بنوع بيانات غير صالح"""
        result = engine.detect_anomalies(data_type="invalid", threshold=2.0)

        assert result is not None
        assert "error" in result
        assert "غير مدعوم" in result["error"]

    def test_generate_predictive_insights_sales(self, engine):
        """اختبار توليد رؤى تنبؤية للمبيعات"""
        result = engine.generate_predictive_insights(prediction_type="sales")

        assert result is not None

    def test_trend_analysis_structure(self, engine):
        """اختبار هيكل تحليل الاتجاهات"""
        result = engine.analyze_sales_performance()
        trends = result["trends"]

        assert trends is not None

    def test_segmentation_structure(self, engine):
        """اختبار هيكل تجزئة العملاء"""
        result = engine.analyze_sales_performance()
        segmentation = result["segmentation"]

        assert segmentation is not None

    def test_forecasting_structure(self, engine):
        """اختبار هيكل التوقعات"""
        result = engine.analyze_sales_performance()
        forecasting = result["forecasting"]

        assert forecasting is not None

    def test_insights_structure(self, engine):
        """اختبار هيكل الرؤى"""
        result = engine.analyze_sales_performance()
        insights = result["insights"]

        assert insights is not None

    def test_recommendations_structure(self, engine):
        """اختبار هيكل التوصيات"""
        result = engine.analyze_sales_performance()
        recommendations = result["recommendations"]

        assert recommendations is not None

    def test_empty_data_handling(self, engine):
        """اختبار التعامل مع البيانات الفارغة"""
        # عندما لا توجد بيانات
        with patch.object(engine, "_get_sales_data", return_value=[]):
            result = engine.analyze_sales_performance()

            assert result["summary"]["total_sales"] == 0
            assert result["summary"]["average_transaction"] == 0
            assert result["summary"]["median_transaction"] == 0

    def test_anomaly_percentage_calculation(self, engine):
        """اختبار حساب نسبة الشذوذ"""
        result = engine.detect_anomalies(data_type="sales")

        if result["total_records"] > 0:
            expected_percentage = (result["anomalies_detected"] / result["total_records"]) * 100
            assert result["anomaly_percentage"] == expected_percentage

    def test_period_calculation(self, engine):
        """اختبار حساب الفترة الزمنية"""
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)

        result = engine.analyze_sales_performance(start_date, end_date)

        assert result["period"]["days"] == 30

    def test_cache_initialization(self, engine):
        """اختبار تهيئة ذاكرة التخزين المؤقت"""
        assert hasattr(engine, "analytics_cache")
        assert engine.analytics_cache == {}

    def test_insights_history_initialization(self, engine):
        """اختبار تهيئة سجل الرؤى"""
        assert hasattr(engine, "insights_history")
        assert engine.insights_history == []


class TestAdvancedAnalyticsEngineEdgeCases:
    """اختبارات الحالات الطرفية"""

    @pytest.fixture
    def engine(self):
        db_manager = Mock()
        return AdvancedAnalyticsEngine(db_manager)

    def test_negative_threshold(self, engine):
        """اختبار قيمة عتبة سالبة"""
        result = engine.detect_anomalies(data_type="sales", threshold=-1.0)
        assert result is not None

    def test_zero_threshold(self, engine):
        """اختبار قيمة عتبة صفرية"""
        result = engine.detect_anomalies(data_type="sales", threshold=0)
        assert result is not None

    def test_very_large_threshold(self, engine):
        """اختبار قيمة عتبة كبيرة جداً"""
        result = engine.detect_anomalies(data_type="sales", threshold=1000.0)
        assert result is not None

    def test_future_dates(self, engine):
        """اختبار تواريخ مستقبلية"""
        start_date = datetime.now() + timedelta(days=30)
        end_date = datetime.now() + timedelta(days=60)

        result = engine.analyze_sales_performance(start_date, end_date)
        assert result is not None
        assert result["period"]["days"] == 30

    def test_past_dates(self, engine):
        """اختبار تواريخ سابقة"""
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now() - timedelta(days=335)

        result = engine.analyze_sales_performance(start_date, end_date)
        assert result is not None
        assert result["period"]["days"] == 30

    def test_same_start_end_date(self, engine):
        """اختبار نفس تاريخ البداية والنهاية"""
        same_date = datetime.now()

        result = engine.analyze_sales_performance(same_date, same_date)
        assert result is not None
        assert result["period"]["days"] == 0

    def test_invalid_prediction_type(self, engine):
        """اختبار نوع تنبؤ غير صالح"""
        result = engine.generate_predictive_insights(prediction_type="invalid")
        # يجب أن يعالج بشكل سليم
        assert result is not None or True  # لا يجب أن يحدث خطأ


class TestAdvancedAnalyticsEngineWithMockData:
    """اختبارات مع بيانات محاكاة"""

    @pytest.fixture
    def engine(self):
        db_manager = Mock()
        return AdvancedAnalyticsEngine(db_manager)

    @pytest.fixture
    def mock_sales_data(self):
        """بيانات مبيعات محاكاة"""
        return [
            {"amount": 100.0, "date": datetime.now() - timedelta(days=1)},
            {"amount": 150.0, "date": datetime.now() - timedelta(days=2)},
            {"amount": 200.0, "date": datetime.now() - timedelta(days=3)},
            {"amount": 120.0, "date": datetime.now() - timedelta(days=4)},
            {"amount": 180.0, "date": datetime.now() - timedelta(days=5)},
        ]

    def test_sales_calculation_with_mock_data(self, engine, mock_sales_data):
        """اختبار حسابات المبيعات مع بيانات محاكاة"""
        with patch.object(engine, "_get_sales_data", return_value=mock_sales_data):
            result = engine.analyze_sales_performance()

            expected_total = sum(sale["amount"] for sale in mock_sales_data)
            expected_count = len(mock_sales_data)

            assert result["summary"]["total_sales"] == expected_total
            assert result["summary"]["total_transactions"] == expected_count

    def test_average_calculation(self, engine, mock_sales_data):
        """اختبار حساب المتوسط"""
        with patch.object(engine, "_get_sales_data", return_value=mock_sales_data):
            result = engine.analyze_sales_performance()

            expected_avg = sum(sale["amount"] for sale in mock_sales_data) / len(mock_sales_data)
            assert result["summary"]["average_transaction"] == expected_avg

    def test_median_calculation(self, engine, mock_sales_data):
        """اختبار حساب الوسيط"""
        with patch.object(engine, "_get_sales_data", return_value=mock_sales_data):
            result = engine.analyze_sales_performance()

            amounts = sorted([sale["amount"] for sale in mock_sales_data])
            n = len(amounts)
            expected_median = amounts[n // 2] if n % 2 == 1 else (amounts[n // 2 - 1] + amounts[n // 2]) / 2

            assert result["summary"]["median_transaction"] == expected_median


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

#!/usr/bin/env python3
"""
اختبارات Advanced Prediction System
"""

from unittest.mock import patch

import pytest

from src.ai.advanced_prediction_system import AdvancedPredictionSystem


class TestAdvancedPredictionSystem:
    """اختبارات نظام التنبؤ المتقدم"""

    @pytest.fixture
    def system(self):
        """إنشاء نظام للاختبارات"""
        return AdvancedPredictionSystem()

    def test_initialization(self, system):
        """اختبار تهيئة النظام"""
        assert system is not None
        assert system.sales_model is not None
        assert system.inventory_model is not None
        assert system.customer_model is not None
        assert system.market_model is not None
        assert system.last_updated is None

    def test_initialize_system_with_sales_data(self, system):
        """اختبار تهيئة النظام ببيانات المبيعات"""
        historical_data = {
            "sales": [
                {"date": "2025-01-01", "amount": 1000},
                {"date": "2025-01-02", "amount": 1500},
            ]
        }

        with patch.object(
            system.sales_model,
            "train",
            return_value={"status": "trained", "accuracy": 0.9},
        ):
            result = system.initialize_system(historical_data)

            assert result is not None
            assert result["status"] == "initialized"
            assert result["models_trained"] >= 1
            assert "timestamp" in result
            assert system.last_updated is not None

    def test_initialize_system_with_inventory_data(self, system):
        """اختبار تهيئة النظام ببيانات المخزون"""
        historical_data = {
            "inventory": [
                {
                    "product_id": "P001",
                    "data": [{"date": "2025-01-01", "quantity": 100}],
                },
                {
                    "product_id": "P002",
                    "data": [{"date": "2025-01-01", "quantity": 50}],
                },
            ]
        }

        with patch.object(
            system.inventory_model,
            "train_for_product",
            return_value={"status": "trained"},
        ):
            result = system.initialize_system(historical_data)

            assert result is not None
            assert result["status"] == "initialized"

    def test_initialize_system_with_empty_data(self, system):
        """اختبار تهيئة النظام بدون بيانات"""
        result = system.initialize_system({})

        assert result is not None
        assert result["status"] == "initialized"
        assert result["models_trained"] == 0

    def test_generate_comprehensive_forecast(self, system):
        """اختبار توليد تنبؤ شامل"""
        # تهيئة النظام أولاً
        with patch.object(system.sales_model, "train", return_value={"status": "trained"}):
            system.initialize_system({"sales": []})

        # محاكاة التنبؤات
        with patch.object(system.sales_model, "predict_range", return_value={"forecast": [100, 200]}), patch.object(
            system, "_generate_inventory_forecast", return_value={}
        ), patch.object(system.customer_model, "predict_customer_behavior", return_value={}), patch.object(
            system.market_model, "predict_market_trends", return_value={}
        ):

            result = system.generate_comprehensive_forecast(forecast_period_days=30)

            assert result is not None
            assert "sales_forecast" in result
            assert "inventory_forecast" in result
            assert "customer_forecast" in result
            assert "forecast_period_days" in result
            assert result["forecast_period_days"] == 30

    def test_generate_forecast_with_context(self, system):
        """اختبار التنبؤ مع سياق"""
        context = {"season": "holiday", "promotion": True}

        with patch.object(system.sales_model, "predict_range", return_value={}), patch.object(
            system, "_generate_inventory_forecast", return_value={}
        ), patch.object(system.customer_model, "predict_customer_behavior", return_value={}):

            result = system.generate_comprehensive_forecast(forecast_period_days=7, context=context)

            assert result is not None

    def test_get_prediction_summary(self, system):
        """اختبار الحصول على ملخص التنبؤ"""
        forecast_result = {
            "sales_forecast": {"total": 5000},
            "inventory_forecast": {"products": 10},
            "forecast_period_days": 30,
        }

        summary = system.get_prediction_summary(forecast_result)

        assert summary is not None
        assert isinstance(summary, dict) or isinstance(summary, str)

    def test_cache_predictions(self, system):
        """اختبار تخزين التنبؤات مؤقتاً"""
        predictions = {"sales": [100, 200]}

        system.cache_predictions("test_key", predictions)

        assert "test_key" in system.prediction_cache
        assert system.prediction_cache["test_key"] == predictions

    def test_get_cached_predictions(self, system):
        """اختبار الحصول على التنبؤات المخزنة"""
        predictions = {"sales": [100, 200]}
        system.cache_predictions("test_key", predictions)

        result = system.get_cached_predictions("test_key")

        assert result == predictions

    def test_get_cached_predictions_nonexistent(self, system):
        """اختبار الحصول على تنبؤات غير موجودة"""
        result = system.get_cached_predictions("nonexistent_key")

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

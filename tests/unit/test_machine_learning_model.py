#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Machine Learning Model
اختبارات نموذج التعلم الآلي
"""

from unittest.mock import mock_open, patch

import pytest

from src.ai.machine_learning_model import (
    InventoryOptimizationModel,
    SalesPredictionModel,
)


class TestSalesPredictionModelInitialization:
    """اختبارات تهيئة نموذج التنبؤ بالمبيعات"""

    def test_initialization(self):
        """اختبار التهيئة الأساسية"""
        model = SalesPredictionModel(model_type="linear")

        assert model.model_type == "linear"
        assert model.is_trained is False
        assert model.weights is None
        assert model.bias is None
        assert model.training_data is None


class TestTrainModel:
    """اختبارات تدريب النموذج"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج جديد"""
        return SalesPredictionModel(model_type="linear")

    def test_train_with_valid_data(self, model):
        """اختبار التدريب مع بيانات صالحة"""
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0, "quantity": 10},
            {"date": "2024-01-02", "amount": 150.0, "quantity": 15},
            {"date": "2024-01-03", "amount": 200.0, "quantity": 20},
        ]

        result = model.train_model(sales_data)

        assert result["success"] is True
        assert "metrics" in result
        assert model.is_trained is True

    def test_train_with_empty_data(self, model):
        """اختبار التدريب مع بيانات فارغة"""
        result = model.train_model([])

        assert result["success"] is False
        assert "error" in result

    def test_train_with_insufficient_data(self, model):
        """اختبار التدريب مع بيانات غير كافية"""
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0},
        ]

        result = model.train_model(sales_data)

        assert result["success"] is False or "error" in result


class TestPredictSales:
    """اختبارات التنبؤ بالمبيعات"""

    @pytest.fixture
    def trained_model(self):
        """إنشاء نموذج مدرب"""
        model = SalesPredictionModel(model_type="linear")
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0, "quantity": 10},
            {"date": "2024-01-02", "amount": 150.0, "quantity": 15},
            {"date": "2024-01-03", "amount": 200.0, "quantity": 20},
        ]
        model.train_model(sales_data)
        return model

    def test_predict_without_training(self):
        """اختبار التنبؤ بدون تدريب"""
        model = SalesPredictionModel(model_type="linear")

        result = model.predict_sales(days=7)

        assert "error" in result

    def test_predict_with_trained_model(self, trained_model):
        """اختبار التنبؤ مع نموذج مدرب"""
        result = trained_model.predict_sales(days=7)

        assert "predictions" in result
        assert len(result["predictions"]) == 7
        assert "confidence" in result


class TestEvaluateModel:
    """اختبارات تقييم النموذج"""

    def test_evaluate_without_training(self):
        """اختبار التقييم بدون تدريب"""
        model = SalesPredictionModel(model_type="linear")

        result = model.evaluate_model([])

        assert "error" in result

    def test_evaluate_with_trained_model(self):
        """اختبار التقييم مع نموذج مدرب"""
        model = SalesPredictionModel(model_type="linear")
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0, "quantity": 10},
            {"date": "2024-01-02", "amount": 150.0, "quantity": 15},
            {"date": "2024-01-03", "amount": 200.0, "quantity": 20},
        ]
        model.train_model(sales_data)

        result = model.evaluate_model(sales_data)

        assert "mse" in result
        assert "mae" in result
        assert "r2" in result


class TestGetModelInfo:
    """اختبارات الحصول على معلومات النموذج"""

    def test_get_info_untrained(self):
        """اختبار الحصول على معلومات نموذج غير مدرب"""
        model = SalesPredictionModel(model_type="linear")

        info = model.get_model_info()

        assert info["model_type"] == "linear"
        assert info["is_trained"] is False

    def test_get_info_trained(self):
        """اختبار الحصول على معلومات نموذج مدرب"""
        model = SalesPredictionModel(model_type="linear")
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0, "quantity": 10},
            {"date": "2024-01-02", "amount": 150.0, "quantity": 15},
            {"date": "2024-01-03", "amount": 200.0, "quantity": 20},
        ]
        model.train_model(sales_data)

        info = model.get_model_info()

        assert info["model_type"] == "linear"
        assert info["is_trained"] is True


class TestSaveLoadModel:
    """اختبارات حفظ وتحميل النموذج"""

    @pytest.fixture
    def trained_model(self):
        """إنشاء نموذج مدرب"""
        model = SalesPredictionModel(model_type="linear")
        sales_data = [
            {"date": "2024-01-01", "amount": 100.0, "quantity": 10},
            {"date": "2024-01-02", "amount": 150.0, "quantity": 15},
            {"date": "2024-01-03", "amount": 200.0, "quantity": 20},
        ]
        model.train_model(sales_data)
        return model

    def test_save_model(self, trained_model):
        """اختبار حفظ النموذج"""
        with patch("builtins.open", mock_open()) as mock_file:
            result = trained_model.save_model("model.json")

            assert result["success"] is True
            mock_file.assert_called_once()

    def test_load_model(self):
        """اختبار تحميل النموذج"""
        model = SalesPredictionModel(model_type="linear")

        with patch(
            "builtins.open",
            mock_open(read_data='{"weights": [1.0], "bias": 0.0, "is_trained": true}'),
        ):
            with patch(
                "json.load",
                return_value={
                    "weights": [1.0],
                    "bias": 0.0,
                    "is_trained": True,
                    "model_type": "linear",
                },
            ):
                result = model.load_model("model.json")

                assert result["success"] is True


class TestInventoryOptimizationModelInitialization:
    """اختبارات تهيئة نموذج تحسين المخزون"""

    def test_initialization(self):
        """اختبار التهيئة الأساسية"""
        model = InventoryOptimizationModel()

        assert model.product_models == {}


class TestTrainInventoryModel:
    """اختبارات تدريب نموذج المخزون"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج جديد"""
        return InventoryOptimizationModel()

    def test_train_with_valid_data(self, model):
        """اختبار التدريب مع بيانات صالحة"""
        inventory_data = [
            {"date": "2024-01-01", "sales_velocity": 10.0, "reorder_point": 20},
            {"date": "2024-01-02", "sales_velocity": 15.0, "reorder_point": 25},
            {"date": "2024-01-03", "sales_velocity": 12.0, "reorder_point": 22},
        ]

        result = model.train("product1", inventory_data)

        assert result["model_trained"] is True
        assert "parameters" in result
        assert "product1" in model.product_models

    def test_train_with_empty_data(self, model):
        """اختبار التدريب مع بيانات فارغة"""
        result = model.train("product1", [])

        assert result["model_trained"] is True


class TestPredictInventoryNeeds:
    """اختبارات التنبؤ باحتياجات المخزون"""

    @pytest.fixture
    def trained_model(self):
        """إنشاء نموذج مدرب"""
        model = InventoryOptimizationModel()
        inventory_data = [
            {"date": "2024-01-01", "sales_velocity": 10.0, "reorder_point": 20},
            {"date": "2024-01-02", "sales_velocity": 15.0, "reorder_point": 25},
            {"date": "2024-01-03", "sales_velocity": 12.0, "reorder_point": 22},
        ]
        model.train("product1", inventory_data)
        return model

    def test_predict_untrained_product(self):
        """اختبار التنبؤ لمنتج غير مدرب"""
        model = InventoryOptimizationModel()

        result = model.predict_inventory_needs("product1")

        assert "error" in result

    def test_predict_trained_product(self, trained_model):
        """اختبار التنبؤ لمنتج مدرب"""
        result = trained_model.predict_inventory_needs("product1", days_ahead=30)

        assert "product_id" in result
        assert "predicted_demand" in result
        assert "recommended_stock_level" in result
        assert "reorder_point" in result
        assert result["product_id"] == "product1"


class TestCalculateSalesVelocity:
    """اختبارات حساب سرعة المبيعات"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج جديد"""
        return InventoryOptimizationModel()

    def test_calculate_with_valid_data(self, model):
        """اختبار حساب سرعة المبيعات مع بيانات صالحة"""
        inventory_data = [
            {"sales_velocity": 10.0},
            {"sales_velocity": 15.0},
            {"sales_velocity": 20.0},
        ]

        result = model._calculate_sales_velocity(inventory_data)

        assert "average_daily" in result
        assert "volatility" in result
        assert "peak_sales" in result
        assert "min_sales" in result
        assert result["average_daily"] == 15.0

    def test_calculate_with_empty_data(self, model):
        """اختبار حساب سرعة المبيعات مع بيانات فارغة"""
        result = model._calculate_sales_velocity([])

        assert result["average_daily"] == 0.0
        assert result["volatility"] == 0.0


class TestAnalyzeReorderPatterns:
    """اختبارات تحليل أنماط إعادة الطلب"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج جديد"""
        return InventoryOptimizationModel()

    def test_analyze_with_valid_data(self, model):
        """اختبار التحليل مع بيانات صالحة"""
        inventory_data = [
            {"reorder_point": 20},
            {"reorder_point": 25},
            {"reorder_point": 30},
        ]

        result = model._analyze_reorder_patterns(inventory_data)

        assert "average_reorder_point" in result
        assert "lead_time_days" in result
        assert result["average_reorder_point"] == 25.0

    def test_analyze_with_empty_data(self, model):
        """اختبار التحليل مع بيانات فارغة"""
        result = model._analyze_reorder_patterns([])

        assert result["average_reorder_point"] == 20  # القيمة الافتراضية
        assert result["lead_time_days"] == 7


class TestAnalyzeSeasonalDemand:
    """اختبارات تحليل الطلب الموسمي"""

    @pytest.fixture
    def model(self):
        """إنشاء نموذج جديد"""
        return InventoryOptimizationModel()

    def test_analyze_with_seasonal_data(self, model):
        """اختبار التحليل مع بيانات موسمية"""
        inventory_data = [
            {"date": "2024-01-15", "sales_velocity": 10.0},
            {"date": "2024-02-15", "sales_velocity": 15.0},
            {"date": "2024-03-15", "sales_velocity": 20.0},
        ]

        result = model._analyze_seasonal_demand(inventory_data)

        assert isinstance(result, dict)
        # التحقق من وجود قيم موسمية
        assert len(result) > 0

    def test_analyze_with_empty_data(self, model):
        """اختبار التحليل مع بيانات فارغة"""
        result = model._analyze_seasonal_demand([])

        assert isinstance(result, dict)
        assert result == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

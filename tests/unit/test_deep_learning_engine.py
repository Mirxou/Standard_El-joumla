#!/usr/bin/env python3
"""
اختبارات Deep Learning Engine
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.ai.deep_learning_engine import (
    DeepLearningEngine, ModelTrainingResult, PredictionResult,
    ModelEvaluation, FeatureImportance, ModelConfig
)


class TestDeepLearningEngine:
    """اختبارات محرك التعلم العميق"""
    
    @pytest.fixture
    def engine(self):
        """إنشاء محرك للاختبارات"""
        return DeepLearningEngine()
    
    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert hasattr(engine, 'models')
        assert hasattr(engine, 'model_history')
        assert hasattr(engine, 'feature_cache')
    
    def test_train_model_returns_result(self, engine):
        """اختبار تدريب النموذج وإرجاع النتيجة"""
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])
        
        result = engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        assert result is not None
        assert isinstance(result, ModelTrainingResult)
        assert result.model_name == "test_model"
        assert hasattr(result, 'accuracy')
        assert hasattr(result, 'loss')
        assert hasattr(result, 'training_time')
        assert hasattr(result, 'epochs_completed')
    
    def test_train_model_invalid_type(self, engine):
        """اختبار تدريب نموذج بنوع غير صالح"""
        X_train = np.array([[1, 2]])
        y_train = np.array([0])
        
        result = engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="invalid_type"
        )
        
        assert result is None or isinstance(result, ModelTrainingResult)
    
    def test_predict_returns_result(self, engine):
        """اختبار التنبؤ وإرجاع النتيجة"""
        # تدريب نموذج أولاً
        X_train = np.array([[1, 2], [3, 4], [5, 6]])
        y_train = np.array([0, 1, 0])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        # التنبؤ
        X_test = np.array([[1, 2]])
        result = engine.predict(model_name="test_model", X=X_test)
        
        assert result is not None
        assert isinstance(result, PredictionResult)
        assert hasattr(result, 'predictions')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'model_used')
    
    def test_predict_nonexistent_model(self, engine):
        """اختبار التنبؤ بنموذج غير موجود"""
        X_test = np.array([[1, 2]])
        
        result = engine.predict(model_name="nonexistent_model", X=X_test)
        
        assert result is None
    
    def test_evaluate_model_returns_result(self, engine):
        """اختبار تقييم النموذج"""
        X_train = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
        y_train = np.array([0, 1, 0, 1])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train[:3],
            y_train=y_train[:3],
            model_type="classification"
        )
        
        X_test = np.array([[1, 2]])
        y_test = np.array([0])
        
        result = engine.evaluate_model(
            model_name="test_model",
            X_test=X_test,
            y_test=y_test
        )
        
        assert result is not None
        assert isinstance(result, ModelEvaluation)
        assert hasattr(result, 'accuracy')
        assert hasattr(result, 'precision')
        assert hasattr(result, 'recall')
        assert hasattr(result, 'f1_score')
    
    def test_analyze_feature_importance_returns_result(self, engine):
        """اختبار تحليل أهمية الميزات"""
        X_train = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        y_train = np.array([0, 1, 0])
        feature_names = ["feature_a", "feature_b", "feature_c"]
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        result = engine.analyze_feature_importance(
            model_name="test_model",
            feature_names=feature_names
        )
        
        assert result is not None
        assert isinstance(result, FeatureImportance)
        assert hasattr(result, 'feature_names')
        assert hasattr(result, 'importance_scores')
        assert hasattr(result, 'top_features')
    
    def test_save_and_load_model(self, engine, tmp_path):
        """اختبار حفظ وتحميل النموذج"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        model_path = tmp_path / "test_model.pkl"
        
        # حفظ النموذج
        save_result = engine.save_model("test_model", str(model_path))
        assert save_result is True
        
        # تحميل النموذج
        load_result = engine.load_model("loaded_model", str(model_path))
        assert load_result is True
        assert "loaded_model" in engine.models
    
    def test_get_model_info(self, engine):
        """اختبار الحصول على معلومات النموذج"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        info = engine.get_model_info("test_model")
        
        assert info is not None
        assert "model_name" in info
        assert "model_type" in info
        assert "created_at" in info
    
    def test_get_model_info_nonexistent(self, engine):
        """اختبار الحصول على معلومات نموذج غير موجود"""
        info = engine.get_model_info("nonexistent_model")
        
        assert info is None
    
    def test_list_models(self, engine):
        """اختبار قائمة النماذج"""
        # بدون نماذج
        models = engine.list_models()
        assert isinstance(models, list)
        
        # مع نموذج
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        models = engine.list_models()
        assert "test_model" in models
    
    def test_delete_model(self, engine):
        """اختبار حذف النموذج"""
        X_train = np.array([[1, 2], [3, 4]])
        y_train = np.array([0, 1])
        
        engine.train_model(
            model_name="test_model",
            X_train=X_train,
            y_train=y_train,
            model_type="classification"
        )
        
        assert "test_model" in engine.models
        
        result = engine.delete_model("test_model")
        
        assert result is True
        assert "test_model" not in engine.models
    
    def test_delete_nonexistent_model(self, engine):
        """اختبار حذف نموذج غير موجود"""
        result = engine.delete_model("nonexistent_model")
        
        assert result is False


class TestModelTrainingResult:
    """اختبارات نتيجة تدريب النموذج"""
    
    def test_model_training_result_creation(self):
        """اختبار إنشاء نتيجة تدريب النموذج"""
        result = ModelTrainingResult(
            model_name="test_model",
            accuracy=0.95,
            loss=0.05,
            training_time=10.5,
            epochs_completed=100,
            best_epoch=95,
            validation_score=0.93,
            model_path="/path/to/model.pkl",
            trained_at=datetime.now()
        )
        
        assert result.model_name == "test_model"
        assert result.accuracy == 0.95
        assert result.loss == 0.05
        assert result.training_time == 10.5
        assert result.epochs_completed == 100
        assert result.best_epoch == 95
        assert result.validation_score == 0.93


class TestPredictionResult:
    """اختبارات نتيجة التنبؤ"""
    
    def test_prediction_result_creation(self):
        """اختبار إنشاء نتيجة التنبؤ"""
        result = PredictionResult(
            predictions=np.array([0, 1, 0]),
            probabilities=np.array([[0.8, 0.2], [0.1, 0.9], [0.7, 0.3]]),
            confidence=0.85,
            model_used="test_model",
            input_shape=(3, 2),
            prediction_time=0.05,
            predicted_at=datetime.now()
        )
        
        assert result.model_used == "test_model"
        assert result.confidence == 0.85
        assert result.prediction_time == 0.05


class TestModelEvaluation:
    """اختبارات تقييم النموذج"""
    
    def test_model_evaluation_creation(self):
        """اختبار إنشاء تقييم النموذج"""
        result = ModelEvaluation(
            model_name="test_model",
            accuracy=0.92,
            precision=0.90,
            recall=0.88,
            f1_score=0.89,
            auc_roc=0.95,
            confusion_matrix=np.array([[45, 5], [3, 47]]),
            classification_report="Test report",
            evaluated_at=datetime.now()
        )
        
        assert result.model_name == "test_model"
        assert result.accuracy == 0.92
        assert result.precision == 0.90
        assert result.recall == 0.88
        assert result.f1_score == 0.89


class TestFeatureImportance:
    """اختبارات أهمية الميزات"""
    
    def test_feature_importance_creation(self):
        """اختبار إنشاء أهمية الميزات"""
        result = FeatureImportance(
            feature_names=["feature_a", "feature_b", "feature_c"],
            importance_scores=[0.5, 0.3, 0.2],
            top_features=[("feature_a", 0.5), ("feature_b", 0.3)],
            analysis_method="feature_importance",
            analyzed_at=datetime.now()
        )
        
        assert result.analysis_method == "feature_importance"
        assert len(result.feature_names) == 3
        assert len(result.importance_scores) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




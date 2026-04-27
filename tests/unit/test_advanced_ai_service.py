#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for AdvancedAIService
اختبارات وحدة لخدمة الذكاء الاصطناعي المتقدمة
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
from src.services.advanced_ai_service import AdvancedAIService, AIModel, TrainingData, AIResult

class TestAdvancedAIService:
    @pytest.fixture
    def db_manager(self):
        mock_db = MagicMock()
        return mock_db

    @pytest.fixture
    def service(self, db_manager):
        with patch('src.services.advanced_ai_service.setup_logger', return_value=MagicMock()):
            with patch('src.services.advanced_ai_service.CognitiveAIService', return_value=MagicMock()):
                with patch('src.services.advanced_ai_service.AdvancedAnalyticsService', return_value=MagicMock()):
                    return AdvancedAIService(db_manager)

    def test_initialization(self, service):
        """Test if the service initializes correctly"""
        assert service.db is not None
        assert service.cognitive_ai is not None
        assert service.analytics is not None
        assert service.models_dir.exists()

    def test_create_ai_model(self, service):
        """Test creating a new AI model"""
        model_config = {
            'model_name': 'Test Classifier',
            'model_type': 'classification',
            'algorithm': 'rf',
            'purpose': 'Testing'
        }
        
        with patch.object(service, '_save_ai_model') as mock_save:
            model = service.create_ai_model(model_config)
            
            assert model is not None
            assert model.model_name == 'Test Classifier'
            assert model.model_type == 'classification'
            assert model.training_status == 'created'
            mock_save.assert_called_once()

    def test_train_ai_model_success(self, service):
        """Test successful training of an AI model"""
        model_id = "test_model_123"
        model = AIModel(
            model_id=model_id,
            model_name="Test Model",
            model_type="classification",
            purpose="Testing",
            algorithm="rf",
            accuracy_score=0.0,
            training_status="created",
            last_trained=None,
            model_path=None,
            parameters={},
            performance_metrics={},
            feature_importance=None,
            confusion_matrix=None,
            cross_validation_scores=None,
            hyperparameters=None,
            feature_names=None,
            created_at=datetime.now()
        )
        
        training_data = [
            TrainingData(
                data_id=f"d{i}", model_id=model_id, data_type="sales",
                data_content=[i, i+1, i+2], labels=i % 2, quality_score=0.9,
                collected_at=datetime.now(), used_in_training=False, metadata={}
            ) for i in range(5)
        ]
        
        # Mocks for internals
        service._get_ai_model = MagicMock(return_value=model)
        service._save_ai_model = MagicMock()
        service._prepare_training_data = MagicMock(return_value=(np.array([[1, 2, 3]]), np.array([0])))
        service._train_model_by_algorithm = MagicMock(return_value=(MagicMock(), {'accuracy': 0.95}))
        service._save_trained_model = MagicMock(return_value="/mock/path/model.pkl")
        service._mark_training_data_used = MagicMock()
        
        result = service.train_ai_model(model_id, training_data)
        
        assert result is True
        assert model.training_status == 'trained'
        assert model.accuracy_score == 0.95
        assert model.model_path == "/mock/path/model.pkl"

    def test_predict_with_ai_success(self, service):
        """Test successful prediction using an AI model"""
        model_id = "test_model_123"
        model = AIModel(
            model_id=model_id,
            model_name="Test Model",
            model_type="classification",
            purpose="Testing",
            algorithm="rf",
            accuracy_score=0.95,
            training_status="trained",
            last_trained=datetime.now(),
            model_path="/mock/path/model.pkl",
            parameters={},
            performance_metrics={},
            feature_importance=None,
            confusion_matrix=None,
            cross_validation_scores=None,
            hyperparameters=None,
            feature_names=None,
            created_at=datetime.now()
        )
        
        # Mocks
        service._get_ai_model = MagicMock(return_value=model)
        service._load_trained_model = MagicMock(return_value=MagicMock())
        service._preprocess_input_data = MagicMock(return_value=np.array([[1, 2, 3]]))
        service._make_prediction = MagicMock(return_value=(1, 0.98))
        service._interpret_prediction = MagicMock(return_value={'result': 'positive'})
        service._save_ai_result = MagicMock()
        
        result = service.predict_with_ai(model_id, [1, 2, 3])
        
        assert result is not None
        assert result.output_data == 1
        assert result.confidence_score == 0.98
        assert result.interpretation == {'result': 'positive'}

    def test_collect_training_data(self, service):
        """Test collecting training data from database"""
        service._collect_sales_training_data = MagicMock(return_value=[MagicMock(spec=TrainingData)])
        service._save_training_data = MagicMock()
        
        data = service.collect_training_data('sales', 'db')
        
        assert len(data) == 1
        service._save_training_data.assert_called()

    def test_monitor_ai_performance(self, service):
        """Test monitoring performance of all models"""
        model1 = MagicMock(spec=AIModel)
        model1.training_status = 'trained'
        model1.accuracy_score = 0.9
        model1.model_id = "m1"
        model1.model_name = "Model 1"
        model1.last_trained = datetime.now()
        
        service._get_all_ai_models = MagicMock(return_value=[model1])
        service._categorize_performance = MagicMock(return_value='excellent')
        service._generate_performance_recommendations = MagicMock(return_value=[])
        
        report = service.monitor_ai_performance()
        
        assert report['total_models'] == 1
        assert report['average_accuracy'] == 0.9
        assert len(report['model_performance']) == 1

if __name__ == "__main__":
    pytest.main([__file__])




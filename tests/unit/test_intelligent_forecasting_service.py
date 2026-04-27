#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for IntelligentForecastingService
اختبارات وحدة لخدمة التنبؤات الذكية
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, Mock
from src.services.intelligent_forecasting_service import (
    IntelligentForecastingService, ForecastModel, ForecastResult, DemandPattern
)

class TestIntelligentForecastingService:
    @pytest.fixture
    def db_manager(self):
        mock_db = MagicMock()
        return mock_db

    @pytest.fixture
    def service(self, db_manager):
        with patch('src.services.intelligent_forecasting_service.setup_logger', return_value=MagicMock()):
            with patch('src.services.intelligent_forecasting_service.CognitiveAIService', return_value=MagicMock()):
                with patch('src.services.intelligent_forecasting_service.AdvancedAnalyticsService', return_value=MagicMock()):
                    # Mock _load_forecast_models to avoid file access
                    with patch.object(IntelligentForecastingService, '_load_forecast_models', return_value=[]):
                        return IntelligentForecastingService(db_manager)

    def test_initialization(self, service):
        """Test if the service initializes correctly"""
        assert service.db is not None
        assert service.cognitive_ai is not None
        assert service.analytics is not None
        assert isinstance(service.forecast_models, list)

    def test_generate_sales_forecast_success(self, service):
        """Test successful generation of sales forecast"""
        # Mock historical data
        mock_history = [
            {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 'value': 100 + i}
            for i in range(30)
        ]
        
        # Mocks
        service._get_sales_history = MagicMock(return_value=mock_history)
        
        # Mock _select_or_train_model
        mock_model = MagicMock(spec=ForecastModel)
        mock_model.model_id = "test_model"
        service._select_or_train_model = MagicMock(return_value=mock_model)
        
        # Mock _prepare_forecast_features
        service._prepare_forecast_features = MagicMock(return_value=pd.DataFrame())
        
        # Mock _generate_predictions
        service._generate_predictions = MagicMock(return_value=[110.0] * 7)
        
        # Mock internals
        service._calculate_confidence_intervals = MagicMock(return_value=[(100.0, 120.0)] * 7)
        service._calculate_forecast_accuracy = MagicMock(return_value={'accuracy_score': 0.9})
        service._identify_influencing_factors = MagicMock(return_value=[])
        service._save_forecast_result = MagicMock()
        
        result = service.generate_sales_forecast(forecast_days=7)
        
        assert result is not None
        assert isinstance(result, ForecastResult)
        assert result.forecast_horizon == 7
        assert len(result.predicted_values) == 7
        assert result.accuracy_metrics['accuracy_score'] == 0.9

    def test_predict_inventory_needs(self, service):
        """Test predicting inventory needs based on forecast"""
        # Mock inventory data
        service._get_inventory_data = MagicMock(return_value={'P1': 50})
        
        # Mock sales forecast
        mock_forecast = MagicMock(spec=ForecastResult)
        service.generate_sales_forecast = MagicMock(return_value=mock_forecast)
        
        # Mock consumption and reorder points
        service._calculate_daily_consumption = MagicMock(return_value=5.0)
        service._get_reorder_point = MagicMock(return_value=20)
        service._get_safety_stock = MagicMock(return_value=10)
        
        result = service.predict_inventory_needs(forecast_days=7)
        
        assert 'inventory_needs' in result
        assert 'P1' in result['inventory_needs']
        assert result['inventory_needs']['P1']['current_stock'] == 50
        assert result['inventory_needs']['P1']['daily_consumption'] == 5.0

    def test_detect_demand_patterns(self, service):
        """Test detection of demand patterns"""
        # Mock sales history
        mock_history = [
            {'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'), 'value': 100}
            for i in range(60)
        ]
        service._get_sales_history = MagicMock(return_value=mock_history)
        
        # Mock detection methods
        mock_pattern = DemandPattern(
            pattern_id="p1", product_id="P1", pattern_type="trend",
            seasonality_period=None, trend_direction="stable",
            confidence_level=0.9, detected_at=datetime.now(), pattern_data={}
        )
        service._detect_seasonal_patterns = MagicMock(return_value=[])
        service._detect_trend_patterns = MagicMock(return_value=[mock_pattern])
        service._detect_cyclical_patterns = MagicMock(return_value=[])
        service._save_demand_pattern = MagicMock()
        
        patterns = service.detect_demand_patterns(product_id="P1")
        
        assert len(patterns) == 1
        assert patterns[0].pattern_type == "trend"

    def test_forecast_financial_performance(self, service):
        """Test financial performance forecasting"""
        # Mock history
        service._get_financial_history = MagicMock(return_value={'income': [1000], 'expenses': [800]})
        
        # Mock individual forecasts
        service._forecast_revenue = MagicMock(return_value={'values': [1100], 'dates': [datetime.now()]})
        service._forecast_costs = MagicMock(return_value={'values': [850], 'dates': [datetime.now()]})
        service._forecast_profit = MagicMock(return_value={'values': [250], 'dates': [datetime.now()]})
        service._calculate_financial_metrics = MagicMock(return_value={'roi': 0.1})
        
        result = service.forecast_financial_performance(forecast_months=1)
        
        assert 'revenue_forecast' in result
        assert 'cost_forecast' in result
        assert 'profit_forecast' in result
        assert result['financial_metrics']['roi'] == 0.1

if __name__ == "__main__":
    pytest.main([__file__])




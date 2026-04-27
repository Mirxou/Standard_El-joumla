#!/usr/bin/env python3
"""
اختبارات Intelligent Recommendation System
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from src.ai.intelligent_recommendation_system import (
    IntelligentRecommendationSystem, RecommendationResult
)


class TestIntelligentRecommendationSystem:
    """اختبارات نظام التوصيات الذكية"""
    
    @pytest.fixture
    def system(self):
        """إنشاء نظام للاختبارات"""
        db_manager = Mock()
        return IntelligentRecommendationSystem(db_manager)
    
    def test_initialization(self, system):
        """اختبار تهيئة النظام"""
        assert system is not None
        assert system.db is not None
        assert hasattr(system, 'recommendation_cache')
    
    def test_get_product_recommendations_for_customer(self, system):
        """اختبار الحصول على توصيات المنتجات للعميل"""
        mock_products = [
            {"id": 1, "name": "Product A", "price": 100},
            {"id": 2, "name": "Product B", "price": 150},
        ]
        mock_history = [{"product_id": 1, "quantity": 2}]
        
        system.db.execute_query.return_value = mock_products
        
        with patch.object(system, '_get_customer_history', return_value=mock_history):
            result = system.get_product_recommendations(customer_id=1, limit=5)
            
            assert result is not None
            assert isinstance(result, list)
            assert len(result) <= 5
    
    def test_get_similar_products(self, system):
        """اختبار الحصول على منتجات مشابهة"""
        mock_products = [
            {"id": 1, "name": "Product A", "category": "electronics"},
            {"id": 2, "name": "Product B", "category": "electronics"},
        ]
        system.db.execute_query.return_value = mock_products
        
        result = system.get_similar_products(product_id=1, limit=3)
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) <= 3
    
    def test_get_frequently_bought_together(self, system):
        """اختبار الحصول على المشتريات المتكررة معاً"""
        result = system.get_frequently_bought_together(product_id=1, limit=5)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_get_trending_products(self, system):
        """اختبار الحصول على المنتجات الرائجة"""
        mock_products = [
            {"id": 1, "name": "Product A", "sales_count": 100},
            {"id": 2, "name": "Product B", "sales_count": 80},
        ]
        system.db.execute_query.return_value = mock_products
        
        result = system.get_trending_products(limit=10, days=30)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_calculate_recommendation_score(self, system):
        """اختبار حساب درجة التوصية"""
        score = system._calculate_recommendation_score(
            product_id=1,
            customer_id=1,
            purchase_history=[],
            product_features={"category": "electronics"}
        )
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    def test_invalid_product_id(self, system):
        """اختبار معرف منتج غير صالح"""
        result = system.get_similar_products(product_id=-1)
        
        assert result == [] or result is None


class TestRecommendationResult:
    """اختبارات نتيجة التوصية"""
    
    def test_recommendation_result_creation(self):
        """اختبار إنشاء نتيجة التوصية"""
        result = RecommendationResult(
            product_id=1,
            product_name="Test Product",
            recommendation_score=0.95,
            reason="Based on your purchase history",
            confidence=0.87
        )
        
        assert result.product_id == 1
        assert result.recommendation_score == 0.95
        assert result.confidence == 0.87


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




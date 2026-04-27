#!/usr/bin/env python3
"""
اختبارات Computer Vision Module
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.ai.computer_vision import ComputerVisionEngine, ImageAnalysisResult


class TestComputerVisionEngine:
    """اختبارات محرك الرؤية الحاسوبية"""
    
    @pytest.fixture
    def engine(self):
        """إنشاء محرك للاختبارات"""
        return ComputerVisionEngine()
    
    def test_initialization(self, engine):
        """اختبار تهيئة المحرك"""
        assert engine is not None
        assert hasattr(engine, 'models')
        assert hasattr(engine, 'image_cache')
    
    def test_analyze_image_returns_result(self, engine):
        """اختبار تحليل الصورة"""
        # إنشاء صورة محاكاة
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = engine.analyze_image(image, analysis_type="general")
        
        assert result is not None
        assert isinstance(result, ImageAnalysisResult)
        assert hasattr(result, 'objects_detected')
        assert hasattr(result, 'labels')
        assert hasattr(result, 'confidence_scores')
    
    def test_detect_objects(self, engine):
        """اختبار كشف الأشياء"""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = engine.detect_objects(image, confidence_threshold=0.5)
        
        assert result is not None
        assert isinstance(result, list)
    
    def test_extract_text(self, engine):
        """اختبار استخراج النص"""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = engine.extract_text(image, language="ar")
        
        assert result is not None
        assert isinstance(result, str) or isinstance(result, list)
    
    def test_compare_images(self, engine):
        """اختبار مقارنة الصور"""
        image1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        image2 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = engine.compare_images(image1, image2)
        
        assert result is not None
        assert hasattr(result, 'similarity_score') or isinstance(result, float)
    
    def test_invalid_analysis_type(self, engine):
        """اختبار نوع تحليل غير صالح"""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        result = engine.analyze_image(image, analysis_type="invalid")
        
        assert result is None or hasattr(result, 'error')


class TestImageAnalysisResult:
    """اختبارات نتيجة تحليل الصورة"""
    
    def test_image_analysis_result_creation(self):
        """اختبار إنشاء نتيجة تحليل الصورة"""
        result = ImageAnalysisResult(
            objects_detected=[{"label": "product", "confidence": 0.95}],
            labels=["retail", "inventory"],
            confidence_scores=[0.95, 0.87],
            processing_time=0.5,
            analyzed_at=datetime.now()
        )
        
        assert len(result.objects_detected) == 1
        assert len(result.labels) == 2
        assert result.processing_time == 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




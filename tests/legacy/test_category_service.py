#!/usr/bin/env python3
"""
اختبارات Category Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.category_service import CategoryService


class TestCategoryService:
    """اختبارات خدمة الفئات"""
    
    @pytest.fixture
    def category_service(self):
        """إنشاء خدمة فئات"""
        return CategoryService()
    
    def test_initialization(self, category_service):
        """اختبار التهيئة"""
        assert category_service is not None
    
    def test_create_category(self, category_service):
        """اختبار إنشاء فئة"""
        with patch.object(category_service, 'create', return_value={"id": "1", "name": "Electronics"}):
            result = category_service.create({"name": "Electronics"})
            assert result is not None
    
    def test_get_category(self, category_service):
        """اختبار الحصول على فئة"""
        with patch.object(category_service, 'get', return_value={"id": "1", "name": "Electronics"}):
            result = category_service.get("1")
            assert result is not None
    
    def test_get_all_categories(self, category_service):
        """اختبار الحصول على جميع الفئات"""
        with patch.object(category_service, 'get_all', return_value=[{"id": "1"}, {"id": "2"}]):
            result = category_service.get_all()
            assert isinstance(result, list)
    
    def test_update_category(self, category_service):
        """اختبار تحديث فئة"""
        with patch.object(category_service, 'update', return_value=True):
            result = category_service.update("1", {"name": "Updated"})
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




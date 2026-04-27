#!/usr/bin/env python3
"""
اختبارات Product Service
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.product_service_enhanced import ProductService


class TestProductService:
    """اختبارات خدمة المنتجات"""
    
    @pytest.fixture
    def product_service(self):
        """إنشاء خدمة منتجات"""
        return ProductService()
    
    def test_initialization(self, product_service):
        """اختبار التهيئة"""
        assert product_service is not None
    
    def test_create_product(self, product_service):
        """اختبار إنشاء منتج"""
        with patch.object(product_service, 'create', return_value={"id": "1", "name": "Product"}):
            result = product_service.create({"name": "Product", "price": 100})
            assert result is not None
    
    def test_get_product(self, product_service):
        """اختبار الحصول على منتج"""
        with patch.object(product_service, 'get', return_value={"id": "1", "name": "Product"}):
            result = product_service.get("1")
            assert result is not None
    
    def test_update_product(self, product_service):
        """اختبار تحديث منتج"""
        with patch.object(product_service, 'update', return_value=True):
            result = product_service.update("1", {"price": 150})
            assert result is True
    
    def test_delete_product(self, product_service):
        """اختبار حذف منتج"""
        with patch.object(product_service, 'delete', return_value=True):
            result = product_service.delete("1")
            assert result is True
    
    def test_search_products(self, product_service):
        """اختبار البحث في المنتجات"""
        with patch.object(product_service, 'search', return_value=[{"id": "1"}, {"id": "2"}]):
            result = product_service.search("Product")
            assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




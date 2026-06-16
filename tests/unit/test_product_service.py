#!/usr/bin/env python3
"""
اختبارات Product Service المحدثة
"""

from unittest.mock import Mock

import pytest

from src.models.product_enhanced import Product
from src.services.product_service_enhanced import ProductService

# إنشاء تطبيق Qt للاختبارات (إذا لزم الأمر، رغم أن هذه خدمة)
# app = QApplication.instance() or QApplication([])


class TestProductService:
    """اختبارات خدمة المنتجات"""

    @pytest.fixture
    def product_service(self):
        """إنشاء خدمة منتجات"""
        db_manager = Mock()
        # محاكاة PRAGMA table_info
        db_manager.fetch_all.return_value = [
            (0, "id", "INTEGER"),
            (1, "name", "TEXT"),
            (2, "barcode", "TEXT"),
            (3, "cost_price", "REAL"),
            (4, "selling_price", "REAL"),
            (5, "current_stock", "REAL"),
            (6, "is_active", "INTEGER"),
            (7, "sku", "TEXT"),
        ]
        return ProductService(db_manager)

    def test_initialization(self, product_service):
        """اختبار التهيئة"""
        assert product_service is not None

    def test_create_product(self, product_service):
        """اختبار إنشاء منتج"""
        product = Product(name="Test Product", cost_price=100, base_price=150)
        product_service.db_manager.execute_query.return_value = Mock(rowcount=1)
        product_service.db_manager.get_last_insert_id.return_value = 1

        result = product_service.create_product(product)
        assert result == 1

    def test_get_product_by_id(self, product_service):
        """اختبار الحصول على منتج"""
        mock_row = [
            1,
            "Product",
            None,
            "SKU1",
            "123",
            1,
            None,
            None,
            "Desc",
            None,
            "unit",
            100.0,
            150.0,
            None,
            10,
            0,
            5,
            5,
            100,
            None,
            None,
            None,
            1,
            0,
            0,
            None,
            None,
            None,
            0,
            0,
            0,
        ]
        product_service.db_manager.fetch_one.return_value = mock_row

        result = product_service.get_product_by_id(1)
        assert result is not None
        assert result.name == "Product"

    def test_update_product(self, product_service):
        """اختبار تحديث منتج"""
        product = Product(id=1, name="Updated Product")
        product_service.db_manager.execute_query.return_value = Mock(rowcount=1)

        result = product_service.update_product(product)
        assert result is True

    def test_delete_product(self, product_service):
        """اختبار حذف منتج"""
        product_service.db_manager.execute_query.return_value = Mock(rowcount=1)

        result = product_service.delete_product(1)
        assert result is True

    def test_search_products(self, product_service):
        """اختبار البحث في المنتجات"""
        product_service.db_manager.fetch_all.side_effect = [
            [(0, "id"), (1, "name")],  # PRAGMA
            [[1, "Product 1"], [2, "Product 2"]],  # Results
        ]

        result = product_service.search_products("Product")
        assert isinstance(result, list)
        assert len(result) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

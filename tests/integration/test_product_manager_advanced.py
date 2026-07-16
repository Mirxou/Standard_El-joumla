"""
Integration Tests for Product Manager Advanced Features
اختبارات تكامل للوظائف المتقدمة في ProductManager
"""

import random

import pytest

from src.models.product import Product, ProductManager


@pytest.mark.requires_db
class TestProductManagerAdvanced:
    """اختبارات متقدمة لـ ProductManager"""

    def test_get_product_by_barcode(self, db_manager, sample_product_data):
        """اختبار الحصول على منتج بالباركود"""
        manager = ProductManager(db_manager)

        # إنشاء منتج بباركود فريد
        product_data = sample_product_data.copy()
        unique_barcode = f"TEST{random.randint(100000, 999999)}"
        product_data["barcode"] = unique_barcode

        product = Product(**product_data)
        product_id = manager.create_product(product)

        # البحث بالباركود
        found_product = manager.get_product_by_barcode(unique_barcode)

        assert found_product is not None
        assert found_product.id == product_id
        assert found_product.barcode == unique_barcode

    def test_search_products_by_name(self, db_manager, sample_product_data):
        """اختبار البحث عن منتجات بالاسم"""
        manager = ProductManager(db_manager)

        # إنشاء منتجات متعددة
        for i in range(3):
            product_data = sample_product_data.copy()
            product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"
            product_data["name"] = f"منتج اختبار {i}"

            product = Product(**product_data)
            manager.create_product(product)

        # البحث
        results = manager.search_products("اختبار")
        assert len(results) >= 3

    def test_search_products_by_barcode(self, db_manager, sample_product_data):
        """اختبار البحث عن منتجات بالباركود"""
        manager = ProductManager(db_manager)

        # إنشاء منتج بباركود معين
        product_data = sample_product_data.copy()
        test_barcode = f"SEARCH{random.randint(100000, 999999)}"
        product_data["barcode"] = test_barcode

        product = Product(**product_data)
        manager.create_product(product)

        # البحث بالباركود
        results = manager.search_products(test_barcode)
        assert len(results) >= 1
        assert any(p.barcode == test_barcode for p in results)

    def test_update_product_stock(self, db_manager, sample_product_data):
        """اختبار تحديث مخزون المنتج"""
        manager = ProductManager(db_manager)

        # إنشاء منتج
        product_data = sample_product_data.copy()
        product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"
        product_data["current_stock"] = 50

        product = Product(**product_data)
        product_id = manager.create_product(product)

        # تحديث المخزون
        product = manager.get_product_by_id(product_id)
        product.current_stock = 100

        success = manager.update_product(product)
        assert success is True

        # التحقق من التحديث
        updated_product = manager.get_product_by_id(product_id)
        assert updated_product.current_stock == 100

    def test_get_all_products(self, db_manager, sample_product_data):
        """اختبار الحصول على جميع المنتجات"""
        manager = ProductManager(db_manager)

        # إنشاء عدة منتجات
        for i in range(5):
            product_data = sample_product_data.copy()
            product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"
            product_data["name"] = f"منتج {i}"

            product = Product(**product_data)
            manager.create_product(product)

        # الحصول على جميع المنتجات
        all_products = manager.get_all_products()
        assert len(all_products) >= 5

    def test_delete_product(self, db_manager, sample_product_data):
        """اختبار حذف منتج"""
        manager = ProductManager(db_manager)

        # إنشاء منتج
        product_data = sample_product_data.copy()
        product_data["barcode"] = f"TEST{random.randint(100000, 999999)}"

        product = Product(**product_data)
        product_id = manager.create_product(product)

        # حذف المنتج
        success = manager.delete_product(product_id)
        assert success is True

        # التحقق من الحذف
        deleted_product = manager.get_product_by_id(product_id)
        assert deleted_product is None or deleted_product.is_active is False

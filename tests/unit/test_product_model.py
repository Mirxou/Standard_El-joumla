"""
Unit Tests for Product Model
اختبارات وحدة لنموذج المنتج
"""

import pytest
import random
from decimal import Decimal
from datetime import datetime
from src.models.product import Product, ProductManager


class TestProduct:
    """اختبارات كائن Product"""
    
    def test_product_creation(self):
        """اختبار إنشاء منتج جديد"""
        product = Product(
            name="منتج اختبار",
            cost_price=100.0,
            selling_price=150.0,
            current_stock=50
        )
        
        assert product.name == "منتج اختبار"
        assert product.cost_price == Decimal('100.0')
        assert product.selling_price == Decimal('150.0')
        assert product.current_stock == 50
    
    def test_product_profit_margin(self):
        """اختبار حساب هامش الربح"""
        product = Product(
            cost_price=100.0,
            selling_price=150.0
        )
        
        margin = product.profit_margin
        assert margin == Decimal('50.00')  # ((150-100)/100) * 100
    
    def test_product_profit_amount(self):
        """اختبار حساب مبلغ الربح"""
        product = Product(
            cost_price=100.0,
            selling_price=150.0
        )
        
        profit = product.profit_amount
        assert profit == Decimal('50.00')
    
    def test_product_stock_value(self):
        """اختبار حساب قيمة المخزون"""
        product = Product(
            cost_price=100.0,
            current_stock=50
        )
        
        stock_value = product.stock_value
        assert stock_value == Decimal('5000.00')
    
    def test_product_is_low_stock(self):
        """اختبار التحقق من انخفاض المخزون"""
        product = Product(
            min_stock=10,
            current_stock=5
        )
        
        assert product.is_low_stock == True
        
        product.current_stock = 15
        assert product.is_low_stock == False
    
    def test_product_to_dict(self):
        """اختبار تحويل المنتج إلى قاموس"""
        product = Product(
            id=1,
            name="منتج اختبار",
            cost_price=100.0,
            selling_price=150.0,
            current_stock=50
        )
        
        product_dict = product.to_dict()
        assert product_dict['id'] == 1
        assert product_dict['name'] == "منتج اختبار"
        assert isinstance(product_dict['cost_price'], float)
        assert isinstance(product_dict['profit_margin'], float)


@pytest.mark.requires_db
class TestProductManager:
    """اختبارات ProductManager"""
    
    def test_create_product(self, db_manager, sample_product_data):
        """اختبار إنشاء منتج في قاعدة البيانات"""
        manager = ProductManager(db_manager)
        
        # 🔥 CRITICAL FIX: استخدام باركود عشوائي لتجنب UNIQUE constraint
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        
        product = Product(**product_data)
        product_id = manager.create_product(product)
        
        assert product_id is not None
        assert product_id > 0
    
    def test_get_product_by_id(self, db_manager, sample_product_data):
        """اختبار الحصول على منتج بالمعرف"""
        manager = ProductManager(db_manager)
        
        # 🔥 CRITICAL FIX: استخدام باركود عشوائي
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        
        # إنشاء منتج أولاً
        product = Product(**product_data)
        product_id = manager.create_product(product)
        
        assert product_id is not None, "فشل في إنشاء المنتج"
        assert product_id > 0, f"product_id يجب أن يكون > 0، لكنه {product_id}"
        
        # الحصول على المنتج
        retrieved_product = manager.get_product_by_id(product_id)
        
        assert retrieved_product is not None
        assert retrieved_product.id == product_id
        assert retrieved_product.name == product_data['name']
    
    def test_update_product(self, db_manager, sample_product_data):
        """اختبار تحديث منتج"""
        manager = ProductManager(db_manager)
        
        # 🔥 CRITICAL FIX: استخدام باركود عشوائي
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        
        # إنشاء منتج
        product = Product(**product_data)
        product_id = manager.create_product(product)
        assert product_id is not None, "فشل في إنشاء المنتج"
        assert product_id > 0, f"product_id يجب أن يكون > 0، لكنه {product_id}"
        
        # الحصول على المنتج من قاعدة البيانات
        product = manager.get_product_by_id(product_id)
        assert product is not None
        
        # تحديث المنتج (update_product يأخذ Product object)
        product.name = "منتج محدث"
        product.selling_price = Decimal('200.0')
        
        success = manager.update_product(product)
        assert success == True
        
        # التحقق من التحديث
        updated_product = manager.get_product_by_id(product_id)
        assert updated_product.name == "منتج محدث"
        assert updated_product.selling_price == Decimal('200.0')
    
    def test_search_products(self, db_manager, sample_product_data):
        """اختبار البحث عن منتجات"""
        manager = ProductManager(db_manager)
        
        # 🔥 CRITICAL FIX: استخدام باركود عشوائي
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        
        # إنشاء منتج
        product = Product(**product_data)
        product_id = manager.create_product(product)
        assert product_id is not None, "فشل في إنشاء المنتج"
        
        # البحث
        results = manager.search_products("اختبار")
        assert len(results) > 0
        assert any(p.name == product_data['name'] for p in results)


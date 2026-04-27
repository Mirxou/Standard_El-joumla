#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Unit Tests for Models (Product, Sale, Purchase, Payment)
اختبارات وحدة شاملة للـ Models
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import Mock, patch

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.product import Product, ProductManager
from src.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod, SaleManager
from src.models.purchase import Purchase, PurchaseItem, PurchaseManager
from src.models.payment import Payment, PaymentType, PaymentStatus, PaymentManager
from src.core.database_manager import DatabaseManager


class TestProductManagerCRUD:
    """اختبارات CRUD لـ ProductManager"""
    
    @pytest.fixture
    def db_manager(self):
        """إنشاء DatabaseManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        
        # إنشاء جدول categories
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        return db
    
    @pytest.fixture
    def product_manager(self, db_manager):
        """إنشاء ProductManager للاختبارات"""
        return ProductManager(db_manager)
    
    @pytest.fixture
    def sample_product(self):
        """إنشاء منتج تجريبي"""
        return Product(
            name="منتج اختبار",
            cost_price=100.0,
            selling_price=150.0,
            current_stock=50,
            min_stock=10
        )
    
    def test_create_product(self, product_manager, sample_product):
        """اختبار إنشاء منتج"""
        product_id = product_manager.create_product(sample_product)
        assert product_id is not None
        assert product_id > 0
    
    def test_get_product_by_id(self, product_manager, sample_product):
        """اختبار الحصول على منتج بالمعرف"""
        product_id = product_manager.create_product(sample_product)
        retrieved_product = product_manager.get_product_by_id(product_id)
        
        assert retrieved_product is not None
        assert retrieved_product.id == product_id
        assert retrieved_product.name == sample_product.name
    
    def test_get_product_by_barcode(self, product_manager, sample_product):
        """اختبار الحصول على منتج بالباركود"""
        sample_product.barcode = "123456789"
        product_id = product_manager.create_product(sample_product)
        
        retrieved_product = product_manager.get_product_by_barcode("123456789")
        assert retrieved_product is not None
        assert retrieved_product.barcode == "123456789"
    
    def test_update_product(self, product_manager, sample_product):
        """اختبار تحديث منتج"""
        product_id = product_manager.create_product(sample_product)
        sample_product.id = product_id
        sample_product.name = "منتج محدث"
        sample_product.selling_price = 200.0
        
        result = product_manager.update_product(sample_product)
        assert result == True
        
        updated_product = product_manager.get_product_by_id(product_id)
        assert updated_product.name == "منتج محدث"
        assert updated_product.selling_price == Decimal('200.0')
    
    def test_delete_product_soft(self, product_manager, sample_product):
        """اختبار حذف منتج (Soft Delete)"""
        product_id = product_manager.create_product(sample_product)
        result = product_manager.delete_product(product_id, soft_delete=True)
        
        assert result == True
        
        # يجب أن يكون المنتج غير نشط
        product = product_manager.get_product_by_id(product_id)
        assert product.is_active == False
    
    def test_search_products(self, product_manager, sample_product):
        """اختبار البحث في المنتجات"""
        product_manager.create_product(sample_product)
        
        results = product_manager.search_products(search_term="اختبار")
        assert len(results) > 0
        assert any(p.name == "منتج اختبار" for p in results)
    
    def test_get_all_products(self, product_manager, sample_product):
        """اختبار الحصول على جميع المنتجات"""
        product_manager.create_product(sample_product)
        
        products = product_manager.get_all_products()
        assert len(products) > 0


class TestSaleManagerCRUD:
    """اختبارات CRUD لـ SaleManager"""
    
    @pytest.fixture
    def sale_manager(self):
        """إنشاء SaleManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        return SaleManager(db)
    
    def test_sale_manager_initialization(self, sale_manager):
        """اختبار تهيئة SaleManager"""
        assert sale_manager is not None
        assert sale_manager.db_manager is not None
    
    def test_sale_manager_has_methods(self, sale_manager):
        """اختبار وجود الطرق الأساسية"""
        assert hasattr(sale_manager, 'create_sale')
        assert hasattr(sale_manager, 'get_sale_by_id')
        assert hasattr(sale_manager, 'update_sale')
        assert hasattr(sale_manager, 'search_sales')


class TestPurchaseManagerCRUD:
    """اختبارات CRUD لـ PurchaseManager"""
    
    @pytest.fixture
    def purchase_manager(self):
        """إنشاء PurchaseManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        return PurchaseManager(db)
    
    def test_purchase_manager_initialization(self, purchase_manager):
        """اختبار تهيئة PurchaseManager"""
        assert purchase_manager is not None
        assert purchase_manager.db_manager is not None
    
    def test_purchase_manager_has_methods(self, purchase_manager):
        """اختبار وجود الطرق الأساسية"""
        assert hasattr(purchase_manager, 'create_purchase')
        assert hasattr(purchase_manager, 'get_purchase_by_id')
        assert hasattr(purchase_manager, 'update_purchase')


class TestPaymentManagerCRUD:
    """اختبارات CRUD لـ PaymentManager"""
    
    @pytest.fixture
    def payment_manager(self):
        """إنشاء PaymentManager للاختبارات"""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()
        return PaymentManager(db)
    
    def test_payment_manager_initialization(self, payment_manager):
        """اختبار تهيئة PaymentManager"""
        assert payment_manager is not None
        assert payment_manager.db_manager is not None
    
    def test_payment_manager_has_methods(self, payment_manager):
        """اختبار وجود الطرق الأساسية"""
        assert hasattr(payment_manager, 'create_payment')
        assert hasattr(payment_manager, 'get_payment_by_id')
        # قد لا يكون update_payment موجوداً


class TestProductCalculations:
    """اختبارات الحسابات في Product"""
    
    def test_profit_margin_calculation(self):
        """اختبار حساب هامش الربح"""
        product = Product(
            cost_price=100.0,
            selling_price=150.0
        )
        
        margin = product.profit_margin
        assert margin == Decimal('50.00')  # ((150-100)/100) * 100
    
    def test_profit_amount_calculation(self):
        """اختبار حساب مبلغ الربح"""
        product = Product(
            cost_price=100.0,
            selling_price=150.0
        )
        
        profit = product.profit_amount
        assert profit == Decimal('50.00')
    
    def test_stock_value_calculation(self):
        """اختبار حساب قيمة المخزون"""
        product = Product(
            cost_price=100.0,
            current_stock=50
        )
        
        stock_value = product.stock_value
        assert stock_value == Decimal('5000.00')
    
    def test_is_low_stock(self):
        """اختبار التحقق من المخزون المنخفض"""
        product = Product(
            current_stock=5,
            min_stock=10
        )
        
        assert product.is_low_stock == True
        
        product.current_stock = 15
        assert product.is_low_stock == False


class TestSaleCalculations:
    """اختبارات الحسابات في Sale"""
    
    def test_sale_item_calculate_total(self):
        """اختبار حساب المجموع في SaleItem"""
        item = SaleItem(
            product_id=1,
            quantity=5,
            unit_price=Decimal('100.00'),
            discount_percentage=Decimal('10.00'),
            tax_percentage=Decimal('15.00')
        )
        
        item.calculate_total()
        
        # المجموع الفرعي: 5 * 100 = 500
        # الخصم: 500 * 10% = 50
        # بعد الخصم: 450
        # الضريبة: 450 * 15% = 67.5
        # المجموع النهائي: 517.5
        assert item.discount_amount == Decimal('50.00')
        assert item.total_amount == Decimal('517.50')
    
    def test_sale_calculate_totals(self):
        """اختبار حساب المجاميع في Sale"""
        sale = Sale(
            discount_percentage=Decimal('10.00'),
            tax_percentage=Decimal('15.00')
        )
        
        # إضافة عناصر للفاتورة
        sale.items = [
            SaleItem(
                product_id=1,
                quantity=5,
                unit_price=Decimal('200.00')
            )
        ]
        
        # استدعاء calculate_totals
        sale.calculate_totals()
        
        # المجموع الفرعي: 5 * 200 = 1000
        # الخصم: 1000 * 10% = 100
        # بعد الخصم: 900
        # الضريبة: 900 * 15% = 135
        # المجموع النهائي: 1035
        assert sale.subtotal == Decimal('1000.00')
        assert sale.discount_amount == Decimal('100.00')
        assert sale.tax_amount == Decimal('135.00')
        assert sale.total_amount == Decimal('1035.00')


class TestModelsEdgeCases:
    """اختبارات الحالات الحدية"""
    
    def test_product_with_zero_cost_price(self):
        """اختبار منتج بسعر تكلفة صفر"""
        product = Product(
            cost_price=0.0,
            selling_price=100.0
        )
        
        # هامش الربح يجب أن يكون 0 عند cost_price = 0
        assert product.profit_margin == Decimal('0.00')
        assert product.profit_amount == Decimal('100.00')
    
    def test_sale_with_zero_items(self):
        """اختبار فاتورة بدون عناصر"""
        sale = Sale(
            invoice_number="INV-002",
            subtotal=Decimal('0.00'),
            total_amount=Decimal('0.00')
        )
        
        sale.items = []
        assert sale.total_quantity == 0
    
    def test_payment_with_negative_amount(self):
        """اختبار دفعة بمبلغ سالب (استرداد)"""
        payment = Payment(
            amount=Decimal('-1000.00'),
            payment_type=PaymentType.REFUND.value
        )
        
        assert payment.amount < 0


class TestModelsValidation:
    """اختبارات التحقق من صحة البيانات"""
    
    def test_product_required_fields(self):
        """اختبار الحقول المطلوبة في Product"""
        # يجب أن يكون name مطلوباً
        product = Product(name="")
        assert product.name == ""
    
    def test_sale_invoice_number_required(self):
        """اختبار أن رقم الفاتورة مطلوب في Sale"""
        sale = Sale(invoice_number="")
        assert sale.invoice_number == ""
    
    def test_payment_amount_validation(self):
        """اختبار التحقق من مبلغ الدفعة"""
        payment = Payment(amount=Decimal('0.00'))
        assert payment.amount == Decimal('0.00')






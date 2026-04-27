"""
Integration Tests for Sale Manager
اختبارات تكامل لـ SaleManager
"""

import pytest
import random
from decimal import Decimal
from datetime import date
from src.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod, SaleManager
from src.models.product import Product, ProductManager
from src.models.customer import Customer, CustomerManager


@pytest.mark.requires_db
class TestSaleManager:
    """اختبارات SaleManager"""
    
    def test_create_sale(self, db_manager, sample_product_data, sample_customer_data):
        """اختبار إنشاء فاتورة مبيعات"""
        # إنشاء عميل
        customer_manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)
        customer_id = customer_manager.create_customer(customer)
        
        if customer_id is None:
            pytest.skip("فشل في إنشاء العميل")
        
        # إنشاء منتج
        product_manager = ProductManager(db_manager)
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        product = Product(**product_data)
        product_id = product_manager.create_product(product)
        
        if product_id is None:
            pytest.skip("فشل في إنشاء المنتج")
        
        # إنشاء فاتورة
        sale_manager = SaleManager(db_manager)
        sale = Sale(
            customer_id=customer_id,
            invoice_number=f"INV-{random.randint(1000, 9999)}",
            items=[
                SaleItem(
                    product_id=product_id,
                    quantity=5,
                    unit_price=product.selling_price
                )
            ],
            status=SaleStatus.CONFIRMED
        )
        
        sale_id = sale_manager.create_sale(sale)
        assert sale_id is not None
        assert sale_id > 0
    
    def test_get_sale_by_id(self, db_manager, sample_product_data, sample_customer_data):
        """اختبار الحصول على فاتورة بالمعرف"""
        # إنشاء عميل ومنتج وفاتورة
        customer_manager = CustomerManager(db_manager)
        customer = Customer(**sample_customer_data)
        customer_id = customer_manager.create_customer(customer)
        
        if customer_id is None:
            pytest.skip("فشل في إنشاء العميل")
        
        product_manager = ProductManager(db_manager)
        product_data = sample_product_data.copy()
        product_data['barcode'] = f"TEST{random.randint(100000, 999999)}"
        product = Product(**product_data)
        product_id = product_manager.create_product(product)
        
        if product_id is None:
            pytest.skip("فشل في إنشاء المنتج")
        
        sale_manager = SaleManager(db_manager)
        sale = Sale(
            customer_id=customer_id,
            invoice_number=f"INV-{random.randint(1000, 9999)}",
            items=[
                SaleItem(product_id=product_id, quantity=3, unit_price=product.selling_price)
            ],
            status=SaleStatus.CONFIRMED
        )
        
        sale_id = sale_manager.create_sale(sale)
        assert sale_id is not None
        
        # الحصول على الفاتورة
        retrieved_sale = sale_manager.get_sale_by_id(sale_id)
        assert retrieved_sale is not None
        assert retrieved_sale.id == sale_id
        assert retrieved_sale.customer_id == customer_id
    
    def test_get_sales_summary(self, db_manager):
        """اختبار الحصول على ملخص المبيعات"""
        sale_manager = SaleManager(db_manager)
        
        summary = sale_manager.get_sales_summary()
        
        assert summary is not None
        assert isinstance(summary, dict)
        assert 'total_sales' in summary or 'total_amount' in summary
    
    def test_search_sales(self, db_manager):
        """اختبار البحث في المبيعات"""
        sale_manager = SaleManager(db_manager)
        
        # البحث بمعايير مختلفة
        results = sale_manager.search_sales(search_term="INV")
        assert isinstance(results, list)
        
        results = sale_manager.search_sales(status=SaleStatus.CONFIRMED)
        assert isinstance(results, list)
        
        results = sale_manager.search_sales(start_date=date.today())
        assert isinstance(results, list)





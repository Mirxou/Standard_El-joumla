"""
Unit Tests for Sale Model
اختبارات وحدة لنموذج المبيعات
"""

import pytest
from decimal import Decimal
from datetime import date, datetime
from src.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod


class TestSaleItem:
    """اختبارات SaleItem"""
    
    def test_sale_item_creation(self):
        """اختبار إنشاء SaleItem"""
        item = SaleItem(
            product_id=1,
            product_name="منتج اختبار",
            quantity=5,
            unit_price=100.0
        )
        
        assert item.product_id == 1
        assert item.product_name == "منتج اختبار"
        assert item.quantity == 5
        assert item.unit_price == Decimal('100.0')
    
    def test_sale_item_calculate_total(self):
        """اختبار حساب المجموع"""
        item = SaleItem(
            product_id=1,
            quantity=5,
            unit_price=100.0,
            discount_percentage=10.0,
            tax_percentage=15.0
        )
        
        item.calculate_total()
        
        # المجموع الفرعي: 5 * 100 = 500
        # الخصم: 500 * 10% = 50
        # بعد الخصم: 450
        # الضريبة: 450 * 15% = 67.5
        # المجموع النهائي: 517.5
        assert item.discount_amount == Decimal('50.00')
        assert item.total_amount == Decimal('517.50')
    
    def test_sale_item_to_dict(self):
        """اختبار تحويل SaleItem إلى قاموس"""
        item = SaleItem(
            id=1,
            sale_id=10,
            product_id=5,
            product_name="منتج",
            quantity=3,
            unit_price=50.0
        )
        
        item_dict = item.to_dict()
        assert item_dict['id'] == 1
        assert item_dict['sale_id'] == 10
        assert item_dict['product_id'] == 5
        assert item_dict['quantity'] == 3
        assert isinstance(item_dict['unit_price'], float)


class TestSale:
    """اختبارات Sale"""
    
    def test_sale_creation(self):
        """اختبار إنشاء Sale"""
        sale = Sale(
            invoice_number="INV-001",
            customer_id=1,
            sale_date=date.today(),
            status=SaleStatus.CONFIRMED
        )
        
        assert sale.invoice_number == "INV-001"
        assert sale.customer_id == 1
        assert sale.status == SaleStatus.CONFIRMED
        assert sale.items == []
    
    def test_sale_calculate_totals(self):
        """اختبار حساب المجاميع"""
        sale = Sale(
            invoice_number="INV-001",
            items=[
                SaleItem(product_id=1, quantity=2, unit_price=100.0),
                SaleItem(product_id=2, quantity=3, unit_price=50.0)
            ],
            discount_percentage=10.0,
            tax_percentage=15.0
        )
        
        sale.calculate_totals()
        
        # المجموع الفرعي: (2*100) + (3*50) = 200 + 150 = 350
        # الخصم: 350 * 10% = 35
        # بعد الخصم: 315
        # الضريبة: 315 * 15% = 47.25
        # المجموع النهائي: 362.25
        assert sale.subtotal == Decimal('350.00')
        assert sale.discount_amount == Decimal('35.00')
        assert sale.tax_amount == Decimal('47.25')
        assert sale.total_amount == Decimal('362.25')
    
    def test_sale_calculate_remaining(self):
        """اختبار حساب المبلغ المتبقي"""
        sale = Sale(
            invoice_number="INV-001",
            paid_amount=300.0
        )
        
        # إضافة items أولاً
        sale.add_item(SaleItem(product_id=1, quantity=1, unit_price=1000.0))
        
        # remaining_amount يتم حسابه تلقائياً في calculate_totals
        assert sale.remaining_amount == Decimal('700.00')
    
    def test_sale_is_paid(self):
        """اختبار التحقق من الدفع الكامل"""
        sale1 = Sale(paid_amount=1000.0)
        sale1.add_item(SaleItem(product_id=1, quantity=1, unit_price=1000.0))
        assert sale1.is_paid == True
        
        sale2 = Sale(paid_amount=500.0)
        sale2.add_item(SaleItem(product_id=1, quantity=1, unit_price=1000.0))
        assert sale2.is_paid == False
    
    def test_sale_status_partially_paid(self):
        """اختبار حالة الدفع الجزئي"""
        sale1 = Sale(paid_amount=500.0)
        sale1.add_item(SaleItem(product_id=1, quantity=1, unit_price=1000.0))
        # calculate_totals يتم استدعاؤه تلقائياً في add_item
        assert sale1.status == SaleStatus.PARTIALLY_PAID
        
        sale2 = Sale(paid_amount=0.0)
        sale2.add_item(SaleItem(product_id=1, quantity=1, unit_price=1000.0))
        assert sale2.status != SaleStatus.PARTIALLY_PAID
    
    def test_sale_to_dict(self):
        """اختبار تحويل Sale إلى قاموس"""
        sale = Sale(
            id=1,
            invoice_number="INV-001",
            customer_id=5,
            total_amount=1000.0
        )
        
        sale_dict = sale.to_dict()
        assert sale_dict['id'] == 1
        assert sale_dict['invoice_number'] == "INV-001"
        assert sale_dict['customer_id'] == 5
        assert isinstance(sale_dict['total_amount'], float)


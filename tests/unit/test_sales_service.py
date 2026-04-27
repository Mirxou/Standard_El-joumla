#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Sales Service
اختبارات خدمة المبيعات
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.services.sales_service import SalesService, SaleStatus, PaymentMethod


class TestSaleStatus:
    """اختبارات حالات الفاتورة"""
    
    def test_sale_status_values(self):
        """اختبار قيم حالات الفاتورة"""
        assert SaleStatus.PENDING.value == "pending"
        assert SaleStatus.COMPLETED.value == "completed"
        assert SaleStatus.CANCELLED.value == "cancelled"
        assert SaleStatus.REFUNDED.value == "refunded"


class TestPaymentMethod:
    """اختبارات طرق الدفع"""
    
    def test_payment_method_values(self):
        """اختبار قيم طرق الدفع"""
        assert PaymentMethod.CASH.value == "cash"
        assert PaymentMethod.CREDIT.value == "credit"
        assert PaymentMethod.CARD.value == "card"
        assert PaymentMethod.TRANSFER.value == "transfer"


class TestSalesServiceInitialization:
    """اختبارات تهيئة خدمة المبيعات"""
    
    def test_initialization_with_db_manager(self):
        """اختبار التهيئة مع مدير قاعدة البيانات"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_customer_manager = Mock()
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager,
            customer_manager=mock_customer_manager
        )
        
        assert service.db == mock_db
        assert service.sale_manager == mock_sale_manager
        assert service.product_manager == mock_product_manager
        assert service.customer_manager == mock_customer_manager
    
    def test_initialization_without_managers(self):
        """اختبار التهيئة بدون مدراء"""
        mock_db = Mock()
        
        with patch('src.services.sales_service.SaleManager') as mock_sale_class, \
             patch('src.services.sales_service.ProductManager') as mock_product_class, \
             patch('src.services.sales_service.CustomerManager') as mock_customer_class:
            
            mock_sale_class.return_value = Mock()
            mock_product_class.return_value = Mock()
            mock_customer_class.return_value = Mock()
            
            service = SalesService(db_manager=mock_db)
            
            assert service.db == mock_db


class TestCreateInvoice:
    """اختبارات إنشاء الفاتورة"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_customer_manager = Mock()
        
        mock_sale_manager.create_invoice.return_value = 1
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager,
            customer_manager=mock_customer_manager
        )
        return service
    
    def test_create_invoice_success(self, service_with_mocks):
        """اختبار إنشاء فاتورة بنجاح"""
        invoice_data = {
            'customer_id': 1,
            'user_id': 1,
            'notes': 'Test invoice'
        }
        
        result = service_with_mocks.create_invoice(invoice_data)
        
        assert result == 1
        service_with_mocks.sale_manager.create_invoice.assert_called_once()
    
    def test_create_invoice_db_error(self):
        """اختبار فشل إنشاء فاتورة"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_sale_manager.create_invoice.side_effect = Exception("DB Error")
        mock_logger = Mock()
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            logger=mock_logger
        )
        
        invoice_data = {'customer_id': 1}
        result = service.create_invoice(invoice_data)
        
        assert result is None


class TestAddSaleItem:
    """اختبارات إضافة عنصر للفاتورة"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_customer_manager = Mock()
        
        # Mock product
        mock_product = Mock()
        mock_product.id = 1
        mock_product.name = "Test Product"
        mock_product.price = 100.0
        mock_product.stock = 50
        mock_product_manager.get_by_id.return_value = mock_product
        
        mock_sale_manager.add_sale_item.return_value = True
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager,
            customer_manager=mock_customer_manager
        )
        return service
    
    def test_add_sale_item_success(self, service_with_mocks):
        """اختبار إضافة عنصر بنجاح"""
        result = service_with_mocks.add_sale_item(
            sale_id=1,
            product_id=1,
            quantity=2,
            unit_price=100.0
        )
        
        assert result is True
        service_with_mocks.product_manager.get_by_id.assert_called_once_with(1)
    
    def test_add_sale_item_product_not_found(self):
        """اختبار إضافة عنصر لمنتج غير موجود"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_product_manager.get_by_id.return_value = None
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager
        )
        
        result = service.add_sale_item(
            sale_id=1,
            product_id=999,
            quantity=1,
            unit_price=100.0
        )
        
        assert result is False
    
    def test_add_sale_item_insufficient_stock(self):
        """اختبار إضافة عنصر بكمية أكبر من المخزون"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        
        mock_product = Mock()
        mock_product.stock = 5
        mock_product_manager.get_by_id.return_value = mock_product
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager
        )
        
        result = service.add_sale_item(
            sale_id=1,
            product_id=1,
            quantity=10,
            unit_price=100.0,
            check_stock=True
        )
        
        assert result is False


class TestCompleteSale:
    """اختبارات إتمام البيع"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_customer_manager = Mock()
        
        # Mock sale
        mock_sale = Mock()
        mock_sale.id = 1
        mock_sale.status = SaleStatus.PENDING.value
        mock_sale.total_amount = 500.0
        mock_sale.customer_id = 1
        mock_sale_manager.get_sale_by_id.return_value = mock_sale
        
        mock_sale_manager.complete_sale.return_value = True
        mock_customer_manager.update_balance.return_value = True
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager,
            customer_manager=mock_customer_manager
        )
        return service
    
    def test_complete_sale_success(self, service_with_mocks):
        """اختبار إتمام البيع بنجاح"""
        result = service_with_mocks.complete_sale(
            sale_id=1,
            payment_method=PaymentMethod.CASH.value,
            amount_paid=500.0
        )
        
        assert result is True
        service_with_mocks.sale_manager.complete_sale.assert_called_once()
    
    def test_complete_sale_sale_not_found(self, service_with_mocks):
        """اختبار إتمام بيع لفاتورة غير موجودة"""
        service_with_mocks.sale_manager.get_sale_by_id.return_value = None
        
        result = service_with_mocks.complete_sale(
            sale_id=999,
            payment_method=PaymentMethod.CASH.value,
            amount_paid=500.0
        )
        
        assert result is False
    
    def test_complete_sale_already_completed(self, service_with_mocks):
        """اختبار إتمام بيع لفاتورة مكتملة"""
        mock_sale = Mock()
        mock_sale.status = SaleStatus.COMPLETED.value
        service_with_mocks.sale_manager.get_sale_by_id.return_value = mock_sale
        
        result = service_with_mocks.complete_sale(
            sale_id=1,
            payment_method=PaymentMethod.CASH.value,
            amount_paid=500.0
        )
        
        assert result is False
    
    def test_complete_sale_insufficient_payment(self, service_with_mocks):
        """اختبار إتمام بيع بمبلغ غير كافٍ"""
        result = service_with_mocks.complete_sale(
            sale_id=1,
            payment_method=PaymentMethod.CASH.value,
            amount_paid=300.0
        )
        
        assert result is False
    
    def test_complete_sale_credit_payment(self, service_with_mocks):
        """اختبار إتمام بيع بالدفع الآجل"""
        result = service_with_mocks.complete_sale(
            sale_id=1,
            payment_method=PaymentMethod.CREDIT.value,
            amount_paid=500.0
        )
        
        assert result is True
        service_with_mocks.customer_manager.update_balance.assert_called_once()


class TestCancelInvoice:
    """اختبارات إلغاء الفاتورة"""
    
    @pytest.fixture
    def service_with_mocks(self):
        """إنشاء خدمة مع mocks"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        mock_customer_manager = Mock()
        
        # Mock sale items
        mock_sale = Mock()
        mock_sale.id = 1
        mock_sale.status = SaleStatus.COMPLETED.value
        mock_sale.total_amount = 500.0
        mock_sale.customer_id = 1
        mock_sale.payment_method = PaymentMethod.CASH.value
        
        mock_sale_items = [
            {'product_id': 1, 'quantity': 2, 'unit_price': 100.0},
            {'product_id': 2, 'quantity': 1, 'unit_price': 300.0}
        ]
        
        mock_sale_manager.get_sale_by_id.return_value = mock_sale
        mock_sale_manager.get_sale_items.return_value = mock_sale_items
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager,
            customer_manager=mock_customer_manager
        )
        return service
    
    def test_cancel_invoice_success(self, service_with_mocks):
        """اختبار إلغاء فاتورة بنجاح"""
        mock_connection = Mock()
        mock_cursor = Mock()
        service_with_mocks.db.get_connection.return_value = (mock_connection, mock_cursor)
        
        result = service_with_mocks.cancel_invoice(
            sale_id=1,
            cancellation_reason="Customer request"
        )
        
        assert result is True
    
    def test_cancel_invoice_sale_not_found(self, service_with_mocks):
        """اختبار إلغاء فاتورة غير موجودة"""
        service_with_mocks.sale_manager.get_sale_by_id.return_value = None
        
        result = service_with_mocks.cancel_invoice(sale_id=999)
        
        assert result is False
    
    def test_cancel_invoice_already_cancelled(self, service_with_mocks):
        """اختبار إلغاء فاتورة ملغاة"""
        mock_sale = Mock()
        mock_sale.status = SaleStatus.CANCELLED.value
        service_with_mocks.sale_manager.get_sale_by_id.return_value = mock_sale
        
        result = service_with_mocks.cancel_invoice(sale_id=1)
        
        assert result is False


class TestRemoveSaleItem:
    """اختبارات حذف عنصر من الفاتورة"""
    
    def test_remove_sale_item_success(self):
        """اختبار حذف عنصر بنجاح"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_product_manager = Mock()
        
        mock_sale_manager.remove_sale_item.return_value = True
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager,
            product_manager=mock_product_manager
        )
        
        result = service.remove_sale_item(sale_id=1, product_id=1)
        
        assert result is True
        mock_sale_manager.remove_sale_item.assert_called_once_with(1, 1)
    
    def test_remove_sale_item_failure(self):
        """اختبار فشل حذف عنصر"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_sale_manager.remove_sale_item.return_value = False
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.remove_sale_item(sale_id=1, product_id=1)
        
        assert result is False


class TestGetSaleDetails:
    """اختبارات الحصول على تفاصيل الفاتورة"""
    
    def test_get_sale_details_success(self):
        """اختبار الحصول على تفاصيل بنجاح"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        
        mock_sale = Mock()
        mock_sale.id = 1
        mock_sale.total_amount = 500.0
        
        mock_sale_items = [
            {'product_id': 1, 'quantity': 2, 'unit_price': 100.0}
        ]
        
        mock_sale_manager.get_sale_by_id.return_value = mock_sale
        mock_sale_manager.get_sale_items.return_value = mock_sale_items
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.get_sale_details(1)
        
        assert result is not None
        assert 'sale' in result
        assert 'items' in result
    
    def test_get_sale_details_not_found(self):
        """اختبار الحصول على تفاصيل فاتورة غير موجودة"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_sale_manager.get_sale_by_id.return_value = None
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.get_sale_details(999)
        
        assert result is None


class TestSearchSales:
    """اختبارات البحث في المبيعات"""
    
    def test_search_sales_success(self):
        """اختبار البحث بنجاح"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        
        mock_sales = [
            {'id': 1, 'total_amount': 500.0},
            {'id': 2, 'total_amount': 300.0}
        ]
        mock_sale_manager.search_sales.return_value = mock_sales
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.search_sales(
            start_date=datetime.now() - timedelta(days=7),
            end_date=datetime.now()
        )
        
        assert len(result) == 2
    
    def test_search_sales_empty(self):
        """اختبار البحث بدون نتائج"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        mock_sale_manager.search_sales.return_value = []
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.search_sales()
        
        assert len(result) == 0


class TestGetSalesSummary:
    """اختبارات الحصول على ملخص المبيعات"""
    
    def test_get_sales_summary_success(self):
        """اختبار الحصول على ملخص بنجاح"""
        mock_db = Mock()
        mock_sale_manager = Mock()
        
        mock_summary = {
            'total_sales': 10000.0,
            'total_invoices': 50,
            'average_invoice': 200.0
        }
        mock_sale_manager.get_sales_summary.return_value = mock_summary
        
        service = SalesService(
            db_manager=mock_db,
            sale_manager=mock_sale_manager
        )
        
        result = service.get_sales_summary(
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now()
        )
        
        assert result is not None
        assert result['total_sales'] == 10000.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])




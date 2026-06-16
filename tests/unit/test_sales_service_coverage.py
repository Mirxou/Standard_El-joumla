#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage Tests for Sales Service
اختبارات تغطية إضافية لـ Sales Service
"""

from datetime import date
from decimal import Decimal
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.sales_service import SalesService


class TestSalesServiceCoverage:
    """اختبارات تغطية إضافية لـ Sales Service"""

    @pytest.fixture
    def db_manager(self):
        """Mock DatabaseManager"""
        mock = Mock()
        return mock

    @pytest.fixture
    def service(self, db_manager):
        """SalesService Instance with mocked managers"""
        with patch("src.services.sales_service.SaleManager"), patch("src.services.sales_service.ProductManager"), patch(
            "src.services.sales_service.CustomerManager"
        ), patch("src.services.sales_service.InventoryService"), patch(
            "src.services.sales_service.AccountingService"
        ), patch(
            "src.services.sales_service.ExchangeRateService"
        ):
            service = SalesService(db_manager, logger=Mock())

        # Restore mock objects for verification
        service.sale_manager = Mock()
        service.product_manager = Mock()
        service.customer_manager = Mock()
        service.inventory_service = Mock()
        service.accounting_service = Mock()
        service.exchange_rate_service = Mock()
        return service

    def test_create_sale_success_with_inventory_update(self, service):
        """اختبار إنشاء فاتورة ناجحة مع تحديث المخزون"""
        # Data Setup
        sale_item = Mock(product_id=1, quantity=2, unit_price=100, discount_amount=0)
        sale = Mock(items=[sale_item], total_amount=200, currency_id=None, customer_id=1)

        # Mocks
        product = Mock(id=1, current_stock=10, name="Test Product")
        service.product_manager.get_product_by_id.return_value = product
        service.sale_manager.create_sale.return_value = 1
        service.accounting_service.create_sale_journal_entry.return_value = 101

        # Execution
        result = service.create_sale(sale, user_id=1)

        # Verification
        assert result == 1
        service.inventory_service.adjust_stock.assert_called_with(
            product_id=1, new_quantity=8, reason="sale:1", user_id=1  # 10 - 2
        )
        service.customer_manager.update_balance.assert_called()

    def test_create_sale_insufficient_stock(self, service):
        """اختبار فشل الفاتورة بسبب نقص المخزون"""
        # Data
        sale_item = Mock(product_id=1, quantity=5)
        sale = Mock(items=[sale_item])

        # Mock product with low stock
        product = Mock(id=1, current_stock=2, name="Low Stock Pro")
        service.product_manager.get_product_by_id.return_value = product

        # Execution
        result = service.create_sale(sale)

        # Verification
        assert result is None
        service.sale_manager.create_sale.assert_not_called()

    def test_create_sale_multi_currency(self, service):
        """اختبار إنشاء فاتورة بعملة مختلفة"""
        sale = Mock(items=[], total_amount=100, currency_id=2, sale_date=date.today())

        # Mock Exchange
        base_currency = Mock(id=1)
        service.exchange_rate_service.currency_manager.get_base_currency.return_value = base_currency
        service.exchange_rate_service.get_exchange_rate.return_value = Decimal("1.2")
        service.sale_manager.create_sale.return_value = 1

        # Execution
        service.create_sale(sale)

        # Verification
        # Check if sale object was updated with rates
        assert sale.exchange_rate == Decimal("1.2")
        assert sale.base_amount == 120  # 100 * 1.2

    def test_start_pos_session_success(self, service, db_manager):
        """اختبار بدء جلسة نقطة بيع"""
        service.current_session = None
        db_manager.execute_query.return_value = Mock(lastrowid=55)

        session_id = service.start_pos_session(user_id=1, opening_cash=100.0)

        assert session_id == 55
        assert service.current_session is not None
        assert service.current_session.id == 55
        assert service.current_session.opening_cash == 100.0

    def test_start_pos_session_already_active(self, service):
        """اختبار منع بدء جلسة جديدة مع وجود جلسة نشطة"""
        service.current_session = Mock(is_active=True)

        result = service.start_pos_session(1)

        assert result is None

    def test_end_pos_session_success(self, service, db_manager):
        """اختبار إنهاء جلسة نقطة بيع"""
        service.current_session = Mock(id=55, is_active=True)
        db_manager.execute_query.return_value = Mock(rowcount=1)

        result = service.end_pos_session(closing_cash=500.0)

        assert result is True
        assert service.current_session.is_active is False
        assert service.current_session.closing_cash == 500.0

    def test_generate_sales_report(self, service):
        """اختبار إنشاء تقرير المبيعات"""
        # Mock internal helpers (mocking methods on the service instance itself requires careful patch)
        # Instead, we mock what they call or rely on calling the actual methods if safe.
        # Here we'll patch the private methods on the instance to simplify unit testing the aggregating method.

        with patch.object(service, "_get_sales_statistics") as mock_stats, patch.object(
            service, "_get_top_selling_products"
        ) as mock_prods, patch.object(service, "_get_top_customers") as mock_custs, patch.object(
            service, "_get_sales_by_day"
        ) as mock_days, patch.object(
            service, "_get_sales_by_payment_method"
        ) as mock_pay:

            mock_stats.return_value = {
                "total_sales": 10,
                "total_revenue": 1000,
                "total_profit": 200,
                "average_sale_value": 100,
            }
            mock_prods.return_value = []
            mock_custs.return_value = []
            mock_days.return_value = []
            mock_pay.return_value = []

            report = service.generate_sales_report(date.today(), date.today())

            assert report.total_sales == 10
            assert report.total_revenue == 1000

    def test_get_daily_summary(self, service, db_manager):
        """اختبار الحصول على الملخص اليومي"""
        # Mock DB response
        # Schema: count, revenue, cash, card, credit, returns
        db_manager.fetch_one.return_value = (10, 5000.0, 2000.0, 3000.0, 0.0, 100.0)

        with patch.object(service, "_calculate_daily_profit", return_value=1500.0):
            summary = service.get_daily_summary(date.today())

            assert summary.total_sales == 10
            assert summary.total_revenue == 5000.0
            assert summary.net_sales == 4900.0  # 5000 - 100
            assert summary.total_profit == 1500.0

    def test_add_sale_item_pricing_logic(self, service):
        """اختبار منطق التسعير عند إضافة منتج"""
        product = Mock(
            id=1,
            current_stock=100,
            selling_price=50,
            min_wholesale_qty=10,
            wholesale_price=40,
            name="P1",
        )
        service.product_manager.get_product_by_id.return_value = product
        service.sale_manager.add_sale_item.return_value = True

        # 1. Normal Quantity -> Selling Price
        result = service.add_sale_item(sale_id=1, product_id=1, quantity=1)
        assert result is True

        assert service.sale_manager.add_sale_item.called
        call_args = service.sale_manager.add_sale_item.call_args[0][0]  # SaleItem object
        assert call_args.unit_price == 50

        # Reset mock for next call
        service.sale_manager.add_sale_item.reset_mock()

        # 2. Wholesale Quantity -> Wholesale Price
        result2 = service.add_sale_item(sale_id=1, product_id=1, quantity=12)
        assert result2 is True

        assert service.sale_manager.add_sale_item.called
        call_args2 = service.sale_manager.add_sale_item.call_args[0][0]
        assert call_args2.unit_price == 40

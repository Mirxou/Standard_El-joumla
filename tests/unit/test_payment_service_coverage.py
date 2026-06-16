#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coverage Tests for Payment Service
اختبارات تغطية إضافية لـ Payment Service
"""

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path  # noqa: F811
from unittest.mock import Mock, patch

import pytest

# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.payment import AccountType, PaymentType
from src.services.payment_service import PaymentService


class TestPaymentServiceCoverage:
    """اختبارات تغطية إضافية لـ Payment Service"""

    @pytest.fixture
    def db_manager(self):
        """Mock DatabaseManager"""
        mock = Mock()
        # Mock table_exists to return True by default
        mock.table_exists.return_value = True
        return mock

    @pytest.fixture
    def service(self, db_manager):
        """PaymentService Instance"""
        # Mock dependencies inside init
        with patch("src.services.payment_service.PaymentManager"), patch(
            "src.services.payment_service.CustomerManager"
        ), patch("src.services.payment_service.SupplierManager"), patch(
            "src.services.payment_service.ExchangeRateService"
        ):
            service = PaymentService(db_manager, logger=Mock())

        # Restore mock managers for testing
        service.payment_manager = Mock()
        service.customer_manager = Mock()
        service.supplier_manager = Mock()
        service.exchange_rate_service = Mock()
        return service

    def test_create_supplier_payment_success(self, service):
        """اختبار إنشاء دفعة مورد بنجاح"""
        # Setup mocks
        service.payment_manager.create_payment.return_value = 1
        service.payment_manager.get_payment_by_id.return_value = Mock(id=1, company_id=1, to_dict=lambda: {"id": 1})

        # Call functionality
        with patch("src.services.webhook_service.WebhookService") as MockWebhook:
            webhook_instance = MockWebhook.return_value

            result = service.create_supplier_payment(
                supplier_id=1,
                amount=Decimal("500.00"),
                payment_method="cash",
                reference_number="SUP123",
            )

            assert result is not None
            # Verify payment creation
            assert service.payment_manager.create_payment.called
            # Verify webhook trigger
            # Use any dictionary mapping for payload since fields like created_at are dynamic
            call_args = webhook_instance.trigger_webhook.call_args
            assert call_args is not None
            _, kwargs = call_args
            assert kwargs["event_type"] == "supplier_payment_made"
            assert kwargs["entity_id"] == 1
            assert kwargs["company_id"] == 1
            assert "event" in kwargs["payload"]
            assert kwargs["payload"]["event"] == "supplier_payment_made"

    def test_create_supplier_payment_exception(self, service):
        """اختبار فشل إنشاء دفعة مورد"""
        service.payment_manager.create_payment.side_effect = Exception("DB Error")

        result = service.create_supplier_payment(1, Decimal("100"))

        assert result is None
        service.logger.error.assert_called()

    def test_create_customer_payment_multi_currency(self, service):
        """اختبار إنشاء دفعة عميل بعملة مختلفة"""
        # Setup currency mocks
        base_currency = Mock(id=1, code="USD")
        service.exchange_rate_service.currency_manager.get_base_currency.return_value = base_currency
        service.exchange_rate_service.get_exchange_rate.return_value = Decimal("1.5")

        service.payment_manager.create_payment.return_value = 1
        service.payment_manager.get_payment_by_id.return_value = Mock(id=1)

        # Create payment with specific currency (ID 2)
        service.create_customer_payment(customer_id=1, amount=Decimal("100.00"), currency_id=2)

        # Verify call to create_payment has converted values
        args, _ = service.payment_manager.create_payment.call_args
        payment_obj = args[0]

        assert payment_obj.exchange_rate == Decimal("1.5")
        assert payment_obj.base_amount == Decimal("150.00")  # 100 * 1.5

    def test_create_customer_payment_currency_error_fallback(self, service):
        """اختبار الفشل في حساب العملة والعودة للأساسي"""
        service.exchange_rate_service.currency_manager.get_base_currency.side_effect = Exception("Rate Error")

        service.payment_manager.create_payment.return_value = 1
        service.payment_manager.get_payment_by_id.return_value = Mock(id=1)

        service.create_customer_payment(customer_id=1, amount=Decimal("100.00"), currency_id=999)

        args, _ = service.payment_manager.create_payment.call_args
        payment_obj = args[0]

        # Should fallback to 1.0 rate
        assert payment_obj.exchange_rate == Decimal("1.0")
        assert payment_obj.base_amount == Decimal("100.00")

    def test_get_overdue_receivables(self, service):
        """اختبار تقرير الذمم المدينة المتأخرة وترتيبها"""
        today = date.today()
        # Create dummy payments with different overdue days
        p1 = Mock(
            customer_id=1,
            payment_type=PaymentType.CUSTOMER_PAYMENT.value,
            due_date=today - timedelta(days=10),
            amount=100,
        )
        p2 = Mock(
            customer_id=2,
            payment_type=PaymentType.CUSTOMER_PAYMENT.value,
            due_date=today - timedelta(days=50),
            amount=200,
        )  # More overdue

        service.payment_manager.get_overdue_payments.return_value = [p1, p2]
        service.customer_manager.get_customer_by_id.side_effect = lambda id: Mock(id=id, name=f"C{id}")

        result = service.get_overdue_receivables()

        # Verify sorting (descending by days overdue)
        assert len(result) == 2
        assert result[0]["customer_id"] == 2  # 50 days overdue
        assert result[1]["customer_id"] == 1  # 10 days overdue
        assert result[0]["days_overdue"] == 50

    def test_get_payment_schedules_filtering(self, service, db_manager):
        """اختبار فلترة جدولة المدفوعات"""
        # Mock DB returns
        db_manager.fetch_all.return_value = []

        # 1. Test without completed
        service.get_payment_schedules(include_completed=False)
        query = db_manager.fetch_all.call_args[0][0]
        assert "status != ?" in query

        # 2. Test with completed
        service.get_payment_schedules(include_completed=True)
        query = db_manager.fetch_all.call_args[0][0]
        assert "status != ?" not in query

    def test_get_payment_schedules_table_not_exists(self, service, db_manager):
        """اختبار عدم وجود جدول الجدولة"""
        db_manager.table_exists.return_value = False
        assert service.get_payment_schedules() == []

    def test_get_aging_report_receivables(self, service, db_manager):
        """اختبار تقرير أعمار الذمم المدينة"""
        service.get_aging_report(AccountType.RECEIVABLE.value)

        # Verify query parameters
        call_args = db_manager.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "FROM customers" in query
        assert params[-2] == PaymentType.CUSTOMER_PAYMENT.value

    def test_get_aging_report_payables(self, service, db_manager):
        """اختبار تقرير أعمار الذمم الدائنة"""
        service.get_aging_report(AccountType.PAYABLE.value)

        # Verify query parameters
        call_args = db_manager.fetch_all.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert "FROM suppliers" in query
        assert params[-2] == PaymentType.SUPPLIER_PAYMENT.value

    def test_init_creates_tables(self, db_manager):
        """اختبار إنشاء الجداول عند التهيئة"""
        # Setup mocks to track calls
        db_manager.execute_query = Mock()

        with patch("src.services.payment_service.PaymentManager"), patch(
            "src.services.payment_service.CustomerManager"
        ), patch("src.services.payment_service.SupplierManager"), patch(
            "src.services.payment_service.ExchangeRateService"
        ):
            PaymentService(db_manager)

        assert db_manager.execute_query.called
        # Check that payments table creation was attempted
        args_list = db_manager.execute_query.call_args_list
        assert any("CREATE TABLE IF NOT EXISTS payments" in str(Call) for Call in args_list)

    def test_create_tables_fallback_cursor(self, db_manager):
        """اختبار إنشاء الجداول باستخدام الـ cursor عند غياب execute_query"""
        # Remove execute_query from mock
        del db_manager.execute_query

        # Setup connection mock
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        db_manager.connection = mock_conn

        # We need to manually invoke _create_tables or init
        # Since init is hard to bypass mocks cleanly without recreating logic,
        # let's instantiate normally but mocking managers
        with patch("src.services.payment_service.PaymentManager"), patch(
            "src.services.payment_service.CustomerManager"
        ), patch("src.services.payment_service.SupplierManager"), patch(
            "src.services.payment_service.ExchangeRateService"
        ):

            srv = PaymentService(db_manager)
            srv._create_tables()  # Explicit call to test fallback path

        assert mock_cursor.execute.called

    def test_create_supplier_payment_webhook_silent_fail(self, service):
        """اختبار فشل الـ Webhook بصمت عند إنشاء دفعة"""
        service.payment_manager.create_payment.return_value = 1
        service.payment_manager.get_payment_by_id.return_value = Mock(id=1)

        # Mock WebhookService to raise Exception
        with patch(
            "src.services.webhook_service.WebhookService",
            side_effect=Exception("Import Error"),
        ):
            # Should not raise exception
            result = service.create_supplier_payment(1, Decimal("100"))
            assert result is not None

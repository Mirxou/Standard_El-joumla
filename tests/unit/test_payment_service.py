from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from src.models.payment import Payment, PaymentType
from src.services.payment_service import PaymentService


class TestPaymentService:
    """اختبارات وحدة لخدمة المدفوعات"""

    @pytest.fixture
    def mock_db_manager(self):
        mock = MagicMock()
        # محاكاة PRAGMA table_info لتجنب أخطاء التهيئة
        mock.connection.execute.return_value.fetchall.return_value = []
        return mock

    @pytest.fixture
    def service(self, mock_db_manager):
        return PaymentService(mock_db_manager)

    def test_get_payment_by_id(self, service):
        """اختبار استرجاع دفعة بواسطة المعرف"""
        payment_id = 1
        mock_payment = Payment(id=1, amount=Decimal("100.00"), payment_type="customer_payment")

        service.payment_manager = MagicMock()
        service.payment_manager.get_payment_by_id.return_value = mock_payment

        payment = service.get_payment_by_id(payment_id)

        assert payment is not None
        assert payment.id == 1
        assert payment.amount == Decimal("100.00")
        service.payment_manager.get_payment_by_id.assert_called_once_with(payment_id)

    def test_create_customer_payment(self, service):
        """اختبار إنشاء دفعة من العميل"""
        customer_id = 1
        amount = Decimal("500.00")

        service.payment_manager = MagicMock()
        service.payment_manager.create_payment.return_value = 1

        mock_payment = Payment(id=1, amount=amount, customer_id=customer_id)
        service.payment_manager.get_payment_by_id.return_value = mock_payment

        service.exchange_rate_service = MagicMock()

        payment = service.create_customer_payment(customer_id=customer_id, amount=amount, payment_method="cash")

        assert payment is not None
        assert payment.amount == amount
        assert payment.customer_id == customer_id

    def test_get_customer_payments(self, service):
        """اختبار استرجاع مدفوعات العميل"""
        customer_id = 1
        mock_payments = [
            Payment(id=1, customer_id=customer_id, amount=Decimal("100.00")),
            Payment(id=2, customer_id=customer_id, amount=Decimal("200.00")),
        ]

        service.payment_manager = MagicMock()
        service.payment_manager.get_customer_payments.return_value = mock_payments

        payments = service.get_customer_payments(customer_id)

        assert len(payments) == 2
        assert all(isinstance(p, Payment) for p in payments)
        assert all(p.customer_id == customer_id for p in payments)

    def test_get_accounts_receivable(self, service, mock_db_manager):
        """اختبار الحصول على الذمم المدينة"""
        # (id, name, phone, current_balance, credit_limit, available_credit, payments_count, last_payment_date, overdue_payments)  # noqa: E501
        mock_rows = [(1, "Customer 1", "123456", 500.0, 1000.0, 500.0, 5, "2023-01-01", 0)]
        mock_db_manager.fetch_all.return_value = mock_rows

        receivables = service.get_accounts_receivable()

        assert len(receivables) == 1
        assert receivables[0]["customer_name"] == "Customer 1"
        assert receivables[0]["balance"] == Decimal("500.0")

    def test_get_payment_summary(self, service, mock_db_manager):
        """اختبار الحصول على ملخص المدفوعات"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)

        # (payment_type, payment_method, count, total_amount)
        mock_rows = [(PaymentType.CUSTOMER_PAYMENT.value, "cash", 5, 1000.0)]
        mock_db_manager.fetch_all.return_value = mock_rows

        summary = service.get_payment_summary(start_date, end_date)

        assert "totals" in summary
        assert summary["totals"]["customer_payments"] == Decimal("1000.0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

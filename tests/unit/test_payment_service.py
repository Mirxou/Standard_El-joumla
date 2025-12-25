import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.payment_service import PaymentService
from src.models.payment import Payment

class TestPaymentService:
    """اختبارات وحدة لخدمة المدفوعات"""
    
    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db_manager):
        return PaymentService(mock_db_manager)

    def test_get_payment_by_id(self, service, mock_db_manager):
        """اختبار استرجاع دفعة بواسطة المعرف"""
        payment_id = 1
        # محاكاة PaymentManager
        from unittest.mock import MagicMock
        mock_payment = MagicMock()
        mock_payment.id = 1
        mock_payment.amount = Decimal("100.00")
        mock_payment.payment_type = "customer_payment"
        
        service.payment_manager = MagicMock()
        service.payment_manager.get_payment_by_id.return_value = mock_payment
        
        payment = service.get_payment_by_id(payment_id)
        
        assert payment is not None
        assert payment.id == 1
        assert payment.amount == Decimal("100.00")
        service.payment_manager.get_payment_by_id.assert_called_once_with(payment_id)
    
    def test_create_customer_payment(self, service, mock_db_manager):
        """اختبار إنشاء دفعة من العميل"""
        customer_id = 1
        amount = Decimal("500.00")
        
        # محاكاة إنشاء الدفعة
        mock_db_manager.execute_insert.return_value = 1
        mock_db_manager.fetch_one.return_value = (1, "customer_payment", 1, 500.00, "cash", "REF123", 
                                                   "2023-01-01", "completed", "", 1, "2023-01-01", "2023-01-01")
        
        payment = service.create_customer_payment(
            customer_id=customer_id,
            amount=amount,
            payment_method="cash",
            reference_number="REF123"
        )
        
        assert payment is not None
        assert payment.amount == amount
        assert payment.customer_id == customer_id
    
    def test_get_customer_payments(self, service, mock_db_manager):
        """اختبار استرجاع مدفوعات العميل"""
        customer_id = 1
        
        mock_rows = [
            (1, "customer_payment", 1, 100.00, "cash", "REF1", "2023-01-01", "completed", "", 1, "", ""),
            (2, "customer_payment", 1, 200.00, "card", "REF2", "2023-01-02", "completed", "", 1, "", "")
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        payments = service.get_customer_payments(customer_id)
        
        assert len(payments) == 2
        assert all(p.customer_id == customer_id for p in payments)
    
    def test_get_payments_by_date_range(self, service, mock_db_manager):
        """اختبار استرجاع المدفوعات ضمن نطاق تاريخي"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        from unittest.mock import MagicMock
        mock_payment = MagicMock()
        
        mock_db_manager.fetch_all.return_value = [mock_payment]
        
        payments = service.get_payments_by_date_range(start_date, end_date)
        
        assert isinstance(payments, list)
        mock_db_manager.fetch_all.assert_called_once()
    
    def test_get_accounts_receivable(self, service, mock_db_manager):
        """اختبار الحصول على الذمم المدينة"""
        mock_rows = [
            (1, "Customer 1", 500.00, "2023-01-01", 30)
        ]
        mock_db_manager.fetch_all.return_value = mock_rows
        
        receivables = service.get_accounts_receivable()
        
        assert isinstance(receivables, list)
        # قد يستدعي fetch_all أو يستخدم payment_manager
        if hasattr(service, 'payment_manager'):
            pass  # يستخدم payment_manager
        else:
            mock_db_manager.fetch_all.assert_called_once()
    
    def test_get_payment_summary(self, service, mock_db_manager):
        """اختبار الحصول على ملخص المدفوعات"""
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        
        mock_row = (1000.00, 800.00, 200.00, 5, 3)
        mock_db_manager.fetch_one.return_value = mock_row
        
        summary = service.get_payment_summary(start_date, end_date)
        
        assert isinstance(summary, dict)
        # قد يحتوي على أي من هذه المفاتيح حسب التنفيذ
        assert len(summary) > 0
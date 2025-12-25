import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.purchase_service import PurchaseService
from src.models.purchase import Purchase
from src.models.supplier import Supplier

class TestPurchaseService:
    """اختبارات وحدة لخدمة المشتريات"""

    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db_manager):
        # عمل mock للمدراء الذين يتم إنشاؤهم داخل الخدمة
        with patch('src.services.purchase_service.PurchaseManager') as MockPurchaseManager, \
             patch('src.services.purchase_service.SupplierManager') as MockSupplierManager, \
             patch('src.services.purchase_service.ExchangeRateService') as MockExchangeRateService:
            
            service = PurchaseService(mock_db_manager, logger=MagicMock())
            # ربط الـ mocks بالخدمة للتحقق منها لاحقاً
            service.purchase_manager = MockPurchaseManager.return_value
            service.supplier_manager = MockSupplierManager.return_value
            service.exchange_rate_service = MockExchangeRateService.return_value
            return service

    def test_create_purchase_success(self, service):
        """اختبار إنشاء فاتورة شراء بنجاح"""
        purchase = Purchase(
            invoice_number="PO-2025-001",
            supplier_id=1,
            total_amount=Decimal("500.00"),
            purchase_date=date.today()
        )
        
        # محاكاة أن مدير المشتريات يعيد ID جديد
        service.purchase_manager.create_purchase.return_value = 101
        
        result = service.create_purchase(purchase)
        
        assert result == 101
        service.purchase_manager.create_purchase.assert_called_once_with(purchase)
        # التحقق من أن المبلغ الأساسي تم تعيينه بشكل صحيح
        assert purchase.base_amount == purchase.total_amount

    def test_create_purchase_with_currency_conversion(self, service):
        """اختبار إنشاء فاتورة شراء مع تحويل العملة"""
        purchase = Purchase(
            invoice_number="PO-2025-002",
            supplier_id=2,
            total_amount=Decimal("100.00"),
            currency_id=2, # مثلاً دولار أمريكي
            purchase_date=date.today()
        )
        
        # محاكاة خدمة أسعار الصرف
        mock_base_currency = MagicMock()
        mock_base_currency.id = 1 # مثلاً دينار جزائري
        service.exchange_rate_service.currency_manager.get_base_currency.return_value = mock_base_currency
        service.exchange_rate_service.get_exchange_rate.return_value = Decimal("134.50")
        
        service.purchase_manager.create_purchase.return_value = 102
        
        result = service.create_purchase(purchase)
        
        assert result == 102
        service.exchange_rate_service.get_exchange_rate.assert_called_once()
        assert purchase.exchange_rate == Decimal("134.50")
        assert purchase.base_amount == Decimal("13450.00") # 100 * 134.50
        service.purchase_manager.create_purchase.assert_called_once_with(purchase)

    def test_get_purchase_by_id(self, service):
        """اختبار استرجاع فاتورة شراء بواسطة المعرف"""
        purchase_id = 1
        mock_purchase = Purchase(id=purchase_id, invoice_number="PO-TEST-1")
        service.purchase_manager.get_purchase_by_id.return_value = mock_purchase
        
        result = service.get_purchase_by_id(purchase_id)
        
        assert result is not None
        assert result.id == purchase_id
        service.purchase_manager.get_purchase_by_id.assert_called_once_with(purchase_id)

    def test_cancel_purchase(self, service):
        """اختبار إلغاء فاتورة شراء"""
        purchase_id = 5
        reason = "Order cancelled by supplier"
        service.purchase_manager.cancel_purchase.return_value = True
        
        result = service.cancel_purchase(purchase_id, reason)
        
        assert result is True
        service.purchase_manager.cancel_purchase.assert_called_once_with(purchase_id, reason)
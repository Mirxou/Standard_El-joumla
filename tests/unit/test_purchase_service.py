import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
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
        service.purchase_manager.create_purchase.assert_called_once()

    def test_create_purchase_failure(self, service):
        """اختبار فشل إنشاء فاتورة شراء"""
        purchase = Purchase(
            invoice_number="PO-2025-002",
            supplier_id=1,
            total_amount=Decimal("500.00"),
            purchase_date=date.today()
        )
        
        # محاكاة فشل الإنشاء
        service.purchase_manager.create_purchase.return_value = None
        
        result = service.create_purchase(purchase)
        
        assert result is None

    def test_get_purchase_by_id_success(self, service):
        """اختبار الحصول على فاتورة شراء بالمعرف"""
        expected_purchase = Purchase(
            id=1,
            invoice_number="PO-2025-001",
            supplier_id=1,
            total_amount=Decimal("500.00"),
            purchase_date=date.today()
        )
        
        service.purchase_manager.get_purchase_by_id.return_value = expected_purchase
        
        result = service.get_purchase_by_id(1)
        
        assert result == expected_purchase
        assert result.invoice_number == "PO-2025-001"

    def test_get_purchase_by_id_not_found(self, service):
        """اختبار الحصول على فاتورة غير موجودة"""
        service.purchase_manager.get_purchase_by_id.return_value = None
        
        result = service.get_purchase_by_id(999)
        
        assert result is None

    def test_update_purchase_success(self, service):
        """اختبار تحديث فاتورة شراء بنجاح"""
        purchase = Purchase(
            id=1,
            invoice_number="PO-2025-001",
            supplier_id=1,
            total_amount=Decimal("600.00"),
            purchase_date=date.today()
        )
        
        service.purchase_manager.update_purchase.return_value = True
        
        result = service.update_purchase(purchase)
        
        assert result is True

    def test_delete_purchase_success(self, service):
        """اختبار حذف فاتورة شراء بنجاح"""
        service.purchase_manager.delete_purchase.return_value = True
        
        result = service.delete_purchase(1)
        
        assert result is True

    def test_get_all_purchases(self, service):
        """اختبار الحصول على جميع فواتير الشراء"""
        purchases = [
            Purchase(id=1, invoice_number="PO-2025-001", supplier_id=1, total_amount=Decimal("500.00")),
            Purchase(id=2, invoice_number="PO-2025-002", supplier_id=2, total_amount=Decimal("300.00"))
        ]
        
        service.purchase_manager.get_all_purchases.return_value = purchases
        
        result = service.get_all_purchases()
        
        assert len(result) == 2
        assert result[0].invoice_number == "PO-2025-001"

    def test_search_purchases(self, service):
        """اختبار البحث في فواتير الشراء"""
        purchases = [
            Purchase(id=1, invoice_number="PO-2025-001", supplier_id=1, total_amount=Decimal("500.00"))
        ]
        
        service.purchase_manager.search_purchases.return_value = purchases
        
        result = service.search_purchases("PO-2025")
        
        assert len(result) == 1
        assert result[0].invoice_number == "PO-2025-001"

    def test_add_purchase_item(self, service):
        """اختبار إضافة عنصر إلى فاتورة شراء"""
        service.purchase_manager.add_purchase_item.return_value = 201
        
        result = service.add_purchase_item(
            purchase_id=1,
            product_id=1,
            quantity=10,
            unit_price=Decimal("50.00")
        )
        
        assert result == 201

    def test_get_purchase_items(self, service):
        """اختبار الحصول على عناصر فاتورة الشراء"""
        items = [
            {"id": 1, "product_id": 1, "quantity": 10, "unit_price": 50.00},
            {"id": 2, "product_id": 2, "quantity": 5, "unit_price": 30.00}
        ]
        
        service.purchase_manager.get_purchase_items.return_value = items
        
        result = service.get_purchase_items(1)
        
        assert len(result) == 2

    def test_calculate_total(self, service):
        """اختبار حساب إجمالي الفاتورة"""
        items = [
            {"quantity": 10, "unit_price": 50.00},
            {"quantity": 5, "unit_price": 30.00}
        ]
        
        service.purchase_manager.get_purchase_items.return_value = items
        
        total = service.calculate_purchase_total(1)
        
        assert total == Decimal("650.00")  # (10*50) + (5*30)

    def test_get_purchases_by_supplier(self, service):
        """اختبار الحصول على فواتير المورد"""
        purchases = [
            Purchase(id=1, invoice_number="PO-2025-001", supplier_id=1, total_amount=Decimal("500.00"))
        ]
        
        service.purchase_manager.get_purchases_by_supplier.return_value = purchases
        
        result = service.get_purchases_by_supplier(1)
        
        assert len(result) == 1
        assert result[0].supplier_id == 1

    def test_get_purchases_by_date_range(self, service):
        """اختبار الحصول على فواتير بنطاق تاريخي"""
        purchases = [
            Purchase(id=1, invoice_number="PO-2025-001", supplier_id=1, 
                   total_amount=Decimal("500.00"), purchase_date=date(2025, 1, 15))
        ]
        
        service.purchase_manager.get_purchases_by_date_range.return_value = purchases
        
        result = service.get_purchases_by_date_range(date(2025, 1, 1), date(2025, 1, 31))
        
        assert len(result) == 1

    def test_cancel_purchase(self, service):
        """اختبار إلغاء فاتورة شراء"""
        service.purchase_manager.cancel_purchase.return_value = True
        
        result = service.cancel_purchase(1)
        
        assert result is True

    def test_get_purchase_summary(self, service):
        """اختبار الحصول على ملخص المشتريات"""
        summary = {
            "total_purchases": 10,
            "total_amount": Decimal("5000.00"),
            "average_amount": Decimal("500.00")
        }
        
        service.purchase_manager.get_purchase_summary.return_value = summary
        
        result = service.get_purchase_summary()
        
        assert result["total_purchases"] == 10
        assert result["total_amount"] == Decimal("5000.00")

    def test_validate_purchase_data(self, service):
        """اختبار التحقق من صحة بيانات الفاتورة"""
        purchase = Purchase(
            invoice_number="PO-2025-001",
            supplier_id=1,
            total_amount=Decimal("500.00"),
            purchase_date=date.today()
        )
        
        # لا يجب أن يظهر خطأ
        assert purchase.invoice_number == "PO-2025-001"
        assert purchase.supplier_id == 1

    def test_update_purchase_status(self, service):
        """اختبار تحديث حالة الفاتورة"""
        service.purchase_manager.update_purchase_status.return_value = True
        
        result = service.update_purchase_status(1, "completed")
        
        assert result is True

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

    def test_cancel_purchase_with_reason(self, service):
        """اختبار إلغاء فاتورة شراء مع سبب"""
        purchase_id = 5
        reason = "Order cancelled by supplier"
        service.purchase_manager.cancel_purchase.return_value = True
        
        result = service.cancel_purchase(purchase_id, reason)
        
        assert result is True
        service.purchase_manager.cancel_purchase.assert_called_once_with(purchase_id, reason)





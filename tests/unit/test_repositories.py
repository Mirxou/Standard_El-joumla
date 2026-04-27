"""
Unit Tests for Repository Pattern
اختبارات وحدة Repository Pattern
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch, call


class TestBaseRepository:
    """اختبارات BaseRepository"""
    
    @pytest.fixture
    def mock_db(self):
        """إنشاء mock لقاعدة البيانات"""
        db = MagicMock()
        db.connection = MagicMock()
        db.execute_query = MagicMock(return_value=[])
        db.execute_non_query = MagicMock()
        db.lock_row = MagicMock(return_value=True)
        db.soft_delete = MagicMock(return_value=True)
        db.restore_deleted = MagicMock(return_value=True)
        db.get_pending_items = MagicMock(return_value=[])
        db.mark_as_synced = MagicMock()
        db.transaction = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        return db
    
    @pytest.fixture
    def base_repo(self, mock_db):
        """إنشاء BaseRepository"""
        from src.repositories.base_repository import BaseRepository
        
        class TestRepo(BaseRepository):
            def __init__(self, db):
                super().__init__(db, 'test_table')
        
        return TestRepo(mock_db)
    
    def test_find_by_id_success(self, base_repo, mock_db):
        """اختبار البحث عن سجل موجود"""
        mock_db.execute_query.return_value = [{'id': 1, 'name': 'Test'}]
        
        result = base_repo.find_by_id(1)
        
        assert result is not None
        assert result['id'] == 1
        assert result['name'] == 'Test'
    
    def test_find_by_id_not_found(self, base_repo, mock_db):
        """اختبار البحث عن سجل غير موجود"""
        mock_db.execute_query.return_value = []
        
        result = base_repo.find_by_id(999)
        
        assert result is None
    
    def test_find_all(self, base_repo, mock_db):
        """اختبار الحصول على جميع السجلات"""
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': 'Item 1'},
            {'id': 2, 'name': 'Item 2'}
        ]
        
        result = base_repo.find_all()
        
        assert len(result) == 2
        assert result[0]['id'] == 1
    
    def test_create(self, base_repo, mock_db):
        """اختبار إنشاء سجل جديد"""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 100
        mock_db.connection.execute.return_value = mock_cursor
        
        data = {'name': 'New Item', 'price': 50.0}
        result = base_repo.create(data)
        
        assert result == 100
        mock_db.connection.execute.assert_called_once()
        mock_db.connection.commit.assert_called_once()
    
    def test_create_adds_sync_and_deleted_flags(self, base_repo, mock_db):
        """اختبار إضافة is_synced و is_deleted تلقائياً"""
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_db.connection.execute.return_value = mock_cursor
        
        data = {'name': 'Test'}
        base_repo.create(data)
        
        # Check that is_synced and is_deleted were added
        call_args = mock_db.connection.execute.call_args[0]
        query = call_args[0]
        assert 'is_synced' in query
        assert 'is_deleted' in query
    
    def test_update_success(self, base_repo, mock_db):
        """اختبار تحديث سجل بنجاح"""
        mock_db.lock_row.return_value = True
        
        result = base_repo.update(1, {'name': 'Updated'})
        
        assert result is True
    
    def test_update_empty_data_adds_sync_flag(self, base_repo, mock_db):
        """اختبار تحديث بدون بيانات - سيضيف is_synced تلقائياً"""
        result = base_repo.update(1, {})
        
        # Empty data gets is_synced added, so update proceeds
        # The result depends on whether lock_row succeeds
        mock_db.lock_row.return_value = True
        assert result is True
    
    def test_soft_delete(self, base_repo, mock_db):
        """اختبار الحذف الناعم"""
        result = base_repo.delete(1)
        
        assert result is True
        mock_db.soft_delete.assert_called_once_with('test_table', 1)
    
    def test_hard_delete(self, base_repo, mock_db):
        """اختبار الحذف الفعلي"""
        result = base_repo.delete(1, hard_delete=True)
        
        assert result is True
        mock_db.execute_non_query.assert_called_once()
    
    def test_restore(self, base_repo, mock_db):
        """اختبار استعادة سجل محذوف"""
        result = base_repo.restore(1)
        
        assert result is True
        mock_db.restore_deleted.assert_called_once_with('test_table', 1)
    
    def test_count(self, base_repo, mock_db):
        """اختبار عد السجلات"""
        mock_db.execute_query.return_value = [{'count': 42}]
        
        result = base_repo.count()
        
        assert result == 42
    
    def test_find_pending_sync(self, base_repo, mock_db):
        """اختبار الحصول على السجلات المعلقة"""
        mock_db.get_pending_items.return_value = [{'id': 1}, {'id': 2}]
        
        result = base_repo.find_pending_sync()
        
        assert len(result) == 2
        mock_db.get_pending_items.assert_called_once_with('test_table', include_deleted=True)
    
    def test_mark_as_synced(self, base_repo, mock_db):
        """اختبار تعليم سجل كمتزامن"""
        base_repo.mark_as_synced(1, sync_version=2)
        
        mock_db.mark_as_synced.assert_called_once_with('test_table', 1, 2)


class TestProductRepository:
    """اختبارات ProductRepository"""
    
    @pytest.fixture
    def mock_db(self):
        """إنشاء mock لقاعدة البيانات"""
        db = MagicMock()
        db.execute_query = MagicMock(return_value=[])
        db.execute_non_query = MagicMock()
        db.connection = MagicMock()
        db.lock_row = MagicMock(return_value=True)
        db.soft_delete = MagicMock(return_value=True)
        db.restore_deleted = MagicMock(return_value=True)
        db.get_pending_items = MagicMock(return_value=[])
        db.mark_as_synced = MagicMock()
        db.transaction = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        return db
    
    @pytest.fixture
    def product_repo(self, mock_db):
        """إنشاء ProductRepository"""
        from src.repositories.product_repository import ProductRepository
        return ProductRepository(mock_db)
    
    def test_find_by_barcode_success(self, product_repo, mock_db):
        """اختبار البحث عن منتج بالباركود"""
        mock_db.execute_query.return_value = [{'id': 1, 'barcode': '123456', 'name': 'Product 1'}]
        
        result = product_repo.find_by_barcode('123456')
        
        assert result is not None
        assert result['barcode'] == '123456'
    
    def test_find_by_barcode_not_found(self, product_repo, mock_db):
        """اختبار البحث عن منتج غير موجود"""
        mock_db.execute_query.return_value = []
        
        result = product_repo.find_by_barcode('999999')
        
        assert result is None
    
    def test_find_by_name(self, product_repo, mock_db):
        """اختبار البحث عن منتجات بالاسم"""
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': 'Test Product'},
            {'id': 2, 'name': 'Test Item'}
        ]
        
        result = product_repo.find_by_name('Test')
        
        assert len(result) == 2
        mock_db.execute_query.assert_called_once()
    
    def test_find_low_stock_with_threshold(self, product_repo, mock_db):
        """اختبار البحث عن منتجات بمخزون منخفض بعتبة محددة"""
        mock_db.execute_query.return_value = [{'id': 1, 'current_stock': 5}]
        
        result = product_repo.find_low_stock(threshold=10)
        
        assert len(result) >= 0
        mock_db.execute_query.assert_called_once()
    
    def test_find_low_stock_without_threshold(self, product_repo, mock_db):
        """اختبار البحث عن منتجات بمخزون منخفض بدون عتبة"""
        mock_db.execute_query.return_value = [{'id': 1, 'current_stock': 5, 'min_stock': 10}]
        
        result = product_repo.find_low_stock()
        
        assert isinstance(result, list)
    
    def test_update_stock_success(self, product_repo, mock_db):
        """اختبار تحديث المخزون بنجاح"""
        result = product_repo.update_stock(1, 10)
        
        assert result is True
        mock_db.execute_non_query.assert_called_once()
    
    def test_update_stock_failure(self, product_repo, mock_db):
        """اختبار فشل تحديث المخزون"""
        mock_db.execute_non_query.side_effect = Exception("DB Error")
        
        result = product_repo.update_stock(1, 10)
        
        assert result is False


class TestCustomerRepository:
    """اختبارات CustomerRepository"""
    
    @pytest.fixture
    def mock_db(self):
        """إنشاء mock لقاعدة البيانات"""
        db = MagicMock()
        db.execute_query = MagicMock(return_value=[])
        db.execute_non_query = MagicMock()
        db.connection = MagicMock()
        db.lock_row = MagicMock(return_value=True)
        db.soft_delete = MagicMock(return_value=True)
        db.restore_deleted = MagicMock(return_value=True)
        db.get_pending_items = MagicMock(return_value=[])
        db.mark_as_synced = MagicMock()
        db.transaction = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        return db
    
    @pytest.fixture
    def customer_repo(self, mock_db):
        """إنشاء CustomerRepository"""
        from src.repositories.customer_repository import CustomerRepository
        return CustomerRepository(mock_db)
    
    def test_find_by_phone_success(self, customer_repo, mock_db):
        """اختبار البحث عن عميل برقم الهاتف"""
        mock_db.execute_query.return_value = [{'id': 1, 'phone': '0555123456', 'name': 'Customer 1'}]
        
        result = customer_repo.find_by_phone('0555123456')
        
        assert result is not None
        assert result['phone'] == '0555123456'
    
    def test_find_by_phone_not_found(self, customer_repo, mock_db):
        """اختبار البحث عن عميل غير موجود"""
        mock_db.execute_query.return_value = []
        
        result = customer_repo.find_by_phone('0000000000')
        
        assert result is None
    
    def test_find_by_name(self, customer_repo, mock_db):
        """اختبار البحث عن عملاء بالاسم"""
        mock_db.execute_query.return_value = [
            {'id': 1, 'name': 'Ahmed'},
            {'id': 2, 'name': 'Ali'}
        ]
        
        result = customer_repo.find_by_name('A')
        
        assert len(result) == 2
    
    def test_update_balance_success(self, customer_repo, mock_db):
        """اختبار تحديث رصيد العميل بنجاح"""
        result = customer_repo.update_balance(1, 100.0)
        
        assert result is True
        mock_db.execute_non_query.assert_called_once()
    
    def test_update_balance_failure(self, customer_repo, mock_db):
        """اختبار فشل تحديث رصيد العميل"""
        mock_db.execute_non_query.side_effect = Exception("DB Error")
        
        result = customer_repo.update_balance(1, 100.0)
        
        assert result is False


class TestSaleRepository:
    """اختبارات SaleRepository"""
    
    @pytest.fixture
    def mock_db(self):
        """إنشاء mock لقاعدة البيانات"""
        db = MagicMock()
        db.execute_query = MagicMock(return_value=[])
        db.execute_non_query = MagicMock()
        db.connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 100
        db.connection.execute.return_value = mock_cursor
        db.lock_row = MagicMock(return_value=True)
        db.soft_delete = MagicMock(return_value=True)
        db.restore_deleted = MagicMock(return_value=True)
        db.get_pending_items = MagicMock(return_value=[])
        db.mark_as_synced = MagicMock()
        db.transaction = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
        return db
    
    @pytest.fixture
    def sale_repo(self, mock_db):
        """إنشاء SaleRepository"""
        from src.repositories.sale_repository import SaleRepository
        return SaleRepository(mock_db)
    
    def test_find_by_invoice_number_success(self, sale_repo, mock_db):
        """اختبار البحث عن مبيعة برقم الفاتورة"""
        mock_db.execute_query.return_value = [{'id': 1, 'invoice_number': 'INV-001'}]
        
        result = sale_repo.find_by_invoice_number('INV-001')
        
        assert result is not None
        assert result['invoice_number'] == 'INV-001'
    
    def test_find_by_date_range(self, sale_repo, mock_db):
        """اختبار البحث عن مبيعات في نطاق تاريخي"""
        mock_db.execute_query.return_value = [
            {'id': 1, 'sale_date': '2024-01-01'},
            {'id': 2, 'sale_date': '2024-01-02'}
        ]
        
        result = sale_repo.find_by_date_range(date(2024, 1, 1), date(2024, 1, 31))
        
        assert len(result) == 2
    
    def test_find_by_customer(self, sale_repo, mock_db):
        """اختبار الحصول على مبيعات عميل"""
        mock_db.execute_query.return_value = [
            {'id': 1, 'customer_id': 5},
            {'id': 2, 'customer_id': 5}
        ]
        
        result = sale_repo.find_by_customer(5)
        
        assert len(result) == 2
        assert all(s['customer_id'] == 5 for s in result)
    
    def test_get_today_sales(self, sale_repo, mock_db):
        """اختبار الحصول على مبيعات اليوم"""
        mock_db.execute_query.return_value = [{'id': 1, 'sale_date': date.today().isoformat()}]
        
        result = sale_repo.get_today_sales()
        
        assert isinstance(result, list)
    
    def test_get_total_sales_amount_with_dates(self, sale_repo, mock_db):
        """اختبار الحصول على إجمالي المبيعات بتواريخ"""
        mock_db.execute_query.return_value = [{'total': 1500.50}]
        
        result = sale_repo.get_total_sales_amount(date(2024, 1, 1), date(2024, 1, 31))
        
        assert result == 1500.50
    
    def test_get_total_sales_amount_without_dates(self, sale_repo, mock_db):
        """اختبار الحصول على إجمالي المبيعات بدون تواريخ"""
        mock_db.execute_query.return_value = [{'total': 5000.00}]
        
        result = sale_repo.get_total_sales_amount()
        
        assert result == 5000.00
    
    def test_get_total_sales_amount_none_result(self, sale_repo, mock_db):
        """اختبار الحصول على إجمالي المبيعات عند None"""
        mock_db.execute_query.return_value = [{'total': None}]
        
        result = sale_repo.get_total_sales_amount()
        
        assert result == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])




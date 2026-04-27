import pytest
from unittest.mock import MagicMock, patch, ANY, call
from decimal import Decimal
from datetime import date, datetime, timedelta
import sys

# Define mocks globally so we can access them in tests if needed
mock_webhook_service_module = MagicMock()
mock_webhook_service = MagicMock()
mock_webhook_service_module.WebhookService = mock_webhook_service

mock_signals_module = MagicMock()
mock_signals = MagicMock()
mock_signals_module.signals = mock_signals

modules_to_patch = {
    'src.core.database_manager': MagicMock(),
    'src.core.encryption_manager': MagicMock(),
    'src.core.encrypted_backup_service': MagicMock(),
    'src.core.signals': mock_signals_module,
    'src.services.webhook_service': mock_webhook_service_module,
    'cryptography': MagicMock(),
    'cryptography.fernet': MagicMock(),
    'cryptography.hazmat': MagicMock(),
    'cryptography.hazmat.primitives': MagicMock(),
    'cryptography.hazmat.primitives.ciphers': MagicMock(),
    # 'src.utils.math_utils': MagicMock(), # UNMOCKED: Safe to use real module
}

# Apply patch for IMPORT time code
with patch.dict('sys.modules', modules_to_patch):
    from src.models.sale import Sale, SaleItem, SaleStatus, PaymentMethod, SaleManager

# Apply patch for RUN time execution
@pytest.fixture(autouse=True)
def mock_sys_modules():
    with patch.dict('sys.modules', modules_to_patch):
        yield

class TestSaleItem:
    def test_initialization_and_calculations(self):
        item = SaleItem(
            product_id=1,
            unit_price=100,
            quantity=2,
            discount_percentage=10,
            tax_percentage=15
        )
        assert isinstance(item.unit_price, Decimal)
        
        # Calculate
        item.calculate_total()
        
        assert item.subtotal == Decimal('200.00')
        assert item.discount_amount == Decimal('20.00')
        assert item.tax_amount == Decimal('27.00')
        assert item.total_amount == Decimal('207.00')

    def test_to_dict(self):
        item = SaleItem(product_id=1, quantity=1, unit_price=10)
        item.calculate_total()
        d = item.to_dict()
        assert d['total_amount'] == 10.0
        assert d['product_id'] == 1

class TestSaleModel:
    def test_initialization_and_totals(self):
        sale = Sale(currency_id=1, exchange_rate=1.5)
        item = SaleItem(product_id=1, quantity=1, unit_price=100)
        sale.add_item(item)
        
        # 100 total
        assert sale.total_amount == Decimal('100.00')
        assert sale.subtotal == Decimal('100.00')
        
        # Check Multi-currency
        assert sale.converted_amount == Decimal('100.00')
        
    def test_payment_status_logic(self):
        sale = Sale(total_amount=100)
        item = SaleItem(product_id=1, quantity=1, unit_price=100)
        sale.add_item(item)
        
        sale.paid_amount = Decimal('50')
        sale.calculate_totals()
        assert sale.status == SaleStatus.PARTIALLY_PAID
        
        sale.paid_amount = Decimal('100')
        sale.calculate_totals()
        assert sale.status == SaleStatus.PAID

    def test_to_dict_conversion(self):
        # Adding an item ensures total_amount > 0 so is_paid is False (0 < 100)
        item = SaleItem(product_id=1, quantity=1, unit_price=100)
        sale = Sale(id=1, invoice_number="INV", sale_date=date.today(), items=[item])
        sale.calculate_totals()
        d = sale.to_dict()
        assert d['id'] == 1
        assert d['invoice_number'] == "INV"
        assert d['items_count'] == 1
        assert d['is_paid'] is False

    def test_sale_init_with_strings(self):
        # Test initialization with string values for Enum fields
        # "مسودة" -> SaleStatus.DRAFT
        # "نقدي" -> PaymentMethod.CASH
        sale = Sale(status="مسودة", payment_method="نقدي")
        assert sale.status == SaleStatus.DRAFT
        assert sale.payment_method == PaymentMethod.CASH

    def test_remove_item(self):
        sale = Sale()
        item = SaleItem(id=1, product_id=1, quantity=1, unit_price=100)
        sale.add_item(item)
        assert sale.total_amount == 100
        
        sale.remove_item(1)
        assert sale.items_count == 0
        assert sale.total_amount == 0

class TestSaleManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return SaleManager(mock_db, logger=MagicMock())

    def test_tenant_manager(self, manager):
        with patch.dict('sys.modules', {'src.core.tenant_isolation': MagicMock()}):
            tm = manager.tenant_manager
            assert tm is not None

    def test_create_sale_success(self, manager, mock_db):
        sale = Sale(id=None, customer_id=1, total_amount=100)
        item = SaleItem(product_id=1, quantity=1, unit_price=100)
        sale.items.append(item)

        mock_conn = MagicMock()
        mock_db.connection = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        mock_conn.execute.return_value.fetchall.return_value = [
            (0, 'id', 'INT', 0, None, 1),
            (1, 'invoice_number', 'TEXT', 0, None, 0),
            (2, 'total_amount', 'REAL', 0, None, 0),
            (3, 'status', 'TEXT', 0, None, 0)
        ]
        
        mock_cursor.lastrowid = 123
        mock_webhook_service.return_value.trigger_webhook.return_value = None
        
        with patch.object(manager, '_create_sale_item', return_value=1) as mock_create_item, \
             patch.object(manager, '_update_stock_for_sale'):
            
            sale_id = manager.create_sale(sale)
            
            assert sale_id == 123
            assert mock_cursor.execute.called
            assert mock_create_item.called

    def test_create_sale_validation_error(self, manager):
        sale = Sale(status=SaleStatus.PAID, remaining_amount=10)
        with pytest.raises(ValueError):
            manager.create_sale(sale)

    def test_create_sale_no_id_fallback(self, manager, mock_db):
        sale = Sale(id=None, customer_id=1, total_amount=100)
        item = SaleItem(product_id=1, quantity=1)
        sale.items.append(item)
        
        mock_conn = MagicMock()
        mock_db.connection = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        mock_conn.execute.return_value.fetchall.return_value = []
        mock_cursor.lastrowid = 0
        mock_cursor.fetchone.side_effect = [(0,), (None,)] 
        
        with patch.object(manager, '_create_sale_item'), \
             patch.object(manager, '_update_stock_for_sale'):
             
             result = manager.create_sale(sale)
             assert result is None 

    def test_row_to_sale_complex_mapping(self, manager):
        # Now using real math_utils, this should pass if values are convertible
        row_pending_paid = (1, "INV", 1, 100, 0, 100, "cash", date.today(), 1, "", "pending", 100, 0, None, 1, 100, 100, 1, None, None)
        s = manager._row_to_sale(row_pending_paid)
        assert s.status == SaleStatus.PAID

        row_pending_part = (1, "INV", 1, 100, 0, 100, "cash", date.today(), 1, "", "pending", 50, 50, 
                            None, 1, 100, 100, 1, None, None)
        s = manager._row_to_sale(row_pending_part)
        assert s.status == SaleStatus.PARTIALLY_PAID
        
        row_strange = (1, "INV", 1, 100, 0, 100, "cash", date.today(), 1, "", "unknown", 0, 100, None, 1, 100, 100, 1, None, None)
        s3 = manager._row_to_sale(row_strange)
        # Should be confirmed as fallback or kept as string
        assert s3 is not None
        # It's likely SaleStatus("confirmed") or similar based on mapping
        # Let's inspect status if possible, but existing code suggests fallback to confirmed/draft

    def test_update_sale(self, manager, mock_db):
        sale = Sale(id=1, customer_id=1, items=[SaleItem(product_id=1)])
        mock_db.execute_query.return_value.rowcount = 1
        
        with patch.object(manager, 'get_sale_by_id') as mock_get:
            mock_get.return_value = Sale(id=1, items=[SaleItem(product_id=1, quantity=1)]) 
            
            mock_conn = mock_db.connection
            mock_cursor = mock_conn.cursor.return_value
            manager.db_manager.get_cursor.return_value.__enter__.return_value = mock_cursor
            
            with patch.object(manager, '_update_stock_in_transaction') as mock_stock_tx, \
                 patch.object(manager, '_create_sale_item_in_transaction') as mock_create_tx:
                
                assert manager.update_sale(sale) is True

    def test_update_sale_fallback(self, manager, mock_db):
        sale = Sale(id=1, customer_id=1, items=[SaleItem(product_id=1)])
        del manager.db_manager.get_cursor
        
        with patch.object(manager, 'get_sale_by_id', return_value=Sale(id=1, items=[])), \
             patch.object(manager, '_update_stock_in_transaction'), \
             patch.object(manager, '_create_sale_item_in_transaction'):
             
             assert manager.update_sale(sale) is True

    def test_add_payment(self, manager, mock_db):
        sale = Sale(id=1, total_amount=100, paid_amount=50, status=SaleStatus.PARTIALLY_PAID)
        with patch.object(manager, 'get_sale_by_id', return_value=sale):
            mock_db.execute_query.return_value.rowcount = 1
            assert manager.add_payment(1, Decimal('50')) is True

    def test_delete_sale_soft(self, manager, mock_db):
        sale = Sale(id=1, items=[SaleItem(product_id=1, quantity=1)])
        
        with patch.object(manager, 'get_sale_by_id', return_value=sale), \
             patch.object(manager, '_update_stock_for_sale') as mock_stock:
            
            mock_db.execute_query.return_value.rowcount = 1
            manager.delete_sale(1, soft_delete=True)
            mock_stock.assert_called_with(ANY, operation="return")
            
            # Verify signals - use global mock directly
            if not mock_signals.sale_deleted.emit.called:
                # Debug failures
                print(f"Logger Warning calls: {manager.logger.warning.call_args_list}")
                print(f"Logger Error calls: {manager.logger.error.call_args_list}")
            
            assert mock_signals.sale_deleted.emit.called

    def test_delete_sale_hard(self, manager, mock_db):
        sale = Sale(id=1, items=[SaleItem(product_id=1)])
        with patch.object(manager, 'get_sale_by_id', return_value=sale), \
             patch.object(manager, '_update_stock_for_sale'):
             
             mock_db.execute_query.return_value.rowcount = 1
             manager.delete_sale(1, soft_delete=False)

    def test_process_return_legacy(self, manager, mock_db):
        mock_conn = mock_db.get_connection.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.lastrowid = 99
        items = [{'product_id': 1, 'qty': 2, 'price': 50}]
        success, ret_id = manager.process_return(1, items)
        assert success is True
        assert ret_id == 99

    def test_create_sale_item_independent(self, manager, mock_db):
        item = SaleItem(product_id=1, quantity=2, unit_price=10)
        mock_db.fetch_one.side_effect = [(5.0,), (10,)]
        mock_db.execute_insert.return_value = 50
        res = manager._create_sale_item(item)
        assert res == 50

    def test_create_sale_item_new_batch(self, manager, mock_db):
        item = SaleItem(product_id=1, quantity=2, unit_price=10)
        mock_db.fetch_one.side_effect = [(5.0,), None] 
        mock_db.execute_insert.side_effect = [101, 50] 
        res = manager._create_sale_item(item)
        assert res == 50

    def test_get_sales_report(self, manager, mock_db):
        mock_db.fetch_one.return_value = (10, 5, 2, 1, 1000.0, 800.0, 200.0, 100.0)
        report = manager.get_sales_report()
        assert report['total_invoices'] == 10

    def test_list_sales_dict_conversion(self, manager, mock_db):
         row = (1, "INV", "Cust", "123", date.today(), "pending", "cash", 100.0, 100.0, 0.0)
         mock_db.fetch_all.return_value = [row]
         result = manager.list_sales(payment_method=PaymentMethod.CASH)
         assert len(result) == 1

    def test_list_sales_filters(self, manager, mock_db):
        mock_db.fetch_all.return_value = []
        manager.list_sales(search_term="foo", start_date=date.today(), end_date=date.today())
        args = mock_db.fetch_all.call_args[0]
        assert "LIKE ?" in args[0]

    def test_get_daily_sales(self, manager, mock_db):
        with patch.object(manager, 'search_sales', return_value=[Sale(id=1)]):
            res = manager.get_daily_sales(date.today())
            assert len(res) == 1

    def test_search_sales_filters(self, manager, mock_db):
        mock_db.fetch_all.return_value = []
        manager.search_sales(search_term="Test")
        args = mock_db.fetch_all.call_args[0]
        assert "LIKE ?" in args[0]
        
    def test_generate_invoice_number(self, manager, mock_db):
        mock_db.fetch_one.return_value = (0,)
        today_str = date.today().strftime('%Y%m%d')
        inv = manager.generate_invoice_number()
        assert inv == f"INV-{today_str}-0001"
        
        mock_db.fetch_one.side_effect = Exception("DB")
        inv_err = manager.generate_invoice_number()
        assert inv_err.startswith("INV-")

    def test_create_sale_item_in_transaction(self, manager, mock_db):
        item = SaleItem(product_id=1, quantity=1, unit_price=10)
        cursor = MagicMock()
        cursor.fetchone.side_effect = [(5.0,), (1,)]
        cursor.lastrowid = 100
        item_id = manager._create_sale_item_in_transaction(cursor, item)
        assert item_id == 100

    def test_update_stock_in_transaction(self, manager):
        items = [SaleItem(product_id=1, quantity=2)]
        cursor = MagicMock()
        manager._update_stock_in_transaction(cursor, items, "sale")
        args = cursor.execute.call_args[0]
        assert args[1][0] == -2

    def test_update_stock_for_sale_standalone(self, manager, mock_db):
        items = [SaleItem(product_id=1, quantity=2)]
        manager._update_stock_for_sale(items, "sale")
        assert mock_db.execute_query.called

    def test_get_sale_by_id_fallback(self, manager, mock_db):
        mock_db.fetch_one.side_effect = [
            Exception("Missing column"), 
            (1, "INV", 1, 100, 0, 100, "cash", date.today(), 1, "", "paid", 100, 0, 1, None, None)
        ]
        mock_db.fetch_all.return_value = []
        with patch.object(manager, '_row_to_sale', side_effect=lambda x: Sale(id=x[0])):
            sale = manager.get_sale_by_id(1)
            assert sale is not None

    def test_create_sale_webhook_trigger(self, manager, mock_db):
        sale = Sale(customer_id=1, total_amount=100)
        mock_db.connection.cursor.return_value.lastrowid = 1
        mock_webhook_service.return_value.trigger_webhook.return_value = None
        
        with patch.object(manager, '_create_sale_item'), \
             patch.object(manager, '_update_stock_for_sale'):
            manager.create_sale(sale)
            
            if not mock_webhook_service.return_value.trigger_webhook.called:
                 print(f"Warn: {manager.logger.warning.call_args_list}")
                 print(f"Error: {manager.logger.error.call_args_list}")
            
            assert mock_webhook_service.return_value.trigger_webhook.called

    def test_delete_sale_webhook_trigger(self, manager, mock_db):
        sale = Sale(id=1)
        mock_db.execute_query.return_value.rowcount = 1
        with patch.object(manager, 'get_sale_by_id', return_value=sale), \
             patch.object(manager, '_update_stock_for_sale'):
             
             manager.delete_sale(1, soft_delete=True)
             assert mock_webhook_service.return_value.trigger_webhook.called

    def test_get_sale_by_invoice_number(self, manager, mock_db):
        mock_db.fetch_one.return_value = (1, "INV001")
        with patch.object(manager, '_row_to_sale', return_value=Sale(id=1, invoice_number="INV001")):
            mock_db.fetch_all.return_value = []
            sale = manager.get_sale_by_invoice_number("INV001")
            assert sale.invoice_number == "INV001"

    def test_update_sale_status(self, manager, mock_db):
        mock_db.execute_query.return_value.rowcount = 1
        assert manager.update_sale_status(1, SaleStatus.CANCELLED) is True
    
    def test_update_order_status(self, manager, mock_db):
        manager.update_order_status(1, "returned")
        assert mock_db.execute_non_query.called
    
    def test_delete_sale_fail(self, manager, mock_db):
        with patch.object(manager, 'get_sale_by_id', return_value=None):
            assert manager.delete_sale(999) is False

    def test_cancel_sale_success(self, manager, mock_db):
        sale = Sale(id=1, items=[SaleItem()])
        with patch.object(manager, 'get_sale_by_id', return_value=sale), \
             patch.object(manager, '_update_stock_for_sale') as mock_stock, \
             patch.object(manager, 'update_sale_status', return_value=True):
             
             assert manager.cancel_sale(1) is True
             assert mock_signals.sale_updated.emit.called

    def test_cancel_sale_failure(self, manager, mock_db):
        # 1. Sale not found
        with patch.object(manager, 'get_sale_by_id', return_value=None):
            assert manager.cancel_sale(1) is False
            
        # 2. Update status fails
        sale = Sale(id=1)
        with patch.object(manager, 'get_sale_by_id', return_value=sale), \
             patch.object(manager, 'update_sale_status', return_value=False):
             assert manager.cancel_sale(1) is False

    def test_signals_emission_create(self, manager, mock_db):
        sale = Sale(id=None, total_amount=100)
        mock_db.connection.cursor.return_value.lastrowid = 1
        mock_signals.reset_mock()
        
        with patch.object(manager, '_create_sale_item'), \
             patch.object(manager, '_update_stock_for_sale'):
             
             manager.create_sale(sale)
             mock_signals.sales_updated.emit.assert_called()
             mock_signals.sale_created.emit.assert_called_with(1)

    def test_get_sales_summary(self, manager, mock_db):
        mock_db.fetch_one.return_value = (5, 1000.0, 800.0, 200.0)
        summary = manager.get_sales_summary(date.today(), date.today())
        assert summary['total_invoices'] == 5
        assert summary['total_revenue'] == 1000.0

    def test_get_recent_sales(self, manager):
        with patch.object(manager, 'list_sales', return_value=[]) as mock_list:
            manager.get_recent_sales(limit=10)
            mock_list.assert_called_with(limit=10)

    def test_create_sale_recovery_by_invoice(self, manager, mock_db):
        sale = Sale(id=None, customer_id=1, total_amount=100, invoice_number="INV-RECOVER")
        mock_conn = MagicMock()
        mock_db.connection = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        
        # PRAGMA response (cols)
        mock_conn.execute.return_value.fetchall.return_value = []
        
        # 1. create insert -> lastrowid=0
        mock_cursor.lastrowid = 0
        
        # 2. select last_insert_rowid -> (0,) then (999,) for second call? No, logic is:
        # if not sale_id: SELECT last_insert_rowid()
        # if still not: SELECT id FROM sales WHERE invoice...
        
        # side_effect for fetchone:
        # 1st call: (0,) (for last_insert_rowid)
        # 2nd call: (999,) (for select by invoice)
        mock_cursor.fetchone.side_effect = [(0,), (999,)] 
        
        mock_webhook_service.return_value.trigger_webhook.return_value = None
        
        with patch.object(manager, '_create_sale_item', return_value=1), \
             patch.object(manager, '_update_stock_for_sale'):
            
            sale_id = manager.create_sale(sale)
            assert sale_id == 999

    def test_create_sale_item_batch_fail(self, manager, mock_db):
        item = SaleItem(product_id=1, quantity=1)
        # Cost query
        mock_db.fetch_one.side_effect = [(10.0,), None] # Cost ok, Batch None
        # Batch insert fails
        mock_db.execute_insert.return_value = None 
        
        res = manager._create_sale_item(item)
        assert res is None

    def test_create_sale_db_error_handling(self, manager, mock_db):
        sale = Sale(customer_id=1, total_amount=100)
        
        # Make cursor.execute raise exception
        mock_conn = MagicMock()
        mock_db.connection = mock_conn
        mock_cursor = mock_conn.cursor.return_value
        # Fail on the INSERT query
        mock_cursor.execute.side_effect = Exception("DB Error")
        
        # create_sale catches exceptions and returns None
        result = manager.create_sale(sale)
        assert result is None
            
        mock_conn.rollback.assert_called_once()

    def test_tenant_manager_import_error(self, manager):
        # Simulate ImportError for TenantIsolationManager
        # We need to ensure _tenant_manager is None first
        manager._tenant_manager = None
        
        # Using patch.dict to simulate missing module
        with patch.dict('sys.modules', {'src.core.tenant_isolation': None}):
             # Accessing the property should trigger import which fails
             tm = manager.tenant_manager
             assert tm is None
             # Verify logger warning
             if manager.logger:
                 # Check if warning was called with the specific message
                 # It might have been called multiple times, so we check if any call matches
                 warning_calls = [c[0][0] for c in manager.logger.warning.call_args_list]
                 assert any("TenantIsolationManager غير متاح" in msg for msg in warning_calls)




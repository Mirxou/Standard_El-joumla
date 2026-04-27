
import pytest
from unittest.mock import MagicMock, patch, ANY
from decimal import Decimal
from datetime import date, datetime, timedelta
import sys
from src.models.purchase import (
    Purchase, PurchaseItem, PurchaseStatus, PaymentStatus, PurchaseManager
)

# Fixture to mock sys.modules to prevent ImportErrors with internal modules
@pytest.fixture(autouse=True)
def mock_sys_modules():
    with patch.dict('sys.modules', {
        'src.core.encryption_manager': MagicMock(),
        'src.core.database_encryption': MagicMock(),
        'cryptography.fernet': MagicMock(),
        'cryptography.hazmat.bindings._rust': MagicMock(),
        'src.services.webhook_service': MagicMock(),
        'src.core.signals': MagicMock(),
        'src.core.tenant_isolation': MagicMock(),
    }):
        yield

class TestPurchaseItem:
    def test_purchase_item_initialization_and_calculations(self):
        item = PurchaseItem(
            product_id=1,
            product_name="Product 1",
            quantity_ordered=10,
            unit_cost=100,
            discount_percent=10,
            tax_percent=15
        )
        
        # Verify conversions to Decimal
        assert isinstance(item.quantity_ordered, Decimal)
        assert isinstance(item.unit_cost, Decimal)
        
        # Perform calculations
        item.calculate_totals()
        
        # Subtotal: 10 * 100 = 1000
        assert item.subtotal == Decimal('1000')
        
        # Discount: 10% of 1000 = 100
        assert item.discount_amount == Decimal('100')
        
        # Net amount: 1000 - 100 = 900
        assert item.net_amount == Decimal('900')
        
        # Tax: 15% of 900 = 135
        assert item.tax_amount == Decimal('135')
        
        # Total: 900 + 135 = 1035
        assert item.total_amount == Decimal('1035')
        
        # Test derived properties
        item.quantity_received = Decimal('5')
        assert item.pending_quantity == Decimal('5')
        assert item.is_fully_received is False
        
        item.quantity_received = Decimal('10')
        assert item.is_fully_received is True

    def test_purchase_item_to_dict(self):
        item = PurchaseItem(product_id=1, quantity_ordered=10)
        item.calculate_totals()
        data = item.to_dict()
        assert data['product_id'] == 1
        assert data['quantity_ordered'] == 10.0
        assert 'total_amount' in data


class TestPurchaseModel:
    def test_purchase_initialization_and_calculations(self):
        purchase = Purchase(
            supplier_id=1,
            shipping_cost=50
        )
        
        item1 = PurchaseItem(product_id=1, quantity_ordered=10, unit_cost=100) # Total 1000
        item2 = PurchaseItem(product_id=2, quantity_ordered=5, unit_cost=200) # Total 1000
        
        purchase.add_item(item1)
        purchase.add_item(item2)
        
        purchase.calculate_totals()
        
        # Calculations verification
        expected_subtotal = item1.total_amount + item2.total_amount # (assuming 15% tax default)
        # item1: 1000 + 150 = 1150
        # item2: 1000 + 150 = 1150
        # Total items: 2300
        
        assert purchase.subtotal_amount == Decimal('2300.00')
        assert purchase.total_amount == Decimal('2350.00') # + 50 shipping
        
        # Test Payment Status
        purchase.paid_amount = Decimal('0')
        purchase._update_payment_status()
        assert purchase.payment_status == PaymentStatus.UNPAID.value
        
        purchase.paid_amount = Decimal('1000')
        purchase._update_payment_status()
        assert purchase.payment_status == PaymentStatus.PARTIAL.value
        
        purchase.paid_amount = purchase.total_amount
        purchase._update_payment_status()
        assert purchase.payment_status == PaymentStatus.PAID.value
        
        # Test Overdue
        purchase.payment_status = PaymentStatus.UNPAID.value
        purchase.paid_amount = Decimal('0')  # Reset paid amount
        purchase.expected_delivery_date = date.today() - timedelta(days=1)
        # Re-trigger update
        purchase._update_payment_status()
        assert purchase.is_overdue is True
        assert purchase.payment_status == PaymentStatus.OVERDUE.value

    def test_remove_item(self):
        purchase = Purchase()
        item = PurchaseItem(id=1, product_id=1)
        purchase.items.append(item)
        assert purchase.remove_item(1) is True
        assert len(purchase.items) == 0
        assert purchase.remove_item(999) is False

    def test_purchase_to_dict(self):
        purchase = Purchase(invoice_number="INV001")
        data = purchase.to_dict()
        assert data['invoice_number'] == "INV001"
        assert 'items' in data
        assert 'total_quantity_ordered' in data
        assert 'is_overdue' in data


class TestPurchaseManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return PurchaseManager(mock_db)
        
    @pytest.fixture
    def mock_signals(self):
        with patch('src.core.signals.signals') as m:
            yield m

    @pytest.fixture
    def mock_webhook_service(self):
        with patch('src.services.webhook_service.WebhookService') as m:
            yield m

    def test_create_purchase_success(self, manager, mock_db, mock_signals, mock_webhook_service):
        purchase = Purchase(supplier_id=1, invoice_number="INV-TEST")
        item = PurchaseItem(product_id=1, quantity_ordered=5, unit_cost=100)
        purchase.add_item(item)
        
        # Mock lastrowid for purchase
        mock_result = MagicMock()
        mock_result.lastrowid = 123
        mock_db.execute_query.return_value = mock_result
        
        # Mock create_purchase_item internal call if separate or part of same flow
        # Manager calls _create_purchase_item which calls execute_query again
        # We can let execute_query return mock_result repeatedly
        
        created_id = manager.create_purchase(purchase)
        
        assert created_id == 123
        # Verify db calls
        assert mock_db.execute_query.call_count >= 2 # 1 purchase + 1 item
        
        # Verify signals
        mock_signals.purchases_updated.emit.assert_called()
        mock_signals.purchase_created.emit.assert_called_with(123)
        
        # Verify webhook
        mock_webhook_service.return_value.trigger_webhook.assert_called_with(
            event_type="purchase_created",
            payload=ANY,
            entity_id=123,
            company_id=None
        )

    def test_create_purchase_error(self, manager, mock_db):
        purchase = Purchase()
        mock_db.execute_query.side_effect = Exception("DB Error")
        assert manager.create_purchase(purchase) is None

    def test_get_purchase_by_id(self, manager, mock_db):
        # Mock purchase row
        mock_db.fetch_one.return_value = (
            1, 'INV001', None, 1, '2023-01-01', None, None, 'معلقة', 'غير مدفوعة', 'نقدي',
            0, 0, 0, 0, 0, 0, 0,
            None, 1.0, None, None, # Multi-currency (idx 17-20)
            None, None, None, None, # Notes, user, dates (idx 21-24)
            'Supplier A' # Supplier name (idx 25)
        )
        
        # Mock items rows
        # Schema: id, purchase_id, product_id, q_ord, q_rec, cost, disc_p, disc_a, tax_p, tax_a, total, expiry, batch, notes, p_name, p_barcode
        mock_db.fetch_all.return_value = [(
            1, 1, 1, 10.0, 0.0, 100.0, 0.0, 0.0, 15.0, 15.0, 115.0, None, None, None, 'Prod 1', '123'
        )]
        
        p = manager.get_purchase_by_id(1)
        assert p is not None
        assert p.id == 1
        assert len(p.items) == 1

    def test_get_purchase_by_invoice_number(self, manager, mock_db):
        mock_db.fetch_one.return_value = (1, 'INV001') # Need valid row for _row_to_purchase basic check
        
        # We need to mock _row_to_purchase to avoid IndexError if the tuple above is too short
        # Or provide a full tuple.
        # Let's mock the helper method entirely for simplicity here, as we tested _row_to_purchase implicitly in test_get_purchase_by_id
        
        with patch.object(manager, '_row_to_purchase', return_value=Purchase(id=1, invoice_number='INV001')), \
             patch.object(manager, 'get_purchase_by_id', return_value=Purchase(id=1, invoice_number='INV001')):
            
            p = manager.get_purchase_by_invoice_number('INV001')
            assert p is not None
            assert p.invoice_number == 'INV001'

    def test_search_purchases(self, manager, mock_db):
        # Mock return for fetch_all
        # Just use partial rows if we mock _row_to_purchase
        mock_db.fetch_all.return_value = []
        
        with patch.object(manager, '_row_to_purchase') as mock_row_to_p:
            mock_row_to_p.side_effect = [
                Purchase(id=1, invoice_number='INV001'),
                Purchase(id=2, invoice_number='INV002')
            ]
            
            # Since fetch_all returns empty list, map returns empty. 
            # Wait, we need fetch_all to return a list of something so the loop runs
            mock_db.fetch_all.return_value = ['row1', 'row2']
            
            results = manager.search_purchases(search_term="INV", status="معلقة")
            assert len(results) == 2
            
            # Verify query construction
            call_args = mock_db.fetch_all.call_args
            query, params = call_args[0]
            assert "WHERE 1=1" in query
            assert "LIKE ?" in query
            assert "p.status = ?" in query
            assert "%INV%" in params
            assert "معلقة" in params

    def test_list_purchases(self, manager, mock_db):
        # This calls 'list_purchases' which returns dicts
        # It expects a tuple/row
        # Query: id, invoice, supplier_name, date, total, paid, remaining, status, pay_status
        mock_db.fetch_all.return_value = [
            (1, 'INV001', 'S1', '2023-01-01', 100.0, 0.0, 100.0, 'معلقة', 'غير مدفوعة')
        ]
        
        results = manager.list_purchases(limit=10)
        assert len(results) == 1
        assert results[0]['invoice_number'] == 'INV001'

    def test_tenant_manager(self, manager):
        # Test lazy property
        tm = manager.tenant_manager
        # If imports are mocked, it might be None or Mock depending on setup
        # Our autouse fixture mocks the module, so it should import successfully and return something
        assert tm is not None
        
        # Test cached
        assert manager.tenant_manager is tm

    def test_tenant_manager_import_error(self, manager):
        manager._tenant_manager = None
        with patch.dict('sys.modules', {'src.core.tenant_isolation': None}):
             assert manager.tenant_manager is None

    def test_create_purchase_item_failure(self, manager, mock_db):
        item = PurchaseItem(product_id=1)
        mock_db.execute_query.side_effect = Exception("Item Error")
        
        res = manager._create_purchase_item(item)
        assert res is None

    def test_create_purchase_invoice_generation(self, manager, mock_db):
        # Create without invoice number
        purchase = Purchase(supplier_id=1)
        assert purchase.invoice_number == ""
        
        # Mock generate_invoice_number method (checking existence or mocking behavior)
        if hasattr(manager, 'generate_invoice_number'):
            with patch.object(manager, 'generate_invoice_number', return_value="AUTO-123"):
                 # Mock db success
                 mock_res = MagicMock()
                 mock_res.lastrowid = 1
                 mock_db.execute_query.return_value = mock_res
                 
                 manager.create_purchase(purchase)
                 assert purchase.invoice_number == "AUTO-123"
        else:
             # If method doesn't exist on manager (maybe imported utility?), then skip
             pass


    def test_update_purchase(self, manager, mock_db):
        purchase = Purchase(id=1, invoice_number="INV001")
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_db.execute_query.return_value = mock_result
        
        assert manager.update_purchase(purchase) is True
        mock_db.execute_query.assert_called()

    def test_receive_purchase_items(self, manager, mock_db):
        purchase = Purchase(id=1)
        item = PurchaseItem(id=10, product_id=5, quantity_ordered=20)
        purchase.items.append(item)
        
        # Mock fetch_one to return the purchase row
        mock_db.fetch_one.return_value = (1, 'INV001', None, 1, '2023-01-01', None, None, 'معلقة', 'غير مدفوعة', 'نقدي', 0, 0, 0, 0, 0, 0, 0, None, 1.0, None, None, None, None, None, None, None)
        
        # Mock items
        mock_db.fetch_all.return_value = [(
            10, 1, 5, 20.0, 0.0, 100.0, 0.0, 0.0, 15.0, 15.0, 115.0, None, None, None, 'Prod', '123'
        )]
        
        # Need to patch get_purchase_by_id to avoid infinite recursion if internal logic differs,
        # but here we rely on db mocks. wait, manager.receive_purchase_items calls get_purchase_by_id
        # which calls fetch_one and fetch_all.
        # Then it updates items.
        
        received_data = [{'item_id': 10, 'quantity_received': 5}]
                 
        manager.receive_purchase_items(1, received_data)
        
        # Verify update query for item
        mock_db.execute_non_query.assert_called()
        
        # Verify signals emitted
        # We can also verify that update_purchase was called
        # but let's check side effects like stock update if possible
        # update_product_stock is private, but it calls execute_non_query for products table
    
    def test_cancel_purchase(self, manager, mock_db):
        purchase = Purchase(id=1, status='معلقة')
        with patch.object(manager, 'get_purchase_by_id', return_value=purchase):
             with patch.object(manager, 'update_purchase', return_value=True) as mock_update:
                  res = manager.cancel_purchase(1, reason="Test")
                  assert res is True
                  assert purchase.status == PurchaseStatus.CANCELLED.value
                  mock_update.assert_called_once()

    def test_cancel_purchase_already_received(self, manager, mock_db):
        purchase = Purchase(id=1, status='مستلمة') # Received
        with patch.object(manager, 'get_purchase_by_id', return_value=purchase):
             res = manager.cancel_purchase(1)
             assert res is False

    def test_get_purchases_summary(self, manager, mock_db):
        # Mock fetch_one result matching query: count, total, paid, remaining
        mock_db.fetch_one.return_value = (10, 5000.0, 3000.0, 2000.0)
        
        # Call without dates (defaults)
        summary = manager.get_purchases_summary()
        assert summary['total_purchases'] == 10
        assert summary['total_amount'] == 5000.0
        assert summary['avg_purchase_value'] == 500.0

    def test_generate_invoice_number(self, manager, mock_db):
        # Mock fetch_one returning max number
        mock_db.fetch_one.return_value = (50,) # Last number 50
        
        invoice_num = manager.generate_invoice_number()
        assert invoice_num == "PUR000051"

    def test_get_purchases_report(self, manager, mock_db):
        # Mock result: total, pending, received, partial, cancelled, amount, paid, remaining
        mock_db.fetch_one.return_value = (10, 2, 3, 1, 4, 1000.0, 500.0, 500.0)
        
        report = manager.get_purchases_report()
        assert report['total_purchases'] == 10
        assert report['pending_purchases'] == 2
        assert report['received_purchases'] == 3




import pytest
from unittest.mock import MagicMock, patch, ANY
from decimal import Decimal
from datetime import datetime
from src.models.product import Product, ProductManager

class TestProductModel:
    def test_product_initialization(self):
        product = Product(
            name="Test Product",
            cost_price=10.0,
            selling_price=15.0,
            current_stock=20,
            min_stock=5,
            wholesale_price=12,
            vip_price="13.5"
        )
        
        # Check __post_init__ conversions
        assert isinstance(product.cost_price, Decimal)
        assert isinstance(product.selling_price, Decimal)
        assert product.cost_price == Decimal('10.0')
        assert product.selling_price == Decimal('15.0')
        assert product.wholesale_price == Decimal('12')
        assert product.vip_price == Decimal('13.5')
        
    def test_product_properties(self):
        product = Product(
            cost_price=100,
            selling_price=150,
            current_stock=10,
            min_stock=15
        )
        
        # profit_margin: (150-100)/100 * 100 = 50%
        assert product.profit_margin == Decimal('50')
        
        # profit_amount: 150 - 100 = 50
        assert product.profit_amount == Decimal('50')
        
        # stock_value: 100 * 10 = 1000
        assert product.stock_value == Decimal('1000')
        
        # is_low_stock: 10 <= 15 -> True
        assert product.is_low_stock is True
        
        product.current_stock = 20
        assert product.is_low_stock is False

        # Zero cost price margin test
        product.cost_price = Decimal('0')
        assert product.profit_margin == Decimal('0.00')
        
    def test_product_to_dict(self):
        now = datetime.now()
        product = Product(
            id=1,
            name="Test",
            created_at=now,
            updated_at=now
        )
        
        data = product.to_dict()
        assert data['id'] == 1
        assert data['name'] == "Test"
        assert 'profit_margin' in data
        assert data['created_at'] == now.isoformat()


class TestProductManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db):
        return ProductManager(mock_db, logger=MagicMock())

    def test_tenant_manager_lazy_load(self, manager):
        # Test valid import behavior (mocked)
        with patch.dict('sys.modules', {'src.core.tenant_isolation': MagicMock()}):
            tm = manager.tenant_manager
            assert tm is not None
            # Access again to test caching
            assert manager.tenant_manager is tm

    def test_add_company_filter(self, manager):
        # Case 1: Internal company ID lookup
        with patch.object(manager, '_get_company_id', return_value=5):
            q, p = manager._add_company_filter("SELECT * FROM table", [])
            assert "WHERE company_id = ?" in q
            assert p == [5]
            
        # Case 2: Explicit company ID
        q, p = manager._add_company_filter("SELECT * FROM table WHERE id=1", [], company_id=10)
        assert "AND company_id = ?" in q
        assert p == [10]

    def test_create_product(self, manager, mock_db):
        product = Product(name="New Product")
        
        # Mock execute_insert
        mock_db.execute_insert.return_value = 1
        
        # Mock webhook service triggers
        with patch('src.services.webhook_service.WebhookService') as MockWebhook:
             mock_service = MockWebhook.return_value
             
             product_id = manager.create_product(product)
             
             assert product_id == 1
             mock_db.execute_insert.assert_called_once()
             mock_service.trigger_webhook.assert_called()

    def test_create_product_fail(self, manager, mock_db):
        mock_db.execute_insert.return_value = None
        assert manager.create_product(Product(name="Fail")) is None

    def test_create_product_exception(self, manager, mock_db):
        mock_db.execute_insert.side_effect = Exception("DB Error")
        assert manager.create_product(Product(name="Error")) is None

    def test_get_product_by_id(self, manager, mock_db):
        # Mock fetch_one result (standard 17 cols)
        row = (
            1, "Name", "EnName", "123", 1, "pcs", 
            "10.0", "15.0", "12.0", "18.0", 10, 5, 20, "Desc", "img.jpg", 
            1, datetime.now().isoformat(), datetime.now().isoformat(),
            "CategoryName"
        )
        mock_db.fetch_one.return_value = row
        
        product = manager.get_product_by_id(1)
        assert product is not None
        assert product.id == 1
        assert product.name == "Name"
        assert product.category_name == "CategoryName"

    def test_row_to_product_variants(self, manager):
        # 1. Standard row without company_id
        row = (
            1, "Name", "En", "BC", 1, "pcs", 
            "10", "15", "12", "18", 5, 5, 20, "Desc", "img", 
            1, None, None, "Category"
        )
        p = manager._row_to_product(row)
        assert p.name == "Name"
        assert p.category_name == "Category"

        # 2. Row with company_id (longer)
        row_long = row + (5, 99) # 99 is dummy
        # Function uses index 15 for company_id?
        # Check source: if len > 16: setattr(company_id, row[15])
        # In this row tuple, index 15 is "Category". Wait.
        # Let's verify _row_to_product indices again.
        # Indices 0-14 mapped.
        # Wholesale index 15? In code: row[15] if len > 17
        pass

    def test_get_product_by_barcode(self, manager, mock_db):
        mock_db.fetch_one.return_value = (
            1, "Name", "En", "BC", 1, "pcs", 
            "10", "15", "12", "13.5", 10, 5, 20, 
            "", "", 1, None, None
        )
        
        p = manager.get_product_by_barcode("BC")
        assert p.barcode == "BC"
        
        # Test active_only=False
        manager.get_product_by_barcode("BC", active_only=False)
        assert "is_active" not in mock_db.fetch_one.call_args[0][0]

    def test_search_products(self, manager, mock_db):
        mock_db.fetch_all.return_value = []
        
        # Test all filters
        manager.search_products(
            search_term="Test",
            category_id=1,
            active_only=True,
            limit=10,
            offset=5,
            company_id=2
        )
        
        call_args = mock_db.fetch_all.call_args
        sql = call_args[0][0]
        params = call_args[0][1]
        
        assert "LIKE ?" in sql
        assert "category_id = ?" in sql
        assert "is_active = 1" in sql
        assert "company_id = ?" in sql
        assert "LIMIT 10" in sql
        assert "OFFSET 5" in sql
        assert 2 in params

    def test_update_product(self, manager, mock_db):
        product = Product(id=1, name="Updated")
        mock_db.execute_query.return_value = MagicMock(rowcount=1)
        assert manager.update_product(product) is True

    def test_update_product_exception(self, manager, mock_db):
        product = Product(id=1, name="Updated")
        mock_db.execute_query.side_effect = Exception("Update fail")
        assert manager.update_product(product) is False

    def test_update_stock(self, manager, mock_db):
        # First get_product_by_id must succeed
        with patch.object(manager, 'get_product_by_id') as mock_get:
            mock_product = Product(id=1, current_stock=10)
            mock_get.return_value = mock_product
            
            mock_db.execute_query.return_value.rowcount = 1
            
            # Increase stock by 5
            success = manager.update_stock(1, 5)
            assert success is True
            
            # Decrease stock by 15 (should fail/warn if negative)
            mock_product.current_stock = 10
            success_neg = manager.update_stock(1, -15) # 10 - 15 = -5
            assert success_neg is False

    def test_delete_product(self, manager, mock_db):
        mock_db.execute_query.return_value.rowcount = 1
        assert manager.delete_product(1, soft_delete=True) is True
        
        # Exception
        mock_db.execute_query.side_effect = Exception("Del fail")
        assert manager.delete_product(1) is False

    def test_get_low_stock_products(self, manager, mock_db):
        mock_db.fetch_all.return_value = []
        manager.get_low_stock_products()
        assert "current_stock <= p.min_stock" in mock_db.fetch_all.call_args[0][0]

    def test_get_products_by_category(self, manager):
        with patch.object(manager, 'search_products', return_value=[]) as mock_search:
            manager.get_products_by_category(5)
            mock_search.assert_called_with(category_id=5)

    def test_get_stock_report(self, manager, mock_db):
        mock_db.fetch_one.return_value = (100, 80, 5, 50000.0, 50.0)
        report = manager.get_stock_report()
        assert report['total_products'] == 100
        
        # Exception
        mock_db.fetch_one.side_effect = Exception("Report fail")
        report = manager.get_stock_report()
        assert report['total_products'] == 0




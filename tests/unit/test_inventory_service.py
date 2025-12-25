import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.inventory_service import InventoryService
from src.models.product import Product

class TestInventoryService:
    
    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db_manager):
        # نحتاج لعمل mock للمدراء الذين يتم إنشاؤهم في __init__
        with patch('src.services.inventory_service.ProductManager') as MockProductManager, \
             patch('src.services.inventory_service.CategoryManager') as MockCategoryManager, \
             patch('src.services.inventory_service.SupplierManager') as MockSupplierManager:
            
            service = InventoryService(mock_db_manager)
            # ربط الـ mocks بالخدمة للتحقق منها لاحقاً
            service.product_manager = MockProductManager.return_value
            service.category_manager = MockCategoryManager.return_value
            service.supplier_manager = MockSupplierManager.return_value
            return service

    def test_add_product_success(self, service):
        """اختبار إضافة منتج بنجاح"""
        product = Product(name="Test Product", barcode="123456", current_stock=10)
        service.product_manager.get_product_by_barcode.return_value = None
        service.product_manager.create_product.return_value = 1
        
        # عزل _record_stock_movement لتجنب استدعاءات قاعدة البيانات
        with patch.object(service, '_record_stock_movement') as mock_record:
            result = service.add_product(product)
            
            assert result == 1
            service.product_manager.create_product.assert_called_once_with(product)
            mock_record.assert_called_once() # يجب تسجيل الرصيد الافتتاحي

    def test_add_product_duplicate_barcode(self, service):
        """اختبار منع إضافة منتج بباركود مكرر"""
        product = Product(name="Test Product", barcode="123456")
        service.product_manager.get_product_by_barcode.return_value = Product(id=2, barcode="123456")
        
        result = service.add_product(product)
        
        assert result is None
        service.product_manager.create_product.assert_not_called()

    def test_update_product_success(self, service):
        """اختبار تحديث منتج"""
        product = Product(id=1, name="Updated Product", current_stock=20)
        current_product = Product(id=1, name="Old Product", current_stock=10)
        
        service.product_manager.get_product_by_id.return_value = current_product
        service.product_manager.update_product.return_value = True
        
        with patch.object(service, '_record_stock_movement') as mock_record:
            result = service.update_product(product)
            
            assert result is True
            service.product_manager.update_product.assert_called_once_with(product)
            mock_record.assert_called_once() # المخزون تغير من 10 إلى 20

    def test_adjust_stock_manual(self, service):
        """اختبار التعديل اليدوي للمخزون"""
        product_id = 1
        new_quantity = 50
        current_product = Product(id=1, current_stock=40)
        
        service.product_manager.get_product_by_id.return_value = current_product
        service.product_manager.update_stock.return_value = True
        
        # تعطيل Multi-Warehouse لهذا الاختبار للتبسيط
        with patch.object(service, 'is_multi_warehouse_enabled', return_value=False):
            with patch.object(service, '_record_stock_movement') as mock_record:
                result = service.adjust_stock(product_id, new_quantity, reason="Audit")
                
                assert result is True
                service.product_manager.update_stock.assert_called_once_with(product_id, new_quantity)
                mock_record.assert_called_once()

    def test_transfer_stock_insufficient(self, service):
        """اختبار فشل النقل عند عدم توفر رصيد كافٍ"""
        from_id = 1
        to_id = 2
        qty = 15
        
        from_product = Product(id=1, current_stock=10) # الرصيد أقل من المطلوب
        to_product = Product(id=2, current_stock=0)
        
        service.product_manager.get_product_by_id.side_effect = [from_product, to_product]
        
        result = service.transfer_stock(from_id, to_id, qty)
        
        assert result is False
        service.product_manager.update_stock.assert_not_called()
    
    def test_delete_product(self, service):
        """اختبار حذف منتج"""
        product_id = 1
        service.product_manager.delete_product.return_value = True
        
        result = service.delete_product(product_id, hard_delete=False)
        
        assert result is True
        service.product_manager.delete_product.assert_called_once_with(product_id, False)
    
    def test_search_products(self, service):
        """اختبار البحث عن المنتجات"""
        query = "test"
        service.product_manager.search_products.return_value = [
            Product(id=1, name="Test Product")
        ]
        
        results = service.search_products(query)
        
        assert len(results) == 1
        service.product_manager.search_products.assert_called_once_with(query, None, None, True)
    
    def test_get_product_by_barcode(self, service):
        """اختبار الحصول على منتج بالباركود"""
        barcode = "123456"
        mock_product = Product(id=1, barcode=barcode)
        service.product_manager.get_product_by_barcode.return_value = mock_product
        
        product = service.get_product_by_barcode(barcode)
        
        assert product is not None
        assert product.barcode == barcode
        service.product_manager.get_product_by_barcode.assert_called_once_with(barcode)
    
    def test_add_category(self, service):
        """اختبار إضافة فئة"""
        from src.models.category import Category
        category = Category(name="Test Category")
        service.category_manager.create_category.return_value = 1
        
        category_id = service.add_category(category)
        
        assert category_id == 1
        service.category_manager.create_category.assert_called_once_with(category)
    
    def test_get_category_tree(self, service):
        """اختبار الحصول على شجرة الفئات"""
        mock_tree = [{"id": 1, "name": "Category 1", "children": []}]
        service.category_manager.get_category_tree.return_value = mock_tree
        
        tree = service.get_category_tree()
        
        assert tree == mock_tree
        service.category_manager.get_category_tree.assert_called_once()
    
    def test_get_stock_alerts(self, service):
        """اختبار الحصول على تنبيهات المخزون"""
        from src.services.inventory_service import StockAlert
        mock_alerts = [
            StockAlert(product_id=1, product_name="Low Stock", current_stock=5, min_stock=10, alert_type="low_stock")
        ]
        service.product_manager.get_low_stock_products.return_value = [
            Product(id=1, name="Low Stock", current_stock=5, min_stock=10)
        ]
        
        alerts = service.get_stock_alerts()
        
        assert len(alerts) > 0
        assert any(a.alert_type == "low_stock" for a in alerts)
    
    def test_generate_inventory_report(self, service):
        """اختبار إنشاء تقرير المخزون"""
        from src.services.inventory_service import InventoryReport
        service.product_manager.get_low_stock_products.return_value = []
        
        # Mock للاستعلامات
        service.db_manager.fetch_one.return_value = (10, 8, 2, 1000.0, 50.0)
        
        report = service.generate_inventory_report(include_movements=False)
        
        assert isinstance(report, InventoryReport)
        assert report.total_products >= 0
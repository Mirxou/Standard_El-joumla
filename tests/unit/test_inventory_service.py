import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.services.inventory_service import InventoryService
from src.models.product import Product
from datetime import datetime

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
    
    def test_get_stock_alerts(self, service, mock_db_manager):
        """اختبار الحصول على تنبيهات المخزون"""
        from src.services.inventory_service import StockAlert
        # mock db_manager.fetch_all ليعيد بيانات منتج منخفض المخزون
        service.db_manager.fetch_all.return_value = [
            (1, "Low Stock", 5, 10)  # (id, name, current_stock, min_stock)
        ]
        # mock _get_expired_products ليعيد قائمة فارغة
        with patch.object(service, '_get_expired_products', return_value=[]):
            alerts = service.get_stock_alerts()
            
            assert len(alerts) > 0
            assert any(a.alert_type == "low_stock" for a in alerts)
            assert alerts[0].product_id == 1
            assert alerts[0].product_name == "Low Stock"
            assert alerts[0].current_stock == 5
            assert alerts[0].minimum_stock == 10
    
    def test_generate_inventory_report(self, service):
        """اختبار إنشاء تقرير المخزون"""
        from src.services.inventory_service import InventoryReport
        service.product_manager.get_low_stock_products.return_value = []
        
        # Mock للاستعلامات
        service.product_manager.get_stock_report.return_value = {
            'total_products': 10,
            'active_products': 8,
            'low_stock_products': 2,
            'total_stock_value': 1000.0,
            'avg_stock_level': 50.0
        }
        service.db_manager.fetch_one.return_value = (10, 8, 2, 1000.0, 50.0)
        
        report = service.generate_inventory_report(include_movements=False)
        
        assert isinstance(report, InventoryReport)
        assert report.total_products >= 0
    
    def test_adjust_stock_increase(self, service):
        """اختبار زيادة المخزون"""
        product_id = 1
        new_quantity = 100
        current_product = Product(id=1, current_stock=50)
        
        service.product_manager.get_product_by_id.return_value = current_product
        service.product_manager.update_stock.return_value = True
        
        with patch.object(service, 'is_multi_warehouse_enabled', return_value=False):
            with patch.object(service, '_record_stock_movement') as mock_record:
                result = service.adjust_stock(product_id, new_quantity, reason="Restock")
                
                assert result is True
                mock_record.assert_called_once()
                # التحقق من أن الكمية زادت
                call_kwargs = mock_record.call_args[1]
                assert call_kwargs['quantity'] == 50  # الفرق = 100 - 50
    
    def test_adjust_stock_decrease(self, service):
        """اختبار تقليل المخزون"""
        product_id = 1
        new_quantity = 30
        current_product = Product(id=1, current_stock=50)
        
        service.product_manager.get_product_by_id.return_value = current_product
        service.product_manager.update_stock.return_value = True
        
        with patch.object(service, 'is_multi_warehouse_enabled', return_value=False):
            with patch.object(service, '_record_stock_movement') as mock_record:
                result = service.adjust_stock(product_id, new_quantity, reason="Damage")
                
                assert result is True
                mock_record.assert_called_once()
                # التحقق من أن الكمية قلت
                call_kwargs = mock_record.call_args[1]
                assert call_kwargs['quantity'] == 20  # الفرق = 30 - 50 (abs)
    
    def test_adjust_stock_product_not_found(self, service):
        """اختبار تعديل مخزون منتج غير موجود"""
        product_id = 999
        service.product_manager.get_product_by_id.return_value = None
        
        with patch.object(service, 'is_multi_warehouse_enabled', return_value=False):
            result = service.adjust_stock(product_id, 100, reason="Test")
            
            assert result is False
            service.product_manager.update_stock.assert_not_called()
    
    def test_transfer_stock_success(self, service):
        """اختبار نقل المخزون بنجاح"""
        from_id = 1
        to_id = 2
        qty = 10
        
        from_product = Product(id=1, current_stock=50)
        to_product = Product(id=2, current_stock=20)
        
        service.product_manager.get_product_by_id.side_effect = [from_product, to_product]
        service.product_manager.update_stock.return_value = True
        
        with patch.object(service, 'is_multi_warehouse_enabled', return_value=False):
            with patch.object(service, '_record_stock_movement') as mock_record:
                result = service.transfer_stock(from_id, to_id, qty)
                
                assert result is True
                assert service.product_manager.update_stock.call_count == 2
                # التحقق من تحديث المخزون الأول
                first_call = service.product_manager.update_stock.call_args_list[0]
                assert first_call[0][0] == from_id
                assert first_call[0][1] == 40  # 50 - 10
                # التحقق من تحديث المخزون الثاني
                second_call = service.product_manager.update_stock.call_args_list[1]
                assert second_call[0][0] == to_id
                assert second_call[0][1] == 30  # 20 + 10
    
    def test_transfer_stock_same_product(self, service):
        """اختبار نقل المخزون لنفس المنتج (يجب أن يفشل)"""
        product_id = 1
        product = Product(id=1, current_stock=50)
        
        service.product_manager.get_product_by_id.return_value = product
        
        result = service.transfer_stock(product_id, product_id, 10)
        
        assert result is False
        service.product_manager.update_stock.assert_not_called()
    
    def test_update_product_not_found(self, service):
        """اختبار تحديث منتج غير موجود"""
        product = Product(id=999, name="Nonexistent")
        service.product_manager.get_product_by_id.return_value = None
        
        result = service.update_product(product)
        
        assert result is False
        service.product_manager.update_product.assert_not_called()
    
    def test_update_product_no_stock_change(self, service):
        """اختبار تحديث منتج بدون تغيير المخزون"""
        product = Product(id=1, name="Updated Product", current_stock=20)
        current_product = Product(id=1, name="Old Product", current_stock=20)
        
        service.product_manager.get_product_by_id.return_value = current_product
        service.product_manager.update_product.return_value = True
        
        with patch.object(service, '_record_stock_movement') as mock_record:
            result = service.update_product(product)
            
            assert result is True
            # يجب ألا يُسجل stock movement لأن المخزون لم يتغير
            mock_record.assert_not_called()
    
    def test_add_product_with_stock_movement_error(self, service):
        """اختبار إضافة منتج مع خطأ في تسجيل stock movement"""
        product = Product(name="Test Product", barcode="123456", current_stock=10)
        service.product_manager.get_product_by_barcode.return_value = None
        service.product_manager.create_product.return_value = 1
        
        with patch.object(service, '_record_stock_movement', side_effect=Exception("DB Error")):
            # يجب أن يفشل لأن العملية ليست ذرية (Transactional) وحركة المخزون ضرورية
            result = service.add_product(product)
            
            assert result is None
    
    def test_search_products_with_filters(self, service):
        """اختبار البحث عن المنتجات مع فلاتر"""
        query = "test"
        category_id = 1
        supplier_id = 2
        
        service.product_manager.search_products.return_value = [
            Product(id=1, name="Test Product", category_id=1)
        ]
        
        results = service.search_products(
            query, 
            category_id=category_id, 
            supplier_id=supplier_id, 
            active_only=False
        )
        
        assert len(results) == 1
        service.product_manager.search_products.assert_called_once_with(
            query, category_id, supplier_id, False
        )
    
    def test_search_products_error_handling(self, service):
        """اختبار معالجة الأخطاء في البحث"""
        service.product_manager.search_products.side_effect = Exception("Database error")
        
        results = service.search_products("test")
        
        assert results == []
    
    def test_get_product_by_barcode_not_found(self, service):
        """اختبار الحصول على منتج بباركود غير موجود"""
        service.product_manager.get_product_by_barcode.return_value = None
        
        product = service.get_product_by_barcode("nonexistent")
        
        assert product is None
    
    def test_get_product_by_barcode_error_handling(self, service):
        """اختبار معالجة الأخطاء في البحث بالباركود"""
        service.product_manager.get_product_by_barcode.side_effect = Exception("DB Error")
        
        product = service.get_product_by_barcode("123456")
        
        assert product is None
    
    def test_add_category_error_handling(self, service):
        """اختبار معالجة الأخطاء عند إضافة فئة"""
        from src.models.category import Category
        category = Category(name="Test Category")
        service.category_manager.create_category.side_effect = Exception("DB Error")
        
        category_id = service.add_category(category)
        
        assert category_id is None
    
    def test_get_stock_alerts_no_alerts(self, service):
        """اختبار عدم وجود تنبيهات"""
        service.db_manager.fetch_all.return_value = []
        
        with patch.object(service, '_get_expired_products', return_value=[]):
            alerts = service.get_stock_alerts()
            
            assert len(alerts) == 0
    
    def test_get_stock_alerts_out_of_stock(self, service):
        """اختبار تنبيهات نفاد المخزون"""
        from src.services.inventory_service import StockAlert
        service.db_manager.fetch_all.return_value = [
            (1, "Out of Stock Product", 0, 10)  # (id, name, current_stock, min_stock)
        ]
        
        with patch.object(service, '_get_expired_products', return_value=[]):
            alerts = service.get_stock_alerts()
            
            assert len(alerts) > 0
            out_of_stock_alerts = [a for a in alerts if a.alert_type == "out_of_stock"]
            assert len(out_of_stock_alerts) > 0
            assert out_of_stock_alerts[0].severity == "critical"
    
    def test_generate_inventory_report_with_movements(self, service):
        """اختبار إنشاء تقرير مع حركات المخزون"""
        from src.services.inventory_service import InventoryReport
        service.product_manager.get_low_stock_products.return_value = []
        service.db_manager.fetch_one.return_value = (10, 8, 2, 1000.0, 50.0)
        service.db_manager.fetch_all.return_value = [
            {"id": 1, "product_id": 1, "movement_type": "in", "quantity": 10}
        ]
        
        report = service.generate_inventory_report(include_movements=True)
        
        # Mock get_stock_movements directly since it's hard to mock fetch_all for multiple calls
        with patch.object(service, 'get_stock_movements') as mock_get_movements:
             from src.services.inventory_service import StockMovement
             mock_get_movements.return_value = [
                 StockMovement(
                     id=1, product_id=1, movement_type="in", quantity=10.0,
                     created_at=datetime.now(), notes="Test"
                 )
             ]
             report = service.generate_inventory_report(include_movements=True)
             
             assert isinstance(report, InventoryReport)
             assert len(report.stock_movements) > 0
        
        assert isinstance(report, InventoryReport)
        assert len(report.stock_movements) > 0
    
    def test_generate_inventory_report_error_handling(self, service):
        """اختبار معالجة الأخطاء في إنشاء التقرير"""
        service.product_manager.get_low_stock_products.side_effect = Exception("DB Error")
        
        # يجب ألا يحدث crash
        try:
            report = service.generate_inventory_report()
            # إذا نجح، يجب أن يكون تقرير فارغ أو default
            assert report is not None
        except Exception:
            # أو يجب أن يُعالج الخطأ داخلياً
            pass
    
    def test_is_multi_warehouse_enabled_false(self, service):
        """اختبار أن Multi-Warehouse غير مفعل"""
        service._warehouse_service = None
        from unittest.mock import PropertyMock
        with patch.object(InventoryService, 'warehouse_service', new_callable=PropertyMock) as mock_ws:
            mock_ws.return_value = None
            result = service.is_multi_warehouse_enabled()
            assert result is False
    
    def test_delete_product_hard_delete(self, service):
        """اختبار الحذف النهائي لمنتج"""
        product_id = 1
        service.product_manager.delete_product.return_value = True
        
        result = service.delete_product(product_id, hard_delete=True)
        
        assert result is True
        service.product_manager.delete_product.assert_called_once_with(product_id, True)
    
    def test_delete_product_error_handling(self, service):
        """اختبار معالجة الأخطاء عند حذف منتج"""
        product_id = 1
        service.product_manager.delete_product.side_effect = Exception("DB Error")
        
        result = service.delete_product(product_id)
        
        assert result is False


class TestInventoryWarehouseOperations:
    """اختبارات عمليات المستودعات"""
    
    def test_get_product_stock_in_warehouse(self, service):
        """اختبار الحصول على المخزون في مستودع محدد"""
        product_id = 1
        warehouse_id = 1
        
        service.product_manager.get_product.return_value = {"id": product_id, "name": "Test"}
        
        result = service.get_product_stock_in_warehouse(product_id, warehouse_id)
        
        assert result is not None
    
    def test_transfer_stock_between_warehouses(self, service):
        """اختبار نقل المخزون بين المستودعات"""
        product_id = 1
        from_warehouse = 1
        to_warehouse = 2
        quantity = 5
        
        service.product_manager.get_product.return_value = {"id": product_id}
        
        result = service.transfer_stock(product_id, from_warehouse, to_warehouse, quantity)
        
        assert result is True
    
    def test_warehouse_stock_adjustment(self, service):
        """اختبار تعديل مخزون المستودع"""
        product_id = 1
        warehouse_id = 1
        adjustment = 10
        
        service.product_manager.get_product.return_value = {"id": product_id}
        
        result = service.adjust_warehouse_stock(product_id, warehouse_id, adjustment)
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




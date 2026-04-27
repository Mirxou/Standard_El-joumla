import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import sys
from pathlib import Path

import sys
import os
from pathlib import Path
# الوصول إلى جذر المشروع
project_root = str(Path(__file__).resolve().parents[2])
from src.models.warehouse import (
    Warehouse, WarehouseManager, 
    WarehouseInventory, WarehouseInventoryManager,
    WarehouseTransfer, WarehouseTransferManager
)

class TestWarehouseManager:
    """اختبارات وحدة لمدير المستودعات"""
    
    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db_manager):
        return WarehouseManager(mock_db_manager)

    def test_create_warehouse_success(self, manager, mock_db_manager):
        """اختبار إنشاء مستودع بنجاح"""
        warehouse = Warehouse(
            code="WH-001",
            name="Main Warehouse",
            is_active=True
        )
        
        # محاكاة عدم وجود الكود مسبقاً
        manager.get_warehouse_by_code = MagicMock(return_value=None)
        # محاكاة نجاح الإدراج
        mock_db_manager.execute_insert.return_value = 1
        
        result = manager.create_warehouse(warehouse)
        
        assert result == 1
        mock_db_manager.execute_insert.assert_called_once()

    def test_create_warehouse_duplicate_code(self, manager):
        """اختبار منع تكرار كود المستودع"""
        warehouse = Warehouse(code="WH-001", name="Duplicate")
        
        # محاكاة وجود الكود
        manager.get_warehouse_by_code = MagicMock(return_value=Warehouse(id=1, code="WH-001"))
        
        result = manager.create_warehouse(warehouse)
        
        assert result is None

    def test_get_warehouse_by_id(self, manager, mock_db_manager):
        """اختبار استرجاع مستودع"""
        mock_row = {
            'id': 1, 'code': 'WH-001', 'name': 'Main', 'is_active': 1, 
            'is_default': 0, 'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        mock_db_manager.execute_query.return_value = [mock_row]
        
        result = manager.get_warehouse_by_id(1)
        
        assert result is not None
        assert result.id == 1
        assert result.code == 'WH-001'

class TestWarehouseInventoryManager:
    """اختبارات وحدة لمدير مخزون المستودعات"""
    
    @pytest.fixture
    def mock_db_manager(self):
        return MagicMock()

    @pytest.fixture
    def manager(self, mock_db_manager):
        return WarehouseInventoryManager(mock_db_manager)

    def test_adjust_quantity_add(self, manager, mock_db_manager):
        """اختبار إضافة كمية للمخزون"""
        warehouse_id = 1
        product_id = 100
        qty_diff = 50.0
        
        # محاكاة وجود مخزون حالي
        current_inv = WarehouseInventory(
            warehouse_id=warehouse_id, 
            product_id=product_id, 
            quantity=10.0
        )
        manager.get_inventory = MagicMock(return_value=current_inv)
        
        result = manager.adjust_quantity(warehouse_id, product_id, qty_diff)
        
        assert result is True
        # التحقق من استدعاء التحديث بالكمية الجديدة (10 + 50 = 60)
        args, _ = mock_db_manager.execute_query.call_args
        assert "UPDATE warehouse_inventory" in args[0]
        assert args[1][0] == 60.0 # New quantity

    def test_adjust_quantity_subtract_insufficient(self, manager):
        """اختبار فشل الطرح إذا كانت الكمية غير كافية"""
        warehouse_id = 1
        product_id = 100
        qty_diff = -20.0
        
        current_inv = WarehouseInventory(
            warehouse_id=warehouse_id, 
            product_id=product_id, 
            quantity=10.0
        )
        manager.get_inventory = MagicMock(return_value=current_inv)
        
        result = manager.adjust_quantity(warehouse_id, product_id, qty_diff)
        
        assert result is False # 10 - 20 = -10 < 0

class TestWarehouseTransferManager:
    """اختبارات وحدة لمدير التحويلات"""
    
    @pytest.fixture
    def mock_db_manager(self):
        db = MagicMock()
        # إعداد context manager للـ cursor
        cursor = MagicMock()
        db.get_cursor.return_value.__enter__.return_value = cursor
        return db

    @pytest.fixture
    def manager(self, mock_db_manager):
        return WarehouseTransferManager(mock_db_manager)

    def test_create_transfer_insufficient_stock(self, manager):
        """اختبار منع التحويل عند عدم توفر رصيد"""
        transfer = WarehouseTransfer(
            from_warehouse_id=1,
            to_warehouse_id=2,
            product_id=100,
            quantity=50.0
        )
        
        # محاكاة رصيد غير كافٍ
        inv = WarehouseInventory(available_quantity=10.0)
        manager.inventory_manager.get_inventory = MagicMock(return_value=inv)
        
        result = manager.create_transfer(transfer)
        
        assert result is None

    def test_complete_transfer_transaction(self, manager, mock_db_manager):
        """اختبار إكمال التحويل كعملية واحدة (Transaction)"""
        transfer_id = 1
        transfer = WarehouseTransfer(
            id=transfer_id,
            from_warehouse_id=1,
            to_warehouse_id=2,
            product_id=100,
            quantity=10.0,
            status='pending'
        )
        
        manager.get_transfer_by_id = MagicMock(return_value=transfer)
        
        # محاكاة الـ cursor
        cursor = mock_db_manager.get_cursor.return_value.__enter__.return_value
        # محاكاة عدم وجود سجل في المستودع الهدف (ليقوم بـ INSERT)
        cursor.fetchone.return_value = None 
        
        result = manager.complete_transfer(transfer_id, received_by=1)
        
        assert result is True
        
        # التحقق من تسلسل العمليات في الـ cursor
        # 1. إلغاء الحجز
        # 2. خصم من المصدر
        # 3. إضافة للهدف
        # 4. تحديث حالة التحويل
        assert cursor.execute.call_count >= 4
        cursor.connection.commit.assert_called_once()





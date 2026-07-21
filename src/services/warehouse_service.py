#!/usr/bin/env python3
import logging
# -*- coding: utf-8 -*-
"""
خدمة إدارة المستودعات - Warehouse Service
إدارة المستودعات والمخزون متعدد المستودعات
"""

from typing import Any, Dict, List, Optional

from src.core.database_manager import DatabaseManager
from src.models.warehouse import (
    Warehouse,
    WarehouseInventory,
    WarehouseInventoryManager,
    WarehouseManager,
    WarehouseTransfer,
    WarehouseTransferManager,
)
from src.utils.logger import setup_logger


class WarehouseService:
    """خدمة إدارة المستودعات"""

    def __init__(self, db_manager: DatabaseManager, logger=None):
        self.db_manager = db_manager
        self.logger = logger or setup_logger(__name__)
        self.warehouse_manager = WarehouseManager(db_manager, logger)
        self.inventory_manager = WarehouseInventoryManager(db_manager, logger)
        self.transfer_manager = WarehouseTransferManager(db_manager, logger)

    # ===== إدارة المستودعات =====

    def create_warehouse(self, warehouse: Warehouse) -> Optional[int]:
        """إنشاء مستودع جديد"""
        return self.warehouse_manager.create_warehouse(warehouse)

    def get_warehouse(self, warehouse_id: int) -> Optional[Warehouse]:
        """الحصول على مستودع"""
        return self.warehouse_manager.get_warehouse_by_id(warehouse_id)

    def get_warehouse_by_code(self, code: str) -> Optional[Warehouse]:
        """الحصول على مستودع بالرمز"""
        return self.warehouse_manager.get_warehouse_by_code(code)

    def get_all_warehouses(self, include_inactive: bool = False) -> List[Warehouse]:
        """الحصول على جميع المستودعات"""
        return self.warehouse_manager.get_all_warehouses(include_inactive)

    def get_default_warehouse(self) -> Optional[Warehouse]:
        """الحصول على المستودع الافتراضي"""
        return self.warehouse_manager.get_default_warehouse()

    def update_warehouse(self, warehouse: Warehouse) -> bool:
        """تحديث مستودع"""
        return self.warehouse_manager.update_warehouse(warehouse)

    def delete_warehouse(self, warehouse_id: int) -> bool:
        """حذف مستودع"""
        return self.warehouse_manager.delete_warehouse(warehouse_id)

    # ===== إدارة المخزون =====

    def get_warehouse_inventory(self, warehouse_id: int) -> List[WarehouseInventory]:
        """الحصول على جميع المخزون في مستودع"""
        return self.inventory_manager.get_warehouse_inventory(warehouse_id)

    def get_product_inventory(self, product_id: int) -> List[WarehouseInventory]:
        """الحصول على مخزون منتج في جميع المستودعات"""
        return self.inventory_manager.get_product_inventory(product_id)

    def get_total_stock(self, product_id: int) -> float:
        """الحصول على إجمالي المخزون لمنتج في جميع المستودعات"""
        inventory_list = self.get_product_inventory(product_id)
        return sum(inv.quantity for inv in inventory_list)

    def get_available_stock(self, product_id: int) -> float:
        """الحصول على المخزون المتاح لمنتج في جميع المستودعات"""
        inventory_list = self.get_product_inventory(product_id)
        return sum(inv.available_quantity for inv in inventory_list)

    def adjust_stock(self, warehouse_id: int, product_id: int, quantity_diff: float) -> bool:
        """تعديل المخزون في مستودع معين"""
        return self.inventory_manager.adjust_quantity(warehouse_id, product_id, quantity_diff)

    def reserve_stock(self, warehouse_id: int, product_id: int, quantity: float) -> bool:
        """حجز كمية من المخزون"""
        return self.inventory_manager.reserve_quantity(warehouse_id, product_id, quantity)

    def release_stock(self, warehouse_id: int, product_id: int, quantity: float) -> bool:
        """إلغاء حجز كمية"""
        return self.inventory_manager.release_reserved(warehouse_id, product_id, quantity)

    # ===== نقل المخزون =====

    def create_transfer(self, transfer: WarehouseTransfer) -> Optional[int]:
        """إنشاء تحويل بين مستودعين"""
        return self.transfer_manager.create_transfer(transfer)

    def complete_transfer(self, transfer_id: int, received_by: Optional[int] = None) -> bool:
        """إكمال تحويل (استلام في المستودع الهدف)"""
        return self.transfer_manager.complete_transfer(transfer_id, received_by)

    def get_transfers(
        self, warehouse_id: Optional[int] = None, status: Optional[str] = None
    ) -> List[WarehouseTransfer]:
        """الحصول على قائمة التحويلات"""
        return self.transfer_manager.get_transfers(warehouse_id, status)

    def get_transfer(self, transfer_id: int) -> Optional[WarehouseTransfer]:
        """الحصول على تحويل"""
        return self.transfer_manager.get_transfer_by_id(transfer_id)

    # ===== التقارير =====

    def get_low_stock_items(self, warehouse_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """الحصول على المنتجات منخفضة المخزون"""
        try:
            query = """
                SELECT
                    w.id as warehouse_id,
                    w.code as warehouse_code,
                    w.name as warehouse_name,
                    wi.product_id,
                    p.name as product_name,
                    p.barcode,
                    wi.quantity,
                    wi.min_stock,
                    wi.reorder_point,
                    CASE
                        WHEN wi.quantity <= 0 THEN 'out_of_stock'
                        WHEN wi.quantity <= wi.min_stock THEN 'low_stock'
                        WHEN wi.quantity <= wi.reorder_point THEN 'reorder_needed'
                        ELSE 'ok'
                    END as stock_status
                FROM warehouse_inventory wi
                JOIN warehouses w ON wi.warehouse_id = w.id
                JOIN products p ON wi.product_id = p.id
                WHERE wi.quantity <= wi.reorder_point OR wi.quantity <= wi.min_stock
            """
            params = []

            if warehouse_id:
                query += " AND wi.warehouse_id = ?"
                params.append(warehouse_id)

            query += " ORDER BY w.name, p.name"

            return self.db_manager.execute_query(query, params)

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على المنتجات منخفضة المخزون: {str(e)}")
            return []

    def get_warehouse_summary(self, warehouse_id: int) -> Dict[str, Any]:
        """الحصول على ملخص المستودع"""
        try:
            warehouse = self.get_warehouse(warehouse_id)

            if not warehouse:
                return {}

            # حساب الإحصائيات باستخدام SQL (أسرع وأدق)
            query = """
                SELECT
                    COUNT(DISTINCT wi.product_id) as total_products,
                    SUM(wi.quantity * COALESCE(p.cost_price, 0)) as total_stock_value,
                    SUM(CASE WHEN wi.quantity <= 0 THEN 1 ELSE 0 END) as out_of_stock_count,
                    SUM(CASE WHEN wi.quantity > 0 AND wi.quantity <= wi.min_stock THEN 1 ELSE 0 END) as low_stock_count,
                    SUM(wi.quantity) as total_quantity,
                    SUM(wi.reserved_quantity) as total_reserved
                FROM warehouse_inventory wi
                LEFT JOIN products p ON wi.product_id = p.id
                WHERE wi.warehouse_id = ?
            """

            result = self.db_manager.execute_query(query, (warehouse_id,))

            if result and len(result) > 0:
                stats = result[0]
                return {
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.name,
                    "warehouse_code": warehouse.code,
                    "total_products": stats.get("total_products", 0) or 0,
                    "total_stock_value": float(stats.get("total_stock_value", 0.0) or 0.0),
                    "low_stock_count": stats.get("low_stock_count", 0) or 0,
                    "out_of_stock_count": stats.get("out_of_stock_count", 0) or 0,
                    "total_quantity": float(stats.get("total_quantity", 0.0) or 0.0),
                    "total_reserved": float(stats.get("total_reserved", 0.0) or 0.0),
                    "is_active": warehouse.is_active,
                    "is_default": warehouse.is_default,
                }
            else:
                return {
                    "warehouse_id": warehouse.id,
                    "warehouse_name": warehouse.name,
                    "warehouse_code": warehouse.code,
                    "total_products": 0,
                    "total_stock_value": 0.0,
                    "low_stock_count": 0,
                    "out_of_stock_count": 0,
                    "total_quantity": 0.0,
                    "total_reserved": 0.0,
                    "is_active": warehouse.is_active,
                    "is_default": warehouse.is_default,
                }

        except Exception as e:
            if self.logger:
                self.logger.error(f"خطأ في الحصول على ملخص المستودع {warehouse_id}: {str(e)}")
            return {}

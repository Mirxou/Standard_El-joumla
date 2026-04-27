#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product Repository
Repository للمنتجات
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
from src.core.local_database_manager import LocalDatabaseManager


class ProductRepository(BaseRepository):
    """Repository للمنتجات"""
    
    def __init__(self, db_manager: LocalDatabaseManager):
        super().__init__(db_manager, 'products')
    
    def find_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """
        البحث عن منتج بالباركود
        
        Args:
            barcode: الباركود
            
        Returns:
            المنتج أو None إذا لم يوجد
        """
        results = self.db.execute_query(
            "SELECT * FROM products WHERE barcode = ? AND is_deleted = 0",
            (barcode,)
        )
        return results[0] if results else None
    
    def find_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        البحث عن منتجات بالاسم
        
        Args:
            name: اسم المنتج (جزئي)
            limit: حد أقصى لعدد النتائج
            
        Returns:
            قائمة بالمنتجات
        """
        return self.db.execute_query(
            """
            SELECT * FROM products
            WHERE (name LIKE ? OR name_en LIKE ?) AND is_deleted = 0
            ORDER BY name
            LIMIT ?
            """,
            (f"%{name}%", f"%{name}%", limit)
        )
    
    def find_low_stock(self, threshold: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        الحصول على المنتجات ذات المخزون المنخفض
        
        Args:
            threshold: عتبة المخزون (اختياري - سيستخدم min_stock)
            
        Returns:
            قائمة بالمنتجات
        """
        if threshold is None:
            query = """
                SELECT * FROM products
                WHERE current_stock <= min_stock AND is_deleted = 0 AND is_active = 1
                ORDER BY current_stock ASC
            """
            return self.db.execute_query(query)
        else:
            query = """
                SELECT * FROM products
                WHERE current_stock <= ? AND is_deleted = 0 AND is_active = 1
                ORDER BY current_stock ASC
            """
            return self.db.execute_query(query, (threshold,))
    
    def update_stock(self, product_id: int, quantity: int) -> bool:
        """
        تحديث المخزون
        
        Args:
            product_id: معرف المنتج
            quantity: الكمية (موجب للإضافة، سالب للخصم)
            
        Returns:
            True إذا نجح التحديث
        """
        try:
            self.db.execute_non_query(
                """
                UPDATE products
                SET current_stock = current_stock + ?, is_synced = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_deleted = 0
                """,
                (quantity, product_id)
            )
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل تحديث المخزون: {str(e)}")
            return False

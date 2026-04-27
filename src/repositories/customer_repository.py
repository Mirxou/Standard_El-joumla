#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Customer Repository
Repository للعملاء
"""

from typing import Optional, List, Dict, Any
from .base_repository import BaseRepository
from src.core.local_database_manager import LocalDatabaseManager


class CustomerRepository(BaseRepository):
    """Repository للعملاء"""
    
    def __init__(self, db_manager: LocalDatabaseManager):
        super().__init__(db_manager, 'customers')
    
    def find_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        البحث عن عميل برقم الهاتف
        
        Args:
            phone: رقم الهاتف
            
        Returns:
            العميل أو None إذا لم يوجد
        """
        results = self.db.execute_query(
            "SELECT * FROM customers WHERE phone = ? AND is_deleted = 0",
            (phone,)
        )
        return results[0] if results else None
    
    def find_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        البحث عن عملاء بالاسم
        
        Args:
            name: اسم العميل (جزئي)
            limit: حد أقصى لعدد النتائج
            
        Returns:
            قائمة بالعملاء
        """
        return self.db.execute_query(
            """
            SELECT * FROM customers
            WHERE name LIKE ? AND is_deleted = 0
            ORDER BY name
            LIMIT ?
            """,
            (f"%{name}%", limit)
        )
    
    def update_balance(self, customer_id: int, amount: float) -> bool:
        """
        تحديث رصيد العميل
        
        Args:
            customer_id: معرف العميل
            amount: المبلغ (موجب للإضافة، سالب للخصم)
            
        Returns:
            True إذا نجح التحديث
        """
        try:
            self.db.execute_non_query(
                """
                UPDATE customers
                SET current_balance = current_balance + ?, is_synced = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_deleted = 0
                """,
                (amount, customer_id)
            )
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل تحديث رصيد العميل: {str(e)}")
            return False

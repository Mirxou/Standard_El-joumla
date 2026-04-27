#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sale Repository
Repository للمبيعات
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base_repository import BaseRepository
from src.core.local_database_manager import LocalDatabaseManager


class SaleRepository(BaseRepository):
    """Repository للمبيعات"""
    
    def __init__(self, db_manager: LocalDatabaseManager):
        super().__init__(db_manager, 'sales')
    
    def find_by_invoice_number(self, invoice_number: str) -> Optional[Dict[str, Any]]:
        """
        البحث عن مبيعة برقم الفاتورة
        
        Args:
            invoice_number: رقم الفاتورة
            
        Returns:
            المبيعة أو None إذا لم توجد
        """
        results = self.db.execute_query(
            "SELECT * FROM sales WHERE invoice_number = ? AND is_deleted = 0",
            (invoice_number,)
        )
        return results[0] if results else None
    
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """
        الحصول على المبيعات في نطاق تاريخي
        
        Args:
            start_date: تاريخ البداية
            end_date: تاريخ النهاية
            
        Returns:
            قائمة بالمبيعات
        """
        return self.db.execute_query(
            """
            SELECT * FROM sales
            WHERE sale_date BETWEEN ? AND ? AND is_deleted = 0
            ORDER BY sale_date DESC, id DESC
            """,
            (start_date.isoformat(), end_date.isoformat())
        )
    
    def find_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """
        الحصول على مبيعات عميل
        
        Args:
            customer_id: معرف العميل
            
        Returns:
            قائمة بالمبيعات
        """
        return self.db.execute_query(
            """
            SELECT * FROM sales
            WHERE customer_id = ? AND is_deleted = 0
            ORDER BY sale_date DESC, id DESC
            """,
            (customer_id,)
        )
    
    def get_today_sales(self) -> List[Dict[str, Any]]:
        """الحصول على مبيعات اليوم"""
        today = date.today().isoformat()
        return self.db.execute_query(
            """
            SELECT * FROM sales
            WHERE sale_date = ? AND is_deleted = 0
            ORDER BY id DESC
            """,
            (today,)
        )
    
    def get_total_sales_amount(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> float:
        """
        الحصول على إجمالي مبلغ المبيعات
        
        Args:
            start_date: تاريخ البداية (اختياري)
            end_date: تاريخ النهاية (اختياري)
            
        Returns:
            إجمالي المبلغ
        """
        if start_date and end_date:
            query = """
                SELECT SUM(final_amount) as total FROM sales
                WHERE sale_date BETWEEN ? AND ? AND is_deleted = 0
            """
            results = self.db.execute_query(query, (start_date.isoformat(), end_date.isoformat()))
        else:
            query = "SELECT SUM(final_amount) as total FROM sales WHERE is_deleted = 0"
            results = self.db.execute_query(query)
        
        return float(results[0]['total'] or 0) if results else 0.0
    
    def create_with_items(self, sale_data: Dict[str, Any], items: List[Dict[str, Any]]) -> int:
        """
        إنشاء مبيعة مع عناصرها
        
        Args:
            sale_data: بيانات المبيعة
            items: قائمة بعناصر المبيعة
            
        Returns:
            معرف المبيعة الجديدة
        """
        with self.db.transaction():
            # إنشاء المبيعة
            sale_id = self.create(sale_data)
            
            # إضافة العناصر
            from .sale_item_repository import SaleItemRepository
            item_repo = SaleItemRepository(self.db)
            for item in items:
                item['sale_id'] = sale_id
                item_repo.create(item)
            
            return sale_id

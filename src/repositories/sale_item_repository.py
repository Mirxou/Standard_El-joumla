#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sale Item Repository
Repository لعناصر المبيعات
"""

from typing import Any, Dict, List

from src.core.local_database_manager import LocalDatabaseManager

from .base_repository import BaseRepository


class SaleItemRepository(BaseRepository):
    """Repository لعناصر المبيعات"""

    def __init__(self, db_manager: LocalDatabaseManager):
        super().__init__(db_manager, "sale_items")

    def find_by_sale_id(self, sale_id: int) -> List[Dict[str, Any]]:
        """
        الحصول على عناصر مبيعة

        Args:
            sale_id: معرف المبيعة

        Returns:
            قائمة بعناصر المبيعة
        """
        return self.db.execute_query(
            """
            SELECT * FROM sale_items
            WHERE sale_id = ? AND is_deleted = 0
            ORDER BY id
            """,
            (sale_id,),
        )

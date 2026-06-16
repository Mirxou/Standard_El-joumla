import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delta Sync Service
خدمة المزامنة الجزئية - مزامنة فقط البيانات المتغيرة
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class DeltaSyncService:
    """خدمة المزامنة الجزئية (Delta Sync)"""

    def __init__(self, local_db: LocalDatabaseManager):
        self.local_db = local_db
        self.logger = setup_logger(__name__)

    def get_changed_items(
        self,
        table_name: str,
        since: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        الحصول على العناصر المتغيرة منذ تاريخ معين

        Args:
            table_name: اسم الجدول
            since: التاريخ (اختياري - سيستخدم last_synced_at)
            limit: حد أقصى لعدد العناصر
            offset: إزاحة

        Returns:
            قائمة بالعناصر المتغيرة
        """
        if since is None:
            since = self.local_db.get_last_synced_at()
            if since is None:
                # إذا لم تكن هناك مزامنة سابقة، إرجاع جميع العناصر
                since = datetime.fromtimestamp(0)

        query = """
            SELECT * FROM {table_name}
            WHERE (updated_at > ? OR created_at > ?) AND is_deleted = 0
            ORDER BY updated_at ASC, created_at ASC
            LIMIT ? OFFSET ?
        """

        since_str = since.isoformat()
        return self.local_db.execute_query(query, (since_str, since_str, limit, offset))

    def get_all_changed_items(
        self, since: Optional[datetime] = None, limit_per_table: int = 100
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        الحصول على جميع العناصر المتغيرة من جميع الجداول

        Args:
            since: التاريخ (اختياري)
            limit_per_table: حد أقصى لكل جدول

        Returns:
            قاموس بالجداول وعناصرها المتغيرة
        """
        tables = [
            "products",
            "customers",
            "sales",
            "sale_items",
            "batches",
            "categories",
            "suppliers",
        ]
        result = {}

        for table in tables:
            try:
                items = self.get_changed_items(table, since, limit=limit_per_table)
                if items:
                    result[table] = items
            except Exception as e:
                self.logger.error(f"❌ فشل الحصول على العناصر المتغيرة من {table}: {str(e)}")

        return result

    def get_pending_count(self, table_name: Optional[str] = None) -> int:
        """
        الحصول على عدد العناصر المعلقة (غير المتزامنة)

        Args:
            table_name: اسم الجدول (اختياري - للحصول على الإجمالي)

        Returns:
            عدد العناصر المعلقة
        """
        if table_name:
            query = """
                SELECT COUNT(*) as count FROM {table_name}
                WHERE is_synced = 0 AND is_deleted = 0
            """
            results = self.local_db.execute_query(query)
            return results[0]["count"] if results else 0
        else:
            # إجمالي من جميع الجداول
            tables = [
                "products",
                "customers",
                "sales",
                "sale_items",
                "batches",
                "categories",
                "suppliers",
            ]
            total = 0
            for table in tables:
                total += self.get_pending_count(table)
            return total

    def get_sync_summary(self) -> Dict[str, Any]:
        """
        الحصول على ملخص حالة المزامنة

        Returns:
            ملخص حالة المزامنة
        """
        last_synced = self.local_db.get_last_synced_at()
        pending_count = self.get_pending_count()

        # تفصيل حسب الجدول
        tables = [
            "products",
            "customers",
            "sales",
            "sale_items",
            "batches",
            "categories",
            "suppliers",
        ]
        table_counts = {}
        for table in tables:
            table_counts[table] = self.get_pending_count(table)

        return {
            "last_synced_at": last_synced.isoformat() if last_synced else None,
            "pending_count": pending_count,
            "table_counts": table_counts,
            "is_synced": pending_count == 0,
        }

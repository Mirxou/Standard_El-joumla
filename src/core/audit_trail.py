import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Trail Manager
نظام Audit Trail (التدقيق المالي) - يسجل كل التغييرات
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger


class AuditTrail:
    """نظام Audit Trail"""

    def __init__(self, local_db: LocalDatabaseManager):
        self.local_db = local_db
        self.logger = setup_logger(__name__)
        self._ensure_audit_table()

    def _ensure_audit_table(self):
        """التأكد من وجود جدول audit_logs"""
        self.local_db.execute_non_query("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                action TEXT NOT NULL,  -- 'create', 'update', 'delete'
                old_value TEXT,  -- JSON
                new_value TEXT,  -- JSON
                user_id INTEGER,
                device_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT
            )
        """)

        # إنشاء فهارس
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_audit_table_record ON audit_logs(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)",
        ]

        for index_sql in indexes:
            try:
                self.local_db.execute_non_query(index_sql)
            except Exception as e:
                self.logger.warning(f"فشل إنشاء الفهرس: {index_sql} - {str(e)}")

    def log(
        self,
        table_name: str,
        record_id: int,
        action: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        تسجيل عملية في Audit Trail

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            action: نوع العملية ('create', 'update', 'delete')
            old_value: القيمة القديمة (JSON)
            new_value: القيمة الجديدة (JSON)
            user_id: معرف المستخدم
            device_id: معرف الجهاز
            ip_address: عنوان IP
            user_agent: User Agent
        """
        try:
            old_value_json = json.dumps(old_value, default=str) if old_value else None
            new_value_json = json.dumps(new_value, default=str) if new_value else None

            self.local_db.execute_non_query(
                """
                INSERT INTO audit_logs (
                    table_name, record_id, action, old_value, new_value,
                    user_id, device_id, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    table_name,
                    record_id,
                    action,
                    old_value_json,
                    new_value_json,
                    user_id,
                    device_id,
                    ip_address,
                    user_agent,
                ),
            )

        except Exception as e:
            self.logger.error(f"❌ فشل تسجيل Audit Trail: {str(e)}")

    def get_audit_logs(
        self,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        الحصول على سجلات Audit Trail

        Args:
            table_name: اسم الجدول (اختياري)
            record_id: معرف السجل (اختياري)
            action: نوع العملية (اختياري)
            start_date: تاريخ البداية (اختياري)
            end_date: تاريخ النهاية (اختياري)
            limit: حد أقصى لعدد السجلات
            offset: إزاحة

        Returns:
            قائمة بسجلات Audit Trail
        """
        conditions = []
        params = []

        if table_name:
            conditions.append("table_name = ?")
            params.append(table_name)

        if record_id is not None:
            conditions.append("record_id = ?")
            params.append(record_id)

        if action:
            conditions.append("action = ?")
            params.append(action)

        if start_date:
            conditions.append("timestamp >= ?")
            params.append(start_date.isoformat())

        if end_date:
            conditions.append("timestamp <= ?")
            params.append(end_date.isoformat())

        where_clause = " AND ".join(conditions) if conditions else "1=1"  # noqa: F841

        query = """
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])

        return self.local_db.execute_query(query, tuple(params))

    def get_record_history(self, table_name: str, record_id: int) -> List[Dict[str, Any]]:
        """
        الحصول على تاريخ سجل معين

        Args:
            table_name: اسم الجدول
            record_id: معرف السجل

        Returns:
            قائمة بجميع التغييرات على السجل
        """
        return self.get_audit_logs(table_name=table_name, record_id=record_id, limit=1000)

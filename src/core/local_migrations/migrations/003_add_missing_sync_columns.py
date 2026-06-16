import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 003: إضافة أعمدة المزامنة والحذف المنطقي للجداول المتبقية
"""


def upgrade(db):
    """تطبيق التعديلات"""
    tables = ["reminders", "security_settings", "users", "audit_log"]

    for table in tables:
        # التحقق من وجود الأعمدة
        try:
            res = db.execute_query(f"PRAGMA table_info({table})")
            if not res:
                # print(f"Table {table} not found, skipping.")
                continue

            columns = [row["name"] for row in res]

            if "is_synced" not in columns:
                db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN is_synced INTEGER DEFAULT 0")

            if "is_deleted" not in columns:
                db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN is_deleted INTEGER DEFAULT 0")

            if "last_synced_at" not in columns:
                db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN last_synced_at TIMESTAMP")

            if "sync_version" not in columns:
                db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN sync_version INTEGER DEFAULT 1")

        except Exception as e:  # noqa: F841
            # print(f"Error updating table {table}: {e}")
            logging.getLogger(__name__).warning("Ignored exception in 003_add_missing_sync_columns.py")


def rollback(db):
    """إلغاء التعديلات (لا ينصح به في SQLite للأعمدة)"""

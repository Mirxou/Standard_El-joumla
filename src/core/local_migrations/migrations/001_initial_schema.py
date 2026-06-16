import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 001: Initial Schema
الـ Migration الأولي - إنشاء الجداول الأساسية
"""

description = "إنشاء الجداول الأساسية للقاعدة المحلية"


def upgrade(db):
    """
    تطبيق Migration

    Args:
        db: LocalDatabaseManager
    """
    # هذا Migration يتم تطبيقه تلقائياً عند إنشاء الجداول
    # في LocalDatabaseManager._create_tables()
    # لذلك لا حاجة لتنفيذ أي شيء هنا


def downgrade(db):
    """
    إلغاء Migration (اختياري)

    Args:
        db: LocalDatabaseManager
    """
    # حذف الجداول (غير مستحسن في Production)
    tables = [
        "sync_queue",
        "sync_status",
        "products",
        "customers",
        "sales",
        "sale_items",
        "batches",
        "categories",
        "suppliers",
    ]
    for table in tables:
        try:
            db.execute_non_query(f"DROP TABLE IF EXISTS {table}")
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in 001_initial_schema.py")

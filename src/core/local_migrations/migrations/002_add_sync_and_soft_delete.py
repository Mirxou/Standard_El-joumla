#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 002: Add Sync and Soft Delete Columns
إضافة أعمدة المزامنة والحذف المنطقي للجداول القائمة
"""

description = "إضافة أعمدة المزامنة والحذف المنطقي للجداول القائمة"


def upgrade(db):
    """
    تطبيق Migration
    """
    tables = [
        "products",
        "customers",
        "sales",
        "sale_items",
        "batches",
        "categories",
        "suppliers",
        "purchases",
        "purchase_items",
        "stock_movements",
        "reminders",
        "security_settings",
    ]

    for table in tables:
        # التحقق من وجود الجدول
        try:
            res = db.execute_query(f"PRAGMA table_info({table})")
            if not res:
                db.logger.info(f"الجدول {table} غير موجود، سيتم تخطيه")
                continue

            columns = [row["name"] for row in res]

            # الأعمدة المطلوب إضافتها
            needed_columns = [
                ("is_synced", "INTEGER DEFAULT 0"),
                ("last_synced_at", "TIMESTAMP"),
                ("sync_version", "INTEGER DEFAULT 1"),
                ("is_deleted", "INTEGER DEFAULT 0"),
                ("deleted_at", "TIMESTAMP"),
            ]

            for col_name, col_type in needed_columns:
                if col_name not in columns:
                    try:
                        db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                        db.logger.info(f"✅ تم إضافة العمود {col_name} إلى جدول {table}")
                    except Exception as e:
                        db.logger.error(f"❌ فشل إضافة {col_name} إلى {table}: {e}")

        except Exception as e:
            db.logger.error(f"❌ خطأ أثناء التحقق من الجدول {table}: {e}")

    # SQLite لا يدعم حذف الأعمدة بسهولة (DROP COLUMN غير متوفر في الإصدارات القديمة)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 008: Add Auto Conversion Columns to Products
إضافة parent_product_id و conversion_factor لجدول المنتجات
"""


def upgrade(db):
    """تطبيق Migration"""
    cursor = db.execute("PRAGMA table_info(products)")
    columns = [row[1] for row in cursor.fetchall()]

    if "parent_product_id" not in columns:
        db.execute_non_query("ALTER TABLE products ADD COLUMN parent_product_id INTEGER DEFAULT NULL")
    if "conversion_factor" not in columns:
        db.execute_non_query("ALTER TABLE products ADD COLUMN conversion_factor INTEGER DEFAULT 1")


def downgrade(db):
    """إلغاء Migration"""
    pass

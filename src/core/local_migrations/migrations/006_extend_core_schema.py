#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 006: Extend Core Schema
إضافة الأعمدة المتقدمة للمنتجات والموردين والمستودعات
"""


def upgrade(db):
    """تطبيق Migration"""

    # تحديثات المنتجات
    products_needed = [
        ("wholesale_price", "REAL DEFAULT 0.0"),
        ("vip_price", "REAL DEFAULT 0.0"),
        ("min_wholesale_qty", "INTEGER DEFAULT 10"),
        ("tax_rate", "REAL DEFAULT 0.0"),
        ("is_perishable", "BOOLEAN DEFAULT 0"),
        ("expiry_date", "DATE"),
        ("batch_number", "TEXT"),
        ("image_path", "TEXT"),
        ("production_date", "DATE"),
        ("abc_classification", "TEXT"),
        ("ai_forecast_demand", "REAL"),
        ("last_analysis_date", "DATETIME"),
    ]

    # تحديثات الموردين
    suppliers_needed = [
        ("name_en", "TEXT"),
        ("website", "TEXT"),
        ("city", "TEXT"),
        ("country", "TEXT DEFAULT 'الجزائر'"),
        ("commercial_register", "TEXT"),
        ("payment_terms", "TEXT DEFAULT 'نقدي'"),
        ("credit_limit", "REAL DEFAULT 0.0"),
        ("current_balance", "REAL DEFAULT 0.0"),
    ]

    # تحديثات المستودعات
    warehouses_needed = [
        ("name_en", "TEXT"),
        ("warehouse_type", "TEXT DEFAULT 'main'"),
        ("capacity", "REAL DEFAULT 0.0"),
        ("current_utilization", "REAL DEFAULT 0.0"),
        ("allow_negative_stock", "BOOLEAN DEFAULT 0"),
    ]

    updates = {
        "products": products_needed,
        "suppliers": suppliers_needed,
        "warehouses": warehouses_needed,
    }

    for table, needed in updates.items():
        # التحقق من وجود الجدول
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cursor.fetchone():
            continue

        # التحقق من الأعمدة
        cursor = db.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        for col_name, col_type in needed:
            if col_name not in columns:
                try:
                    db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"Error adding {col_name} to {table}: {e}")


def downgrade(db):
    """إلغاء Migration"""

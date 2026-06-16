#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 005: Fix Sales and Purchases Schema
إضافة أعمدة المبالغ المدفوعة والمتبقية والحالة لجداول المبيعات والمشتريات
"""


def upgrade(db):
    """تطبيق Migration"""
    tables = ["sales", "purchases"]

    for table in tables:
        # التحقق من الأعمدة الموجودة
        cursor = db.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]

        # الأعمدة المطلوب إضافتها
        needed = [
            ("status", 'TEXT DEFAULT "confirmed"'),
            ("paid_amount", "DECIMAL(10,2) DEFAULT 0"),
            ("remaining_amount", "DECIMAL(10,2) DEFAULT 0"),
            ("due_date", "DATE"),
        ]

        for col_name, col_type in needed:
            if col_name not in columns:
                try:
                    db.execute_non_query(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                except Exception as e:
                    print(f"Error adding {col_name} to {table}: {e}")


def downgrade(db):
    """إلغاء Migration"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 009: Add hardware_config table (GAP-2.2)
إضافة جدول إعدادات الأجهزة (الفجوة 2.2 — طابعة الإيصالات ودرج النقدية)

Creates the hardware_config table used by ESC/POS printer and cash drawer
services to persist per-device connection settings, plus an index on
device_type for fast default-device lookups.

ينشئ جدول hardware_config المستخدم من خدمات طابعة ESC/POS ودرج النقدية
لتخزين إعدادات الاتصال لكل جهاز، مع فهرس على device_type لتسريع البحث.

Idempotent: safe to apply multiple times (CREATE TABLE IF NOT EXISTS +
per-column existence checks, same pattern as migration 008).
آمن للتطبيق المتكرر (IF NOT EXISTS + فحص وجود كل عمود، بنفس نمط 008).
"""


def upgrade(db):
    """تطبيق Migration — إنشاء جدول إعدادات الأجهزة والفهرس"""
    db.execute_non_query("""
        CREATE TABLE IF NOT EXISTS hardware_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type VARCHAR(50) NOT NULL,      -- 'receipt_printer' | 'cash_drawer' | 'scanner' | 'label_printer' | 'customer_display'
            connection_type VARCHAR(20) NOT NULL,  -- 'usb' | 'serial' | 'network' | 'bluetooth' | 'file'
            connection_params TEXT,                -- JSON: {"port": "COM3", "baud_rate": 9600} / {"ip": "192.168.1.100", "port": 9100} / {"file": "/tmp/printer.out"}
            device_name VARCHAR(100),
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # فهرس لتسريع البحث عن الجهاز الافتراضي حسب النوع
    db.execute_non_query(
        "CREATE INDEX IF NOT EXISTS idx_hardware_config_device_type "
        "ON hardware_config(device_type)"
    )

    # نمط 008: فحص وجود الأعمدة على قواعد بيانات قديمة جزئية، وإضافتها إن نقصت
    cursor = db.execute("PRAGMA table_info(hardware_config)")
    columns = [row[1] for row in cursor.fetchall()]

    if "connection_params" not in columns:
        db.execute_non_query("ALTER TABLE hardware_config ADD COLUMN connection_params TEXT")
    if "device_name" not in columns:
        db.execute_non_query("ALTER TABLE hardware_config ADD COLUMN device_name VARCHAR(100)")
    if "is_default" not in columns:
        db.execute_non_query("ALTER TABLE hardware_config ADD COLUMN is_default INTEGER DEFAULT 0")
    if "is_active" not in columns:
        db.execute_non_query("ALTER TABLE hardware_config ADD COLUMN is_active INTEGER DEFAULT 1")
    # created_at: لا يمكن إضافته بـ ALTER في SQLite (default غير ثابت) — يُنشأ مع الجدول


def downgrade(db):
    """إلغاء Migration — حذف الجدول والفهرس"""
    db.execute_non_query("DROP INDEX IF EXISTS idx_hardware_config_device_type")
    db.execute_non_query("DROP TABLE IF EXISTS hardware_config")

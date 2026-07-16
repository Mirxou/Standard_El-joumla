#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration 004: Add MFA Column
إضافة عمود otp_secret لجدول المستخدمين
"""


def upgrade(db):
    """تطبيق Migration"""
    # التحقق من وجود العمود أولاً لتجنب الأخطاء
    cursor = db.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    if "otp_secret" not in columns:
        db.execute_non_query("ALTER TABLE users ADD COLUMN otp_secret TEXT")


def downgrade(db):
    """إلغاء Migration"""
    # SQLite لا يدعم DROP COLUMN بسهولة (يتطلب إعادة إنشاء الجدول)
    # سنترك العمود كما هو لتجنب تعقيدات فقدان البيانات

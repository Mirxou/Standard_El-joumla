#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار منطق حجب محاولات الدخول المتكررة (Brute force protection)"""
import pytest
from datetime import datetime
from src.core.database_manager import DatabaseManager
from src.services.security_service import SecurityService

@pytest.fixture
def security(tmp_path):
    db_path = tmp_path / 'bf.db'
    dm = DatabaseManager(str(db_path))
    dm.initialize()
    # إنشاء جدول login_attempts إذا لم يكن موجوداً (قد يكون منشأ مسبقاً في الهجرات)
    dm.execute_query("""
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            ip TEXT,
            user_agent TEXT,
            success INTEGER,
            created_at TEXT
        )
    """)
    return SecurityService(dm)

def test_bruteforce_blocking(security):
    username = 'testuser'
    # إضافة 5 محاولات فاشلة داخل النافذة الزمنية
    for _ in range(5):
        security.record_login_attempt(username, success=False, ip='1.1.1.1')
    assert security.is_blocked(username, ip='1.1.1.1', window_minutes=15, max_failures=5) is True

def test_bruteforce_not_blocked_after_success(security):
    username = 'alloweduser'
    # أربع محاولات فاشلة ثم ناجحة
    for _ in range(4):
        security.record_login_attempt(username, success=False)
    security.record_login_attempt(username, success=True)
    assert security.is_blocked(username, window_minutes=15, max_failures=5) is False

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إصلاح جدول role_permissions"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = LocalDatabaseManager(config.get_database_path())
db.initialize()

print("=== إعادة إنشاء جدول role_permissions ===")

# حذف الجدول القديم
try:
    db.execute_non_query("DROP TABLE IF EXISTS role_permissions")
    print("✓ تم حذف الجدول القديم")
except Exception as e:
    print(f"✗ خطأ في الحذف: {e}")

# إنشاء الجدول الجديد بالشكل الصحيح
try:
    db.execute_non_query('''
        CREATE TABLE role_permissions (
            role_id INTEGER NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
        )
    ''')
    print("✓ تم إنشاء الجدول الجديد")
except Exception as e:
    print(f"✗ خطأ في الإنشاء: {e}")

print("\n✅ اكتمل التصحيح!")

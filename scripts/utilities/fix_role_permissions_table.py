#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إصلاح جدول role_permissions"""
import sys
import io
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = DatabaseManager(config.get_database_path())
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
            granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            granted_by INTEGER,
            PRIMARY KEY (role_id, permission_id),
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE,
            FOREIGN KEY (granted_by) REFERENCES users(id)
        )
    ''')
    print("✓ تم إنشاء الجدول الجديد")
except Exception as e:
    print(f"✗ خطأ في الإنشاء: {e}")

print("\n✅ اكتمل التصحيح!")

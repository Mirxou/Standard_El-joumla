#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص وإضافة الصلاحيات الافتراضية"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = DatabaseManager(config.get_database_path())
db.initialize()

print("\n=== بنية جدول role_permissions ===")
schema = db.fetch_all('PRAGMA table_info(role_permissions)')
for col in schema:
    print(f"{col['name']} ({col['type']})")

print("\n=== الصلاحيات الحالية ===")
perms = db.fetch_all('SELECT * FROM role_permissions LIMIT 10')
for p in perms:
    print(dict(p))

print("\n=== بنية جدول permissions ===")
schema2 = db.fetch_all('PRAGMA table_info(permissions)')
for col in schema2:
    print(f"{col['name']} ({col['type']})")

print("\n=== جميع الصلاحيات المسجلة ===")
all_perms = db.fetch_all('SELECT * FROM permissions')
for p in all_perms:
    print(dict(p))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص بنية role_permissions"""
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

print("=== role_permissions CREATE TABLE ===")
schema = db.fetch_one("SELECT sql FROM sqlite_master WHERE type='table' AND name='role_permissions'")
if schema:
    print(schema['sql'])
else:
    print("NOT FOUND")

print("\n=== Checking roles table ===")
roles_check = db.fetch_one("SELECT sql FROM sqlite_master WHERE type='table' AND name='roles'")
if roles_check:
    print(roles_check['sql'])
else:
    print("NO ROLES TABLE - يستخدم users.role بدلاً من ذلك")

print("\n=== جدول users.role_id ===")
users_schema = db.fetch_all("PRAGMA table_info(users)")
for col in users_schema:
    if 'role' in col['name'].lower():
        print(f"{col['name']} ({col['type']})")

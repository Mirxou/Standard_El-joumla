#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص أعمدة الـ Foreign Keys"""
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

print("=== permissions CREATE TABLE ===")
schema = db.fetch_one("SELECT sql FROM sqlite_master WHERE name='permissions'")
print(schema['sql'] if schema else "NOT FOUND")

print("\n=== roles CREATE TABLE ===")
schema2 = db.fetch_one("SELECT sql FROM sqlite_master WHERE name='roles'")
print(schema2['sql'] if schema2 else "NOT FOUND")

print("\n=== role_permissions CREATE TABLE ===")
schema3 = db.fetch_one("SELECT sql FROM sqlite_master WHERE name='role_permissions'")
print(schema3['sql'] if schema3 else "NOT FOUND")

print("\n=== users CREATE TABLE (PRIMARY KEY) ===")
schema4 = db.fetch_one("SELECT sql FROM sqlite_master WHERE name='users'")
if schema4:
    sql = schema4['sql']
    # عرض الأسطر الأولى فقط
    lines = sql.split('\n')
    for i, line in enumerate(lines[:10]):
        print(line)

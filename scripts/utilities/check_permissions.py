#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص الصلاحيات"""
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

print("\n=== المستخدمين ===")
users = db.fetch_all('SELECT id, username, role, is_active FROM users')
for u in users:
    print(f"ID: {u['id']}, User: {u['username']}, Role: {u['role']}, Active: {u['is_active']}")

print("\n=== جداول الصلاحيات ===")
tables = db.fetch_all("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%perm%'")
for t in tables:
    print(f"Table: {t['name']}")

print("\n=== بنية جدول المستخدمين ===")
schema = db.fetch_all("PRAGMA table_info(users)")
for col in schema:
    print(f"{col['name']} ({col['type']})")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص كلمات السر الافتراضية"""
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

print("=== معلومات المستخدمين ===\n")

users = db.fetch_all('SELECT id, username, full_name, role, created_at FROM users')

for user in users:
    print(f"👤 {user['username']}")
    print(f"   الاسم الكامل: {user['full_name']}")
    print(f"   الدور: {user['role']}")
    print(f"   تاريخ الإنشاء: {user['created_at']}")
    print()

print("\n💡 كلمات السر الافتراضية المحتملة:")
print("   • admin")
print("   • 123456")
print("   • password")
print("   • admin123")
print("\n🔍 جرب تسجيل الدخول باستخدام:")
print("   Username: admin")
print("   Password: (جرب الخيارات أعلاه)")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص صلاحيات عرض المنتجات"""
import sys
import io
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager
from src.services.user_service import UserService

config = ConfigManager()
db = DatabaseManager(config.get_database_path())
db.initialize()

# إنشاء UserService
user_service = UserService(db)

print("\n=== صلاحيات المستخدمين ===")
users = db.fetch_all('SELECT id, username, role FROM users')

for user in users:
    print(f"\n👤 المستخدم: {user['username']} ({user['role']})")
    
    # التحقق من صلاحيات المنتجات
    perms_to_check = [
        'products.view',
        'products.create', 
        'products.edit',
        'products.delete',
        'inventory.view',
        'inventory.manage'
    ]
    
    for perm in perms_to_check:
        has_perm = user_service.check_permission(user['id'], perm)
        status = "✓" if has_perm else "✗"
        print(f"  {status} {perm}")

# التحقق من الصلاحيات الافتراضية للأدوار
print("\n\n=== صلاحيات الأدوار ===")
role_perms = db.fetch_all('SELECT * FROM role_permissions ORDER BY role')
for rp in role_perms:
    print(f"{rp['role']}: {rp['permission']}")

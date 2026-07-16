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
from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager
from src.services.user_service import UserService

config = ConfigManager()
db = LocalDatabaseManager(config.get_database_path())
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
query = '''
    SELECT r.name as role, p.name as permission
    FROM role_permissions rp
    JOIN roles r ON rp.role_id = r.id
    JOIN permissions p ON rp.permission_id = p.id
    ORDER BY r.name
'''
role_perms = db.fetch_all(query)
for rp in role_perms:
    print(f"{rp['role']}: {rp['permission']}")

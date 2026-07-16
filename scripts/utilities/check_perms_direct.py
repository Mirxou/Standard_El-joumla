#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""فحص الصلاحيات مباشرة من قاعدة البيانات"""
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

print("\n=== صلاحيات المستخدمين (من role_permissions) ===")

# الحصول على المستخدمين
users = db.fetch_all('SELECT id, username, role, role_id FROM users')

for user in users:
    print(f"\n👤 {user['username']} (role_id={user['role_id']})")
    
    # الحصول على صلاحيات هذا المستخدم من خلال دوره
    if user['role_id']:
        perms = db.fetch_all('''
            SELECT p.code, p.description
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = ?
            ORDER BY p.code
        ''', (user['role_id'],))
        
        if perms:
            print(f"  لديه {len(perms)} صلاحية:")
            for perm in perms:
                print(f"    ✓ {perm['code']}: {perm['description']}")
        else:
            print("  ⚠ لا توجد صلاحيات!")
    else:
        print("  ⚠ غير مرتبط بدور (role_id = NULL)")

print("\n=== نتيجة الفحص ===")
admin = [u for u in users if u['username'] == 'admin'][0]
admin_can_view = db.fetch_one('''
    SELECT COUNT(*) as has_perm
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    WHERE rp.role_id = ? AND p.code = ?
''', (admin['role_id'], 'products.view'))

if admin_can_view and admin_can_view['has_perm'] > 0:
    print("✅ المدير يمكنه عرض المنتجات")
else:
    print("❌ المدير لا يمكنه عرض المنتجات")

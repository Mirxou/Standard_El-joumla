#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إضافة الأدوار والصلاحيات الافتراضية"""
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

print("\n=== 1️⃣ إضافة الأدوار الأساسية ===")
roles = [
    (1, 'مدير', 'مدير النظام - صلاحيات كاملة'),
    (2, 'كاشير', 'موظف مبيعات - صلاحيات محدودة'),
    (3, 'مشرف مخزون', 'مسؤول المخزون - إدارة المنتجات والمخزون'),
    (4, 'محاسب', 'المحاسب - الوصول للتقارير المالية'),
]

for role_id, role_name, role_desc in roles:
    try:
        db.execute_insert(
            'INSERT OR IGNORE INTO roles (id, name, description) VALUES (?, ?, ?)',
            (role_id, role_name, role_desc)
        )
        print(f"✓ {role_name} (ID: {role_id})")
    except Exception as e:
        print(f"✗ خطأ في {role_name}: {e}")

print("\n=== 2️⃣ إضافة الصلاحيات الأساسية ===")
permissions = [
    ('products.view', 'منتجات', 'عرض', 'عرض قائمة المنتجات'),
    ('products.create', 'منتجات', 'إضافة', 'إضافة منتج جديد'),
    ('products.edit', 'منتجات', 'تعديل', 'تعديل معلومات منتج'),
    ('products.delete', 'منتجات', 'حذف', 'حذف منتج'),
    ('inventory.view', 'مخزون', 'عرض', 'عرض حالة المخزون'),
    ('inventory.manage', 'مخزون', 'إدارة', 'إدارة وتعديل المخزون'),
    ('sales.view', 'مبيعات', 'عرض', 'عرض قائمة المبيعات'),
    ('sales.create', 'مبيعات', 'إضافة', 'إضافة فاتورة بيع جديدة'),
    ('sales.edit', 'مبيعات', 'تعديل', 'تعديل فاتورة بيع'),
    ('sales.delete', 'مبيعات', 'حذف', 'حذف فاتورة بيع'),
    ('reports.view', 'تقارير', 'عرض', 'عرض التقارير'),
    ('reports.export', 'تقارير', 'تصدير', 'تصدير التقارير'),
    ('settings.view', 'إعدادات', 'عرض', 'عرض الإعدادات'),
    ('settings.edit', 'إعدادات', 'تعديل', 'تعديل الإعدادات'),
    ('users.view', 'مستخدمين', 'عرض', 'عرض قائمة المستخدمين'),
    ('users.manage', 'مستخدمين', 'إدارة', 'إدارة المستخدمين والصلاحيات'),
]

for code, resource, action, desc in permissions:
    try:
        db.execute_insert(
            '''INSERT OR IGNORE INTO permissions (name, code, resource_type, action, description, is_system, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)''',
            (code, code, resource, action, desc, datetime.now())
        )
        print(f"✓ {code}")
    except Exception as e:
        print(f"✗ خطأ في {code}: {e}")

# الحصول على IDs الصلاحيات
all_perms = db.fetch_all('SELECT id, code FROM permissions')
perm_map = {p['code']: p['id'] for p in all_perms}

print(f"\n=== تم تسجيل {len(all_perms)} صلاحية ===")

print("\n=== 3️⃣ منح جميع الصلاحيات للمدير (role_id=1) ===")
for perm_code, perm_id in perm_map.items():
    try:
        db.execute_insert(
            '''INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_at, granted_by)
               VALUES (1, ?, ?, 1)''',
            (perm_id, datetime.now())
        )
        print(f"✓ {perm_code}")
    except Exception as e:
        print(f"✗ {perm_code}: {e}")

# صلاحيات الكاشير (role_id=2)
cashier_perms = ['products.view', 'inventory.view', 'sales.view', 'sales.create', 'reports.view']
print(f"\n=== 4️⃣ منح صلاحيات للكاشير (role_id=2) ===")
for perm_code in cashier_perms:
    if perm_code in perm_map:
        try:
            db.execute_insert(
                '''INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_at, granted_by)
                   VALUES (2, ?, ?, 1)''',
                (perm_map[perm_code], datetime.now())
            )
            print(f"✓ {perm_code}")
        except Exception as e:
            print(f"✗ {perm_code}: {e}")

# صلاحيات مشرف المخزون (role_id=3)
warehouse_perms = ['products.view', 'products.create', 'products.edit', 'inventory.view', 'inventory.manage', 'reports.view']
print(f"\n=== 5️⃣ منح صلاحيات لمشرف المخزون (role_id=3) ===")
for perm_code in warehouse_perms:
    if perm_code in perm_map:
        try:
            db.execute_insert(
                '''INSERT OR IGNORE INTO role_permissions (role_id, permission_id, granted_at, granted_by)
                   VALUES (3, ?, ?, 1)''',
                (perm_map[perm_code], datetime.now())
            )
            print(f"✓ {perm_code}")
        except Exception as e:
            print(f"✗ {perm_code}: {e}")

# تحديث المستخدمين الحاليين لربطهم بالأدوار
print("\n=== 6️⃣ تحديث المستخدمين ===")
users_update = [
    (1, 'admin'),  # role_id=1 للمدير
    (2, 'regular1'),  # role_id=2 للكاشير
]

for role_id, username in users_update:
    try:
        result = db.execute_non_query(
            'UPDATE users SET role_id = ? WHERE username = ?',
            (role_id, username)
        )
        print(f"✓ تحديث {username} → role_id={role_id}")
    except Exception as e:
        print(f"✗ خطأ في تحديث {username}: {e}")

print("\n✅ اكتمل إعداد النظام!")

# التحقق النهائي
print("\n=== التحقق النهائي ===")
admin_perms = db.fetch_all('''
    SELECT p.code 
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    WHERE rp.role_id = 1
''')
print(f"المدير لديه {len(admin_perms)} صلاحية")

cashier_perms_check = db.fetch_all('''
    SELECT p.code 
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    WHERE rp.role_id = 2
''')
print(f"الكاشير لديه {len(cashier_perms_check)} صلاحية")

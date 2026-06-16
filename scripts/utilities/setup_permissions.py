#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""إضافة الصلاحيات الافتراضية للنظام"""
import sys
import io
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = LocalDatabaseManager(config.get_database_path())
db.initialize()

print("\n=== إضافة الصلاحيات الأساسية ===")

# الصلاحيات الأساسية
permissions = [
    # المنتجات
    ('products.view', 'منتجات', 'عرض', 'عرض قائمة المنتجات', True),
    ('products.create', 'منتجات', 'إضافة', 'إضافة منتج جديد', True),
    ('products.edit', 'منتجات', 'تعديل', 'تعديل معلومات منتج', True),
    ('products.delete', 'منتجات', 'حذف', 'حذف منتج', True),
    
    # المخزون
    ('inventory.view', 'مخزون', 'عرض', 'عرض حالة المخزون', True),
    ('inventory.manage', 'مخزون', 'إدارة', 'إدارة وتعديل المخزون', True),
    
    # المبيعات
    ('sales.view', 'مبيعات', 'عرض', 'عرض قائمة المبيعات', True),
    ('sales.create', 'مبيعات', 'إضافة', 'إضافة فاتورة بيع جديدة', True),
    ('sales.edit', 'مبيعات', 'تعديل', 'تعديل فاتورة بيع', True),
    ('sales.delete', 'مبيعات', 'حذف', 'حذف فاتورة بيع', True),
    
    # التقارير
    ('reports.view', 'تقارير', 'عرض', 'عرض التقارير', True),
    ('reports.export', 'تقارير', 'تصدير', 'تصدير التقارير', True),
    
    # الإعدادات
    ('settings.view', 'إعدادات', 'عرض', 'عرض الإعدادات', True),
    ('settings.edit', 'إعدادات', 'تعديل', 'تعديل الإعدادات', True),
    
    # المستخدمين
    ('users.view', 'مستخدمين', 'عرض', 'عرض قائمة المستخدمين', True),
    ('users.manage', 'مستخدمين', 'إدارة', 'إدارة المستخدمين والصلاحيات', True),
]

for code, resource, action, desc, is_system in permissions:
    try:
        db.execute_insert(
            '''INSERT OR IGNORE INTO permissions (name, code, resource_type, action, description, is_system, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (code, code, resource, action, desc, is_system, datetime.now())
        )
        print(f"✓ تم إضافة: {code}")
    except Exception as e:
        print(f"✗ خطأ في {code}: {e}")

# الحصول على IDs الصلاحيات
all_perms = db.fetch_all('SELECT id, code FROM permissions')
perm_map = {p['code']: p['id'] for p in all_perms}

print(f"\n=== تم تسجيل {len(all_perms)} صلاحية ===")

# الحصول على role_id للمدير
admin_role_query = "SELECT id FROM users WHERE role='مدير' OR username='admin' LIMIT 1"
admin_user = db.fetch_one(admin_role_query)
admin_role_id = 1  # افتراضي

print(f"\n=== منح جميع الصلاحيات للمدير (role_id={admin_role_id}) ===")

# منح جميع الصلاحيات للمدير
for perm_code, perm_id in perm_map.items():
    try:
        db.execute_insert(
            '''INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
               VALUES (?, ?)''',
            (admin_role_id, perm_id)
        )
        print(f"✓ {perm_code}")
    except Exception as e:
        print(f"✗ خطأ في {perm_code}: {e}")

# صلاحيات الكاشير (role_id=2 عادة)
cashier_perms = [
    'products.view',
    'inventory.view', 
    'sales.view',
    'sales.create',
    'reports.view'
]

print(f"\n=== منح صلاحيات محدودة للكاشير (role_id=2) ===")
for perm_code in cashier_perms:
    if perm_code in perm_map:
        try:
            db.execute_insert(
                '''INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                   VALUES (?, ?)''',
                (2, perm_map[perm_code])
            )
            print(f"✓ {perm_code}")
        except Exception as e:
            print(f"✗ خطأ في {perm_code}: {e}")

print("\n✅ تم إضافة الصلاحيات بنجاح!")

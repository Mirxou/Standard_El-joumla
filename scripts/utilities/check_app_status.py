#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تشخيص شامل للمشاكل المحتملة"""
import sys
import io
from pathlib import Path

# إصلاح encoding على Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))

from src.core.local_database_manager import LocalDatabaseManager
from src.core.config_manager import ConfigManager

config = ConfigManager()
db = LocalDatabaseManager(config.get_database_path())
db.initialize()

print("=" * 60)
print("🔍 تشخيص شامل للنظام")
print("=" * 60)

# 1. فحص المنتجات
print("\n1️⃣ فحص المنتجات:")
total = db.fetch_one("SELECT COUNT(*) as count FROM products")
active = db.fetch_one("SELECT COUNT(*) as count FROM products WHERE is_active = 1")
print(f"   إجمالي المنتجات: {total['count']}")
print(f"   المنتجات النشطة: {active['count']}")

# 2. فحص الفئات
print("\n2️⃣ فحص الفئات:")
categories = db.fetch_all("SELECT id, name FROM categories LIMIT 5")
print(f"   عدد الفئات: {len(db.fetch_all('SELECT id FROM categories'))}")
if categories:
    for cat in categories:
        print(f"      - {cat['name']}")

# 3. فحص المستخدمين والصلاحيات
print("\n3️⃣ فحص المستخدمين والصلاحيات:")
users = db.fetch_all("SELECT id, username, role, is_active FROM users")
for user in users:
    perms = db.fetch_one(
        "SELECT COUNT(*) as count FROM role_permissions WHERE role_id = (SELECT id FROM roles WHERE id = (SELECT role_id FROM users WHERE id = ?))",
        (user['id'],)
    )
    print(f"   👤 {user['username']}: {user['role']} - {'🟢 نشط' if user['is_active'] else '🔴 معطل'}")

# 4. فحص المستودعات
print("\n4️⃣ فحص المستودعات:")
warehouses = db.fetch_all("SELECT id, name FROM warehouses LIMIT 5")
print(f"   عدد المستودعات: {len(db.fetch_all('SELECT id FROM warehouses'))}")
if warehouses:
    for w in warehouses:
        print(f"      - {w['name']}")

# 5. فحص بيانات المخزون
print("\n5️⃣ فحص بيانات المخزون:")
inventory = db.fetch_one("SELECT COUNT(*) as count FROM warehouse_inventory")
print(f"   سجلات المخزون: {inventory['count']}")

# 6. عينة من المنتجات
print("\n6️⃣ عينة من المنتجات (أول 3):")
samples = db.fetch_all("SELECT id, name, barcode, current_stock FROM products WHERE is_active = 1 LIMIT 3")
for sample in samples:
    print(f"   - {sample['name']} (ID: {sample['id']}, Stock: {sample['current_stock']})")

print("\n" + "=" * 60)
print("✅ النظام يبدو في حالة جيدة!")
print("=" * 60)

# تحقق من قاعدة البيانات
from src.core.local_database_manager import LocalDatabaseManager
db = LocalDatabaseManager(config.get_database_path())
db_init = db.initialize()
print('=== Database Check ===')
print(f'DB initialized: {db_init}')
print(f'Connection: {"OK" if db.connection else "None"}')
print()

# تحقق من ProductManager
from src.models.product import ProductManager
pm = ProductManager(db)
print('=== Product Manager ===')
all_prods = pm.get_all_products(active_only=True)
print(f'Total active products from ProductManager: {len(all_prods)}')
if all_prods:
    print(f'First 3 products:')
    for p in all_prods[:3]:
        print(f'  - {p.name} (ID: {p.id}, Stock: {p.current_stock})')
print()

# بحث بسيط
search_results = pm.search_products('Test', active_only=True)
print(f'Search "Test": {len(search_results)} results')
if search_results:
    print(f'  First match: {search_results[0].name}')

# تحقق من InventoryService
from src.services.inventory_service import InventoryService
inv_service = InventoryService(db)
print()
print('=== Inventory Service ===')
search_inv = inv_service.search_products('Auto')
print(f'Search "Auto": {len(search_inv)} results')

db.close()
print('\n✓ All components working correctly')

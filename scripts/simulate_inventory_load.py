#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""محاكاة تحميل بيانات المخزون كما يفعل التطبيق"""
import sys
import io
from pathlib import Path
import sqlite3

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.config_manager import ConfigManager

config = ConfigManager()
db_path = config.get_database_path()

print(f"=== محاكاة تحميل المخزون ===")
print(f"DB Path: {db_path}")

# محاكاة الاستعلام المستخدم في InventoryDataLoaderThread
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

query = """
    SELECT 
        p.id,
        p.barcode,
        p.name,
        COALESCE(c.name, 'غير محدد') as category,
        COALESCE(p.unit, 'قطعة') as unit,
        COALESCE(p.current_stock, 0) as current_stock,
        COALESCE(p.min_stock, 0) as min_stock,
        COALESCE(p.selling_price, 0.0) as selling_price
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE COALESCE(p.is_active, 1) = 1
    ORDER BY p.id DESC
    LIMIT 10
"""

cursor = conn.execute(query)
results = cursor.fetchall()

print(f"\n✅ تم جلب {len(results)} منتج (أول 10)")

if results:
    print("\n=== عينة من البيانات ===")
    for i, row in enumerate(results[:3]):
        print(f"\n{i+1}. {row['name']}")
        print(f"   ID: {row['id']}")
        print(f"   Barcode: {row['barcode']}")
        print(f"   Category: {row['category']}")
        print(f"   Stock: {row['current_stock']}")
        print(f"   Price: {row['selling_price']}")
else:
    print("\n❌ لم يتم العثور على أي منتجات!")
    
    # فحص المشكلة
    total_check = conn.execute("SELECT COUNT(*) as count FROM products").fetchone()
    print(f"   إجمالي المنتجات في الجدول: {total_check['count']}")
    
    active_check = conn.execute("SELECT COUNT(*) as count FROM products WHERE is_active = 1").fetchone()
    print(f"   المنتجات النشطة: {active_check['count']}")

conn.close()

print("\n=== النتيجة ===")
if results:
    print("✅ الاستعلام يعمل بشكل صحيح - المنتجات يجب أن تظهر في الواجهة")
else:
    print("❌ الاستعلام لا يرجع بيانات - هناك مشكلة في البيانات")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""اختبار أداء تحميل البيانات"""
import sys
import io
import time
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path.cwd()))
from src.core.config_manager import ConfigManager
import sqlite3
import pandas as pd

config = ConfigManager()
db_path = config.get_database_path()

print("=" * 70)
print("⚡ اختبار أداء تحميل البيانات")
print("=" * 70)

# اختبار 1: تحميل 200 منتج
print("\n1️⃣ تحميل 200 منتج الأول:")
start = time.perf_counter()
conn = sqlite3.connect(db_path, timeout=30)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA query_only=true")

query = """
    SELECT 
        p.id, p.barcode, p.name,
        COALESCE(c.name, 'غير محدد') as category,
        COALESCE(p.unit, 'قطعة') as unit,
        COALESCE(p.current_stock, 0) as current_stock,
        COALESCE(p.min_stock, 0) as min_stock,
        COALESCE(p.selling_price, 0.0) as selling_price
    FROM products p
    LEFT JOIN categories c ON p.category_id = c.id
    WHERE COALESCE(p.is_active, 1) = 1
    ORDER BY p.id DESC
    LIMIT 200
"""

df = pd.read_sql_query(query, conn)
elapsed = time.perf_counter() - start

print(f"   ✅ تم تحميل {len(df)} منتج في {elapsed:.2f} ثانية")
print(f"   السرعة: {len(df) / elapsed:.0f} منتج/ثانية")

# اختبار 2: تحميل 500 منتج
print("\n2️⃣ تحميل 500 منتج:")
start = time.perf_counter()
query2 = query.replace("LIMIT 200", "LIMIT 500")
df2 = pd.read_sql_query(query2, conn)
elapsed = time.perf_counter() - start

print(f"   ✅ تم تحميل {len(df2)} منتج في {elapsed:.2f} ثانية")
print(f"   السرعة: {len(df2) / elapsed:.0f} منتج/ثانية")

# اختبار 3: مع البحث
print("\n3️⃣ تحميل مع البحث ('Test'):")
start = time.perf_counter()
query3 = query + " AND (p.name LIKE ? OR p.barcode LIKE ?)"
search_pattern = "%Test%"
df3 = pd.read_sql_query(query3, conn, params=[search_pattern, search_pattern])
elapsed = time.perf_counter() - start

print(f"   ✅ تم تحميل {len(df3)} منتج في {elapsed:.2f} ثانية")

conn.close()

print("\n" + "=" * 70)
print("✅ النتائج:")
print("=" * 70)
print("   إذا كانت الأرقام < 0.5 ثانية، فالمشكلة ليست في قاعدة البيانات")
print("   قد تكون المشكلة في عرض البيانات على الواجهة (UI rendering)")
print("\n💡 الحل المقترح:")
print("   - تقليل عدد المنتجات المحملة في المرة (تم: 200 بدلاً من 500)")
print("   - استخدام Virtual Scrolling (تم)")
print("   - استخدام ScrollPerItem بدلاً من ScrollPerPixel (تم)")
print("=" * 70)

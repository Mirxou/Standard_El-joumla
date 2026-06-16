#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص قاعدة البيانات للبحث عن مشاكل محتملة
"""

import sys
from pathlib import Path
import io

# لضمان عرض الأحرف العربية بشكل صحيح في PowerShell
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.local_database_manager import LocalDatabaseManager

def check_database():
    """فحص قاعدة البيانات للبحث عن مشاكل"""
    print("🔍 فحص قاعدة البيانات...\n")
    
    db_path = Path(__file__).parent.parent / "data" / "standard_eljoumla.db"
    
    if not db_path.exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    print(f"✅ قاعدة البيانات موجودة: {db_path}")
    print(f"📊 حجم الملف: {db_path.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    try:
        db_manager = LocalDatabaseManager()
        if not db_manager.initialize():
            print("❌ فشل تهيئة قاعدة البيانات")
            return False
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 1. فحص الجداول
        print("=" * 60)
        print("📋 الجداول الموجودة:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        print(f"عدد الجداول: {len(tables)}")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} صف")
        print()
        
        # 2. فحص هيكل جدول products
        print("=" * 60)
        print("📦 هيكل جدول products:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(products)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
        
        # 3. فحص هيكل جدول sales
        print("=" * 60)
        print("💰 هيكل جدول sales:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(sales)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
        
        # 4. فحص هيكل جدول sale_items
        print("=" * 60)
        print("🛒 هيكل جدول sale_items:")
        print("=" * 60)
        cursor.execute("PRAGMA table_info(sale_items)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
        
        # 5. فحص البيانات المكررة
        print("=" * 60)
        print("🔍 فحص البيانات المكررة:")
        print("=" * 60)
        
        # فحص products مكررة
        cursor.execute("""
            SELECT name, COUNT(*) as count 
            FROM products 
            GROUP BY name 
            HAVING COUNT(*) > 1
            LIMIT 10
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            print("⚠️  منتجات مكررة:")
            for dup in duplicates:
                print(f"  - {dup[0]}: {dup[1]} نسخة")
        else:
            print("✅ لا توجد منتجات مكررة")
        print()
        
        # 6. فحص العلاقات المكسورة
        print("=" * 60)
        print("🔗 فحص العلاقات المكسورة:")
        print("=" * 60)
        
        # sale_items بدون sale
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sale_items si 
            LEFT JOIN sales s ON si.sale_id = s.id 
            WHERE s.id IS NULL
        """)
        orphaned_items = cursor.fetchone()[0]
        if orphaned_items > 0:
            print(f"⚠️  {orphaned_items} عنصر مبيعات بدون فاتورة")
        else:
            print("✅ جميع عناصر المبيعات مرتبطة بفواتير")
        
        # sale_items بدون product
        cursor.execute("""
            SELECT COUNT(*) 
            FROM sale_items si 
            LEFT JOIN products p ON si.product_id = p.id 
            WHERE p.id IS NULL
        """)
        orphaned_products = cursor.fetchone()[0]
        if orphaned_products > 0:
            print(f"⚠️  {orphaned_products} عنصر مبيعات بدون منتج")
        else:
            print("✅ جميع عناصر المبيعات مرتبطة بمنتجات")
        print()
        
        # 7. فحص الفهارس
        print("=" * 60)
        print("📇 الفهارس الموجودة:")
        print("=" * 60)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        indexes = cursor.fetchall()
        print(f"عدد الفهارس: {len(indexes)}")
        for idx in indexes[:20]:  # أول 20 فهرس
            print(f"  - {idx[0]}")
        if len(indexes) > 20:
            print(f"  ... و {len(indexes) - 20} فهرس آخر")
        print()
        
        # 8. فحص integrity
        print("=" * 60)
        print("🔒 فحص سلامة قاعدة البيانات:")
        print("=" * 60)
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]
        if integrity == 'ok':
            print("✅ قاعدة البيانات سليمة")
        else:
            print(f"⚠️  {integrity}")
        print()
        
        # 9. فحص foreign keys
        print("=" * 60)
        print("🔑 فحص Foreign Keys:")
        print("=" * 60)
        cursor.execute("PRAGMA foreign_key_check")
        fk_errors = cursor.fetchall()
        if fk_errors:
            print(f"⚠️  {len(fk_errors)} خطأ في Foreign Keys:")
            for error in fk_errors[:10]:  # أول 10 أخطاء
                print(f"  - جدول {error[0]}: صف {error[1]}")
        else:
            print("✅ جميع Foreign Keys سليمة")
        print()
        
        conn.close()
        print("✅ انتهى الفحص")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database()


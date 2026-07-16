#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من عدد المنتجات في قاعدة البيانات
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

def check_products_count():
    """التحقق من عدد المنتجات"""
    print("🔍 التحقق من عدد المنتجات في قاعدة البيانات...\n")
    
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
        
        # فحص عدد المنتجات
        print("=" * 60)
        print("📦 إحصائيات المنتجات:")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        print(f"إجمالي المنتجات: {total_products:,}")
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
        active_products = cursor.fetchone()[0]
        print(f"المنتجات النشطة: {active_products:,}")
        
        cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 0")
        inactive_products = cursor.fetchone()[0]
        print(f"المنتجات غير النشطة: {inactive_products:,}")
        
        # فحص المبيعات
        print("\n" + "=" * 60)
        print("💰 إحصائيات المبيعات:")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_sales = cursor.fetchone()[0]
        print(f"إجمالي المبيعات: {total_sales:,}")
        
        cursor.execute("SELECT COUNT(*) FROM sale_items")
        total_items = cursor.fetchone()[0]
        print(f"إجمالي عناصر المبيعات: {total_items:,}")
        
        # فحص أكبر الجداول
        print("\n" + "=" * 60)
        print("📊 أكبر الجداول (أول 10):")
        print("=" * 60)
        
        # الحصول على قائمة الجداول
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = cursor.fetchall()
        
        table_counts = []
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                if count > 0:
                    table_counts.append((table_name, count))
            except Exception:
                pass
        
        # ترتيب حسب العدد
        table_counts.sort(key=lambda x: x[1], reverse=True)
        
        for table_name, count in table_counts[:10]:
            print(f"  {table_name}: {count:,} صف")
        
        # فحص حجم قاعدة البيانات
        print("\n" + "=" * 60)
        print("💾 معلومات قاعدة البيانات:")
        print("=" * 60)
        
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        db_size_mb = (page_count * page_size) / 1024 / 1024
        print(f"عدد الصفحات: {page_count:,}")
        print(f"حجم الصفحة: {page_size:,} بايت")
        print(f"الحجم الإجمالي: {db_size_mb:.2f} MB")
        
        # فحص الفهارس
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
        index_count = cursor.fetchone()[0]
        print(f"عدد الفهارس: {index_count:,}")
        
        conn.close()
        
        print("\n" + "=" * 60)
        if total_products > 0:
            print(f"✅ تم العثور على {total_products:,} منتج في قاعدة البيانات")
        else:
            print("⚠️  لا توجد منتجات في قاعدة البيانات")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_products_count()


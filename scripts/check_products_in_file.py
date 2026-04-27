#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التحقق من عدد المنتجات في ملف قاعدة بيانات محدد
"""

import sys
import sqlite3
from pathlib import Path
import io

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

# لضمان عرض الأحرف العربية بشكل صحيح في PowerShell
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def check_products_in_file(db_path: str):
    """التحقق من عدد المنتجات في ملف قاعدة بيانات"""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ الملف غير موجود: {db_path}")
        return False
    
    print(f"🔍 فحص ملف قاعدة البيانات: {db_file.name}")
    print(f"📊 حجم الملف: {db_file.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    try:
        db_manager = DatabaseManager(str(db_file))
        db_manager.initialize()
        db_manager.connection.row_factory = sqlite3.Row
        cursor = db_manager.connection.cursor()
        
        # فحص عدد المنتجات
        print("=" * 60)
        print("📦 إحصائيات المنتجات:")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        print(f"إجمالي المنتجات: {total_products:,}")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM products WHERE is_active = 1")
            active_products = cursor.fetchone()[0]
            print(f"المنتجات النشطة: {active_products:,}")
        except:
            print("المنتجات النشطة: غير متاح")
        
        # فحص المبيعات
        print("\n" + "=" * 60)
        print("💰 إحصائيات المبيعات:")
        print("=" * 60)
        
        try:
            cursor.execute("SELECT COUNT(*) FROM sales")
            total_sales = cursor.fetchone()[0]
            print(f"إجمالي المبيعات: {total_sales:,}")
        except:
            print("إجمالي المبيعات: غير متاح")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM sale_items")
            total_items = cursor.fetchone()[0]
            print(f"إجمالي عناصر المبيعات: {total_items:,}")
        except:
            print("إجمالي عناصر المبيعات: غير متاح")
        
        # فحص أكبر الجداول
        print("\n" + "=" * 60)
        print("📊 أكبر الجداول (أول 10):")
        print("=" * 60)
        
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
            except:
                pass
        
        table_counts.sort(key=lambda x: x[1], reverse=True)
        
        for table_name, count in table_counts[:10]:
            print(f"  {table_name}: {count:,} صف")
        
        db_manager.connection.close()
        
        print("\n" + "=" * 60)
        if total_products > 0:
            print(f"✅ تم العثور على {total_products:,} منتج في قاعدة البيانات")
        else:
            print("⚠️  لا توجد منتجات في قاعدة البيانات")
        print("=" * 60)
        
        return total_products
        
    except Exception as e:
        print(f"❌ خطأ في فحص قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return 0

if __name__ == "__main__":
    # فحص الملفات المختلفة
    base_path = Path(__file__).parent.parent / "data"
    
    files_to_check = [
        "logical_release.db",
        "logical_release_new.db",
        "backups/logical_release_old_20251231_103627.db",
        "backups/logical_release_corrupted_20251231_103600.db"
    ]
    
    print("🔍 فحص جميع ملفات قاعدة البيانات...\n")
    
    for file_name in files_to_check:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"\n{'='*60}")
            print(f"📁 {file_name}")
            print('='*60)
            check_products_in_file(str(file_path))
            print()


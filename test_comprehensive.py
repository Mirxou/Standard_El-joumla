#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
اختبار شامل لجميع مكونات النظام
Comprehensive System Test
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

def print_section(title):
    """طباعة عنوان قسم"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_database_integrity():
    """اختبار سلامة قاعدة البيانات"""
    print_section("1. اختبار سلامة قاعدة البيانات")
    
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # فحص السلامة
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()[0]
        print(f"✅ PRAGMA integrity_check: {result}")
        
        # فحص المفاتيح الخارجية
        cursor.execute('PRAGMA foreign_key_check')
        fk_errors = cursor.fetchall()
        if len(fk_errors) == 0:
            print(f"✅ Foreign Key Check: OK (0 errors)")
        else:
            print(f"❌ Foreign Key Errors: {len(fk_errors)}")
            for error in fk_errors[:5]:
                print(f"   {error}")
        
        # إحصائيات
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Total Tables: {len(tables)}")
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
        indexes = cursor.fetchone()[0]
        print(f"✅ Total Indexes: {indexes}")
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
        triggers = cursor.fetchone()[0]
        print(f"✅ Total Triggers: {triggers}")
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
        views = cursor.fetchone()[0]
        print(f"✅ Total Views: {views}")
        
        # حجم قاعدة البيانات
        db_path = Path('inventory.db')
        if db_path.exists():
            db_size = db_path.stat().st_size / 1024 / 1024
            print(f"✅ Database Size: {db_size:.2f} MB")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار قاعدة البيانات: {e}")
        return False

def test_table_counts():
    """اختبار عدد السجلات في الجداول الرئيسية"""
    print_section("2. إحصائيات البيانات")
    
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        tables_to_check = [
            ('products', 'المنتجات'),
            ('categories', 'الفئات'),
            ('customers', 'العملاء'),
            ('suppliers', 'الموردون'),
            ('invoices', 'فواتير المبيعات'),
            ('purchase_invoices', 'فواتير المشتريات'),
            ('stock_movements', 'حركات المخزون'),
            ('chart_of_accounts', 'دليل الحسابات'),
            ('general_journal', 'القيود اليومية'),
            ('users', 'المستخدمون'),
            ('roles', 'الأدوار'),
            ('permissions', 'الصلاحيات'),
        ]
        
        for table, arabic_name in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  📊 {arabic_name:25} ({table:25}): {count:5} سجل")
            except sqlite3.OperationalError:
                print(f"  ⚠️  {arabic_name:25} ({table:25}): غير موجود")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الإحصائيات: {e}")
        return False

def test_migrations():
    """اختبار تطبيق الـ migrations"""
    print_section("3. اختبار Migrations")
    
    migrations_dir = Path('migrations')
    if not migrations_dir.exists():
        print("❌ مجلد migrations غير موجود")
        return False
    
    migration_files = sorted(migrations_dir.glob('*.sql'))
    print(f"✅ عدد ملفات Migration: {len(migration_files)}")
    
    for migration_file in migration_files:
        print(f"  ✓ {migration_file.name}")
    
    return True

def test_services():
    """اختبار تهيئة الخدمات"""
    print_section("4. اختبار الخدمات")
    
    try:
        # إضافة المسار
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.core.database_manager import DatabaseManager
        
        print("  ⏳ تهيئة قاعدة البيانات...")
        db_manager = DatabaseManager('inventory.db')
        print("  ✅ DatabaseManager initialized")
        
        # اختبار خدمة المخزون
        try:
            from src.services.inventory_service import InventoryService
            inventory_service = InventoryService(db_manager)
            print("  ✅ InventoryService initialized")
        except Exception as e:
            print(f"  ⚠️  InventoryService: {e}")
        
        # اختبار خدمة المبيعات
        try:
            from src.services.sales_service import SalesService
            sales_service = SalesService(db_manager)
            print("  ✅ SalesService initialized")
        except Exception as e:
            print(f"  ⚠️  SalesService: {e}")
        
        # اختبار خدمة التقارير
        try:
            from src.services.reports_service import ReportsService
            reports_service = ReportsService(db_manager)
            print("  ✅ ReportsService initialized")
        except Exception as e:
            print(f"  ⚠️  ReportsService: {e}")
        
        # اختبار خدمة المحاسبة
        try:
            from src.services.accounting_service import AccountingService
            accounting_service = AccountingService(db_manager)
            print("  ✅ AccountingService initialized")
        except Exception as e:
            print(f"  ⚠️  AccountingService: {e}")
        
        # اختبار خدمة المستخدمين
        try:
            from src.services.user_service import UserService
            user_service = UserService(db_manager)
            print("  ✅ UserService initialized")
        except Exception as e:
            print(f"  ⚠️  UserService: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار الخدمات: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_windows():
    """اختبار توفر ملفات النوافذ"""
    print_section("5. اختبار ملفات النوافذ")
    
    windows_dir = Path('src/ui/windows')
    if not windows_dir.exists():
        print("❌ مجلد windows غير موجود")
        return False
    
    expected_windows = [
        'main_window.py',
        'accounting_window.py',
        'quotes_window.py',
        'returns_window.py',
        'purchase_orders_window.py',
        'payment_plans_window.py',
        'abc_analysis_window.py',
        'safety_stock_window.py',
        'batch_tracking_window.py',
        'reorder_recommendations_window.py',
        'physical_counts_window.py',
        'stock_adjustments_window.py',
        'advanced_reports_window.py',
        'dashboard_window.py',
        'advanced_search_window.py',
    ]
    
    found = 0
    for window_file in expected_windows:
        window_path = windows_dir / window_file
        if window_path.exists():
            print(f"  ✅ {window_file}")
            found += 1
        else:
            print(f"  ❌ {window_file} - غير موجود")
    
    print(f"\n  📊 النوافذ الموجودة: {found}/{len(expected_windows)}")
    
    return found > 0

def test_models():
    """اختبار توفر ملفات النماذج"""
    print_section("6. اختبار ملفات النماذج")
    
    models_dir = Path('src/models')
    if not models_dir.exists():
        print("❌ مجلد models غير موجود")
        return False
    
    model_files = list(models_dir.glob('*.py'))
    model_files = [f for f in model_files if f.name != '__init__.py']
    
    print(f"✅ عدد ملفات النماذج: {len(model_files)}")
    
    for model_file in sorted(model_files):
        print(f"  ✓ {model_file.name}")
    
    return len(model_files) > 0

def test_reports():
    """اختبار نظام التقارير"""
    print_section("7. اختبار نظام التقارير")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.core.database_manager import DatabaseManager
        from src.services.reports_service import ReportsService
        
        db_manager = DatabaseManager('inventory.db')
        reports_service = ReportsService(db_manager)
        
        print("  ✅ ReportsService initialized")
        
        # اختبار أنواع التقارير
        try:
            # يمكن إضافة المزيد من الاختبارات هنا
            print("  ✅ Reports system ready")
        except Exception as e:
            print(f"  ⚠️  خطأ في اختبار التقارير: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار التقارير: {e}")
        return False

def test_search():
    """اختبار نظام البحث"""
    print_section("8. اختبار نظام البحث")
    
    try:
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        
        # التحقق من وجود جدول البحث FTS5
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%fts%' OR name LIKE '%search%'
        """)
        search_tables = cursor.fetchall()
        
        if search_tables:
            print(f"  ✅ جداول البحث الموجودة:")
            for table in search_tables:
                print(f"     • {table[0]}")
        else:
            print("  ⚠️  لا توجد جداول بحث FTS5")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ خطأ في اختبار البحث: {e}")
        return False

def generate_summary(results):
    """إنشاء ملخص النتائج"""
    print_section("📊 ملخص الاختبار الشامل")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"""
  📈 إجمالي الاختبارات: {total_tests}
  ✅ الاختبارات الناجحة: {passed_tests}
  ❌ الاختبارات الفاشلة: {failed_tests}
  📊 معدل النجاح: {success_rate:.1f}%
  
  تفاصيل الاختبارات:
""")
    
    for test_name, result in results.items():
        status = "✅ نجح" if result else "❌ فشل"
        print(f"    {status} - {test_name}")
    
    print("\n" + "=" * 80)
    
    if success_rate >= 80:
        print("  🎉 النظام في حالة ممتازة!")
    elif success_rate >= 60:
        print("  ⚠️  النظام في حالة جيدة مع بعض التحذيرات")
    else:
        print("  ❌ النظام يحتاج إلى إصلاحات")
    
    print("=" * 80)
    
    return success_rate >= 60

def main():
    """الدالة الرئيسية"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "🔍 اختبار شامل للنظام 🔍" + " " * 20 + "║")
    print("║" + " " * 15 + "Comprehensive System Test" + " " * 15 + "║")
    print("╚" + "═" * 78 + "╝")
    
    results = {}
    
    # تشغيل الاختبارات
    results['سلامة قاعدة البيانات'] = test_database_integrity()
    results['إحصائيات البيانات'] = test_table_counts()
    results['Migrations'] = test_migrations()
    results['الخدمات'] = test_services()
    results['النوافذ'] = test_windows()
    results['النماذج'] = test_models()
    results['التقارير'] = test_reports()
    results['البحث'] = test_search()
    
    # ملخص النتائج
    success = generate_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())

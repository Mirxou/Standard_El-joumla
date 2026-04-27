#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إضافة company_id إلى جميع الجداول الرئيسية
Add Company ID Columns to All Main Tables Script
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

def column_exists(cursor, table_name: str, column_name: str) -> bool:
    """التحقق من وجود عمود في جدول"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def table_exists(cursor, table_name: str) -> bool:
    """التحقق من وجود جدول"""
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?
    """, (table_name,))
    return cursor.fetchone() is not None

def add_company_columns(db_path: str):
    """إضافة company_id إلى جميع الجداول الرئيسية"""
    
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()
    db_manager.connection.execute("PRAGMA foreign_keys = ON")
    cursor = db_manager.connection.cursor()
    
    try:
        # الحصول على معرف الشركة الافتراضية
        cursor.execute("SELECT id FROM companies WHERE is_default = 1 LIMIT 1")
        default_company = cursor.fetchone()
        
        if not default_company:
            print("❌ لم يتم العثور على شركة افتراضية!")
            print("   يرجى تشغيل migration 021_add_multi_company_support.sql أولاً")
            return
        
        default_company_id = default_company[0]
        print(f"✅ الشركة الافتراضية: ID = {default_company_id}")
        print("=" * 60)
        
        # قائمة الجداول التي تحتاج company_id
        tables_to_update = [
            # المنتجات والمخزون
            ('products', 'المنتجات'),
            ('product_variants', 'متغيرات المنتجات'),
            ('bundle_products', 'منتجات الحزم'),
            ('pricing_tiers', 'مستويات الأسعار'),
            ('product_labels', 'ملصقات المنتجات'),
            ('stock_movements', 'حركات المخزون'),
            ('batches', 'الدفعات'),
            
            # العملاء والموردين
            ('customers', 'العملاء'),
            ('suppliers', 'الموردين'),
            
            # المبيعات والمشتريات
            ('sales', 'المبيعات'),
            ('sale_items', 'عناصر المبيعات'),
            ('purchases', 'المشتريات'),
            ('purchase_items', 'عناصر المشتريات'),
            
            # الفواتير والاقتباسات
            ('invoices', 'الفواتير'),
            ('quotes', 'الاقتباسات'),
            ('quote_items', 'عناصر الاقتباسات'),
            ('return_invoices', 'فواتير المرتجعات'),
            ('return_items', 'عناصر المرتجعات'),
            
            # المدفوعات
            ('payments', 'المدفوعات'),
            ('payment_schedules', 'جدولة المدفوعات'),
            ('payment_plans', 'خطط الدفع'),
            ('payment_installments', 'أقساط الدفع'),
            
            # المستودعات
            ('warehouses', 'المستودعات'),
            ('warehouse_inventory', 'مخزون المستودعات'),
            ('warehouse_transfers', 'نقلات المستودعات'),
            ('warehouse_transfer_items', 'عناصر نقلات المستودعات'),
            
            # الطلبات والاستلام
            ('purchase_orders', 'طلبات الشراء'),
            ('purchase_order_items', 'عناصر طلبات الشراء'),
            ('receiving_notes', 'إذونات الاستلام'),
            ('receiving_items', 'عناصر الاستلام'),
            
            # الجرد
            ('physical_counts', 'الجرد الفعلي'),
            ('count_items', 'عناصر الجرد'),
            ('cycle_counts', 'الجرد الدوري'),
            
            # المحاسبة
            ('chart_of_accounts', 'دليل الحسابات'),
            ('journal_entries', 'قيود اليومية'),
            ('journal_lines', 'بنود القيود'),
            
            # التسويق والعلاقات
            ('marketing_campaigns', 'الحملات التسويقية'),
            ('customer_segments', 'شرائح العملاء'),
            
            # التقارير
            ('reports', 'التقارير'),
            ('report_templates', 'قوالب التقارير'),
        ]
        
        added_count = 0
        skipped_count = 0
        updated_count = 0
        
        for table_name, table_name_ar in tables_to_update:
            if not table_exists(cursor, table_name):
                print(f"⏭️  تخطي {table_name_ar} ({table_name}) - الجدول غير موجود")
                skipped_count += 1
                continue
            
            # إضافة company_id إذا لم يكن موجوداً
            if not column_exists(cursor, table_name, 'company_id'):
                try:
                    cursor.execute(f"""
                        ALTER TABLE {table_name} 
                        ADD COLUMN company_id INTEGER DEFAULT NULL
                    """)
                    print(f"✅ تم إضافة company_id إلى {table_name_ar} ({table_name})")
                    added_count += 1
                    
                    # تحديث البيانات الموجودة بالشركة الافتراضية
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET company_id = ? 
                        WHERE company_id IS NULL
                    """, (default_company_id,))
                    
                    updated_rows = cursor.rowcount
                    if updated_rows > 0:
                        print(f"   📝 تم تحديث {updated_rows} سجل بالشركة الافتراضية")
                        updated_count += updated_rows
                    
                except Exception as e:
                    print(f"❌ خطأ في إضافة company_id إلى {table_name}: {e}")
            else:
                print(f"ℹ️  company_id موجود بالفعل في {table_name_ar} ({table_name})")
        
        # إضافة Foreign Key constraint (إذا أمكن)
        # ملاحظة: SQLite لا يدعم إضافة Foreign Key بعد إنشاء الجدول مباشرة
        # سنستخدم طريقة بديلة: التحقق من وجود الشركة في الكود
        
        db_manager.connection.commit()
        
        print("\n" + "=" * 60)
        print("📊 ملخص التحديث:")
        print(f"   ✅ تم إضافة company_id إلى {added_count} جدول")
        print(f"   ⏭️  تم تخطي {skipped_count} جدول (غير موجود)")
        print(f"   📝 تم تحديث {updated_count} سجل بالشركة الافتراضية")
        print("\n✅ تم إضافة جميع أعمدة company_id بنجاح!")
        
    except Exception as e:
        db_manager.connection.rollback()
        print(f"\n❌ خطأ: {e}")
        raise
    finally:
        db_manager.connection.close()

if __name__ == "__main__":
    # تحديد مسار قاعدة البيانات
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        project_root = Path(__file__).parent.parent
        db_path = str(project_root / "data" / "logical_release.db")
    
    print(f"📁 قاعدة البيانات: {db_path}")
    print("=" * 60)
    
    if not Path(db_path).exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        sys.exit(1)
    
    add_company_columns(db_path)
    print("\n✅ اكتمل التحديث بنجاح!")


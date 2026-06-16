#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إضافة أعمدة العملة إلى الجداول المالية
Add Currency Columns to Financial Tables Script
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.local_database_manager import LocalDatabaseManager

def add_currency_columns(db_path: str):
    """إضافة أعمدة العملة إلى الجداول المالية"""
    
    db_manager = LocalDatabaseManager(db_path)
    db_manager.initialize()
    db_manager.connection.execute("PRAGMA foreign_keys = ON")
    cursor = db_manager.connection.cursor()
    
    try:
        # الحصول على قائمة الأعمدة الموجودة في كل جدول
        def column_exists(table_name: str, column_name: str) -> bool:
            """التحقق من وجود عمود في جدول"""
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            return column_name in columns
        
        # =====================================================
        # 1. جدول المبيعات (Sales)
        # =====================================================
        if not column_exists('sales', 'currency_id'):
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN currency_id INTEGER DEFAULT NULL
            """)
            print("✅ تم إضافة currency_id إلى جدول sales")
        else:
            print("ℹ️  العمود currency_id موجود بالفعل في جدول sales")
        
        if not column_exists('sales', 'exchange_rate'):
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN exchange_rate REAL DEFAULT 1.0
            """)
            print("✅ تم إضافة exchange_rate إلى جدول sales")
        else:
            print("ℹ️  العمود exchange_rate موجود بالفعل في جدول sales")
        
        if not column_exists('sales', 'base_amount'):
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN base_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة base_amount إلى جدول sales")
        else:
            print("ℹ️  العمود base_amount موجود بالفعل في جدول sales")
        
        if not column_exists('sales', 'converted_amount'):
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN converted_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة converted_amount إلى جدول sales")
        else:
            print("ℹ️  العمود converted_amount موجود بالفعل في جدول sales")
        
        # إضافة Foreign Key للعملة
        # ملاحظة: SQLite لا يدعم إضافة Foreign Key بعد إنشاء الجدول مباشرة
        # سنستخدم طريقة بديلة: التحقق من وجود العملة في الكود
        
        # =====================================================
        # 2. جدول المشتريات (Purchases)
        # =====================================================
        if not column_exists('purchases', 'currency_id'):
            cursor.execute("""
                ALTER TABLE purchases 
                ADD COLUMN currency_id INTEGER DEFAULT NULL
            """)
            print("✅ تم إضافة currency_id إلى جدول purchases")
        else:
            print("ℹ️  العمود currency_id موجود بالفعل في جدول purchases")
        
        if not column_exists('purchases', 'exchange_rate'):
            cursor.execute("""
                ALTER TABLE purchases 
                ADD COLUMN exchange_rate REAL DEFAULT 1.0
            """)
            print("✅ تم إضافة exchange_rate إلى جدول purchases")
        else:
            print("ℹ️  العمود exchange_rate موجود بالفعل في جدول purchases")
        
        if not column_exists('purchases', 'base_amount'):
            cursor.execute("""
                ALTER TABLE purchases 
                ADD COLUMN base_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة base_amount إلى جدول purchases")
        else:
            print("ℹ️  العمود base_amount موجود بالفعل في جدول purchases")
        
        if not column_exists('purchases', 'converted_amount'):
            cursor.execute("""
                ALTER TABLE purchases 
                ADD COLUMN converted_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة converted_amount إلى جدول purchases")
        else:
            print("ℹ️  العمود converted_amount موجود بالفعل في جدول purchases")
        
        # =====================================================
        # 3. جدول المدفوعات (Payments)
        # =====================================================
        if not column_exists('payments', 'currency_id'):
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN currency_id INTEGER DEFAULT NULL
            """)
            print("✅ تم إضافة currency_id إلى جدول payments")
        else:
            print("ℹ️  العمود currency_id موجود بالفعل في جدول payments")
        
        if not column_exists('payments', 'exchange_rate'):
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN exchange_rate REAL DEFAULT 1.0
            """)
            print("✅ تم إضافة exchange_rate إلى جدول payments")
        else:
            print("ℹ️  العمود exchange_rate موجود بالفعل في جدول payments")
        
        if not column_exists('payments', 'base_amount'):
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN base_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة base_amount إلى جدول payments")
        else:
            print("ℹ️  العمود base_amount موجود بالفعل في جدول payments")
        
        if not column_exists('payments', 'converted_amount'):
            cursor.execute("""
                ALTER TABLE payments 
                ADD COLUMN converted_amount DECIMAL(10,2) DEFAULT NULL
            """)
            print("✅ تم إضافة converted_amount إلى جدول payments")
        else:
            print("ℹ️  العمود converted_amount موجود بالفعل في جدول payments")
        
        # =====================================================
        # 4. تحديث البيانات الموجودة
        # =====================================================
        # تعيين العملة الأساسية (DZD) لجميع السجلات الموجودة
        cursor.execute("SELECT id FROM currencies WHERE code = 'DZD' AND is_base = 1 LIMIT 1")
        base_currency = cursor.fetchone()
        
        if base_currency:
            base_currency_id = base_currency[0]
            
            # تحديث المبيعات
            cursor.execute("""
                UPDATE sales 
                SET currency_id = ?, exchange_rate = 1.0, 
                    base_amount = COALESCE(total_amount, final_amount, 0),
                    converted_amount = COALESCE(total_amount, final_amount, 0)
                WHERE currency_id IS NULL
            """, (base_currency_id,))
            
            # تحديث المشتريات
            cursor.execute("""
                UPDATE purchases 
                SET currency_id = ?, exchange_rate = 1.0,
                    base_amount = COALESCE(total_amount, final_amount, 0),
                    converted_amount = COALESCE(total_amount, final_amount, 0)
                WHERE currency_id IS NULL
            """, (base_currency_id,))
            
            # تحديث المدفوعات
            cursor.execute("""
                UPDATE payments 
                SET currency_id = ?, exchange_rate = 1.0,
                    base_amount = COALESCE(amount, 0),
                    converted_amount = COALESCE(amount, 0)
                WHERE currency_id IS NULL
            """, (base_currency_id,))
            
            print("✅ تم تحديث البيانات الموجودة بالعملة الأساسية")
        
        db_manager.connection.commit()
        print("\n✅ تم إضافة جميع أعمدة العملة بنجاح!")
        
    except Exception as e:
        db_manager.connection.rollback()
        print(f"❌ خطأ: {e}")
        raise
    finally:
        db_manager.connection.close()

if __name__ == "__main__":
    # تحديد مسار قاعدة البيانات
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        project_root = Path(__file__).parent.parent
        db_path = str(project_root / "data" / "standard_eljoumla.db")
    
    print(f"📁 قاعدة البيانات: {db_path}")
    print("=" * 50)
    
    if not Path(db_path).exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        sys.exit(1)
    
    add_currency_columns(db_path)
    print("\n✅ اكتمل التحديث بنجاح!")


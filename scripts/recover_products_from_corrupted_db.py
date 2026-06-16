#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
استعادة المنتجات من قاعدة بيانات تالفة
"""

import sqlite3
import sys
from pathlib import Path
import io

# لضمان عرض الأحرف العربية بشكل صحيح في PowerShell
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def recover_products(corrupted_db_path: str, target_db_path: str = None):
    """استعادة المنتجات من قاعدة بيانات تالفة"""
    
    corrupted_file = Path(corrupted_db_path)
    
    if not corrupted_file.exists():
        print(f"❌ الملف غير موجود: {corrupted_db_path}")
        return False
    
    print(f"🔧 محاولة استعادة المنتجات من: {corrupted_file.name}")
    print(f"📊 حجم الملف: {corrupted_file.stat().st_size / 1024 / 1024:.2f} MB\n")
    
    # تحديد ملف الهدف
    if target_db_path is None:
        target_db_path = Path(__file__).parent.parent / "data" / "standard_eljoumla.db"
    else:
        target_db_path = Path(target_db_path)
    
    print(f"📁 ملف الهدف: {target_db_path.name}\n")
    
    try:
        # محاولة فتح الملف التالف
        print("=" * 60)
        print("🔍 محاولة فتح قاعدة البيانات التالفة...")
        print("=" * 60)
        
        # استخدام dump method
        try:
            old_conn = sqlite3.connect(f"file:{corrupted_file}?mode=ro", uri=True)
            old_cursor = old_conn.cursor()
            
            # محاولة قراءة عدد المنتجات
            try:
                old_cursor.execute("SELECT COUNT(*) FROM products")
                product_count = old_cursor.fetchone()[0]
                print(f"✅ تم العثور على {product_count:,} منتج في الملف التالف")
            except Exception as e:
                print(f"⚠️  لا يمكن قراءة عدد المنتجات: {e}")
                product_count = 0
            
            if product_count == 0:
                print("⚠️  لا توجد منتجات في الملف التالف")
                old_conn.close()
                return False
            
            # محاولة استخراج البيانات
            print("\n" + "=" * 60)
            print("📥 محاولة استخراج البيانات...")
            print("=" * 60)
            
            # قراءة المنتجات بشكل دفعات
            batch_size = 1000
            recovered_count = 0
            
            try:
                # التحقق من وجود جدول products في الهدف
                target_conn = sqlite3.connect(str(target_db_path))
                target_cursor = target_conn.cursor()
                
                # التحقق من وجود الجدول
                target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
                if not target_cursor.fetchone():
                    print("❌ جدول products غير موجود في قاعدة البيانات الهدف")
                    target_conn.close()
                    old_conn.close()
                    return False
                
                # بدء استخراج البيانات
                offset = 0
                while True:
                    try:
                        old_cursor.execute(f"SELECT * FROM products LIMIT {batch_size} OFFSET {offset}")
                        products = old_cursor.fetchall()
                        
                        if not products:
                            break
                        
                        # الحصول على أسماء الأعمدة
                        old_cursor.execute("PRAGMA table_info(products)")
                        columns_info = old_cursor.fetchall()
                        column_names = [col[1] for col in columns_info]
                        
                        # إدراج البيانات
                        for product in products:
                            try:
                                # بناء استعلام INSERT
                                placeholders = ','.join(['?' for _ in column_names])
                                columns = ','.join(column_names)
                                
                                # التحقق من عدم وجود المنتج مسبقاً
                                if 'id' in column_names:
                                    product_id = product[column_names.index('id')]
                                    target_cursor.execute("SELECT COUNT(*) FROM products WHERE id = ?", (product_id,))
                                    if target_cursor.fetchone()[0] > 0:
                                        continue  # تخطي المنتج الموجود
                                
                                target_cursor.execute(f"INSERT OR IGNORE INTO products ({columns}) VALUES ({placeholders})", product)
                                recovered_count += 1
                                
                                if recovered_count % 1000 == 0:
                                    print(f"  ✅ تم استعادة {recovered_count:,} منتج...")
                                    target_conn.commit()
                                    
                            except Exception as e:  # noqa: F841
                                # تخطي المنتجات التي لا يمكن إدراجها
                                continue
                        
                        offset += batch_size
                        
                        if len(products) < batch_size:
                            break
                            
                    except Exception as e:
                        print(f"⚠️  خطأ في استخراج الدفعة {offset}: {e}")
                        break
                
                target_conn.commit()
                target_conn.close()
                
                print(f"\n✅ تم استعادة {recovered_count:,} منتج بنجاح!")
                
            except Exception as e:
                print(f"❌ خطأ في استخراج البيانات: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            old_conn.close()
            
        except Exception as e:
            print(f"❌ لا يمكن فتح الملف التالف: {e}")
            print("\n💡 اقتراحات:")
            print("  1. تأكد من إغلاق جميع التطبيقات التي تستخدم قاعدة البيانات")
            print("  2. حاول استخدام أداة إصلاح SQLite خارجية")
            print("  3. استخدم نسخة احتياطية أخرى إن وجدت")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # محاولة استعادة من الملفات التالفة
    base_path = Path(__file__).parent.parent / "data"
    
    corrupted_files = [
        "logical_release_new.db",
        "backups/logical_release_old_20251231_103627.db",
        "backups/logical_release_corrupted_20251231_103600.db"
    ]
    
    print("🔧 محاولة استعادة المنتجات من الملفات التالفة...\n")
    
    for file_name in corrupted_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"\n{'='*60}")
            print(f"📁 محاولة استعادة من: {file_name}")
            print('='*60)
            
            if recover_products(str(file_path)):
                print(f"\n✅ نجحت الاستعادة من {file_name}")
                break
            else:
                print(f"\n❌ فشلت الاستعادة من {file_name}")
                print()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إصلاح مشاكل قاعدة البيانات
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

def fix_database_issues():
    """إصلاح مشاكل قاعدة البيانات"""
    print("🔧 إصلاح مشاكل قاعدة البيانات...\n")
    
    db_path = Path(__file__).parent.parent / "data" / "standard_eljoumla.db"
    
    if not db_path.exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    try:
        db_manager = LocalDatabaseManager()
        if not db_manager.initialize():
            print("❌ فشل تهيئة قاعدة البيانات")
            return False
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # 1. إصلاح role_permissions
        print("=" * 60)
        print("🔧 إصلاح Foreign Key في role_permissions:")
        print("=" * 60)
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='role_permissions'")
            if cursor.fetchone():
                print("✅ جدول role_permissions موجود")
                
                cursor.execute("SELECT COUNT(*) FROM role_permissions")
                count = cursor.fetchone()[0]
                print(f"📊 عدد الصفوف: {count}")
                
                print("\n🔄 إعادة إنشاء الجدول مع Foreign Key الصحيح...")
                
                # إنشاء جدول مؤقت
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS role_permissions_temp (
                        role_id INTEGER NOT NULL,
                        permission_id INTEGER NOT NULL,
                        PRIMARY KEY (role_id, permission_id),
                        FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE CASCADE,
                        FOREIGN KEY (permission_id) REFERENCES permissions(permission_id) ON DELETE CASCADE
                    )
                """)
                
                # نسخ البيانات
                if count > 0:
                    cursor.execute("INSERT INTO role_permissions_temp SELECT * FROM role_permissions")
                    print(f"✅ تم نسخ {count} صف")
                
                # حذف وإعادة تسمية
                cursor.execute("DROP TABLE role_permissions")
                cursor.execute("ALTER TABLE role_permissions_temp RENAME TO role_permissions")
                
                # إعادة إنشاء الفهارس
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_perms_role ON role_permissions(role_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_role_perms_perm ON role_permissions(permission_id)")
                
                conn.commit()
                print("✅ تم إصلاح Foreign Key في role_permissions بنجاح")
            else:
                print("ℹ️  جدول role_permissions غير موجود")
        except Exception as e:
            print(f"⚠️  خطأ في إصلاح role_permissions: {e}")
            conn.rollback()
        
        # 2. فحص Foreign Keys
        print("\n" + "=" * 60)
        print("🔍 فحص Foreign Keys:")
        print("=" * 60)
        
        try:
            cursor.execute("PRAGMA foreign_key_check")
            fk_errors = cursor.fetchall()
            if fk_errors:
                print(f"⚠️  {len(fk_errors)} خطأ في Foreign Keys:")
                for error in fk_errors[:10]:
                    print(f"  - جدول {error[0]}: صف {error[1]}")
            else:
                print("✅ جميع Foreign Keys سليمة")
        except Exception as e:
            print(f"⚠️  لا يمكن فحص Foreign Keys: {e}")
        
        conn.close()
        print("\n✅ انتهى الإصلاح")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إصلاح قاعدة البيانات: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_database_issues()

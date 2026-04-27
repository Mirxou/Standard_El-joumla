#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت إصلاح قاعدة البيانات التالفة
Database Repair Script
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

def fix_database(db_path: Path, backup_path: Path = None):
    """إصلاح قاعدة البيانات التالفة"""
    
    if not db_path.exists():
        print("قاعدة البيانات غير موجودة")
        return False
    
    # إنشاء نسخة احتياطية
    if backup_path is None:
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_corrupted_{timestamp}{db_path.suffix}"
    
    print(f"إنشاء نسخة احتياطية: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    # محاولة إصلاح
    try:
        print("محاولة إصلاح قاعدة البيانات...")
        
        # محاولة فتح قاعدة البيانات التالفة
        old_db_manager = DatabaseManager(str(db_path))
        old_db_manager.initialize()
        
        # محاولة استخراج البيانات
        try:
            cursor = old_db_manager.connection.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            print(f"   Integrity Check: {result[0]}")
        except Exception as e:
            print(f"   لا يمكن التحقق من السلامة: {e}")
        
        # إنشاء قاعدة بيانات جديدة
        new_db_path = db_path.parent / f"{db_path.stem}_new{db_path.suffix}"
        
        # محاولة نسخ البيانات
        try:
            new_db_manager = DatabaseManager(str(new_db_path))
            new_db_manager.initialize()
            old_db_manager.connection.backup(new_db_manager.connection)
            new_db_manager.connection.close()
            print("   تم نسخ البيانات")
        except Exception as e:
            print(f"   فشل نسخ البيانات: {e}")
            new_db_path.unlink(missing_ok=True)
            raise
        
        old_db_manager.connection.close()
        
        # التحقق من قاعدة البيانات الجديدة
        test_db_manager = DatabaseManager(str(new_db_path))
        test_db_manager.initialize()
        test_cursor = test_db_manager.connection.cursor()
        test_cursor.execute("PRAGMA integrity_check")
        test_result = test_cursor.fetchone()
        test_db_manager.connection.close()
        
        if test_result[0] == "ok":
            # استبدال قاعدة البيانات القديمة
            db_path.unlink()
            new_db_path.rename(db_path)
            print("تم إصلاح قاعدة البيانات بنجاح!")
            return True
        else:
            print(f"قاعدة البيانات الجديدة غير صالحة: {test_result[0]}")
            new_db_path.unlink(missing_ok=True)
            return False
            
    except Exception as e:
        print(f"فشل إصلاح قاعدة البيانات: {e}")
        return False

def create_new_database(db_path: Path):
    """إنشاء قاعدة بيانات جديدة"""
    print("إنشاء قاعدة بيانات جديدة...")
    
    # حذف قاعدة البيانات التالفة
    if db_path.exists():
        db_path.unlink()
    
    # إنشاء قاعدة بيانات جديدة فارغة
    db_manager = DatabaseManager(str(db_path))
    db_manager.initialize()
    db_manager.connection.execute("PRAGMA journal_mode=WAL")
    db_manager.connection.close()
    
    print("تم إنشاء قاعدة بيانات جديدة")
    print("   سيتم تطبيق migrations تلقائياً عند التشغيل")
    return True

if __name__ == "__main__":
    # إعداد الترميز
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "logical_release.db"
    
    print("إصلاح قاعدة البيانات...")
    print(f"   المسار: {db_path}")
    print("")
    
    # محاولة الإصلاح
    success = fix_database(db_path)
    
    if not success:
        print("")
        print("فشل إصلاح قاعدة البيانات")
        response = input("هل تريد إنشاء قاعدة بيانات جديدة؟ (y/n): ")
        
        if response.lower() == 'y':
            create_new_database(db_path)
        else:
            print("تم الإلغاء")
            sys.exit(1)
    
    print("")
    print("اكتمل الإصلاح!")
    print("   يمكنك الآن تشغيل Backend API")


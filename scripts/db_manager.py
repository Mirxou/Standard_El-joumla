#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إدارة قواعد البيانات - Database Management Utility
وحدة مركزية لإصلاح مشاكل قاعدة البيانات

الاستخدام:
    python db_manager.py checkIntegrity
    python db_manager.py fixIntegrity
    python db_manager.py vacuum
    python db_manager.py backup [path]
    python db_manager.py restore [path]

أو استخدم متغير البيئة:
    DB_PATH=data/standard_eljoumla.db python db_manager.py checkIntegrity
"""

import sys
import os
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.local_database_manager import LocalDatabaseManager


def get_db_path():
    """الحصول على مسار قاعدة البيانات"""
    # Check for explicit database path argument
    if len(sys.argv) > 2:
        # For restore command, second arg is backup path, third is target
        if sys.argv[1] == "restore":
            return sys.argv[3] if len(sys.argv) > 3 else None
        # For other commands, second arg might be db path
        elif sys.argv[1] not in ["checkIntegrity", "fixIntegrity", "vacuum", "backup"]:
            return sys.argv[2]
    
    # Check environment variable
    db_path = os.getenv('DB_PATH')
    if db_path and os.path.exists(db_path):
        return db_path
    
    # Default paths
    default_paths = [
        Path(__file__).parent.parent / "data" / "standard_eljoumla.db",
        Path(__file__).parent.parent / "data" / "database.db",
        Path(__file__).parent.parent / "erp_system.db",
    ]
    
    for path in default_paths:
        if path.exists():
            return str(path)
    
    return None


def check_integrity(db_path):
    """فحص سلامة قاعدة البيانات"""
    if not db_path or not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    print(f"🔍 فحص سلامة قاعدة البيانات: {db_path}")
    
    try:
        db_manager = LocalDatabaseManager(db_path)
        db_manager.initialize()
        cursor = db_manager.connection.cursor()
        
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == 'ok':
            print("✅ قاعدة البيانات سليمة")
            db_manager.connection.close()
            return True
        else:
            print(f"❌ توجد مشاكل: {result[0]}")
            db_manager.connection.close()
            return False
    
    except Exception as e:
        print(f"❌ خطأ في الفحص: {e}")
        return False


def fix_integrity(db_path):
    """إصلاح قاعدة البيانات"""
    if not db_path or not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    print(f"🔧 إصلاح قاعدة البيانات: {db_path}")
    
    try:
        db_manager = LocalDatabaseManager(db_path)
        db_manager.initialize()
        cursor = db_manager.connection.cursor()
        
        print("   - إعادة الفهرسة...")
        cursor.execute("REINDEX")
        
        print("   - تحسين الجداول...")
        cursor.execute("VACUUM")
        
        db_manager.connection.commit()
        db_manager.connection.close()
        
        print("✅ تم الإصلاح بنجاح")
        return check_integrity(db_path)
    
    except Exception as e:
        print(f"❌ خطأ في الإصلاح: {e}")
        return False


def vacuum_db(db_path):
    """ضغط قاعدة البيانات"""
    if not db_path or not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    print(f"📦 ضغط قاعدة البيانات: {db_path}")
    
    original_size = os.path.getsize(db_path)
    
    try:
        db_manager = LocalDatabaseManager(db_path)
        db_manager.initialize()
        cursor = db_manager.connection.cursor()
        cursor.execute("VACUUM")
        db_manager.connection.close()
        
        new_size = os.path.getsize(db_path)
        saved = original_size - new_size
        saved_pct = (saved / original_size) * 100 if original_size > 0 else 0
        
        print(f"✅ تم الضغط بنجاح")
        print(f"   الحجم الأصلي: {original_size / 1024 / 1024:.2f} MB")
        print(f"   الحجم الجديد: {new_size / 1024 / 1024:.2f} MB")
        print(f"   تم توفير: {saved / 1024 / 1024:.2f} MB ({saved_pct:.1f}%)")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ في الضغط: {e}")
        return False


def backup_db(db_path, backup_path=None):
    """نسخ احتياطي"""
    if not db_path or not os.path.exists(db_path):
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    if not backup_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{timestamp}"
    
    print(f"💾 إنشاء نسخة احتياطية...")
    print(f"   المصدر: {db_path}")
    print(f"   الوجهة: {backup_path}")
    
    try:
        shutil.copy2(db_path, backup_path)
        size = os.path.getsize(backup_path)
        print(f"✅ تم إنشاء النسخة الاحتياطية ({size / 1024 / 1024:.2f} MB)")
        return True
    
    except Exception as e:
        print(f"❌ خطأ في النسخ الاحتياطي: {e}")
        return False


def restore_db(backup_path, target_path=None):
    """استعادة من نسخة احتياطية"""
    if not backup_path or not os.path.exists(backup_path):
        print(f"❌ نسخة الاحتياط غير موجودة: {backup_path}")
        return False
    
    if not target_path:
        db_path = get_db_path()
        if not db_path:
            print("❌ لا يمكن تحديد مسار قاعدة البيانات الهدف")
            return False
        target_path = db_path
    
    print(f"🔄 استعادة قاعدة البيانات...")
    print(f"   المصدر: {backup_path}")
    print(f"   الوجهة: {target_path}")
    
    try:
        shutil.copy2(backup_path, target_path)
        print("✅ تم الاستعادة بنجاح")
        return True
    
    except Exception as e:
        print(f"❌ خطأ في الاستعادة: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1]
    db_path = get_db_path() if command not in ["backup", "restore"] else None
    
    if command == "checkIntegrity":
        check_integrity(db_path)
    
    elif command == "fixIntegrity":
        if not db_path:
            print("❌ يجب تحديد مسار قاعدة البيانات")
            return
        check_integrity(db_path)
        fix_integrity(db_path)
    
    elif command == "vacuum":
        if not db_path:
            print("❌ يجب تحديد مسار قاعدة البيانات")
            return
        vacuum_db(db_path)
    
    elif command == "backup":
        backup_path = sys.argv[2] if len(sys.argv) > 2 else None
        backup_db(db_path, backup_path)
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("❌ الاستخدام: python db_manager.py restore [backup_path] [target_path]")
            return
        restore_db(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    
    else:
        print(f"❌ أمر غير معروف: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

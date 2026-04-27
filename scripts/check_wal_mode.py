#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت سريع للتحقق من تفعيل WAL mode
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

def check_wal_mode(db_path: str = "data/logical_release.db"):
    """التحقق من وضع WAL"""
    db_file = Path(db_path)
    wal_file = db_file.parent / f"{db_file.name}-wal"
    
    print("=" * 70)
    print("🔍 التحقق من وضع WAL (Write-Ahead Logging)")
    print("=" * 70)
    print()
    
    # التحقق من وجود ملف قاعدة البيانات
    if not db_file.exists():
        print(f"❌ ملف قاعدة البيانات غير موجود: {db_path}")
        return False
    
    print(f"📁 قاعدة البيانات: {db_file}")
    print(f"📁 ملف WAL المتوقع: {wal_file}")
    print()
    
    try:
        # الاتصال بقاعدة البيانات
        db_manager = DatabaseManager(str(db_file))
        db_manager.initialize()
        cursor = db_manager.connection.cursor()
        
        # التحقق من وضع Journal
        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0].upper()
        
        # التحقق من وجود ملف WAL
        wal_exists = wal_file.exists()
        
        print(f"📊 النتائج:")
        print(f"   Journal Mode: {journal_mode}")
        print(f"   ملف WAL موجود: {'✅ نعم' if wal_exists else '❌ لا'}")
        print()
        
        # التقييم
        if journal_mode == "WAL":
            if wal_exists:
                print("✅ ممتاز! WAL mode مفعّل ويعمل بشكل صحيح")
                print("   - SQLite في وضع تعدد الخيوط")
                print("   - لا يوجد قفل قاعدة البيانات")
                db_manager.connection.close()
                return True
            else:
                print("⚠️  WAL mode مفعّل لكن ملف WAL غير موجود")
                print("   - قد يكون التطبيق لم يكتب بعد")
                print("   - أو أن الملف تم حذفه")
        else:
            print(f"❌ WAL mode غير مفعّل - الوضع الحالي: {journal_mode}")
            print("   - يجب تفعيل WAL mode للأداء الأمثل")
            print("   - تحقق من إعدادات Connection Pool")
        
        db_manager.connection.close()
        
    except Exception as e:
        print(f"❌ خطأ في التحقق: {e}")
        return False
    
    print("=" * 70)
    return False

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/logical_release.db"
    success = check_wal_mode(db_path)
    sys.exit(0 if success else 1)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
تحسين وتنظيف قاعدة البيانات
Database optimization and cleanup utility
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database_manager import DatabaseManager

def optimize_database():
    """تحسين وتنظيف قاعدة البيانات"""
    print("=" * 70)
    print("⚡ تحسين قاعدة البيانات")
    print("=" * 70)
    
    try:
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize()
        
        print("\n📊 الحالة الحالية:")
        db_info = db_manager.get_database_info()
        print(f"   الحجم: {db_info.get('size_mb', 0):.2f} MB")
        print(f"   الجداول: {db_info.get('tables_count', 0)}")
        
        # Get cursor
        with db_manager.get_cursor() as cursor:
            # 1. VACUUM - تنظيف وإعادة بناء
            print("\n1️⃣ تنفيذ VACUUM...")
            cursor.execute("VACUUM")
            print("   ✅ تم")
            
            # 2. ANALYZE - تحديث إحصائيات الاستعلامات
            print("\n2️⃣ تنفيذ ANALYZE...")
            cursor.execute("ANALYZE")
            print("   ✅ تم")
            
            # 3. إعادة بناء الفهارس
            print("\n3️⃣ إعادة بناء الفهارس...")
            cursor.execute("REINDEX")
            print("   ✅ تم")
            
            # 4. تنظيف السجلات القديمة (اختياري)
            print("\n4️⃣ تنظيف السجلات القديمة...")
            
            # حذف سجلات التدقيق الأقدم من 6 أشهر
            cursor.execute("""
                DELETE FROM audit_log 
                WHERE timestamp < datetime('now', '-6 months')
            """)
            deleted_audit = cursor.rowcount
            
            # حذف الجلسات المنتهية
            cursor.execute("""
                DELETE FROM user_sessions 
                WHERE expires_at < datetime('now')
            """)
            deleted_sessions = cursor.rowcount
            
            print(f"   - حذف {deleted_audit} سجل تدقيق قديم")
            print(f"   - حذف {deleted_sessions} جلسة منتهية")
            print("   ✅ تم")
            
            # 5. تحديث الإحصائيات
            print("\n5️⃣ تحديث الإحصائيات...")
            cursor.execute("PRAGMA optimize")
            print("   ✅ تم")
        
        # Get final info
        print("\n📊 الحالة النهائية:")
        db_info_final = db_manager.get_database_info()
        print(f"   الحجم: {db_info_final.get('size_mb', 0):.2f} MB")
        
        space_saved = db_info.get('size_mb', 0) - db_info_final.get('size_mb', 0)
        if space_saved > 0:
            print(f"   المساحة المحررة: {space_saved:.2f} MB")
        
        print("\n" + "=" * 70)
        print("✅ اكتمل التحسين بنجاح!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'db_manager' in locals():
            db_manager.close()

if __name__ == "__main__":
    success = optimize_database()
    sys.exit(0 if success else 1)

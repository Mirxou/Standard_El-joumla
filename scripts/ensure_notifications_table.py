#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
التأكد من وجود جدول الإشعارات
Ensure notifications table exists
"""

import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.local_database_manager import LocalDatabaseManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def ensure_notifications_table():
    """التأكد من وجود جدول الإشعارات"""
    try:
        print("🔧 تهيئة قاعدة البيانات...")
        db_manager = LocalDatabaseManager()
        if not db_manager.initialize():
            print("❌ فشل تهيئة قاعدة البيانات")
            return False
        
        print("📋 التحقق من وجود جدول الإشعارات...")
        
        # التحقق من وجود الجدول
        table_exists = db_manager.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='notifications'"
        )
        
        if table_exists:
            print("✅ جدول الإشعارات موجود بالفعل")
        else:
            print("➕ إنشاء جدول الإشعارات...")
            db_manager.connection.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    user_id INTEGER,
                    action_url TEXT,
                    data TEXT,
                    read BOOLEAN DEFAULT 0,
                    read_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # إنشاء الفهارس
            db_manager.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_user 
                ON notifications(user_id, read, created_at DESC)
            """)
            
            db_manager.connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_notifications_category 
                ON notifications(category, created_at DESC)
            """)
            
            db_manager.connection.commit()
            print("✅ تم إنشاء جدول الإشعارات بنجاح")
        
        # التحقق من عدد الإشعارات
        count = db_manager.fetch_one("SELECT COUNT(*) as count FROM notifications")
        print(f"📊 عدد الإشعارات الحالية: {count['count'] if isinstance(count, dict) else count[0]}")
        
        return True
    
    except Exception as e:
        print(f"❌ خطأ: {e}")
        logger.error(f"خطأ في التأكد من جدول الإشعارات: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = ensure_notifications_table()
    sys.exit(0 if success else 1)


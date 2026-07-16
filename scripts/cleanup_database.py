#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت تنظيف قاعدة البيانات
يقوم بـ VACUUM لضغط قاعدة البيانات وإزالة البيانات المؤقتة
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.local_database_manager import LocalDatabaseManager

def cleanup_database(db_path: str = "data/standard_eljoumla.db"):
    """تنظيف قاعدة البيانات"""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ قاعدة البيانات غير موجودة: {db_path}")
        return False
    
    try:
        # الحصول على الحجم قبل التنظيف
        size_before = db_file.stat().st_size / (1024 * 1024)  # بالميجابايت
        
        print(f"📊 حجم قاعدة البيانات قبل التنظيف: {size_before:.2f} MB")
        
        # الاتصال بقاعدة البيانات
        db_manager = LocalDatabaseManager(db_path)
        db_manager.initialize()
        cursor = db_manager.connection.cursor()
        
        # تنفيذ VACUUM
        print("🧹 جاري تنظيف قاعدة البيانات (VACUUM)...")
        cursor.execute("VACUUM")
        
        # تحليل الجداول لتحسين الأداء
        print("📈 جاري تحليل الجداول لتحسين الأداء...")
        cursor.execute("ANALYZE")
        
        db_manager.connection.close()
        
        # الحصول على الحجم بعد التنظيف
        size_after = db_file.stat().st_size / (1024 * 1024)
        saved = size_before - size_after
        
        print(f"✅ تم التنظيف بنجاح!")
        print(f"📊 حجم قاعدة البيانات بعد التنظيف: {size_after:.2f} MB")
        print(f"💾 تم توفير: {saved:.2f} MB")
        
        return True
        
    except Exception as e:
        print(f"❌ حدث خطأ أثناء التنظيف: {e}")
        return False

if __name__ == "__main__":
    cleanup_database()


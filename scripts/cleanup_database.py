#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكربت تنظيف قاعدة البيانات
يقوم بـ VACUUM لضغط قاعدة البيانات وإزالة البيانات المؤقتة
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def cleanup_database(db_path: str = "data/logical_release.db"):
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # تنفيذ VACUUM
        print("🧹 جاري تنظيف قاعدة البيانات (VACUUM)...")
        cursor.execute("VACUUM")
        
        # تحليل الجداول لتحسين الأداء
        print("📈 جاري تحليل الجداول لتحسين الأداء...")
        cursor.execute("ANALYZE")
        
        conn.close()
        
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


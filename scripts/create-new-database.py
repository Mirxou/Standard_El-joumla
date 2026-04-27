#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إنشاء قاعدة بيانات جديدة
Create New Database
"""

import sqlite3
import sys
import shutil
from pathlib import Path
from datetime import datetime

# إعداد الترميز
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def create_new_database(db_path: Path):
    """إنشاء قاعدة بيانات جديدة"""
    print("إنشاء قاعدة بيانات جديدة...")
    
    # إنشاء نسخة احتياطية من قاعدة البيانات القديمة إن وجدت
    if db_path.exists():
        backup_dir = db_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_old_{timestamp}{db_path.suffix}"
        print(f"إنشاء نسخة احتياطية من قاعدة البيانات القديمة: {backup_path}")
        try:
            shutil.copy2(db_path, backup_path)
            print("تم حفظ النسخة الاحتياطية")
        except Exception as e:
            print(f"تحذير: فشل حفظ النسخة الاحتياطية: {e}")
        
        # حذف قاعدة البيانات القديمة
        db_path.unlink()
        print("تم حذف قاعدة البيانات القديمة")
    
    # إنشاء قاعدة بيانات جديدة فارغة
    print("إنشاء قاعدة بيانات جديدة...")
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.close()
    
    print("تم إنشاء قاعدة بيانات جديدة بنجاح!")
    print("سيتم تطبيق migrations تلقائياً عند تشغيل Backend API")
    return True

if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "logical_release.db"
    
    print("=" * 50)
    print("إنشاء قاعدة بيانات جديدة")
    print(f"المسار: {db_path}")
    print("=" * 50)
    print("")
    
    success = create_new_database(db_path)
    
    if success:
        print("")
        print("=" * 50)
        print("اكتمل!")
        print("يمكنك الآن تشغيل Backend API")
        print("=" * 50)
        sys.exit(0)
    else:
        print("")
        print("فشل إنشاء قاعدة البيانات")
        sys.exit(1)


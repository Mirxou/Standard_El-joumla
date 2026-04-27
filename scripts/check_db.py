#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فحص قاعدة البيانات - Check Database Tables

الاستخدام: python check_db.py [database_path]
           أو يستخدم المسار الافتراضي: data/logical_release.db
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager

# تحديد مسار قاعدة البيانات
def get_db_path():
    # استخدام المعامل إذا تم تمريره
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    # استخدام متغير البيئة
    db_path = os.getenv('DB_PATH')
    if db_path and os.path.exists(db_path):
        return db_path
    
    # المسارات الافتراضية
    default_paths = [
        Path(__file__).parent.parent / "data" / "logical_release.db",
        Path(__file__).parent.parent / "data" / "database.db",
        Path(__file__).parent.parent / "erp_system.db",
    ]
    
    for path in default_paths:
        if path.exists():
            return str(path)
    
    return None

db_path = get_db_path()

if not db_path:
    print("❌ خطأ: لم يتم العثور على قاعدة البيانات")
    print("   الاستخدام: python check_db.py [path_to_database]")
    print("   أو عين متغير البيئة: DB_PATH=/path/to/database.db")
    sys.exit(1)

if not os.path.exists(db_path):
    print(f"❌ خطأ: قاعدة البيانات غير موجودة: {db_path}")
    sys.exit(1)

print(f"📂 الاتصال بقاعدة البيانات: {db_path}\n")

db_manager = DatabaseManager(db_path)
db_manager.initialize()
cursor = db_manager.connection.cursor()

print("--- Categories Table ---")
cursor.execute("SELECT * FROM categories")
rows = cursor.fetchall()
for row in rows:
    print(row)

print("\n--- Products Table Count ---")
cursor.execute("SELECT COUNT(*) FROM products")
print(f"عدد المنتجات: {cursor.fetchone()[0]}")

db_manager.connection.close()
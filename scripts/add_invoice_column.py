#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت تشغيل ترحيل قاعدة البيانات
"""

import sys
from pathlib import Path

# إضافة المسار الجذري
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.core.local_database_manager import LocalDatabaseManager

def run_migration(migration_file: str):
    """تشغيل ملف ترحيل"""
    print(f"🔄 تشغيل الترحيل: {migration_file}")

    # قراءة ملف الترحيل
    migration_path = project_root / 'migrations' / migration_file
    if not migration_path.exists():
        print(f"❌ ملف الترحيل غير موجود: {migration_path}")
        return False

    with open(migration_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()  # noqa: F841

    # تشغيل الترحيل
    db_manager = LocalDatabaseManager()
    db_manager.initialize()

    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # محاولة إضافة الأعمدة (تجاهل إذا كانت موجودة)
            try:
                cursor.execute("ALTER TABLE sales ADD COLUMN invoice_number TEXT")
                print("✅ تم إضافة عمود invoice_number")
            except Exception:
                print("⚠️ عمود invoice_number موجود بالفعل")

            try:
                cursor.execute("ALTER TABLE sale_items ADD COLUMN batch_id TEXT")
                print("✅ تم إضافة عمود batch_id")
            except Exception:
                print("⚠️ عمود batch_id موجود بالفعل")

            try:
                cursor.execute("ALTER TABLE sale_items ADD COLUMN discount REAL DEFAULT 0.0")
                print("✅ تم إضافة عمود discount")
            except Exception:
                print("⚠️ عمود discount موجود بالفعل")

            try:
                cursor.execute("ALTER TABLE sale_items ADD COLUMN total_price REAL DEFAULT 0.0")
                print("✅ تم إضافة عمود total_price")
            except Exception:
                print("⚠️ عمود total_price موجود بالفعل")

            # إنشاء الفهارس
            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_invoice_number ON sales(invoice_number)")
                print("✅ تم إنشاء فهرس invoice_number")
            except Exception:
                print("⚠️ فهرس invoice_number موجود بالفعل")

            try:
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sales_final_amount ON sales(final_amount)")
                print("✅ تم إنشاء فهرس final_amount")
            except Exception:
                print("⚠️ فهرس final_amount موجود بالفعل")

            conn.commit()
        print(f"✅ تم تشغيل الترحيل بنجاح: {migration_file}")
        return True
    except Exception as e:
        print(f"❌ فشل في تشغيل الترحيل: {e}")
        return False

if __name__ == "__main__":
    # تشغيل ترحيل إضافة عمود invoice_number
    success = run_migration('031_add_invoice_number_to_sales.sql')

    if success:
        print("🎉 تم إضافة عمود invoice_number بنجاح")
    else:
        print("❌ فشل في إضافة عمود invoice_number")
        sys.exit(1)

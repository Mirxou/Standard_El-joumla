import sys
import os
from pathlib import Path

# إعداد المسارات لكي نتمكن من استيراد DatabaseManager
current_dir = Path(__file__).parent.parent

try:
    from src.core.database_manager import DatabaseManager
except ImportError:
    # محاولة بديلة إذا كان الملف في الجذر
    from src.core.database_manager import DatabaseManager

def update_database():
    print("🚀 بدء عملية تحديث قاعدة البيانات...")
    
    # تهيئة مدير قاعدة البيانات
    # استخدام المسار الافتراضي (data/logical_release.db)
    db = DatabaseManager()
    
    # تهيئة التجمع والاتصال
    if not db.initialize():
        print("❌ فشل تهيئة قاعدة البيانات")
        return
    
    # قائمة التعديلات المطلوبة (الجدول، العمود، النوع، القيمة الافتراضية)
    updates = [
        # --- تحديثات المنتجات (Products) ---
        ("products", "wholesale_price", "REAL", "0.0"),
        ("products", "tax_rate", "REAL", "0.0"),
        ("products", "supplier_id", "INTEGER", "NULL"),
        ("products", "is_perishable", "BOOLEAN", "0"),
        ("products", "expiry_date", "DATE", "NULL"),
        ("products", "batch_number", "TEXT", "NULL"),
        ("products", "production_date", "DATE", "NULL"),
        ("products", "abc_classification", "TEXT", "NULL"),
        ("products", "ai_forecast_demand", "REAL", "NULL"),
        ("products", "last_analysis_date", "DATETIME", "NULL"),

        # --- تحديثات الموردين (Suppliers) ---
        ("suppliers", "name_en", "TEXT", "NULL"),
        ("suppliers", "website", "TEXT", "NULL"),
        ("suppliers", "city", "TEXT", "NULL"),
        ("suppliers", "country", "TEXT", "'الجزائر'"),
        ("suppliers", "commercial_register", "TEXT", "NULL"),
        ("suppliers", "payment_terms", "TEXT", "'نقدي'"),
        ("suppliers", "credit_limit", "REAL", "0.0"),
        ("suppliers", "current_balance", "REAL", "0.0"),
        
        # --- تحديثات المستودعات (Warehouses) ---
        ("warehouses", "name_en", "TEXT", "NULL"),
        ("warehouses", "warehouse_type", "TEXT", "'main'"),
        ("warehouses", "capacity", "REAL", "0.0"),
        ("warehouses", "current_utilization", "REAL", "0.0"),
        ("warehouses", "allow_negative_stock", "BOOLEAN", "0"),
    ]

    conn = db.get_connection()
    cursor = conn.cursor()

    for table, column, type_, default in updates:
        try:
            # التحقق مما إذا كان العمود موجوداً
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [info[1] for info in cursor.fetchall()]
            
            if column not in columns:
                print(f"🛠️  جاري إضافة العمود '{column}' إلى جدول '{table}'...")
                alter_query = f"ALTER TABLE {table} ADD COLUMN {column} {type_} DEFAULT {default}"
                cursor.execute(alter_query)
                print(f"✅ تم إضافة {column}")
            else:
                print(f"ℹ️  العمود '{column}' موجود مسبقاً في '{table}'.")
                
        except Exception as e:
            print(f"❌ خطأ أثناء معالجة {table}.{column}: {e}")

    conn.commit()
    conn.close()
    print("\n🎉 تم تحديث هيكلية قاعدة البيانات بنجاح! النظام جاهز.")

if __name__ == "__main__":
    update_database()

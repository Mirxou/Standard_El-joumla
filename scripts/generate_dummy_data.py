#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress Test Script - Generate Dummy Data
سكريبت اختبار الضغط - إنشاء بيانات وهمية ضخمة
"""

import sqlite3
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import random
from typing import List, Tuple

# إضافة مسار src
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

try:
    from faker import Faker
    FAKER_AVAILABLE = True
except ImportError:
    FAKER_AVAILABLE = False
    print("⚠️  Warning: faker library not installed. Install it with: pip install faker")
    print("   Using basic random data instead...")

# إعداد Faker
if FAKER_AVAILABLE:
    fake = Faker(['ar_SA', 'en_US'])  # دعم العربية والإنجليزية
else:
    fake = None


def get_database_path() -> Path:
    """الحصول على مسار قاعدة البيانات"""
    # محاولة استخدام ConfigManager
    try:
        from src.core.config_manager import ConfigManager
        config = ConfigManager()
        db_path = config.get_database_path()
        if db_path and os.path.exists(db_path):
            return Path(db_path)
    except Exception:
        pass
    
    # البحث في المجلدات الشائعة
    possible_paths = [
        project_root / "data" / "logical_release.db",
        project_root / "database.db",
        Path("data/logical_release.db"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    # إنشاء مسار افتراضي
    return project_root / "data" / "logical_release.db"


def get_category_ids(conn: sqlite3.Connection) -> List[int]:
    """الحصول على قائمة معرفات الفئات"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM categories")
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        # إذا لم تكن هناك فئات، إنشاء فئات افتراضية
        default_categories = [
            ("إلكترونيات", "الأجهزة الإلكترونية والكهربائية"),
            ("ملابس", "الملابس والأزياء"),
            ("طعام ومشروبات", "المواد الغذائية والمشروبات"),
            ("كتب وقرطاسية", "الكتب والأدوات المكتبية"),
            ("منزل وحديقة", "أدوات المنزل والحديقة"),
        ]
        for name, desc in default_categories:
            cursor.execute(
                "INSERT INTO categories (name, description, created_at) VALUES (?, ?, ?)",
                (name, desc, datetime.now().isoformat())
            )
        conn.commit()
        cursor.execute("SELECT id FROM categories")
        return [row[0] for row in cursor.fetchall()]


def get_supplier_ids(conn: sqlite3.Connection) -> List[int]:
    """الحصول على قائمة معرفات الموردين"""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM suppliers")
        suppliers = [row[0] for row in cursor.fetchall()]
        if not suppliers:
            # إنشاء موردين وهميين
            suppliers = create_dummy_suppliers(conn, 50)
        return suppliers
    except Exception:
        return create_dummy_suppliers(conn, 50)


def create_dummy_suppliers(conn: sqlite3.Connection, count: int) -> List[int]:
    """إنشاء موردين وهميين"""
    cursor = conn.cursor()
    supplier_ids = []
    
    for _ in range(count):
        if FAKER_AVAILABLE:
            name = fake.company()
            phone = fake.phone_number()
            email = fake.email()
            address = fake.address()
        else:
            name = f"مورد {random.randint(1, 1000)}"
            phone = f"0{random.randint(100000000, 999999999)}"
            email = f"supplier{random.randint(1, 1000)}@example.com"
            address = f"عنوان {random.randint(1, 100)}"
        
        cursor.execute("""
            INSERT INTO suppliers (name, phone, email, address, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, phone, email, address, datetime.now().isoformat()))
        supplier_ids.append(cursor.lastrowid)
    
    conn.commit()
    return supplier_ids


def generate_products(count: int, category_ids: List[int], supplier_ids: List[int]) -> List[Tuple]:
    """إنشاء قائمة منتجات وهمية"""
    products = []
    
    for i in range(count):
        if FAKER_AVAILABLE:
            name = fake.word().capitalize() + " " + fake.word().capitalize()
            barcode = fake.ean13()
            description = fake.text(max_nb_chars=100)
        else:
            name = f"منتج {i+1}"
            barcode = f"{random.randint(1000000000000, 9999999999999)}"
            description = f"وصف المنتج {i+1}"
        
        category_id = random.choice(category_ids) if category_ids else None
        
        # بيانات واقعية
        cost_price = round(random.uniform(10, 1000), 2)
        selling_price = round(cost_price * random.uniform(1.2, 2.5), 2)  # ربح 20-150%
        current_stock = random.randint(0, 500)
        min_stock = random.randint(5, 50)
        
        unit = random.choice(["قطعة", "كيلو", "لتر", "متر", "علبة"])
        
        created_at = datetime.now() - timedelta(days=random.randint(0, 365))
        
        # استخدام بنية الجدول الفعلية
        products.append((
            name, None, barcode, category_id, unit,  # name, name_en, barcode, category_id, unit
            cost_price, selling_price, min_stock, current_stock,  # cost_price, selling_price, min_stock, current_stock
            description, None, 1,  # description, image_path, is_active
            created_at.isoformat(), datetime.now().isoformat()  # created_at, updated_at
        ))
    
    return products


def generate_sales(count: int, product_ids: List[int], conn: sqlite3.Connection) -> int:
    """إنشاء فواتير مبيعات وهمية"""
    cursor = conn.cursor()
    
    # الحصول على معرفات العملاء
    try:
        cursor.execute("SELECT id FROM customers")
        customer_ids = [row[0] for row in cursor.fetchall()]
        if not customer_ids:
            customer_ids = create_dummy_customers(conn, 100)
    except Exception:
        customer_ids = create_dummy_customers(conn, 100)
    
    # الحصول على معرفات المستخدمين
    try:
        cursor.execute("SELECT id FROM users LIMIT 1")
        user_result = cursor.fetchone()
        user_id = user_result[0] if user_result else 1
    except Exception:
        user_id = 1
    
    sales_inserted = 0
    batch_size = 100
    
    for batch_start in range(0, count, batch_size):
        batch_end = min(batch_start + batch_size, count)
        sales_batch = []
        
        for i in range(batch_start, batch_end):
            # تاريخ عشوائي في آخر 6 أشهر
            sale_date = datetime.now() - timedelta(days=random.randint(0, 180))
            
            # حالة عشوائية
            status = random.choice(["مكتمل", "مكتمل", "مكتمل", "مسودة", "ملغية"])  # معظمها مكتمل
            
            # طريقة دفع عشوائية
            payment_method = random.choice(["نقدي", "بطاقة", "تحويل بنكي", "آجل"])
            
            # عميل عشوائي (أو null للزبائن النقديين)
            customer_id = random.choice(customer_ids) if random.random() > 0.3 else None
            
            # حساب المبلغ الإجمالي (سيتم تحديثه بعد إضافة العناصر)
            total_amount = 0.0
            
            # استخدام بنية الجدول الفعلية (customer_id, status, total_amount, created_at, updated_at, meta)
            meta_data = json.dumps({
                "invoice_number": f"INV-{sale_date.strftime('%Y%m%d')}-{i+1:05d}",
                "payment_method": payment_method,
                "user_id": user_id,
                "sale_date": sale_date.isoformat()
            }, ensure_ascii=False)
            
            sales_batch.append((
                customer_id, status, total_amount,
                sale_date.isoformat(), datetime.now().isoformat(), meta_data
            ))
        
        # Bulk insert للفواتير (حسب بنية الجدول الفعلية)
        cursor.executemany("""
            INSERT INTO sales (
                customer_id, status, total_amount,
                created_at, updated_at, meta
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, sales_batch)
        
        # الحصول على معرفات الفواتير المدرجة
        cursor.execute("SELECT id FROM sales ORDER BY id DESC LIMIT ?", (batch_end - batch_start,))
        sale_ids = [row[0] for row in cursor.fetchall()]
        
        # إضافة عناصر الفواتير
        sale_items_batch = []
        for sale_id in sale_ids:
            # عدد العناصر في الفاتورة (1-5 عناصر)
            num_items = random.randint(1, 5)
            sale_total = 0.0
            
            for _ in range(num_items):
                product_id = random.choice(product_ids)
                quantity = random.randint(1, 10)
                
                # الحصول على سعر المنتج (base_price بدلاً من selling_price)
                cursor.execute("SELECT base_price FROM products WHERE id = ?", (product_id,))
                price_result = cursor.fetchone()
                unit_price = price_result[0] if price_result and price_result[0] else random.uniform(10, 500)
                
                subtotal = round(unit_price * quantity, 2)
                sale_total += subtotal
                
                # استخدام بنية sale_items الفعلية (sale_id, product_id, variant_id, quantity, unit_price)
                sale_items_batch.append((
                    sale_id, product_id, None, quantity, unit_price  # variant_id = None
                ))
            
            # تحديث المبلغ الإجمالي للفاتورة (حسب بنية الجدول الفعلية)
            cursor.execute("""
                UPDATE sales 
                SET total_amount = ?, subtotal = ?, final_amount = ?, remaining_amount = ?
                WHERE id = ?
            """, (sale_total, sale_total, sale_total, sale_total, sale_id))
        
        # Bulk insert لعناصر الفواتير (حسب بنية الجدول الفعلية)
        if sale_items_batch:
            cursor.executemany("""
                INSERT INTO sale_items (
                    sale_id, product_id, variant_id, quantity, unit_price
                ) VALUES (?, ?, ?, ?, ?)
            """, sale_items_batch)
        
        conn.commit()
        sales_inserted += len(sales_batch)
        
        # عرض التقدم
        progress = (batch_end / count) * 100
        print(f"   ⏳ Sales: {sales_inserted}/{count} ({progress:.1f}%)", end='\r')
    
    print()  # سطر جديد بعد الانتهاء
    return sales_inserted


def create_dummy_customers(conn: sqlite3.Connection, count: int) -> List[int]:
    """إنشاء عملاء وهميين"""
    cursor = conn.cursor()
    customer_ids = []
    
    for _ in range(count):
        if FAKER_AVAILABLE:
            name = fake.name()
            phone = fake.phone_number()
            email = fake.email()
            city = fake.city()
        else:
            name = f"عميل {random.randint(1, 1000)}"
            phone = f"0{random.randint(100000000, 999999999)}"
            email = f"customer{random.randint(1, 1000)}@example.com"
            city = f"مدينة {random.randint(1, 50)}"
        
        credit_limit = round(random.uniform(1000, 50000), 2)
        current_balance = round(random.uniform(-5000, 10000), 2)
        
        cursor.execute("""
            INSERT INTO customers (
                name, phone, email, city, credit_limit, current_balance, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, phone, email, city, credit_limit, current_balance, datetime.now().isoformat()))
        customer_ids.append(cursor.lastrowid)
    
    conn.commit()
    return customer_ids


def main():
    """الدالة الرئيسية"""
    print("=" * 60)
    print("🔥 Stress Test Script - Generate Dummy Data")
    print("   سكريبت اختبار الضغط - إنشاء بيانات وهمية ضخمة")
    print("=" * 60)
    print()
    
    # الحصول على مسار قاعدة البيانات
    db_path = get_database_path()
    print(f"📁 Database Path: {db_path}")
    
    if not db_path.exists():
        print(f"❌ Error: Database file not found at {db_path}")
        print("   Please run the application first to create the database.")
        return 1
    
    print(f"✅ Database found: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # الاتصال بقاعدة البيانات
    try:
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA journal_mode=WAL")  # تحسين الأداء
        conn.execute("PRAGMA synchronous=NORMAL")  # تحسين السرعة
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return 1
    
    # الحصول على البيانات الأساسية
    print("📋 Preparing data...")
    category_ids = get_category_ids(conn)
    supplier_ids = get_supplier_ids(conn)
    print(f"   ✓ Categories: {len(category_ids)}")
    print(f"   ✓ Suppliers: {len(supplier_ids)}")
    print()
    
    # إنشاء المنتجات
    print("📦 Generating Products...")
    num_products = 50000
    print(f"   Creating {num_products:,} products...")
    
    batch_size = 1000
    product_ids = []
    
    for batch_start in range(0, num_products, batch_size):
        batch_end = min(batch_start + batch_size, num_products)
        products_batch = generate_products(batch_end - batch_start, category_ids, supplier_ids)
        
        # استخدام بنية الجدول الفعلية
        cursor.executemany("""
            INSERT INTO products (
                name, name_en, barcode, category_id, unit,
                cost_price, selling_price, min_stock, current_stock,
                description, image_path, is_active,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, products_batch)
        
        # الحصول على معرفات المنتجات المدرجة
        cursor.execute("SELECT id FROM products ORDER BY id DESC LIMIT ?", (batch_end - batch_start,))
        batch_ids = [row[0] for row in cursor.fetchall()]
        product_ids.extend(batch_ids)
        
        conn.commit()
        
        # عرض التقدم
        progress = (batch_end / num_products) * 100
        print(f"   ⏳ Products: {batch_end:,}/{num_products:,} ({progress:.1f}%)", end='\r')
    
    print()
    print(f"   ✅ Created {len(product_ids):,} products")
    print()
    
    # إنشاء المبيعات
    print("💰 Generating Sales...")
    num_sales = 10000
    print(f"   Creating {num_sales:,} sales records...")
    
    sales_inserted = generate_sales(num_sales, product_ids, conn)
    print(f"   ✅ Created {sales_inserted:,} sales records")
    print()
    
    # إحصائيات نهائية
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sales")
    total_sales = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sale_items")
    total_items = cursor.fetchone()[0]
    
    print("=" * 60)
    print("📊 Final Statistics:")
    print(f"   Products: {total_products:,}")
    print(f"   Sales: {total_sales:,}")
    print(f"   Sale Items: {total_items:,}")
    print(f"   Database Size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
    print("=" * 60)
    print()
    print("✅ Stress test data generation complete!")
    print("🚀 You can now run the app to test performance with massive data.")
    print()
    
    conn.close()
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


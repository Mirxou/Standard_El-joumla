#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
إعداد قاعدة البيانات للمرحلة 5 - Advanced Inventory Management
إنشاء الجداول المطلوبة لإدارة المخزون المتقدمة وتكامل سلاسل التوريد
"""

import sys
from pathlib import Path

# إضافة مسار src
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.database_manager import DatabaseManager

def create_inventory_tables():
    """إنشاء جداول إدارة المخزون المتقدمة"""

    # إنشاء اتصال قاعدة البيانات
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        raise Exception("فشل في تهيئة قاعدة البيانات")

    try:
        # التحقق من وجود الجداول أولاً
        existing_tables_result = db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('advanced_inventory', 'inventory_transactions', 'inventory_alerts', 'inventory_optimizations')"
        )
        existing_table_names = [row[0] for row in existing_tables_result] if existing_tables_result else []

        # جدول المخزون المتقدم
        if 'advanced_inventory' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE advanced_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    batch_id TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_cost DECIMAL(10,2) NOT NULL,
                    expiry_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_id, warehouse_id, batch_id)
                )
            """)

        # جدول معاملات المخزون
        if 'inventory_transactions' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE inventory_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    product_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    batch_id TEXT,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_cost DECIMAL(10,2),
                    reason TEXT,
                    reference_id TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول تنبيهات المخزون
        if 'inventory_alerts' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE inventory_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    product_id INTEGER,
                    warehouse_id INTEGER,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    recommended_action TEXT,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول تحسينات المخزون
        if 'inventory_optimizations' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE inventory_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    current_stock INTEGER NOT NULL,
                    optimal_stock INTEGER NOT NULL,
                    reorder_point INTEGER NOT NULL,
                    safety_stock INTEGER NOT NULL,
                    recommended_action TEXT NOT NULL,
                    expected_savings DECIMAL(10,2) NOT NULL,
                    confidence_score DECIMAL(3,2) NOT NULL,
                    is_implemented BOOLEAN DEFAULT FALSE,
                    implemented_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        print("✅ تم إنشاء جداول إدارة المخزون المتقدمة بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إنشاء جداول المخزون: {e}")
        return False

    return True

def create_supply_chain_tables():
    """إنشاء جداول تكامل سلاسل التوريد"""

    db_manager = DatabaseManager()
    if not db_manager.initialize():
        raise Exception("فشل في تهيئة قاعدة البيانات")

    try:
        # التحقق من وجود الجداول أولاً
        existing_tables_result = db_manager.fetch_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('suppliers', 'purchase_orders', 'purchase_order_items', 'supplier_performance', 'supply_chain_alerts', 'purchase_plans')"
        )
        existing_table_names = [row[0] for row in existing_tables_result] if existing_tables_result else []

        # جدول الموردين
        if 'suppliers' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    contact_person TEXT,
                    email TEXT,
                    phone TEXT,
                    address TEXT,
                    payment_terms TEXT,
                    lead_time_days INTEGER,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول أوامر الشراء
        if 'purchase_orders' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    items TEXT NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    status TEXT DEFAULT 'draft',
                    expected_delivery DATE,
                    actual_delivery DATE,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    received_by INTEGER,
                    received_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول عناصر أوامر الشراء
        if 'purchase_order_items' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE purchase_order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_id TEXT NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10,2) NOT NULL,
                    received_quantity INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    batch_id TEXT,
                    expiry_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول أداء الموردين
        if 'supplier_performance' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE supplier_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    evaluation_date DATE NOT NULL,
                    total_orders INTEGER NOT NULL,
                    total_value DECIMAL(10,2) NOT NULL,
                    on_time_delivery_rate DECIMAL(3,2) NOT NULL,
                    quality_score DECIMAL(3,2) NOT NULL,
                    average_lead_time DECIMAL(5,2) NOT NULL,
                    performance_rating TEXT NOT NULL,
                    last_order_date DATE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(supplier_id, evaluation_date)
                )
            """)

        # جدول تنبيهات سلسلة التوريد
        if 'supply_chain_alerts' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE supply_chain_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    affected_items TEXT,
                    recommended_actions TEXT,
                    is_resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        # جدول خطط المشتريات
        if 'purchase_plans' not in existing_table_names:
            db_manager.execute_query("""
                CREATE TABLE purchase_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT UNIQUE NOT NULL,
                    items TEXT NOT NULL,
                    total_estimated_cost DECIMAL(10,2) NOT NULL,
                    priority_items TEXT,
                    status TEXT DEFAULT 'draft',
                    created_by INTEGER NOT NULL,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    executed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

        print("✅ تم إنشاء جداول تكامل سلاسل التوريد بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إنشاء جداول سلاسل التوريد: {e}")
        return False

    return True

def insert_sample_data():
    """إدراج بيانات تجريبية"""

    db_manager = DatabaseManager()
    if not db_manager.initialize():
        raise Exception("فشل في تهيئة قاعدة البيانات")

    try:
        # إضافة الأعمدة المفقودة للجداول الموجودة
        # إضافة lead_time_days لجدول suppliers إذا لم يكن موجوداً
        supplier_columns = db_manager.fetch_all("PRAGMA table_info(suppliers)")
        supplier_column_names = [col[1] for col in supplier_columns]
        
        if 'lead_time_days' not in supplier_column_names:
            db_manager.execute_non_query("ALTER TABLE suppliers ADD COLUMN lead_time_days INTEGER DEFAULT 7")
        
        if 'status' not in supplier_column_names:
            db_manager.execute_non_query("ALTER TABLE suppliers ADD COLUMN status TEXT DEFAULT 'active'")

        # إضافة الأعمدة المفقودة لجدول products
        product_columns = db_manager.fetch_all("PRAGMA table_info(products)")
        product_column_names = [col[1] for col in product_columns]
        
        if 'category' not in product_column_names:
            db_manager.execute_non_query("ALTER TABLE products ADD COLUMN category TEXT")
        
        if 'min_stock' not in product_column_names:
            db_manager.execute_non_query("ALTER TABLE products ADD COLUMN min_stock INTEGER DEFAULT 0")
        
        if 'max_stock' not in product_column_names:
            db_manager.execute_non_query("ALTER TABLE products ADD COLUMN max_stock INTEGER DEFAULT 1000")

        # التحقق من وجود البيانات أولاً
        existing_suppliers = db_manager.fetch_all("SELECT COUNT(*) FROM suppliers")
        if existing_suppliers and existing_suppliers[0][0] == 0:
            # إدراج موردين تجريبيين
            db_manager.execute_non_query("""
                INSERT INTO suppliers (name, contact_person, email, phone, payment_terms, lead_time_days, status)
                VALUES
                    ('شركة الأدوية المتقدمة', 'أحمد محمد', 'ahmed@pharma.com', '+966501234567', '30 يوم', 7, 'active'),
                    ('مستودعات الدواء المركزية', 'فاطمة علي', 'fatima@medstore.com', '+966507654321', '15 يوم', 5, 'active')
            """)

        # التحقق من وجود مستودعات
        existing_warehouses = db_manager.fetch_all("SELECT COUNT(*) FROM warehouses")
        if existing_warehouses and existing_warehouses[0][0] == 0:
            # إدراج مستودعات تجريبية
            db_manager.execute_non_query("""
                INSERT INTO warehouses (id, name, location, status)
                VALUES
                    (1, 'المستودع الرئيسي', 'الرياض', 'active'),
                    (2, 'مستودع الفرع الشمالي', 'جدة', 'active')
            """)

        # التحقق من وجود منتجات
        existing_products = db_manager.fetch_all("SELECT COUNT(*) FROM products")
        if existing_products and existing_products[0][0] == 0:
            # إدراج منتجات تجريبية
            db_manager.execute_non_query("""
                INSERT INTO products (id, name, description, category, selling_price, min_stock, max_stock)
                VALUES
                    (1, 'أموكسيسيلين 500 مجم', 'مضاد حيوي', 'أدوية', 15.50, 100, 500),
                    (2, 'إيبوبروفين 200 مجم', 'مسكن', 'أدوية', 8.75, 200, 1000)
            """)

        print("✅ تم إدراج البيانات التجريبية بنجاح")

    except Exception as e:
        print(f"❌ خطأ في إدراج البيانات التجريبية: {e}")
        return False

    return True

def run_database_setup():
    """تشغيل إعداد قاعدة البيانات"""

    print("🚀 بدء إعداد قاعدة البيانات للمرحلة 5...")

    success = True

    # إنشاء جداول المخزون
    if not create_inventory_tables():
        success = False

    # إنشاء جداول سلاسل التوريد
    if not create_supply_chain_tables():
        success = False

    # إدراج البيانات التجريبية
    if not insert_sample_data():
        success = False

    if success:
        print("\n🎉 تم إعداد قاعدة البيانات بنجاح للمرحلة 5!")
        print("📋 الجداول المُنشأة:")
        print("   • advanced_inventory - المخزون المتقدم")
        print("   • inventory_transactions - معاملات المخزون")
        print("   • inventory_alerts - تنبيهات المخزون")
        print("   • inventory_optimizations - تحسينات المخزون")
        print("   • suppliers - الموردين")
        print("   • purchase_orders - أوامر الشراء")
        print("   • purchase_order_items - عناصر أوامر الشراء")
        print("   • supplier_performance - أداء الموردين")
        print("   • supply_chain_alerts - تنبيهات سلسلة التوريد")
        print("   • purchase_plans - خطط المشتريات")
    else:
        print("\n❌ فشل في إعداد قاعدة البيانات")

    return success

if __name__ == '__main__':
    success = run_database_setup()
    sys.exit(0 if success else 1)
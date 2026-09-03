#!/usr/bin/env python3
"""
اختبار التحمّل - Load Test
يختبر أداء التطبيق مع حجم بيانات واقعي
"""

import os
import sys
import time
import sqlite3
import random
import string
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

# إضافة src للمسار
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# حجم البيانات
NUM_PRODUCTS = 1000
NUM_CUSTOMERS = 500
NUM_INVOICES = 10000
NUM_PAYMENTS = 50000
NUM_RETURN_INVOICES = 500


class LoadTester:
    """اختبار التحمّل"""
    
    def __init__(self, db_path: str = "load_test.db"):
        self.db_path = db_path
        self.results: List[Dict[str, Any]] = []
        self._conn = None
    
    def setup(self):
        """إعداد قاعدة بيانات الاختبار"""
        # حذف ملف قديم
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA cache_size=10000")
        
        # إنشاء الجداول
        self._create_tables()
        
        print(f"✓ قاعدة بيانات الاختبار جاهزة: {self.db_path}")
    
    def _create_tables(self):
        """إنشاء جداول الاختبار"""
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                sku TEXT UNIQUE,
                category TEXT,
                cost_price REAL DEFAULT 0,
                selling_price REAL DEFAULT 0,
                wholesale_price REAL DEFAULT 0,
                current_stock REAL DEFAULT 0,
                min_stock REAL DEFAULT 5,
                unit TEXT DEFAULT 'unit',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                balance REAL DEFAULT 0,
                credit_limit REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE,
                customer_id INTEGER,
                subtotal REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'confirmed',
                payment_method TEXT DEFAULT 'cash',
                sale_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                product_id INTEGER,
                quantity REAL DEFAULT 1,
                unit_price REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                total_price REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER,
                customer_id INTEGER,
                amount REAL DEFAULT 0,
                payment_method TEXT DEFAULT 'cash',
                payment_date TEXT,
                reference_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
            CREATE INDEX IF NOT EXISTS idx_sales_status ON sales(status);
            CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(sale_date);
            CREATE INDEX IF NOT EXISTS idx_payments_sale ON payments(sale_id);
            CREATE INDEX IF NOT EXISTS idx_payments_customer ON payments(customer_id);
            CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
            CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
        """)
    
    def _generate_name(self, prefix: str = "") -> str:
        """توليد اسم عشوائي"""
        return prefix + ''.join(random.choices(string.ascii_uppercase, k=5)) + ''.join(random.choices(string.digits, k=3))
    
    def test_insert_products(self) -> Dict[str, Any]:
        """اختبار إدراج المنتجات"""
        print(f"\n📦 إدراج {NUM_PRODUCTS} منتج...")
        start = time.time()
        
        categories = ["إلكترونيات", "ملابس", "أغذية", "أدوات", "مواد تنظيف"]
        data = []
        for i in range(NUM_PRODUCTS):
            name = f"منتج-{i+1:05d}"
            sku = f"SKU-{i+1:05d}"
            cat = random.choice(categories)
            cost = round(random.uniform(10, 5000), 2)
            selling = round(cost * random.uniform(1.2, 2.5), 2)
            wholesale = round(cost * random.uniform(1.1, 1.8), 2)
            stock = round(random.uniform(0, 1000), 2)
            data.append((name, sku, cat, cost, selling, wholesale, stock))
        
        self._conn.executemany(
            "INSERT INTO products (name, sku, category, cost_price, selling_price, wholesale_price, current_stock) VALUES (?, ?, ?, ?, ?, ?, ?)",
            data
        )
        self._conn.commit()
        
        elapsed = time.time() - start
        rate = NUM_PRODUCTS / elapsed
        result = {"test": "إدراج المنتجات", "count": NUM_PRODUCTS, "time_s": round(elapsed, 2), "rate_per_s": round(rate, 0)}
        print(f"  ✓ {NUM_PRODUCTS:,} منتج في {elapsed:.2f}s ({rate:,.0f}/s)")
        return result
    
    def test_insert_customers(self) -> Dict[str, Any]:
        """اختبار إدراج العملاء"""
        print(f"\n👥 إدراج {NUM_CUSTOMERS} عميل...")
        start = time.time()
        
        data = []
        for i in range(NUM_CUSTOMERS):
            name = f"عميل-{i+1:04d}"
            phone = f"0{random.choice([5,6,7])}{random.randint(10000000, 99999999)}"
            balance = round(random.uniform(-5000, 50000), 2)
            credit = round(random.uniform(5000, 100000), 2)
            data.append((name, phone, balance, credit))
        
        self._conn.executemany(
            "INSERT INTO customers (name, phone, balance, credit_limit) VALUES (?, ?, ?, ?)",
            data
        )
        self._conn.commit()
        
        elapsed = time.time() - start
        rate = NUM_CUSTOMERS / elapsed
        result = {"test": "إدراج العملاء", "count": NUM_CUSTOMERS, "time_s": round(elapsed, 2), "rate_per_s": round(rate, 0)}
        print(f"  ✓ {NUM_CUSTOMERS:,} عميل في {elapsed:.2f}s ({rate:,.0f}/s)")
        return result
    
    def test_insert_sales(self) -> Dict[str, Any]:
        """اختبار إدراج الفواتير"""
        print(f"\n🧾 إدراج {NUM_INVOICES} فاتورة...")
        start = time.time()
        
        # توليد الفواتير
        statuses = ['confirmed', 'paid', 'partially_paid', 'cancelled', 'returned']
        methods = ['cash', 'card', 'transfer', 'check']
        base_date = datetime(2024, 1, 1)
        
        sales_data = []
        for i in range(NUM_INVOICES):
            inv_num = f"INV-{i+1:06d}"
            cust_id = random.randint(1, NUM_CUSTOMERS)
            subtotal = round(random.uniform(50, 50000), 2)
            discount = round(subtotal * random.uniform(0, 0.15), 2)
            tax = round((subtotal - discount) * 0.19, 2)  # TAP 19%
            total = round(subtotal - discount + tax, 2)
            paid = round(random.uniform(0, total), 2)
            remaining = round(total - paid, 2)
            status = random.choice(statuses)
            method = random.choice(methods)
            days_offset = random.randint(0, 365)
            sale_date = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%d')
            
            sales_data.append((inv_num, cust_id, subtotal, discount, tax, total, paid, remaining, status, method, sale_date))
        
        self._conn.executemany(
            """INSERT INTO sales (invoice_number, customer_id, subtotal, discount_amount, tax_amount, 
               total_amount, paid_amount, remaining_amount, status, payment_method, sale_date) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            sales_data
        )
        self._conn.commit()
        
        elapsed = time.time() - start
        rate = NUM_INVOICES / elapsed
        result = {"test": "إدراج الفواتير", "count": NUM_INVOICES, "time_s": round(elapsed, 2), "rate_per_s": round(rate, 0)}
        print(f"  ✓ {NUM_INVOICES:,} فاتورة في {elapsed:.2f}s ({rate:,.0f}/s)")
        return result
    
    def test_insert_payments(self) -> Dict[str, Any]:
        """اختبار إدراج المدفوعات"""
        print(f"\n💰 إدراج {NUM_PAYMENTS} عملية دفع...")
        start = time.time()
        
        methods = ['cash', 'card', 'transfer', 'check']
        data = []
        for i in range(NUM_PAYMENTS):
            sale_id = random.randint(1, NUM_INVOICES)
            cust_id = random.randint(1, NUM_CUSTOMERS)
            amount = round(random.uniform(10, 10000), 2)
            method = random.choice(methods)
            ref = f"REF-{random.randint(100000, 999999)}"
            pay_date = (datetime(2024,1,1) + timedelta(days=random.randint(0,365))).strftime('%Y-%m-%d')
            data.append((sale_id, cust_id, amount, method, pay_date, ref))
        
        # إدراج على دفعات
        batch_size = 5000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            self._conn.executemany(
                "INSERT INTO payments (sale_id, customer_id, amount, payment_method, payment_date, reference_number) VALUES (?, ?, ?, ?, ?, ?)",
                batch
            )
            self._conn.commit()
        
        elapsed = time.time() - start
        rate = NUM_PAYMENTS / elapsed
        result = {"test": "إدراج المدفوعات", "count": NUM_PAYMENTS, "time_s": round(elapsed, 2), "rate_per_s": round(rate, 0)}
        print(f"  ✓ {NUM_PAYMENTS:,} عملية دفع في {elapsed:.2f}s ({rate:,.0f}/s)")
        return result
    
    def test_query_performance(self) -> List[Dict[str, Any]]:
        """اختبار أداء الاستعلامات"""
        print(f"\n🔍 اختبار أداء الاستعلامات...")
        results = []
        
        queries = [
            ("بحث فاتورة برقمها", "SELECT * FROM sales WHERE invoice_number = ?", (f"INV-{random.randint(1, NUM_INVOICES):06d}",)),
            ("فواتير عميل", "SELECT * FROM sales WHERE customer_id = ? ORDER BY sale_date DESC LIMIT 50", (random.randint(1, NUM_CUSTOMERS),)),
            ("إجمالي مبيعات شهر", "SELECT SUM(total_amount) FROM sales WHERE sale_date BETWEEN '2024-06-01' AND '2024-06-30' AND status != 'cancelled'", ()),
            ("أكثر المنتجات مبيعاً", "SELECT product_id, SUM(quantity) as qty FROM sale_items GROUP BY product_id ORDER BY qty DESC LIMIT 20", ()),
            ("عملاء مع رصيد مستحق", "SELECT id, name, balance FROM customers WHERE balance > 0 ORDER BY balance DESC LIMIT 50", ()),
            ("عدد الفواتير حسب الحالة", "SELECT status, COUNT(*) as cnt FROM sales GROUP BY status", ()),
            ("بحث منتج بالاسم", "SELECT * FROM products WHERE name LIKE ?", (f"%{random.randint(1, NUM_PRODUCTS):05d}%",)),
            ("آخر 100 فاتورة", "SELECT * FROM sales ORDER BY sale_date DESC LIMIT 100", ()),
            ("إجمالي المدفوعات اليوم", "SELECT SUM(amount) FROM payments WHERE payment_date = '2024-06-15'", ()),
            ("منتجات منخفضة المخزون", "SELECT * FROM products WHERE current_stock <= min_stock AND is_active = 1", ()),
        ]
        
        for name, query, params in queries:
            start = time.time()
            try:
                cursor = self._conn.execute(query, params)
                rows = cursor.fetchall()
                elapsed = time.time() - start
                ms = elapsed * 1000
                status = "✓" if ms < 100 else "⚠" if ms < 500 else "✗"
                print(f"  {status} {name}: {ms:.1f}ms ({len(rows)} صف)")
                results.append({"test": f"استعلام: {name}", "time_ms": round(ms, 1), "rows": len(rows), "status": "OK" if ms < 500 else "SLOW"})
            except Exception as e:
                elapsed = time.time() - start
                print(f"  ✗ {name}: خطأ — {e}")
                results.append({"test": f"استعلام: {name}", "time_ms": round(elapsed*1000, 1), "rows": 0, "status": "ERROR"})
        
        return results
    
    def test_db_size(self) -> Dict[str, Any]:
        """فحص حجم قاعدة البيانات"""
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)
        wal_size = 0
        wal_path = self.db_path + "-wal"
        if os.path.exists(wal_path):
            wal_size = os.path.getsize(wal_path) / (1024 * 1024)
        
        print(f"\n💾 حجم قاعدة البيانات: {db_size:.1f} MB (WAL: {wal_size:.1f} MB)")
        
        # فحص سلامة البيانات
        start = time.time()
        result = self._conn.execute("PRAGMA integrity_check").fetchone()
        elapsed = time.time() - start
        
        print(f"  فحص السلامة: {result[0]} ({elapsed*1000:.0f}ms)")
        
        return {"test": "حجم DB", "size_mb": round(db_size, 1), "wal_mb": round(wal_size, 1), "integrity": result[0]}
    
    def run(self):
        """تشغيل كل الاختبارات"""
        print("=" * 60)
        print("اختبار التحمّل — El-Joumla ERP")
        print("=" * 60)
        print(f"المنتجات: {NUM_PRODUCTS:,} | العملاء: {NUM_CUSTOMERS:,}")
        print(f"الفواتير: {NUM_INVOICES:,} | المدفوعات: {NUM_PAYMENTS:,}")
        print("=" * 60)
        
        self.setup()
        
        # إدراج البيانات
        self.results.append(self.test_insert_products())
        self.results.append(self.test_insert_customers())
        self.results.append(self.test_insert_sales())
        self.results.append(self.test_insert_payments())
        
        # أداء الاستعلامات
        self.results.extend(self.test_query_performance())
        
        # حجم DB
        db_info = self.test_db_size()
        self.results.append(db_info)
        
        # ملخص
        print("\n" + "=" * 60)
        print("ملخص النتائج")
        print("=" * 60)
        
        for r in self.results:
            if "time_s" in r:
                print(f"  {r['test']}: {r['count']:,} سجل في {r['time_s']}s ({r['rate_per_s']:,.0f}/s)")
            elif "time_ms" in r:
                print(f"  {r['test']}: {r['time_ms']}ms ({r.get('rows', '?')} صف) [{r.get('status', '?')}]")
            elif "size_mb" in r:
                print(f"  {r['test']}: {r['size_mb']} MB — {r['integrity']}")
        
        # تنظيف
        self._conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        wal = self.db_path + "-wal"
        if os.path.exists(wal):
            os.remove(wal)
        shm = self.db_path + "-shm"
        if os.path.exists(shm):
            os.remove(shm)
        
        print("\n✓ اختبار التحمّل مكتمل")


if __name__ == "__main__":
    tester = LoadTester()
    tester.run()

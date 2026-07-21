# ╔══════════════════════════════════════════════════════════════════╗
# ║  Tests Configuration — Standard El-Joumla ERP                ║
# ║  Aurora Noir v4.0 — Shared Fixtures & Mocks                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
import sqlite3
from typing import Any, Dict, List, Optional

import pytest


@pytest.fixture()
def logger():
    log = logging.getLogger("test_erp")
    log.setLevel(logging.DEBUG)
    return log


class MockDatabaseManager:
    """Mock database manager mimicking LocalDatabaseManager API."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._setup_schema()

    def _setup_schema(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, sku TEXT, barcode TEXT,
                cost_price REAL DEFAULT 0, selling_price REAL DEFAULT 0,
                current_stock REAL DEFAULT 0, min_stock REAL DEFAULT 0,
                category_id INTEGER, is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, phone TEXT, email TEXT, address TEXT,
                balance REAL DEFAULT 0, is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, contact_person TEXT, phone TEXT, email TEXT,
                address TEXT, balance REAL DEFAULT 0, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE, customer_id INTEGER,
                total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0, status TEXT DEFAULT 'PENDING',
                payment_method TEXT, sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
                product_name TEXT, quantity REAL DEFAULT 0,
                unit_price REAL DEFAULT 0, total_price REAL DEFAULT 0,
                cost_price REAL DEFAULT 0,
                FOREIGN KEY (sale_id) REFERENCES sales(id)
            );
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER, status TEXT DEFAULT 'pending',
                total REAL DEFAULT 0, order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_delivery_date TIMESTAMP, delivery_date TIMESTAMP,
                notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER, product_id INTEGER,
                quantity REAL DEFAULT 0, quantity_received REAL DEFAULT 0,
                unit_price REAL DEFAULT 0, actual_delivery_date TIMESTAMP,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id)
            );
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER, movement_type TEXT, quantity REAL,
                reference_id INTEGER, reference_type TEXT, notes TEXT,
                user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_code TEXT UNIQUE NOT NULL, account_name TEXT NOT NULL,
                account_type TEXT NOT NULL, parent_id INTEGER,
                balance REAL DEFAULT 0, is_active INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_number TEXT UNIQUE, description TEXT,
                entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reference_type TEXT, reference_id TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL, account_code TEXT NOT NULL,
                account_name TEXT, debit_amount REAL DEFAULT 0,
                credit_amount REAL DEFAULT 0, description TEXT,
                FOREIGN KEY (entry_id) REFERENCES journal_entries(id)
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER, customer_id INTEGER, amount REAL DEFAULT 0,
                payment_method TEXT, payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT, reference TEXT
            );
            CREATE TABLE IF NOT EXISTS returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE, sale_id INTEGER, customer_id INTEGER,
                total_amount REAL DEFAULT 0, reason TEXT,
                status TEXT DEFAULT 'pending',
                return_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS return_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL, product_id INTEGER,
                product_name TEXT, quantity REAL DEFAULT 0,
                unit_price REAL DEFAULT 0, total_price REAL DEFAULT 0,
                FOREIGN KEY (return_id) REFERENCES returns(id)
            );
            CREATE TABLE IF NOT EXISTS payment_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_number TEXT UNIQUE, customer_id INTEGER,
                total_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0,
                remaining_amount REAL DEFAULT 0, status TEXT DEFAULT 'active',
                start_date TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS installments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL, installment_number INTEGER,
                due_amount REAL DEFAULT 0, paid_amount REAL DEFAULT 0,
                due_date TIMESTAMP, status TEXT DEFAULT 'pending',
                paid_date TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES payment_plans(id)
            );
        """)
        self.conn.commit()

    def execute_query(self, query, params=None):
        cursor = self.conn.execute(query, params or [])
        self.conn.commit()
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query, params=None):
        cursor = self.conn.execute(query, params or [])
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query, params=None):
        cursor = self.conn.execute(query, params or [])
        return [dict(row) for row in cursor.fetchall()]

    def execute_insert(self, query, params=None):
        cursor = self.conn.execute(query, params or [])
        self.conn.commit()
        return cursor.lastrowid

    def execute_non_query(self, query, params=None):
        cursor = self.conn.execute(query, params or [])
        self.conn.commit()
        return cursor.rowcount

    def close(self):
        self.conn.close()

    @property
    def connection(self):
        return self.conn


@pytest.fixture()
def db_manager():
    mgr = MockDatabaseManager()
    yield mgr
    mgr.close()


@pytest.fixture()
def db_manager_with_data(db_manager):
    """Pre-populated with test data."""
    db_manager.execute_insert("INSERT INTO categories (name) VALUES (?)", ("إلكترونيات",))
    db_manager.execute_insert("INSERT INTO categories (name) VALUES (?)", ("أدوات مكتبية",))
    db_manager.execute_insert(
        "INSERT INTO products (name, sku, cost_price, selling_price, current_stock, min_stock) VALUES (?,?,?,?,?,?)",
        ("لابتوب HP", "LP-001", 80000, 120000, 15, 5),
    )
    db_manager.execute_insert(
        "INSERT INTO products (name, sku, cost_price, selling_price, current_stock, min_stock) VALUES (?,?,?,?,?,?)",
        ("طابعة Canon", "PR-001", 25000, 35000, 8, 3),
    )
    db_manager.execute_insert(
        "INSERT INTO products (name, sku, cost_price, selling_price, current_stock, min_stock) VALUES (?,?,?,?,?,?)",
        ("شاشة Samsung", "MN-001", 45000, 65000, 2, 2),
    )
    db_manager.execute_insert(
        "INSERT INTO customers (name, phone, balance) VALUES (?,?,?)",
        ("أحمد بن علي", "0551234567", 5000),
    )
    db_manager.execute_insert(
        "INSERT INTO customers (name, phone, balance) VALUES (?,?,?)",
        ("شركة النور", "0559876543", 0),
    )
    db_manager.execute_insert(
        "INSERT INTO suppliers (name, contact_person, phone) VALUES (?,?,?)",
        ("مؤسسة التقنية", "محمد", "0551112233"),
    )
    for code, name, atype in [
        ("1010", "الصندوق", "asset"), ("1100", "البنك", "asset"),
        ("4001", "المبيعات", "revenue"), ("4100", "المخزون", "asset"),
        ("2100", "الدائنون", "liability"), ("2300", "الضريبة المستحقة", "liability"),
        ("5100", "تكلفة المبيعات", "expense"), ("6000", "مصاريف إدارية", "expense"),
    ]:
        db_manager.execute_insert(
            "INSERT INTO accounts (account_code, account_name, account_type) VALUES (?,?,?)",
            (code, name, atype),
        )
    return db_manager

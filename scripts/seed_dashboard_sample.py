#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seed a small dataset for the dashboard to display KPIs and charts.
- Adds products/customers/suppliers if missing
- Inserts purchases and sales over the last 14 days
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.core.database_manager import DatabaseManager


def ensure_entities(db: DatabaseManager):
    # Products
    products = [
        ("قلم حبر", 3, 10.0, 15.0, 20),
        ("دفتر 100 ورقة", 5, 6.0, 10.0, 50),
        ("دباسة", 3, 12.0, 20.0, 8),
        ("ملف أوراق", 4, 4.0, 7.0, 6),
        ("آلة حاسبة", 2, 25.0, 40.0, 3),
    ]
    for name, min_stock, cost, price, stock in products:
        row = db.fetch_one("SELECT id FROM products WHERE name = ?", (name,))
        if not row:
            db.execute_query(
                """
                INSERT INTO products(name, unit, cost_price, selling_price, min_stock, current_stock, is_active, created_at, updated_at)
                VALUES(?, 'قطعة', ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (name, cost, price, min_stock, stock),
            )

    # Customers
    customers = ["شركة الأفق", "مؤسسة النجاح", "الحدود للتجارة", "الرياض الحديثة", "نور المتحدة"]
    for c in customers:
        row = db.fetch_one("SELECT id FROM customers WHERE name = ?", (c,))
        if not row:
            db.execute_query(
                "INSERT INTO customers(name, current_balance, is_active) VALUES(?, 0, 1)",
                (c,),
            )

    # Suppliers
    suppliers = ["مورد القرطاسية", "مؤسسة الأدوات", "النخبة"]
    for s in suppliers:
        row = db.fetch_one("SELECT id FROM suppliers WHERE name = ?", (s,))
        if not row:
            db.execute_query(
                "INSERT INTO suppliers(name, is_active) VALUES(?, 1)", (s,)
            )


def seed_purchases(db: DatabaseManager, days: int = 14):
    suppliers = db.execute_query("SELECT id, name FROM suppliers")
    products = db.execute_query("SELECT id, name, cost_price FROM products")
    today = date.today()
    for d in range(days):
        purchase_date = today - timedelta(days=d)
        sup = random.choice(suppliers)
        total = 0.0
        # create purchase
        db.execute_query(
            """
            INSERT INTO purchases(invoice_number, supplier_id, total_amount, discount_amount, final_amount, purchase_date)
            VALUES(?, ?, 0, 0, 0, ?)
            """,
            (f"PO-{purchase_date.strftime('%Y%m%d')}-{d:02d}", sup["id"], purchase_date),
        )
        purchase_id = db.get_last_insert_id()
        # add 1-3 items
        for _ in range(random.randint(1, 3)):
            p = random.choice(products)
            qty = random.randint(3, 10)
            unit_cost = float(p["cost_price"]) if p["cost_price"] is not None else 5.0
            total_cost = qty * unit_cost
            db.execute_query(
                """
                INSERT INTO purchase_items(purchase_id, product_id, quantity, unit_cost, total_cost)
                VALUES(?, ?, ?, ?, ?)
                """,
                (purchase_id, p["id"], qty, unit_cost, total_cost),
            )
            total += total_cost
            # increment stock
            db.execute_query(
                "UPDATE products SET current_stock = current_stock + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (qty, p["id"]),
            )
        db.execute_query(
            "UPDATE purchases SET total_amount = ?, final_amount = ? WHERE id = ?",
            (total, total, purchase_id),
        )


def seed_sales(db: DatabaseManager, days: int = 14):
    customers = db.execute_query("SELECT id, name FROM customers")
    products = db.execute_query("SELECT id, name, selling_price, cost_price FROM products")
    today = date.today()
    for d in range(days):
        sale_date = today - timedelta(days=d)
        cust = random.choice(customers)
        # create sale header
        db.execute_query(
            """
            INSERT INTO sales(invoice_number, customer_id, total_amount, discount_amount, final_amount, payment_method, sale_date)
            VALUES(?, ?, 0, 0, 0, 'نقدي', ?)
            """,
            (f"INV-{sale_date.strftime('%Y%m%d')}-{d:02d}", cust["id"], sale_date),
        )
        sale_id = db.get_last_insert_id()
        total = 0.0
        # add 1-3 items
        for _ in range(random.randint(1, 3)):
            p = random.choice(products)
            qty = random.randint(1, 4)
            unit_price = float(p["selling_price"]) if p["selling_price"] is not None else 10.0
            total_price = qty * unit_price
            cost_price = float(p["cost_price"]) if p["cost_price"] is not None else unit_price * 0.6
            profit = total_price - (qty * cost_price)
            # find a batch
            batch = db.fetch_one("SELECT id FROM batches WHERE product_id = ? LIMIT 1", (p["id"],))
            batch_id = batch[0] if batch else None
            if batch_id is None:
                # create a batch
                db.execute_query(
                    """
                    INSERT INTO batches (product_id, batch_number, quantity, cost_price, selling_price)
                    VALUES (?, ?, 0, ?, ?)
                    """,
                    (p["id"], f"auto-{p['id']}", cost_price, unit_price),
                )
                batch_id = db.get_last_insert_id()
            db.execute_query(
                """
                INSERT INTO sale_items(sale_id, product_id, batch_id, quantity, unit_price, total_price, cost_price, profit)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (sale_id, p["id"], batch_id, qty, unit_price, total_price, cost_price, profit),
            )
            total += total_price
            # decrement stock
            db.execute_query(
                "UPDATE products SET current_stock = MAX(current_stock - ?, 0), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (qty, p["id"]),
            )
        db.execute_query(
            "UPDATE sales SET total_amount = ?, final_amount = ? WHERE id = ?",
            (total, total, sale_id),
        )


def main():
    db = DatabaseManager()
    db.initialize()
    ensure_entities(db)
    seed_purchases(db, days=14)
    seed_sales(db, days=14)
    print("Seed completed")


if __name__ == "__main__":
    random.seed(42)
    main()

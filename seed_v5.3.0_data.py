import sqlite3
from datetime import datetime, timedelta
import random

def seed_data():
    db_path = 'data/logical_release.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("Seeding data for v5.3.0 testing...")

    # 1. Create a dummy product
    cur.execute("INSERT INTO products (name, current_stock, min_stock, cost_price, selling_price) VALUES (?, ?, ?, ?, ?)",
                ('Test Product AI', 10, 50, 100, 150))
    pid = cur.lastrowid
    print(f"Created Product ID: {pid}")

    # 2. Insert stock movements (Sales) for AI Forecast
    # Simulate increasing demand
    start_date = datetime.now() - timedelta(days=60)
    for i in range(60):
        date = start_date + timedelta(days=i)
        qty = random.randint(1, 5) + (i // 10) # Increasing trend
        cur.execute("INSERT INTO stock_movements (product_id, movement_type, quantity, created_at) VALUES (?, ?, ?, ?)",
                    (pid, 'بيع', qty, date))
    print("Inserted 60 days of stock movements.")

    # 3. Create a dummy vendor
    cur.execute("INSERT INTO suppliers (name, is_active) VALUES (?, ?)", ('Test Vendor AI', 1))
    vid = cur.lastrowid
    print(f"Created Vendor ID: {vid}")

    # 4. Insert Purchase Orders for Vendor Quality
    # 3 orders: 2 on time, 1 late
    dates = [
        (datetime.now() - timedelta(days=20), datetime.now() - timedelta(days=15), datetime.now() - timedelta(days=15)), # On time (5 days)
        (datetime.now() - timedelta(days=10), datetime.now() - timedelta(days=5), datetime.now() - timedelta(days=5)),   # On time (5 days)
        (datetime.now() - timedelta(days=30), datetime.now() - timedelta(days=20), datetime.now() - timedelta(days=25)), # Late (Expected 25 days ago, arrived 20 days ago -> 5 days late? No, expected at -25, arrived at -20. Late.)
    ]
    
    for order_date, delivery_date, expected_date in dates:
        cur.execute('''
            INSERT INTO purchase_orders 
            (po_number, supplier_id, status, order_date, delivery_date, expected_delivery_date, total_amount) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (f'PO-{random.randint(1000,9999)}', vid, 'received', order_date, delivery_date, expected_date, 1000))
        poid = cur.lastrowid
        
        # Insert item
        cur.execute('''
            INSERT INTO purchase_order_items 
            (purchase_order_id, product_id, product_name, quantity_ordered, quantity_received, unit_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (poid, pid, 'Test Product AI', 10, 10, 100, order_date))

    print("Inserted 3 Purchase Orders.")

    conn.commit()
    conn.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_data()
import sqlite3

conn = sqlite3.connect('data/logical_release.db')
cur = conn.cursor()

# Get all table names with 'sale' in them
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%sale%'")
tables = [row[0] for row in cur.fetchall()]
print("جداول Sales:", tables)

# Check invoices table
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%invoice%'")
invoice_tables = [row[0] for row in cur.fetchall()]
print("جداول Invoices:", invoice_tables)

# Get last 3 invoices
cur.execute("SELECT id, invoice_number, customer_id FROM invoices ORDER BY id DESC LIMIT 3")
print("\nآخر 3 فواتير:")
for row in cur.fetchall():
    print(f"  ID={row[0]}, Invoice={row[1]}, Customer={row[2]}")

conn.close()

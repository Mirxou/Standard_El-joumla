
import sqlite3
import os

db_path = "data/unified_erp.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(ai_models)")
    cols = cursor.fetchall()
    print("ai_models columns:")
    for col in cols:
        print(col)
    conn.close()

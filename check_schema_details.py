import sqlite3

def check_schema():
    conn = sqlite3.connect('data/logical_release.db')
    cur = conn.cursor()
    
    # List all tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables:")
    for t in tables:
        print(f"- {t[0]}")
        
    # Check columns for specific tables
    target_tables = ['products']
    for t in target_tables:
        print(f"\nColumns in {t}:")
        try:
            cur.execute(f"PRAGMA table_info({t})")
            cols = cur.fetchall()
            if cols:
                for c in cols:
                    print(f"  {c[1]} ({c[2]})")
            else:
                print("  (Table not found)")
        except Exception as e:
            print(f"  Error: {e}")

    conn.close()

if __name__ == "__main__":
    check_schema()
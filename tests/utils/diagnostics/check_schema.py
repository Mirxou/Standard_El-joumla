
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), 'data', 'logical_release.db')

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(chart_of_accounts)")
        columns = cursor.fetchall()
        
        if not columns:
            print("Table 'chart_of_accounts' does not exist.")
        else:
            print("Columns in 'chart_of_accounts':")
            for col in columns:
                print(f"- {col[1]} ({col[2]})")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()




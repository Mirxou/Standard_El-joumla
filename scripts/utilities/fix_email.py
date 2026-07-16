import sqlite3
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
DB_PATH = str(project_root / "data" / "standard_eljoumla.db")

try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET email = 'admin@standard.com' WHERE username = 'admin'")
    conn.commit()
    print("✅ updated admin email from 'admin@system.local' to 'admin@standard.com' successfully.")
    
    # Verify
    cursor.execute("SELECT username, email FROM users WHERE username = 'admin'")
    print(f"Current Admin: {cursor.fetchone()}")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")

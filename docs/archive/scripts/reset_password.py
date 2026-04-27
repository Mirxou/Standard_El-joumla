import sys
from pathlib import Path
import hashlib

# Setup path to import src
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService

db_path = project_root / "data" / "logical_release.db"

def reset_admin_password():
    print(f"Connecting to {db_path}...")
    db_manager = DatabaseManager(str(db_path))
    db_manager.initialize()
    cursor = db_manager.connection.cursor()
    
    username = "admin"
    new_password = "123" 
    
    # Initialize security service
    security = AdvancedSecurityService()
    
    # Check if user exists
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        print(f"User '{username}' not found. Creating it...")
        # Create admin user
        hashed = security.hash_password(new_password)
        cursor.execute("INSERT INTO users (username, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, ?)", 
                       (username, hashed, "System Admin", "مدير", 1))
        db_manager.connection.commit()
        print(f"Created user '{username}' with password '{new_password}'")
    else:
        print(f"User '{username}' found. ID: {user[0]}")
        # Reset password
        hashed = security.hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
        db_manager.connection.commit()
        print(f"Reset password for '{username}' to '{new_password}'")
        
    db_manager.connection.close()

if __name__ == "__main__":
    # We need to ensure we can import hash_password. 
    # If src.utils.security is demanding, we might need to mock it or verify imports.
    try:
        reset_admin_password()
    except ImportError as e:
        print(f"Import Error: {e}")
        # Fallback if we can't import the app's hashing function:
        # We'll just define a simple SHA256 or bcrypt if we knew what the app uses.
        # But let's verify verify src/utils/security.py first if this script fails.

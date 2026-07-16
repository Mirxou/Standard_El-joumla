import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from src.core.local_database_manager import LocalDatabaseManager
from src.core.security_service import AdvancedSecurityService
import os

def reset_admin_password():
    # Get password from environment variable or command line argument
    new_password = os.getenv('ADMIN_PASSWORD')
    if not new_password:
        print("❌ Error: Please set ADMIN_PASSWORD environment variable")
        print("   Usage: ADMIN_PASSWORD=your_password python reset_password.py")
        return
    
    if len(new_password) < 8:
        print("❌ Error: Password must be at least 8 characters")
        return
    
    db_manager = LocalDatabaseManager()
    if not db_manager.initialize():
        print("Failed to init DB")
        return

    security_service = AdvancedSecurityService(db_manager)
    
    password_hash = security_service.hash_password(new_password)
    
    # Update DB
    try:
        db_manager.execute_query(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (password_hash,)
        )
        print(f"✅ Password for 'admin' has been reset")
    except Exception as e:
        print(f"❌ Error resetting password: {e}")

if __name__ == "__main__":
    reset_admin_password()
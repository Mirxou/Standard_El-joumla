from src.core.database_manager import DatabaseManager
from src.core.security_service import AdvancedSecurityService

def reset_admin_password():
    db_manager = DatabaseManager()
    if not db_manager.initialize():
        print("Failed to init DB")
        return

    security_service = AdvancedSecurityService(db_manager)
    
    # New password
    new_password = "123456"
    password_hash = security_service.hash_password(new_password)
    
    # Update DB
    try:
        db_manager.execute_query(
            "UPDATE users SET password_hash = ? WHERE username = 'admin'",
            (password_hash,)
        )
        print(f"✅ Password for 'admin' reset to '{new_password}'")
    except Exception as e:
        print(f"❌ Error resetting password: {e}")

if __name__ == "__main__":
    reset_admin_password()

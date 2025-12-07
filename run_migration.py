import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager

def main():
    print("Starting Database Migration...")
    try:
        db = DatabaseManager()
        print(f"Database path: {db.db_path}")
        
        # Initialize triggers check_and_migrate_db because we added the hook
        success = db.initialize()
        
        if success:
            print("✅ Database initialized and migrated successfully.")
            
            # Verify columns
            cols = db._get_table_columns('sales')
            if 'status' in cols:
                print("✅ 'status' column exists in 'sales'.")
            else:
                print("❌ 'status' column MISSING in 'sales'.")
                
            # Verify tables
            try:
                db.execute_query("SELECT count(*) FROM returns")
                print("✅ 'returns' table exists.")
            except Exception as e:
                print(f"❌ 'returns' table check failed: {e}")
                
        else:
            print("❌ Database initialization failed.")
            
    except Exception as e:
        print(f"❌ Error during migration: {e}")

if __name__ == "__main__":
    main()

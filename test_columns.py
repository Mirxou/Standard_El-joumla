#!/usr/bin/env python3
"""
Test script to check database table columns
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.core.database_manager import DatabaseManager
from src.core.config_manager import ConfigManager

# Get database path
config = ConfigManager()
db_path = config.get_database_path()

# Create database manager
db = DatabaseManager(db_path)

# Initialize database connection
db.initialize()

# Check products table columns
print("=" * 50)
print("Products Table Columns:")
print("=" * 50)
cols_info = db.fetch_all("PRAGMA table_info(products)")
if cols_info:
    for row in cols_info:
        col_id, col_name, col_type, not_null, default, pk = row
        print(f"  {col_name:20} - {col_type:10} (pk={pk}, not_null={not_null})")
else:
    print("  No columns found")

print("\n" + "=" * 50)
print("Sample Product Record:")
print("=" * 50)
sample = db.fetch_one("SELECT * FROM products LIMIT 1")
if sample:
    col_names = [row[1] for row in cols_info] if cols_info else []
    for name, value in zip(col_names, sample):
        print(f"  {name:20} = {value}")
else:
    print("  No products in database")

db.close()

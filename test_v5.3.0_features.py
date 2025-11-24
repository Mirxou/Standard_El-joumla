import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.ai_service import AIService
from services.vendor_service import VendorService

class DBManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def execute_query(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        self.conn.commit()
        return cur

    def fetch_all(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def fetch_one(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

def test_features():
    print("Testing v5.3.0 Features...")
    db_path = 'data/logical_release.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    db = DBManager(db_path)
    ai = AIService(db)
    vendor = VendorService(db)

    # 1. Test AI Linear Regression
    print("\n1. Testing AI Linear Regression Forecast...")
    # Find a product with stock movements
    products = db.fetch_all("SELECT DISTINCT product_id FROM stock_movements LIMIT 1")
    if products:
        pid = products[0][0]
        print(f"Forecasting for Product ID: {pid}")
        forecast = ai.demand_forecast_linear_regression(pid, days=90, forecast_days=7)
        for f in forecast:
            print(f"  Date: {f['date']}, Predicted: {f['predicted_quantity']}")
    else:
        print("No products with stock movements found.")

    # 2. Test Vendor Quality Score
    print("\n2. Testing Vendor Quality Score...")
    # Find the seeded vendor
    vendors = db.fetch_all("SELECT id, name FROM suppliers WHERE name = 'Test Vendor AI' LIMIT 1")
    if not vendors:
        vendors = db.fetch_all("SELECT id, name FROM suppliers LIMIT 1")
    
    if vendors:
        vid = vendors[0][0]
        vname = vendors[0][1]
        print(f"Calculating score for Vendor: {vname} (ID={vid})")
        score = vendor.calculate_quality_score(vid)
        print(f"  Quality Score: {score}")
        
        perf = vendor.vendor_performance(vid)
        print(f"  Performance: {perf}")
    else:
        print("No vendors found.")

    # 3. Test Demand Plan
    print("\n3. Testing Demand Plan Generation...")
    plan = vendor.generate_demand_plan(ai, days_ahead=30)
    if plan:
        print(f"Generated Plan with {len(plan)} items:")
        for item in plan[:3]: # Show first 3
            print(f"  Product: {item['product_name']}, Need: {item['suggested_quantity']}, Reason: {item['reason']}")
    else:
        print("No demand plan generated (maybe stock is sufficient).")

if __name__ == "__main__":
    test_features()
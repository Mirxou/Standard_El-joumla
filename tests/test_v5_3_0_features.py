import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime, timedelta

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

    def execute_scalar(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        result = cur.fetchone()
        return result[0] if result else None

    def close(self):
        self.conn.close()

def setup_test_data(db: DBManager):
    print("  Setting up test data...")
    try:
        # Product
        db.execute_query("INSERT OR IGNORE INTO products (id, name, cost_price, selling_price) VALUES (999, 'Test Product Season', 10, 20)")
        # Customer
        db.execute_query("INSERT OR IGNORE INTO customers (id, name) VALUES (999, 'Test Customer Fraud')")
        # Sales for seasonality (higher on weekends)
        for i in range(30):
            day = datetime.now() - timedelta(days=i)
            qty = 10 if day.weekday() >= 5 else 2 # Weekend sales are 5x higher
            db.execute_query("INSERT INTO stock_movements (product_id, movement_type, quantity, created_at) VALUES (?, 'بيع', ?, ?)", (999, qty, day.isoformat()))
        # Sales for fraud
        sale_id = db.execute_query("INSERT INTO sales (id, customer_id, total_amount, status) VALUES (999, 999, 100, 'confirmed')").lastrowid
        db.execute_query("INSERT INTO sale_items (sale_id, product_id, profit) VALUES (?, 999, 10)", (sale_id,))
        # Corresponding refund
        refund_id = db.execute_query("INSERT INTO sales (id, customer_id, total_amount, status, type) VALUES (1000, 999, 100, 'confirmed', 'refund')").lastrowid
        db.execute_query("INSERT INTO sale_items (sale_id, product_id, profit) VALUES (?, 999, -10)", (refund_id,))
        print("  Test data setup complete.")
        return {'sale_id': sale_id, 'refund_id': refund_id}
    except Exception as e:
        print(f"  Error setting up test data: {e}")
        return {}

def cleanup_test_data(db: DBManager):
    print("  Cleaning up test data...")
    db.execute_query("DELETE FROM stock_movements WHERE product_id = 999")
    db.execute_query("DELETE FROM sale_items WHERE sale_id IN (999, 1000)")
    db.execute_query("DELETE FROM sales WHERE id IN (999, 1000)")
    db.execute_query("DELETE FROM products WHERE id = 999")
    db.execute_query("DELETE FROM customers WHERE id = 999")
    print("  Cleanup complete.")

def test_smart_assistant(ai: AIService):
    print("\n4. Testing Smart Assistant...")
    queries = {
        "مبيعات": "get_revenue_summary",
        "مخزون منخفض": "get_low_stock_products",
        "أفضل مبيعات": "get_top_selling_products",
        "invalid query": "unknown"
    }
    for query, expected_intent in queries.items():
        response = ai.smart_assistant_query(query)
        print(f"  Query: '{query}' -> Intent: '{response['intent']}' -> Message: '{response['message']}'")
        assert response['intent'] == expected_intent, f"Failed on query: {query}"
    print("  Smart Assistant test PASSED.")

def test_fraud_flagging(db: DBManager, ai: AIService, test_data: dict):
    print("\n5. Testing Fraud Flagging...")
    if not test_data.get('refund_id'):
        print("  Skipping fraud test due to data setup failure.")
        return

    refund_id = test_data['refund_id']
    
    # Check status before
    status_before = db.execute_scalar("SELECT status FROM sales WHERE id = ?", (refund_id,))
    print(f"  Status of refund sale {refund_id} before: {status_before}")

    # Run fraud detection
    ai.detect_fraud_patterns(days=1)

    # Check status after
    status_after = db.execute_scalar("SELECT status FROM sales WHERE id = ?", (refund_id,))
    print(f"  Status of refund sale {refund_id} after: {status_after}")
    
    assert status_after == 'under_review', "Fraud detection did not flag the sale."
    print("  Fraud Flagging test PASSED.")

def test_seasonality_forecast(ai: AIService):
    print("\n6. Testing Seasonality in Forecast...")
    # Using product 999 which has seasonal data
    forecast = ai.demand_forecast_linear_regression(product_id=999, days=30, forecast_days=7)
    if not forecast:
        print("  Forecast generation failed.")
        return
        
    print("  Forecast results for product 999:")
    weekend_forecast = 0
    weekday_forecast = 0
    for f in forecast:
        day = datetime.fromisoformat(f['date'])
        pred_qty = f['predicted_quantity']
        print(f"    Date: {f['date']} ({day.strftime('%A')}), Predicted: {pred_qty}")
        if day.weekday() >= 5: # Saturday or Sunday
            weekend_forecast += pred_qty
        else:
            weekday_forecast += pred_qty
    
    avg_weekend = weekend_forecast / 2
    avg_weekday = weekday_forecast / 5
    print(f"  Avg Weekend Forecast: {avg_weekend:.2f}, Avg Weekday Forecast: {avg_weekday:.2f}")
    assert avg_weekend > avg_weekday * 1.5, "Forecast does not reflect seasonality."
    print("  Seasonality test PASSED.")

def test_features():
    print("Testing v5.3.0 Features...")
    db_path = 'data/logical_release.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    db = None
    try:
        db = DBManager(db_path)
        ai = AIService(db)
        vendor = VendorService(db)

        # 1. Test AI Linear Regression
        print("\n1. Testing AI Linear Regression Forecast...")
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
            for item in plan[:3]:
                print(f"  Product: {item['product_name']}, Need: {item['suggested_quantity']}, Reason: {item['reason']}")
        else:
            print("No demand plan generated (maybe stock is sufficient).")

        # --- New Tests for v5.3.0 ---
        test_data = setup_test_data(db)
        
        test_smart_assistant(ai)
        test_fraud_flagging(db, ai, test_data)
        test_seasonality_forecast(ai)

    except AssertionError as e:
        print(f"\n--- A test FAILED: {e} ---")
    except Exception as e:
        print(f"\n--- An ERROR occurred: {e} ---")
    finally:
        if db:
            cleanup_test_data(db)
            db.close()


if __name__ == "__main__":
    test_features()
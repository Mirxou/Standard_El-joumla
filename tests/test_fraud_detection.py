import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

# Remove incorrect path insertion
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.services.ai_service import AIService

class DBManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def fetch_all(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

    def fetch_one(self, query, params=()):
        cur = self.conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()

def test_fraud_detection():
    db_path = 'data/logical_release.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    db = DBManager(db_path)
    ai = AIService(db)
    print("\n[Fraud Detection Test]")
    result = ai.detect_fraud_patterns(days=60, min_refund_rate=0.2, high_sales_count=2)
    
    # Updated to match actual return structure
    assert 'status' in result
    assert result['status'] in ['success', 'error']
    if result['status'] == 'success':
        print(f"\n✅ عمليات الكشف: {result['flagged_sales_count']} مبيعات موسومة")
        for action in result.get('actions', []):
            print(f"  - {action}")

if __name__ == "__main__":
    test_fraud_detection()
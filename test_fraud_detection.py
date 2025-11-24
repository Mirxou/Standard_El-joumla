import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.ai_service import AIService

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
    result = ai.detect_fraud_patterns(days=60, min_refund_rate=0.2, min_large_sales=2)
    print("\nمنتجات مشتبه بها (معدل مرتجعات مرتفع):")
    for p in result['suspicious_products']:
        print(f"- {p['product_name']} (مباع: {p['sold_qty']}, مرتجع: {p['refund_qty']}, معدل: {p['refund_rate']})")
    print("\nعملاء مشتبه بهم (مبيعات كبيرة متكررة):")
    for c in result['suspicious_customers']:
        print(f"- {c['customer_name']} (عدد العمليات: {c['sales_count']}, إجمالي: {c['total_sales']})")

if __name__ == "__main__":
    test_fraud_detection()
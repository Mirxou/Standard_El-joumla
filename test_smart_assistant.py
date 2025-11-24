import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from services.smart_assistant import SmartAssistant

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

def test_smart_assistant():
    db_path = 'data/logical_release.db'
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    db = DBManager(db_path)
    sa = SmartAssistant(db)
    print("\n[Smart Assistant Test]")
    questions = [
        "كم مبيعات اليوم؟",
        "ما هي المنتجات منخفضة المخزون؟",
        "أكثر المنتجات مبيعاً",
        "ما هو رصيد العملاء؟",
        "سؤال غير مدعوم"
    ]
    for q in questions:
        print(f"\nQ: {q}")
        print("A:", sa.answer(q))

if __name__ == "__main__":
    test_smart_assistant()
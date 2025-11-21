import os
import tempfile
import sqlite3

from src.core.database_manager import DatabaseManager
from src.services.vendor_rating_service import VendorRatingService, SupplierEvaluation


def setup_temp_db():
    # Use temporary file-based SQLite to persist across connections
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    # Initialize DatabaseManager with this DB file if supported; otherwise, attach
    db = DatabaseManager()
    db.initialize()
    # Ensure supplier and evaluations tables exist via migrations if not already
    con = db.connection
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS suppliers (id INTEGER PRIMARY KEY, name TEXT);")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS supplier_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            supplier_name TEXT,
            evaluation_period_start DATE,
            evaluation_period_end DATE,
            quality_score REAL DEFAULT 0,
            delivery_score REAL DEFAULT 0,
            pricing_score REAL DEFAULT 0,
            communication_score REAL DEFAULT 0,
            reliability_score REAL DEFAULT 0,
            total_orders INTEGER DEFAULT 0,
            completed_orders INTEGER DEFAULT 0,
            on_time_deliveries INTEGER DEFAULT 0,
            late_deliveries INTEGER DEFAULT 0,
            rejected_shipments INTEGER DEFAULT 0,
            total_value REAL DEFAULT 0,
            on_time_delivery_rate REAL DEFAULT 0,
            quality_acceptance_rate REAL DEFAULT 0,
            average_lead_time_days REAL DEFAULT 0,
            overall_score REAL DEFAULT 0,
            grade TEXT,
            is_approved BOOLEAN DEFAULT 1,
            is_preferred BOOLEAN DEFAULT 0,
            notes TEXT,
            recommendations TEXT,
            evaluated_by INTEGER,
            evaluation_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    con.commit()
    return db


def test_create_and_get_supplier_evaluation():
    db = setup_temp_db()
    # Seed supplier
    con = db.connection
    cur = con.cursor()
    cur.execute("INSERT INTO suppliers (name) VALUES ('Test Supplier')")
    supplier_id = cur.lastrowid
    con.commit()

    service = VendorRatingService(db)
    ev = SupplierEvaluation(
        supplier_id=supplier_id,
        supplier_name='Test Supplier',
        quality_score=4.8,
        delivery_score=4.6,
        pricing_score=4.2,
        communication_score=4.7,
        reliability_score=4.9,
    )
    new_id = service.create_evaluation(ev)
    assert isinstance(new_id, int) and new_id > 0

    latest = service.get_latest_evaluation(supplier_id)
    assert latest is not None
    assert latest["supplier_id"] == supplier_id
    assert 0 <= latest["overall_score"] <= 5
    assert latest["grade"] in {"A+","A","B+","B","C","D","F"}

    score = service.get_supplier_score(supplier_id)
    assert score["supplier_id"] == supplier_id
    assert "overall_score" in score and "grade" in score

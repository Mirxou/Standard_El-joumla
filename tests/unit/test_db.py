import os
import sqlite3

import pytest


def _available_db_path():
    """Return the first existing database path among known locations."""
    # Realistic candidate locations inside the repo (under data/)
    candidates = [
        os.path.join("data", "logical_release.db"),
        os.path.join("data", "database.db"),
        os.path.join("data", "erp_system.db"),
    ]
    for p in candidates:
        # Move from tests/unit -> tests -> repo root, then into p
        abs_p = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", p))
        if os.path.exists(abs_p):
            return os.path.abspath(abs_p)
    return None


def test_ai_models_table_exists():
    db_path = _available_db_path()
    if db_path is None:
        pytest.skip("No database file found for ai_models table check.")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="ai_models"')
    result = cur.fetchone()
    assert result is not None, f"ai_models table does not exist in {db_path}"
    conn.close()


def test_ai_models_table_has_columns():
    db_path = _available_db_path()
    if db_path is None:
        pytest.skip("No database file found for ai_models table column check.")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(ai_models)")
    columns = cur.fetchall()
    assert len(columns) > 0, f"ai_models table in {db_path} has no columns"
    conn.close()

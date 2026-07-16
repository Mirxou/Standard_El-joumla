import sqlite3


def test_ai_models_table_inmemory_exists():
    # Create an in-memory DB and define a minimal ai_models table
    conn = sqlite3.connect(":memory:")
    cur = conn.cursor()
    cur.execute("CREATE TABLE ai_models (id INTEGER PRIMARY KEY, name TEXT)")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ai_models'")
    result = cur.fetchone()
    assert result is not None
    cur.execute("PRAGMA table_info(ai_models)")
    columns = cur.fetchall()
    assert len(columns) == 2
    conn.close()

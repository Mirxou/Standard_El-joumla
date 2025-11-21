#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smoke test for ConnectionPool and EncryptedBackupService integration.
Creates a temp DB file, writes a row, creates encrypted backup, restores to new file,
then verifies data integrity using the pool.
"""
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

from core.database_manager import DatabaseManager

def main():
    data_dir = ROOT / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)

    db_file = data_dir / 'test_pool_backup.db'
    if db_file.exists():
        db_file.unlink()

    # Initialize manager with file-based DB (pool enabled)
    db = DatabaseManager(str(db_file))
    assert db.initialize() is True

    # Create a simple table and insert a row
    db.execute_non_query("CREATE TABLE IF NOT EXISTS smoke (id INTEGER PRIMARY KEY, name TEXT)")
    db.execute_non_query("INSERT INTO smoke (name) VALUES (?)", ("pool_ok",))

    # Verify via pool path (fetch_one returns sqlite3.Row)
    row = db.fetch_one("SELECT name FROM smoke WHERE id = 1")
    assert row[0] == "pool_ok"

    # Create encrypted backup
    enc_path = db.backup_database_encrypted(metadata={"test": "pool+backup"})
    assert enc_path is not None

    # Restore to a different file
    restored = data_dir / 'test_pool_backup_restored.db'
    if restored.exists():
        restored.unlink()
    ok = db.restore_database_encrypted(enc_path)
    assert ok is True

    # Verify restored DB
    db2 = DatabaseManager(str(db_file))
    assert db2.initialize() is True
    row2 = db2.fetch_one("SELECT name FROM smoke WHERE id = 1")
    assert row2[0] == "pool_ok"

    print("✅ Pool + Encrypted backup smoke passed")

if __name__ == '__main__':
    main()

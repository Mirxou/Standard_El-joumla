#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Database Backend (SQLiteBackend)
اختبارات Database Backend
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from src.database.sqlite_backend import SQLiteBackend
from src.database.backend import DatabaseBackend


@pytest.fixture(scope="function")
def temp_db_path():
    """مسار قاعدة بيانات مؤقتة"""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_backend.db")
    yield db_path
    # تنظيف
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
    except Exception:
        pass


@pytest.fixture(scope="function")
def sqlite_backend(temp_db_path):
    """SQLiteBackend instance للاختبارات"""
    backend = SQLiteBackend(temp_db_path)
    yield backend
    backend.disconnect()


class TestSQLiteBackend:
    """اختبارات SQLiteBackend"""
    
    def test_sqlite_backend_initialization(self, temp_db_path):
        """اختبار تهيئة SQLiteBackend"""
        backend = SQLiteBackend(temp_db_path)
        assert backend.db_path == temp_db_path
        assert backend.connection is None
        assert backend._in_transaction is False
        assert backend.is_connected is False
    
    def test_sqlite_backend_connect(self, sqlite_backend):
        """اختبار الاتصال الناجح"""
        result = sqlite_backend.connect()
        assert result is True
        assert sqlite_backend.is_connected is True
        assert sqlite_backend.connection is not None
    
    def test_sqlite_backend_connect_creates_file(self, temp_db_path):
        """اختبار إنشاء ملف قاعدة البيانات"""
        backend = SQLiteBackend(temp_db_path)
        assert not os.path.exists(temp_db_path)
        backend.connect()
        assert os.path.exists(temp_db_path)
        backend.disconnect()
    
    def test_sqlite_backend_wal_mode(self, sqlite_backend):
        """اختبار WAL mode"""
        sqlite_backend.connect()
        cursor = sqlite_backend.connection.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        assert result[0].upper() == "WAL"
    
    def test_sqlite_backend_pragma_settings(self, sqlite_backend):
        """اختبار PRAGMA settings"""
        sqlite_backend.connect()
        
        # Foreign keys
        cursor = sqlite_backend.connection.execute("PRAGMA foreign_keys")
        assert cursor.fetchone()[0] == 1
        
        # Synchronous
        cursor = sqlite_backend.connection.execute("PRAGMA synchronous")
        assert cursor.fetchone()[0] == 1  # NORMAL = 1
        
        # Cache size
        cursor = sqlite_backend.connection.execute("PRAGMA cache_size")
        cache_size = cursor.fetchone()[0]
        # SQLite returns positive value for pages (10000 pages = ~40MB with default page size)
        assert cache_size == 10000  # positive means pages
        
        # Temp store
        cursor = sqlite_backend.connection.execute("PRAGMA temp_store")
        assert cursor.fetchone()[0] == 2  # MEMORY = 2
    
    def test_sqlite_backend_is_connected(self, sqlite_backend):
        """اختبار حالة الاتصال"""
        assert sqlite_backend.is_connected is False
        sqlite_backend.connect()
        assert sqlite_backend.is_connected is True
        sqlite_backend.disconnect()
        assert sqlite_backend.is_connected is False
    
    def test_sqlite_backend_disconnect(self, sqlite_backend):
        """اختبار إغلاق الاتصال"""
        sqlite_backend.connect()
        assert sqlite_backend.is_connected is True
        sqlite_backend.disconnect()
        assert sqlite_backend.is_connected is False
        assert sqlite_backend.connection is None
    
    def test_sqlite_backend_execute_query(self, sqlite_backend):
        """اختبار SELECT queries"""
        sqlite_backend.connect()
        
        # إنشاء جدول اختبار
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        sqlite_backend.connection.commit()
        
        # إدراج بيانات
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 123)
        )
        sqlite_backend.connection.commit()
        
        # استعلام
        results = sqlite_backend.execute_query(
            "SELECT * FROM test_table WHERE id = ?",
            (1,)
        )
        
        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["name"] == "test"
        assert results[0]["value"] == 123
    
    def test_sqlite_backend_execute_query_empty_result(self, sqlite_backend):
        """اختبار SELECT بدون نتائج"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (id INTEGER PRIMARY KEY)
        """)
        sqlite_backend.connection.commit()
        
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 0
        assert isinstance(results, list)
    
    def test_sqlite_backend_execute_query_not_connected(self, sqlite_backend):
        """اختبار execute_query بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.execute_query("SELECT 1")
    
    def test_sqlite_backend_execute_insert(self, sqlite_backend):
        """اختبار INSERT وإرجاع last_insert_id"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        last_id = sqlite_backend.execute_insert(
            "INSERT INTO test_table (name) VALUES (?)",
            ("test",)
        )
        
        assert last_id == 1
        
        # التحقق من الإدراج
        results = sqlite_backend.execute_query("SELECT * FROM test_table WHERE id = ?", (1,))
        assert len(results) == 1
        assert results[0]["name"] == "test"
    
    def test_sqlite_backend_execute_insert_multiple(self, sqlite_backend):
        """اختبار INSERT متعدد"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        id1 = sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test1",))
        id2 = sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test2",))
        
        assert id1 == 1
        assert id2 == 2
    
    def test_sqlite_backend_execute_insert_not_connected(self, sqlite_backend):
        """اختبار execute_insert بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.execute_insert("INSERT INTO test VALUES (?)", (1,))
    
    def test_sqlite_backend_execute_update(self, sqlite_backend):
        """اختبار UPDATE"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (id, name) VALUES (?, ?)",
            (1, "old_name")
        )
        sqlite_backend.connection.commit()
        
        rowcount = sqlite_backend.execute_update(
            "UPDATE test_table SET name = ? WHERE id = ?",
            ("new_name", 1)
        )
        
        assert rowcount == 1
        
        # التحقق من التحديث
        results = sqlite_backend.execute_query("SELECT * FROM test_table WHERE id = ?", (1,))
        assert results[0]["name"] == "new_name"
    
    def test_sqlite_backend_execute_update_no_match(self, sqlite_backend):
        """اختبار UPDATE بدون مطابقة"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        rowcount = sqlite_backend.execute_update(
            "UPDATE test_table SET name = ? WHERE id = ?",
            ("new_name", 999)
        )
        
        assert rowcount == 0
    
    def test_sqlite_backend_execute_delete(self, sqlite_backend):
        """اختبار DELETE"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (id, name) VALUES (?, ?), (?, ?)",
            (1, "test1", 2, "test2")
        )
        sqlite_backend.connection.commit()
        
        rowcount = sqlite_backend.execute_update(
            "DELETE FROM test_table WHERE id = ?",
            (1,)
        )
        
        assert rowcount == 1
        
        # التحقق من الحذف
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 1
        assert results[0]["id"] == 2
    
    def test_sqlite_backend_execute_update_not_connected(self, sqlite_backend):
        """اختبار execute_update بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.execute_update("UPDATE test SET name = ?", ("test",))
    
    def test_sqlite_backend_execute_scalar(self, sqlite_backend):
        """اختبار execute_scalar"""
        sqlite_backend.connect()
        
        result = sqlite_backend.execute_scalar("SELECT 42")
        assert result == 42
        
        result = sqlite_backend.execute_scalar("SELECT 'test'")
        assert result == "test"
        
        result = sqlite_backend.execute_scalar("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        assert isinstance(result, int)
    
    def test_sqlite_backend_execute_scalar_empty_result(self, sqlite_backend):
        """اختبار execute_scalar بدون نتائج"""
        sqlite_backend.connect()
        
        result = sqlite_backend.execute_scalar(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='nonexistent'"
        )
        assert result is None
    
    def test_sqlite_backend_execute_scalar_not_connected(self, sqlite_backend):
        """اختبار execute_scalar بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.execute_scalar("SELECT 1")
    
    def test_sqlite_backend_table_exists(self, sqlite_backend):
        """اختبار التحقق من وجود جدول"""
        sqlite_backend.connect()
        
        assert sqlite_backend.table_exists("nonexistent") is False
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (id INTEGER PRIMARY KEY)
        """)
        sqlite_backend.connection.commit()
        
        assert sqlite_backend.table_exists("test_table") is True
    
    def test_sqlite_backend_table_exists_not_connected(self, sqlite_backend):
        """اختبار table_exists بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.table_exists("test")
    
    def test_sqlite_backend_get_last_insert_id(self, sqlite_backend):
        """اختبار get_last_insert_id"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test",))
        last_id = sqlite_backend.get_last_insert_id()
        assert last_id == 1
        
        sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test2",))
        last_id = sqlite_backend.get_last_insert_id()
        assert last_id == 2
    
    def test_sqlite_backend_get_last_insert_id_no_insert(self, sqlite_backend):
        """اختبار get_last_insert_id بدون INSERT"""
        sqlite_backend.connect()
        last_id = sqlite_backend.get_last_insert_id()
        assert last_id == 0
    
    def test_sqlite_backend_get_last_insert_id_not_connected(self, sqlite_backend):
        """اختبار get_last_insert_id بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.get_last_insert_id()
    
    def test_sqlite_backend_begin_transaction(self, sqlite_backend):
        """اختبار بدء transaction"""
        sqlite_backend.connect()
        
        assert sqlite_backend._in_transaction is False
        sqlite_backend.begin_transaction()
        assert sqlite_backend._in_transaction is True
    
    def test_sqlite_backend_begin_transaction_not_connected(self, sqlite_backend):
        """اختبار begin_transaction بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.begin_transaction()
    
    def test_sqlite_backend_commit(self, sqlite_backend):
        """اختبار commit transaction"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.begin_transaction()
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (id, name) VALUES (?, ?)",
            (1, "test")
        )
        sqlite_backend.commit()
        
        assert sqlite_backend._in_transaction is False
        
        # التحقق من أن البيانات تم حفظها
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 1
    
    def test_sqlite_backend_commit_not_connected(self, sqlite_backend):
        """اختبار commit بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.commit()
    
    def test_sqlite_backend_rollback(self, sqlite_backend):
        """اختبار rollback transaction"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.begin_transaction()
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (id, name) VALUES (?, ?)",
            (1, "test")
        )
        sqlite_backend.rollback()
        
        assert sqlite_backend._in_transaction is False
        
        # التحقق من أن البيانات لم يتم حفظها
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 0
    
    def test_sqlite_backend_rollback_not_connected(self, sqlite_backend):
        """اختبار rollback بدون اتصال"""
        with pytest.raises(RuntimeError, match="Database connection not initialized"):
            sqlite_backend.rollback()
    
    def test_sqlite_backend_transaction_context_manager(self, sqlite_backend):
        """اختبار transaction context manager"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        # Transaction ناجح
        with sqlite_backend.transaction():
            sqlite_backend.connection.execute(
                "INSERT INTO test_table (id, name) VALUES (?, ?)",
                (1, "test")
            )
        
        assert sqlite_backend._in_transaction is False
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 1
        
        # Transaction مع rollback
        try:
            with sqlite_backend.transaction():
                sqlite_backend.connection.execute(
                    "INSERT INTO test_table (id, name) VALUES (?, ?)",
                    (2, "test2")
                )
                raise Exception("Test error")
        except Exception:
            pass
        
        assert sqlite_backend._in_transaction is False
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 1  # البيانات الثانية لم يتم حفظها
    
    def test_sqlite_backend_execute_insert_in_transaction(self, sqlite_backend):
        """اختبار INSERT داخل transaction"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.begin_transaction()
        id1 = sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test1",))
        id2 = sqlite_backend.execute_insert("INSERT INTO test_table (name) VALUES (?)", ("test2",))
        sqlite_backend.commit()
        
        assert id1 == 1
        assert id2 == 2
        
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert len(results) == 2
    
    def test_sqlite_backend_get_connection(self, sqlite_backend):
        """اختبار get_connection"""
        assert sqlite_backend.get_connection() is None
        
        sqlite_backend.connect()
        conn = sqlite_backend.get_connection()
        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
    
    def test_sqlite_backend_row_factory(self, sqlite_backend):
        """اختبار Row factory (dict results)"""
        sqlite_backend.connect()
        
        sqlite_backend.connection.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """)
        sqlite_backend.connection.commit()
        
        sqlite_backend.connection.execute(
            "INSERT INTO test_table (id, name, value) VALUES (?, ?, ?)",
            (1, "test", 123)
        )
        sqlite_backend.connection.commit()
        
        results = sqlite_backend.execute_query("SELECT * FROM test_table")
        assert isinstance(results[0], dict)
        assert "id" in results[0]
        assert "name" in results[0]
        assert "value" in results[0]





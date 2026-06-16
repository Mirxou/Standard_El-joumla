#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Database Connection Pool
اختبارات Connection Pool لقاعدة البيانات
"""

import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.database.connection_pool import ConnectionPool, PoolConfig


class TestPoolConfig:
    """اختبارات إعدادات Connection Pool"""

    def test_default_config(self):
        """اختبار الإعدادات الافتراضية"""
        config = PoolConfig()

        assert config.pool_size == 15
        assert config.max_overflow == 30
        assert config.timeout == 60.0
        assert config.health_check_interval == 300

    def test_custom_config(self):
        """اختبار إعدادات مخصصة"""
        config = PoolConfig(pool_size=10, max_overflow=20, timeout=60.0, health_check_interval=600)

        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.timeout == 60.0
        assert config.health_check_interval == 600


class TestConnectionPoolInitialization:
    """اختبارات تهيئة Connection Pool"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        # إنشاء جدول تجريبي
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        yield db_path

        # تنظيف
        Path(db_path).unlink(missing_ok=True)

    def test_pool_initialization(self, temp_db):
        """اختبار تهيئة Connection Pool"""
        config = PoolConfig(pool_size=3, max_overflow=5)
        pool = ConnectionPool(temp_db, config)

        assert pool.database_path == temp_db
        assert pool.config == config

        pool.close()

    def test_pool_stats_initialization(self, temp_db):
        """اختبار تهيئة إحصائيات Pool"""
        config = PoolConfig(pool_size=3, max_overflow=5)
        pool = ConnectionPool(temp_db, config)

        stats = pool.get_stats()

        assert stats["max_pool_size"] == config.pool_size
        assert stats["max_overflow"] == config.max_overflow
        assert stats["total_connections"] == config.pool_size
        assert stats["pool_size"] == config.pool_size
        assert stats["connections_created"] == config.pool_size
        assert stats["checkouts"] == 0
        assert stats["timeouts"] == 0

        pool.close()


class TestConnectionPoolGetConnection:
    """اختبارات الحصول على اتصال من Pool"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def pool(self, temp_db):
        """إنشاء Connection Pool للاختبارات"""
        config = PoolConfig(pool_size=3, max_overflow=2)
        pool = ConnectionPool(temp_db, config)
        yield pool
        pool.close()

    def test_get_connection(self, pool):
        """اختبار الحصول على اتصال"""
        with pool.get_connection() as conn:
            assert conn is not None

    def test_connection_context_manager(self, pool):
        """اختبار استخدام الاتصال كـ context manager"""
        with pool.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1

    def test_connection_reuse(self, pool):
        """اختبار إعادة استخدام الاتصال"""
        with pool.get_connection() as conn1:  # noqa: F841
            pass

        with pool.get_connection() as conn2:  # noqa: F841
            pass

        stats = pool.get_stats()
        assert stats["checkouts"] >= 2
        assert stats["checkins"] >= 1


class TestConnectionPoolExecute:
    """اختبارات تنفيذ الاستعلامات"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        conn.close()

        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def pool(self, temp_db):
        """إنشاء Connection Pool للاختبارات"""
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(temp_db, config)
        yield pool
        pool.close()

    def test_execute_insert(self, pool):
        """اختبار إدراج بيانات"""
        pool.execute("INSERT INTO users (name) VALUES (?)", ("Test User",), fetch_all=False)

        result = pool.execute("SELECT * FROM users WHERE name = ?", ("Test User",))

        assert len(result) == 1
        assert result[0]["name"] == "Test User"

    def test_execute_select(self, pool):
        """اختبار استعلام SELECT"""
        pool.execute("INSERT INTO users (name) VALUES (?)", ("User1",), fetch_all=False)
        pool.execute("INSERT INTO users (name) VALUES (?)", ("User2",), fetch_all=False)

        results = pool.execute("SELECT * FROM users ORDER BY id")

        assert len(results) == 2
        assert results[0]["name"] == "User1"
        assert results[1]["name"] == "User2"

    def test_execute_update(self, pool):
        """اختبار تحديث بيانات"""
        pool.execute("INSERT INTO users (name) VALUES (?)", ("Old Name",), fetch_all=False)

        pool.execute(
            "UPDATE users SET name = ? WHERE name = ?",
            ("New Name", "Old Name"),
            fetch_all=False,
        )

        result = pool.execute("SELECT * FROM users WHERE name = ?", ("New Name",))
        assert len(result) == 1


class TestConnectionPoolTransaction:
    """اختبارات المعاملات (Transactions)"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance REAL)")
        conn.execute("INSERT INTO accounts (balance) VALUES (100.0)")
        conn.execute("INSERT INTO accounts (balance) VALUES (200.0)")
        conn.commit()
        conn.close()

        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def pool(self, temp_db):
        """إنشاء Connection Pool للاختبارات"""
        config = PoolConfig(pool_size=2, isolation_level="DEFERRED")
        pool = ConnectionPool(temp_db, config)
        yield pool
        pool.close()

    def test_successful_transaction(self, pool):
        """اختبار معاملة ناجحة"""
        with pool.transaction() as conn:
            conn.execute("UPDATE accounts SET balance = balance - 50 WHERE id = 1")
            conn.execute("UPDATE accounts SET balance = balance + 50 WHERE id = 2")

        result = pool.execute("SELECT * FROM accounts WHERE id = 1")
        assert result[0]["balance"] == 50.0

        result = pool.execute("SELECT * FROM accounts WHERE id = 2")
        assert result[0]["balance"] == 250.0

    def test_failed_transaction_rollback(self, pool):
        """اختبار التراجع عن المعاملة الفاشلة"""
        try:
            with pool.transaction() as conn:
                conn.execute("UPDATE accounts SET balance = balance - 50 WHERE id = 1")
                # رفع استثناء لإحداث فشل
                raise ValueError("Test error")
        except ValueError:
            pass

        # التحقق من عدم تغير البيانات
        result = pool.execute("SELECT * FROM accounts WHERE id = 1")
        assert result[0]["balance"] == 100.0


class TestConnectionPoolStats:
    """اختبارات إحصائيات Connection Pool"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        yield db_path
        Path(db_path).unlink(missing_ok=True)

    def test_stats_increment_on_get_connection(self, temp_db):
        """اختبار زيادة الإحصائيات عند الحصول على اتصال"""
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(temp_db, config)

        initial_requests = pool.get_stats()["checkouts"]

        with pool.get_connection() as conn:  # noqa: F841
            pass

        stats = pool.get_stats()
        assert stats["checkouts"] == initial_requests + 1

        pool.close()


class TestConnectionPoolClose:
    """اختبارات إغلاق Connection Pool"""

    @pytest.fixture
    def temp_db(self):
        """إنشاء قاعدة بيانات مؤقتة"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        yield db_path
        Path(db_path).unlink(missing_ok=True)

    def test_pool_close(self, temp_db):
        """اختبار إغلاق Connection Pool"""
        config = PoolConfig(pool_size=2)
        pool = ConnectionPool(temp_db, config)

        # الحصول على بعض الاتصالات وإغلاقها
        with pool.get_connection() as conn1:  # noqa: F841
            pass
        with pool.get_connection() as conn2:  # noqa: F841
            pass

        # إغلاق Pool
        pool.close()

        # التحقق من إغلاق جميع الاتصالات
        stats = pool.get_stats()
        assert stats["connections_closed"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

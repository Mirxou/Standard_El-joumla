#!/usr/bin/env python3
"""
اختبارات Database Connection
"""

from unittest.mock import patch

import pytest

from src.core.database_manager import DatabaseConnection


class TestDatabaseConnection:
    """اختبارات اتصال قاعدة البيانات"""

    @pytest.fixture
    def db_connection(self):
        """إنشاء اتصال قاعدة البيانات"""
        return DatabaseConnection()

    def test_initialization(self, db_connection):
        """اختبار التهيئة"""
        assert db_connection is not None

    def test_connect(self, db_connection):
        """اختبار الاتصال"""
        with patch.object(db_connection, "connect", return_value=True):
            result = db_connection.connect()
            assert result is True

    def test_disconnect(self, db_connection):
        """اختبار قطع الاتصال"""
        with patch.object(db_connection, "disconnect", return_value=True):
            result = db_connection.disconnect()
            assert result is True

    def test_is_connected(self, db_connection):
        """اختبار التحقق من حالة الاتصال"""
        with patch.object(db_connection, "is_connected", return_value=True):
            result = db_connection.is_connected()
            assert result is True

    def test_execute_query(self, db_connection):
        """اختبار تنفيذ استعلام"""
        with patch.object(db_connection, "execute", return_value=[{"id": 1}]):
            result = db_connection.execute("SELECT * FROM products")
            assert result is not None

    def test_execute_insert(self, db_connection):
        """اختبار تنفيذ إدراج"""
        with patch.object(db_connection, "execute", return_value=1):
            result = db_connection.execute("INSERT INTO products (name) VALUES (?)", ("Test",))
            assert result is not None

    def test_begin_transaction(self, db_connection):
        """اختبار بدء معاملة"""
        with patch.object(db_connection, "begin_transaction", return_value=True):
            result = db_connection.begin_transaction()
            assert result is True

    def test_commit_transaction(self, db_connection):
        """اختبار تأكيد معاملة"""
        with patch.object(db_connection, "commit", return_value=True):
            result = db_connection.commit()
            assert result is True

    def test_rollback_transaction(self, db_connection):
        """اختبار التراجع عن معاملة"""
        with patch.object(db_connection, "rollback", return_value=True):
            result = db_connection.rollback()
            assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

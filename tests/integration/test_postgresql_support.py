import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock psycopg2 before importing modules that use it
sys.modules["psycopg2"] = MagicMock()
sys.modules["psycopg2.pool"] = MagicMock()
sys.modules["psycopg2.extras"] = MagicMock()

import importlib

import src.core.database_manager
from src.database.postgresql_backend import PostgreSQLBackend

importlib.reload(src.core.database_manager)
from src.core.database_manager import ConnectionPool, PoolConfig


class TestPostgreSQLSupport:

    def test_backend_initialization(self):
        backend = PostgreSQLBackend("postgresql://user:pass@localhost/db")
        assert backend.db_url == "postgresql://user:pass@localhost/db"
        assert backend.is_connected is False

    @patch("src.database.postgresql_backend.psycopg2")
    def test_backend_connect(self, mock_pg):
        # Configure the mock connection to have .closed = 0
        mock_conn = MagicMock()
        mock_conn.closed = 0
        mock_pg.connect.return_value = mock_conn

        backend = PostgreSQLBackend("dummy_url")
        backend.connect()

        mock_pg.connect.assert_called_with("dummy_url")
        assert backend.is_connected is True

    @patch("src.core.database_manager.pg_pool")
    def test_pool_initialization_postgres(self, mock_pg_pool):
        # Setup config for Postgres
        config = PoolConfig(
            db_type="postgres",
            pool_size=5,
            postgres_config={"application_name": "test"},
        )

        # Initialize pool
        pool = ConnectionPool("dummy_path", config)  # noqa: F841

        # Verify ThreadedConnectionPool was initialized
        mock_pg_pool.ThreadedConnectionPool.assert_called_once()
        call_kwargs = mock_pg_pool.ThreadedConnectionPool.call_args[1]
        assert call_kwargs["minconn"] == 1
        assert call_kwargs["maxconn"] == 5
        assert call_kwargs["application_name"] == "test"

    @patch("src.core.database_manager.sqlite3")
    def test_pool_initialization_sqlite_default(self, mock_sqlite):
        # Default config is sqlite
        pool = ConnectionPool(":memory:")

        # Verify sqlite connection created (called loop times)
        assert mock_sqlite.connect.called
        assert pool.config.db_type == "sqlite"

    @patch("src.core.database_manager.pg_pool")
    def test_pool_get_connection_postgres(self, mock_pg_pool):
        # Setup mock pool instance
        mock_pool_instance = MagicMock()
        mock_pg_pool.ThreadedConnectionPool.return_value = mock_pool_instance
        mock_conn = MagicMock()
        mock_pool_instance.getconn.return_value = mock_conn

        config = PoolConfig(db_type="postgres")
        pool = ConnectionPool("dummy", config)

        # Test usage
        with pool.get_connection() as conn:
            assert conn == mock_conn

        # Verify putconn called
        mock_pool_instance.putconn.assert_called_with(mock_conn)

    @patch("src.core.database_manager.pg_pool")
    def test_pool_execute_postgres_placeholder_replacement(self, mock_pg_pool):
        # Setup mock
        mock_pool_instance = MagicMock()
        mock_pg_pool.ThreadedConnectionPool.return_value = mock_pool_instance
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_pool_instance.getconn.return_value = mock_conn

        config = PoolConfig(db_type="postgres")
        pool = ConnectionPool("dummy", config)

        # Execute query with SQLite style placeholder
        pool.execute("SELECT * FROM table WHERE id = ?", (1,))

        # Verify replacment to %s
        mock_cursor.execute.assert_called_with("SELECT * FROM table WHERE id = %s", (1,))


if __name__ == "__main__":
    pytest.main([__file__])

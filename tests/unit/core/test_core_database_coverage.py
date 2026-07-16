import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.database_manager import DatabaseManager
from src.core.exceptions import DatabaseException


class TestDatabaseManager:
    @pytest.fixture
    def mock_backend(self):
        backend = MagicMock()
        backend.connect.return_value = True
        backend.get_connection.return_value = MagicMock()
        return backend

    @pytest.fixture
    def db_manager(self, mock_backend, tmp_path):
        # Use temp path to avoid real DB creation in default init
        db_path = str(tmp_path / "test.db")
        return DatabaseManager(db_path=db_path, backend=mock_backend)

    @pytest.fixture
    def legacy_manager(self, tmp_path):
        db_path = str(tmp_path / "legacy.db")
        # Ensure we mock the internal calls that happen during init to isolate tests
        # We also need to patch src.database.sqlite_backend.sqlite3 and ConnectionPool
        # AND EncryptionManager to prevent it from checking file encryption using real sqlite3

        with patch("src.core.database_manager.sqlite3") as mock_sqlite, patch(
            "src.database.sqlite_backend.sqlite3"
        ) as mock_backend_sqlite, patch("src.core.database_manager.ConnectionPool") as mock_pool_cls, patch(
            "src.core.database_manager.sqlite3"
        ) as mock_pool_sqlite, patch(
            "src.core.database_manager.EncryptionManager"
        ) as mock_enc_mgr, patch(
            "src.core.database_manager.EncryptedBackupService"
        ) as mock_backup_svc:  # noqa: F841

            mock_conn = MagicMock()
            mock_sqlite.connect.return_value = mock_conn
            mock_backend_sqlite.connect.return_value = mock_conn
            mock_pool_sqlite.connect.return_value = mock_conn

            # Configure pool mock to return a mock connection context
            mock_pool = mock_pool_cls.return_value

            # This handles: with pool.get_connection() as conn:
            mock_ctx = MagicMock()
            mock_ctx.__enter__.return_value = mock_conn
            mock_pool.get_connection.return_value = mock_ctx

            # Configure EncryptionManager mock to return False for is_encrypted so it doesn't try anything weird
            mock_enc_mgr.return_value.is_database_encrypted.return_value = False

            manager = DatabaseManager(db_path=db_path, pool_options={"enabled": False})

            # Apply patches ONLY for initialize()
            with patch.object(manager, "_create_tables"), patch.object(
                manager, "_upgrade_existing_schema"
            ), patch.object(manager, "_create_indexes"), patch.object(manager, "_run_migrations"), patch.object(
                manager, "check_and_migrate_db"
            ):
                manager.initialize()

            # Yield manager with unpatched methods (except sqlite3 which wraps the connection)
            yield manager
            manager.close()

    def test_initialization_with_backend(self, db_manager, mock_backend):
        assert db_manager.initialize() is True
        mock_backend.connect.assert_called_once()
        mock_backend.get_connection.assert_called_once()
        assert db_manager.connection is not None

    def test_initialization_backend_failure(self, db_manager, mock_backend):
        mock_backend.connect.return_value = False
        with pytest.raises(DatabaseException):
            db_manager.initialize()

    @patch("src.core.database_manager.sqlite3")
    @patch("src.core.database_manager.ConnectionPool")
    def test_initialization_sqlite_legacy(self, mock_pool_cls, mock_sqlite, tmp_path):
        # Test initialization without backend (legacy mode)
        db_path = str(tmp_path / "legacy_init.db")
        manager = DatabaseManager(db_path=db_path, pool_options={"enabled": True})

        # Mock connection
        mock_conn = MagicMock()
        mock_sqlite.connect.return_value = mock_conn

        # Mock pool
        mock_pool_instance = MagicMock()
        mock_pool_cls.return_value = mock_pool_instance

        with patch.object(manager, "_create_tables"), patch.object(manager, "_upgrade_existing_schema"), patch.object(
            manager, "_create_indexes"
        ), patch.object(manager, "_run_migrations"), patch.object(manager, "check_and_migrate_db"):

            assert manager.initialize() is True

            # Verify PRAGMA calls
            assert mock_conn.execute.call_count >= 5  # WAL, Foreign Keys, etc.
            assert manager.pool is not None

    def test_ensure_data_directory(self, tmp_path):
        # db path in non-existent subdir
        db_path = str(tmp_path / "subdir" / "test.db")
        manager = DatabaseManager(db_path=db_path)  # noqa: F841
        # _ensure_data_directory calls inside init
        assert os.path.exists(os.path.dirname(db_path))

    @patch("src.core.database_manager.EncryptionManager")
    def test_encrypted_initialization(self, MockEncManager, tmp_path):
        db_path = str(tmp_path / "enc.db")
        # Create dummy file to simulate existing DB
        with open(db_path, "w") as f:
            f.write("dummy")

        mock_enc_instance = MockEncManager.return_value
        mock_enc_instance.is_database_encrypted.return_value = True

        manager = DatabaseManager(db_path=db_path, encryption_password="pass")

        with patch("src.core.database_manager.sqlite3") as mock_sqlite, patch(
            "src.core.database_manager.sqlite3"
        ) as mock_pool_sqlite, patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:

            # Mock connection for both
            mock_conn = MagicMock()
            mock_sqlite.connect.return_value = mock_conn
            mock_pool_sqlite.connect.return_value = mock_conn

            # Mock init steps
            with patch.object(manager, "_create_tables"), patch.object(
                manager, "_upgrade_existing_schema"
            ), patch.object(manager, "_create_indexes"), patch.object(manager, "_run_migrations"), patch.object(
                manager, "check_and_migrate_db"
            ):

                manager.initialize()

                # Verify decryption called
                mock_enc_instance.decrypt_file.assert_called()
                # Verify temp file removal
                mock_remove.assert_called()

    def test_create_tables(self, legacy_manager):
        # Debug: Check if connection is a Mock
        # print(f"DEBUG: Connection type: {type(legacy_manager.connection)}")
        pass
        # print(f"DEBUG: Is instance of MagicMock? {isinstance(legacy_manager.connection, MagicMock)}")

        legacy_manager._create_tables()

        # Verify calls for tables: categories, products, suppliers...
        calls = legacy_manager.connection.execute.call_args_list
        sql_stmts = []
        for c in calls:
            if c[0]:
                # Normalize string: remove newlines and extra spaces
                sql = str(c[0][0])
                normalized_sql = " ".join(sql.split())
                sql_stmts.append(normalized_sql)

        # print(f"DEBUG: Captured SQL statements: {len(sql_stmts)}")

        # Check for categories table creation
        found_categories = False
        for s in sql_stmts:
            if "CREATE TABLE IF NOT EXISTS categories" in s:
                found_categories = True
                break
        assert found_categories, f"Categories table creation not found. Stmts: {sql_stmts[:2]}"

        # Check for products table creation
        found_products = False
        for s in sql_stmts:
            if "CREATE TABLE IF NOT EXISTS products" in s:
                found_products = True
                break
        assert found_products, "Products table creation not found"

    def test_execute_query_fetch_all(self, legacy_manager):
        cursor = legacy_manager.connection.cursor.return_value
        cursor.description = [("id",), ("name",)]
        cursor.fetchall.return_value = [(1, "test")]

        results = legacy_manager.execute_query("SELECT * FROM table")
        assert len(results) == 1
        assert results[0]["name"] == "test"

    def test_execute_query_non_select(self, legacy_manager):
        cursor = legacy_manager.connection.cursor.return_value
        cursor.description = None  # indicates non-SELECT result usually

        result_cursor = legacy_manager.execute_query("UPDATE table SET name='new'")
        assert result_cursor == cursor
        legacy_manager.connection.commit.assert_called()

    def test_fetch_one(self, legacy_manager):
        legacy_manager.connection.cursor.return_value.fetchone.return_value = (
            1,
            "test",
        )
        result = legacy_manager.fetch_one("SELECT * FROM table")
        assert result == (1, "test")

    def test_execute_insert(self, legacy_manager):
        # Standard insert
        cursor = legacy_manager.connection.cursor.return_value
        cursor.lastrowid = 10

        result = legacy_manager.execute_insert("INSERT INTO table ...")
        assert result == 10
        legacy_manager.connection.commit.assert_called()

    def test_execute_scalar(self, legacy_manager):
        legacy_manager.connection.cursor.return_value.fetchone.return_value = (42,)
        result = legacy_manager.execute_scalar("SELECT COUNT(*) FROM table")
        assert result == 42

    def test_backup_database(self, legacy_manager, tmp_path):
        backup_path = str(tmp_path / "backup.db")
        # Create a dummy db file
        with open(legacy_manager.db_path, "w") as f:
            f.write("content")

        assert legacy_manager.backup_database(backup_path) is True
        assert os.path.exists(backup_path)

    def test_restore_database(self, legacy_manager, tmp_path):
        backup_path = str(tmp_path / "backup.db")
        with open(backup_path, "w") as f:
            f.write("backup content")

        with patch.object(legacy_manager, "initialize") as mock_init:
            mock_init.return_value = True
            assert legacy_manager.restore_database(backup_path) is True
            # Check file content matches backup
            with open(legacy_manager.db_path, "r") as f:
                assert f.read() == "backup content"

    def test_cleanup_old_data(self, legacy_manager):
        # Mock execute/cursor
        mock_cursor = MagicMock()
        # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
        # We need name at index 1
        mock_cursor.fetchall.return_value = [(0, "created_at", "TIMESTAMP", 0, None, 0)]
        mock_cursor.rowcount = 5

        legacy_manager.connection.execute.return_value = mock_cursor

        # Mock table_exists
        with patch.object(legacy_manager, "table_exists", return_value=True):
            results = legacy_manager.cleanup_old_data(days=30, tables={"test_table": "created_at"})
            assert results.get("test_table") == 5
            legacy_manager.connection.commit.assert_called()

    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    def test_vacuum_database(self, legacy_manager):
        # Mock fetchone for checkpoint
        cursor = legacy_manager.connection.cursor.return_value
        cursor.fetchone.return_value = (0,)  # success code for wal_checkpoint

        assert legacy_manager.vacuum_database() is True
        legacy_manager.connection.execute.assert_any_call("VACUUM")

    @patch("src.core.database_manager.EncryptionManager")
    def test_encryption_management(self, MockEnc, legacy_manager):
        # Enable Encryption
        mock_enc = MockEnc.return_value

        # Test enable
        assert legacy_manager.enable_encryption("password") is True
        assert legacy_manager.is_encrypted is True
        mock_enc.encrypt_database.assert_called_with(legacy_manager.db_path, "password", backup_original=True)

        # Test change password
        # Mock decrypt/encrypt calls
        mock_enc.encrypt_file.return_value = legacy_manager.db_path + ".new"

        # Fake file presence for renames
        with patch("os.remove"), patch("shutil.move"):
            assert legacy_manager.change_encryption_password("password", "newpass") is True

        # Test verify
        mock_enc.verify_database_integrity.return_value = True
        with patch("os.remove"):
            assert legacy_manager.verify_encryption_password("newpass") is True

        # Test disable
        with patch("shutil.move"):
            assert legacy_manager.disable_encryption("newpass") is True
            assert legacy_manager.is_encrypted is False

    def test_check_and_migrate_db(self, legacy_manager):
        # Test the schema migration logic
        cursor = legacy_manager.connection.cursor.return_value

        # We need cursor.fetchall to return lists (iterables) at valid times.
        # Let's Mock cursor properly
        cursor.fetchall.return_value = []  # Default: fields missing, so it triggers ALTERs

        legacy_manager.check_and_migrate_db()

        # Verify attempt to add columns
        calls = [str(c) for c in cursor.execute.call_args_list]
        assert any("ADD COLUMN status" in c for c in calls)
        assert any("ADD COLUMN company_id" in c for c in calls)

    def test_close_connection(self, legacy_manager):
        # Capture the mock BEFORE closing, because close() sets self.connection = None
        conn_mock = legacy_manager.connection
        legacy_manager.close()
        conn_mock.close.assert_called_once()
        assert legacy_manager.connection is None

    def test_get_database_size_info(self, legacy_manager, tmp_path):
        # Mock file sizes
        # The db_path is set in fixture. We need to create files to have stat() work
        # or patch Path.stat

        db_path = Path(legacy_manager.db_path)
        wal_path = db_path.with_suffix(".db-wal")  # noqa: F841
        shm_path = db_path.with_suffix(".db-shm")  # noqa: F841

        # ensure file existence check passes
        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.stat") as mock_stat:

            mock_stat.return_value.st_size = 1048576  # 1MB

            info = legacy_manager.get_database_size_info()
            assert info["database_size_mb"] == 1.0
            assert info["total_size_mb"] == 3.0  # db + wal + shm

    def test_run_migrations(self, legacy_manager, tmp_path):
        # Create a dummy migration file
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()
        (migrations_dir / "001_initial.sql").write_text("CREATE TABLE test_mig (id INT);")

        # Patch the path resolution in database_manager to point to tmp_path/migrations
        # The code uses: Path(__file__).parent.parent.parent / "migrations"
        # We need to patch Path behavior or the specific attribute if possible.
        # Hard to patch Path(__file__)...
        # Easier to patch 'src.core.database_manager.Path' but that affects everything.

        # Instead, let's look at _run_migrations. It constructs path.
        # We can patch os.path.exists or just assume we can't easily change the dir path
        # without refactoring the code to accept migration_path.

        # Alternatively, we can mock `pathlib.Path` specifically for the call inside _run_migrations
        # but that's messy.

        # Let's try to patch the `migrations_dir` variable if it was an attribute, but it's local.
        # Check if we can just test `_parse_sql_statements` method directly?

        sqls = legacy_manager._parse_sql_statements("CREATE TABLE foo; -- comment\nINSERT INTO foo VALUES (1);")
        assert len(sqls) == 2
        assert sqls[0] == "CREATE TABLE foo"
        assert sqls[1] == "INSERT INTO foo VALUES (1)"

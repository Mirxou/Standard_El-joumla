import logging
# ... (Header remains)
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from queue import Empty, Full, Queue
from typing import Any, Dict, Optional

from src.utils.logger import setup_logger

# Optional import for psycopg2
try:
    from psycopg2 import pool as pg_pool

    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False


@dataclass
class PoolConfig:
    """تكوين Connection Pool"""

    # حجم Pool (موسّع للتعامل مع 200K+ منتج)
    pool_size: int = 15
    max_overflow: int = 30

    # المهلات الزمنية
    timeout: float = 60.0
    recycle: int = 3600

    # إعدادات SQLite
    check_same_thread: bool = False
    isolation_level: Optional[str] = None  # None = autocommit

    # إعدادات PostgreSQL
    db_type: str = "sqlite"  # 'sqlite' or 'postgres'
    postgres_config: Optional[Dict[str, Any]] = None

    # الصيانة
    enable_health_check: bool = True
    health_check_interval: int = 300


class PooledConnection:
    """
    اتصال في Pool (SQLite only wrapper)
    """

    def __init__(self, connection: Any, pool: "ConnectionPool"):
        self.connection = connection
        self.pool = pool
        self.created_at = time.time()
        self.last_used = time.time()
        self.in_use = False
        self.uses = 0

    def is_expired(self, recycle_time: int) -> bool:
        age = time.time() - self.created_at
        return age > recycle_time

    def mark_used(self) -> None:
        self.in_use = True
        self.last_used = time.time()
        self.uses += 1

    def mark_returned(self) -> None:
        self.in_use = False

    def is_healthy(self) -> bool:
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            logging.getLogger(__name__).warning("Ignored exception in connection_pool.py")


class ConnectionPool:
    """
    Connection Pool يدعم SQLite و PostgreSQL
    """

    def __init__(self, database_path: str, config: Optional[PoolConfig] = None):
        self.database_path = database_path
        self.config = config or PoolConfig()

        # تهيئة logger
        self.logger = setup_logger(__name__)

        self.is_closed = False
        self.lock = threading.RLock()

        # إحصائيات
        self.stats = {
            "connections_created": 0,
            "connections_closed": 0,
            "overflow_created": 0,
            "checkouts": 0,
            "checkins": 0,
            "timeouts": 0,
            "health_checks": 0,
            "recycled": 0,
        }

        # PostgreSQL Pool
        self.pg_connection_pool = None

        # SQLite Pool components
        self.pool: Queue[PooledConnection] = Queue(maxsize=self.config.pool_size)
        self.all_connections: list[PooledConnection] = []
        self.overflow_connections: list[PooledConnection] = []

        if self.config.db_type == "postgres":
            if not HAS_POSTGRES:
                raise ImportError("psycopg2 is required for PostgreSQL support but not installed.")
            self._initialize_postgres_pool()
        else:
            # SQLite initialization
            self._initialize_sqlite_pool()

            # Start maintenance thread only for SQLite manual pool
            if self.config.enable_health_check:
                self._start_maintenance_thread()

    def _initialize_postgres_pool(self):
        """تهيئة pool للـ PostgreSQL"""
        try:
            pg_conf = self.config.postgres_config or {}
            # Use ThreadedConnectionPool
            self.pg_connection_pool = pg_pool.ThreadedConnectionPool(
                minconn=1, maxconn=self.config.pool_size, **pg_conf
            )
            self.logger.info("تم تهيئة PostgreSQL Connection Pool بنجاح")
        except Exception as e:
            self.logger.error(f"فشل تهيئة PostgreSQL Pool: {e}")
            raise

    def _initialize_sqlite_pool(self) -> None:
        """إنشاء الاتصالات الأولية لـ SQLite"""
        for _ in range(self.config.pool_size):
            conn = self._create_sqlite_connection()
            if conn:
                self.pool.put(conn)

    def _create_sqlite_connection(self) -> Optional[PooledConnection]:
        """إنشاء اتصال SQLite جديد"""
        try:
            connection = sqlite3.connect(
                self.database_path,
                check_same_thread=self.config.check_same_thread,
                isolation_level=self.config.isolation_level,
                timeout=self.config.timeout,
            )

            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA cache_size=10000")
            connection.execute("PRAGMA temp_store=MEMORY")

            connection.row_factory = sqlite3.Row

            pooled = PooledConnection(connection, self)

            with self.lock:
                self.all_connections.append(pooled)
                self.stats["connections_created"] += 1

            return pooled

        except Exception as e:
            self.logger.error(f"فشل إنشاء اتصال SQLite: {e}", exc_info=True)
            try:
                if "connection" in locals():
                    connection.close()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in connection_pool.py")
            return None

    def _create_overflow_connection(self) -> Optional[PooledConnection]:
        """إنشاء اتصال overflow مؤقت (SQLite only)"""
        if self.config.db_type == "postgres":
            return None  # Postgres pool handles overflow internally (kinda) or blocks

        with self.lock:
            current_overflow = len(self.overflow_connections)
            if current_overflow >= self.config.max_overflow:
                return None

            conn = self._create_sqlite_connection()
            if conn:
                self.overflow_connections.append(conn)
                self.stats["overflow_created"] += 1

            return conn

    @contextmanager
    def get_connection(self):
        """
        الحصول على اتصال من Pool (يدعم SQLite و PostgreSQL)
        """
        if self.is_closed:
            raise RuntimeError("Connection Pool مُغلق")

        if self.config.db_type == "postgres":
            # Postgres Logic
            if not self.pg_connection_pool:
                raise RuntimeError("PostgreSQL Pool not initialized")

            conn = None
            try:
                conn = self.pg_connection_pool.getconn()
                # Ensure autocommit is on by default to match SQLite behavior often expected?
                # Or keep default. Psycopg2 default is autocommit=False (transactional).
                # SQLite with isolation_level=None is autocommit.
                # We'll assume the user manages transactions or expects auto-commit for reads.
                # But let's check config.
                if conn:
                    self.stats["checkouts"] += 1
                    yield conn
            except Exception as e:
                self.logger.error(f"Error getting PG connection: {e}")
                raise
            finally:
                if conn:
                    self.pg_connection_pool.putconn(conn)
                    self.stats["checkins"] += 1
        else:
            # SQLite Logic
            pooled_conn = None
            is_overflow = False

            try:
                try:
                    pooled_conn = self.pool.get(timeout=self.config.timeout)
                except Empty:
                    pooled_conn = self._create_overflow_connection()
                    is_overflow = True

                    if pooled_conn is None:
                        self.stats["timeouts"] += 1
                        raise TimeoutError(f"فشل الحصول على اتصال خلال {self.config.timeout} ثانية")

                if pooled_conn.is_expired(self.config.recycle):
                    pooled_conn.close()
                    pooled_conn = self._create_sqlite_connection()
                    self.stats["recycled"] += 1

                if self.config.enable_health_check:
                    if not pooled_conn.is_healthy():
                        pooled_conn.close()
                        pooled_conn = self._create_sqlite_connection()
                    self.stats["health_checks"] += 1

                pooled_conn.mark_used()
                self.stats["checkouts"] += 1

                yield pooled_conn.connection

            finally:
                if pooled_conn:
                    pooled_conn.mark_returned()

                    if is_overflow:
                        pooled_conn.close()
                        with self.lock:
                            if pooled_conn in self.overflow_connections:
                                self.overflow_connections.remove(pooled_conn)
                            if pooled_conn in self.all_connections:
                                self.all_connections.remove(pooled_conn)
                    else:
                        try:
                            self.pool.put(pooled_conn, block=False)
                            self.stats["checkins"] += 1
                        except Full:
                            pooled_conn.close()

    def execute(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True,
    ) -> Any:
        with self.get_connection() as conn:
            # Handle placeholder difference
            final_query = query
            if self.config.db_type == "postgres":
                final_query = query.replace("?", "%s")

            cursor = conn.cursor()
            cursor.execute(final_query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                if self.config.db_type == "postgres":
                    # No lastrowid in PG by default without RETURNING
                    return 0
                return cursor.lastrowid

    def execute_many(self, query: str, params_list: list[tuple]) -> None:
        with self.get_connection() as conn:
            final_query = query
            if self.config.db_type == "postgres":
                final_query = query.replace("?", "%s")

            cursor = conn.cursor()
            cursor.executemany(final_query, params_list)
            conn.commit()

    def transaction(self):
        @contextmanager
        def _transaction():
            with self.get_connection() as conn:
                try:
                    yield conn
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

        return _transaction()

    def _start_maintenance_thread(self) -> None:
        import weakref
        self_weak = weakref.ref(self)

        def maintenance():
            while True:
                pool_ref = self_weak()
                if pool_ref is None or pool_ref.is_closed:
                    break
                
                interval = pool_ref.config.health_check_interval
                time.sleep(min(5, interval))
                
                pool_ref = self_weak()
                if pool_ref is None or pool_ref.is_closed:
                    break
                
                try:
                    pool_ref._perform_maintenance()
                except Exception:
                    pass

        # Skip maintenance thread in headless offscreen test environment
        from PySide6.QtWidgets import QApplication
        is_headless = False
        if QApplication.instance():
            is_headless = QApplication.platformName() == "offscreen"

        if not is_headless:
            thread = threading.Thread(target=maintenance, daemon=True)
            thread.start()

    def _perform_maintenance(self) -> None:
        with self.lock:
            for pooled in self.all_connections[:]:
                if not pooled.in_use and not pooled.is_healthy():
                    pooled.close()
                    self.all_connections.remove(pooled)

                    new_conn = self._create_sqlite_connection()
                    if new_conn:
                        try:
                            self.pool.put(new_conn, block=False)
                        except Full:
                            logging.getLogger(__name__).warning("Ignored exception in connection_pool.py")

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            stats = {**self.stats}
            if self.config.db_type == "sqlite":
                stats.update(
                    {
                        "pool_size": self.pool.qsize(),
                        "max_pool_size": self.config.pool_size,
                        "overflow_size": len(self.overflow_connections),
                        "max_overflow": self.config.max_overflow,
                        "total_connections": len(self.all_connections),
                        "in_use": sum(1 for c in self.all_connections if c.in_use),
                    }
                )
            return stats

    def close(self) -> None:
        with self.lock:
            self.is_closed = True

            if self.pg_connection_pool:
                try:
                    self.pg_connection_pool.closeall()
                except Exception:
                    logging.getLogger(__name__).warning("Ignored exception in connection_pool.py")

            if self.config.db_type == "sqlite":
                for pooled in self.all_connections[:]:
                    pooled.close()
                    self.stats["connections_closed"] += 1

                self.all_connections.clear()
                self.overflow_connections.clear()

                while not self.pool.empty():
                    try:
                        self.pool.get_nowait()
                    except Empty:
                        break


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    # print("=" * 70)
    pass
    # print("🔗 اختبار Connection Pool")
    # print("=" * 70)

    # إنشاء قاعدة بيانات تجريبية
    test_db = "test_pool.db"
    Path(test_db).unlink(missing_ok=True)

    # إنشاء جدول تجريبي
    temp_conn = sqlite3.connect(test_db)
    temp_conn.execute("""
        CREATE TABLE test_users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """)
    temp_conn.commit()
    temp_conn.close()

    # 1. إنشاء Pool
    # print("\n1️⃣ إنشاء Connection Pool:")
    config = PoolConfig(pool_size=5, max_overflow=10)
    pool = ConnectionPool(test_db, config)
    # print(f"   ✅ تم إنشاء Pool بحجم {config.pool_size}")

    # 2. استخدام with statement
    # print("\n2️⃣ استخدام with statement:")
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("أحمد", "ahmad@example.com"),
        )
        conn.commit()
        # print("   ✅ تم إدراج مستخدم")

    # 3. استخدام execute helper
    # print("\n3️⃣ استخدام execute helper:")
    pool.execute(
        "INSERT INTO test_users (name, email) VALUES (?, ?)",
        ("محمد", "mohamed@example.com"),
        fetch_all=False,
    )
    # print("   ✅ تم إدراج مستخدم ثاني")

    # 4. استعلام
    # print("\n4️⃣ استعلام البيانات:")
    users = pool.execute("SELECT * FROM test_users")
    for user in users:
        # print(f"   - {dict(user)}")
        pass

    # 5. استخدام transaction
    # print("\n5️⃣ استخدام Transaction:")
    try:
        with pool.transaction() as conn:
            conn.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("سارة", "sara@example.com"),
            )
            conn.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("فاطمة", "fatima@example.com"),
            )
        # print("   ✅ تمت Transaction بنجاح")
    except Exception as e:  # noqa: F841
        # print(f"   ❌ فشل Transaction: {e}")
        logging.getLogger(__name__).warning("Ignored exception in connection_pool.py")

    # 6. الإحصائيات
    # print("\n6️⃣ إحصائيات Pool:")
    stats = pool.get_stats()
    for key, value in stats.items():
        # print(f"   {key}: {value}")
        pass

    # 7. إغلاق
    # print("\n7️⃣ إغلاق Pool:")
    pool.close()
    # print("   ✅ تم إغلاق Pool")

    # تنظيف
    Path(test_db).unlink(missing_ok=True)

    # print("\n" + "=" * 70)
    # print("✅ اكتملت جميع الاختبارات بنجاح!")
    # print("=" * 70)

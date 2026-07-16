import logging
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PostgreSQL Backend Implementation
تنفيذ DatabaseBackend لـ PostgreSQL
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
import psycopg2.extras

from src.utils.logger import setup_logger

from .backend import DatabaseBackend


class PostgreSQLBackend(DatabaseBackend):
    """
    PostgreSQL implementation لـ DatabaseBackend
    """

    def __init__(self, db_url: str):
        """
        تهيئة PostgreSQL Backend

        Args:
            db_url: PostgreSQL connection URL (postgresql://user:pass@host:5432/dbname)
        """
        self.db_url = db_url
        self.connection = None
        self.logger = setup_logger(__name__)
        self._in_transaction = False

    def connect(self) -> bool:
        """إنشاء الاتصال بقاعدة البيانات"""
        try:
            self.connection = psycopg2.connect(self.db_url)
            self.connection.autocommit = True  # Default to autocommit, manage transactions manually
            return True
        except Exception as e:
            self.logger.error(f"فشل الاتصال بقاعدة البيانات PostgreSQL: {e}")
            return False

    def disconnect(self) -> None:
        """إغلاق الاتصال"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                logging.getLogger(__name__).warning("Ignored exception in postgresql_backend.py")
            finally:
                self.connection = None

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """تنفيذ SELECT query"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        # تحويل صيغة placeholers من ؟ إلى %s الخاصة بـ psycopg2
        pg_query = query.replace("?", "%s")

        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(pg_query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error executing query: {query}, Error: {e}")
            raise

    def execute_insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        """تنفيذ INSERT query وإرجاع last_insert_id"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        # تحويل صيغة placeholers
        pg_query = query.replace("?", "%s")

        # PostgreSQL يحتاج RETURNING id للحصول على last_insert_id
        if "RETURNING" not in pg_query.upper():
            pg_query += " RETURNING id"

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(pg_query, params)
                last_id = cursor.fetchone()[0]
                return last_id
        except Exception as e:
            self.logger.error(f"Error executing insert: {query}, Error: {e}")
            raise

    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ UPDATE/DELETE query"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        pg_query = query.replace("?", "%s")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(pg_query, params)
                return cursor.rowcount
        except Exception as e:
            self.logger.error(f"Error executing update: {query}, Error: {e}")
            raise

    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ query وإرجاع قيمة واحدة"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        pg_query = query.replace("?", "%s")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(pg_query, params)
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error executing scalar: {query}, Error: {e}")
            raise

    def begin_transaction(self) -> None:
        """بدء transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        self.connection.autocommit = False
        self._in_transaction = True

    def commit(self) -> None:
        """Commit transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        try:
            self.connection.commit()
        finally:
            self.connection.autocommit = True
            self._in_transaction = False

    def rollback(self) -> None:
        """Rollback transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")

        try:
            self.connection.rollback()
        finally:
            self.connection.autocommit = True
            self._in_transaction = False

    @contextmanager
    def transaction(self):
        """Context manager للـ transaction"""
        if self._in_transaction:
            # Nested transaction support (savepoint) could be added here,
            # but for now we just yield
            yield self
        else:
            self.begin_transaction()
            try:
                yield self
                self.commit()
            except Exception:
                self.rollback()
                raise

    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        query = "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)"
        return self.execute_scalar(query, (table_name,))

    def get_last_insert_id(self) -> int:
        """
        الحصول على آخر ID تم إدراجه.
        ملاحظة: في PG يفضل استخدام RETURNING id في جملة INSERT نفسها (تم معالجتها في execute_insert)
        """
        # هذه الدالة قد لا تعمل بدقة في PG بدون تسلسل محدد، لذا نعتمد على execute_insert
        return 0

    @property
    def is_connected(self) -> bool:
        """التحقق من حالة الاتصال"""
        return self.connection is not None and self.connection.closed == 0

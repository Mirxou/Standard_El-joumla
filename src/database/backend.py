#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Backend Interface
واجهة abstraction للـ database backends (SQLite, PostgreSQL, etc.)
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple


class DatabaseBackend(ABC):
    """Interface لـ database backends"""

    @abstractmethod
    def connect(self) -> bool:
        """
        إنشاء الاتصال بقاعدة البيانات

        Returns:
            bool: True إذا نجح الاتصال، False خلاف ذلك
        """

    @abstractmethod
    def disconnect(self) -> None:
        """إغلاق الاتصال بقاعدة البيانات"""

    @abstractmethod
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """
        تنفيذ SELECT query وإرجاع النتائج كقائمة من dictionaries

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            List[Dict[str, Any]]: قائمة النتائج
        """

    @abstractmethod
    def execute_insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        """
        تنفيذ INSERT query وإرجاع last_insert_id

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            Optional[int]: last_insert_id أو None إذا فشل
        """

    @abstractmethod
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """
        تنفيذ UPDATE/DELETE query وإرجاع عدد الصفوف المتأثرة

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            int: عدد الصفوف المتأثرة
        """

    @abstractmethod
    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """
        تنفيذ query وإرجاع قيمة واحدة

        Args:
            query: SQL query string
            params: Query parameters tuple

        Returns:
            Any: القيمة الأولى من النتيجة
        """

    @abstractmethod
    def begin_transaction(self) -> None:
        """بدء transaction"""

    @abstractmethod
    def commit(self) -> None:
        """Commit transaction"""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback transaction"""

    @contextmanager
    @abstractmethod
    def transaction(self):
        """
        Context manager للـ transaction
        الاستخدام:
            with backend.transaction():
                backend.execute_insert(...)
                backend.execute_update(...)
        """

    @abstractmethod
    def table_exists(self, table_name: str) -> bool:
        """
        التحقق من وجود جدول

        Args:
            table_name: اسم الجدول

        Returns:
            bool: True إذا كان الجدول موجوداً
        """

    @abstractmethod
    def get_last_insert_id(self) -> int:
        """
        الحصول على آخر ID تم إدراجه

        Returns:
            int: last_insert_id
        """

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """التحقق من حالة الاتصال"""

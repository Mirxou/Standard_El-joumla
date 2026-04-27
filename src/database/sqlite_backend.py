#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Backend Implementation
تنفيذ DatabaseBackend لـ SQLite
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from .backend import DatabaseBackend
from src.utils.logger import setup_logger


class SQLiteBackend(DatabaseBackend):
    """SQLite implementation لـ DatabaseBackend"""
    
    def __init__(self, db_path: str):
        """
        تهيئة SQLite Backend
        
        Args:
            db_path: مسار قاعدة البيانات
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self.logger = setup_logger(__name__)
        self._in_transaction = False
    
    def connect(self) -> bool:
        """إنشاء الاتصال بقاعدة البيانات"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=60.0
            )
            
            # إعدادات WAL mode للأداء والموثوقية
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            
            # Row factory للحصول على نتائج كـ dict
            self.connection.row_factory = sqlite3.Row
            
            return True
        except Exception as e:
            self.logger.error(f"فشل الاتصال بقاعدة البيانات SQLite: {e}")
            return False
    
    def disconnect(self) -> None:
        """إغلاق الاتصال"""
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
            finally:
                self.connection = None
    
    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """تنفيذ SELECT query"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute(query, params)
        rows = cursor.fetchall()
        
        # تحويل إلى list of dicts
        return [dict(row) for row in rows]
    
    def execute_insert(self, query: str, params: Tuple = ()) -> Optional[int]:
        """تنفيذ INSERT query وإرجاع last_insert_id"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute(query, params)
        lastrowid = cursor.lastrowid
        
        # Commit إذا لم نكن في transaction
        if not self._in_transaction:
            self.connection.commit()
        
        return lastrowid if lastrowid else None
    
    def execute_update(self, query: str, params: Tuple = ()) -> int:
        """تنفيذ UPDATE/DELETE query"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute(query, params)
        
        # Commit إذا لم نكن في transaction
        if not self._in_transaction:
            self.connection.commit()
        
        return cursor.rowcount
    
    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ query وإرجاع قيمة واحدة"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else None
    
    def begin_transaction(self) -> None:
        """بدء transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        self._in_transaction = True
        # SQLite transactions تبدأ تلقائياً
    
    def commit(self) -> None:
        """Commit transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        try:
            self.connection.commit()
        finally:
            self._in_transaction = False
    
    def rollback(self) -> None:
        """Rollback transaction"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        try:
            self.connection.rollback()
        finally:
            self._in_transaction = False
    
    @contextmanager
    def transaction(self):
        """Context manager للـ transaction"""
        self.begin_transaction()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return cursor.fetchone() is not None
    
    def get_last_insert_id(self) -> int:
        """الحصول على آخر ID تم إدراجه"""
        if not self.connection:
            raise RuntimeError("Database connection not initialized")
        
        cursor = self.connection.execute("SELECT last_insert_rowid()")
        result = cursor.fetchone()
        return result[0] if result else 0
    
    @property
    def is_connected(self) -> bool:
        """التحقق من حالة الاتصال"""
        return self.connection is not None
    
    def get_connection(self):
        """الحصول على الاتصال المباشر (للاستخدام المتقدم)"""
        return self.connection


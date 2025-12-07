#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
خدمة Connection Pooling
إدارة اتصالات قاعدة البيانات بكفاءة
"""

import sqlite3
import threading
import time
from typing import Optional, Callable, Any, Dict
from queue import Queue, Empty, Full
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PoolConfig:
    """تكوين Connection Pool"""
    
    # حجم Pool (موسّع للتعامل مع 200K+ منتج)
    pool_size: int = 15  # عدد الاتصالات الافتراضي (زيادة من 10)
    max_overflow: int = 30  # أقصى عدد اتصالات إضافية (زيادة من 20)
    
    # المهلات الزمنية
    timeout: float = 60.0  # مهلة انتظار اتصال (زيادة من 30 إلى 60 ثانية)
    recycle: int = 3600  # إعادة تدوير الاتصال بعد ساعة
    
    # إعدادات SQLite
    check_same_thread: bool = False
    isolation_level: Optional[str] = None  # None = autocommit
    
    # الصيانة
    enable_health_check: bool = True
    health_check_interval: int = 300  # 5 دقائق


class PooledConnection:
    """
    اتصال في Pool
    يحتوي على الاتصال الفعلي ومعلومات الحالة
    """
    
    def __init__(self, connection: sqlite3.Connection, pool: 'ConnectionPool'):
        self.connection = connection
        self.pool = pool
        self.created_at = time.time()
        self.last_used = time.time()
        self.in_use = False
        self.uses = 0
    
    def is_expired(self, recycle_time: int) -> bool:
        """التحقق من انتهاء صلاحية الاتصال"""
        age = time.time() - self.created_at
        return age > recycle_time
    
    def mark_used(self) -> None:
        """تعليم الاتصال كمستخدم"""
        self.in_use = True
        self.last_used = time.time()
        self.uses += 1
    
    def mark_returned(self) -> None:
        """تعليم الاتصال كمُعاد"""
        self.in_use = False
    
    def is_healthy(self) -> bool:
        """التحقق من سلامة الاتصال"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        """إغلاق الاتصال"""
        try:
            self.connection.close()
        except Exception:
            pass


class ConnectionPool:
    """
    Connection Pool لـ SQLite
    
    المزايا:
    - Pool بحجم قابل للتكوين
    - دعم Overflow (اتصالات إضافية مؤقتة)
    - إعادة تدوير الاتصالات القديمة
    - فحص سلامة الاتصالات
    - Thread-safe
    - إحصائيات الاستخدام
    """
    
    def __init__(
        self,
        database_path: str,
        config: Optional[PoolConfig] = None
    ):
        """
        تهيئة Connection Pool
        
        Args:
            database_path: مسار قاعدة البيانات
            config: تكوين Pool
        """
        self.database_path = database_path
        self.config = config or PoolConfig()
        
        # Queue للاتصالات المتاحة
        self.pool: Queue[PooledConnection] = Queue(maxsize=self.config.pool_size)
        
        # جميع الاتصالات (للتتبع)
        self.all_connections: list[PooledConnection] = []
        self.overflow_connections: list[PooledConnection] = []
        
        # قفل للعمليات الحساسة
        self.lock = threading.RLock()
        
        # حالة Pool
        self.is_closed = False
        
        # إحصائيات
        self.stats = {
            'connections_created': 0,
            'connections_closed': 0,
            'overflow_created': 0,
            'checkouts': 0,
            'checkins': 0,
            'timeouts': 0,
            'health_checks': 0,
            'recycled': 0
        }
        
        # إنشاء الاتصالات الأولية
        self._initialize_pool()
        
        # بدء thread للصيانة
        if self.config.enable_health_check:
            self._start_maintenance_thread()
    
    def _initialize_pool(self) -> None:
        """إنشاء الاتصالات الأولية"""
        for _ in range(self.config.pool_size):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
    
    def _create_connection(self) -> Optional[PooledConnection]:
        """إنشاء اتصال جديد"""
        try:
            # إنشاء اتصال SQLite
            connection = sqlite3.connect(
                self.database_path,
                check_same_thread=self.config.check_same_thread,
                isolation_level=self.config.isolation_level,
                timeout=self.config.timeout
            )
            
            # إعدادات أداء وموثوقية
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA synchronous=NORMAL")
            connection.execute("PRAGMA cache_size=10000")
            connection.execute("PRAGMA temp_store=MEMORY")
            
            # Row factory للنتائج كـ dict
            connection.row_factory = sqlite3.Row
            
            # إنشاء PooledConnection
            pooled = PooledConnection(connection, self)
            
            with self.lock:
                self.all_connections.append(pooled)
                self.stats['connections_created'] += 1
            
            return pooled
            
        except Exception as e:
            print(f"❌ فشل إنشاء اتصال: {e}")
            return None
    
    def _create_overflow_connection(self) -> Optional[PooledConnection]:
        """إنشاء اتصال overflow مؤقت"""
        with self.lock:
            # التحقق من عدم تجاوز الحد الأقصى
            current_overflow = len(self.overflow_connections)
            if current_overflow >= self.config.max_overflow:
                return None
            
            conn = self._create_connection()
            if conn:
                self.overflow_connections.append(conn)
                self.stats['overflow_created'] += 1
            
            return conn
    
    @contextmanager
    def get_connection(self):
        """
        الحصول على اتصال من Pool
        
        يُستخدم مع with statement لضمان الإرجاع:
        
        Example:
            >>> with pool.get_connection() as conn:
            ...     cursor = conn.cursor()
            ...     cursor.execute("SELECT * FROM users")
        
        Yields:
            sqlite3.Connection
        """
        if self.is_closed:
            raise RuntimeError("Connection Pool مُغلق")
        
        pooled_conn = None
        is_overflow = False
        
        try:
            # محاولة الحصول من Pool
            try:
                pooled_conn = self.pool.get(timeout=self.config.timeout)
            except Empty:
                # محاولة إنشاء overflow
                pooled_conn = self._create_overflow_connection()
                is_overflow = True
                
                if pooled_conn is None:
                    self.stats['timeouts'] += 1
                    raise TimeoutError(
                        f"فشل الحصول على اتصال خلال {self.config.timeout} ثانية"
                    )
            
            # التحقق من الصلاحية وإعادة التدوير إذا لزم الأمر
            if pooled_conn.is_expired(self.config.recycle):
                pooled_conn.close()
                pooled_conn = self._create_connection()
                self.stats['recycled'] += 1
            
            # التحقق من السلامة
            if self.config.enable_health_check:
                if not pooled_conn.is_healthy():
                    pooled_conn.close()
                    pooled_conn = self._create_connection()
                self.stats['health_checks'] += 1
            
            # تعليم كمستخدم
            pooled_conn.mark_used()
            self.stats['checkouts'] += 1
            
            # إعطاء الاتصال الفعلي
            yield pooled_conn.connection
            
        finally:
            # إرجاع الاتصال
            if pooled_conn:
                pooled_conn.mark_returned()
                
                if is_overflow:
                    # إغلاق overflow connections
                    pooled_conn.close()
                    with self.lock:
                        if pooled_conn in self.overflow_connections:
                            self.overflow_connections.remove(pooled_conn)
                        if pooled_conn in self.all_connections:
                            self.all_connections.remove(pooled_conn)
                else:
                    # إرجاع إلى Pool
                    try:
                        self.pool.put(pooled_conn, block=False)
                        self.stats['checkins'] += 1
                    except Full:
                        # لا ينبغي أن يحدث
                        pooled_conn.close()
    
    def execute(
        self,
        query: str,
        params: tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True
    ) -> Any:
        """
        تنفيذ استعلام مع إدارة تلقائية للاتصال
        
        Args:
            query: الاستعلام
            params: المعاملات
            fetch_one: إرجاع صف واحد
            fetch_all: إرجاع جميع الصفوف
            
        Returns:
            النتيجة أو None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                conn.commit()
                return cursor.lastrowid
    
    def execute_many(
        self,
        query: str,
        params_list: list[tuple]
    ) -> None:
        """
        تنفيذ استعلام متعدد (batch insert/update)
        
        Args:
            query: الاستعلام
            params_list: قائمة المعاملات
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
    
    def transaction(self):
        """
        سياق لـ Transaction
        
        Example:
            >>> with pool.transaction() as conn:
            ...     conn.execute("INSERT INTO users ...")
            ...     conn.execute("UPDATE stats ...")
        """
        @contextmanager
        def _transaction():
            with self.get_connection() as conn:
                try:
                    yield conn
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    raise
        
        return _transaction()
    
    def _start_maintenance_thread(self) -> None:
        """بدء thread للصيانة الدورية"""
        def maintenance():
            while not self.is_closed:
                time.sleep(self.config.health_check_interval)
                self._perform_maintenance()
        
        thread = threading.Thread(target=maintenance, daemon=True)
        thread.start()
    
    def _perform_maintenance(self) -> None:
        """إجراء الصيانة الدورية"""
        with self.lock:
            # فحص جميع الاتصالات
            for pooled in self.all_connections[:]:
                # إزالة الاتصالات الميتة
                if not pooled.in_use and not pooled.is_healthy():
                    pooled.close()
                    self.all_connections.remove(pooled)
                    
                    # إنشاء بديل
                    new_conn = self._create_connection()
                    if new_conn:
                        try:
                            self.pool.put(new_conn, block=False)
                        except Full:
                            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات Pool"""
        with self.lock:
            return {
                **self.stats,
                'pool_size': self.pool.qsize(),
                'max_pool_size': self.config.pool_size,
                'overflow_size': len(self.overflow_connections),
                'max_overflow': self.config.max_overflow,
                'total_connections': len(self.all_connections),
                'in_use': sum(1 for c in self.all_connections if c.in_use)
            }
    
    def close(self) -> None:
        """إغلاق Pool وجميع الاتصالات"""
        with self.lock:
            self.is_closed = True
            
            # إغلاق جميع الاتصالات
            for pooled in self.all_connections[:]:
                pooled.close()
                self.stats['connections_closed'] += 1
            
            self.all_connections.clear()
            self.overflow_connections.clear()
            
            # تفريغ Queue
            while not self.pool.empty():
                try:
                    self.pool.get_nowait()
                except Empty:
                    break


# ==================== مثال على الاستخدام ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🔗 اختبار Connection Pool")
    print("=" * 70)
    
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
    print("\n1️⃣ إنشاء Connection Pool:")
    config = PoolConfig(pool_size=5, max_overflow=10)
    pool = ConnectionPool(test_db, config)
    print(f"   ✅ تم إنشاء Pool بحجم {config.pool_size}")
    
    # 2. استخدام with statement
    print("\n2️⃣ استخدام with statement:")
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_users (name, email) VALUES (?, ?)",
            ("أحمد", "ahmad@example.com")
        )
        conn.commit()
        print("   ✅ تم إدراج مستخدم")
    
    # 3. استخدام execute helper
    print("\n3️⃣ استخدام execute helper:")
    pool.execute(
        "INSERT INTO test_users (name, email) VALUES (?, ?)",
        ("محمد", "mohamed@example.com"),
        fetch_all=False
    )
    print("   ✅ تم إدراج مستخدم ثاني")
    
    # 4. استعلام
    print("\n4️⃣ استعلام البيانات:")
    users = pool.execute("SELECT * FROM test_users")
    for user in users:
        print(f"   - {dict(user)}")
    
    # 5. استخدام transaction
    print("\n5️⃣ استخدام Transaction:")
    try:
        with pool.transaction() as conn:
            conn.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("سارة", "sara@example.com")
            )
            conn.execute(
                "INSERT INTO test_users (name, email) VALUES (?, ?)",
                ("فاطمة", "fatima@example.com")
            )
        print("   ✅ تمت Transaction بنجاح")
    except Exception as e:
        print(f"   ❌ فشل Transaction: {e}")
    
    # 6. الإحصائيات
    print("\n6️⃣ إحصائيات Pool:")
    stats = pool.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # 7. إغلاق
    print("\n7️⃣ إغلاق Pool:")
    pool.close()
    print("   ✅ تم إغلاق Pool")
    
    # تنظيف
    Path(test_db).unlink(missing_ok=True)
    
    print("\n" + "=" * 70)
    print("✅ اكتملت جميع الاختبارات بنجاح!")
    print("=" * 70)

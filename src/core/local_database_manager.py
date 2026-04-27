#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مدير قاعدة البيانات المحلية - Local Database Manager
إدارة قاعدة البيانات المحلية (Local Cache) للتطبيق المكتبي
"""

import sqlite3
import os
import platform
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
from datetime import datetime
from src.utils.logger import setup_logger
from src.core.exceptions import DatabaseException
from src.core.database_encryption import DatabaseEncryption
from src.core.keyring_manager import KeyringManager


class LocalDatabaseManager:
    """مدير قاعدة البيانات المحلية (Local Cache)"""
    
    def __init__(self, db_path: Optional[str] = None, encryption_password: Optional[str] = None):
        """
        تهيئة مدير قاعدة البيانات المحلية
        
        Args:
            db_path: مسار قاعدة البيانات (اختياري - سيتم تحديده تلقائياً)
            encryption_password: كلمة مرور التشفير (اختياري - سيتم الحصول عليها من Keyring)
        """
        self.logger = setup_logger(__name__)
        
        # تهيئة Keyring Manager و Database Encryption
        self.keyring_manager = KeyringManager()
        self.db_encryption = DatabaseEncryption(self.keyring_manager)
        
        # تحديد مسار قاعدة البيانات المحلية
        if db_path is None:
            self.db_path = self._get_local_db_path()
        else:
            self.db_path = db_path
        
        self.encryption_password = encryption_password
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_data_directory()
    
    def _get_local_db_path(self) -> str:
        """
        الحصول على مسار قاعدة البيانات المحلية حسب نظام التشغيل
        
        Returns:
            مسار قاعدة البيانات المحلية
        """
        system = platform.system()
        
        if system == "Windows":
            # Windows: %APPDATA%/LogicalERP/local_cache.db
            appdata = os.getenv("APPDATA")
            if appdata:
                db_dir = Path(appdata) / "LogicalERP"
            else:
                # Fallback إلى مجلد المستخدم
                home = Path.home()
                db_dir = home / "AppData" / "Roaming" / "LogicalERP"
        elif system == "Darwin":  # macOS
            # macOS: ~/Library/Application Support/LogicalERP/local_cache.db
            home = Path.home()
            db_dir = home / "Library" / "Application Support" / "LogicalERP"
        else:  # Linux
            # Linux: ~/.local/share/logical_erp/local_cache.db
            home = Path.home()
            db_dir = home / ".local" / "share" / "logical_erp"
        
        db_dir.mkdir(parents=True, exist_ok=True)
        return str(db_dir / "local_cache.db")
    
    def _ensure_data_directory(self):
        """التأكد من وجود مجلد قاعدة البيانات"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self) -> bool:
        """
        تهيئة قاعدة البيانات المحلية
        
        Returns:
            True إذا نجحت التهيئة، False خلاف ذلك
        """
        try:
            # إنشاء الاتصال (مشفر إذا كان SQLCipher متوفر)
            if self.db_encryption.is_available():
                # استخدام SQLCipher
                password = self.encryption_password or self.db_encryption.get_encryption_password()
                self.connection = self.db_encryption.create_encrypted_connection(
                    self.db_path,
                    password
                )
                self.logger.info("✅ تم الاتصال بقاعدة البيانات المشفرة")
            else:
                # استخدام SQLite العادي
                self.connection = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=60.0
                )
                self.logger.warning("⚠️ SQLCipher غير متوفر - قاعدة البيانات غير مشفرة")
            
            # تفعيل WAL Mode للأداء والموثوقية (ACID Compliance)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA synchronous=NORMAL")
            self.connection.execute("PRAGMA cache_size=10000")
            self.connection.execute("PRAGMA temp_store=MEMORY")
            
            # تفعيل المفاتيح الخارجية
            self.connection.execute("PRAGMA foreign_keys=ON")
            
            # إنشاء الجداول
            self._create_tables()
            
            # إنشاء الفهارس
            self._create_indexes()
            
            # تطبيق Migrations
            from src.core.local_migrations.migration_manager import LocalMigrationManager
            migration_manager = LocalMigrationManager(self)
            migration_manager.initialize()
            migration_manager.apply_all_pending()
            
            self.logger.info(f"✅ تم تهيئة قاعدة البيانات المحلية: {self.db_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل تهيئة قاعدة البيانات المحلية: {str(e)}")
            raise DatabaseException(f"فشل تهيئة قاعدة البيانات المحلية: {str(e)}")

    def create_thread_connection(self, timeout: float = 30.0, read_only: bool = False) -> sqlite3.Connection:
        """إنشاء اتصال آمن للخيوط باستخدام LocalDatabaseManager"""
        if self.db_encryption.is_available():
            password = self.encryption_password or self.db_encryption.get_encryption_password()
            conn = self.db_encryption.create_encrypted_connection(self.db_path, password)
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=timeout)

        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        if read_only:
            conn.execute("PRAGMA query_only=true")
        return conn
    
    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات المحلية"""
        
        # جدول sync_queue - لتتبع العمليات المعلقة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                record_id INTEGER NOT NULL,
                operation TEXT NOT NULL,  -- 'create', 'update', 'delete'
                data TEXT,  -- JSON data
                retry_count INTEGER DEFAULT 0,
                last_retry_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_name, record_id, operation)
            )
        """)
        
        # جدول sync_status - حالة المزامنة العامة
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                device_id TEXT,
                server_url TEXT,
                is_online BOOLEAN DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول products - نسخة محلية من المنتجات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT,
                barcode TEXT UNIQUE,
                category_id INTEGER,
                unit TEXT NOT NULL DEFAULT 'قطعة',
                cost_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                selling_price DECIMAL(10,2) NOT NULL DEFAULT 0,
                min_stock INTEGER DEFAULT 0,
                current_stock INTEGER DEFAULT 0,
                description TEXT,
                image_url TEXT,  -- URL فقط (لا BLOB)
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,  -- 0 = غير متزامن، 1 = متزامن
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,  -- Soft Delete
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول customers - نسخة محلية من العملاء
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                credit_limit DECIMAL(10,2) DEFAULT 0,
                current_balance DECIMAL(10,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول sales - نسخة محلية من المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                final_amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT DEFAULT 'نقدي',
                sale_date DATE DEFAULT CURRENT_DATE,
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول sale_items - نسخة محلية من عناصر المبيعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY,
                sale_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                cost_price DECIMAL(10,2) NOT NULL,
                profit DECIMAL(10,2) NOT NULL,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sale_id) REFERENCES sales(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # جدول batches - نسخة محلية من الدفعات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                cost_price DECIMAL(10,2) NOT NULL,
                selling_price DECIMAL(10,2),
                expiry_date DATE,
                purchase_date DATE DEFAULT CURRENT_DATE,
                supplier_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # جدول categories - نسخة محلية من الفئات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                name_en TEXT,
                description TEXT,
                parent_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id)
            )
        """)
        
        # جدول users - نسخة محلية من المستخدمين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                full_name TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL DEFAULT 'user',
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_locked BOOLEAN DEFAULT 0,
                failed_login_attempts INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                last_password_change TIMESTAMP,
                password_expires_at TIMESTAMP,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)

        # جدول suppliers - نسخة محلية من الموردين
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                contact_person TEXT,
                phone TEXT,
                phone2 TEXT,
                email TEXT,
                address TEXT,
                tax_number TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول purchases - نسخة محلية من المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY,
                invoice_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER,
                total_amount DECIMAL(10,2) NOT NULL,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                final_amount DECIMAL(10,2) NOT NULL,
                payment_method TEXT DEFAULT 'نقدي',
                purchase_date DATE DEFAULT CURRENT_DATE,
                user_id INTEGER,
                notes TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # جدول purchase_items - نسخة محلية من عناصر المشتريات
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY,
                purchase_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # جدول stock_movements - نسخة محلية من حركات المخزون
        self.connection.execute("""
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                batch_id INTEGER,
                movement_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                reference_id INTEGER,
                reference_type TEXT,
                notes TEXT,
                user_id INTEGER,
                is_synced INTEGER DEFAULT 0,
                last_synced_at TIMESTAMP,
                sync_version INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)

        # تهيئة sync_status
        self.connection.execute("""
            INSERT OR IGNORE INTO sync_status (id, last_synced_at, sync_version)
            VALUES (1, NULL, 1)
        """)

        self.connection.commit()
    
    def _create_indexes(self):
        """إنشاء الفهارس لتحسين الأداء"""
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_synced ON products(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_products_deleted ON products(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_customers_synced ON customers(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_customers_deleted ON customers(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sales_synced ON sales(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_sales_deleted ON sales(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sale_items_synced ON sale_items(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_batches_synced ON batches(is_synced)",
            "CREATE INDEX IF NOT EXISTS idx_batches_deleted ON batches(is_deleted)",
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_table_record ON sync_queue(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_sync_queue_retry ON sync_queue(retry_count, last_retry_at)",
        ]
        
        for index_sql in indexes:
            try:
                self.connection.execute(index_sql)
            except Exception as e:
                self.logger.warning(f"فشل إنشاء الفهرس: {index_sql} - {str(e)}")
        
        self.connection.commit()
    
    @contextmanager
    def transaction(self, timeout: int = 5):
        """
        Context manager للعمليات داخل Transaction مع Row-level Locking
        
        Args:
            timeout: مهلة الانتظار على Lock بالثواني (افتراضي: 5)
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")
        
        try:
            # تعيين timeout للانتظار على Lock
            self.connection.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
            self.connection.execute("BEGIN IMMEDIATE")  # BEGIN IMMEDIATE للحصول على Lock فوراً
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise DatabaseException(f"فشل Transaction: {str(e)}")
    
    def lock_row(self, table_name: str, record_id: int) -> bool:
        """
        قفل صف معين (Row-level Locking)
        
        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            
        Returns:
            True إذا نجح القفل
        """
        try:
            # استخدام SELECT ... FOR UPDATE لـ Row-level Locking
            self.connection.execute(
                f"SELECT * FROM {table_name} WHERE id = ? FOR UPDATE",
                (record_id,)
            )
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ فشل قفل الصف: {table_name}.{record_id} - {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Tuple = (), exclude_deleted: bool = True) -> List[Dict[str, Any]]:
        """
        تنفيذ استعلام SELECT
        
        Args:
            query: استعلام SQL (يجب أن يكون parameterized)
            params: معاملات الاستعلام
            exclude_deleted: استبعاد السجلات المحذوفة منطقياً (افتراضي: True)
            
        Returns:
            قائمة من النتائج كـ dictionaries
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")
        
        try:
            # إضافة فلتر is_deleted = 0 تلقائياً إذا كان exclude_deleted = True
            # (فقط إذا كان الاستعلام لا يحتوي على is_deleted)
            modified_query = query
            if exclude_deleted and 'is_deleted' not in query.upper():
                # محاولة إضافة WHERE clause
                query_upper = query.upper().strip()
                if 'WHERE' in query_upper:
                    # إضافة AND is_deleted = 0
                    modified_query = query + " AND is_deleted = 0"
                elif 'FROM' in query_upper:
                    # إضافة WHERE is_deleted = 0
                    from_pos = query_upper.find('FROM')
                    where_pos = query_upper.find('WHERE', from_pos)
                    if where_pos == -1:
                        # إضافة WHERE قبل ORDER BY أو GROUP BY أو LIMIT
                        order_pos = query_upper.find('ORDER BY', from_pos)
                        group_pos = query_upper.find('GROUP BY', from_pos)
                        limit_pos = query_upper.find('LIMIT', from_pos)
                        
                        insert_pos = len(query)
                        if order_pos != -1:
                            insert_pos = min(insert_pos, query_upper.find('ORDER BY', from_pos))
                        if group_pos != -1:
                            insert_pos = min(insert_pos, query_upper.find('GROUP BY', from_pos))
                        if limit_pos != -1:
                            insert_pos = min(insert_pos, query_upper.find('LIMIT', from_pos))
                        
                        modified_query = query[:insert_pos] + " WHERE is_deleted = 0 " + query[insert_pos:]
            
            cursor = self.connection.execute(modified_query, params)
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")
    
    def execute(self, query: str, params: Tuple = ()):
        """تنفيذ استعلام SQL مباشر"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            return self.connection.execute(query, params)
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """
        تنفيذ استعلام غير SELECT (INSERT, UPDATE, DELETE)
        
        Args:
            query: استعلام SQL (يجب أن يكون parameterized)
            params: معاملات الاستعلام
            
        Returns:
            عدد الصفوف المتأثرة
        """
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")
        
        try:
            cursor = self.connection.execute(query, params)
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")
    
    def get_last_synced_at(self) -> Optional[datetime]:
        """الحصول على آخر وقت مزامنة"""
        results = self.execute_query(
            "SELECT last_synced_at FROM sync_status WHERE id = 1"
        )
        if results and results[0].get('last_synced_at'):
            return datetime.fromisoformat(results[0]['last_synced_at'])
        return None
    
    def set_last_synced_at(self, timestamp: datetime):
        """تعيين آخر وقت مزامنة"""
        self.execute_non_query(
            "UPDATE sync_status SET last_synced_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (timestamp.isoformat(),)
        )
    
    def soft_delete(self, table_name: str, record_id: int) -> bool:
        """
        حذف منطقي (Soft Delete) لسجل
        
        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            
        Returns:
            True إذا نجح الحذف
        """
        try:
            self.execute_non_query(
                f"""
                UPDATE {table_name}
                SET is_deleted = 1, deleted_at = CURRENT_TIMESTAMP, is_synced = 0
                WHERE id = ?
                """,
                (record_id,)
            )
            self.logger.info(f"✅ تم حذف السجل منطقياً: {table_name}.{record_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل الحذف المنطقي: {str(e)}")
            return False
    
    def restore_deleted(self, table_name: str, record_id: int) -> bool:
        """
        استعادة سجل محذوف منطقياً
        
        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            
        Returns:
            True إذا نجحت الاستعادة
        """
        try:
            self.execute_non_query(
                f"""
                UPDATE {table_name}
                SET is_deleted = 0, deleted_at = NULL, is_synced = 0
                WHERE id = ?
                """,
                (record_id,)
            )
            self.logger.info(f"✅ تم استعادة السجل: {table_name}.{record_id}")
            return True
        except Exception as e:
            self.logger.error(f"❌ فشل استعادة السجل: {str(e)}")
            return False
    
    def get_pending_items(self, table_name: Optional[str] = None, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """
        الحصول على العناصر المعلقة (غير المتزامنة)
        
        Args:
            table_name: اسم الجدول (اختياري - للحصول على جميع الجداول)
            
        Returns:
            قائمة بالعناصر المعلقة
        """
        if table_name:
            query = f"""
                SELECT * FROM {table_name}
                WHERE is_synced = 0 AND is_deleted = 0
                ORDER BY created_at ASC
            """
            return self.execute_query(query)
        else:
            # الحصول على جميع العناصر المعلقة من جميع الجداول
            tables = ['products', 'customers', 'sales', 'sale_items', 'batches', 'categories', 'suppliers']
            all_pending = []
            for table in tables:
                query = f"""
                    SELECT *, '{table}' as source_table FROM {table}
                    WHERE is_synced = 0 AND is_deleted = 0
                """
                all_pending.extend(self.execute_query(query))
            return all_pending
    
    def mark_as_synced(self, table_name: str, record_id: int, sync_version: int = 1):
        """
        تعليم سجل كمتزامن
        
        Args:
            table_name: اسم الجدول
            record_id: معرف السجل
            sync_version: إصدار المزامنة
        """
        self.execute_non_query(
            f"""
            UPDATE {table_name}
            SET is_synced = 1, last_synced_at = CURRENT_TIMESTAMP, sync_version = ?
            WHERE id = ?
            """,
            (sync_version, record_id)
        )

    def execute_scalar(self, query: str, params: Tuple = ()) -> Any:
        """تنفيذ استعلام وإرجاع قيمة واحدة"""
        if not self.connection:
            raise DatabaseException("قاعدة البيانات غير مهيأة")

        try:
            cursor = self.connection.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"خطأ في تنفيذ الاستعلام: {query} - {str(e)}")
            raise DatabaseException(f"خطأ في تنفيذ الاستعلام: {str(e)}")

    def table_exists(self, table_name: str) -> bool:
        """التحقق من وجود جدول"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_scalar(query, (table_name,))
            return result is not None
        except Exception as e:
            self.logger.error(f"Error checking table {table_name} existence: {e}")
            return False

    def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """تنفيذ استعلام وإرجاع صف واحد"""
        results = self.execute_query(query, params)
        return results[0] if results else None

    def get_last_insert_id(self) -> int:
        """الحصول على آخر ID تم إدراجه"""
        result = self.execute_scalar("SELECT last_insert_rowid()")
        return result if result else 0

    def close(self):
        """إغلاق الاتصال بقاعدة البيانات"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("تم إغلاق قاعدة البيانات المحلية")
